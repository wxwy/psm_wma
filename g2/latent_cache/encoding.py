"""Independent spatial-image preprocessing and a lazy, frozen Wan Encode1.

Importing this module or describing an encoder never loads Torch, a VAE, a
Policy, or a graphics runtime. The existing Cosmos normalization and Wan
implementation are imported only when encoding. Real VAE parity is a separate
GPU gate; the private factory seam exists only for CPU contract tests.

First encoding must run before other code imports the bound Cosmos modules.
Unmanaged preloaded modules cannot be authenticated from their current files
and are conservatively refused, never reloaded. Constructor/descriptor calls
remain lazy and do not claim an import binding for future online integration.
The five bound source modules are compiled from hash-checked source bytes;
their imports neither read nor write Python bytecode caches in the Child.
"""

from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.abc
import importlib.machinery
import importlib.metadata
import importlib.util
import json
import os
import re
import sys
import threading
from pathlib import Path

_SOURCE_FILES = (
    "cosmos_framework/model/generator/vision_encoder.py",
    "cosmos_framework/model/generator/mot/vae_load_balance.py",
    "cosmos_framework/model/generator/tokenizers/wan2pt2_vae_4x16x16.py",
    "cosmos_framework/model/generator/tokenizers/interface.py",
    "cosmos_framework/utils/flags.py",
)
_CONSTRUCTOR = {
    "chunk_duration": 93,
    "keep_decoder_cache": False,
    "use_streaming_encode": False,
    "encode_chunk_frames": {"256": 68, "480": 24, "720": 8},
    "encode_exact_durations": [1],
    "spatial_compression_factor": 16,
    "temporal_compression_factor": 4,
    "causal": True,
}
_IMPORTED_SOURCE = {}
_IMPORT_LOCK = threading.RLock()


def _regular_file(path):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("encoder dependencies must not use symbolic links")
    if not path.is_file():
        raise ValueError("encoder dependency is not a local regular file: " + str(path))
    return path


def _fingerprint(path):
    stat = _regular_file(path).stat()
    return (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)


