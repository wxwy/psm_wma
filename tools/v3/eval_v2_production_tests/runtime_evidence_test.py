"""Public Fresh/Resume runtime evidence with real identity hashing and Store.

Vendor/interpreter probes and physics/model execution are explicit CPU doubles.
The real prepare/verify_source/model-header/hash/cache/CLI/Store algorithms run;
source verification uses two tiny real Git repositories, never a disabled guard.
"""

import errno
import hashlib
import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from cosmos_framework.evaluation.robocasa_v2 import store as store_module
from cosmos_framework.evaluation.robocasa_v2.contract import canonical, digest
from cosmos_framework.simulation.robocasa.closed_loop_eval import verify_runtime
from robocasa_eval_v2 import cli, identity, resources
from robocasa_eval_v2.runtime import Runtime

from tools.v3.eval_v2_production_tests.entry_test import CpuRuntime, config

MIB = 1024 * 1024


def git(repo, *args):
    return subprocess.check_output(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.name=CPU identity fixture",
            "-c",
            "user.email=cpu-fixture@example.invalid",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        text=True,
    ).strip()


@pytest.fixture
def real_prepare(tmp_path, monkeypatch):
    path, cfg = config(tmp_path)
    source = tmp_path / "mini-source"
    child = source / "cosmos-framework"
    child.mkdir(parents=True)
    git(child, "init", "-q")
    (child / "source.py").write_text("# Synthetic Child provenance sentinel.\n")
    git(child, "add", "source.py")
    git(child, "commit", "-qm", "CPU Child source")
    git(source, "init", "-q")
    for name in ("scripts", "configs", "third_party/robosuite_patches"):
        (source / name).mkdir(parents=True, exist_ok=True)
    (source / "scripts/source.py").write_text("# Synthetic Root provenance sentinel.\n")
    (source / "configs/source.yaml").write_text("cpu_fixture: true\n")
    (source / "third_party/robosuite_patches/vendor.lock.json").write_bytes(
        Path(cfg["vendor_lock"]).read_bytes()
    )
    git(source, "add", "scripts", "configs", "third_party")
    git(
        source,
        "update-index",
        "--add",
        "--cacheinfo",
        "160000",
        git(child, "rev-parse", "HEAD"),
        "cosmos-framework",
    )
    git(source, "commit", "-qm", "CPU Root source and exact Child Gitlink")
    monkeypatch.setattr(identity, "ROOT", source)
    monkeypatch.setattr(identity, "CHILD", child)
    monkeypatch.setattr(CpuRuntime, "starts", 0)
    state = SimpleNamespace(
        path=path,
        cfg=cfg,
        source=source,
        child=child,
        root=Path(cfg["output_dir"]),
        assets={"robocasa/models/assets/cpu_fixture/asset_000000.png": "0" * 64},
        warning="first CPU vendor warning",
        revision=1,
        attestations=[],
        constructed=[],
    )

    def collect(**kwargs):
        assert kwargs["tasks"] == ["CloseFridge"]
        runtime = {
            "schema": "psm_robocasa_runtime_v1",
            "synthetic_CPU_only": True,
            "protocol": {"official_horizons": {"CloseFridge": 2}},
            "packages": {"robocasa": {"untracked_asset_sha256": state.assets}},
            "revision": state.revision,
        }
        runtime["digest"] = digest(runtime)
        attestation = {
            "evaluation_runtime": runtime,
            "runtime_probe_evidence": {
                "argv": ["CPU_SYNTHETIC_VENDOR_BOUNDARY"],
                "stdout": state.warning
                + "\nPSM_RUNTIME "
                + json.dumps(runtime, sort_keys=True)
                + "\n",
                "stderr": "CPU fixture: no simulator imported\n",
                "returncode": 0,
            },
        }
        state.attestations.append(attestation)
        return attestation

    monkeypatch.setattr(identity, "collect_runtime", collect)
    monkeypatch.setattr(
        identity,
        "interpreter_libraries",
        lambda executable, environment, names: {
            n: "CPU-fixture-version" for n in names
        },
    )

    class Runtime(CpuRuntime):
        def __init__(self, store, resolved, inputs, environment):
            assert store.held
            assert inputs["runtime"] == {
                "digest": state.attestations[-1]["evaluation_runtime"]["digest"]
            }
            assert "runtime_probe_evidence" not in inputs
            assert list((store.root / "_internal/runtime_probe").glob("*.json"))
            state.constructed.append(inputs)
            super().__init__(store, resolved, inputs, environment)

    state.Runtime = Runtime
    return state


def public(case, mode, *, output=None):
    argv = [mode, "--config", str(case.path)]
    if output is not None:
        argv += ["--output-dir", str(output)]
    return cli.main(argv, prepare_inputs=identity.prepare, runtime_type=case.Runtime)


