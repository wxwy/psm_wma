"""Replay unchanged reviewer assertions with local source/output bindings only."""

import os
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "docs/collab/chatgpt/evidence/2026-11-16_issue52_900c87aa"
OUTPUT = Path(__file__).parent / os.environ.get("ISSUE52_GATE_PHASE", "green")
OUTPUT.mkdir(parents=True, exist_ok=True)
for file, names in (
    (
        "test_review_edges.py",
        (
            "test_foreign_cosmos_parent_must_be_rejected",
            "test_plan_must_reject_native_unsupported_canvas",
        ),
    ),
    (
        "test_native_namespace.py",
        ("test_selected_child_native_namespace_must_be_accepted",),
    ),
):
    namespace = runpy.run_path(str(EVIDENCE / file))
    for name in names:
        function = namespace[name]
        function.__globals__["SOURCE"] = ROOT
        function.__globals__["__file__"] = str(OUTPUT / file)
        globals()[name] = function
