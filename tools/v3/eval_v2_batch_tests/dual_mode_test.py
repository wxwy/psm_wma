"""Public CLI identity and real OS No-TTT Sim/Server paths; no GPU/assets."""
# ruff: noqa: F811 -- imported pytest fixture names are resolved by pytest.

import json

import pytest
import yaml
from cosmos_framework.evaluation.robocasa_v2.contract import validate_manifest
from cosmos_framework.evaluation.robocasa_v2.scheduler import logical_plan
from cosmos_framework.evaluation.robocasa_v2.store import records
from cosmos_framework.inference.robocasa_session_transactions_test import (
    clock_kernel as clock_kernel,
)
from robocasa_eval_v2 import identity
from robocasa_eval_v2.config import resolve
from robocasa_eval_v2.runtime import Runtime
from robocasa_eval_v2_processes import process_identity
from tools.v3.eval_v2_batch_tests.runtime_test import cpu_run
from tools.v3.eval_v2_production_tests.runtime_evidence_test import (
    core_bytes,
    public,
)

from tools.v3.eval_v2_production_tests.runtime_evidence_test import (
    real_prepare as real_prepare,
)  # noqa: F401, F811


@pytest.mark.parametrize("mode", ["off", "required"])
def test_public_CLI_Fresh_Resume_immutable_mode_identity(
    real_prepare, monkeypatch, mode
):
    case = real_prepare
    case.cfg.update(
        execution_profile="phase_b",
        sims_per_gpu=2,
        max_infer_batch_size=2,
        local_memory_mode=mode,
    )
    case.path.write_text(yaml.safe_dump(case.cfg))
    monkeypatch.setattr(
        identity, "clock_environment", lambda *a: {"domain": "CPU-double"}
    )
    assert public(case, "fresh") == 0
    manifest = json.loads((case.root / "manifest.json").read_bytes())
    assert manifest["protocol"]["local_memory"] == mode
    assert validate_manifest(manifest) == manifest
    original = core_bytes(case.root)
    anchor = (case.root / "_internal/run_inputs.json").read_bytes()
    assert public(case, "resume") == 0
    assert core_bytes(case.root) == original
    assert (case.root / "_internal/run_inputs.json").read_bytes() == anchor
    case.cfg["local_memory_mode"] = "required" if mode == "off" else "off"
    case.path.write_text(yaml.safe_dump(case.cfg))
    with pytest.raises(ValueError, match="immutable"):
        public(case, "resume")
    assert core_bytes(case.root) == original
    assert (case.root / "_internal/run_inputs.json").read_bytes() == anchor


@pytest.mark.parametrize("mode", [None, "auto", True, "none"])
def test_unknown_mode_never_silently_falls_back(real_prepare, mode):
    real_prepare.cfg["local_memory_mode"] = mode
    real_prepare.path.write_text(yaml.safe_dump(real_prepare.cfg))
    with pytest.raises(ValueError, match="mode"):
        resolve(["dry-run", "--config", str(real_prepare.path)])


