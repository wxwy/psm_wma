"""Configuration -> real server argv/options -> actor effective spool settings."""
# ruff: noqa: F811 -- pytest resolves imported fixture names in parameters.

import ast
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from cosmos_framework.evaluation.robocasa_v2.contract import (
    build_manifest,
    validate_manifest,
)
from cosmos_framework.evaluation.robocasa_v2.store import Store, load
from cosmos_framework.inference import robocasa_session_transactions as session
from cosmos_framework.inference.g2_cache_budget import CacheBudget
from robocasa_eval_v2 import identity, runtime
from robocasa_eval_v2.cli import main
from robocasa_eval_v2.config import DEFAULTS, execution, rendering, resolve

from g2.latent_cache.batch_contract import ENCODER_SCHEMA, NUMERICS, make_batch_recipe
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
from tools.v3.eval_v2_streaming_tests.capacity_test import streaming_config


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


@pytest.mark.parametrize("r07", [False, True])
def test_g2_r1_configuration_binds_profile_recipe_and_native_source(
    tmp_path, capsys, r07
):
    path, cfg = config(tmp_path)
    recipe = tmp_path / "recipe.json"
    recipe.write_text("{}")
    cfg.update(
        execution_profile="phase_b",
        gpu_ids=[4],
        render_backend="egl",
        g2_profile="g2_r1",
        g2_run_recipe=str(recipe),
        g2_checkpoint_metadata_sha256="a" * 64,
        g2_actor_options={
            "nav_checkout": str(tmp_path / "nav"),
            "nav_revision": "b" * 40,
            "ros_setup": str(tmp_path / "devel/setup.bash"),
            "scratch_root": str(tmp_path / "scratch"),
        },
    )
    if r07:
        cfg.update(streaming_config(sims_per_gpu=16, render_gpu_ids=[4, 5]))
    path.write_text(yaml.safe_dump(cfg))
    _, resolved = resolve(["dry-run", "--config", str(path)])
    bound = identity.g2_experiment(resolved)
    assert bound["profile"] == "g2_r1"
    assert bound["cache_budget"] == vars(CacheBudget())
    assert resolved["g2_actor_options"]["render_f27"] is False
    assert bound["checkpoint_metadata_sha256"] == "a" * 64
    assert (
        bound["run_recipe_sha256"]
        == "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a"
    )
    assert identity.g2_experiment({}) is None
    manifest = build_manifest(
        tasks=["CloseFridge"],
        episodes=cfg["episodes_per_task"],
        seed=resolved["seed"],
        horizons={"CloseFridge": 2},
        execution=execution(resolved),
        rendering=rendering(resolved),
        experiment={
            "model_digest": "1" * 64,
            "config_sha256": "2" * 64,
            "runtime_digest": "3" * 64,
            "root_sha": "a" * 40,
            "child_sha": "b" * 40,
            "task_metadata": {"CloseFridge": "4" * 64},
            "g2": bound,
        },
    )
    Store(Path(cfg["output_dir"]), manifest).create()
    assert main(["dry-run", "--config", str(path)]) == 0
    preview = json.loads(capsys.readouterr().out)
    assert preview["models_loaded"] == preview["environments_created"] == 0
    if r07:
        assert len(preview["physical_slots"]) == 32
        assert preview["used_gpus"] == [6, 7]
        assert manifest["execution"]["max_infer_batch_size"] == 8
        assert preview["render_slots"] == {
            slot: {6: 4, 7: 5}[gpu] for slot, gpu in preview["physical_slots"].items()
        }
        assert list(preview["render_slots"].values()).count(4) == 16
        assert list(preview["render_slots"].values()).count(5) == 16
        with pytest.raises(ValueError, match="differs from frozen Run"):
            main(["dry-run", "--config", str(path), "--max-infer-batch-size", "4"])
    recipe.write_text('{"changed":true}')
    with pytest.raises(ValueError, match="differs from frozen Run"):
        main(["dry-run", "--config", str(path)])
    assert (
        identity.g2_experiment(resolved)["run_recipe_sha256"]
        != bound["run_recipe_sha256"]
    )
    path.write_text(
        yaml.safe_dump(
            {**cfg, "g2_actor_options": {**cfg["g2_actor_options"], "render_f27": True}}
        )
    )
    _, diagnostics = resolve(["dry-run", "--config", str(path)])
    assert diagnostics["g2_actor_options"]["render_f27"] is True
    assert (
        identity.g2_experiment(diagnostics)["actor_options_sha256"]
        != bound["actor_options_sha256"]
    )
    osmesa = yaml.safe_load(path.read_text())
    osmesa["render_gpu_ids"] = None
    path.write_text(yaml.safe_dump(osmesa))
    with pytest.raises(ValueError, match="G2 F27"):
        resolve(["dry-run", "--config", str(path), "--render-backend", "osmesa"])
    for invalid in (
        {"g2_profile": "legacy"},
        {"local_memory_mode": "off"},
        {"guidance": 1.5},
        {"g2_actor_options": {**cfg["g2_actor_options"], "render_f27": "true"}},
    ):
        path.write_text(yaml.safe_dump({**cfg, **invalid}))
        with pytest.raises(ValueError, match="G2"):
            resolve(["dry-run", "--config", str(path)])