@pytest.mark.parametrize("inherited_project_paths", [False, True])
def test_g2_actor_launch_uses_the_attested_pythonpath(
    real_prepare, tmp_path, monkeypatch, inherited_project_paths
):
    case = real_prepare
    recipe = tmp_path / "recipe.json"
    recipe.write_text("{}")
    case.cfg.update(
        execution_profile="phase_b",
        render_backend="egl",
        g2_profile="g2_r1",
        g2_run_recipe=str(recipe),
        batch_wait_ms=120,
        g2_cache_gpu_bytes=1 << 30,
        g2_checkpoint_metadata_sha256=identity.sha256_file(
            Path(case.cfg["checkpoint"]) / "model/.metadata"
        ),
        g2_actor_options={
            "nav_checkout": str(tmp_path / "nav"),
            "nav_revision": "b" * 40,
            "ros_setup": str(tmp_path / "setup.bash"),
            "scratch_root": str(tmp_path / "spatial"),
        },
    )
    case.path.write_text(json.dumps(case.cfg))
    monkeypatch.setattr("eval_robocasa_18task_queue.CHILD", case.child)
    monkeypatch.setattr(identity, "clock_environment", lambda *args: {"domain": "cpu"})
    monkeypatch.setattr(
        resources,
        "gpu_identity",
        lambda gpu: {"gpu_id": gpu, "uuid": "GPU-cpu", "pci_bus_id": "0000:04:00.0"},
    )
    inherited = str(tmp_path / "other-imports")
    project = [str(case.source), str(case.child)]
    parent_paths = [project[1], inherited, *project] if inherited_project_paths else []
    expected_path = os.pathsep.join(project + ([inherited] if parent_paths else []))
    probe = tmp_path / "cpu_vendor_probe.py"
    probe.write_text(
        "import hashlib, os\n"
        "def probe_runtime(*, lock_path, asset_manifest, tasks):\n"
        "    path = os.environ.get('PYTHONPATH', '')\n"
        "    return {'digest': hashlib.sha256(path.encode()).hexdigest(),\n"
        "            'interpreter': {'pythonpath_env': path},\n"
        "            'protocol': {'official_horizons': {t: 2 for t in tasks}}}\n"
    )
    preflight = []

    def collect(*, simulation_env, tasks, **kwargs):
        path = simulation_env["PYTHONPATH"]
        preflight.append(path)
        # Fresh must move caches without rereading the parent's search path.
        monkeypatch.setenv("PYTHONPATH", "/unattested-parent-path")
        return {
            "evaluation_runtime": {
                "digest": hashlib.sha256(path.encode()).hexdigest(),
                "protocol": {"official_horizons": {task: 2 for task in tasks}},
            },
            "runtime_probe_evidence": {},
        }

    monkeypatch.setattr(identity, "collect_runtime", collect)
    launches = []

    class CapturedLaunch(Exception):
        pass

    class RuntimeProbe(CpuRuntime):
        def __init__(self, store, resolved, inputs, environment):
            super().__init__(store, resolved, inputs, environment)
            assert (
                store.manifest["experiment"]["g2"]["cache_budget"]["gpu_bytes"]
                == 1 << 30
            )
            assert store.manifest["execution"]["batch_wait_ms"] == 120
            runner = Runtime(store, resolved, inputs, environment)
            monkeypatch.setattr(runner, "_server", lambda worker: (None, {}, 8912))

            def start(command, *, env, **kwargs):
                actor = json.loads(
                    Path(command[command.index("--config") + 1]).read_text()
                )
                assert actor["settings"]["g2_profile"] == "g2_r1"
                assert env["NUMBA_CACHE_DIR"] == str(
                    case.root / "_internal/cache/numba"
                )
                args = SimpleNamespace(
                    **dict(actor["runtime_args"], runtime_probe_script=str(probe))
                )
                with monkeypatch.context() as actor_process:
                    actor_process.setenv("PYTHONPATH", env["PYTHONPATH"])
                    attested = verify_runtime(args, "CloseFridge")
                    assert (
                        attested["interpreter"]["pythonpath_env"]
                        == preflight[-1]
                        == expected_path
                    )
                    actor_process.setenv(
                        "PYTHONPATH", expected_path + os.pathsep + "/unexpected"
                    )
                    with pytest.raises(
                        ValueError, match="runtime changed after preflight"
                    ):
                        verify_runtime(args, "CloseFridge")
                launches.append(env["PYTHONPATH"])
                raise CapturedLaunch

            monkeypatch.setattr(runner, "_spawn", start)
            try:
                with pytest.raises(CapturedLaunch):
                    runner._setup_actor(
                        {"task": "CloseFridge", "physical_worker": runner.workers[0]}
                    )
            finally:
                for log in runner.logs:
                    log.close()

    case.Runtime = RuntimeProbe
    for mode in ("fresh", "resume"):
        if parent_paths:
            monkeypatch.setenv("PYTHONPATH", os.pathsep.join(parent_paths))
        else:
            monkeypatch.delenv("PYTHONPATH", raising=False)
        assert public(case, mode) == 0
    assert preflight == launches == [expected_path, expected_path]
    case.cfg["g2_cache_gpu_bytes"] = 2 << 30
    case.path.write_text(json.dumps(case.cfg))
    with pytest.raises(ValueError, match="immutable scientific protocol"):
        public(case, "resume")


def core_bytes(root):
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in root.glob("tasks/*/episodes/*/result.json")
    }


def invocations(root):
    return store_module.records(root / "_internal/invocations")


