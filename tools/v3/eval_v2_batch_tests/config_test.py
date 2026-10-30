"""Explicit profile, G/M/B plan and immutable scientific Resume identity."""

import json
from pathlib import Path

import pytest
import yaml
from cosmos_framework.evaluation.robocasa_v2.contract import (
    build_manifest,
    validate_manifest,
)
from robocasa_eval_v2.config import resolve, execution
from robocasa_eval_v2.resources import physical_slots
from robocasa_eval_v2.cli import main
from tools.v3.eval_v2_production_tests.entry_test import config
from tools.v3.eval_v2_production_tests.contract_test import manifest


@pytest.mark.parametrize(
    "g,n,m", [(1, 2, 2), (2, 3, 2), (3, 1, 8), (3, 7, 3), (8, 18, 4)]
)
def test_useful_slots_are_slot_major_gpu_minor_and_models_per_used_GPU(g, n, m):
    cfg = {"gpu_ids": list(range(g)), "execution_profile": "phase_b", "sims_per_gpu": m}
    actual = physical_slots(cfg, n)
    assert len(actual) == min(g * m, n)
    assert (
        list(actual.items())
        == [(f"GPU{gpu}_S{slot}", gpu) for slot in range(m) for gpu in range(g)][:n]
    )
    assert len(set(actual.values())) == min(g, n)


@pytest.mark.parametrize(
    "field,value",
    [
        ("sims_per_gpu", 0),
        ("sims_per_gpu", 9),
        ("max_infer_batch_size", 9),
        ("batch_wait_ms", 0),
        ("batch_wait_ms", 1001),
        ("execution_profile", "unknown"),
    ],
)
def test_profile_bounds_fail_closed_without_source_or_runtime(tmp_path, field, value):
    path, cfg = config(tmp_path)
    cfg.update(execution_profile="phase_b", sims_per_gpu=2, max_infer_batch_size=2)
    cfg[field] = value
    path.write_text(yaml.safe_dump(cfg))
    with pytest.raises(ValueError):
        resolve(["dry-run", "--config", str(path)])


def test_optin_batch_preview_does_not_read_model_or_probe_GPU_and_legacy_default_stays_m1(
    tmp_path, capsys
):
    path, cfg = config(tmp_path)
    cfg.update(execution_profile="phase_b", sims_per_gpu=2, max_infer_batch_size=2)
    Path(cfg["checkpoint"], "model/.metadata").write_bytes(
        b"not real DCP; dry-run cannot inspect"
    )
    path.write_text(yaml.safe_dump(cfg))
    assert main(["dry-run", "--config", str(path)]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["models_loaded"] == data["environments_created"] == 0
    assert (
        data["resolved"]["sims_per_gpu"]
        == data["resolved"]["max_infer_batch_size"]
        == 2
    )
    cfg["execution_profile"] = "phase_a"
    path.write_text(yaml.safe_dump(cfg))
    with pytest.raises(ValueError, match="Phase A"):
        resolve(["dry-run", "--config", str(path)])


@pytest.mark.parametrize(
    "change", ["gpu_ids", "sims_per_gpu", "max_infer_batch_size", "batch_wait_ms"]
)
def test_each_execution_layout_field_changes_manifest_and_cannot_silently_resume(
    change,
):
    m = manifest()
    cfg = dict(
        execution_profile="phase_b",
        gpu_ids=[4],
        sims_per_gpu=2,
        max_infer_batch_size=2,
        batch_wait_ms=20,
    )

    def create(c):
        return build_manifest(
            tasks=m["tasks"],
            episodes=m["episodes_per_task"],
            seed=m["seed"],
            horizons=m["horizons"],
            experiment=m["experiment"],
            execution=execution(c),
        )

    a = create(cfg)
    assert validate_manifest(a) == a
    cfg[change] = [5] if change == "gpu_ids" else cfg[change] + 1
    b = create(cfg)
    assert b["digest"] != a["digest"]
    assert "execution" not in m


def test_runtime_cannot_reinterpret_old_manifest_as_batch_profile(tmp_path):
    from cosmos_framework.evaluation.robocasa_v2.store import Store
    from robocasa_eval_v2.runtime import Runtime

    value = Store(tmp_path / "not-created", manifest())
    cfg = dict(
        execution_profile="phase_b",
        gpu_ids=[4],
        sims_per_gpu=2,
        max_infer_batch_size=2,
        batch_wait_ms=20,
    )
    with pytest.raises(ValueError, match="execution profile"):
        Runtime(value, cfg, {}, {})
    assert not value.root.exists()