def test_real_OS_NoTTT_two_Sim_B2_Common_Session_D5_Resume_cleanup(
    tmp_path, monkeypatch
):
    store, cfg, runtime, report, error = cpu_run(
        tmp_path, monkeypatch, local_memory_mode="off"
    )
    if error is not None:
        pytest.fail(
            str(error)
            + "\n"
            + "\n".join(
                p.read_text()[-8000:] for p in (store.root / "logs").glob("*.log")
            )
        )
    assert report["valid"] == 4 and report["results_qualified"]
    processes = records(store.root / "_internal/processes")
    assert sum(p["kind"] == "server" for p in processes) == 1
    assert sum(p["kind"].startswith("simulator_slot:") for p in processes) == 2
    for p in processes:
        assert (store.root / "_internal/process_closed" / (p["id"] + ".json")).exists()
        assert process_identity(p["identity"]["pid"]) is None
    calls = [
        json.loads(s.removeprefix("CPU_NATIVE_BATCH "))
        for p in (store.root / "logs").glob("*_server.log")
        for s in p.read_text().splitlines()
        if s.startswith("CPU_NATIVE_BATCH ")
    ]
    assert any(c["size"] == 2 for c in calls) and sum(c["size"] for c in calls) == 8
    assert all(c["prefix_present"] == [] for c in calls)
    predictions = [
        json.loads(s)
        for p in store.root.glob("tasks/*/episodes/*/predictions.jsonl")
        for s in p.read_text().splitlines()
    ]
    assert len(predictions) == 8 and all(p["local_memory"] is None for p in predictions)
    assert all(
        p["transaction"]["protocol"] == "robocasa.session-transactions.no-ttt.v1"
        for p in predictions
    )
    first = [p for p in predictions if p["source_step"] == 0]
    assert len({p["transaction"]["assignment"]["session_id"] for p in first}) == 4
    rows = records(next((store.root / "_internal/scheduler").iterdir()))
    assert [
        (x["data"]["task"], x["data"]["episode"])
        for x in rows
        if x["kind"] == "DISPATCH"
    ] == logical_plan(store.manifest)
    assert sum(x["kind"] == "ROUND_BARRIER" for x in rows) == 2
    original = core_bytes(store.root)
    resumed = Runtime(
        store,
        cfg,
        runtime.inputs,
        runtime.environment,
        resource_probe=lambda *a, **k: None,
    )
    with store.locked():
        report, error = resumed.run()
    assert error is None and report["valid"] == 4 and core_bytes(store.root) == original
    assert not resumed.actors and not resumed.servers


@pytest.mark.parametrize(
    "damage", ["protocol", "assignment", "Local_status", "Local_action", "End"]
)
def test_NoTTT_Core_commit_and_read_reject_wrong_mode_or_unproven_Session(
    tmp_path, damage
):
    from cosmos_framework.evaluation.robocasa_v2.contract import build_manifest
    from cosmos_framework.evaluation.robocasa_v2.store import Store
    from tools.v3.eval_v2_production_tests.contract_test import manifest, record
    from tools.v3.eval_v2_production_tests.store_test import admitted, fixture_core

    base = manifest(episodes=1)
    value = Store(
        tmp_path / "run",
        build_manifest(
            tasks=base["tasks"],
            episodes=1,
            seed=base["seed"],
            horizons=base["horizons"],
            experiment=base["experiment"],
            local_memory="off",
        ),
    )
    value.create()

    def corrupt(directory):
        if damage in ("protocol", "assignment", "Local_status"):
            path = directory / "predictions.jsonl"
            events = [json.loads(line) for line in path.read_text().splitlines()]
            if damage == "protocol":
                events[0]["transaction"]["protocol"] = (
                    "robocasa.session-transactions.b1.v1"
                )
            elif damage == "assignment":
                events[0]["transaction"]["assignment"]["attempt_id"] = "foreign"
            else:
                events[0]["local_memory"] = {"prefix_present": False}
            raw = path.read_bytes()
            path.write_text("".join(json.dumps(event) + "\n" for event in events))
        elif damage == "Local_action":
            path = directory / "actions.jsonl"
            events = [json.loads(line) for line in path.read_text().splitlines()]
            events[0]["canonical_executed_raw15"] = [0.0] * 15
            raw = path.read_bytes()
            path.write_text("".join(json.dumps(event) + "\n" for event in events))
        else:
            path = directory / "local_memory.json"
            event = json.loads(path.read_bytes())
            event["reset_ok"] = False
            raw = path.read_bytes()
            path.write_text(json.dumps(event))
        return path, raw

    with value.locked():
        value.begin_task("CloseFridge")
        attempt = admitted(value, value.begin_episode("CloseFridge", 0))
        row = record(value.manifest, {**attempt, "reset_index": 0}, 0)
        staging = fixture_core(value, attempt, row)
        path, raw = corrupt(staging)
        with pytest.raises(ValueError, match="No-TTT|action evidence|acknowledgement"):
            value.commit(row, staging=staging)
        assert not (value._slot("CloseFridge", 0) / "result.json").exists()
        path.write_bytes(raw)
        value.commit(row, staging=staging)
        public_dir = value._slot("CloseFridge", 0)
        assert value._result("CloseFridge", 0) == row
        path, raw = corrupt(public_dir)
        with pytest.raises(ValueError, match="No-TTT|action evidence|acknowledgement"):
            value._result("CloseFridge", 0)
        path.write_bytes(raw)
        assert value._result("CloseFridge", 0) == row
