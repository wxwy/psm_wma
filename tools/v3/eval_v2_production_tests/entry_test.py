"""Production CLI/identity/resource gates, tiny readonly model fixture only."""

import json
import pickle
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from cosmos_framework.evaluation.robocasa_v2.contract import build_manifest
from cosmos_framework.evaluation.robocasa_v2.store import Store
from robocasa_episode_resume.model_identity import build_model_identity
from robocasa_eval_v2.cli import main
from robocasa_eval_v2.config import resolve
from robocasa_eval_v2.identity import discover
from robocasa_eval_v2.resources import check

from tools.v3.eval_v2_production_tests.store_test import close_streams, complete


def config(tmp_path):
    inp = tmp_path / "inputs"
    inp.mkdir()
    model = inp / "checkpoint/model"
    model.mkdir(parents=True)
    (model / ".metadata").write_bytes(pickle.dumps(None))
    with zipfile.ZipFile(model / "rank0.distcp", "w") as z:
        z.writestr("fake", b"CPU synthetic container, not a real DCP")
    (inp / "model.yaml").write_text("raw_action_dim: 15\n")
    metadata = inp / "dataset/CloseFridge/lerobot/extras/dataset_meta.json"
    metadata.parent.mkdir(parents=True)
    metadata.write_text(
        json.dumps({"env_args": {"env_name": "CloseFridge", "env_kwargs": {}}})
    )
    (inp / "vendor.lock").write_bytes(
        (
            Path(__file__).resolve().parents[3]
            / "third_party/robosuite_patches/vendor.lock.json"
        ).read_bytes()
    )
    data = {
        "schema": "psm_robocasa_eval_v2",
        "checkpoint": str(model.parent),
        "config_file": str(inp / "model.yaml"),
        "dataset_root": str(inp / "dataset"),
        "vendor_lock": str(inp / "vendor.lock"),
        "output_dir": str(tmp_path / "out"),
        "server_python": sys.executable,
        "sim_python": sys.executable,
        "gpu_ids": [4],
        "tasks": ["CloseFridge"],
        "episodes_per_task": 2,
    }
    path = tmp_path / "eval.yaml"
    path.write_text(yaml.safe_dump(data))
    return path, data


def fake_prepare(cfg, *, cache, anchor=None, manifest=None):
    tasks = discover(cfg)
    model = build_model_identity(
        checkpoint=Path(cfg["checkpoint"]),
        num_steps=cfg["prediction_steps"],
        action_horizon=16,
        guidance=cfg["guidance"],
    )
    m = build_manifest(
        tasks=[t for t, _ in tasks],
        episodes=cfg["episodes_per_task"],
        seed=cfg["seed"],
        horizons={t: 2 for t, _ in tasks},
        experiment={
            "model_digest": model["digest"],
            "config_sha256": "2" * 64,
            "runtime_digest": "3" * 64,
            "root_sha": "a" * 40,
            "child_sha": "b" * 40,
            "task_metadata": {t: "4" * 64 for t, _ in tasks},
        },
    )
    if manifest is not None and m != manifest:
        raise ValueError("immutable identity changed")
    return (
        m,
        {
            "model": model,
            "actual_root": "a" * 40,
            "tasks": dict((t, str(d)) for t, d in tasks),
        },
        {},
    )


class CpuRuntime:
    starts = 0

    def __init__(self, store, cfg, inputs, environment):
        self.store = store

    def run(self):
        for task in self.store.manifest["tasks"]:
            if len(self.store.rows(task)) == self.store.manifest["episodes_per_task"]:
                continue
            CpuRuntime.starts += 1
            self.store.begin_task(task)
            for ep in range(self.store.manifest["episodes_per_task"]):
                if self.store.slot(task, ep)["result"] is None:
                    complete(self.store, task, ep, success=ep % 2 == 0)
            close_streams(self.store, task)
        return self.store.publish_views(), None


