"""Pure AST projection for the frozen Stage-1 v1.7 request closure."""
from __future__ import annotations

import ast
import base64
import hashlib
import json
from dataclasses import dataclass

from tools.psm_wma.stage1_v17_launcher_replay import AuthorityReplayError


OUTER = (18875, "658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8")
ADAPTER = ("4a51bddd15ec9a88883e3071cc550de85721599b", "87e22fac98e61ba9fbf5e0c1adaf3f620365f35a04a266576c5bce4b83e9e816")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _fail(category: str) -> None:
    raise AuthorityReplayError(f"BLOCKED_AUTHORITY_NOT_CLOSED:projection_{category}")


@dataclass(frozen=True)
class ProjectedBytes:
    raw: bytes
    byte_length: int
    sha256: str


@dataclass(frozen=True)
class ProjectedRequestClosure:
    selection: ProjectedBytes
    config: ProjectedBytes
    parser_argv: ProjectedBytes
    parser_argv_items: tuple[str, ...]
    bootstrap_argv: ProjectedBytes
    bootstrap: ProjectedBytes
    bootstrap_contract: ProjectedBytes
    outer: ProjectedBytes
    adapter_source: ProjectedBytes


def _box(raw: bytes) -> ProjectedBytes:
    return ProjectedBytes(raw, len(raw), _sha(raw))


def _literal(node: ast.AST) -> bytes:
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes)):
        return node.value.encode() if isinstance(node.value, str) else node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _literal(node.left) + _literal(node.right)
    _fail("literal")


def _decode(node: ast.AST) -> bytes:
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name) and node.func.value.id == "base64"
            and node.func.attr == "b64decode" and len(node.args) == 1 and not node.keywords):
        _fail("raw_target")
    try:
        return base64.b64decode(_literal(node.args[0]), validate=True)
    except Exception:
        _fail("base64")


def project_request_closure(outer_payload_bytes: bytes, adapter_source_bytes: bytes) -> ProjectedRequestClosure:
    if (len(outer_payload_bytes), _sha(outer_payload_bytes)) != OUTER: _fail("input_identity")
    if _sha(adapter_source_bytes) != ADAPTER[1]: _fail("input_identity")
    try:
        tree = ast.parse(outer_payload_bytes.decode())
        raw_nodes = [n.value for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "RAW" for t in n.targets)]
        if len(raw_nodes) != 1 or not isinstance(raw_nodes[0], ast.Tuple) or len(raw_nodes[0].elts) != 3: _fail("raw_shape")
        selection, config, parser_raw = _decode(raw_nodes[0].elts[0]), _decode(raw_nodes[0].elts[1]), _literal(raw_nodes[0].elts[2])
        items = json.loads(parser_raw)
        if not isinstance(items, list) or any(not isinstance(x, str) for x in items): _fail("argv")
        bootstrap_argv = json.dumps(["--", *items], separators=(",", ":"), ensure_ascii=False).encode()
        adapter = ast.parse(adapter_source_bytes.decode())
        funcs = [n for n in adapter.body if isinstance(n, ast.FunctionDef) and n.name == "bootstrap_payload"]
        if len(funcs) != 1 or funcs[0].args.args or not funcs[0].body or not isinstance(funcs[0].body[-1], ast.Return): _fail("bootstrap")
        bootstrap = _literal(funcs[0].body[-1].value)
    except AuthorityReplayError:
        raise
    except Exception:
        _fail("parse")
    contract = json.dumps({"bootstrap_argv_sha256": _sha(bootstrap_argv), "bootstrap_raw_sha256": _sha(bootstrap)}, sort_keys=True, separators=(",", ":")).encode()
    return ProjectedRequestClosure(_box(selection), _box(config), _box(parser_raw), tuple(items), _box(bootstrap_argv), _box(bootstrap), _box(contract), _box(outer_payload_bytes), _box(adapter_source_bytes))
