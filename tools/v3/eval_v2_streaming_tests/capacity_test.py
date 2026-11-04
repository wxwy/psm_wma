"""Versioned M/B capacity, immutable identity and honest physical plans."""

import copy

import pytest
import yaml
from cosmos_framework.evaluation.robocasa_v2.contract import (
    STREAMING_SCHEDULE,
    STREAMING_SAMPLING,
    build_manifest,
    validate_manifest,
)
from cosmos_framework.inference.robocasa_transaction_client import (
    TransactionPolicyClient,
)
from cosmos_framework.inference.robocasa_session_transactions_test import (
    clock_kernel as clock_kernel,
)  # noqa: F401
from robocasa_eval_v2.config import execution, resolve
from robocasa_eval_v2.resources import physical_slots
from tools.v3.eval_v2_production_tests.contract_test import manifest
from tools.v3.eval_v2_production_tests.entry_test import config


def streaming_config(**updates):
    return (
        dict(
            execution_profile="phase_b",
            scheduling_protocol=STREAMING_SCHEDULE,
            gpu_ids=[6, 7],
            sims_per_gpu=32,
            max_infer_batch_size=8,
            batch_wait_ms=20,
            max_rss_bytes=16 * 1024**3,
            streaming_resources=dict(
                max_owned_gpu_bytes=16 * 1024**3,
                sim_startup_rss_bytes=1024**2,
                sim_startup_gpu_bytes=1024**2,
                server_startup_rss_bytes=1024**2,
                server_startup_gpu_bytes=1024**2,
                initialization_concurrency=32,
            ),
        )
        | updates
    )


def streaming_manifest(
    tasks=("CloseFridge",), episodes=3, cfg=None, mode="off", experiment=None
):
    old = manifest(tasks, episodes)
    return build_manifest(
        tasks=tasks,
        episodes=episodes,
        formal=len(tasks) == 18 and episodes == 50,
        seed=old["seed"],
        horizons=old["horizons"],
        experiment=experiment or old["experiment"],
        execution=execution(cfg or streaming_config()),
        local_memory=mode,
    )


@pytest.mark.parametrize("m", [1, 8, 16, 32])
@pytest.mark.parametrize("b", [1, 8, 16, 32])
def test_capacity_is_independent_and_bound_to_manifest_and_client(tmp_path, m, b):
    path, raw = config(tmp_path)
    raw.update(streaming_config(sims_per_gpu=m, max_infer_batch_size=b))
    path.write_text(yaml.safe_dump(raw))
    _, cfg = resolve(["dry-run", "--config", str(path)])
    value = streaming_manifest(cfg=cfg)
    assert validate_manifest(value) == value
    assert value["execution"]["sims_per_gpu"] == m
    assert value["execution"]["max_infer_batch_size"] == b
    assert value["protocol"]["schedule"] == STREAMING_SCHEDULE
    assert value["protocol"]["sampling"] == STREAMING_SAMPLING
    client = TransactionPolicyClient(
        "http://unused", max_batch_size=b, capacity_profile="streaming32"
    )
    assert client.max_batch_size == b
    assert len(physical_slots(cfg, 18)) == 2 * m


@pytest.mark.parametrize("field", ["sims_per_gpu", "max_infer_batch_size"])
@pytest.mark.parametrize("invalid", [0, 33, 1.5, True, "32"])
def test_invalid_capacity_rejected_before_startup(tmp_path, field, invalid):
    path, raw = config(tmp_path)
    raw.update(streaming_config(**{field: invalid}))
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(ValueError):
        resolve(["dry-run", "--config", str(path)])
    with pytest.raises(ValueError):
        streaming_manifest(cfg=raw)


def test_64_physical_slots_are_real_distinct_plan_identities_not_task_count():
    actual = physical_slots(streaming_config(), 18)
    assert len(actual) == 64 and len(set(actual)) == 64
    assert all(sum(g == gpu for g in actual.values()) == 32 for gpu in (6, 7))
    legacy = streaming_config(
        scheduling_protocol="episode_major_frozen_order_round_barrier_v1"
    )
    assert len(physical_slots(legacy, 18)) == 18


@pytest.mark.parametrize("change", ["schedule", "resources", "capacity"])
def test_new_protocol_and_budgets_cannot_reinterpret_old_resume(change):
    value = streaming_manifest()
    old = manifest()
    assert old["protocol"]["schedule"] != value["protocol"]["schedule"]
    altered = copy.deepcopy(value)
    if change == "schedule":
        altered["protocol"]["schedule"] = old["protocol"]["schedule"]
    elif change == "resources":
        altered["execution"]["resources"]["max_owned_gpu_bytes"] += 1
    else:
        altered["execution"]["sims_per_gpu"] = 8
    with pytest.raises(ValueError):
        validate_manifest(altered)


def test_streaming_requires_explicit_budgets_and_phase_b(tmp_path):
    path, raw = config(tmp_path)
    raw.update(streaming_config())
    raw["streaming_resources"] = None
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(ValueError, match="streaming_resources"):
        resolve(["dry-run", "--config", str(path)])
    raw.update(
        streaming_config(
            execution_profile="phase_a", sims_per_gpu=1, max_infer_batch_size=1
        )
    )
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(ValueError, match="Phase B"):
        resolve(["dry-run", "--config", str(path)])