def configure_resume_r1(case, tmp_path, monkeypatch, *, episodes=2):
    recipe = tmp_path / "r1_recipe.json"
    recipe.write_text("{}")
    case.cfg.update(
        execution_profile="phase_b",
        episodes_per_task=episodes,
        render_backend="egl",
        g2_profile="g2_r1",
        g2_run_recipe=str(recipe),
        batch_wait_ms=120,
        g2_checkpoint_metadata_sha256=identity.sha256_file(
            Path(case.cfg["checkpoint"]) / "model/.metadata"
        ),
        g2_actor_options={
            "nav_checkout": str(tmp_path / "nav"),
            "nav_revision": "b" * 40,
            "ros_setup": str(tmp_path / "setup.bash"),
            "scratch_root": str(tmp_path / "spatial"),
            "render_f27": True,
        },
    )
    case.path.write_text(json.dumps(case.cfg))
    monkeypatch.setattr(identity, "clock_environment", lambda *args: {"domain": "cpu"})


@pytest.fixture
def stopped_f27_run(real_prepare, tmp_path, monkeypatch):
    case = real_prepare
    configure_resume_r1(case, tmp_path, monkeypatch)
    complete_run = case.Runtime

    class StopAfterFirstCore(complete_run):
        def run(self):
            from tools.v3.eval_v2_production_tests.store_test import (
                close_streams,
                complete,
            )

            self.store.begin_task("CloseFridge")
            complete(self.store, "CloseFridge", 0, success=False)
            close_streams(self.store, "CloseFridge")
            return self.store.publish_views(), None

    case.Runtime = StopAfterFirstCore
    assert public(case, "fresh") == 1
    case.Runtime = complete_run
    case.manifest = store_module.read(case.root / "manifest.json")
    for relative in sorted(identity.F27_RASTER_PATHS):
        path = case.source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# synthetic F27 repair\n")
    git(case.source, "add", "g2")
    git(case.source, "commit", "-qm", "reviewable F27 repair")
    case.approval = {
        "schema": "psm_eval_v2_f27_resume_approval_v1",
        "approved_by": "Owner",
        "owner_decision_ref": "CPU fixture only",
        "review_ref": "CPU fixture only",
        "manifest_digest": case.manifest["digest"],
        "from_root": case.manifest["experiment"]["root_sha"],
        "to_root": git(case.source, "rev-parse", "HEAD"),
        "child_sha": case.manifest["experiment"]["child_sha"],
    }
    case.approval_path = tmp_path / "f27_approval.json"
    case.approval_path.write_text(json.dumps(case.approval))
    return case


def approved_f27(case, mode):
    return cli.main(
        [
            mode,
            "--config",
            str(case.path),
            "--f27-resume-approval",
            str(case.approval_path),
        ],
        prepare_inputs=identity.prepare,
        runtime_type=case.Runtime,
    )


def test_f27_resume_approval_preserves_committed_failure_and_executes_missing(
    stopped_f27_run, capsys
):
    case = stopped_f27_run
    capsys.readouterr()
    old_cores = core_bytes(case.root)
    manifest = (case.root / "manifest.json").read_bytes()
    anchor = (case.root / "_internal/run_inputs.json").read_bytes()
    assert len(old_cores) == 1

    with pytest.raises(ValueError, match="production source"):
        public(case, "resume")
    assert approved_f27(case, "dry-run") == 0
    preview = json.loads(capsys.readouterr().out)
    assert [item["action"] for item in preview["resume_dispositions"]] == [
        "skip_valid",
        "execute_missing",
    ]
    assert len(invocations(case.root)) == 1

    assert approved_f27(case, "resume") == 0
    assert (case.root / "manifest.json").read_bytes() == manifest
    assert (case.root / "_internal/run_inputs.json").read_bytes() == anchor
    final_cores = core_bytes(case.root)
    assert len(final_cores) == 2 and all(
        final_cores[key] == val for key, val in old_cores.items()
    )
    _, resume = invocations(case.root)
    assert resume["f27_resume_approval"] == case.approval
    assert resume["actual_root"] == case.approval["to_root"]
    assert resume["retained_valid_cores"] == [
        {
            "task": "CloseFridge",
            "episode": 0,
            "core_digest": json.loads(next(iter(old_cores.values())))["sha256"],
        }
    ]
    assert CpuRuntime.starts == 1


@pytest.mark.parametrize(
    "drift", ["manifest", "child", "scope", "head", "dirty", "model_config", "null"]
)
def test_f27_resume_approval_does_not_accept_other_identity_drift(
    stopped_f27_run, drift
):
    case = stopped_f27_run
    old_cores = core_bytes(case.root)
    if drift == "manifest":
        case.approval["manifest_digest"] = "0" * 64
    elif drift == "child":
        case.approval["child_sha"] = "0" * 40
    elif drift == "scope":
        (case.source / "scripts/source.py").write_text("# unrelated change\n")
        git(case.source, "commit", "-qam", "unreviewed script change")
        case.approval["to_root"] = git(case.source, "rev-parse", "HEAD")
    elif drift == "head":
        git(case.source, "commit", "--allow-empty", "-qm", "another revision")
    elif drift == "dirty":
        (case.source / "g2" / "untracked.py").write_text("# unreviewed source\n")
    elif drift == "model_config":
        Path(case.cfg["config_file"]).write_text("raw_action_dim: 15\n# other config\n")
    case.approval_path.write_text(
        json.dumps(None if drift == "null" else case.approval)
    )
    with pytest.raises(ValueError):
        approved_f27(case, "resume")
    assert core_bytes(case.root) == old_cores
    assert len(invocations(case.root)) == 1


