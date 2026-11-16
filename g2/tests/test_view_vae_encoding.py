"""CPU contracts only: fake Wan is not evidence of real VAE/GPU parity."""

import copy
import hashlib
import importlib
import json
import os
import py_compile
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from g2.latent_cache.encoding import WanSingleFrameEncoder, preprocess_rgb

ROOT = Path(__file__).resolve().parents[2]
CHILD = ROOT / "cosmos-framework"


def recipe(height=32, width=32, interpolation="nearest"):
    return {
        "height": height,
        "width": width,
        "interpolation": interpolation,
        "padding_rgb": [255, 255, 255],
        "aspect": "fit",
        "rounding": "floor_half_up",
        "layout": "RGB_HWC",
    }


@pytest.mark.parametrize(
    "shape,resized,padding",
    [
        ((8, 16, 3), [16, 32], {"top": 8, "bottom": 8, "left": 0, "right": 0}),
        ((16, 8, 3), [32, 16], {"top": 0, "bottom": 0, "left": 8, "right": 8}),
        ((11, 11, 3), [32, 32], {"top": 0, "bottom": 0, "left": 0, "right": 0}),
        ((1, 17, 3), [2, 32], {"top": 15, "bottom": 15, "left": 0, "right": 0}),
    ],
)
def test_fit_geometry_and_padding_are_recorded_without_rgb_inference(
    shape, resized, padding
):
    pixels = np.full(shape, 255, np.uint8)
    before = pixels.copy()
    out, meta = preprocess_rgb(pixels, recipe())
    assert out.shape == (32, 32, 3) and out.dtype == np.uint8
    assert np.array_equal(out, np.full_like(out, 255))
    assert np.array_equal(pixels, before) and not np.shares_memory(out, pixels)
    assert meta["original_hw"] == list(shape[:2])
    assert meta["resized_hw"] == resized and meta["padding"] == padding
    assert meta["valid_region"]["basis"] == "resize_and_pad_geometry_not_rgb"
    assert meta["valid_region"]["box_xyxy"] == meta["content_box"]
    assert meta["pillow_version"]


def test_exact_half_up_and_odd_padding_placement():
    out, meta = preprocess_rgb(np.zeros((3, 4, 3), np.uint8), recipe(8, 6))
    # 3 * (6/4) = 4.5 -> 5, with the extra pad pixel below the source.
    assert meta["resized_hw"] == [5, 6]
    assert meta["padding"] == {"top": 1, "bottom": 2, "left": 0, "right": 0}
    assert meta["content_box"] == [0, 1, 6, 6]
    assert not out[1:6].any() and (out[:1] == 255).all() and (out[6:] == 255).all()


@pytest.mark.parametrize("interpolation", ["nearest", "bilinear", "lanczos"])
def test_rgb_channel_order_and_existing_marker_are_not_redrawn(interpolation):
    pixels = np.full((16, 32, 3), 255, np.uint8)
    pixels[5:9, 12:16] = [22, 103, 217]
    out, meta = preprocess_rgb(pixels, recipe(interpolation=interpolation))
    assert np.array_equal(out[8:24], pixels)
    assert out[13, 12].tolist() == [22, 103, 217]
    assert meta["content_box"] == [0, 8, 32, 24]


@pytest.mark.parametrize(
    "pixels",
    [
        np.zeros((3, 8, 8), np.uint8),
        np.zeros((8, 8, 4), np.uint8),
        np.zeros((8, 8, 3), np.float32),
        np.zeros((0, 8, 3), np.uint8),
        np.zeros((2, 8, 8, 3), np.uint8),
        [[[0, 0, 0]]],
    ],
)
def test_preprocessing_rejects_wrong_layout_dtype_empty_or_batch(pixels):
    with pytest.raises(ValueError, match="RGB HWC"):
        preprocess_rgb(pixels, recipe())


