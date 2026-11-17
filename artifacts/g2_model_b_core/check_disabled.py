"""Compare disabled native MoT against the exact public C0 sources on CPU."""
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

import torch

from cosmos_framework.model.generator.mot import attention as current_attention
from cosmos_framework.model.generator.mot.g2_core_test import cpu_attention, native_pack, tiny_model
from cosmos_framework.model.generator.mot.memory_prefix import build_memory_prefix_context
from cosmos_framework.data.generator.sequence_packing.runtime import get_gen_seq, get_und_seq

BASE = "ec9356fafd1fd18cc0bd552b7eb23428f59df7f6"
ROOT = Path.cwd()
PKG = "cosmos_framework.model.generator.mot"


def load_source(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


with tempfile.TemporaryDirectory(dir=ROOT / "work") as temporary:
    temp = Path(temporary)
    for stem in ("attention", "unified_mot"):
        (temp / f"{stem}.py").write_bytes(subprocess.check_output([
            "git", "show", f"{BASE}:cosmos_framework/model/generator/mot/{stem}.py"
        ], cwd=ROOT))
    old_attention = load_source(f"{PKG}._c0_attention", temp / "attention.py")
    sys.modules[f"{PKG}.attention"] = old_attention
    try:
        old_mot = load_source(f"{PKG}._c0_unified_mot", temp / "unified_mot.py")
    finally:
        sys.modules[f"{PKG}.attention"] = current_attention
    old_attention.attention = current_attention.attention = cpu_attention
    print(f"baseline={BASE} device=cpu torch={torch.__version__} synthetic_only=True")
    for lengths in ((3,), (3, 0, 1)):
        for use_local in (False, True):
            torch.manual_seed(123)
            new = tiny_model()
            new_rng = torch.random.get_rng_state().clone()
            torch.manual_seed(123)
            old = old_mot.Qwen3VLTextModel(new.config, qk_norm_for_text=False,
                qk_norm_for_diffusion=True, use_und_k_norm_for_gen=True)
            for name, p in old.named_parameters():
                p.requires_grad_("moe_gen" in name or "k_norm_und_for_gen" in name)
            assert torch.equal(new_rng, torch.random.get_rng_state())
            assert new.state_dict().keys() == old.state_dict().keys()
            for name, value in new.state_dict().items():
                torch.testing.assert_close(value, old.state_dict()[name], atol=0, rtol=0)
            gen = [torch.randn(2, 16) for _ in lengths]
            local_data = torch.randn(4, 4)
            bridge = torch.nn.Linear(4, 16)
            grads, outs, rngs = [], [], []
            for model in (old, new):
                local = local_data.clone().requires_grad_()
                prefix = build_memory_prefix_context(tuple(local if i % 2 == 0 else None for i in range(len(lengths))),
                    bridge, torch.zeros(16), target_dtype=torch.float32) if use_local else None
                pack, mask, pos, _ = native_pack(model, lengths, gen)
                rng = torch.random.get_rng_state().clone()
                out, _ = model(pack, mask, pos, memory_prefix_context=prefix)
                values = get_gen_seq(out)[:2 * len(lengths)]
                loss = (values * torch.arange(1, 17)).sum()
                loss.backward()
                grads.append({n: None if p.grad is None else p.grad.clone() for n, p in model.named_parameters()})
                if use_local:
                    grads[-1]["local_input"] = local.grad.clone()
                outs.append((values.detach(), get_und_seq(out)[:sum(lengths)].detach()))
                rngs.append(torch.equal(rng, torch.random.get_rng_state()))
                bridge.zero_grad(set_to_none=True)
            for lhs, rhs in zip(outs[0], outs[1], strict=True):
                torch.testing.assert_close(lhs, rhs, atol=0, rtol=0)
            for name, value in grads[0].items():
                if value is None:
                    assert grads[1][name] is None
                else:
                    torch.testing.assert_close(value, grads[1][name], atol=0, rtol=0)
            assert all(rngs)
            print(f"lengths={lengths} local={use_local}: output/grad/init_rng/forward_rng exact PASS")
