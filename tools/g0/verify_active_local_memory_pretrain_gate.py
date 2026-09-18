"""Canonical acceptance entrypoint for the active Local-Memory A2 delivery.

Historical B=1 Gate summaries are retained in Git history. They cannot authorize
an A2 run. This entrypoint delegates to actual source-bound execution evidence.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if "--cpu" not in sys.argv and not any(arg in sys.argv for arg in ("-h", "--help")):
        report = {
            "result": "BLOCKED",
            "long_run_authorization": False,
            "reason": "Historical B=1 artifact summaries do not verify the current A2 route.",
            "required": [
                "--cpu",
                "--control",
                "--resume",
                "--expected-child",
                "--output",
            ],
            "budget": "Use --budget and --require-budget for the 20-step delivery check.",
        }
        print(json.dumps(report, indent=2))
        if "--output-json" in sys.argv:
            index = sys.argv.index("--output-json")
            if index + 1 < len(sys.argv):
                path = Path(sys.argv[index + 1])
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(report, indent=2) + "\n")
        return 2
    if __package__:
        from .verify_a2_delivery import main as verify
    else:
        from verify_a2_delivery import main as verify
    return verify()


if __name__ == "__main__":
    raise SystemExit(main())
