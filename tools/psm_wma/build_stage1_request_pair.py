"""Pure byte construction for the pragmatic Stage-1 v0.5 request pair.

This module deliberately has no filesystem, Git, subprocess, or write entrypoint.
Callers inject immutable tree bytes and write a verified pair only after the
non-consuming execution preflight has frozen their observations.
"""
from __future__ import annotations

import ast
import base64
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path


CANON = "utf-8; recursive sorted keys; compact separators; exactly one terminal LF"


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob_oid(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()


def canonical_json(payload: dict[str, object]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"


def build_pair(json_path: Path, payload: dict[str, object]) -> tuple[bytes, bytes]:
    raw = canonical_json(payload)
    digest = sha256(raw)
    markdown = (
        f"json_filename: {json_path.as_posix()}\n"
        f"json_bytes: {len(raw)}\n"
        f"json_sha256: {digest}\n"
        f"canonicalization: {CANON}\n"
        f"json_git_blob_oid: {git_blob_oid(raw)}\n"
    ).encode("utf-8")
    return raw, markdown


def unified_patch(json_path: Path, markdown_path: Path, raw: bytes, markdown: bytes) -> bytes:
    """Return the exact two-new-file patch consumed by the Stage-1 request seam."""
    def added(path: Path, value: bytes) -> bytes:
        if not value.endswith(b"\n"):
            raise ValueError("request pair member requires terminal LF")
        return b"--- /dev/null\n+++ b/" + path.as_posix().encode() + b"\n" + b"".join(
            b"+" + line for line in value.splitlines(keepends=True)
        )

    return added(json_path, raw) + added(markdown_path, markdown)


def verify_pair(json_path: Path, raw: bytes, markdown: bytes) -> None:
    payload = json.loads(raw.decode("utf-8", "strict"))
    if not isinstance(payload, dict) or canonical_json(payload) != raw:
        raise ValueError("request JSON is not canonical")
    expected_raw, expected_markdown = build_pair(json_path, payload)
    if raw != expected_raw or markdown != expected_markdown:
        raise ValueError("request pair identity mismatch")


@dataclass(frozen=True)
class TreeBlob:
    path: str
    blob_oid: str
    raw_sha256: str


@dataclass(frozen=True)
class LauncherInputs:
    formal_root: str
    child_gitlink: str
    clean_suffix: str
    adapter: TreeBlob
    authority: TreeBlob
    collection: TreeBlob
    audit: TreeBlob


@dataclass(frozen=True)
class LauncherBytes:
    outer: bytes
    parser_argv: bytes
    parser_items: tuple[str, ...]
    bootstrap: bytes
    bootstrap_argv: bytes
    bootstrap_contract: bytes


def _identity(blob: TreeBlob, raw: bytes) -> dict[str, object]:
    if git_blob_oid(raw) != blob.blob_oid or sha256(raw) != blob.raw_sha256:
        raise ValueError(f"tree blob identity: {blob.path}")
    return {
        "path": blob.path,
        "blob_oid": blob.blob_oid,
        "bytes": len(raw),
        "sha256": blob.raw_sha256,
    }


def build_request_payload(
    inputs: LauncherInputs,
    base: TreeBlob,
    base_source: bytes,
    adapter_source: bytes,
    launcher: LauncherBytes,
    selection_raw: bytes,
    config_raw: bytes,
    preflight: dict[str, object],
) -> dict[str, object]:
    """Build the complete reviewable payload from already-frozen bytes/facts."""
    if not preflight:
        raise ValueError("missing non-consuming preflight")
    base_identity = _identity(base, base_source)
    adapter_identity = _identity(inputs.adapter, adapter_source)
    outer = launcher.outer.decode("utf-8", "strict")
    return {
        "schema": "r09_b_ttt_v035_stage1_request_instance_v0_5_pragmatic_immutable_commit",
        "formal_root": inputs.formal_root,
        "child_gitlink": inputs.child_gitlink,
        "environment": {
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": "/dev/null",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "LANG": "C",
            "LC_ALL": "C",
        },
        "launcher": {
            "base": base_identity,
            "outer_utf8": outer,
            "outer_bytes": len(launcher.outer),
            "outer_sha256": sha256(launcher.outer),
            "outer_git_blob_oid": git_blob_oid(launcher.outer),
            "argv_prefix": ["/opt/conda/bin/python3", "-I", "-S", "-B", "-c"],
            "inner_parser_argv": list(launcher.parser_items),
            "inner_parser_bytes": len(launcher.parser_argv),
            "inner_parser_sha256": sha256(launcher.parser_argv),
            "bootstrap": {
                "raw_utf8": launcher.bootstrap.decode("utf-8", "strict"),
                "bytes": len(launcher.bootstrap),
                "sha256": sha256(launcher.bootstrap),
                "argv_bytes": len(launcher.bootstrap_argv),
                "argv_sha256": sha256(launcher.bootstrap_argv),
                "contract_utf8": launcher.bootstrap_contract.decode("utf-8", "strict"),
                "contract_sha256": sha256(launcher.bootstrap_contract),
            },
        },
        "input_fd_contract": {
            "selection": {"fd": 3, "raw_utf8": selection_raw.decode("utf-8", "strict"), "bytes": len(selection_raw), "sha256": sha256(selection_raw)},
            "config": {"fd": 4, "raw_utf8": config_raw.decode("utf-8", "strict"), "bytes": len(config_raw), "sha256": sha256(config_raw)},
            "bootstrap_contract": {"fd": 5, "raw_utf8": launcher.bootstrap_contract.decode("utf-8", "strict"), "bytes": len(launcher.bootstrap_contract), "sha256": sha256(launcher.bootstrap_contract)},
            "owner_root": {"fd": 8, "open": "directory_no_follow"},
        },
        "tool_closure": [
            adapter_identity,
            {"path": inputs.authority.path, "blob_oid": inputs.authority.blob_oid, "sha256": inputs.authority.raw_sha256},
            {"path": inputs.collection.path, "blob_oid": inputs.collection.blob_oid, "sha256": inputs.collection.raw_sha256},
            {"path": inputs.audit.path, "blob_oid": inputs.audit.blob_oid, "sha256": inputs.audit.raw_sha256},
        ],
        "preflight": preflight,
        "stop": "freshness_snapshot -> one atomic request-pair write -> byte-for-byte verify -> hard stop",
    }


def _literal(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes)):
        return node.value.decode("utf-8") if isinstance(node.value, bytes) else node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _literal(node.left) + _literal(node.right)
    raise ValueError("bootstrap payload is not a literal")


def bootstrap_payload(adapter_source: bytes) -> bytes:
    """Extract an adapter literal bootstrap payload without importing it."""
    tree = ast.parse(adapter_source.decode("utf-8", "strict"))
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "bootstrap_payload"]
    if len(functions) != 1 or not functions[0].body or not isinstance(functions[0].body[-1], ast.Return):
        raise ValueError("bootstrap_payload shape")
    return _literal(functions[0].body[-1].value).encode("utf-8")