def set_gitlink(case, message):
    child = git(case.child, "rev-parse", "HEAD")
    git(case.source, "update-index", "--cacheinfo", "160000", child, "cosmos-framework")
    git(case.source, "commit", "-qm", message)
    return git(case.source, "rev-parse", "HEAD")


@pytest.fixture
def stopped_end_fairness_run(real_prepare, tmp_path, monkeypatch):
    from cosmos_framework.evaluation.robocasa_v2.scheduler import slot_disposition

    from tools.v3.eval_v2_production_tests.store_test import (
        admitted,
        close_streams,
        complete,
        healthy,
    )

    case = real_prepare
    configure_resume_r1(case, tmp_path, monkeypatch, episodes=4)
    cpu_runtime = case.Runtime
    task = "CloseFridge"

    class StopBeforeEndFairnessFix(cpu_runtime):
        def run(self):
            self.store.begin_task(task)
            complete(self.store, task, 0)
            complete(self.store, task, 1, success=False)
            failed = admitted(self.store, self.store.begin_episode(task, 2))
            self.store.finish_invalid(failed, "CPU fixture End timeout")
            close_streams(self.store, task)
            return self.store.publish_views(), None

    case.Runtime = StopBeforeEndFairnessFix
    assert public(case, "fresh") == 1
    case.manifest = store_module.read(case.root / "manifest.json")
    case.original_child = git(case.child, "rev-parse", "HEAD")
    for name in identity.END_FAIRNESS_CHILD_PATHS:
        path = case.child / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# synthetic End fairness delta\n")
    git(case.child, "add", "cosmos_framework")
    git(case.child, "commit", "-qm", "reviewed End fairness Child fixture")
    fixed_child = git(case.child, "rev-parse", "HEAD")
    pinned = set_gitlink(case, "synthetic merged #95 pin")
    approval_module = case.source / "scripts/robocasa_eval_v2/identity.py"
    approval_module.parent.mkdir()
    approval_module.write_text("# synthetic approval implementation\n")
    git(case.source, "add", "scripts")
    git(case.source, "commit", "-qm", "scoped approval implementation")
    monkeypatch.setattr(identity, "END_FAIRNESS_ROOT", pinned)
    monkeypatch.setattr(
        identity, "END_FAIRNESS_CHILD_PAIR", (case.original_child, fixed_child)
    )
    case.approval = {
        "schema": "psm_eval_v2_end_fairness_resume_approval_v1",
        "approved_by": "Owner",
        "owner_decision_ref": "CPU fixture only",
        "review_ref": "CPU fixture only",
        "run_root": str(case.root),
        "manifest_digest": case.manifest["digest"],
        "from_root": case.manifest["experiment"]["root_sha"],
        "to_root": git(case.source, "rev-parse", "HEAD"),
        "from_child": case.original_child,
        "to_child": fixed_child,
    }
    case.approval_path = tmp_path / "end_fairness_approval.json"
    case.approval_path.write_text(json.dumps(case.approval))
    case.executed = []

    class ContinueOneThenStop(cpu_runtime):
        def __init__(self, store, cfg, inputs, environment):
            super().__init__(store, cfg, inputs, environment)
            identity.guard(cfg, store.manifest, inputs)

        def run(self):
            next_episode = next(
                (
                    ep
                    for ep in range(4)
                    if slot_disposition(self.store, task, ep) == "execute"
                ),
                None,
            )
            if next_episode is None:
                return self.store.publish_views(), None
            self.store.begin_task(task)
            fault = next(
                (
                    e
                    for e in self.store.errors(task)
                    if e["attempt"]["episode"] == next_episode
                ),
                None,
            )
            cert = (
                self.store.certify_recovery(task, fault["stream_id"], healthy)
                if fault
                else None
            )
            result = complete(self.store, task, next_episode)
            if cert:
                self.store.resolve_error(task, fault["id"], cert, replacement=result)
            case.executed.append((next_episode, result["generation"]))
            close_streams(self.store, task)
            return self.store.publish_views(), None

    case.Runtime = ContinueOneThenStop
    return case


def approved_end_fairness(case, mode, *extra):
    return cli.main(
        [
            mode,
            "--config",
            str(case.path),
            "--end-fairness-resume-approval",
            str(case.approval_path),
            *extra,
        ],
        prepare_inputs=identity.prepare,
        runtime_type=case.Runtime,
    )


def retained_core_files(root):
    return {
        p.relative_to(root): p.read_bytes()
        for p in root.glob("tasks/*/episodes/*/*")
        if p.is_file()
    }


