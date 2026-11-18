"""Thin posthoc CLI uses shared real CPU ledger; no Wan/network/native run."""

import json
import subprocess
import sys

import pytest

from g2.io import digest, read_json, write_json
from g2.latent_cache import encoding, ledger_archive
from g2.offline.view_only_source import PACKED
from g2.tests.test_view_first_recovery import ready_job
from g2.tests.test_view_first_retirement import encode_case, retirement_case
from g2.tests.test_view_vae_builder import FakeEncoder
from g2.tests.test_working_source_access import view_first_case
from tools.g2 import build_spatial_view_vae_cache as build_cli
from tools.g2 import retire_view_first_sources as retire_cli


def retirement_args(tmp_path, root, policy, *, action="--plan"):
    path = tmp_path / "policy.json"
    write_json(path, policy)
    recipe = read_json(root / "vae_cache/manifest.json")["recipe"]["recipe_id"]
    return [
        "--dataset-root",
        policy["output_root"],
        "--spool-root",
        policy["spool_root"],
        "--source-policy",
        str(path),
        "--recipe-id",
        recipe,
        action,
    ]


def test_existing_build_cli_requires_explicit_view_first_and_preserves_old_output(
    tmp_path, monkeypatch, capsys
):
    root = view_first_case(tmp_path)
    original = {
        p: digest(root / p) for p in ("COMPLETE.json", "episode_manifest.json", PACKED)
    }
    encoder = FakeEncoder()
    monkeypatch.setattr(encoding, "WanSingleFrameEncoder", lambda *a, **k: encoder)
    common = [
        "--dataset-root",
        str(root),
        "--weights",
        str(tmp_path / "TEST_ONLY_FAKE"),
        "--height",
        "32",
        "--width",
        "32",
    ]
    assert build_cli.main(common + ["--plan"]) == 2
    capsys.readouterr()
    assert build_cli.main(common + ["--view-first", "--plan"]) == 0
    assert (
        json.loads(capsys.readouterr().out)["results"][0]["physical_image_count"] == 5
    )
    assert not (root / "vae_cache").exists()
    assert (
        build_cli.main(
            common
            + ["--view-first", "--execute", "--spool-root", str(tmp_path / "spool")]
        )
        == 0
    )
    assert encoder.calls == 5 and original == {p: digest(root / p) for p in original}


def test_retire_cli_plan_is_readonly_execute_and_repeat_need_no_encoder(
    tmp_path, monkeypatch, capsys
):
    root, policy = retirement_case(tmp_path)
    encode_case(tmp_path, root)
    args = retirement_args(tmp_path, root, policy)
    assert retire_cli.main(args) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["vae_loaded"] is False and not report["results"][0]["source_retired"]
    assert (root / PACKED).exists() and not (tmp_path / "retirement_spool").exists()
    monkeypatch.setattr(
        encoding,
        "WanSingleFrameEncoder",
        lambda *a, **kw: pytest.fail("retirement must not instantiate VAE"),
    )
    assert retire_cli.main(args[:-1] + ["--execute"]) == 0
    capsys.readouterr()
    assert not (root / PACKED).exists()
    assert retire_cli.main(args[:-1] + ["--execute", "--resume"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["results"][0]["already_complete"]


@pytest.mark.parametrize("mode", ["count", "recipe"])
def test_cli_scope_conflicts_start_no_retirement(tmp_path, mode):
    root, policy = retirement_case(tmp_path)
    encode_case(tmp_path, root)
    args = retirement_args(tmp_path, root, policy, action="--execute")
    if mode == "count":
        args += ["--expected-episodes", "2"]
    else:
        args[args.index("--recipe-id") + 1] = "0" * 64
    assert retire_cli.main(args) == 2
    assert (root / PACKED).exists() and not (
        root / "spatial_source_index.json"
    ).exists()


def test_retire_cli_recovers_swapped_source_before_episode_discovery(
    tmp_path, monkeypatch, capsys
):
    root, policy, spool, job = ready_job(tmp_path, monkeypatch)
    args = retirement_args(tmp_path, root, policy, action="--execute")

    def stop(phase):
        if phase == "capsule_published:episode_manifest.json":
            raise RuntimeError("TEST_ONLY_MIXED_INDICES")

    with pytest.raises(RuntimeError):
        ledger_archive.archive(spool, job, failpoint=stop)
    assert retire_cli.main(args) == 75
    capsys.readouterr()
    assert retire_cli.main(args + ["--resume"]) == 0
    assert not (root / PACKED).exists()


def test_new_cli_help_imports_no_model_or_renderer():
    script = """import sys
from tools.g2 import retire_view_first_sources as cli
try: cli.main(['--help'])
except SystemExit as e: assert e.code == 0
assert 'torch' not in sys.modules and 'mujoco' not in sys.modules
assert not any('wan2pt2' in k for k in sys.modules)
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", script], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
