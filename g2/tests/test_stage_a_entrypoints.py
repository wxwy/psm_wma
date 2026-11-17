"""Original producer wiring and lightweight new-protocol/viewer entrypoints."""

import shutil
import subprocess
from pathlib import Path

import pytest

from g2.io import ContractError, write_json
from g2.offline import atomic_6views_plan as planner
from g2.offline import atomic_6views_run as producer
from g2.offline.output_profile import OutputProfile
from g2.offline.stage_a import package_stage_a
from g2.tests.test_stage_a_package import stage_case
from tools.g2.verify_spatial_profile import main as verify_main


def test_original_producer_sg_only_skips_color_and_f27_stages(tmp_path, monkeypatch):
    profile = OutputProfile(
        sixview_png=False,
        island_png=False,
        spatial_metadata=False,
        selection=False,
        language=False,
        marker_variants=False,
    )
    kwargs, _ = stage_case(tmp_path / "fixture", profile)
    original = tmp_path / "original"
    original.mkdir()
    (original / "model.xml.gz").write_bytes(b"TEST_ONLY_NEVER_LOADED")
    (original / "states.npz").write_bytes(b"TEST_ONLY_NEVER_LOADED")
    write_json(original / "ep_meta.json", kwargs["ep_meta"])
    observed = []

    def stage(work, name, row, builder, **options):
        observed.append(name)
        if name == "snapshots":
            return kwargs["inputs"].parent
        root = tmp_path / "stages" / name
        root.mkdir(parents=True, exist_ok=True)
        if name == "grid":
            write_json(
                root / "grid_plan.json",
                {"grid": {"resolution": 0.1, "dims": [2, 2, 2], "origin": [0, 0, 0]}},
            )
        return root

    monkeypatch.setattr(producer, "stage", stage)
    config = producer.WorkerConfig(
        nav_repo=tmp_path / "nav",
        nav_setup=tmp_path / "setup",
        native_binary=tmp_path / "native",
        python=Path("python"),
        output_root=tmp_path / "output",
        work_root=tmp_path / "work",
        keep_work=True,
        min_z=0.1,
        max_z=1.5,
        port=1234,
        gpu=0,
        robocasa_repo=tmp_path / "robocasa",
        robosuite_repo=tmp_path / "robosuite",
        sim_direct_geometry_only=True,
        sim_color_only=True,
        output_profile=profile,
    )
    row = dict(
        episode_id=0,
        task_class="NavigateKitchen",
        source_fingerprint="a" * 64,
        source_frames=21,
        spatial_frames=[0, 10, 20],
        layout_id=1,
        expected_relative_output="tasks/NavigateKitchen/episodes/episode_000000",
        original={
            name: str(original / name)
            for name in ("model.xml.gz", "ep_meta.json", "states.npz")
        },
    )
    result = producer.produce_one(row, config)
    assert result["profile_complete"]
    assert not set(observed) & {"prescan", "color", "native_dualmap", "f27"}
    assert observed[-1] == "snapshots"
    assert producer.produce_one(row, config) == result
    assert planner.completed_output(row, config.output_root, output_profile=profile)
    with pytest.raises(planner.PlanError, match="identity/recipe"):
        planner.completed_output(row, config.output_root)


def test_new_validator_cli_pending_exit_and_profile_identity(tmp_path, capsys):
    profile = OutputProfile(selection_top_variant="both", view_vae=True)
    kwargs, _ = stage_case(tmp_path, profile)
    target = tmp_path / "published"
    package_stage_a(destination=target, **kwargs)
    assert verify_main(["--episode-root", str(target)]) == 2
    assert verify_main(["--episode-root", str(target), "--allow-source-ready"]) == 75
    assert '"profile_complete": false' in capsys.readouterr().out
    other = tmp_path / "other.json"
    write_json(other, OutputProfile(selection_top_variant="clean").to_dict())
    assert (
        verify_main(
            [
                "--episode-root",
                str(target),
                "--allow-source-ready",
                "--output-profile",
                str(other),
            ]
        )
        == 2
    )


def test_profile_config_change_after_dispatch_is_rejected(tmp_path):
    profile = tmp_path / "profile.json"
    write_json(profile, OutputProfile(selection_top_variant="clean").to_dict())
    args = producer.parser().parse_args(["scan", "--output-profile", str(profile)])
    args.output_profile_sha256 = planner.sha_file(profile)
    assert producer._output_profile(args).selection_top_variant == "clean"
    write_json(profile, OutputProfile(selection_top_variant="both").to_dict())
    with pytest.raises(ContractError, match="changed after dispatch"):
        producer._output_profile(args)


def test_viewer_multroom_variants_count_canonical_directions():
    node = shutil.which("node")
    assert node is not None, (
        "Node is needed for this UI contract test; do not install implicitly"
    )
    script = Path(__file__).with_name("viewer_stage_a_variants_smoke.js")
    result = subprocess.run(
        [node, str(script)], capture_output=True, text=True, timeout=20
    )
    assert result.returncode == 0, result.stderr
    assert "CANONICAL_COUNT_PASS" in result.stdout
