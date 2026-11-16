"""Replay unchanged reviewer assertions without rewriting reviewer evidence."""

import os
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = (
    ROOT
    / "docs/collab/chatgpt/evidence/2026-11-16_issue52_aa0450b8/test_review_edges.py"
)
namespace = runpy.run_path(str(ORIGINAL))
OUTPUT = Path(__file__).parent / os.environ.get("ISSUE52_GATE_PHASE", "green")
OUTPUT.mkdir(parents=True, exist_ok=True)
for name in (
    "test_foreign_cosmos_parent_must_be_rejected",
    "test_plan_must_reject_native_unsupported_canvas",
):
    function = namespace[name]
    function.__globals__["SOURCE"] = ROOT
    function.__globals__["__file__"] = str(OUTPUT / "test_review_edges.py")
    globals()[name] = function