def test_r2_uses_the_same_r07_capacity_and_binds_the_trained_view_recipe(
    tmp_path, capsys
):
    path, cfg = config(tmp_path)
    view_recipe = make_batch_recipe(
        dict(
            schema=ENCODER_SCHEMA,
            numerics=NUMERICS,
            max_batch_size=32,
            test_only=False,
            legacy_loader={"device": "cuda:0"},
        )
    )
    view_path = tmp_path / "view_recipe.json"
    view_path.write_text(json.dumps(view_recipe))
    weights = tmp_path / "view_weights.pth"
    weights.touch()
    run = tmp_path / "r2_recipe.json"
    record = dict(
        training={"profile": "R2"},
        global_memory={"enabled": True, "top_view_variant": "with_robot"},
        view_recipe_id=view_recipe["recipe_id"],
    )
    run.write_text(json.dumps(record))
    cfg.update(streaming_config(sims_per_gpu=16, render_gpu_ids=[4, 5]))
    cfg.update(
        g2_profile="g2_r2",
        g2_run_recipe=str(run),
        g2_checkpoint_metadata_sha256="a" * 64,
        g2_view_vae_recipe=str(view_path),
        g2_view_vae_weights=str(weights),
        g2_actor_options={
            "nav_checkout": str(tmp_path / "nav"),
            "nav_revision": "b" * 40,
            "ros_setup": str(tmp_path / "devel/setup.bash"),
            "scratch_root": str(tmp_path / "scratch"),
            "render_f27": True,
        },
    )
    path.write_text(yaml.safe_dump(cfg))
    assert main(["dry-run", "--config", str(path)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["used_gpus"] == [6, 7]
    assert len(result["physical_slots"]) == 32
    assert result["models_loaded"] == result["environments_created"] == 0
    assert (
        identity.g2_experiment(result["resolved"])["view_recipe_id"]
        == view_recipe["recipe_id"]
    )
    assert identity.g2_experiment(result["resolved"])["cache_budget"] == vars(
        CacheBudget()
    )

    with pytest.raises(ValueError, match="R2 profile"):
        path.write_text(yaml.safe_dump({**cfg, "g2_profile": "g2_r1"}))
        resolve(["dry-run", "--config", str(path)])
    path.write_text(yaml.safe_dump(cfg))
    run.write_text(json.dumps({**record, "view_recipe_id": "c" * 64}))
    with pytest.raises(ValueError, match="training job's"):
        resolve(["dry-run", "--config", str(path)])


def _r1_config(tmp_path, **changes):
    path, cfg = config(tmp_path)
    recipe = tmp_path / "recipe.json"
    recipe.write_text("{}")
    cfg.update(
        streaming_config(sims_per_gpu=8, max_infer_batch_size=4, render_gpu_ids=[4, 5])
    )
    cfg.update(
        g2_profile="g2_r1",
        g2_run_recipe=str(recipe),
        g2_checkpoint_metadata_sha256="a" * 64,
        g2_actor_options={
            "nav_checkout": str(tmp_path / "nav"),
            "nav_revision": "b" * 40,
            "ros_setup": str(tmp_path / "setup.bash"),
            "scratch_root": str(tmp_path / "scratch"),
        },
        batch_wait_ms=120,
    )
    cfg.update(changes)
    path.write_text(yaml.safe_dump(cfg))
    return path, cfg


@pytest.mark.parametrize(
    "field,value,message",
    [
        ("g2_cache_gpu_bytes", (16 << 30) + 1, "per-device owned"),
        ("g2_cache_cpu_bytes", 9 << 30, "owned RSS limit"),
        ("g2_cache_max_sessions", 7, "assigned per-Policy slots"),
        ("g2_cache_max_entries", True, "bounded integer"),
        ("g2_cache_handles", None, "bounded integer"),
        ("g2_profile", "legacy", "explicit G2 profile"),
    ],
)
def test_g2_budget_admission_is_bounded_before_spawn(tmp_path, field, value, message):
    path, _ = _r1_config(tmp_path, g2_cache_handles=1024)
    cfg = yaml.safe_load(path.read_text())
    cfg[field] = value
    path.write_text(yaml.safe_dump(cfg))
    with pytest.raises(ValueError, match=message):
        resolve(["dry-run", "--config", str(path)])


def test_formal_r1_uses_120ms_and_prior_manifests_remain_readable(tmp_path):
    from tools.v3.eval_v2_production_tests.contract_test import manifest

    path, raw = _r1_config(tmp_path, tasks="all", episodes_per_task=50)
    del raw["batch_wait_ms"]
    path.write_text(yaml.safe_dump(raw))
    _, cfg = resolve(["dry-run", "--config", str(path)])
    assert cfg["batch_wait_ms"] == 120
    with pytest.raises(ValueError, match="formal G2 R1.*120"):
        resolve(["dry-run", "--config", str(path), "--batch-wait-ms", "119"])
    old = manifest(tasks=identity.ATOMIC_TASKS, episodes=50)
    frozen = dict(
        tasks=old["tasks"],
        episodes=50,
        seed=old["seed"],
        horizons=old["horizons"],
        formal=True,
        experiment={**old["experiment"], "g2": identity.g2_experiment(cfg)},
        execution=execution(cfg),
    )
    assert (
        validate_manifest(build_manifest(**frozen))["execution"]["batch_wait_ms"] == 120
    )
    frozen["execution"]["batch_wait_ms"] = 20
    with pytest.raises(ValueError, match="formal G2 R1.*120"):
        build_manifest(**frozen)
    del frozen["experiment"]["g2"]["cache_budget"]
    prior = build_manifest(**frozen)
    assert validate_manifest(prior) == prior


def test_g2_budget_yaml_manifest_policy_argv_and_info_round_trip(tmp_path, monkeypatch):
    import requests
    from cosmos_framework.inference.g2_policy_conditions_test import FixtureHooks
    from cosmos_framework.scripts import action_policy_server_robocasa as policy

    from tools.v3.eval_v2_production_tests.contract_test import manifest

    limits = dict(
        g2_cache_max_sessions=12,
        g2_cache_max_entries=112,
        g2_cache_cpu_bytes=3 << 28,
        g2_cache_gpu_bytes=1 << 30,
        g2_cache_handles=6000,
    )
    path, _ = _r1_config(tmp_path, **limits)
    _, cfg = resolve(["dry-run", "--config", str(path)])
    old = manifest(episodes=cfg["episodes_per_task"])
    g2 = identity.g2_experiment(cfg)
    bound = build_manifest(
        tasks=old["tasks"],
        episodes=old["episodes_per_task"],
        seed=old["seed"],
        horizons=old["horizons"],
        experiment={**old["experiment"], "g2": g2},
        execution=execution(cfg),
    )
    assert g2["cache_budget"] == vars(CacheBudget(12, 112, 3 << 28, 1 << 30, 6000))
    store = Store(Path(cfg["output_dir"]), bound)
    store.create()
    runner = runtime.Runtime(store, cfg, {}, {})
    info = {}

    def spawn(command, **_):
        args = policy.tyro_cli(
            policy.ActionServerArgs,
            args=command[3:],
            config=(
                policy.tyro.conf.OmitArgPrefixes,
                policy.tyro.conf.CascadeSubcommandArgs,
                policy.tyro.conf.OmitSubcommandPrefixes,
            ),
        )
        tx = policy._transaction_options(args)
        obj = policy.ActionModelService.__new__(policy.ActionModelService)
        obj.g2_native_authority = SimpleNamespace(
            hooks=lambda _: FixtureHooks(), versions=g2
        )
        obj.model = None
        obj._configure_g2_conditions(args)
        info.update(
            g2_conditions=obj._g2_info(),
            session_transactions=dict(
                enabled=True,
                local_memory_mode=args.local_memory_mode,
                execution_profile="session_native_batch_v1",
                run_lease=tx["run_lease"],
                manifest_digest=tx["manifest_digest"],
                slot_ids=list(tx["slot_ids"]),
                max_native_batch=tx["max_batch_size"],
                batch_wait_ms=tx["batch_wait_ms"],
                capacity_profile=tx["capacity_profile"],
            ),
        )
        assert tx["batch_wait_ms"] == 120 and len(tx["slot_ids"]) == 8
        return SimpleNamespace(proc=None), {}

    monkeypatch.setattr(runner, "_spawn", spawn)
    monkeypatch.setattr(runtime, "wait_server", lambda *a, **kw: info)
    monkeypatch.setattr(
        requests.Session, "get", lambda *a, **kw: SimpleNamespace(json=lambda: info)
    )
    try:
        with store.locked():
            worker = runner.workers[0]
            runner._create_server(worker)
            assert info["g2_conditions"]["cache"]["budget"] == g2["cache_budget"]
            runner._batch_telemetry(final=True)
            receipt = next(
                (store.root / "_internal/runtime").glob("g2_cache_final_*.json")
            )
            record = load(receipt)
            assert record["manifest_digest"] == bound["digest"]
            assert (
                record["servers"]["GPU6"]["g2_condition_cache"]["high_water"][
                    "active_leases"
                ]
                == 0
            )
            # The same server endpoint must reject ignored flags and missing dimensions.
            for replacement in ({}, {**g2["cache_budget"], "gpu_bytes": 256 << 20}):
                broken = {**info["g2_conditions"]["cache"], "budget": replacement}
                with pytest.raises(ValueError, match="Condition Cache budget mismatch"):
                    runner._g2_cache_report(
                        {
                            **info,
                            "g2_conditions": {**info["g2_conditions"], "cache": broken},
                        }
                    )
    finally:
        for log in runner.logs:
            log.close()
    with pytest.raises(ValueError, match="frozen manifest"):
        runtime.Runtime(store, {**cfg, "g2_cache_gpu_bytes": 2 << 30}, {}, {})


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
