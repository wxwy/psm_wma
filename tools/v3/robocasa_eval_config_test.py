"""CPU-only configuration contract: parsing never starts a model or claims output."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("robocasa_eval_config", ROOT / "scripts/robocasa_eval_config.py")
config = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(config)


@pytest.fixture
def base(tmp_path):
    return {
        "schema": config.SCHEMA,
        "checkpoint": str(tmp_path / "job/checkpoints/iter_000008900"),
        "dataset_root": str(tmp_path / "data"),
        "output_root": str(tmp_path / "evaluations"),
        "run_name": "case01",
        "server_python": sys.executable,
        "sim_python": sys.executable,
        "tasks": ["CloseFridge", "TurnOnSinkFaucet"],
        "episodes_per_task": 5,
        "gpu_ids": [2, 3],
    }


def write(tmp_path, data):
    # JSON is valid safe YAML; no test-specific parser replacement.
    path = tmp_path / "eval.yaml"
    path.write_text(json.dumps(data))
    return path


def test_cli_yaml_defaults_precedence_and_no_output_writes(tmp_path, base):
    base["timeouts"] = {"server_start_s": 120, "predict_request_s": 90}
    args = config.resolve(
        [
            "--config",
            str(write(tmp_path, base)),
            "--gpus",
            "4,5",
            "--episodes",
            "7",
            "--tasks",
            "TurnOnSinkFaucet",
            "--run-name",
            "override",
            "--save-generated-video",
            "all",
            "--no-save-rollout-mp4",
            "--task-wall-timeout-s",
            "240",
        ]
    )
    assert args.gpus == "4,5" and args.gpu_ids == [4, 5]
    assert args.tasks == ["TurnOnSinkFaucet"] and args.num_test_episodes == 7
    assert args.save_generated_video == "all" and args.save_rollout_mp4 is False
    assert args.output_dir == tmp_path / "evaluations/override"
    assert args.server_start_timeout_s == 120 and args.predict_request_timeout_s == 90
    assert args.task_wall_timeout_s == 240 and args.episode_wall_timeout_s == 1800
    assert args.action_horizon == 16 and args.num_steps == 30 and args.local_memory_mode == "required"
    assert args.config_file == tmp_path / "job/config.yaml"
    assert not args.output_dir.exists()
    json.dumps(args.resolved_config, allow_nan=False)


def test_progress_defaults_are_enabled_and_available_in_resolved_dry_run(tmp_path, base):
    args = config.resolve(["--config", str(write(tmp_path, base)), "--dry-run"])
    assert args.progress is True and args.progress_interval_s == 5.0
    assert args.resolved_config["progress"] is True
    assert args.resolved_config["progress_interval_s"] == 5.0
    assert not args.output_dir.exists()


def test_owner_legacy_relocation_cli_optin_requires_resume_and_does_not_change_defaults(tmp_path, base):
    path = write(tmp_path, base)
    default = config.resolve(["--config", str(path)])
    assert default.allow_relocated_legacy_checkpoint is False
    assert default.resolved_config["allow_relocated_legacy_checkpoint"] is False
    with pytest.raises(ValueError, match="requires --resume"):
        config.resolve(["--config", str(path), "--allow-relocated-legacy-checkpoint"])
    approved = config.resolve([
        "--config", str(path), "--resume", "--allow-relocated-legacy-checkpoint", "--dry-run",
    ])
    assert approved.resume is True and approved.dry_run is True
    assert approved.allow_relocated_legacy_checkpoint is True
    assert approved.resolved_config["allow_relocated_legacy_checkpoint"] is True
    disallowed = config.resolve(["--config", str(path), "--resume", "--no-allow-relocated-legacy-checkpoint"])
    assert disallowed.allow_relocated_legacy_checkpoint is False


@pytest.mark.parametrize("bad", [1, "true", None, {}, []])
def test_legacy_relocation_yaml_requires_exact_bool(tmp_path, base, bad):
    base.update(allow_relocated_legacy_checkpoint=bad, resume=True)
    with pytest.raises(ValueError, match="allow_relocated_legacy_checkpoint"):
        config.resolve(["--config", str(write(tmp_path, base))])


@pytest.mark.parametrize("enabled,interval", [(False, 1), (True, 2.5)])
def test_yaml_progress_is_strictly_resolved(tmp_path, base, enabled, interval):
    base.update(progress=enabled, progress_interval_s=interval)
    args = config.resolve(["--config", str(write(tmp_path, base))])
    assert args.progress is enabled and args.progress_interval_s == interval


@pytest.mark.parametrize("yaml_progress,flag,expected", [(False, "--progress", True), (True, "--no-progress", False)])
def test_progress_cli_overrides_yaml_and_leaves_execution_controls_unchanged(
    tmp_path, base, yaml_progress, flag, expected
):
    base.update(progress=yaml_progress, progress_interval_s=2.5, resume=True)
    base["timeouts"] = {"server_start_s": 47, "predict_request_s": 23, "task_wall_s": 100}
    path = write(tmp_path, base)
    before = config.resolve(["--config", str(path)])
    after = config.resolve(["--config", str(path), flag, "--progress-interval-s", "0.25"])
    assert after.progress is expected and after.progress_interval_s == 0.25
    presentation = {"progress", "progress_interval_s"}
    assert {key: value for key, value in before.resolved_config.items() if key not in presentation} == {
        key: value for key, value in after.resolved_config.items() if key not in presentation
    }
    assert after.resume is before.resume is True
    assert after.task_wall_timeout_s == before.task_wall_timeout_s == 100
    assert after.predict_request_timeout_s == before.predict_request_timeout_s == 23


def test_legacy_cli_remains_explicit_and_aliases_override(tmp_path, base):
    args = config.resolve(
        [
            "--checkpoint-path",
            base["checkpoint"],
            "--dataset-root",
            base["dataset_root"],
            "--output-dir",
            str(tmp_path / "legacy"),
            "--server-python",
            sys.executable,
            "--sim-python",
            sys.executable,
            "--gpus",
            "0,1",
            "--expected-tasks",
            "4",
            "--tasks",
            "CloseFridge",
            "--num-test-episodes",
            "5",
            "--num-steps",
            "11",
            "--timeout",
            "12",
            "--predict-request-timeout-s",
            "14",
            "--resume",
        ]
    )
    assert args.checkpoint_path == Path(base["checkpoint"])
    assert args.expected_tasks == 4 and args.num_test_episodes == 5 and args.num_steps == 11
    assert args.server_start_timeout_s == 12 and args.predict_request_timeout_s == 14
    assert args.resume is True and args.tasks == ["CloseFridge"]


def test_list_tasks_needs_only_dataset(tmp_path):
    args = config.resolve(["--dataset-root", str(tmp_path), "--list-tasks"])
    assert args.list_tasks and args.checkpoint is None and args.output_dir is None
    assert not (tmp_path / "evaluation_manifest.json").exists()


def test_all_tasks_cannot_redefine_the_18_class_protocol(tmp_path, base):
    with pytest.raises(ValueError, match="exactly 18"):
        config.resolve(["--config", str(write(tmp_path, base)), "--tasks", "all", "--expected-tasks", "4"])


def test_yaml_paths_are_relative_to_yaml_and_python_venv_symlink_retained(tmp_path, base):
    executable = tmp_path / "python"
    executable.symlink_to(sys.executable)
    base.update(
        checkpoint="job/checkpoints/iter_000008900",
        dataset_root="data",
        output_root="results",
        server_python="python",
        sim_python="python",
    )
    args = config.resolve(["--config", str(write(tmp_path, base)), "--dry-run"])
    assert args.checkpoint_path == tmp_path / "job/checkpoints/iter_000008900"
    assert args.server_python == executable and args.sim_python == executable
    assert args.output_dir == tmp_path / "results/case01" and args.dry_run


def test_cli_output_dir_replaces_yaml_namespace(tmp_path, base):
    args = config.resolve(["--config", str(write(tmp_path, base)), "--output-dir", str(tmp_path / "other")])
    assert args.output_dir == tmp_path / "other"
    assert "output_root" not in args.resolved_config and "run_name" not in args.resolved_config


def test_cli_namespace_replaces_yaml_output_dir(tmp_path, base):
    base.pop("output_root")
    base.pop("run_name")
    base["output_dir"] = str(tmp_path / "old")
    args = config.resolve(["--config", str(write(tmp_path, base)), "--output-root", str(tmp_path), "--run-name", "new"])
    assert args.output_dir == tmp_path / "new"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema", "v2"),
        ("unexpected", True),
        ("tasks", []),
        ("tasks", ""),
        ("tasks", ["CloseFridge", "CloseFridge"]),
        ("tasks", ["../escape"]),
        ("tasks", ["CloseFridge", "all"]),
        ("gpu_ids", []),
        ("gpu_ids", [1, 1]),
        ("gpu_ids", [True]),
        ("gpu_ids", [-1]),
        ("gpu_ids", [1.0]),
        ("gpu_ids", "1,,2"),
        ("gpu_ids", [1, "01"]),
        ("gpu_ids", ""),
        ("episodes_per_task", 0),
        ("episodes_per_task", True),
        ("slots_per_gpu", 2),
        ("base_port", 65535),
        ("base_port", -1),
        ("prediction_steps", 0),
        ("action_horizon", 17),
        ("action_horizon", 0),
        ("seed", True),
        ("seed", -1),
        ("guidance", float("nan")),
        ("guidance", float("inf")),
        ("guidance", True),
        ("fps", 30),
        ("local_memory_mode", "off"),
        ("server_lifecycle", "reuse"),
        ("on_infrastructure_error", "ignore"),
        ("save_generated_video", "yes"),
        ("save_rollout_mp4", "false"),
        ("save_init_png", 1),
        ("save_action_jsonl", False),
        ("save_prediction_jsonl", False),
        ("resume", "true"),
        ("progress", 1),
        ("progress", 0),
        ("progress", "false"),
        ("progress", None),
        ("progress_interval_s", True),
        ("progress_interval_s", False),
        ("progress_interval_s", 0),
        ("progress_interval_s", -1),
        ("progress_interval_s", float("nan")),
        ("progress_interval_s", float("inf")),
        ("progress_interval_s", -float("inf")),
        ("progress_interval_s", "5"),
        ("progress_interval_s", None),
        ("run_name", "../old"),
        ("run_name", "."),
        ("run_name", ""),
        ("dataset_root", ""),
        ("sim_python", "/not/executable"),
        ("server_python", "/not/executable"),
        ("timeouts", {"unknown": 1}),
        ("timeouts", []),
        ("timeouts", {"server_start_s": 0}),
        ("timeouts", {"predict_request_s": float("inf")}),
        ("timeouts", {"terminate_grace_s": True}),
    ],
)
def test_invalid_config_fails_closed(tmp_path, base, field, value):
    base[field] = value
    with pytest.raises(ValueError):
        config.resolve(["--config", str(write(tmp_path, base))])
    assert not (tmp_path / "evaluations").exists()


@pytest.mark.parametrize(
    "text",
    [
        "schema: psm_wma_robocasa_eval_v1\nschema: psm_wma_robocasa_eval_v1\n",
        "schema: psm_wma_robocasa_eval_v1\ntimeouts:\n  server_start_s: 1\n  server_start_s: 2\n",
        "[one, two]\n",
        "schema: [\n",
        "!!python/object:os.system {}",
    ],
)
def test_malformed_or_duplicate_yaml_rejected(tmp_path, text):
    path = tmp_path / "bad.yaml"
    path.write_text(text)
    with pytest.raises(ValueError):
        config.resolve(["--config", str(path)])


@pytest.mark.parametrize(
    "args",
    [
        ["--gpus", "1,1"],
        ["--gpus", "1,,2"],
        ["--tasks", "CloseFridge,"],
        ["--timeout", "nan"],
        ["--terminate-grace-s", "0"],
        ["--slots-per-gpu", "2"],
        ["--progress-interval-s", "nan"],
        ["--progress-interval-s", "inf"],
        ["--progress-interval-s", "0"],
        ["--progress-interval-s", "-1"],
        ["--output-dir", "out", "--run-name", "run"],
    ],
)
def test_invalid_cli_overrides_rejected(tmp_path, base, args):
    with pytest.raises(ValueError):
        config.resolve(["--config", str(write(tmp_path, base)), *args])


def test_unknown_cli_not_silently_ignored(tmp_path):
    with pytest.raises(SystemExit) as caught:
        config.resolve(["--dataset-root", str(tmp_path), "--list-tasks", "--ignore-errors"])
    assert caught.value.code == 2


def test_example_schema_is_parsed_by_actual_safe_yaml_loader():
    example = config._yaml(ROOT / "configs/eval/robocasa_g1_iter8900.example.yaml")
    assert example["schema"] == config.SCHEMA
    assert example["tasks"] == ["CloseFridge", "TurnOnSinkFaucet"]
    assert example["gpu_ids"] == [2, 3] and example["save_generated_video"] == "first"