def test_end_fairness_resume_preserves_core_bytes_across_another_interruption(
    stopped_end_fairness_run, capsys
):
    case = stopped_end_fairness_run
    capsys.readouterr()
    old_cores = retained_core_files(case.root)
    originals = {
        p: (case.root / p).read_bytes()
        for p in ("manifest.json", "_internal/run_inputs.json")
    }
    with pytest.raises(ValueError, match="production source"):
        public(case, "resume")
    assert approved_end_fairness(case, "dry-run") == 0
    preview = json.loads(capsys.readouterr().out)
    assert [row["action"] for row in preview["resume_dispositions"]] == [
        "skip_valid",
        "skip_valid",
        "execute_missing",
        "execute_missing",
    ]
    assert (
        preview["runtime_attested"]
        and preview["end_fairness_execution"]["actual_child"]
        == case.approval["to_child"]
    )
    assert len(invocations(case.root)) == len(probe_records(case.root)) == 1
    assert approved_end_fairness(case, "resume") == 1
    assert case.executed == [
        (2, 1)
    ]  # Native Store issues an independent retry generation.
    interrupted = retained_core_files(case.root)
    assert all(interrupted[path] == payload for path, payload in old_cores.items())
    assert approved_end_fairness(case, "resume") == 0
    assert approved_end_fairness(case, "resume") == 0
    assert [episode for episode, _ in case.executed] == [2, 3]
    assert all(
        (case.root / p).read_bytes() == payload
        for p, payload in {**originals, **interrupted}.items()
    )
    for record, count in zip(invocations(case.root)[1:], (2, 3, 4), strict=True):
        assert record["end_fairness_resume_approval"] == case.approval
        assert (
            record["actual_root"] == case.approval["to_root"]
            and record["actual_child"] == case.approval["to_child"]
        )
        assert record["source_changes"] == {
            "root": ["cosmos-framework", "scripts/robocasa_eval_v2/identity.py"],
            "child": sorted(identity.END_FAIRNESS_CHILD_PATHS),
        }
        assert len(record["retained_valid_cores"]) == count
        for row in record["retained_valid_cores"]:
            p = (
                case.root
                / "tasks"
                / row["task"]
                / "episodes"
                / f"ep_{row['episode']:03d}"
                / "result.json"
            )
            assert row["core_digest"] == store_module.read(p)["sha256"]
        assert record["frozen_run"] == {
            "manifest_sha256": hashlib.sha256(originals["manifest.json"]).hexdigest(),
            "run_inputs_sha256": hashlib.sha256(
                originals["_internal/run_inputs.json"]
            ).hexdigest(),
        }
    assert len(probe_records(case.root)) == 4


@pytest.mark.parametrize(
    "drift,match",
    [
        ("manifest", "invalid Run-bound"),
        ("run_root", "invalid Run-bound"),
        ("child", "invalid Run-bound"),
        ("root_scope", "outside the reviewed End fairness Resume scope"),
        ("child_scope", "outside the reviewed End fairness repair"),
        ("dirty", "dirty Root worktree"),
        ("untracked_ignored", "untracked production source"),
        ("child_dirty", "production source"),
        ("wrong_head", "differs from approved history"),
        ("weights", "Checkpoint/model sampling identity changed"),
        ("model_config", "immutable scientific"),
        ("run_config", "original Run inputs/configuration"),
        ("runtime", "immutable scientific"),
        ("recipe", "immutable scientific"),
        ("task_metadata", "immutable scientific"),
        ("vendor_lock", "vendor lock differs"),
    ],
)
def test_end_fairness_resume_refuses_drift_before_new_evidence(
    stopped_end_fairness_run, monkeypatch, drift, match
):
    case = stopped_end_fairness_run
    before = retained_core_files(case.root)
    if drift in ("manifest", "run_root", "child"):
        key = {
            "manifest": "manifest_digest",
            "run_root": "run_root",
            "child": "to_child",
        }[drift]
        case.approval[key] = "0" * 64
    elif drift == "root_scope":
        (case.source / "scripts/source.py").write_text("# unrelated change\n")
        git(case.source, "commit", "-qam", "unrelated Root source")
        case.approval["to_root"] = git(case.source, "rev-parse", "HEAD")
    elif drift == "child_scope":
        (case.child / "source.py").write_text("# unrelated change\n")
        git(case.child, "commit", "-qam", "unrelated Child source")
        case.approval["to_child"] = git(case.child, "rev-parse", "HEAD")
        monkeypatch.setattr(
            identity,
            "END_FAIRNESS_CHILD_PAIR",
            (case.original_child, case.approval["to_child"]),
        )
        case.approval["to_root"] = set_gitlink(case, "pin unrelated Child")
    elif drift == "dirty":
        (case.source / "SESSION.md").write_text("original notes\n")
        git(case.source, "add", "SESSION.md")
        git(case.source, "commit", "-qm", "allowed notes")
        case.approval["to_root"] = git(case.source, "rev-parse", "HEAD")
        (case.source / "SESSION.md").write_text("dirty notes\n")
    elif drift == "untracked_ignored":
        (case.source / ".git/info/exclude").write_text("scripts/ignored.py\n")
        (case.source / "scripts/ignored.py").write_text("# ignored code\n")
    elif drift == "child_dirty":
        (case.child / "source.py").write_text("# dirty Child\n")
    elif drift == "wrong_head":
        git(case.source, "commit", "--allow-empty", "-qm", "wrong Root target")
    elif drift == "weights":
        from zipfile import ZipFile

        with ZipFile(
            Path(case.cfg["checkpoint"]) / "model/rank0.distcp", "w"
        ) as archive:
            archive.writestr("fake", b"changed synthetic weight shard")
    elif drift == "model_config":
        Path(case.cfg["config_file"]).write_text(
            "raw_action_dim: 15\n# other model config\n"
        )
    elif drift == "run_config":
        case.cfg["request_timeout_s"] = 70
        case.path.write_text(json.dumps(case.cfg))
    elif drift == "runtime":
        case.revision += 1
    elif drift == "recipe":
        Path(case.cfg["g2_run_recipe"]).write_text('{"new_recipe": true}')
    elif drift == "task_metadata":
        path = next(Path(case.cfg["dataset_root"]).rglob("dataset_meta.json"))
        path.write_text(path.read_text() + "\n")
    elif drift == "vendor_lock":
        path = Path(case.cfg["vendor_lock"])
        path.write_bytes(path.read_bytes() + b"\n")
    case.approval_path.write_text(json.dumps(case.approval))
    with pytest.raises(ValueError, match=match):
        approved_end_fairness(case, "resume")
    assert retained_core_files(case.root) == before
    assert len(invocations(case.root)) == len(probe_records(case.root)) == 1
    assert not case.constructed[1:]


