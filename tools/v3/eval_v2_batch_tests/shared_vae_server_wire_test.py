"""Actual Root server argv reaches Child strict options with configured M/B."""

from types import SimpleNamespace

import pytest

from cosmos_framework.evaluation.robocasa_v2.contract import build_manifest
from cosmos_framework.evaluation.robocasa_v2.store import Store
from cosmos_framework.inference.robocasa_session_transactions_test import (
    clock_kernel as clock_kernel,
)
from cosmos_framework.scripts.robocasa_feature_http_test import server
from robocasa_eval_v2.config import execution
from robocasa_eval_v2.runtime import Runtime
from tools.v3.eval_v2_batch_tests.shared_vae_topology_test import topology
from tools.v3.eval_v2_production_tests.contract_test import manifest
from tools.v3.eval_v2_production_tests.entry_test import config


@pytest.mark.parametrize(
    "servers,sims,batch", [(1, 1, 1), (1, 8, 8), (2, 8, 8), (3, 3, 5), (2, 32, 8)]
)
def test_original_runtime_builds_policy_argv_for_all_configured_slots_without_b1_fallback(
    tmp_path, monkeypatch, servers, sims, batch
):
    path, paths = config(tmp_path)
    cfg = topology(tmp_path, servers, sims, batch, streaming=True)
    cfg.update({k: v for k, v in paths.items() if k not in ("gpu_ids", "schema")})
    old = manifest(tasks=[f"Task{i}" for i in range(18)])
    m = build_manifest(
        tasks=old["tasks"],
        episodes=old["episodes_per_task"],
        seed=old["seed"],
        horizons=old["horizons"],
        experiment=old["experiment"],
        execution=execution(cfg),
    )
    store = Store(tmp_path / "run", m)
    store.create()
    runtime = Runtime(store, cfg, {}, {})
    launches = []

    class StopBeforeHardware(Exception):
        pass

    def capture(command, **options):
        launches.append((command, options))
        raise StopBeforeHardware()

    monkeypatch.setattr(runtime, "_spawn", capture)
    try:
        assert len(runtime.workers) == servers * sims
        with store.locked():
            for gpu in cfg["gpu_ids"]:
                worker = next(w for w, g in runtime.worker_gpus.items() if g == gpu)
                with pytest.raises(StopBeforeHardware):
                    runtime._create_server(worker)
        assert len(launches) == servers
        for command, options in launches:

            def value(flag):
                return command[command.index(flag) + 1]

            assert value("--transaction-max-batch-size") == str(batch)
            assert (
                value("--host") == "127.0.0.1"
                and value("--history-source") == "sim_shared_vae"
            )
            assert "--single-latency-arm" not in command
            args = SimpleNamespace(
                transaction_profile="batch",
                history_source="sim_shared_vae",
                local_memory_mode="required",
                single_latency_arm=None,
                transaction_slot_id=None,
                transaction_slot_ids=value("--transaction-slot-ids"),
                transaction_owner_token_file=value("--transaction-owner-token-file"),
                transaction_run_lease=value("--transaction-run-lease"),
                transaction_manifest_digest=value("--transaction-manifest-digest"),
                transaction_capacity_profile=value("--transaction-capacity-profile"),
                local_memory_max_sessions=int(value("--local-memory-max-sessions")),
                transaction_max_batch_size=int(value("--transaction-max-batch-size")),
                transaction_batch_wait_ms=int(value("--transaction-batch-wait-ms")),
                transaction_timeout_s=float(value("--transaction-timeout-s")),
                action_chunk_size=16,
            )
            accepted = server._transaction_options(args)
            assert accepted["max_batch_size"] == batch
            assert (
                len(accepted["slot_ids"]) == sims
                and accepted["capacity_profile"] == "streaming32"
            )
    finally:
        runtime.shared_vae.close()
        for log in runtime.logs:
            log.close()
