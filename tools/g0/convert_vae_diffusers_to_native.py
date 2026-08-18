#!/usr/bin/env python
"""Convert the Cosmos3-Edge-Policy-DROID diffusers-layout Wan2.2 VAE into the
cosmos-framework native Wan2.2 VAE key layout.

Why: the framework's ``Wan2pt2VAEInterface``/``WanVAE_`` expects the Wan-native
layout (top-level ``conv1``/``conv2`` = quant/post_quant 1x1, ``encoder.conv1``,
``encoder.head``, ``decoder.conv1``, ``decoder.head``, ``encoder.downsamples.*``,
``decoder.upsamples.*``). The Edge-Policy-DROID HF package ships the *same* VAE
weights in diffusers ``AutoencoderKLWan`` layout (``encoder.conv_in``,
``encoder.down_blocks.*``, ``encoder.mid_block.*``, ``encoder.norm_out``,
``encoder.conv_out``, ``quant_conv``/``post_quant_conv`` ...). This is a pure
key re-map + ``torch.save``; no weight download, no value transform.

Both layouts have exactly 196 keys. The block structure is index-identical
(encoder 4 downsample stages 14/18/18/12, decoder 4 upsample stages
22/22/22/20, mid 17, ends as tabulated below), so every rule is positional.

Usage:
    python tools/g0/convert_vae_diffusers_to_native.py \
        /disk/rl/models/Cosmos3-Edge-Policy-DROID/vae/diffusion_pytorch_model.safetensors \
        examples/checkpoints/wan22_vae/Wan2.2_VAE.pth
"""
from __future__ import annotations

import argparse

import torch

from cosmos_framework.model.generator.tokenizers.wan2pt2_vae_4x16x16 import WanVAE_


