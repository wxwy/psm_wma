"""CPU-only Wan canvas gates compared with the fixed Child classifier."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from g2.latent_cache.contract import make_recipe, preprocessing_recipe
from g2.latent_cache.encoding import (
    _CONSTRUCTOR,
    WanSingleFrameEncoder,
    validate_wan_canvas,
)
from g2.tests.test_view_vae_source import _fixture

ROOT = Path(__file__).resolve().parents[2]
CHILD = ROOT / "cosmos-framework"


@pytest.fixture(scope="module")
def native_resolution():
    path = CHILD / "cosmos_framework/utils/generator/image_resize.py"
    spec = importlib.util.spec_from_file_location("g2_native_canvas_reference", path)
    module = importlib.util.module_from_spec(spec)
    # Execute fixed source without importing a Cosmos package or writing Child pyc.
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module.get_vision_data_resolution


@pytest.mark.parametrize(
    "shape",
    [
        (16, 32),
        (256, 256),
        (272, 480),
        (640, 960),
        (656, 960),
        (720, 1280),
        (960, 2048),
        (256, 4096),
        (1024, 1024),
        (1184, 880),
        (880, 1184),
        (1360, 768),
        (768, 1360),
        (976, 1024),
        (2048, 2048),
        (2064, 2064),
    ],
)
def test_canvas_preflight_matches_native_classifier_and_fixed_constructor(
    shape, native_resolution
):
    try:
        tier = native_resolution(shape)
    except ValueError:
        with pytest.raises(ValueError):
            validate_wan_canvas(*shape)
    else:
        if tier in _CONSTRUCTOR["encode_chunk_frames"]:
            assert validate_wan_canvas(*shape) == tier
        else:
            with pytest.raises(ValueError, match="unsupported|Unsupported|support"):
                validate_wan_canvas(*shape)


@pytest.mark.parametrize(
    "shape", [(0, 256), (-16, 256), (255, 256), (256, 257), (True, 256), (256.0, 256)]
)
def test_canvas_preflight_rejects_invalid_dimensions(shape):
    with pytest.raises(ValueError):
        validate_wan_canvas(*shape)


def test_canvas_preflight_does_not_import_torch_wan_or_access_gpu():
    script = """
import builtins,sys
original=builtins.__import__
def guard(name,*args,**kwargs):
 if name=='torch' or name.startswith(('torch.','cosmos_framework','mujoco','rospy')):
  raise AssertionError('unexpected runtime import '+name)
 return original(name,*args,**kwargs)
builtins.__import__=guard
from g2.latent_cache.encoding import validate_wan_canvas
assert validate_wan_canvas(256,256)=='256'
assert validate_wan_canvas(480,640)=='480'
assert validate_wan_canvas(720,1280)=='720'
for shape in [(1024,1024),(2064,2064)]:
 try: validate_wan_canvas(*shape)
 except ValueError: pass
 else: raise AssertionError('unsupported canvas accepted')
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("shape", [(1024, 1024), (2064, 2064)])
def test_direct_encode_rejects_before_preprocessing_or_loading(
    tmp_path, monkeypatch, shape
):
    weights = tmp_path / "identity_only.weights"
    weights.write_bytes(b"CPU placeholder, not model weights")
    encoder = WanSingleFrameEncoder(weights, device="cpu", cosmos_root=CHILD)

    def forbidden(*args, **kwargs):
        pytest.fail("unsupported canvas reached preprocessing/model loading")

    monkeypatch.setattr("g2.latent_cache.encoding.preprocess_rgb", forbidden)
    monkeypatch.setattr(encoder, "_load", forbidden)
    with pytest.raises(ValueError):
        encoder.encode(np.zeros((2, 3, 3), np.uint8), preprocessing_recipe(*shape))
    assert encoder._tokenizer is None


@pytest.mark.parametrize(
    "shape", [None, (480, 640), (720, 1280), (1024, 1024), (2064, 2064)]
)
def test_cli_plan_supports_legal_canvas_and_refuses_other_tiers_model_free(
    tmp_path, shape
):
    episode = tmp_path / "episode"
    _fixture(episode)
    weights = tmp_path / "identity_only.weights"
    weights.write_bytes(b"CPU planning placeholder, not model weights")
    script = """
import sys
from tools.g2.build_spatial_view_vae_cache import main
status=main(sys.argv[1:])
assert not any(k=='torch' or k.startswith(('torch.','cosmos_framework','mujoco','rospy')) for k in sys.modules)
raise SystemExit(status)
"""
    command = [
        sys.executable,
        "-c",
        script,
        "--dataset-root",
        str(episode),
        "--weights",
        str(weights),
        "--device",
        "cpu",
        "--dry-run",
    ]
    if shape is not None:
        command += ["--height", str(shape[0]), "--width", str(shape[1])]
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=dict(
            os.environ,
            CUDA_VISIBLE_DEVICES="",
            PYTHONDONTWRITEBYTECODE="1",
            PYTHONPATH=str(ROOT),
        ),
        capture_output=True,
        text=True,
        check=False,
    )
    if shape is None or shape[0] in (480, 720):
        assert result.returncode == 0, result.stderr
        report = json.loads(result.stdout)
        canvas = report["results"][0]["recipe"]["preprocessing"]
        assert [canvas["height"], canvas["width"]] == list(shape or (256, 256))
        assert report["vae_loaded"] is False and report["gpu_accessed"] is False
    else:
        assert result.returncode == 2, result.stderr
        assert not result.stdout
    assert not (episode / "vae_cache").exists()


@pytest.mark.parametrize("shape", [(1024, 1024), (2064, 2064)])
def test_direct_plan_refuses_unsupported_canvas_without_writing_cache(tmp_path, shape):
    from g2.latent_cache.builder import plan_episode

    episode = tmp_path / "episode"
    _fixture(episode)
    recipe = make_recipe({"implementation": "TEST_ONLY"}, preprocessing_recipe(*shape))
    with pytest.raises(ValueError):
        plan_episode(episode, recipe)
    assert not (episode / "vae_cache").exists()