@pytest.mark.parametrize(
    "key,value",
    [
        ("height", True),
        ("width", 0),
        ("padding_rgb", [0, 0, 0]),
        ("padding_rgb", [255.0, 255, 255]),
        ("interpolation", "bicubic"),
        ("aspect", "stretch"),
        ("rounding", "bankers"),
        ("layout", "BGR_HWC"),
    ],
)
def test_recipe_is_explicit_and_has_no_bucket_fallback(key, value):
    config = recipe()
    config[key] = value
    with pytest.raises(ValueError):
        preprocess_rgb(np.zeros((8, 8, 3), np.uint8), config)


class FakeWan:
    """Produces a deliberate non-inferred 2x3 grid; no network is instantiated."""

    def __init__(self, constructor_config, **kwargs):
        module = torch.nn.Linear(1, 1, bias=False).to(dtype=torch.bfloat16)
        module.eval().requires_grad_(False)
        module._enc_cache = [None]
        module._enc_stream_shape = None
        module.temporal_window = copy.deepcopy(
            constructor_config["encode_chunk_frames"]
        )
        module._encode_exact_durations = set(
            constructor_config["encode_exact_durations"]
        )
        self.model = SimpleNamespace(model=module, dtype=torch.bfloat16)
        self.is_causal = True
        self.use_streaming_encode = False
        self._keep_encoder_cache = self._keep_decoder_cache = False
        self.spatial_compression_factor = 16
        self.temporal_compression_factor = 4
        self.chunk_duration = constructor_config["chunk_duration"]
        self.encode_chunk_frames = copy.deepcopy(
            constructor_config["encode_chunk_frames"]
        )
        self.encode_exact_durations = list(constructor_config["encode_exact_durations"])
        self.calls = []
        self.failure = None

    def encode(self, pixels):
        assert tuple(pixels.shape) == (1, 3, 1, 32, 32)
        assert pixels.dtype == torch.float32 and not torch.is_grad_enabled()
        assert not torch.is_autocast_enabled("cpu")
        assert -1 <= pixels.min() <= pixels.max() <= 1
        self.calls.append(pixels.detach().clone())
        out = pixels.mean().reshape(1, 1, 1, 1, 1).expand(1, 48, 1, 2, 3).clone()
        if self.failure == "nan":
            out[0, 0, 0, 0, 0] = float("nan")
        if self.failure == "dtype":
            out = out.to(torch.float16)
        if self.failure == "time":
            out = out.repeat(1, 1, 2, 1, 1)
        if self.failure == "batch":
            out = out.repeat(2, 1, 1, 1, 1)
        if self.failure == "empty":
            out = out[:, :, :, :0]
        if self.failure == "retained":
            self.model.model._enc_cache[0] = torch.ones(1)
        return out


@pytest.fixture
def encoder(tmp_path):
    weights = tmp_path / "weights.pth"
    weights.write_bytes(b"CPU_FAKE_NOT_REAL_WAN_WEIGHTS")
    made = []

    def factory(**kwargs):
        model = FakeWan(**kwargs)
        made.append(model)
        return model

    obj = WanSingleFrameEncoder(
        weights, device="cpu", cosmos_root=CHILD, _tokenizer_factory=factory
    )
    return obj, made