def build_mapping() -> dict[str, str]:
    """Return {native_key: diffusers_key}."""
    mapping: dict[str, str] = {}

    def add(native: str, diffusers: str) -> None:
        assert native not in mapping, f"native key already mapped: {native}"
        mapping[native] = diffusers

    # --- terminal / top-level convs (shapes verified below) ---
    # native top-level conv1 = quant_conv (1x1 96->96); conv2 = post_quant_conv (1x1 48->48)
    add("conv1.weight", "quant_conv.weight")
    add("conv1.bias", "quant_conv.bias")
    add("conv2.weight", "post_quant_conv.weight")
    add("conv2.bias", "post_quant_conv.bias")
    # encoder input conv + head (groupnorm + final conv)
    add("encoder.conv1.weight", "encoder.conv_in.weight")
    add("encoder.conv1.bias", "encoder.conv_in.bias")
    add("encoder.head.0.gamma", "encoder.norm_out.gamma")
    add("encoder.head.2.weight", "encoder.conv_out.weight")
    add("encoder.head.2.bias", "encoder.conv_out.bias")
    # decoder input conv + head
    add("decoder.conv1.weight", "decoder.conv_in.weight")
    add("decoder.conv1.bias", "decoder.conv_in.bias")
    add("decoder.head.0.gamma", "decoder.norm_out.gamma")
    add("decoder.head.2.weight", "decoder.conv_out.weight")
    add("decoder.head.2.bias", "decoder.conv_out.bias")

    # --- mid block (attention naming is identical) ---
    # native encoder.middle = {0: residual, 1: attention, 2: residual}
    for side, dims in (("encoder", "640"), ("decoder", "1024")):
        add(f"{side}.middle.0.residual.0.gamma", f"{side}.mid_block.resnets.0.norm1.gamma")
        add(f"{side}.middle.0.residual.2.bias", f"{side}.mid_block.resnets.0.conv1.bias")
        add(f"{side}.middle.0.residual.2.weight", f"{side}.mid_block.resnets.0.conv1.weight")
        add(f"{side}.middle.0.residual.3.gamma", f"{side}.mid_block.resnets.0.norm2.gamma")
        add(f"{side}.middle.0.residual.6.bias", f"{side}.mid_block.resnets.0.conv2.bias")
        add(f"{side}.middle.0.residual.6.weight", f"{side}.mid_block.resnets.0.conv2.weight")
        # attention: names already identical
        add(f"{side}.middle.1.norm.gamma", f"{side}.mid_block.attentions.0.norm.gamma")
        add(f"{side}.middle.1.proj.bias", f"{side}.mid_block.attentions.0.proj.bias")
        add(f"{side}.middle.1.proj.weight", f"{side}.mid_block.attentions.0.proj.weight")
        add(f"{side}.middle.1.to_qkv.bias", f"{side}.mid_block.attentions.0.to_qkv.bias")
        add(f"{side}.middle.1.to_qkv.weight", f"{side}.mid_block.attentions.0.to_qkv.weight")
        add(f"{side}.middle.2.residual.0.gamma", f"{side}.mid_block.resnets.1.norm1.gamma")
        add(f"{side}.middle.2.residual.2.bias", f"{side}.mid_block.resnets.1.conv1.bias")
        add(f"{side}.middle.2.residual.2.weight", f"{side}.mid_block.resnets.1.conv1.weight")
        add(f"{side}.middle.2.residual.3.gamma", f"{side}.mid_block.resnets.1.norm2.gamma")
        add(f"{side}.middle.2.residual.6.bias", f"{side}.mid_block.resnets.1.conv2.bias")
        add(f"{side}.middle.2.residual.6.weight", f"{side}.mid_block.resnets.1.conv2.weight")

    # --- encoder downsample stages: native downsamples.N.downsamples.M  <->  diffusers down_blocks.N.resnets.M ---
    for stage in range(4):
        prefix_n = f"encoder.downsamples.{stage}.downsamples"
        prefix_d = f"encoder.down_blocks.{stage}.resnets"
        sub = 0
        for resnet in range(2):
            base_n = f"{prefix_n}.{sub}"
            base_d = f"{prefix_d}.{resnet}"
            add(f"{base_n}.residual.0.gamma", f"{base_d}.norm1.gamma")
            add(f"{base_n}.residual.2.bias", f"{base_d}.conv1.bias")
            add(f"{base_n}.residual.2.weight", f"{base_d}.conv1.weight")
            add(f"{base_n}.residual.3.gamma", f"{base_d}.norm2.gamma")
            add(f"{base_n}.residual.6.bias", f"{base_d}.conv2.bias")
            add(f"{base_n}.residual.6.weight", f"{base_d}.conv2.weight")
            if f"{base_d}.conv_shortcut.weight" in diffusers_keys:
                add(f"{base_n}.shortcut.weight", f"{base_d}.conv_shortcut.weight")
                add(f"{base_n}.shortcut.bias", f"{base_d}.conv_shortcut.bias")
            sub += 1
        # spatial + temporal downsampler (absent on the last stage)
        if f"encoder.down_blocks.{stage}.downsampler.resample.1.weight" in diffusers_keys:
            add(f"{prefix_n}.{sub}.resample.1.weight", f"encoder.down_blocks.{stage}.downsampler.resample.1.weight")
            add(f"{prefix_n}.{sub}.resample.1.bias", f"encoder.down_blocks.{stage}.downsampler.resample.1.bias")
        if f"encoder.down_blocks.{stage}.downsampler.time_conv.weight" in diffusers_keys:
            add(f"{prefix_n}.{sub}.time_conv.weight", f"encoder.down_blocks.{stage}.downsampler.time_conv.weight")
            add(f"{prefix_n}.{sub}.time_conv.bias", f"encoder.down_blocks.{stage}.downsampler.time_conv.bias")

    # --- decoder upsample stages: native upsamples.N.upsamples.M  <->  diffusers up_blocks.N.resnets.M ---
    for stage in range(4):
        prefix_n = f"decoder.upsamples.{stage}.upsamples"
        prefix_d = f"decoder.up_blocks.{stage}.resnets"
        sub = 0
        for resnet in range(3):
            base_n = f"{prefix_n}.{sub}"
            base_d = f"{prefix_d}.{resnet}"
            add(f"{base_n}.residual.0.gamma", f"{base_d}.norm1.gamma")
            add(f"{base_n}.residual.2.bias", f"{base_d}.conv1.bias")
            add(f"{base_n}.residual.2.weight", f"{base_d}.conv1.weight")
            add(f"{base_n}.residual.3.gamma", f"{base_d}.norm2.gamma")
            add(f"{base_n}.residual.6.bias", f"{base_d}.conv2.bias")
            add(f"{base_n}.residual.6.weight", f"{base_d}.conv2.weight")
            if f"{base_d}.conv_shortcut.weight" in diffusers_keys:
                add(f"{base_n}.shortcut.weight", f"{base_d}.conv_shortcut.weight")
                add(f"{base_n}.shortcut.bias", f"{base_d}.conv_shortcut.bias")
            sub += 1
        # spatial + temporal upsampler (absent on the last stage)
        if f"decoder.up_blocks.{stage}.upsampler.resample.1.weight" in diffusers_keys:
            add(f"{prefix_n}.{sub}.resample.1.weight", f"decoder.up_blocks.{stage}.upsampler.resample.1.weight")
            add(f"{prefix_n}.{sub}.resample.1.bias", f"decoder.up_blocks.{stage}.upsampler.resample.1.bias")
        if f"decoder.up_blocks.{stage}.upsampler.time_conv.weight" in diffusers_keys:
            add(f"{prefix_n}.{sub}.time_conv.weight", f"decoder.up_blocks.{stage}.upsampler.time_conv.weight")
            add(f"{prefix_n}.{sub}.time_conv.bias", f"decoder.up_blocks.{stage}.upsampler.time_conv.bias")

    return mapping


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("diffusers_vae", type=Path, help="path to Edge package vae/diffusion_pytorch_model.safetensors")
    parser.add_argument("out", type=Path, help="output Wan2.2_VAE.pth (native layout)")
    args = parser.parse_args()

    global diffusers_keys
    from safetensors.torch import load_file
    d = load_file(args.diffusers_vae)
    diffusers_keys = set(d.keys())
    assert len(d) == 196, f"expected 196 keys, got {len(d)}"

    mapping = build_mapping()

    with torch.device("meta"):
        m = WanVAE_(temporal_window=4, encode_exact_durations=None)
    native_keys = set(m.state_dict().keys())

    # -- verify mapping is a complete bijection with matching shapes --
    assert set(mapping) == native_keys, (
        f"native keys not fully mapped: {sorted(native_keys - set(mapping))}"
    )
    assert set(mapping.values()) == diffusers_keys, (
        f"diffusers keys not consumed: {sorted(diffusers_keys - set(mapping.values()))}"
    )

    out: dict[str, torch.Tensor] = {}
    for native_key, diff_key in mapping.items():
        n_shape = tuple(m.state_dict()[native_key].shape)
        d_shape = tuple(d[diff_key].shape)
        assert n_shape == d_shape, f"shape mismatch {native_key} {n_shape} vs {diff_key} {d_shape}"
        out[native_key] = d[diff_key].contiguous()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(out, args.out)
    print(f"OK: {len(out)} keys mapped (shapes verified), saved -> {args.out}")
    print("top-level: " + ", ".join(sorted(k for k in out if not k.startswith(("encoder.", "decoder.")))))


if __name__ == "__main__":
    main()
