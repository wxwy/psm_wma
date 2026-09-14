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
PARSER_ARGV = (2336, "1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333")
BOOTSTRAP_ARGV = (2341, "85ac67c8a062399dfbface5f9c42867401ffab45320f802697c704061be8df9d")
BOOTSTRAP_CONTRACT = (182, "bec6a57aab61fd888ef0eedce37adce227a38a299a9faded53b252c8b5901702")
FLAG_VALUES = (
    ("--selection-fd", "3"), ("--config-fd", "4"),
    ("--formal-root", "08d5828cdb4c12afa3b798ff01826c91ceb8755a"),
    ("--child-gitlink", "93a89ba61306d840a008813f62f26a34d54850f4"),
    ("--selection-raw-sha256", "8fe4585f366cb69ad9181e30c25b5f4e99040c83d8ffe66426897bfa9d331edd"),
    ("--config-raw-sha256", "43b3b77b5934107c54b8bee157b46d07cb17b85ca89305ad6fb7405237e42d1d"),
    ("--cwd", "/proc/self/fd/8"), ("--remote", "https://github.com/wxwy/psm_wma.git"),
    ("--index", "/proc/self/fd/8/.authority-root.index"),
    ("--evidence-path", "/disk/rl/psm_wma/artifacts/g0/r09/authority_root_materialization_evidence_v1.json"),
    ("--git", "/usr/bin/git"), ("--git-raw-sha256", "587ef21868c948b883993e23209b86a72a6ddc06aab1545c697ffc31075acd4a"),
    ("--git-version", "git version 2.34.1"), ("--interpreter", "/opt/conda/bin/python3"),
    ("--interpreter-raw-sha256", "f3e3f561b473976be55d937616915d6c507dedcb3950c3ca72df786b28e8efdc"),
    ("--interpreter-version", "Python 3.11.9"), ("--bootstrap-contract-fd", "5"),
    ("--bootstrap-project-root", "/proc/self/fd/8"), ("--bootstrap-owner-root-fd", "8"),
    ("--bootstrap-module", "tools.psm_wma.materialize_immutable_source_authority_root"),
    ("--adapter-path", "tools/psm_wma/materialize_immutable_source_authority_root.py"),
    ("--adapter-blob-oid", "4a51bddd15ec9a88883e3071cc550de85721599b"),
    ("--adapter-raw-sha256", "87e22fac98e61ba9fbf5e0c1adaf3f620365f35a04a266576c5bce4b83e9e816"),
    ("--authority-module-path", "tools/psm_wma/immutable_source_authority_root.py"),
    ("--authority-module-blob-oid", "9937f74c49b14d489823c731aa2856b00c1a3d06"),
    ("--authority-module-raw-sha256", "4ebf9fb8b0605bc30c45800bdfa7d367444ff97daee69926eba9aa5c9817f5d0"),
    ("--collection-module-path", "tools/psm_wma/immutable_source_collection.py"),
    ("--collection-module-blob-oid", "4e9f51a52e822e7e57b67aa6ff5eaab8613566c1"),
    ("--collection-module-raw-sha256", "89eb3ee194f16665aea76ed4dcbaba803fc944d1e0b889d25be69d0831e68c67"),
    ("--audit-module-path", "tools/g0/audit_r09_b_ttt_root_gitlink_authority.py"),
    ("--audit-module-blob-oid", "d0020f067badfe591152fafa6336e20b485eb5ba"),
    ("--audit-module-raw-sha256", "3db6376b35141d8ca5dc72c1bb38359943961db92545a88f320603121db4c39e"),
    ("--author-name", "wxwy"), ("--author-email", "1036648581@qq.com"),
    ("--author-date", "2026-09-12T23:07:43+08:00"), ("--committer-name", "wxwy"),
    ("--committer-email", "1036648581@qq.com"), ("--committer-date", "2026-09-12T23:07:43+08:00"),
    ("--commit-message", "chore: materialize immutable source authority root"),
)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _blob_oid(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


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
        raw = _literal(node.args[0])
        if any(value > 127 for value in raw): _fail("raw_target")
        return base64.b64decode(raw, validate=True)
    except Exception:
        _fail("base64")


def project_request_closure(outer_payload_bytes: bytes, adapter_source_bytes: bytes) -> ProjectedRequestClosure:
    if (len(outer_payload_bytes), _sha(outer_payload_bytes)) != OUTER: _fail("input_identity")
    if (_blob_oid(adapter_source_bytes), _sha(adapter_source_bytes)) != ADAPTER: _fail("input_identity")
    try:
        tree = ast.parse(outer_payload_bytes.decode())
        raw_nodes = [n.value for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "RAW" for t in n.targets)]
        if len(raw_nodes) != 1 or not isinstance(raw_nodes[0], ast.Tuple) or len(raw_nodes[0].elts) != 3: _fail("raw_shape")
        selection, config, parser_raw = _decode(raw_nodes[0].elts[0]), _decode(raw_nodes[0].elts[1]), _literal(raw_nodes[0].elts[2])
        items = json.loads(parser_raw)
        canonical = json.dumps(items, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        if (not isinstance(items, list) or any(not isinstance(x, str) for x in items)
                or canonical != parser_raw or len(items) % 2 or tuple(zip(items[::2], items[1::2])) != FLAG_VALUES): _fail("argv")
        bootstrap_argv = json.dumps(["--", *items], separators=(",", ":"), ensure_ascii=False).encode()
        adapter = ast.parse(adapter_source_bytes.decode())
        funcs = [n for n in adapter.body if isinstance(n, ast.FunctionDef) and n.name == "bootstrap_payload"]
        if len(funcs) != 1: _fail("bootstrap")
        function = funcs[0]
        arguments = function.args
        if (function.decorator_list or arguments.posonlyargs or arguments.args or arguments.kwonlyargs
                or arguments.vararg or arguments.kwarg or arguments.defaults or arguments.kw_defaults
                or len(function.body) not in (1, 2) or not isinstance(function.body[-1], ast.Return)
                or (len(function.body) == 2 and not (isinstance(function.body[0], ast.Expr)
                    and isinstance(function.body[0].value, ast.Constant)
                    and isinstance(function.body[0].value.value, str)))): _fail("bootstrap")
        bootstrap = _literal(function.body[-1].value)
    except AuthorityReplayError:
        raise
    except Exception:
        _fail("parse")
    contract = json.dumps({"bootstrap_argv_sha256": _sha(bootstrap_argv), "bootstrap_raw_sha256": _sha(bootstrap)}, sort_keys=True, separators=(",", ":")).encode()
    if ((len(parser_raw), _sha(parser_raw)) != PARSER_ARGV
            or (len(bootstrap_argv), _sha(bootstrap_argv)) != BOOTSTRAP_ARGV
            or (len(contract), _sha(contract)) != BOOTSTRAP_CONTRACT): _fail("identity")
    return ProjectedRequestClosure(_box(selection), _box(config), _box(parser_raw), tuple(items), _box(bootstrap_argv), _box(bootstrap), _box(contract), _box(outer_payload_bytes), _box(adapter_source_bytes))