def test_end_fairness_approval_is_exclusive_and_runtime_guard_rechecks_source(
    stopped_end_fairness_run, tmp_path
):
    case = stopped_end_fairness_run
    with pytest.raises(SystemExit):
        approved_end_fairness(
            case, "dry-run", "--f27-resume-approval", str(case.approval_path)
        )
    with pytest.raises(SystemExit):
        approved_end_fairness(case, "fresh")
    _, cfg = cli.resolve(["resume", "--config", str(case.path)])
    _, inputs, _ = identity.prepare(
        cfg,
        cache=tmp_path / "cache",
        anchor=store_module.read(case.root / "_internal/run_inputs.json"),
        manifest=case.manifest,
        end_fairness_resume_approval=case.approval,
    )
    identity.guard(cfg, case.manifest, inputs)
    with pytest.raises(ValueError, match="runtime configuration changed"):
        identity.guard(
            dict(cfg, batch_wait_ms=121), case.manifest, inputs, source=False
        )
    (case.child / "source.py").write_text("# dirty after preflight\n")
    with pytest.raises(ValueError, match="production source"):
        identity.guard(cfg, case.manifest, inputs)


def probe_records(root):
    result = []
    for invocation in invocations(root):
        reference = invocation["runtime_probe"]
        assert set(reference) == {"path", "canonical_sha256"}
        path = Path(reference["path"])
        if not path.is_absolute():
            path = root / path
        assert path.parent == root / "_internal/runtime_probe"
        assert len(path.stem) == 32 and all(c in "0123456789abcdef" for c in path.stem)
        record = json.loads(path.read_bytes())
        assert set(record) == {
            "manifest_digest",
            "evaluation_runtime",
            "runtime_probe_evidence",
        }
        assert (
            record["manifest_digest"]
            == store_module.read(root / "manifest.json")["digest"]
        )
        assert reference["canonical_sha256"] == digest(record)
        assert path.read_bytes() == canonical(record) + b"\n"
        result.append((path, record))
    return result


