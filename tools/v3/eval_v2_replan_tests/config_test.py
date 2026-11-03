"""Configuration -> real server argv/options -> actor effective spool settings."""
# ruff: noqa: F811 -- pytest resolves imported fixture names in parameters.

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from cosmos_framework.inference import robocasa_session_transactions as session
from robocasa_eval_v2 import runtime
from robocasa_eval_v2.config import DEFAULTS, resolve

from tools.v3.eval_v2_production_tests.entry_test import config
from tools.v3.eval_v2_replan_tests.support import (
    clock_kernel as clock_kernel,
)
from tools.v3.eval_v2_replan_tests.support import (
    production_function,
)
from tools.v3.eval_v2_replan_tests.support import (
    systems as systems,
)


@pytest.mark.parametrize(
    "field,value",
    [
        ("media_spool_max_jobs", True),
        ("media_spool_max_jobs", 0),
        ("media_spool_max_jobs", 65),
        ("media_spool_max_bytes", False),
        ("media_spool_max_bytes", 0),
        ("media_spool_max_bytes", 2**31 + 1),
        ("media_drain_timeout_s", False),
        ("media_drain_timeout_s", 0),
        ("media_drain_timeout_s", float("nan")),
        ("media_drain_timeout_s", float("inf")),
        ("media_drain_timeout_s", 3601),
    ],
)
def test_invalid_spool_and_deadline_rejected_before_runtime(tmp_path, field, value):
    path, cfg = config(tmp_path)
    cfg[field] = value
    path.write_text(yaml.safe_dump(cfg))
    with pytest.raises(ValueError):
        resolve(["dry-run", "--config", str(path)])


def test_defaults_and_CLI_override_record_effective_values(tmp_path):
    path, _ = config(tmp_path)
    _, cfg = resolve(["dry-run", "--config", str(path)])
    assert tuple(
        cfg[k]
        for k in (
            "media_spool_max_jobs",
            "media_spool_max_bytes",
            "media_drain_timeout_s",
        )
    ) == (4, 512 * 1024**2, 300.0)
    _, cfg = resolve(
        [
            "dry-run",
            "--config",
            str(path),
            "--media-spool-max-jobs",
            "3",
            "--media-spool-max-bytes",
            "1048576",
            "--media-drain-timeout-s",
            "30",
        ]
    )
    assert tuple(
        cfg[k]
        for k in (
            "media_spool_max_jobs",
            "media_spool_max_bytes",
            "media_drain_timeout_s",
        )
    ) == (3, 1048576, 30.0)


def test_real_server_option_parser_passes_spool_to_actor_and_info(tmp_path, systems):
    token = tmp_path / "owner"
    token.write_text("cpu-owner")
    token.chmod(0o600)
    parse = production_function(
        "_transaction_options",
        dict(
            Path=Path,
            identifier=session.identifier,
            monotonic_clock_domain=session.monotonic_clock_domain,
        ),
    )
    fields = dict(
        transaction_profile="batch",
        transaction_owner_token_file=str(token),
        transaction_run_lease="run",
        transaction_manifest_digest="a" * 64,
        transaction_slot_ids="slot0",
        transaction_slot_id=None,
        local_memory_mode="off",
        local_memory_max_sessions=1,
        action_chunk_size=16,
        transaction_max_batch_size=1,
        transaction_batch_wait_ms=20,
    )
    options = parse(SimpleNamespace(**fields))
    _, actor, _ = systems(**options)
    assert (
        actor.info()["media_spool_max_jobs"] == 4
        and actor.info()["media_spool_max_bytes"] == 512 * 1024**2
    )
    assert actor.info()["media_drain_timeout_s"] == 300
    for name, value in [
        ("media_spool_max_jobs", True),
        ("media_spool_max_bytes", 0),
        ("media_drain_timeout_s", float("nan")),
    ]:
        with pytest.raises(ValueError, match="spool/drain"):
            parse(SimpleNamespace(**fields, **{name: value}))


def test_runtime_argv_contains_settings_and_mismatched_info_rejected(
    tmp_path, monkeypatch
):
    from tools.v3.eval_v2_batch_tests.render_mapping_test import store_cfg

    store, cfg = store_cfg(tmp_path)
    cfg.update(
        save_generated_video="all",
        media_spool_max_jobs=3,
        media_spool_max_bytes=1048576,
        media_drain_timeout_s=30.0,
    )
    launches = []
    runner = runtime.Runtime(store, cfg, {}, {}, resource_probe=lambda *a, **k: None)
    monkeypatch.setattr(
        runner.registry,
        "start",
        lambda command, **kw: (
            launches.append(command) or SimpleNamespace(proc=None),
            {},
        ),
    )
    worker = runner.workers[0]
    slots = [runner.slot_ids[w] for w in runner.workers if runner.worker_gpus[w] == 4]

    def info(*a, **k):
        return {
            "session_transactions": dict(
                enabled=True,
                local_memory_mode=store.manifest["protocol"]["local_memory"],
                execution_profile="session_native_batch_v1",
                run_lease=store.lease_id,
                manifest_digest=store.manifest["digest"],
                slot_ids=slots,
                max_native_batch=cfg["max_infer_batch_size"],
                batch_wait_ms=cfg["batch_wait_ms"],
                media_spool_max_jobs=3,
                media_spool_max_bytes=1048576,
                media_drain_timeout_s=30.0,
            )
        }

    monkeypatch.setattr(runtime, "wait_server", info)
    try:
        with store.locked():
            runner._server(worker)
            argv = launches[0]
            for flag, expected in [
                ("--media-spool-max-jobs", "3"),
                ("--media-spool-max-bytes", "1048576"),
                ("--media-drain-timeout-s", "30.0"),
            ]:
                assert argv[argv.index(flag) + 1] == expected
            # A server which ignores the requested YAML must fail identity proof.
            runner.servers.clear()
            correct = info()
            correct["session_transactions"]["media_spool_max_jobs"] = 4
            monkeypatch.setattr(runtime, "wait_server", lambda *a, **k: correct)
            with pytest.raises(
                ValueError, match="media spool/drain configuration mismatch"
            ):
                runner._server(worker)
    finally:
        for log in runner.logs:
            log.close()


def test_RPC_media_wait_extension_does_not_change_prediction_Episode_deadline():
    # Check the two distinct keyword expressions in the actual coordinator AST.
    tree = ast.parse(Path(runtime.__file__).read_text())
    actor_call = next(
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == "Actor"
    )
    expr = ast.Expression(body=actor_call.args[-1])
    for mode, expected in [("none", 1800), ("first", 1800), ("all", 2100)]:
        context = {
            "self": SimpleNamespace(cfg={**DEFAULTS, "save_generated_video": mode})
        }
        assert (
            eval(compile(expr, "<production Actor deadline>", "eval"), context)
            == expected
        )
    assert "episode_deadline=deadline" in Path(runtime.__file__).read_text()