def test_dry_run_real_entry_prints_episode_major_plan_without_checkpoint_reads_or_runtime(
    tmp_path, capsys
):
    path, cfg = config(tmp_path)
    Path(cfg["checkpoint"], "model", ".metadata").write_bytes(
        b"bad but dry-run must not inspect model"
    )
    assert main(["dry-run", "--config", str(path)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["slots"] == [["CloseFridge", 0], ["CloseFridge", 1]]
    assert payload["models_loaded"] == payload["environments_created"] == 0
    assert not Path(cfg["output_dir"]).exists()


def test_fresh_then_resume_valid_success_and_failure_reuse_real_cli_store(
    tmp_path, capsys
):
    path, cfg = config(tmp_path)
    CpuRuntime.starts = 0
    assert (
        main(
            ["fresh", "--config", str(path)],
            prepare_inputs=fake_prepare,
            runtime_type=CpuRuntime,
        )
        == 0
    )
    before = {
        str(p): p.read_bytes()
        for p in Path(cfg["output_dir"]).glob("tasks/*/episodes/*/result.json")
    }
    assert (
        main(
            ["resume", "--config", str(path)],
            prepare_inputs=fake_prepare,
            runtime_type=CpuRuntime,
        )
        == 0
    )
    assert CpuRuntime.starts == 1
    assert {
        str(p): p.read_bytes()
        for p in Path(cfg["output_dir"]).glob("tasks/*/episodes/*/result.json")
    } == before
    with pytest.raises(FileExistsError):
        main(
            ["fresh", "--config", str(path)],
            prepare_inputs=lambda **k: pytest.fail(
                "must reject namespace before preflight"
            ),
        )


def test_config_and_resource_gates_no_protected_writes(tmp_path):
    path, cfg = config(tmp_path)
    cfg["output_dir"] = str(Path(cfg["config_file"]).parent / "inside_training_job")
    path.write_text(yaml.safe_dump(cfg))
    with pytest.raises(ValueError, match="overlaps"):
        resolve(["fresh", "--config", str(path)])

    def nvml(args, **kwargs):
        if "index,uuid,memory.total,memory.used" in args[1]:
            text = "4, GPU-cpu, 81920, 1000\n"
        else:
            text = "GPU-cpu, 987654\n"
        return SimpleNamespace(stdout=text)

    with pytest.raises(RuntimeError, match="foreign process"):
        check(
            {"gpu_ids": [4], "max_gpu_fraction": 0.85, "max_rss_bytes": 10**9}, run=nvml
        )


def test_owner_skip_release_is_separate_explicit_command_not_resume(tmp_path, capsys):
    path, cfg = config(tmp_path)
    _, cfg = resolve(["fresh", "--config", str(path)])
    m, inputs, env = fake_prepare(cfg, cache=tmp_path)
    s = Store(Path(cfg["output_dir"]), m)
    s.create()
    with s.locked():
        s.begin_task("CloseFridge")
        a = s.begin_episode("CloseFridge", 0)
        for _ in range(4):
            s.begin_initialization(a)
            s.initialization_outcome(
                a, error=ValueError("bad reset"), stage="reset", safe_to_retry=True
            )
        close_streams(s, "CloseFridge")
    permit = {
        "schema": "psm_eval_v2_owner_release_v1",
        "approved_by": "Owner",
        "owner_decision_ref": "CPU synthetic explicit release",
        "manifest_digest": m["digest"],
        "slots": [{"task": "CloseFridge", "episode": 0}],
    }
    file = tmp_path / "owner.json"
    file.write_text(json.dumps(permit))
    with pytest.raises(ValueError, match="separate authorize"):
        resolve(["resume", "--config", str(path), "--owner-decision", str(file)])
    assert (
        main(["authorize", "--config", str(path), "--owner-decision", str(file)]) == 0
    )
    assert s._permit("CloseFridge", 0)["owner_ref"].startswith(
        "CPU synthetic explicit release"
    )
    assert not s.rows("CloseFridge")


def test_runtime_failure_still_persists_non_success_summary(tmp_path, capsys):
    path, cfg = config(tmp_path)

    class Failure:
        def __init__(self, *a):
            pass

        def run(self):
            raise RuntimeError("CPU synthetic resource gate failure")

        def close(self):
            pass

    assert (
        main(
            ["fresh", "--config", str(path)],
            prepare_inputs=fake_prepare,
            runtime_type=Failure,
        )
        == 1
    )
    report = json.loads((Path(cfg["output_dir"]) / "summary.json").read_text())
    assert report["sr"] is None and not report["results_qualified"]
    assert (Path(cfg["output_dir"]) / "_internal/last_failure.json").is_file()


def test_fresh_preflight_import_cache_cannot_adopt_output_namespace(tmp_path):
    path, cfg = config(tmp_path)
    caches = []

    def writing_preflight(cfg, *, cache, **kwargs):
        caches.append(Path(cache))
        assert not Path(cfg["output_dir"]).exists()
        (cache / "numba").mkdir(parents=True)
        (cache / "numba" / "import.cache").write_bytes(b"synthetic import cache")
        return fake_prepare(cfg, cache=cache, **kwargs)

    assert (
        main(
            ["fresh", "--config", str(path)],
            prepare_inputs=writing_preflight,
            runtime_type=CpuRuntime,
        )
        == 0
    )
    assert len(caches) == 1 and not caches[0].exists()
    assert (Path(cfg["output_dir"]) / "manifest.json").is_file()


def test_dry_run_existing_valid_Core_only_skips_and_never_rewrites(tmp_path, capsys):
    path, cfg = config(tmp_path)
    main(
        ["fresh", "--config", str(path)],
        prepare_inputs=fake_prepare,
        runtime_type=CpuRuntime,
    )
    capsys.readouterr()
    before = {
        str(p): p.read_bytes()
        for p in Path(cfg["output_dir"]).rglob("*")
        if p.is_file()
    }
    assert main(["dry-run", "--config", str(path)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert all(x["action"] == "skip_valid" for x in payload["resume_dispositions"])
    assert before == {
        str(p): p.read_bytes()
        for p in Path(cfg["output_dir"]).rglob("*")
        if p.is_file()
    }


def test_real_preflight_cache_warm_zero_model_reads_and_config_drift_refused(
    tmp_path, monkeypatch
):
    from cosmos_framework.evaluation.robocasa_v2.contract import digest
    from cosmos_framework.evaluation.robocasa_v2.store import write
    from robocasa_episode_resume.model_identity import verification_record
    from robocasa_eval_v2 import identity

    path, cfg = config(tmp_path)
    _, cfg = resolve(["fresh", "--config", str(path)])
    monkeypatch.setattr(
        identity, "verify_source", lambda *a: ("a" * 40, "b" * 40, "a" * 40)
    )
    monkeypatch.setattr(
        identity,
        "collect_runtime",
        lambda **kw: {
            "evaluation_runtime": {
                "digest": "3" * 64,
                "protocol": {"official_horizons": {"CloseFridge": 2}},
            },
            "runtime_probe_evidence": {},
        },
    )
    m, inputs, env = identity.prepare(cfg, cache=tmp_path / "cache")
    s = Store(Path(cfg["output_dir"]), m)
    s.create()
    with s.locked():
        write(s.root / "_internal/run_inputs.json", inputs)
        write(
            s.root / "_internal/verification_cache.json",
            verification_record(
                inputs["model"], run_root=s.root, anchor_sha256=digest(inputs)
            ),
        )
        _, warm, _ = identity.prepare(
            cfg, cache=tmp_path / "cache", anchor=inputs, manifest=m
        )
        assert warm["model"]["checkpoint_read_telemetry"]["cache_hit"] is True
        assert warm["model"]["checkpoint_read_telemetry"]["bytes_read"] == 0
        Path(cfg["config_file"]).write_text("raw_action_dim: 32\n")
        with pytest.raises(ValueError, match="identity changed"):
            identity.prepare(cfg, cache=tmp_path / "cache", anchor=inputs, manifest=m)