def test_descriptor_and_constructor_do_not_import_torch_wan_or_touch_gpu(tmp_path):
    weights = tmp_path / "weights.pth"
    weights.write_bytes(b"not_loaded")
    code = """
import builtins,json,sys
real=builtins.__import__
def guard(name,*args,**kwargs):
 if name=='torch' or name.startswith(('torch.','cosmos_framework.','mujoco','rospy')):
  raise AssertionError('unexpected heavy import '+name)
 return real(name,*args,**kwargs)
builtins.__import__=guard
from g2.latent_cache.encoding import WanSingleFrameEncoder
obj=WanSingleFrameEncoder(sys.argv[1],cosmos_root=sys.argv[2],device='cuda:9999')
value=obj.descriptor()
assert 'torch' not in sys.modules and value['input_time']==1
assert value['compute_dtype']=='bfloat16' and value['streaming'] is False
print(json.dumps(value))
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(weights), str(CHILD)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["test_only"] is False


def test_fake_abi_reuses_real_normalizer_one_loaded_model_and_preserves_complete_grid(
    encoder,
):
    obj, made = encoder
    first = obj.descriptor()
    assert not made and first["test_only"] is True
    # Mutation of a returned descriptor cannot change the held configuration.
    first["constructor"]["encode_chunk_frames"]["256"] = 4
    assert obj.descriptor()["constructor"]["encode_chunk_frames"]["256"] == 68
    dark = np.zeros((32, 32, 3), np.uint8)
    a, meta = obj.encode(dark, recipe())
    b, _ = obj.encode(np.full_like(dark, 255), recipe())
    again, _ = obj.encode(dark, recipe())
    assert len(made) == 1 and len(made[0].calls) == 3
    module = importlib.import_module("cosmos_framework.model.generator.vision_encoder")
    assert obj._normalizer is module.normalize_uint8_item
    assert a.shape == (48, 2, 3) and a.dtype == torch.float32 and a.device.type == "cpu"
    assert torch.equal(a, torch.full_like(a, -1)) and torch.equal(b, torch.ones_like(b))
    assert torch.equal(a, again) and a.data_ptr() != again.data_ptr()
    assert meta["latent_shape"] == [48, 2, 3] and meta["vae_input_shape"] == [
        1,
        3,
        1,
        32,
        32,
    ]
    assert meta["temporal_dimension_removed"] is True
    assert "NOT_INFERRED" in meta["valid_region"]["latent_patch_mask"]


def test_no_external_autocast_changes_the_declared_encoding_contract(encoder):
    obj, _ = encoder
    with torch.autocast("cpu", dtype=torch.bfloat16):
        out, _ = obj.encode(np.zeros((32, 32, 3), np.uint8), recipe())
    assert out.dtype == torch.float32


@pytest.mark.parametrize(
    "failure", ["nan", "dtype", "time", "batch", "empty", "retained"]
)
def test_invalid_output_or_retained_state_never_becomes_a_record(encoder, failure):
    obj, made = encoder
    obj.encode(np.zeros((32, 32, 3), np.uint8), recipe())
    made[0].failure = failure
    with pytest.raises((ValueError, RuntimeError)):
        obj.encode(np.zeros((32, 32, 3), np.uint8), recipe())


@pytest.mark.parametrize(
    "mutation", ["streaming", "cached", "training", "gradient", "dtype", "config"]
)
def test_mutated_loaded_encoder_is_rejected_before_next_encode(encoder, mutation):
    obj, made = encoder
    obj.encode(np.zeros((32, 32, 3), np.uint8), recipe())
    token = made[0]
    if mutation == "streaming":
        token.use_streaming_encode = True
    if mutation == "cached":
        token._keep_encoder_cache = True
    if mutation == "training":
        token.model.model.train()
    if mutation == "gradient":
        next(token.model.model.parameters()).requires_grad_(True)
    if mutation == "dtype":
        token.model.model.float()
    if mutation == "config":
        token.encode_chunk_frames["256"] = 4
    with pytest.raises(RuntimeError):
        obj.encode(np.zeros((32, 32, 3), np.uint8), recipe())
    assert len(token.calls) == 1


def test_changed_weights_are_rejected_without_loading_any_encoder(encoder):
    obj, made = encoder
    obj.descriptor()
    obj.weights_path.write_bytes(b"changed")
    with pytest.raises(RuntimeError, match="changed"):
        obj.encode(np.zeros((32, 32, 3), np.uint8), recipe())
    assert not made


def test_changed_source_is_a_different_identity_and_existing_descriptor_fails(tmp_path):
    from g2.latent_cache.encoding import _SOURCE_FILES

    child = tmp_path / "cosmos"
    for rel in _SOURCE_FILES:
        p = child / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes((CHILD / rel).read_bytes())
    weights = tmp_path / "weights"
    weights.write_bytes(b"not_loaded")
    obj = WanSingleFrameEncoder(weights, device="cpu", cosmos_root=child)
    before = obj.descriptor()
    path = child / _SOURCE_FILES[0]
    path.write_text(path.read_text() + "\n# changed source\n")
    with pytest.raises(RuntimeError, match="changed"):
        obj.descriptor()
    after = WanSingleFrameEncoder(weights, device="cpu", cosmos_root=child).descriptor()
    assert before["cosmos_source_sha256"] != after["cosmos_source_sha256"]


def test_weight_and_parent_symlinks_are_rejected(tmp_path):
    weights = tmp_path / "weights"
    weights.write_bytes(b"not_loaded")
    link = tmp_path / "link"
    link.symlink_to(weights)
    with pytest.raises(ValueError, match="symbolic"):
        WanSingleFrameEncoder(link, cosmos_root=CHILD).descriptor()
    directory = tmp_path / "alias"
    directory.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match="symbolic"):
        WanSingleFrameEncoder(directory / "weights", cosmos_root=CHILD).descriptor()


def test_invalid_canvas_is_rejected_before_loading(encoder):
    obj, made = encoder
    with pytest.raises(ValueError, match="multiples of 16"):
        obj.encode(np.zeros((8, 8, 3), np.uint8), recipe(31, 32))
    assert not made


@pytest.mark.parametrize(
    "field,new", [("device", "cuda"), ("cosmos_root", Path("/another/root"))]
)
def test_configuration_cannot_change_after_descriptor(encoder, field, new):
    obj, made = encoder
    obj.descriptor()
    setattr(obj, field, new)
    with pytest.raises(RuntimeError, match="configuration changed"):
        obj.encode(np.zeros((32, 32, 3), np.uint8), recipe())
    assert not made


def test_weights_changed_by_loader_are_rejected(tmp_path):
    path = tmp_path / "weights"
    path.write_bytes(b"original")

    def factory(**kwargs):
        path.write_bytes(b"tampered while loading")
        return FakeWan(**kwargs)

    obj = WanSingleFrameEncoder(
        path, device="cpu", cosmos_root=CHILD, _tokenizer_factory=factory
    )
    with pytest.raises(RuntimeError, match="weights changed while loading"):
        obj.encode(np.zeros((32, 32, 3), np.uint8), recipe())


def test_new_encoder_cannot_use_old_imported_source_after_source_change(tmp_path):
    from g2.latent_cache.encoding import _IMPORTED_SOURCE

    name = "g2_vae_import_probe"
    path = tmp_path / (name + ".py")
    path.write_text("VALUE=1\n")
    weights = tmp_path / "weights"
    weights.write_bytes(b"not_loaded")
    obj = WanSingleFrameEncoder(weights, device="cpu", cosmos_root=tmp_path)
    try:
        module = obj._cosmos_module(name, name + ".py")
        assert module.VALUE == 1
        path.write_text("VALUE=222\n")
        newer = WanSingleFrameEncoder(weights, device="cpu", cosmos_root=tmp_path)
        with pytest.raises(RuntimeError, match="source changed"):
            newer._cosmos_module(name, name + ".py")
    finally:
        sys.modules.pop(name, None)
        _IMPORTED_SOURCE.pop(name, None)


def test_external_preload_cannot_be_attested_using_changed_disk_source(
    tmp_path, monkeypatch
):
    from g2.latent_cache.encoding import _IMPORTED_SOURCE

    name = "g2_vae_external_preload_probe"
    path = tmp_path / (name + ".py")
    path.write_text("VALUE=1\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    module = importlib.import_module(name)
    assert module.VALUE == 1 and name not in _IMPORTED_SOURCE
    path.write_text("VALUE=222\n")
    weights = tmp_path / "weights"
    weights.write_bytes(b"not_loaded")
    obj = WanSingleFrameEncoder(weights, device="cpu", cosmos_root=tmp_path)
    try:
        with pytest.raises(RuntimeError, match="preloaded module"):
            obj._cosmos_module(name, name + ".py")
        assert module.VALUE == 1 and name not in _IMPORTED_SOURCE
    finally:
        sys.modules.pop(name, None)


@pytest.mark.parametrize("external_dependency", [False, True])
def test_controlled_import_binds_transitive_dependencies_but_refuses_external_ones(
    tmp_path, external_dependency
):
    package = tmp_path / "cosmos_framework"
    package.mkdir()
    (package / "__init__.py").write_text("")
    (package / "g2_probe_flags.py").write_text("VALUE=1\n")
    (package / "g2_probe_primary.py").write_text(
        "from . import g2_probe_flags\nVALUE=g2_probe_flags.VALUE+1\n"
    )
    weights = tmp_path / "weights"
    weights.write_bytes(b"not_loaded")
    code = """
