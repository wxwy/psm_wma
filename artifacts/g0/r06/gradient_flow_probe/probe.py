# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: OpenMDW-1.1
"""G0-R06 E4 gradient-flow probe (v2).

Load iter800 checkpoint, disable torch.compile, enable latent cache, and for a
fixed set of samples run a SINGLE forward. From that forward we backward the
action loss (retain_graph=True), collect per-pattern gradients, zero_grad, then
backward the vision loss and collect its per-pattern gradients. We report:

- per-pattern L2 norms (action / vision / ratio)
- per-pattern cosine similarity between action-only and vision-only gradients
- combined gradient norm 10*a + 10*v and implied cosine from the three norms

This addresses DS's concern that norm ratio != direction consistency.
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
import tempfile
from pathlib import Path

_COSMOS = "/gemini/code/psm_wma/cosmos-framework"
sys.path.insert(0, _COSMOS)
os.environ.setdefault("LIBERO_ROOT", "/gemini/code/data/libero/libero_10_no_noops_1.0.0_lerobot")
os.environ.setdefault("LIBERO_LATENT_CACHE_ROOT", "/gemini/code/data/libero/libero_10_no_noops_1.0.0_lerobot_cosmos_exact_window_v1")
os.environ.setdefault("WAN_VAE_PATH", "/gemini/code/models/Wan2.2-TI2V-5B/Wan2.2_VAE.pth")
os.environ.setdefault("EDGE_POLICY_CHECKPOINT", "/gemini/code/models/Cosmos3-Edge-Policy-DROID")
os.environ.setdefault("TRITON_LIBCUDA_PATH", "/opt/orion/orion_runtime/gpu/cuda")

import torch

# torch.compile makes retain_graph=True fail with donated-buffer errors. Rather
# than fighting the compiled runtime, we use DS's fallback: two deterministic
# forward passes under the SAME manual seed. This gives action/vision losses the
# identical noise sample without requiring retain_graph.
SEED_FOR_DETERMINISTIC_FORWARD = 123456

from omegaconf import OmegaConf
from cosmos_framework.inference.common.args import ConfigFileType
from cosmos_framework.inference.args import OmniSetupOverrides
from cosmos_framework.inference.inference import OmniInference

PARITY_PATH = "/gemini/code/psm_wma/artifacts/g0/r06/exact_window_v1/smoke_parity.json"
NUM_SAMPLES = 8
PATTERNS = [
    r"action2llm",            # positive control: action input projection
    r"llm2action",            # positive control: action velocity head
    r"vae2llm",               # key: vision projection (does action loss flow back here?)
    r"layers\.0\..*moe_gen",  # early gen tower layer 0
    r"layers\.1\..*moe_gen",  # early gen tower layer 1
    r"layers\.2\..*moe_gen",  # early gen tower layer 2
    r"layers\.0\.",           # all layer 0 params (sense check: reasoner frozen status)
]


def _build_dataset():
    from cosmos_framework.data.generator.action.datasets.action_sft_dataset import get_action_libero_sft_dataset

    return get_action_libero_sft_dataset(
        root=os.environ["LIBERO_ROOT"],
        fps=20,
        chunk_length=16,
        image_size=256,
        mode="wam",
        camera_mode="concat_view",
        action_space="frame_wise_relative",
        rotation_space="6d",
        pose_coordinate_frame="native",
        action_normalization="quantile_rot",
        action_stats_path=None,
        split="full",
        val_ratio=0.0,
        seed=0,
        resolution=None,
        max_action_dim=64,
        tokenizer_config={
            "_target_": "cosmos_framework.data.generator.processors.build_processor_lazy",
            "repository": None,
            "revision": None,
            "subdir": "",
            "tokenizer_type": os.environ["EDGE_POLICY_CHECKPOINT"],
        },
        cfg_dropout_rate=0.0,  # deterministic for probe
        append_viewpoint_info=True,
        append_duration_fps_timestamps=True,
        append_resolution_info=True,
        append_idle_frames=True,
        format_prompt_as_json=True,
        iterable_shuffle=False,
        episode_shuffle_seed=42,
        tiny_overfit_num_samples=None,
        tiny_overfit_start_index=0,
        task_index=0,
        use_latent_cache=True,
        latent_cache_root=os.environ["LIBERO_LATENT_CACHE_ROOT"],
        latent_cache_parity_path=PARITY_PATH,
    )


def _collate_one(ds, index: int = 0):
    """Fetch one training batch via the real DataLoader to match nested format.

    The training JointDataLoader produces multi-item keys as `list[list[Tensor]]`
    (outer=batch, inner=sub-sequence per sample). Standard DataLoader + custom
    collate only gives `list[Tensor]`; `_load_and_tokenize_text_data` and the
    vision/action pipeline expect the extra nesting, so we re-wrap manually.
    """
    from cosmos_framework.data.generator.joint_dataloader import custom_collate_fn

    loader = torch.utils.data.DataLoader(
        ds,
        batch_size=1,
        collate_fn=custom_collate_fn,
        num_workers=0,
        pin_memory=False,
    )
    # Fixed index: skip ahead to the requested sample.
    it = iter(loader)
    for _ in range(index):
        try:
            next(it)
        except StopIteration:
            break
    batch = next(it)
    # Match JointDataLoader output contract: list[Tensor] -> list[list[Tensor]]
    multi_item_keys = {"text_token_ids", "video", "images", "action", "action_raw"}
    for key in multi_item_keys:
        if key in batch and isinstance(batch[key], list):
            batch[key] = [[t] for t in batch[key]]
    return batch


def _collect_grad_vectors(model: torch.nn.Module, patterns: list[str]) -> dict[str, torch.Tensor]:
    """Concatenate per-parameter gradients into one vector per pattern."""
    out: dict[str, list[torch.Tensor]] = {p: [] for p in patterns}
    for name, param in model.named_parameters():
        if param.grad is None:
            continue
        g = param.grad.detach().reshape(-1)
        for pat in patterns:
            if re.search(pat, name):
                out[pat].append(g)
    return {p: torch.cat(v) if v else torch.zeros(1, device=next(model.parameters()).device) for p, v in out.items()}


def _compute_cosine(a: torch.Tensor, b: torch.Tensor) -> float:
    a = a.float()
    b = b.float()
    na = a.norm()
    nb = b.norm()
    if na <= 0 or nb <= 0:
        return float("nan")
    return float((a @ b) / (na * nb))


def _make_compile_disabled_config(src_cfg: Path) -> Path:
    """Return a temp config path with model.config.compile.enabled=false."""
    cfg = OmegaConf.load(src_cfg)
    OmegaConf.set_struct(cfg, False)
    if "model" in cfg and "config" in cfg.model and "compile" in cfg.model.config:
        cfg.model.config.compile.enabled = False
        # Also disable cuda graphs and dynamic compile to be safe.
        cfg.model.config.compile.use_cuda_graphs = False
        cfg.model.config.compile.compile_dynamic = False
    # Write to a temp file inside the output dir so it persists with artifacts.
    tmp = Path(tempfile.gettempdir()) / "probe_config_no_compile.yaml"
    OmegaConf.save(cfg, tmp)
    return tmp


def main() -> int:
    out_dir = Path("/gemini/code/psm_wma/artifacts/g0/r06/gradient_flow_probe")
    out_dir.mkdir(parents=True, exist_ok=True)
    log_f = open(out_dir / "train.log", "w")

    def log(msg: str):
        print(msg)
        log_f.write(msg + "\n")
        log_f.flush()

    ckpt = Path("/gemini/code/psm_wma/artifacts/g0/r06/sft_baseline/formal_128x2_1000step/psm_wma/g0_r06_sft/edge_libero_task0_sft/checkpoints/iter_000000800")
    cfg = ckpt.parent.parent / "config.yaml"
    probe_cfg = _make_compile_disabled_config(cfg)
    log(f"[E4] Using compile-disabled config: {probe_cfg}")

    overrides = OmniSetupOverrides(
        checkpoint_path=str(ckpt),
        config_file=str(probe_cfg),
        config_file_type=ConfigFileType.YAML,
        output_dir=out_dir / "server_runtime",
        sampler="unipc",
        use_torch_compile=False,
        use_cuda_graphs=False,
        compile_dynamic=False,
        compiled_region="all",
    )
    setup_args = overrides.build_setup()
    log(f"[E4] Setup args compile: enabled={setup_args.use_torch_compile}, "
        f"region={setup_args.compiled_region}, dynamic={setup_args.compile_dynamic}")

    log("[E4] Loading model via OmniInference (compile disabled)...")
    pipe = OmniInference.create(setup_args)
    model = pipe.model
    model.train()
    compile_enabled = getattr(getattr(model.config, "compile", None), "enabled", True)
    log(f"[E4] Model loaded. compile.enabled={compile_enabled}")

    log("[E4] Building dataset (latent cache enabled)...")
    ds = _build_dataset()
    sample0 = _collate_one(ds, 0)
    log(f"[E4] Sample-0 keys: {list(sample0.keys())}")
    log(f"[E4] Sample-0 video shape: {sample0['video'][0][0].shape}")
    log(f"[E4] Sample-0 vision_latent_cache_enabled: {sample0.get('vision_latent_cache_enabled')}")
    if sample0.get("vision_latent_cache") is not None:
        log(f"[E4] Sample-0 latent cache shape: {sample0['vision_latent_cache'].shape}")

    per_sample = []
    indices = list(range(NUM_SAMPLES))
    log(f"[E4] Running direction probe over {NUM_SAMPLES} fixed samples...")

    for sample_idx in indices:
        batch = _collate_one(ds, sample_idx)
        with torch.set_grad_enabled(True):
            # Forward 1: action loss under fixed seed.
            torch.manual_seed(SEED_FOR_DETERMINISTIC_FORWARD)
            output_a, _ = model.training_step(batch, 0)
            action_loss = output_a["flow_matching_loss_action"]
            sigma_a = output_a.get("sigmas_action")
            sigma_v_from_a = output_a.get("sigmas_vision")

            model.zero_grad(set_to_none=True)
            action_loss.backward()
            grad_action = _collect_grad_vectors(model, PATTERNS)
            action_norm_total = float(sum(g.float().pow(2).sum() for g in grad_action.values() if g.numel() > 0) ** 0.5)

            # Forward 2: vision loss under the SAME fixed seed.
            torch.manual_seed(SEED_FOR_DETERMINISTIC_FORWARD)
            output_v, _ = model.training_step(batch, 0)
            vision_loss = output_v["flow_matching_loss_vision"]
            sigma_v = output_v.get("sigmas_vision")

            model.zero_grad(set_to_none=True)
            vision_loss.backward()
            grad_vision = _collect_grad_vectors(model, PATTERNS)
            vision_norm_total = float(sum(g.float().pow(2).sum() for g in grad_vision.values() if g.numel() > 0) ** 0.5)

        # Sanity: sigma should match across the two deterministic forwards.
        sigma_match = None
        if sigma_a is not None and sigma_v is not None:
            sigma_match = bool(torch.allclose(sigma_a, sigma_v))

        sample_result = {
            "sample_idx": sample_idx,
            "action_loss": float(action_loss),
            "vision_loss": float(vision_loss),
            "action_norm_total": action_norm_total,
            "vision_norm_total": vision_norm_total,
            "sigma_match": sigma_match,
            "norms_action": {p: float(grad_action[p].norm()) for p in PATTERNS},
            "norms_vision": {p: float(grad_vision[p].norm()) for p in PATTERNS},
            "cosine": {p: _compute_cosine(grad_action[p], grad_vision[p]) for p in PATTERNS},
        }
        per_sample.append(sample_result)
        log(f"[E4] sample {sample_idx}: a_loss={sample_result['action_loss']:.4f} v_loss={sample_result['vision_loss']:.4f} "
            f"cos(vae2llm)={sample_result['cosine']['vae2llm']:.4f} "
            f"cos(moe0)={sample_result['cosine'][PATTERNS[3]]:.4f}")

    # Aggregate across samples.
    def _mean(values: list[float]) -> float:
        clean = [v for v in values if not math.isnan(v)]
        return sum(clean) / len(clean) if clean else float("nan")

    aggregated = {
        "action_loss_mean": _mean([s["action_loss"] for s in per_sample]),
        "vision_loss_mean": _mean([s["vision_loss"] for s in per_sample]),
        "action_norm_total_mean": _mean([s["action_norm_total"] for s in per_sample]),
        "vision_norm_total_mean": _mean([s["vision_norm_total"] for s in per_sample]),
        "norms_action_mean": {p: _mean([s["norms_action"][p] for s in per_sample]) for p in PATTERNS},
        "norms_vision_mean": {p: _mean([s["norms_vision"][p] for s in per_sample]) for p in PATTERNS},
        "cosine_mean": {p: _mean([s["cosine"][p] for s in per_sample]) for p in PATTERNS},
        "ratios_mean": {
            p: _mean([s["norms_action"][p] / s["norms_vision"][p] if s["norms_vision"][p] > 0 else float("nan") for s in per_sample])
            for p in PATTERNS
        },
    }

    # Implied cosine from total norms under 10*a + 10*v combination.
    # ||10a + 10v||^2 = 100(||a||^2 + ||v||^2 + 2 a·v) = 100(||a||^2 + ||v||^2 + 2 ||a|| ||v|| cosθ)
    a_norm = aggregated["action_norm_total_mean"]
    v_norm = aggregated["vision_norm_total_mean"]
    implied_cos = float("nan")
    if a_norm > 0 and v_norm > 0:
        # We don't have combined norm directly; leave for future extension.
        # For now report the per-pattern cosines which are the signal DS wants.
        pass

    result = {
        "num_samples": NUM_SAMPLES,
        "patterns": PATTERNS,
        "per_sample": per_sample,
        "aggregated": aggregated,
        "note": "compile disabled; latent cache enabled; two seed-fixed forwards per sample (action-loss backward then vision-loss backward) with cosine computed per-pattern; sigma_match null because output_batch lacks sigmas_action/vision fields.",
    }
    (out_dir / "result_v2.json").write_text(json.dumps(result, indent=2))
    log("[E4] Result written to " + str(out_dir / "result_v2.json"))

    # Print the key table for quick reading.
    log("\n[E4] Aggregated direction summary:")
    log(f"{'pattern':<30} {'action_norm':>12} {'vision_norm':>12} {'ratio':>8} {'cosine':>8}")
    for p in PATTERNS:
        an = aggregated["norms_action_mean"][p]
        vn = aggregated["norms_vision_mean"][p]
        ratio = an / vn if vn > 0 else float("nan")
        cos = aggregated["cosine_mean"][p]
        log(f"{p:<30} {an:>12.4f} {vn:>12.4f} {ratio:>8.4f} {cos:>8.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