def test_public_large_runtime_evidence_fresh_resume_preserves_anchor_and_Core(
    real_prepare, tmp_path, capsys
):
    case = real_prepare
    case.assets = {
        f"robocasa/models/assets/cpu_fixture/asset_{index:06d}.png": f"{index:064x}"
        for index in range(150_000)
    }
    _, resolved = cli.resolve(["fresh", "--config", str(case.path)])
    prepared = identity.prepare(resolved, cache=tmp_path / "direct-prepare-cache")
    assert isinstance(prepared, tuple) and len(prepared) == 3
    assert prepared[1]["runtime"] == case.attestations[-1]["evaluation_runtime"]
    assert (
        prepared[1]["runtime_probe_evidence"]
        == case.attestations[-1]["runtime_probe_evidence"]
    )
    assert len(canonical(prepared[1]["runtime"])) > 16 * MIB
    assert public(case, "fresh") == 0
    initial = case.attestations[-1]
    anchor_path = case.root / "_internal/run_inputs.json"
    anchor_bytes = anchor_path.read_bytes()
    anchor = store_module.read(anchor_path)
    assert len(anchor_bytes) < 256 * 1024
    assert anchor["runtime"] == {"digest": initial["evaluation_runtime"]["digest"]}
    assert "runtime_probe_evidence" not in anchor
    before = core_bytes(case.root)
    assert len(before) == 2
    fresh_records = probe_records(case.root)
    assert len(fresh_records) == 1
    first_path, first_record = fresh_records[0]
    assert first_record["evaluation_runtime"] == initial["evaluation_runtime"]
    assert first_record["runtime_probe_evidence"] == initial["runtime_probe_evidence"]
    assert (
        first_record["evaluation_runtime"]["packages"]["robocasa"][
            "untracked_asset_sha256"
        ]
        == case.assets
    )
    first_bytes = first_path.read_bytes()
    assert len(first_bytes) > 16 * MIB
    with pytest.raises(ValueError):
        store_module.read(first_path)  # The ordinary read limit is not widened.
    cache = store_module.read(case.root / "_internal/verification_cache.json")
    assert cache["anchor_sha256"] == digest(anchor)

    case.warning = "changed CPU vendor warning only"
    assert public(case, "resume") == 0
    assert (
        case.attestations[-1]["evaluation_runtime"]["digest"]
        == initial["evaluation_runtime"]["digest"]
    )
    assert anchor_path.read_bytes() == anchor_bytes and core_bytes(case.root) == before
    assert first_path.read_bytes() == first_bytes
    records = probe_records(case.root)
    assert len(records) == 2 and records[0][0] != records[1][0]
    assert {r["runtime_probe_evidence"]["stdout"] for _, r in records} == {
        initial["runtime_probe_evidence"]["stdout"],
        case.attestations[-1]["runtime_probe_evidence"]["stdout"],
    }
    assert all(
        r["evaluation_runtime"] == initial["evaluation_runtime"] for _, r in records
    )
    cache = store_module.read(case.root / "_internal/verification_cache.json")
    assert cache["anchor_sha256"] == digest(anchor)
    assert CpuRuntime.starts == 1 and len(case.constructed) == 2
    capsys.readouterr()
    latest_stdout = case.attestations[-1]["runtime_probe_evidence"]["stdout"]
    warning_only = (
        initial["runtime_probe_evidence"]["stdout"].split("\n", 1)[1]
        == latest_stdout.split("\n", 1)[1]
        and initial["runtime_probe_evidence"]["stdout"].split("\n", 1)[0]
        != latest_stdout.split("\n", 1)[0]
    )
    assert warning_only
    with capsys.disabled():
        print(
            "V2_RUNTIME_EVIDENCE_WITNESS "
            + json.dumps(
                {
                    "synthetic_CPU_only": True,
                    "sidecar_bytes": [p.stat().st_size for p, _ in records],
                    "run_inputs_bytes": anchor_path.stat().st_size,
                    "synthetic_asset_SHA_entries": len(case.assets),
                    "runtime_digest": initial["evaluation_runtime"]["digest"],
                    "anchor_canonical_sha256_before": digest(anchor),
                    "anchor_canonical_sha256_after": digest(
                        store_module.read(anchor_path)
                    ),
                    "anchor_bytes_unchanged": anchor_path.read_bytes() == anchor_bytes,
                    "fresh_evidence_count": len(fresh_records),
                    "resume_evidence_count": len(records),
                    "stdout_warning_only_changed": warning_only,
                    "Core_bytes_unchanged": core_bytes(case.root) == before,
                }
            ),
            flush=True,
        )


@pytest.mark.parametrize(
    "drift", ["runtime", "model", "config", "source_dirty", "source_commit", "child"]
)
def test_public_resume_rejects_identity_drift_before_new_evidence_or_Runtime(
    real_prepare, drift, capsys
):
    case = real_prepare
    assert public(case, "fresh") == 0
    original = core_bytes(case.root)
    anchor = (case.root / "_internal/run_inputs.json").read_bytes()
    probes = {str(p): p.read_bytes() for p, _ in probe_records(case.root)}
    if drift == "runtime":
        case.revision += 1
    elif drift == "model":
        shard = Path(case.cfg["checkpoint"]) / "model/rank0.distcp"
        shard.write_bytes(shard.read_bytes() + b"changed synthetic payload")
    elif drift == "config":
        Path(case.cfg["config_file"]).write_text("raw_action_dim: 15\nchanged: true\n")
    elif drift.startswith("source"):
        (case.source / "scripts/source.py").write_text("# changed production source\n")
        if drift == "source_commit":
            git(case.source, "add", "scripts/source.py")
            git(case.source, "commit", "-qm", "CPU committed source drift")
    else:
        (case.child / "source.py").write_text("# changed Child source\n")
        git(case.child, "add", "source.py")
        git(case.child, "commit", "-qm", "CPU Child drift")
    with pytest.raises(ValueError):
        public(case, "resume")
    assert len(case.constructed) == 1 and len(invocations(case.root)) == 1
    assert (case.root / "_internal/run_inputs.json").read_bytes() == anchor
    assert core_bytes(case.root) == original
    assert {str(p): p.read_bytes() for p, _ in probe_records(case.root)} == probes
    capsys.readouterr()


@pytest.mark.parametrize("mode", ["fresh", "resume"])
def test_public_evidence_write_failure_never_constructs_Runtime_or_adopts_fresh(
    real_prepare, monkeypatch, mode, capsys
):
    case = real_prepare
    if mode == "resume":
        assert public(case, "fresh") == 0
    before = core_bytes(case.root)
    previous_invocations = len(invocations(case.root))
    previous_constructors = len(case.constructed)
    error = OSError(errno.EIO, "synthetic evidence write failure")

    def fail(path, value):
        assert Path(path).parent == case.root / "_internal/runtime_probe"
        assert (
            value["evaluation_runtime"] == case.attestations[-1]["evaluation_runtime"]
        )
        raise error

    with monkeypatch.context() as fault:
        fault.setattr(cli, "write_runtime_probe", fail)
        with pytest.raises(OSError) as raised:
            public(case, mode)
        assert raised.value is error
    assert case.root.exists() and len(case.constructed) == previous_constructors
    assert len(invocations(case.root)) == previous_invocations
    assert core_bytes(case.root) == before
    if mode == "fresh":
        assert not (case.root / "summary.json").exists()
    residue = {str(p): p.read_bytes() for p in case.root.rglob("*") if p.is_file()}
    with pytest.raises(FileExistsError):
        public(case, "fresh")
    assert {
        str(p): p.read_bytes() for p in case.root.rglob("*") if p.is_file()
    } == residue
    assert public(case, "fresh", output=case.root.with_name("clean-new-run")) == 0
    assert len(case.constructed) == previous_constructors + 1
    capsys.readouterr()


