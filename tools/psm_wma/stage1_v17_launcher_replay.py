"""Pure Stage-1 v1.7 launcher payload replay; intentionally no I/O entrypoint."""
from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import dataclass


class AuthorityReplayError(RuntimeError):
    pass


@dataclass(frozen=True)
class ReplayBinding:
    formal_parent: str
    base_path: str
    base_blob_oid: str
    base_raw_sha256: str
    base_bytes: int
    parser_replacements: tuple[tuple[str, str, str], ...]
    source_replacements: tuple[tuple[str, str], ...]
    owner_fd_flag: str
    owner_fd_value: str
    expected_parser_bytes: int
    expected_parser_sha256: str
    expected_outer_bytes: int
    expected_outer_sha256: str


@dataclass(frozen=True)
class ReplayedOuterPayload:
    parser_argv_bytes: bytes
    parser_argv_sha256: str
    outer_payload_bytes: bytes
    outer_payload_sha256: str


def _fail(category: str) -> None:
    raise AuthorityReplayError(f"BLOCKED_AUTHORITY_NOT_CLOSED:{category}")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _table_digest(rows: object) -> str:
    return _sha(json.dumps(rows, separators=(",", ":"), ensure_ascii=False).encode())


_GUARDS = {
    "7538": ("if len(raw)!=", " or digest(raw)!="),
    "7e1c0ecc2161984a88ea0d0eae82f9f7ced709ca919f0302f74a3a068e08c9b8": ("if len(raw)!=9406 or digest(raw)!=\"", "\": fail(\"bootstrap identity\")"),
    "2427": ("len(RAW[2])!=", " or tuple(digest(x) for x in RAW)!="),
    "72777bd7305c760c48c069eafd068f1a538383a6fdb8d40258acf3d8fc3b7ae2": ("+(\"", "\",): fail(\"embedded authority\")"),
}
_BOOT_ROWS = frozenset(("7538", "7e1c0ecc2161984a88ea0d0eae82f9f7ced709ca919f0302f74a3a068e08c9b8"))
_CANONICAL_PARENT = "08d5828cdb4c12afa3b798ff01826c91ceb8755a"
_CANONICAL_TABLE_DIGESTS = ("961985b47da32e589cfab7c3c064bd336f853fd319c701be3361ba6c129da707", "24d287620936fd334526b30745839527ce3720e2be3e55ea09de8309ffa71b05")


def _function_span(raw: str, name: str) -> tuple[int, int]:
    try:
        tree = ast.parse(raw)
    except SyntaxError:
        _fail("source_target")
    node = next((item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == name), None)
    if node is None or node.end_lineno is None:
        _fail("source_target")
    lines = raw.splitlines(keepends=True)
    return sum(map(len, lines[:node.lineno - 1])), sum(map(len, lines[:node.end_lineno]))


def _replace_once(raw: str, old: str, new: str) -> str:
    guard = _GUARDS.get(old)
    if guard is not None:
        token = guard[0] + old + guard[1]
        start, end = _function_span(raw, "boot" if old in _BOOT_ROWS else "main")
        region = raw[start:end]
        if raw.count(token) != 1 or region.count(token) != 1:
            _fail("source_target")
        changed = region.replace(token, guard[0] + new + guard[1], 1)
        return raw[:start] + changed + raw[end:]
    if raw.count(old) != 1:
        _fail("source_target")
    return raw.replace(old, new, 1)


def replay_outer_payload(*, base_source: bytes, binding: ReplayBinding) -> ReplayedOuterPayload:
    """Rebuild frozen payload bytes from injected source without filesystem or process I/O."""
    if len(base_source) != binding.base_bytes or _sha(base_source) != binding.base_raw_sha256:
        _fail("base_identity")
    if binding.formal_parent == _CANONICAL_PARENT:
        if _table_digest(binding.parser_replacements) != _CANONICAL_TABLE_DIGESTS[0]: _fail("parser_target")
        if _table_digest(binding.source_replacements) != _CANONICAL_TABLE_DIGESTS[1]: _fail("source_target")
    try:
        source = base_source.decode("utf-8")
        match = re.search(r"RAW\s*=\s*\(.*?b'''(\[.*?\])'''", source, re.S)
        if match is None:
            _fail("raw_shape")
        argv = json.loads(match.group(1))
    except (UnicodeDecodeError, json.JSONDecodeError):
        _fail("raw_shape")
    if not isinstance(argv, list) or any(not isinstance(item, str) for item in argv):
        _fail("raw_shape")
    if binding.owner_fd_flag in argv:
        _fail("owner_fd")
    seen: set[str] = set()
    previous_index = -1
    for flag, old, new in binding.parser_replacements:
        if flag in seen or argv.count(flag) != 1:
            _fail("parser_target")
        seen.add(flag)
        index = argv.index(flag)
        if index <= previous_index or index + 1 >= len(argv) or argv[index + 1] != old:
            _fail("parser_target")
        previous_index = index
        argv[index + 1] = new
    root_flag = "--bootstrap-project-root"
    if argv.count(root_flag) != 1:
        _fail("insert_position")
    root_index = argv.index(root_flag)
    if root_index + 1 >= len(argv):
        _fail("insert_position")
    argv[root_index + 2:root_index + 2] = [binding.owner_fd_flag, binding.owner_fd_value]
    parser = json.dumps(argv, separators=(",", ":"), ensure_ascii=False).encode()
    if len(parser) != binding.expected_parser_bytes or _sha(parser) != binding.expected_parser_sha256:
        _fail("replay_drift")
    source = source[:match.start(1)] + parser.decode() + source[match.end(1):]
    for old, new in binding.source_replacements:
        source = _replace_once(source, old, new)
    outer = source.encode()
    if len(outer) != binding.expected_outer_bytes or _sha(outer) != binding.expected_outer_sha256:
        _fail("replay_drift")
    return ReplayedOuterPayload(parser, _sha(parser), outer, _sha(outer))
