#!/usr/bin/env python3
"""Check VAE dtype under training model setup."""

from __future__ import annotations

import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "cosmos-framework"))

from cosmos_framework.model.generator.omni_mot_model import OmniMoTModel
from cosmos_framework.utils.config import load_config


def main() -> int:
    config_path = Path("/disk/rl/psm_wma/outputs/verify_cache_v6/cosmos3_action_libero/action_sft/edge_libero_4in1/config.yaml")
    config = load_config(str(config_path), opts=[])
    model = OmniMoTModel(config)
    print(f"model.precision = {model.precision}")
    print(f"tensor_kwargs = {model.tensor_kwargs}")
    print(f"tensor_kwargs_fp32 = {model.tensor_kwargs_fp32}")
    if model.tokenizer_vision_gen is not None:
        print(f"tokenizer_vision_gen dtype = {model.tokenizer_vision_gen.dtype}")
        m = model.tokenizer_vision_gen.model
        print(f"tokenizer model dtype = {next(m.parameters()).dtype}")
        if hasattr(m, "model"):
            print(f"tokenizer model.model dtype = {next(m.model.parameters()).dtype}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