def _digest(path):
    value = hashlib.sha256()
    with _regular_file(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def _bound_digest(path):
    before = _fingerprint(path)
    value = _digest(path)
    if _fingerprint(path) != before:
        raise RuntimeError("encoder dependency changed while hashing")
    return value, before


def _version(distribution):
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError as error:
        raise RuntimeError("missing encoder dependency: " + distribution) from error


def _preprocessing(value):
    required = {
        "height",
        "width",
        "interpolation",
        "padding_rgb",
        "aspect",
        "rounding",
        "layout",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("preprocessing must declare the exact spatial fit recipe")
    if any(type(value[k]) is not int or value[k] <= 0 for k in ("height", "width")):
        raise ValueError("canvas height and width must be positive integers")
    if (
        value["interpolation"] not in ("lanczos", "bilinear", "nearest")
        or value["padding_rgb"] != [255, 255, 255]
        or any(type(x) is not int for x in value["padding_rgb"])
        or value["aspect"] != "fit"
        or value["rounding"] != "floor_half_up"
        or value["layout"] != "RGB_HWC"
    ):
        raise ValueError("unsupported spatial preprocessing recipe")
    return copy.deepcopy(value)


def preprocess_rgb(rgb, preprocessing):
    """Fit uint8 HWC RGB on an explicit white canvas without changing its content.

    The returned metadata describes a half-open pixel rectangle, not a mask
    inferred from color or an assumed latent receptive field. White source
    pixels remain valid source pixels. Odd padding leaves the extra pixel on
    the right or bottom. Size rounding uses exact integer half-up arithmetic.
    """
    import numpy as np
    from PIL import Image

    recipe = _preprocessing(preprocessing)
    if (
        not isinstance(rgb, np.ndarray)
        or rgb.dtype != np.uint8
        or rgb.ndim != 3
        or rgb.shape[2] != 3
        or min(rgb.shape[:2]) <= 0
    ):
        raise ValueError("spatial input must be a nonempty uint8 RGB HWC array")
    height, width = rgb.shape[:2]
    target_h, target_w = recipe["height"], recipe["width"]
    if target_w * height <= target_h * width:
        resized_w = target_w
        resized_h = max(1, (2 * height * target_w + width) // (2 * width))
    else:
        resized_h = target_h
        resized_w = max(1, (2 * width * target_h + height) // (2 * height))
    top, left = (target_h - resized_h) // 2, (target_w - resized_w) // 2
    bottom, right = target_h - resized_h - top, target_w - resized_w - left
    mode = {
        "lanczos": Image.Resampling.LANCZOS,
        "bilinear": Image.Resampling.BILINEAR,
        "nearest": Image.Resampling.NEAREST,
    }[recipe["interpolation"]]
    image = Image.fromarray(np.ascontiguousarray(rgb)).resize(
        (resized_w, resized_h), resample=mode
    )
    canvas = np.full((target_h, target_w, 3), 255, dtype=np.uint8)
    canvas[top : top + resized_h, left : left + resized_w] = np.asarray(
        image, dtype=np.uint8
    )
    box = [left, top, left + resized_w, top + resized_h]
    metadata = {
        "preprocessing": recipe,
        "original_hw": [height, width],
        "resized_hw": [resized_h, resized_w],
        "canvas_hw": [target_h, target_w],
        "padding": {"top": top, "bottom": bottom, "left": left, "right": right},
        "content_box": box,
        "valid_region": {
            "kind": "half_open_pixel_rectangle",
            "box_xyxy": box,
            "basis": "resize_and_pad_geometry_not_rgb",
            "latent_patch_mask": "NOT_INFERRED_FROM_PIXEL_RECTANGLE",
        },
        "resize_implementation": "PIL.Image.resize",
        "pillow_version": _version("Pillow"),
        "input_layout": "RGB_HWC",
        "input_dtype": "uint8",
        "input_range": [0, 255],
    }
    return canvas, metadata


class WanSingleFrameEncoder:
    """One process-local eager Wan VAE; one independent T=1 image per call.

    Construction and descriptor calculation do not instantiate the VAE or
    initialize CUDA. The descriptor records deterministic file/source and
    effective configuration dependencies, not an independent loaded-tensor
    authentication claim. Actual Encode1/decode correctness needs the real gate.
    """

    def __init__(
        self, weights_path, *, device="cuda", cosmos_root=None, _tokenizer_factory=None
    ):
        self.weights_path = Path(weights_path).absolute()
        self.cosmos_root = (
            Path(cosmos_root).absolute()
            if cosmos_root is not None
            else Path(__file__).resolve().parents[2] / "cosmos-framework"
        )
        if (
            not isinstance(device, str)
            or re.fullmatch(r"cpu|cuda(?::(?:0|[1-9][0-9]*))?", device) is None
        ):
            raise ValueError("encoder device must be cpu, cuda or cuda:<index>")
        self.device = device
        self._factory = _tokenizer_factory
        self._identity = None
        self._files = {}
        self._tokenizer = self._loaded = self._module = self._normalizer = None
        self._lock = threading.RLock()
        self._configuration = (
            self.weights_path,
            self.cosmos_root,
            self.device,
            self._factory,
        )

    def descriptor(self):
        """JSON-only recipe dependencies, without importing Torch or Wan."""
        with self._lock:
            return self._descriptor()

    def _descriptor(self):
        if self._identity is None:
            sources = {}
            weights_sha, self._files[self.weights_path] = _bound_digest(
                self.weights_path
            )
            for name in _SOURCE_FILES:
                sources[name], self._files[self.cosmos_root / name] = _bound_digest(
                    self.cosmos_root / name
                )
            adapter_sha, self._files[Path(__file__)] = _bound_digest(Path(__file__))
            self._identity = {
                "schema": "g2_spatial_wan_encode1_v1",
                "implementation": "Wan2pt2VAEInterface"
                if self._factory is None
                else "TEST_ONLY_FAKE_TOKENIZER",
                "test_only": self._factory is not None,
                "weights_sha256": weights_sha,
                "cosmos_source_sha256": sources,
                "adapter_source_sha256": adapter_sha,
                "constructor": copy.deepcopy(_CONSTRUCTOR),
                "normalizer": "cosmos_framework.model.generator.vision_encoder.normalize_uint8_item",
                "normalization": "FP32_div127.5_sub1",
                "latent_scale": "EXISTING_WAN_INTERNAL_MEAN_INV_STD_NO_EXTRA_SCALE",
                "backend": "eager",
                "compute_dtype": "bfloat16",
                "normalize_dtype": "float32",
                "output_dtype": "float32",
                "device": self.device,
                "input_layout": "BCTHW",
                "input_batch": 1,
                "input_time": 1,
                "record_layout": "CHW",
                "streaming": False,
                "retained_state": False,
                "torch_version": _version("torch"),
                "pillow_version": _version("Pillow"),
                "numpy_version": _version("numpy"),
            }
        self._check_files()
        return copy.deepcopy(self._identity)

    def _check_files(self):
        if (
            self.weights_path,
            self.cosmos_root,
            self.device,
            self._factory,
        ) != self._configuration:
            raise RuntimeError("encoder configuration changed after construction")
        for path, expected in self._files.items():
            if _fingerprint(path) != expected:
                raise RuntimeError(
                    "encoder dependency changed after identity was established: "
                    + str(path)
                )

    def _cosmos_module(self, name, relative):
        with _IMPORT_LOCK:
            return self._import_bound_module(name, relative)

    def _import_bound_module(self, name, relative):
        # Only the selected Cosmos child is used, never another root g2 package.
        paths = {name: relative}
        if name.startswith("cosmos_framework."):
            paths.update(
                {
                    path.removesuffix(".py").replace("/", "."): path
                    for path in _SOURCE_FILES
                }
            )
            if paths[name] != relative:
                raise RuntimeError(
                    "Cosmos module path differs from its declared source"
                )
        bound = (
            self._identity["cosmos_source_sha256"] if self._identity is not None else {}
        )
        expected = {
            key: bound[path] if path in bound else _digest(self.cosmos_root / path)
            for key, path in paths.items()
        }

        def check_source(key, module):
            file = getattr(module, "__file__", None)
            path = self.cosmos_root / paths[key]
            if file is None or Path(file).resolve() != path.resolve():
                raise RuntimeError(
                    "already imported Cosmos module belongs to another checkout"
                )
            if _digest(path) != expected[key]:
                raise RuntimeError("Cosmos source changed during controlled import")

        # Checking just the requested module misses an externally preloaded
        # dependency reused by importlib. All bound dependencies need a token.
        for key in paths:
            if key not in sys.modules:
                continue
            module = sys.modules[key]
            previous = _IMPORTED_SOURCE.get(key)
            if previous is None:
                raise RuntimeError(
                    "preloaded module has no verified source binding; "
                    "first encode requires a fresh Cosmos process"
                )
            if previous != (module, expected[key]):
                raise RuntimeError(
                    "Cosmos source changed in this process; use a fresh encoder process"
                )
            check_source(key, module)

        class BoundSourceLoader(importlib.machinery.SourceFileLoader):
            def get_code(loader, fullname):
                # Default SourceFileLoader may accept timestamp/size-matching
                # .pyc containing different code. Compile the very source bytes
                # whose SHA is bound here, bypassing both pyc reads and writes.
                payload = _regular_file(loader.path).read_bytes()
                source_sha = hashlib.sha256(payload).hexdigest()
                if source_sha != expected[fullname]:
                    raise RuntimeError("Cosmos source changed before compilation")
                code = compile(payload, loader.path, "exec", dont_inherit=True)
                loader.bound_source_sha256 = source_sha
                return code

        class BoundSourceFinder(importlib.abc.MetaPathFinder):
            def find_spec(finder, fullname, path=None, target=None):
                if fullname not in paths:
                    return None
                file = str(self.cosmos_root / paths[fullname])
                loader = BoundSourceLoader(fullname, file)
                return importlib.util.spec_from_file_location(
                    fullname, file, loader=loader
                )

        before = set(sys.modules)
        finder = BoundSourceFinder()
        root = str(self.cosmos_root)
        sys.path.insert(0, root)
        sys.meta_path.insert(0, finder)
        try:
            module = importlib.import_module(name)
        finally:
            sys.meta_path.remove(finder)
            sys.path.remove(root)

        # Imports may load flags or another bound dependency transitively.
        # Authenticate every newly loaded bound module before publishing any
        # token; failed imports stay untrusted and require a fresh process.
        claimed = {name} | ((set(sys.modules) - before) & paths.keys())
        pending = {}
        for key in claimed:
            loaded = sys.modules[key]
            check_source(key, loaded)
            if key not in before:
                loader = getattr(loaded, "__loader__", None)
                if (
                    not isinstance(loader, BoundSourceLoader)
                    or getattr(loader, "bound_source_sha256", None) != expected[key]
                ):
                    raise RuntimeError(
                        "new Cosmos module was not compiled from bound source"
                    )
            pending[key] = (loaded, expected[key])
        self._check_files()
        _IMPORTED_SOURCE.update(pending)
        return module

    def _load(self):
        import torch

        identity = self.descriptor()
        if _digest(self.weights_path) != identity["weights_sha256"]:
            raise RuntimeError("VAE weights changed before loading")
        normalizer = self._cosmos_module(
            "cosmos_framework.model.generator.vision_encoder",
            "cosmos_framework/model/generator/vision_encoder.py",
        )
        self._normalizer = normalizer.normalize_uint8_item
        if self._factory is None:
            # Respect an already configured Cosmos process; never patch imported
            # global flags to pretend a different device/training mode was used.
            requested = torch.device(self.device)
            os.environ.setdefault("COSMOS_TRAINING", "0")
            os.environ.setdefault("COSMOS_INTERNAL", "0")
            os.environ.setdefault("COSMOS_DEVICE", requested.type)
            flags = self._cosmos_module(
                "cosmos_framework.utils.flags", "cosmos_framework/utils/flags.py"
            )
            if flags.TRAINING or flags.INTERNAL or str(flags.DEVICE) != requested.type:
                raise RuntimeError(
                    "offline Wan requires matching COSMOS_DEVICE, COSMOS_TRAINING=0 and COSMOS_INTERNAL=0 before import"
                )
            if requested.type == "cuda" and requested.index is not None:
                torch.cuda.set_device(requested.index)
            module = self._cosmos_module(
                "cosmos_framework.model.generator.tokenizers.wan2pt2_vae_4x16x16",
                "cosmos_framework/model/generator/tokenizers/wan2pt2_vae_4x16x16.py",
            )
            tokenizer = module.Wan2pt2VAEInterface(
                vae_path=str(self.weights_path),
                bucket_name="",
                object_store_credential_path_pretrained="",
                **copy.deepcopy(_CONSTRUCTOR),
            )
        else:
            tokenizer = self._factory(
                weights_path=self.weights_path,
                device=self.device,
                constructor_config=copy.deepcopy(_CONSTRUCTOR),
            )
        if _digest(self.weights_path) != identity["weights_sha256"]:
            raise RuntimeError("VAE weights changed while loading")
        self._tokenizer = tokenizer
        self._loaded = getattr(tokenizer, "model", None)
        self._module = getattr(self._loaded, "model", None)
        self._check_files()
        self._validate_tokenizer()

    def _validate_tokenizer(self):
        import torch

        token, loaded, module = self._tokenizer, self._loaded, self._module
        if (
            not callable(getattr(token, "encode", None))
            or getattr(token, "model", None) is not loaded
            or getattr(loaded, "model", None) is not module
            or module is None
            or getattr(module, "training", None) is not False
            or getattr(token, "is_causal", None) is not True
            or getattr(token, "use_streaming_encode", None) is not False
            or getattr(token, "_keep_encoder_cache", None) is not False
            or getattr(token, "spatial_compression_factor", None) != 16
            or getattr(token, "temporal_compression_factor", None) != 4
            or getattr(token, "chunk_duration", None) != _CONSTRUCTOR["chunk_duration"]
            or getattr(token, "encode_chunk_frames", None)
            != _CONSTRUCTOR["encode_chunk_frames"]
            or getattr(token, "encode_exact_durations", None)
            != _CONSTRUCTOR["encode_exact_durations"]
            or getattr(token, "_keep_decoder_cache", None) is not False
            or getattr(module, "temporal_window", None)
            != _CONSTRUCTOR["encode_chunk_frames"]
            or getattr(module, "_encode_exact_durations", None) != {1}
            or getattr(loaded, "dtype", None) != torch.bfloat16
            or getattr(module, "_enc_stream_shape", None) is not None
            or any(x is not None for x in getattr(module, "_enc_cache", ()))
            or getattr(module, "_aot_chunk_fns", None)
        ):
            raise RuntimeError(
                "Encode1 requires frozen eager non-streaming Wan without retained state"
            )
        parameters = tuple(module.parameters())
        if not parameters or any(
            p.requires_grad or p.dtype != torch.bfloat16 for p in parameters
        ):
            raise RuntimeError("Encode1 requires frozen bfloat16 parameters")
        device = parameters[0].device
        requested = torch.device(self.device)
        if (
            device.type != requested.type
            or (requested.index is not None and device.index != requested.index)
            or any(p.device != device for p in parameters)
        ):
            raise RuntimeError(
                "loaded Wan parameter device differs from the declared device"
            )
        return device

    def encode(self, rgb, preprocessing):
        """Return an independent CPU FP32 [C,H_z,W_z] tensor and pixel provenance."""
        import torch

        canvas, metadata = preprocess_rgb(rgb, preprocessing)
        height, width = canvas.shape[:2]
        if height % 16 or width % 16:
            raise ValueError("Wan canvas dimensions must be multiples of 16")
        with self._lock:
            identity = self.descriptor()
            if self._tokenizer is None:
                self._load()
            self._check_files()
            device = self._validate_tokenizer()
            pixels = torch.from_numpy(canvas).permute(2, 0, 1).unsqueeze(0).unsqueeze(2)
            normalized = self._normalizer(
                pixels, {"device": device, "dtype": torch.float32}
            )
            with (
                torch.no_grad(),
                torch.autocast(device_type=device.type, enabled=False),
            ):
                encoded = self._tokenizer.encode(normalized)
            self._check_files()
            self._validate_tokenizer()
            if (
                not isinstance(encoded, torch.Tensor)
                or encoded.dtype != torch.float32
                or encoded.ndim != 5
                or tuple(encoded.shape[:3]) != (1, 48, 1)
                or min(encoded.shape[3:]) <= 0
                or encoded.device != device
                or not bool(torch.isfinite(encoded).all())
            ):
                raise ValueError(
                    "Encode1 must return finite FP32 [1,48,1,H_z,W_z] on the encoder device"
                )
            latent = (
                encoded[0, :, 0]
                .detach()
                .to(device="cpu", dtype=torch.float32, copy=True)
                .contiguous()
            )
            metadata.update(
                latent_shape=list(latent.shape),
                latent_layout="CHW",
                latent_dtype="float32",
                vae_input_shape=list(normalized.shape),
                vae_input_layout="BCTHW",
                temporal_index=0,
                temporal_dimension_removed=True,
                encoder_descriptor_sha256=hashlib.sha256(
                    json.dumps(
                        identity, sort_keys=True, separators=(",", ":"), allow_nan=False
                    ).encode()
                ).hexdigest(),
            )
            return latent, metadata
