"""Real CLI/config/discovery wildcard parity, synthetic task metadata only."""

import json
import sys
from pathlib import Path

import pytest
import yaml
from robocasa_eval_v2.cli import main
from robocasa_eval_v2.config import resolve
from robocasa_eval_v2.identity import ATOMIC_TASKS, discover


@pytest.fixture
def selection(tmp_path):
    inputs = tmp_path / "inputs"
    dataset = inputs / "dataset"
    for task in ATOMIC_TASKS:
        meta = dataset / task / "lerobot/extras/dataset_meta.json"
        meta.parent.mkdir(parents=True)
        meta.write_text(json.dumps({"env_args": {"env_name": task, "env_kwargs": {}}}))
    cfg = dict(
        schema="psm_robocasa_eval_v2",
        checkpoint=str(inputs / "checkpoint_NOT_PRESENT"),
        config_file=str(inputs / "model_NOT_PRESENT.yaml"),
        dataset_root=str(dataset),
        vendor_lock=str(inputs / "vendor_NOT_PRESENT.json"),
        output_dir=str(tmp_path / "evaluation_NOT_CREATED"),
        server_python=sys.executable,
        sim_python=sys.executable,
        gpu_ids=[7],
        execution_profile="phase_b",
        local_memory_mode="off",
        sims_per_gpu=2,
        max_infer_batch_size=2,
        episodes_per_task=2,
        tasks=["CloseFridge"],
    )
    path = tmp_path / "eval.yaml"
    path.write_text(yaml.safe_dump(cfg))
    return path, cfg


@pytest.mark.parametrize("mode", ["dry-run", "fresh", "resume"])
def test_cli_all_overrides_subset_and_matches_yaml_all_in_every_run_mode(
    selection, mode
):
    path, cfg = selection
    _, explicit = resolve([mode, "--config", str(path), "--tasks", "all"])
    assert explicit["tasks"] == "all"
    cfg["tasks"] = "all"
    path.write_text(yaml.safe_dump(cfg))
    _, yaml_only = resolve([mode, "--config", str(path)])
    assert explicit == yaml_only
    assert discover(explicit) == discover(yaml_only)
    assert [t for t, _ in discover(explicit)] == sorted(ATOMIC_TASKS)
    assert len(discover(explicit)) == 18
    assert not Path(cfg["output_dir"]).exists()


def test_default_all_yaml_all_and_cli_all_are_the_same_selection(selection):
    path, cfg = selection
    del cfg["tasks"]
    path.write_text(yaml.safe_dump(cfg))
    _, default = resolve(["dry-run", "--config", str(path)])
    _, explicit = resolve(["dry-run", "--config", str(path), "--tasks", "all"])
    assert default == explicit and default["tasks"] == "all"
    assert len(discover(default)) == 18


def test_csv_still_preserves_requested_order_and_overrides_yaml_all(selection):
    path, cfg = selection
    cfg["tasks"] = "all"
    path.write_text(yaml.safe_dump(cfg))
    ordered = ["OpenCabinet", "CloseFridge"]
    _, explicit = resolve(
        ["dry-run", "--config", str(path), "--tasks", ",".join(ordered)]
    )
    assert explicit["tasks"] == ordered
    assert [t for t, _ in discover(explicit)] == ordered
    cfg["tasks"] = ordered
    path.write_text(yaml.safe_dump(cfg))
    assert resolve(["dry-run", "--config", str(path)])[1] == explicit


@pytest.mark.parametrize(
    "value", ["all,CloseFridge", "all,all", "NoSuchTask", "", "ALL"]
)
def test_mixed_wildcard_duplicate_empty_or_unknown_names_remain_rejected(
    selection, value
):
    path, _ = selection
    with pytest.raises(ValueError):
        _, cfg = resolve(["dry-run", "--config", str(path), "--tasks", value])
        discover(cfg)


def test_all_still_requires_the_complete_18_task_metadata_catalog(selection):
    path, cfg = selection
    missing = (
        Path(cfg["dataset_root"]) / ATOMIC_TASKS[0] / "lerobot/extras/dataset_meta.json"
    )
    missing.unlink()  # Synthetic fixture only.
    _, explicit = resolve(["dry-run", "--config", str(path), "--tasks", "all"])
    with pytest.raises(ValueError, match="all requires18"):
        discover(explicit)
    cfg["tasks"] = "all"
    path.write_text(yaml.safe_dump(cfg))
    with pytest.raises(ValueError, match="all requires18"):
        discover(resolve(["dry-run", "--config", str(path)])[1])


def test_public_dry_run_cli_and_yaml_all_emit_same_18_task_plan_without_runtime(
    selection, capsys
):
    path, cfg = selection

    def forbidden(*args, **kwargs):
        pytest.fail("dry-run must not prepare model/runtime/environment")

    def preview(extra):
        assert (
            main(
                ["dry-run", "--config", str(path), *extra],
                prepare_inputs=forbidden,
                runtime_type=forbidden,
            )
            == 0
        )
        return json.loads(capsys.readouterr().out)

    cfg["tasks"] = "all"
    path.write_text(yaml.safe_dump(cfg))
    yaml_plan = preview([])
    cli_plan = preview(["--tasks", "all"])
    assert cli_plan == yaml_plan
    assert cli_plan["task_order"] == sorted(ATOMIC_TASKS)
    assert cli_plan["slots"] == [
        [task, ep] for ep in range(2) for task in sorted(ATOMIC_TASKS)
    ]
    assert cli_plan["models_loaded"] == cli_plan["environments_created"] == 0
    assert cli_plan["runtime_attested"] is False
    assert not Path(cfg["checkpoint"]).exists()
    assert not Path(cfg["config_file"]).exists()
    assert not Path(cfg["output_dir"]).exists()
