"""Replay actual ordered T1 batch contexts; explicitly loads the real VAE."""

import argparse
import json
import sys
from pathlib import Path


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset-root", type=Path, required=True)
    p.add_argument("--weights", type=Path, required=True)
    p.add_argument("--cosmos-root", type=Path)
    p.add_argument("--device", default="cuda:0")
    p.add_argument("--task", action="append")
    p.add_argument("--episode", type=int, action="append")
    p.add_argument("--max-batch-size", type=int, default=32)
    a = p.parse_args(argv)
    try:
        from g2.latent_cache.batch_encoding import WanBatchEncoder
        from g2.latent_cache.batch_verify import verify_replay

        e = WanBatchEncoder(
            a.weights,
            cosmos_root=a.cosmos_root,
            device=a.device,
            max_batch_size=a.max_batch_size,
        )
        print(
            json.dumps(
                verify_replay(a.dataset_root, e, tasks=a.task, episodes=a.episode),
                sort_keys=True,
            )
        )
        return 0
    except (ValueError, OSError, RuntimeError, KeyError, TypeError) as exc:
        print(json.dumps(dict(complete=False, error=str(exc))), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
