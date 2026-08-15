#!/usr/bin/env python3
"""G0-R04 正式验收：domain 行保护对比。

对比源 DCP 与训练后 checkpoint 的 4 个 DomainAwareLinear 表
（net.action2llm/net.llm2action 的 fc/bias.weight，shape [32, ...]）：
LIBERO 批次只应更新 domain 5 行，其余行必须 bitwise 不变。

用法：
  python tools/g0/verify_domain_rows.py \
      --source /gemini/code/models/Cosmos3-Edge-Policy-DROID-dcp/model \
      --updated <run>/checkpoints/iter_000000020/model \
      --domain 5 --output domain_row_guard.json
"""

from __future__ import annotations

import argparse
import json

import torch
from torch.distributed.checkpoint.state_dict_loader import _load_state_dict_from_keys

DOMAIN_KEYS = [
    "net.action2llm.fc.weight",
    "net.action2llm.bias.weight",
    "net.llm2action.fc.weight",
    "net.llm2action.bias.weight",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="源 DCP model/ 目录")
    parser.add_argument("--updated", required=True, help="训练后 checkpoint model/ 目录")
    parser.add_argument("--domain", type=int, default=5, help="LIBERO domain_id")
    parser.add_argument("--output", required=True, help="结果 JSON 路径")
    args = parser.parse_args()

    source = _load_state_dict_from_keys(DOMAIN_KEYS, checkpoint_id=args.source)
    updated = _load_state_dict_from_keys(DOMAIN_KEYS, checkpoint_id=args.updated)

    report: dict[str, object] = {"source": args.source, "updated": args.updated, "domain": args.domain, "keys": {}}
    all_pass = True
    for key in DOMAIN_KEYS:
        src, upd = source[key].float(), updated[key].float()
        row_mask = torch.ones(src.shape[0], dtype=torch.bool)
        row_mask[args.domain] = False
        frozen_diff = (src[row_mask] - upd[row_mask]).abs().max().item()
        domain_diff = (src[~row_mask] - upd[~row_mask]).abs().max().item()
        frozen_ok = frozen_diff == 0.0
        domain_moved = domain_diff > 0.0
        all_pass &= frozen_ok and domain_moved
        report["keys"][key] = {
            "shape": list(src.shape),
            "frozen_rows_max_abs_diff": frozen_diff,
            "frozen_rows_bitwise_unchanged": frozen_ok,
            "domain_row_max_abs_diff": domain_diff,
            "domain_row_updated": domain_moved,
        }
    report["pass"] = all_pass
    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False))
    raise SystemExit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
