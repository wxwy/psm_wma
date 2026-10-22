"""CPU contracts against an independently built vendor, never Kitchen/reset/step.

Set PSM_VENDOR_BUILD to build_robocasa_vendor.py's new output directory. Real
controller/XML code executes; environment lifecycle uses original source bodies
with a counting Sim boundary double. Runtime-probe import doubles are explicit.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib
import importlib.util
import json
import os
import py_compile
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import OrderedDict
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import mujoco
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tools/v3"))
import robocasa_vendor as vendor
from build_robocasa_vendor import DEFAULT_LOCK, build, git


@pytest.fixture(scope="session")
def checkout():
    path = Path(os.environ["PSM_VENDOR_BUILD"]).resolve()
    lock = json.loads(DEFAULT_LOCK.read_text())
    assert git(path / "robosuite", "rev-parse", "HEAD") == lock["robosuite"]["patched_commit"]
    assert git(path / "robocasa", "rev-parse", "HEAD") == lock["robocasa"]["commit"]
    return path


@pytest.fixture
def modules(checkout, monkeypatch):
    # Bypass only eager registration imports. Real helpers/controllers/XML classes
    # resolve from the actual built source, not copied method implementations.
    for name in ("robosuite", "robosuite.models", "robosuite.controllers", "robosuite.controllers.parts"):
        package = ModuleType(name)
        package.__file__ = str(checkout / "robosuite" / name.replace(".", "/") / "__init__.py")
        package.__path__ = [str(Path(package.__file__).parent)]
        monkeypatch.setitem(sys.modules, name, package)
        if "." in name:
            parent, child_name = name.rsplit(".", 1)
            setattr(sys.modules[parent], child_name, package)
    sys.modules["robosuite.models"].assets_root = str(checkout / "robosuite/robosuite/models/assets")
    # Avoid cached modules from another test retaining an older package namespace.
    for name in list(sys.modules):
        if name.startswith("robosuite.") and name not in {
            "robosuite.models",
            "robosuite.controllers",
            "robosuite.controllers.parts",
        }:
            monkeypatch.delitem(sys.modules, name)
    return SimpleNamespace(
        joint=importlib.import_module("robosuite.controllers.parts.mobile_base.joint_vel"),
        world=importlib.import_module("robosuite.models.world"),
    )


def test_rebuild_same_patch_has_same_commit_and_does_not_edit_cache(checkout, tmp_path):
    before = {
        name: git(checkout / name, "status", "--porcelain", "--untracked-files=all")
        for name in ("robosuite", "robocasa")
    }
    built = build(robosuite_cache=checkout / "robosuite", robocasa_cache=checkout / "robocasa", output=tmp_path / "new")
    lock = json.loads(DEFAULT_LOCK.read_text())
    assert built["robosuite"]["commit"] == lock["robosuite"]["patched_commit"]
    assert built["robosuite"]["tree"] == lock["robosuite"]["patched_tree"]
    assert not built["package_install_performed"]
    assert before == {name: git(checkout / name, "status", "--porcelain", "--untracked-files=all") for name in before}


def test_existing_output_never_overwritten(checkout, tmp_path):
    output = tmp_path / "existing"
    output.mkdir()
    (output / "keep").write_bytes(b"history")
    with pytest.raises(FileExistsError):
        build(robosuite_cache=checkout / "robosuite", robocasa_cache=checkout / "robocasa", output=output)
    assert (output / "keep").read_bytes() == b"history"


def test_patch_checksum_failure_precedes_output_claim(checkout, tmp_path):
    lock = json.loads(DEFAULT_LOCK.read_text())
    lock_path = tmp_path / "vendor.lock.json"
    lock_path.write_text(json.dumps(lock))
    (tmp_path / lock["robosuite"]["patch"]).write_text("not the frozen patch")
    with pytest.raises(ValueError, match="SHA256"):
        build(
            robosuite_cache=checkout / "robosuite",
            robocasa_cache=checkout / "robocasa",
            output=tmp_path / "no",
            lock_path=lock_path,
        )
    assert not (tmp_path / "no").exists()


@pytest.mark.parametrize("axis", ["x", "y"])
@pytest.mark.parametrize("angle", [0.0, np.pi / 2, -np.pi / 2, np.pi])
@pytest.mark.parametrize(
    "command", [[1.0, 0.0, 0.0], [-1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, -1.0, 0.0], [0.0, 0.0, 1.0], [0.0, 0.0, -1.0]]
)
def test_legacy_forward_lateral_yaw_in_both_axis_definitions(modules, axis, angle, command):
    cls = modules.joint.LegacyMobileBaseJointVelocityController
    controller = cls.__new__(cls)
    controller.joint_names = ["robot0_joint_mobile_forward", "robot0_joint_mobile_side", "robot0_joint_mobile_yaw"]
    controller.sim = SimpleNamespace(
        model=SimpleNamespace(jnt_axis=np.array([[1, 0, 0] if axis == "x" else [0, 1, 0]]), joint_name2id=lambda _: 0)
    )
    controller.qpos_index = [0, 1, 2]
    controller.impedance_mode = "fixed"
    controller.update = lambda: None
    controller.scale_action = lambda a: a
    controller.init_ori = np.eye(3)
    orientation = np.array([[np.cos(angle), -np.sin(angle), 0], [np.sin(angle), np.cos(angle), 0], [0, 0, 1]])
    controller.get_base_pose = lambda: (np.zeros(3), orientation)
    controller.interpolator = Mock()
    action = np.array(command)
    before = action.copy()
    controller.set_goal(action)
    # Independent explicit golden convention from the upstream Legacy contract:
    # X-forward uses +theta. Historical Y-forward swaps the planar inputs and
    # uses -theta. Yaw sign is unchanged in both, including nonzero base heading.
    x, y, yaw = command if axis == "x" else [command[1], command[0], command[2]]
    theta = angle if axis == "x" else -angle
    expected = [x * np.cos(theta) - y * np.sin(theta), x * np.sin(theta) + y * np.cos(theta), yaw]
    np.testing.assert_allclose(controller.goal_qvel, expected, atol=1e-7)
    np.testing.assert_array_equal(action, before)
    controller.interpolator.set_goal.assert_called_once()


def test_normal_alias_is_not_equivalent_at_nonzero_heading(modules):
    # Exercise the original ordinary-controller source body too, showing why
    # merely selecting its class cannot close the legacy direction contract.
    normal = modules.joint.MobileBaseJointVelocityController.__new__(modules.joint.MobileBaseJointVelocityController)
    normal.qpos_index = [0, 1, 2]
    normal.impedance_mode = "fixed"
    normal.update = lambda: None
    normal.scale_action = lambda a: a
    normal.init_ori = np.eye(3)
    normal.get_base_pose = lambda: (np.zeros(3), np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]]))
    normal.interpolator = None
    normal.set_goal(np.array([1.0, 0.0, 0.0]))
    np.testing.assert_allclose(normal.goal_qvel, [0, -1, 0], atol=1e-7)
    assert not np.allclose(normal.goal_qvel, [0, 1, 0])


def test_factory_exports_real_legacy_class_not_alias(checkout, modules):
    package = importlib.import_module("robosuite.controllers.parts.mobile_base")
    assert package.LegacyMobileBaseJointVelocityController is modules.joint.LegacyMobileBaseJointVelocityController
    file = checkout / "robosuite/robosuite/controllers/parts/controller_factory.py"
    node = next(
        n
        for n in ast.parse(file.read_text()).body
        if isinstance(n, ast.FunctionDef) and n.name == "mobile_base_controller_factory"
    )
    scope = {
        "mobile_base_controllers": SimpleNamespace(
            LegacyMobileBaseJointVelocityController=Mock(return_value="legacy"),
            MobileBaseJointVelocityController=Mock(return_value="ordinary"),
        )
    }
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(file), "exec"), scope)
    assert scope["mobile_base_controller_factory"]("JOINT_VELOCITY_LEGACY", {}) == "legacy"
    scope["mobile_base_controllers"].MobileBaseJointVelocityController.assert_not_called()
    with pytest.raises(ValueError):
        scope["mobile_base_controller_factory"]("unknown", {})


@pytest.mark.parametrize("ccd", [False, True])
def test_task_world_options_reach_actual_mujoco_model(checkout, modules, ccd):
    # Execute original Task.__init__ through a real MujocoWorldBase. Stub only
    # arena/robot merges; no environment, MjData or simulation is created.
    path = checkout / "robosuite/robosuite/models/tasks/task.py"
    node = next(n for n in ast.parse(path.read_text()).body if isinstance(n, ast.ClassDef) and n.name == "Task")
    init = next(n for n in node.body if isinstance(n, ast.FunctionDef) and n.name == "__init__")
    cls = ast.ClassDef(
        name="Task", bases=[ast.Name(id="World", ctx=ast.Load())], keywords=[], body=[init], decorator_list=[]
    )
    scope = {
        "World": modules.world.MujocoWorldBase,
        "RobotModel": type("RobotModel", (), {}),
        "MujocoObject": type("MujocoObject", (), {}),
    }
    exec(compile(ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[])), str(path), "exec"), scope)
    Task = scope["Task"]
    Task.merge_arena = lambda *a: None
    Task.merge_robot = lambda *a: None
    Task.merge_objects = lambda *a: None
    task = Task(mujoco_arena=None, mujoco_robots=[], enable_multiccd=ccd, enable_sleeping_islands=False)
    model = mujoco.MjModel.from_xml_string(task.get_xml())
    assert bool(model.opt.enableflags & int(mujoco.mjtEnableBit.mjENBL_MULTICCD)) is ccd
    assert task.enable_sleeping_islands is False
    assert len(task.root.findall("option")) == 1


@pytest.mark.parametrize(
    "kwargs", [{"enable_multiccd": 1}, {"enable_sleeping_islands": None}, {"enable_sleeping_islands": True}]
)
def test_physics_options_do_not_accept_ignored_or_unsupported_values(modules, kwargs):
    with pytest.raises((TypeError, ValueError)):
        modules.world.MujocoWorldBase(**kwargs)


def lifecycle_classes(checkout):
    # Original full base class and original chain constructors with zero-arg
    # super preserved. External renderer/model/sim operations are overrides.
    scope = {
        "np": np,
        "OrderedDict": OrderedDict,
        "deepcopy": copy.deepcopy,
        "EnvMeta": type,
        "macros": SimpleNamespace(SIMULATION_TIMESTEP=0.002),
    }
    base = ast.parse((checkout / "robosuite/robosuite/environments/base.py").read_text())
    node = next(n for n in base.body if isinstance(n, ast.ClassDef) and n.name == "MujocoEnv")
    exec(compile(ast.Module(body=[node], type_ignores=[]), "vendor/base.py", "exec"), scope)
    for name, parent, file in [
        ("RobotEnv", "MujocoEnv", "robot_env.py"),
        ("ManipulationEnv", "RobotEnv", "manipulation/manipulation_env.py"),
    ]:
        tree = ast.parse((checkout / "robosuite/robosuite/environments" / file).read_text())
        node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name)
        node.body = [n for n in node.body if isinstance(n, ast.FunctionDef) and n.name in {"__init__", "_input2list"}]
        exec(compile(ast.Module(body=[node], type_ignores=[]), "vendor/" + file, "exec"), scope)
    return scope


@pytest.mark.parametrize("defer", [False, True])
@pytest.mark.parametrize("hard_reset", [False, True])
def test_full_inheritance_chain_defers_model_and_rng_to_first_reset(checkout, defer, hard_reset):
    chain = lifecycle_classes(checkout)

    class Harness(chain["ManipulationEnv"]):
        def _check_robot_configuration(self, *a):
            pass

        def _load_model(self):
            self.events.append(("load", int(self.rng.integers(100000))))

        def _initialize_sim(self):
            self.sim = SimpleNamespace(
                reset=lambda: self.events.append(("sim-reset", None)),
                forward=lambda: None,
                free=lambda: self.events.append(("free", None)),
            )

        def initialize_renderer(self):
            self.events.append(("renderer", None))

        def _reset_internal(self):
            pass

        def _setup_observables(self):
            return {}

        def _reset_observables(self):
            pass

        def visualize(self, *a, **kw):
            pass

        def update_state(self):
            pass

        def _get_observations(self, **kw):
            return {"cpu": True}

        @property
        def _visualizations(self):
            return {}

    env = Harness.__new__(Harness)
    env.events = []
    env.__init__(robots="PandaOmron", renderer="mujoco", load_model_on_init=not defer, hard_reset=hard_reset, seed=7)
    assert len([e for e in env.events if e[0] == "load"]) == (0 if defer else 1)
    env.reset()
    loads = [e for e in env.events if e[0] == "load"]
    assert len(loads) == (1 if defer or not hard_reset else 2)
    assert loads[0][1] == int(np.random.default_rng(7).integers(100000))
    assert env._env_is_initialized is True
    before = len(loads)
    env.reset()
    assert len([e for e in env.events if e[0] == "load"]) == before + int(hard_reset)


@pytest.mark.parametrize("state", ["absent", "none", "live"])
def test_destroy_sim_idempotent_before_and_after_creation(checkout, state):
    cls = lifecycle_classes(checkout)["MujocoEnv"]
    obj = cls.__new__(cls)
    free = Mock()
    if state != "absent":
        obj.sim = None if state == "none" else SimpleNamespace(free=free)
    obj._destroy_sim()
    obj._destroy_sim()
    assert free.call_count == int(state == "live")


def tiny_source(tmp_path):
    (tmp_path / "robocasa").mkdir()
    (tmp_path / "robocasa/__init__.py").write_text("__version__='1.0.1'\n")
    git(tmp_path, "init", "-q")
    git(tmp_path, "add", ".")
    git(tmp_path, "-c", "user.name=CPU", "-c", "user.email=cpu@example.invalid", "commit", "-qm", "CPU")
    return tmp_path / "robocasa/__init__.py", git(tmp_path, "rev-parse", "HEAD")


@pytest.mark.parametrize(
    "kind",
    ["tracked", "staged", "untracked", "ignored", "backup", "symlink", "wrong_commit", "wrong_origin", "poison_pyc"],
)
def test_runtime_source_audit_rejects_dirty_or_ambiguous_imports(tmp_path, kind):
    origin, sha = tiny_source(tmp_path)
    if kind in ("tracked", "staged"):
        origin.write_text("__version__='evil'\n")
    if kind == "staged":
        git(tmp_path, "add", ".")
    if kind in ("untracked", "ignored", "backup"):
        path = tmp_path / ("robocasa/injected.py" if kind != "backup" else "robocasa/old.py.bak")
        path.write_text("bad")
        if kind == "ignored":
            (tmp_path / ".git/info/exclude").write_text("*.py\n")
    if kind == "symlink":
        (tmp_path / "robocasa/external").symlink_to("/tmp")
    if kind == "poison_pyc":
        py_compile.compile(str(origin), doraise=True)
        cached = Path(importlib.util.cache_from_source(str(origin)))
        original = origin.read_text()
        origin.write_text("raise RuntimeError('poison')\n")
        py_compile.compile(str(origin), doraise=True)
        origin.write_text(original)
        assert cached.exists()
    if kind == "wrong_commit":
        sha = "0" * 40
    if kind == "wrong_origin":
        origin = tmp_path / "shadow/__init__.py"
        origin.parent.mkdir()
        origin.write_text("")
    with pytest.raises((ValueError, subprocess.CalledProcessError)):
        vendor.audit_source(origin, package="robocasa", expected_commit=sha, assets={})


def test_clean_source_bytecode_and_explicit_asset_inventory(tmp_path):
    origin, sha = tiny_source(tmp_path)
    py_compile.compile(str(origin), doraise=True)
    assert vendor.audit_source(origin, package="robocasa", expected_commit=sha, assets={})["tracked_clean"]
    asset = tmp_path / "robocasa/models/assets/fixtures/example.xml"
    asset.parent.mkdir(parents=True)
    asset.write_text("<mujoco/>")
    with pytest.raises(ValueError, match="inventory"):
        vendor.audit_source(origin, package="robocasa", expected_commit=sha, assets={})
    approved = {"robocasa": {str(asset.relative_to(tmp_path)): vendor.sha256_file(asset)}}
    assert vendor.audit_source(origin, package="robocasa", expected_commit=sha, assets=approved)[
        "untracked_asset_sha256"
    ]
    asset.write_text("changed")
    with pytest.raises(ValueError, match="SHA mismatch"):
        vendor.audit_source(origin, package="robocasa", expected_commit=sha, assets=approved)


def test_dataset_metadata_is_separate_from_runtime_and_capture_time(tmp_path):
    meta = tmp_path / "dataset_meta.json"
    meta.write_text(
        json.dumps(
            {
                "robocasa_version": "0.5.1",
                "robosuite_version": "1.5.2",
                "mujoco_version": "3.3.1",
                "env_args": {"env_name": "CloseFridge"},
            }
        )
    )
    record = vendor.dataset_provenance(meta)
    assert record["recorded_generation_versions"]["robocasa"] == "0.5.1"
    assert record["capture_time_commit"] == record["generation_git_commit"] == "UNKNOWN"
    assert record["equivalent_to_evaluation_runtime"] == "NOT_PROVEN"
    meta.write_text(json.dumps({"robocasa_version": "0.5.1", "nested": {"robocasa_version": "1.0.1"}}))
    with pytest.raises(ValueError, match="ambiguous"):
        vendor.dataset_provenance(meta)


def test_absent_metadata_versions_are_not_filled_with_evaluator_version(tmp_path):
    meta = tmp_path / "dataset_meta.json"
    meta.write_text('{"env_version":"0.5.1"}')
    record = vendor.dataset_provenance(meta)
    assert record["recorded_generation_versions"]["robocasa"] == "NOT_RECORDED"
    assert record["metadata_recorded_versions"] == {"/env_version": "0.5.1"}


def official_registry(checkout):
    file = checkout / "robocasa/robocasa/utils/dataset_registry.py"
    nodes = [
        n
        for n in ast.parse(file.read_text()).body
        if isinstance(n, ast.Assign)
        and any(
            isinstance(t, ast.Name) and t.id in {"ATOMIC_TASK_DATASETS", "COMPOSITE_TASK_DATASETS"} for t in n.targets
        )
    ]
    scope = {"OrderedDict": OrderedDict}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(file), "exec"), scope)
    # The original getter contains only one local registry import; substitute
    # those globals with the actual registry dictionaries parsed above.
    getter = checkout / "robocasa/robocasa/utils/dataset_registry_utils.py"
    node = next(
        n for n in ast.parse(getter.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == "get_task_horizon"
    )
    node.body = [n for n in node.body if not isinstance(n, ast.ImportFrom)]
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(getter), "exec"), scope)
    return scope["get_task_horizon"]


def runtime_doubles(checkout, monkeypatch):
    lock = json.loads(DEFAULT_LOCK.read_text())
    expected = dict(lock["runtime_versions"], robosuite="1.5.2", robocasa="1.0.1")
    real_modules = {"numpy": np, "mujoco": mujoco}
    for name in ("robocasa", "robosuite"):
        real_modules[name] = SimpleNamespace(
            __file__=str(checkout / name / name / "__init__.py"), __version__=expected[name]
        )
    getter = official_registry(checkout)
    real_modules["robocasa.utils.dataset_registry_utils"] = SimpleNamespace(get_task_horizon=getter)
    monkeypatch.setattr(vendor.importlib.metadata, "version", lambda name: expected[name])
    monkeypatch.setattr(
        vendor.importlib.util, "find_spec", lambda name: SimpleNamespace(origin=real_modules[name].__file__)
    )
    monkeypatch.setattr(vendor.importlib, "import_module", lambda name: real_modules[name])
    return real_modules


def test_probe_actual_git_native_versions_and_original_official_horizons(checkout, monkeypatch):
    runtime_doubles(checkout, monkeypatch)
    result = vendor.probe_runtime()
    assert result["packages"]["mujoco"]["native_version"] == "3.3.1"
    assert result["packages"]["numpy"]["distribution_version"] == "2.2.5"
    assert result["packages"]["robocasa"]["commit"] == "6f90063c0ec2b9916bbd977368b54c98d9c2d908"
    getter = official_registry(checkout)
    assert result["protocol"]["official_horizons"] == {
        name: getter(name) for name in ("CloseFridge", "NavigateKitchen")
    }
    assert result["protocol"]["horizon_multiplier_applied"] is False
    assert result["physics_capabilities"]["real_kitchen_behavior_validated"] is False
    digest = result.pop("digest")
    assert digest == hashlib.sha256(vendor.canonical(result)).hexdigest()


@pytest.mark.parametrize(
    "wrong", ["metadata_version", "module_version", "module_origin", "native_version", "missing_horizon"]
)
def test_probe_rejects_false_runtime_claims(checkout, monkeypatch, wrong):
    modules = runtime_doubles(checkout, monkeypatch)
    if wrong == "metadata_version":
        monkeypatch.setattr(vendor.importlib.metadata, "version", lambda _: "wrong")
    elif wrong == "module_version":
        modules["robocasa"].__version__ = "0.5.1"
    elif wrong == "module_origin":
        # spec points at the correct package; actual imported object points elsewhere.
        origins = {name: module.__file__ for name, module in modules.items() if hasattr(module, "__file__")}
        monkeypatch.setattr(vendor.importlib.util, "find_spec", lambda name: SimpleNamespace(origin=origins[name]))
        modules["robocasa"].__file__ = str(checkout / "robosuite/robosuite/__init__.py")
    elif wrong == "native_version":
        monkeypatch.setattr(mujoco, "mj_versionString", lambda: "3.3.2")
    else:
        modules["robocasa.utils.dataset_registry_utils"].get_task_horizon = lambda _: -1
    with pytest.raises(ValueError):
        vendor.probe_runtime()


@pytest.mark.parametrize(
    "wrong", [None, "digest", "interpreter", "pythonpath", "lock", "probe", "duplicate", "missing", "nonzero"]
)
def test_collector_binds_actual_interpreter_command_and_payload(checkout, monkeypatch, wrong):
    runtime_doubles(checkout, monkeypatch)
    result = vendor.probe_runtime()
    if wrong in ("digest", "interpreter", "pythonpath", "lock", "probe"):
        result.pop("digest")
        if wrong == "digest":
            result["digest"] = "0" * 64
        elif wrong == "interpreter":
            result["interpreter"]["executable"] = "/wrong/python"
        elif wrong == "pythonpath":
            result["interpreter"]["pythonpath_env"] = "/wrong/import/context"
        elif wrong == "lock":
            result["lock_sha256"] = "0" * 64
        else:
            result["probe_sha256"] = "0" * 64
        if wrong != "digest":
            result["digest"] = hashlib.sha256(vendor.canonical(result)).hexdigest()

    def run(argv, **kwargs):
        assert argv[1] == "-B" and "-I" not in argv
        assert kwargs["env"]["CUDA_VISIBLE_DEVICES"] == ""
        assert kwargs["env"]["MUJOCO_GL"] == "disable"
        assert kwargs["check"] is True and kwargs["timeout"] == 120
        if wrong == "nonzero":
            raise subprocess.CalledProcessError(1, argv, stderr="import failed")
        record = "PSM_RUNTIME " + json.dumps(result) + "\n"
        return SimpleNamespace(
            stdout="vendor warnings\n" + (record * 2 if wrong == "duplicate" else "" if wrong == "missing" else record),
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(vendor.subprocess, "run", run)
    if wrong is None:
        answer = vendor.collect_runtime(sim_python=Path(sys.executable))
        assert answer["evaluation_runtime"]["digest"] == result["digest"]
        assert "vendor warnings" in answer["runtime_probe_evidence"]["stdout"]
    else:
        with pytest.raises((ValueError, subprocess.CalledProcessError)):
            vendor.collect_runtime(sim_python=Path(sys.executable))


def test_verified_manifest_keeps_dataset_runtime_and_transient_logs_separate(tmp_path, monkeypatch):
    import v3_evaluation_identity as base_identity

    meta = tmp_path / "lerobot/extras/dataset_meta.json"
    meta.parent.mkdir(parents=True)
    meta.write_text('{"robocasa_version":"0.5.1"}')
    runtime = {"packages": {"robocasa": {"distribution_version": "1.0.1"}}, "digest": "runtime-digest"}
    monkeypatch.setattr(
        vendor,
        "collect_runtime",
        lambda **kw: {"evaluation_runtime": runtime, "runtime_probe_evidence": {"stdout": "volatile warnings"}},
    )
    monkeypatch.setattr(
        base_identity,
        "build_evaluation_identity",
        lambda **kw: {"identity": {"protocol": kw["protocol"]}, "digest": "ignored"},
    )
    bundle = vendor.build_verified_evaluation_identity(
        sim_python=Path(sys.executable),
        tasks=[("CloseFridge", meta.parent.parent)],
        protocol={"local_memory_mode": "required"},
    )
    identity = bundle["manifest"]["identity"]
    assert identity["dataset"]["sources"][0]["recorded_generation_versions"]["robocasa"] == "0.5.1"
    assert identity["evaluation_runtime"]["packages"]["robocasa"]["distribution_version"] == "1.0.1"
    assert "volatile" not in json.dumps(bundle["manifest"])
    assert bundle["manifest"]["digest"] == hashlib.sha256(vendor.canonical(identity)).hexdigest()


def test_collector_uses_the_same_explicit_simulator_import_environment(checkout, monkeypatch):
    runtime_doubles(checkout, monkeypatch)
    monkeypatch.setenv("PYTHONPATH", "/synthetic/pinned/simulator/imports")
    result = vendor.probe_runtime()

    def run(argv, **kwargs):
        assert kwargs["env"]["PYTHONPATH"] == "/synthetic/pinned/simulator/imports"
        assert kwargs["env"]["PSM_TEST_ENV"] == "same-child-environment"
        return SimpleNamespace(stdout="PSM_RUNTIME " + json.dumps(result) + "\n", stderr="", returncode=0)

    monkeypatch.setattr(vendor.subprocess, "run", run)
    env = dict(os.environ, PSM_TEST_ENV="same-child-environment")
    answer = vendor.collect_runtime(sim_python=Path(sys.executable), simulation_env=env)
    assert answer["evaluation_runtime"]["interpreter"]["pythonpath_env"] == env["PYTHONPATH"]


def test_pinned_omron_xml_and_kitchen_request_the_reviewed_contract(checkout):
    xml = ET.parse(checkout / "robosuite/robosuite/models/assets/bases/omron_mobile_base.xml")
    axes = {j.attrib["name"]: j.attrib.get("axis") for j in xml.iter("joint") if "name" in j.attrib}
    assert axes["joint_mobile_forward"] == "1 0 0"
    assert axes["joint_mobile_side"] == "0 1 0"
    assert axes["joint_mobile_yaw"] == "0 0 1"
    tree = ast.parse((checkout / "robocasa/robocasa/environments/kitchen/kitchen.py").read_text())
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
    assert any(
        k.arg == "load_model_on_init" and isinstance(k.value, ast.Constant) and k.value.value is False
        for c in calls
        for k in c.keywords
    )
    task = next(c for c in calls if isinstance(c.func, ast.Name) and c.func.id == "ManipulationTask")
    keys = {k.arg: k.value.value for k in task.keywords if isinstance(k.value, ast.Constant)}
    assert keys["enable_multiccd"] is True and keys["enable_sleeping_islands"] is False
    assert any(isinstance(n, ast.Constant) and n.value == "JOINT_VELOCITY_LEGACY" for n in ast.walk(tree))


@pytest.mark.parametrize("command", [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]])
@pytest.mark.parametrize("base_mode", [False, True])
def test_original_raw15_decoder_preserves_native_base_axes(command, base_mode):
    from scipy.spatial.transform import Rotation

    file = ROOT / "cosmos-framework/cosmos_framework/simulation/robocasa/eval_utils.py"
    nodes = [
        n
        for n in ast.parse(file.read_text()).body
        if isinstance(n, ast.FunctionDef)
        and n.name in {"rot6d_to_matrix", "decode_10d_to_env12", "decode_15d_to_env12"}
    ]
    scope = {"np": np, "R": Rotation}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(file), "exec"), scope)
    raw = np.zeros(15)
    raw[:3] = command
    raw[4] = 1 if base_mode else -1
    raw[8:14] = [1, 0, 0, 0, 1, 0]
    result = scope["decode_15d_to_env12"](raw, False)
    np.testing.assert_array_equal(result[7:10], command if base_mode else [0, 0, 0])
    assert result[11] == (1 if base_mode else -1)


def test_backport_body_matches_frozen_official_reference_AST(checkout):
    provenance = json.loads((DEFAULT_LOCK.parent / "source_provenance.json").read_text())
    for item in provenance["exact_backports"]:
        tree = ast.parse((checkout / "robosuite" / item["file"]).read_text())
        node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == item["class"])
        if item["method"]:
            node = next(n for n in node.body if isinstance(n, ast.FunctionDef) and n.name == item["method"])
        assert hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest() == item["ast_sha256"]


def test_target_kitchens_and_object_split_match_pinned_official_protocol(checkout):
    path = checkout / "robocasa/robocasa/utils/env_utils.py"
    node = next(
        n for n in ast.parse(path.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == "create_env"
    )
    branch = next(
        n
        for n in ast.walk(node)
        if isinstance(n, ast.If)
        and isinstance(n.test, ast.Compare)
        and isinstance(n.test.left, ast.Name)
        and n.test.left.id == "split"
        and any(isinstance(c, ast.Constant) and c.value == "target" for c in n.test.comparators)
    )
    observed = {}
    exec(compile(ast.Module(body=branch.body, type_ignores=[]), str(path), "exec"), observed)
    assert observed["obj_instance_split"] == "target"
    assert observed["layout_and_style_ids"] == list(zip(range(1, 11), range(1, 11)))
