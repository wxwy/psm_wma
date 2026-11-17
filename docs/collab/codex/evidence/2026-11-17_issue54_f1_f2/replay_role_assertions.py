"""Run the two unchanged reviewer role bodies without importing optional Arrow.

The full original three-test file remains untouched. Its F1 test requires real
PyArrow and must run separately in an existing Arrow-capable environment.
No pyarrow stubs, substitute parser, or edited reviewer assertions are used.
"""

import ast
import hashlib
from pathlib import Path

from g2.offline.task_entities import bind_task_entities  # noqa: F401

SOURCE = (
    Path(__file__).parents[3]
    / "chatgpt/evidence/2026-11-17_issue54_27ccadb0/test_review_source_contracts.py"
)
PAYLOAD = SOURCE.read_bytes()
assert (
    hashlib.sha256(PAYLOAD).hexdigest()
    == "860424fa81b6447cb361d7272ff0a365dfef6ef6087b0a3f51ab97f63fd306e0"
)
NAMES = {
    "entity",
    "test_close_blender_lid_binds_independent_auxiliary_fixture",
    "test_counter_to_stove_binds_named_source_container",
}
NODES = [
    node
    for node in ast.parse(PAYLOAD).body
    if isinstance(node, ast.FunctionDef) and node.name in NAMES
]
assert {node.name for node in NODES} == NAMES
exec(compile(ast.Module(body=NODES, type_ignores=[]), str(SOURCE), "exec"), globals())
