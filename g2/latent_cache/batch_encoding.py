"""True Wan BCTHW batching over the unchanged #53 B1 loader/preprocessor."""

from __future__ import annotations

import copy
import os
import time
from contextlib import contextmanager
from pathlib import Path

from .batch_contract import ENCODER_SCHEMA, NUMERICS
from .contract import CacheError, fingerprint
from .encoding import WanSingleFrameEncoder, _bound_digest, _fingerprint, preprocess_rgb


@contextmanager
def deterministic_numerics(torch):
    previous = torch.are_deterministic_algorithms_enabled()
    warn = torch.is_deterministic_algorithms_warn_only_enabled()
    tf32 = torch.backends.cuda.matmul.allow_tf32
    try:
        torch.use_deterministic_algorithms(True)
        torch.backends.cuda.matmul.allow_tf32 = False
        with torch.backends.cudnn.flags(
            benchmark=False, deterministic=True, allow_tf32=False
        ):
            yield
    finally:
        torch.backends.cuda.matmul.allow_tf32 = tf32
        torch.use_deterministic_algorithms(previous, warn_only=warn)


class WanBatchEncoder:
    """One resident native model per process, one actual encode call per batch.

    Never loops over single-image VAE calls. The private tokenizer factory is
    CPU-test-only, as in the unchanged legacy loader. Real callers use CUDA.
    """

    def __init__(
        self,
        weights_path,
        *,
        device="cuda:0",
        cosmos_root=None,
        max_batch_size=32,
        _tokenizer_factory=None,
    ):
        if type(max_batch_size) is not int or not 1 <= max_batch_size <= 32:
            raise CacheError("per-GPU batch maximum must be in1..32")
        os.environ.setdefault(
            "CUBLAS_WORKSPACE_CONFIG", NUMERICS["cublas_workspace_config"]
        )
        if os.environ["CUBLAS_WORKSPACE_CONFIG"] != NUMERICS["cublas_workspace_config"]:
            raise CacheError("batch numerical workspace configuration differs")
        self.base = WanSingleFrameEncoder(
            weights_path,
            device=device,
            cosmos_root=cosmos_root,
            _tokenizer_factory=_tokenizer_factory,
        )
        self.max_batch_size = max_batch_size
        self._adapter_sha, self._adapter_stat = _bound_digest(Path(__file__))

    def descriptor(self):
        if _fingerprint(Path(__file__)) != self._adapter_stat:
            raise CacheError("batch adapter changed during execution")
        return dict(
            schema=ENCODER_SCHEMA,
            implementation="EXISTING_WAN_NATIVE_BCTHW_T1",
            legacy_loader=self.base.descriptor(),
            batch_adapter_sha256=self._adapter_sha,
            max_batch_size=self.max_batch_size,
            numerics=copy.deepcopy(NUMERICS),
            test_only=self.base.descriptor()["test_only"],
        )

    def encode(self, *args, **kwargs):
        raise CacheError("batch recipe requires encode_batch; no silent B1 fallback")

    def encode_batch(self, images, preprocessing):
        import numpy as np
        import torch

        if (
            not isinstance(images, (list, tuple))
            or not 1 <= len(images) <= self.max_batch_size
        ):
            raise CacheError("batch images must have actual B in1..maximum")
        if (preprocessing["height"], preprocessing["width"]) != (256, 256):
            raise CacheError("B32/T1 uses the explicit256x256 canvas")
        started = time.perf_counter()
        prepared = [preprocess_rgb(image, preprocessing) for image in images]
        with self.base._lock:
            identity = self.descriptor()
            if self.base._tokenizer is None:
                self.base._load()
            self.base._check_files()
            device = self.base._validate_tokenizer()
            pixels = (
                torch.from_numpy(np.stack([p[0] for p in prepared]))
                .permute(0, 3, 1, 2)
                .unsqueeze(2)
            )
            normalized = self.base._normalizer(
                pixels, {"device": device, "dtype": torch.float32}
            )
            timing = None
            if device.type == "cuda":
                torch.cuda.reset_peak_memory_stats(device)
                timing = (
                    torch.cuda.Event(enable_timing=True),
                    torch.cuda.Event(enable_timing=True),
                )
            with (
                torch.no_grad(),
                torch.autocast(device_type=device.type, enabled=False),
                deterministic_numerics(torch),
            ):
                if timing is not None:
                    timing[0].record()
                encoded = self.base._tokenizer.encode(normalized)
                if timing is not None:
                    timing[1].record()
            self.base._check_files()
            self.base._validate_tokenizer()
            if (
                type(encoded) is not torch.Tensor
                or encoded.dtype != torch.float32
                or encoded.device != device
                or tuple(encoded.shape) != (len(images), 48, 1, 16, 16)
                or not bool(torch.isfinite(encoded).all())
            ):
                raise CacheError("native batch must return finite FP32[B,48,1,16,16]")
            latents = (
                encoded[:, :, 0]
                .detach()
                .to(device="cpu", dtype=torch.float32, copy=True)
                .contiguous()
            )
            if identity != self.descriptor():
                raise CacheError("batch numerical dependencies changed")
            self.last_metrics = dict(
                native_input_shape=list(normalized.shape),
                native_calls=1,
                encode_wall_seconds=time.perf_counter() - started,
                native_cuda_ms=timing[0].elapsed_time(timing[1]) if timing else None,
                peak_allocated_bytes=torch.cuda.max_memory_allocated(device)
                if timing
                else 0,
                peak_reserved_bytes=torch.cuda.max_memory_reserved(device)
                if timing
                else 0,
            )
            result = []
            for position, (_, metadata) in enumerate(prepared):
                metadata.update(
                    latent_shape=[48, 16, 16],
                    latent_layout="CHW",
                    latent_dtype="float32",
                    vae_input_shape=list(normalized.shape),
                    vae_input_layout="BCTHW",
                    temporal_index=0,
                    temporal_dimension_removed=True,
                    encoder_descriptor_sha256=fingerprint(identity),
                    actual_batch_size=len(images),
                    batch_position=position,
                    latent_mask_basis="CONTENT_RECT_ONLY_RECEPTIVE_FIELD_NOT_CERTIFIED",
                    storage_conversion=dict(
                        from_dtype="float32",
                        to_dtype="float32",
                        exact=True,
                        max_abs_error=0.0,
                    ),
                )
                result.append((latents[position].clone(), metadata))
            return result
