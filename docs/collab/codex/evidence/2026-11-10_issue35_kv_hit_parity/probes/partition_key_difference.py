"""Server-only CPU reduction of private key operands; publish no tensor values."""

import json
from pathlib import Path
import sys

import torch

from probe_cache_hit import tensor_info

BASE = Path(
    "/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_codex_issue35_kv_hit_parity_20261110"
)
ROOT = BASE.parent / "_codex_issue31_prefix_pack_20261109/root2"
sys.path[:0] = [str(ROOT), str(ROOT / "cosmos-framework"), str(ROOT / "scripts")]


def main():
    records = []
    for history, layer in [(1, 18), (16, 16)]:
        source = BASE / f"probe03/k{history}/first_hit_probe"
        args = torch.load(
            source / f"full_compute_capture_s01_l{layer:02d}_layer_input.pt",
            map_location="cpu",
            weights_only=False,
        )
        operands = BASE / "operands04/k1/operand_probe"
        full = torch.load(
            operands / f"K{history}_full_attention.pt",
            map_location="cpu",
            weights_only=False,
        )["k"]
        hit = torch.load(
            operands / f"K{history}_hit_attention.pt",
            map_location="cpu",
            weights_only=False,
        )["k"]
        pack = args["args"][0]
        prefix = args["kwargs"]["memory_prefix_context"].k_local
        parts = dict(
            prefix=torch.arange(prefix),
            und=pack["_causal_indices"].long() + prefix,
            gen=pack["_full_indices"].long() + prefix,
        )
        used = torch.cat(list(parts.values()))
        assert used.unique().numel() == used.numel()
        unused = torch.ones(full.shape[0], dtype=torch.bool)
        unused[used] = False
        parts["padding"] = unused.nonzero().flatten()
        row = dict(k=history, layer=layer, prefix_len=prefix, parts={})
        for name, indices in parts.items():
            a = full.index_select(0, indices)
            b = hit.index_select(0, indices)
            changed = (a != b).nonzero()
            row["parts"][name] = dict(
                rows=indices.numel(),
                changed_elements=changed.shape[0],
                changed_rows=changed[:, 0].unique().numel() if changed.numel() else 0,
                max_abs=float((a.float() - b.float()).abs().max()) if a.numel() else 0,
                full_sha256=tensor_info(a)["sha256"],
                hit_sha256=tensor_info(b)["sha256"],
            )
        records.append(row)
    result = dict(
        status="KEY_OPERAND_PARTITION_COMPLETE",
        records=records,
        original_tensor_values_exported=False,
    )
    with (BASE / "key_partition01.json").open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