def _replace_one(raw: str, old: str, new: str, category: str) -> str:
    if raw.count(old) != 1:
        raise ValueError(f"launcher {category} is ambiguous")
    return raw.replace(old, new, 1)


def _parser_items(source: str) -> tuple[str, list[str]]:
    tree = ast.parse(source)
    raw_nodes = [node.value for node in tree.body if isinstance(node, ast.Assign)
                 and any(isinstance(target, ast.Name) and target.id == "RAW" for target in node.targets)]
    if len(raw_nodes) != 1 or not isinstance(raw_nodes[0], ast.Tuple) or len(raw_nodes[0].elts) != 3:
        raise ValueError("launcher RAW shape")
    node = raw_nodes[0].elts[2]
    if not isinstance(node, ast.Constant) or not isinstance(node.value, bytes):
        raise ValueError("launcher parser literal")
    parser = node.value.decode("utf-8", "strict")
    items = json.loads(parser)
    if not isinstance(items, list) or any(not isinstance(item, str) for item in items) or len(items) % 2:
        raise ValueError("launcher parser argv")
    return parser, items


def embedded_input_raws(base_source: bytes) -> tuple[bytes, bytes]:
    """Extract the two immutable FD payloads from frozen launcher source."""
    tree = ast.parse(base_source.decode("utf-8", "strict"))
    raw_nodes = [node.value for node in tree.body if isinstance(node, ast.Assign)
                 and any(isinstance(target, ast.Name) and target.id == "RAW" for target in node.targets)]
    if len(raw_nodes) != 1 or not isinstance(raw_nodes[0], ast.Tuple) or len(raw_nodes[0].elts) != 3:
        raise ValueError("launcher RAW shape")
    values: list[bytes] = []
    for node in raw_nodes[0].elts[:2]:
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name) and node.func.value.id == "base64"
                and node.func.attr == "b64decode" and len(node.args) == 1 and not node.keywords
                and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
            raise ValueError("launcher input literal")
        try:
            values.append(base64.b64decode(node.args[0].value.encode("ascii"), validate=True))
        except ValueError as error:
            raise ValueError("launcher input base64") from error
    return tuple(values)  # type: ignore[return-value]