import importlib,sys
from pathlib import Path
import g2.latent_cache.encoding as encoding
root=Path(sys.argv[1]);external=sys.argv[2]=='True'
encoding._SOURCE_FILES=(
 'cosmos_framework/g2_probe_primary.py',
 'cosmos_framework/g2_probe_flags.py',
)
if external:
 sys.path.insert(0,str(root))
 old=importlib.import_module('cosmos_framework.g2_probe_flags')
 sys.path.remove(str(root))
 (root/'cosmos_framework/g2_probe_flags.py').write_text('VALUE=222\\n')
obj=encoding.WanSingleFrameEncoder(root/'weights',device='cpu',cosmos_root=root)
obj.descriptor()
if external:
 try:
  obj._cosmos_module('cosmos_framework.g2_probe_primary',encoding._SOURCE_FILES[0])
 except RuntimeError as error:
  assert 'preloaded module' in str(error),str(error)
 else:raise AssertionError('unmanaged preloaded dependency accepted')
 assert old.VALUE==1
 assert 'cosmos_framework.g2_probe_primary' not in sys.modules
 assert not encoding._IMPORTED_SOURCE
else:
 first=obj._cosmos_module('cosmos_framework.g2_probe_primary',encoding._SOURCE_FILES[0])
 assert first.VALUE==2
 assert 'cosmos_framework.g2_probe_flags' in encoding._IMPORTED_SOURCE
 flags=obj._cosmos_module('cosmos_framework.g2_probe_flags',encoding._SOURCE_FILES[1])
 assert flags.VALUE==1
 other=encoding.WanSingleFrameEncoder(root/'weights',device='cpu',cosmos_root=root)
 other.descriptor()
 assert other._cosmos_module('cosmos_framework.g2_probe_primary',encoding._SOURCE_FILES[0]) is first