def probe_path(tmp_path):
    return tmp_path / "run/_internal/runtime_probe" / ("a" * 32 + ".json")


def test_ordinary_JSON_limits_stay_small_and_probe_limit_is_private_64MiB(tmp_path):
    assert store_module.MAX_JSON == 256 * 1024
    assert store_module.MAX_RUNTIME_PROBE == 64 * MIB
    ordinary = tmp_path / "ordinary.json"
    value = {"synthetic": "x" * store_module.MAX_JSON}
    with pytest.raises(ValueError):
        store_module.write(ordinary, value)
    assert not ordinary.exists()
    ordinary.write_bytes(canonical(value) + b"\n")
    with pytest.raises(ValueError):
        store_module.read(ordinary)
    oversized = {"synthetic": "x" * store_module.MAX_RUNTIME_PROBE}
    target = probe_path(tmp_path)
    with pytest.raises(ValueError):
        store_module.write_runtime_probe(target, oversized)
    assert not target.exists()


@pytest.mark.parametrize("wrong", ["parent", "ancestor", "suffix", "uuid"])
def test_runtime_probe_writer_rejects_non_probe_paths(tmp_path, wrong):
    target = probe_path(tmp_path)
    if wrong == "parent":
        target = target.parent.with_name("ledger") / target.name
    elif wrong == "ancestor":
        target = tmp_path / "public/runtime_probe" / target.name
    elif wrong == "suffix":
        target = target.with_suffix(".txt")
    else:
        target = target.with_name("not-a-uuid.json")
    with pytest.raises(ValueError):
        store_module.write_runtime_probe(target, {"synthetic": True})
    assert not target.exists()


@pytest.mark.parametrize("kind", ["overwrite", "leaf_symlink", "parent_symlink"])
def test_runtime_probe_writer_never_overwrites_or_follows_symlinks(tmp_path, kind):
    target = probe_path(tmp_path)
    target.parent.mkdir(parents=True)
    value = {"synthetic": "original evidence"}
    if kind == "overwrite":
        store_module.write_runtime_probe(target, value)
        before = target.read_bytes()
        with pytest.raises(FileExistsError):
            store_module.write_runtime_probe(target, {"synthetic": "overwrite"})
        assert target.read_bytes() == before
    else:
        other = tmp_path / "outside"
        other.mkdir()
        if kind == "leaf_symlink":
            protected = other / "protected.json"
            protected.write_bytes(b"keep original")
            target.symlink_to(protected)
        else:
            target.parent.rmdir()
            target.parent.symlink_to(other, target_is_directory=True)
        with pytest.raises(ValueError):
            store_module.write_runtime_probe(target, value)
        if kind == "leaf_symlink":
            assert protected.read_bytes() == b"keep original"
        else:
            assert not list(other.iterdir())
    assert not list(target.parent.glob(".pending-*"))


@pytest.mark.parametrize(
    "stage", ["partial", "file_fsync", "publish", "directory_fsync"]
)
def test_probe_partial_publish_and_fsync_faults_preserve_errors_and_no_success(
    tmp_path, monkeypatch, stage
):
    target = probe_path(tmp_path)
    target.parent.mkdir(parents=True)
    value = {"synthetic": "complete evidence"}
    error = OSError(errno.EIO, "synthetic " + stage)
    original_fdopen, original_sync = store_module.os.fdopen, store_module.sync_dir

    def failed(*args, **kwargs):
        raise error

    if stage == "partial":

        class Partial:
            def __init__(self, stream):
                self.stream = stream

            def __enter__(self):
                self.stream.__enter__()
                return self

            def __exit__(self, *args):
                return self.stream.__exit__(*args)

            def write(self, raw):
                self.stream.write(raw[:5])
                raise error

        monkeypatch.setattr(
            store_module.os, "fdopen", lambda *a, **k: Partial(original_fdopen(*a, **k))
        )
    elif stage == "file_fsync":
        monkeypatch.setattr(store_module.os, "fsync", failed)
    elif stage == "publish":
        monkeypatch.setattr(store_module.os, "link", failed)
    else:

        def sync(path):
            if Path(path) == target.parent:
                assert target.exists()  # Link precedes the directory durability fence.
                raise error
            return original_sync(path)

        monkeypatch.setattr(store_module, "sync_dir", sync)
    with pytest.raises(OSError) as raised:
        store_module.write_runtime_probe(target, value)
    assert raised.value is error
    assert not list(target.parent.glob(".pending-*"))
    if stage == "directory_fsync":
        # A visible complete record after failed directory fsync is retained
        # diagnostic residue, never a successful return or invocation receipt.
        assert json.loads(target.read_bytes()) == value
    else:
        assert not target.exists()
