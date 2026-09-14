"""Pure Stage-1 v1.7 launcher payload replay; intentionally no I/O entrypoint."""
from __future__ import annotations

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


_GUARDS = {
    "7538": ("if len(raw)!=", " or digest(raw)!="),
    "7e1c0ecc2161984a88ea0d0eae82f9f7ced709ca919f0302f74a3a068e08c9b8": ("if len(raw)!=9406 or digest(raw)!=\"", "\": fail(\"bootstrap identity\")"),
    "2427": ("len(RAW[2])!=", " or tuple(digest(x) for x in RAW)!="),
    "72777bd7305c760c48c069eafd068f1a538383a6fdb8d40258acf3d8fc3b7ae2": ("+(\"", "\",): fail(\"embedded authority\")"),
}


def _replace_once(raw: str, old: str, new: str) -> str:
    guard = _GUARDS.get(old)
    if guard is not None:
        token = guard[0] + old + guard[1]
        if raw.count(token) != 1:
            _fail("source_target")
        return raw.replace(token, guard[0] + new + guard[1], 1)
    if raw.count(old) != 1:
        _fail("source_target")
    return raw.replace(old, new, 1)


def replay_outer_payload(*, base_source: bytes, binding: ReplayBinding) -> ReplayedOuterPayload:
    """Rebuild frozen payload bytes from injected source without filesystem or process I/O."""
    if len(base_source) != binding.base_bytes or _sha(base_source) != binding.base_raw_sha256:
        _fail("base_identity")
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