print('PASS')
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(tmp_path), str(external_dependency)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "PASS"


@pytest.mark.parametrize("stale_cache", [False, True])
def test_bound_import_compiles_actual_source_without_reading_or_writing_pyc(
    tmp_path, monkeypatch, stale_cache
):
    from g2.latent_cache.encoding import _IMPORTED_SOURCE

    name = "g2_vae_stale_pyc_probe"
    path = tmp_path / (name + ".py")
    path.write_text("VALUE=1\n" if stale_cache else "VALUE=2\n")
    cached = Path(importlib.util.cache_from_source(str(path)))
    previous_bytes = previous_mtime = None
    if stale_cache:
        stat = path.stat()
        py_compile.compile(
            str(path),
            doraise=True,
            invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP,
        )
        previous_bytes = cached.read_bytes()
        previous_mtime = cached.stat().st_mtime_ns
        path.write_text("VALUE=2\n")
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        assert path.stat().st_size == stat.st_size

    original_get_data = importlib.machinery.SourceFileLoader.get_data

    def no_bound_pyc_read(loader, filename):
        if loader.name == name and str(filename).endswith(".pyc"):
            raise AssertionError(
                "bound loader read bytecode instead of verified source"
            )
        return original_get_data(loader, filename)

    monkeypatch.setattr(
        importlib.machinery.SourceFileLoader, "get_data", no_bound_pyc_read
    )
    weights = tmp_path / "weights"
    weights.write_bytes(b"not_real_weights_no_model_loaded")
    obj = WanSingleFrameEncoder(weights, device="cpu", cosmos_root=tmp_path)
    try:
        assert name not in sys.modules
        module = obj._cosmos_module(name, name + ".py")
        assert module.VALUE == 2
        assert _IMPORTED_SOURCE[name] == (
            module,
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )
        if stale_cache:
            assert cached.read_bytes() == previous_bytes
            assert cached.stat().st_mtime_ns == previous_mtime
        else:
            assert not cached.exists()
    finally:
        sys.modules.pop(name, None)
        _IMPORTED_SOURCE.pop(name, None)