def _set_flag(items: list[str], flag: str, value: str) -> None:
    if items.count(flag) != 1:
        raise ValueError(f"launcher missing flag: {flag}")
    index = items.index(flag)
    if index + 1 >= len(items):
        raise ValueError(f"launcher missing flag value: {flag}")
    items[index + 1] = value


def _replace_guard(source: str, pattern: str, replacement: str, category: str) -> str:
    source, count = re.subn(pattern, replacement, source, count=1)
    if count != 1:
        raise ValueError(f"launcher {category} guard")
    return source


def rebuild_launcher(base_source: bytes, adapter_source: bytes, inputs: LauncherInputs) -> LauncherBytes:
    """Mechanically retarget frozen launcher bytes to one immutable tree."""
    if len(inputs.formal_root) != 40 or len(inputs.child_gitlink) != 40:
        raise ValueError("commit identity")
    source = base_source.decode("utf-8", "strict")
    parser_literal, items = _parser_items(source)
    pairs = dict(zip(items[::2], items[1::2]))
    old_root = pairs.get("--formal-root")
    old_clean = pairs.get("--cwd")
    if old_root is None or old_clean is None or not old_clean.startswith("/disk/rl/psm_wma/.authority-root-materialization-"):
        raise ValueError("launcher historical root")
    values = {
        "--formal-root": inputs.formal_root,
        "--child-gitlink": inputs.child_gitlink,
        "--cwd": "/proc/self/fd/8",
        "--index": "/proc/self/fd/8/.authority-root.index",
        "--bootstrap-project-root": "/proc/self/fd/8",
        "--adapter-path": inputs.adapter.path,
        "--adapter-blob-oid": inputs.adapter.blob_oid,
        "--adapter-raw-sha256": inputs.adapter.raw_sha256,
        "--authority-module-path": inputs.authority.path,
        "--authority-module-blob-oid": inputs.authority.blob_oid,
        "--authority-module-raw-sha256": inputs.authority.raw_sha256,
        "--collection-module-path": inputs.collection.path,
        "--collection-module-blob-oid": inputs.collection.blob_oid,
        "--collection-module-raw-sha256": inputs.collection.raw_sha256,
        "--audit-module-path": inputs.audit.path,
        "--audit-module-blob-oid": inputs.audit.blob_oid,
        "--audit-module-raw-sha256": inputs.audit.raw_sha256,
    }
    for flag, value in values.items():
        _set_flag(items, flag, value)
    owner_flag = "--bootstrap-owner-root-fd"
    if owner_flag in items:
        raise ValueError("launcher already owns FD")
    root_index = items.index("--bootstrap-project-root")
    items[root_index + 2:root_index + 2] = [owner_flag, "8"]
    parser = json.dumps(items, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    source = _replace_one(source, parser_literal, parser.decode("utf-8"), "parser literal")
    source = source.replace(old_root, inputs.formal_root)
    clean_pattern = r'CLEAN = ROOT \+ "/\.authority-root-materialization-[0-9a-f]+"'
    if len(re.findall(clean_pattern, source)) != 1:
        raise ValueError("launcher clean declaration")
    source = re.sub(
        clean_pattern,
        f'CLEAN = ROOT + "/.authority-root-materialization-{inputs.clean_suffix}"',
        source,
        count=1,
    )
    adapter_pattern = r'ADAPTER = \("[^\"]+",\n\s+"[0-9a-f]{40}"\)'
    if len(re.findall(adapter_pattern, source)) != 1:
        raise ValueError("launcher adapter declaration")
    source = re.sub(
        adapter_pattern,
        f'ADAPTER = ("{inputs.adapter.path}",\n           "{inputs.adapter.blob_oid}")',
        source,
        count=1,
    )
    owner_collision = "require_closed(GIT_TARGET_FD,PARENT_OWNER_FD,BOOTSTRAP_FD,CLEAN_OWNER_FD)"
    if source.count(owner_collision) > 1:
        raise ValueError("launcher owner collision guard")
    source = source.replace(owner_collision, "require_closed(GIT_TARGET_FD,PARENT_OWNER_FD,CLEAN_OWNER_FD)", 1)
    route_admin = "adfd = os.open(admin, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC); ads = os.fstat(adfd)"
    route_config = "cfd, cs, raw = nofollow(admin + \"/config\")"
    if source.count(route_admin) > 1 or source.count(route_config) > 1:
        raise ValueError("launcher route fd allocation")
    if route_admin in source:
        source = source.replace(
            route_admin,
            "adfd0 = os.open(admin, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC); adfd = fcntl.fcntl(adfd0, fcntl.F_DUPFD_CLOEXEC, 10); os.close(adfd0); ads = os.fstat(adfd)",
            1,
        )
    if route_config in source:
        source = source.replace(
            route_config,
            "cfd, cs, raw = nofollow(admin + \"/config\"); cfd0 = fcntl.fcntl(cfd, fcntl.F_DUPFD_CLOEXEC, 10); os.close(cfd); cfd = cfd0",
            1,
        )
    bootstrap = bootstrap_payload(adapter_source)
    bootstrap_argv = json.dumps(["--", *items], separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    contract = json.dumps({"bootstrap_argv_sha256": sha256(bootstrap_argv), "bootstrap_raw_sha256": sha256(bootstrap)},
                          sort_keys=True, separators=(",", ":")).encode("utf-8")
    source = _replace_guard(source, r'if len\(raw\)!=\d+ or digest\(raw\)!="[0-9a-f]{64}": fail\("bootstrap identity"\)',
                            f'if len(raw)!={len(bootstrap)} or digest(raw)!="{sha256(bootstrap)}": fail("bootstrap identity")', "bootstrap")
    source = _replace_guard(source, r'len\(RAW\[2\]\)!=\d+ or tuple\(digest\(x\) for x in RAW\)!=EXPECTED\[0\]\[2:\]\+EXPECTED\[1\]\[2:\]\+\("[0-9a-f]{64}",\): fail\("embedded authority"\)',
                            f'len(RAW[2])!={len(parser)} or tuple(digest(x) for x in RAW)!=EXPECTED[0][2:]+EXPECTED[1][2:]+("{sha256(parser)}",): fail("embedded authority")', "parser")
    source = _replace_guard(source, r'(\("\.authority-root\.bootstrap-contract\.json", 5, ")[0-9a-f]{64}("\))',
                            rf'\g<1>{sha256(contract)}\g<2>', "contract")
    ast.parse(source)
    return LauncherBytes(source.encode("utf-8"), parser, tuple(items), bootstrap, bootstrap_argv, contract)