def test_transitive_bound_sources_also_ignore_stale_bytecode(tmp_path):
    package = tmp_path / "cosmos_framework"
    package.mkdir()
    (package / "__init__.py").write_text("")
    flags = package / "g2_pyc_flags.py"
    primary = package / "g2_pyc_primary.py"
    old = {
        flags: "VALUE=1\n",
        primary: "from . import g2_pyc_flags\nVALUE=g2_pyc_flags.VALUE+10\n",
    }
    new = {
        flags: "VALUE=2\n",
        primary: "from . import g2_pyc_flags\nVALUE=g2_pyc_flags.VALUE+20\n",
    }
    caches = {}
    for path in (flags, primary):
        path.write_text(old[path])
        stat = path.stat()
        cache = Path(
            py_compile.compile(
                str(path),
                doraise=True,
                invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP,
            )
        )
        caches[cache] = (cache.read_bytes(), cache.stat().st_mtime_ns)
        path.write_text(new[path])
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        assert path.stat().st_size == stat.st_size
    (tmp_path / "weights").write_bytes(b"not_loaded")
    code = """
import sys
from pathlib import Path
import g2.latent_cache.encoding as encoding
root=Path(sys.argv[1])
encoding._SOURCE_FILES=(
 'cosmos_framework/g2_pyc_primary.py',
 'cosmos_framework/g2_pyc_flags.py',
)
obj=encoding.WanSingleFrameEncoder(root/'weights',device='cpu',cosmos_root=root)
obj.descriptor()
first=obj._cosmos_module('cosmos_framework.g2_pyc_primary',encoding._SOURCE_FILES[0])
assert first.VALUE==22,first.VALUE
flags=obj._cosmos_module('cosmos_framework.g2_pyc_flags',encoding._SOURCE_FILES[1])
assert flags.VALUE==2
assert set(encoding._IMPORTED_SOURCE)=={
 'cosmos_framework.g2_pyc_primary','cosmos_framework.g2_pyc_flags'}
assert obj._cosmos_module('cosmos_framework.g2_pyc_primary',encoding._SOURCE_FILES[0]) is first
print('PASS')
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(tmp_path)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "PASS"
    for cache, (data, mtime) in caches.items():
        assert cache.read_bytes() == data and cache.stat().st_mtime_ns == mtime


def test_bound_finder_and_search_path_are_removed_after_import_failure(tmp_path):
    from g2.latent_cache.encoding import _IMPORTED_SOURCE

    name = "g2_vae_failed_source_probe"
    (tmp_path / (name + ".py")).write_text(
        "raise RuntimeError('probe source failed')\n"
    )
    weights = tmp_path / "weights"
    weights.write_bytes(b"not_loaded")
    obj = WanSingleFrameEncoder(weights, device="cpu", cosmos_root=tmp_path)
    before_meta, before_path = list(sys.meta_path), list(sys.path)
    with pytest.raises(RuntimeError, match="probe source failed"):
        obj._cosmos_module(name, name + ".py")
    assert sys.meta_path == before_meta and sys.path == before_path
    assert name not in _IMPORTED_SOURCE and name not in sys.modules
