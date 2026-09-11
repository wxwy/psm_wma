"""Fail-closed, root-owned Gitlink authority source audit (temporary-fixture use)."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
from typing import Any


GIT_EXECUTABLE = Path("/usr/bin/git")
SUBMODULE_PATH = "cosmos-framework"
PUBLICATION_PATH = "docs/build/PSM-WMA_root_gitlink_authority_publication_v1.json"
CHECK_NAMES = (
    "root_commit",
    "root_tree",
    "root_tree_record",
    "gitlink",
    "publication_blob",
    "publication_json",
    "canonical_model_config",
    "checkpoint_source_descriptor",
    "child_commit",
    "child_tree",
    "child_tree_record",
    "audit_record",
)
AUDIT_RECORD_KEYS = (
    "schema",
    "formal_root_revision",
    "root_tree_native_oid",
    "submodule_path",
    "child_git_revision",
    "child_tree_native_oid",
    "publication_path",
    "publication_blob_native_oid",
    "publication_blob_sha256",
    "verifier_schema",
    "canonical_model_config_sha256",
    "checkpoint_source_descriptor_sha256",
    "root_tree_record_sha256",
    "child_tree_record_sha256",
)
ENVIRONMENT = {
    "LC_ALL": "C",
    "LANG": "C",
    "PATH": "/usr/bin:/bin",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_NO_REPLACE_OBJECTS": "1",
    "GIT_OPTIONAL_LOCKS": "0",
}
WHITELIST = (
    "root cat-file -e {formal}^{commit}",
    "root rev-parse {formal}^{tree}",
    "root cat-file -t/-s {tree}",
    "root cat-file tree {tree}",
    "root ls-tree {tree} -- cosmos-framework",
    "root ls-tree {tree} -- publication",
    "root cat-file blob {publication_blob}",
    "child cat-file -e {gitlink}^{commit}",
    "child rev-parse {gitlink}^{tree}",
    "child cat-file -t/-s {tree}",
    "child cat-file tree {tree}",
)
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class AuditFailure(Exception):
    def __init__(self, reason: str, operational: bool = False) -> None:
        self.reason = reason
        self.operational = operational
        super().__init__(reason)


class AuditArgumentParser(argparse.ArgumentParser):
    def error(self, _: str) -> None:
        raise AuditFailure("ARGUMENTS", True)


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def exact_keys(value: object, keys: tuple[str, ...], reason: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != set(keys):
        raise AuditFailure(reason)
    return value


def lower_hex(value: object, length: int, reason: str) -> str:
    pattern = HEX40 if length == 40 else HEX64
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise AuditFailure(reason)
    return value


def non_bool_int(value: object, reason: str, positive: bool = False) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or (positive and value <= 0)
    ):
        raise AuditFailure(reason)
    return value


def finite_number(value: object, reason: str, positive: bool = False) -> float | int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AuditFailure(reason)
    if (
        value != value
        or value in (float("inf"), float("-inf"))
        or (positive and value <= 0)
    ):
        raise AuditFailure(reason)
    return value


def validate_config(value: object) -> tuple[dict[str, Any], str]:
    keys = (
        "schema",
        "local_memory_enabled",
        "local_memory_dim",
        "local_history_enabled",
        "local_history_backend",
        "local_history_evidence_dim",
        "local_history_state_enabled",
        "local_ttt_enabled",
        "enable_input_bias",
        "ttt_tbptt_steps",
        "ttt_inner_lr",
        "k_local",
        "local_evidence_feature_version",
        "local_fast_state_dtype",
        "local_runtime_resume_mode",
    )
    data = exact_keys(value, keys, "CONFIG_KEYS")
    if data["schema"] != "canonical_native_local_ttt_config_v2":
        raise AuditFailure("CONFIG_SCHEMA")
    for key in (
        "local_memory_enabled",
        "local_history_enabled",
        "local_history_state_enabled",
        "local_ttt_enabled",
        "enable_input_bias",
    ):
        if not isinstance(data[key], bool):
            raise AuditFailure("CONFIG_BOOL")
    if data["local_memory_dim"] != 32 or isinstance(data["local_memory_dim"], bool):
        raise AuditFailure("CONFIG_DIM")
    if data["local_history_backend"] != "ttt_fast_weight":
        raise AuditFailure("CONFIG_BACKEND")
    for key in ("local_history_evidence_dim", "ttt_tbptt_steps", "k_local"):
        non_bool_int(data[key], "CONFIG_INTEGER", True)
    finite_number(data["ttt_inner_lr"], "CONFIG_LR", True)
    fixed = {
        "local_evidence_feature_version": "causal_visual96_executed_action10_v1",
        "local_fast_state_dtype": "fp32",
        "local_runtime_resume_mode": "slow_only_no_mid_episode_resume",
    }
    if any(data[key] != expected for key, expected in fixed.items()):
        raise AuditFailure("CONFIG_FIXED_VALUE")
    if not (
        data["local_memory_enabled"]
        and data["local_history_enabled"]
        and not data["local_history_state_enabled"]
        and data["local_ttt_enabled"]
    ):
        raise AuditFailure("CONFIG_ACTIVE_MAPPING")
    return data, sha256(canonical_bytes(data))


def validate_descriptor(value: object) -> tuple[dict[str, Any], str]:
    keys = (
        "schema",
        "source_kind",
        "immutable_source_identifier",
        "source_manifest_sha256",
        "source_input_sha256",
    )
    data = exact_keys(value, keys, "SOURCE_KEYS")
    if (
        data["schema"] != "root_gitlink_checkpoint_source_descriptor_v1"
        or data["source_kind"] != "checkpoint_source_manifest_v1"
    ):
        raise AuditFailure("SOURCE_SCHEMA")
    for key in keys[2:]:
        lower_hex(data[key], 64, "SOURCE_DIGEST")
    return data, sha256(canonical_bytes(data))


def bootstrap_git() -> dict[str, Any]:
    base = {
        "schema": "root_gitlink_git_bootstrap_v1",
        "status": "FAIL",
        "reason": None,
        "git_executable": None,
        "git_executable_sha256": None,
        "git_version": None,
    }
    try:
        mode = GIT_EXECUTABLE.stat().st_mode
    except FileNotFoundError:
        base["reason"] = "GIT_MISSING"
        return base
    except OSError:
        base["reason"] = "GIT_UNREADABLE"
        return base
    if not stat.S_ISREG(mode) or not os.access(GIT_EXECUTABLE, os.X_OK):
        base["reason"] = "GIT_NOT_REGULAR_EXECUTABLE"
        return base
    try:
        executable_sha = sha256(GIT_EXECUTABLE.read_bytes())
    except OSError:
        base["reason"] = "GIT_UNREADABLE"
        return base
    try:
        result = subprocess.run(
            (str(GIT_EXECUTABLE), "--version"),
            env=ENVIRONMENT,
            shell=False,
            text=False,
            close_fds=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        version = result.stdout.decode("ascii")
        if (
            result.returncode
            or result.stderr
            or not re.fullmatch(r"git version [^\r\n]+\n", version)
        ):
            raise ValueError
    except (OSError, UnicodeDecodeError, ValueError):
        base["reason"] = "GIT_VERSION_INVALID"
        return base
    return {
        "schema": "root_gitlink_git_bootstrap_v1",
        "status": "READY",
        "reason": "READY",
        "git_executable": str(GIT_EXECUTABLE),
        "git_executable_sha256": executable_sha,
        "git_version": version[:-1],
    }


def command_identity(bootstrap: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "root_gitlink_git_command_identity_v1",
        "git_executable": bootstrap["git_executable"],
        "git_executable_sha256": bootstrap["git_executable_sha256"],
        "git_version": bootstrap["git_version"],
        "environment_sha256": sha256(canonical_bytes(ENVIRONMENT)),
        "command_whitelist_sha256": sha256(canonical_bytes(WHITELIST)),
    }


def run_git(
    root: Path | None, child_git_dir: Path | None, args: tuple[str, ...]
) -> bytes:
    command = [str(GIT_EXECUTABLE)]
    if root is not None:
        command.extend(("-C", str(root)))
    if child_git_dir is not None:
        command.extend(("--git-dir", str(child_git_dir)))
    command.extend(args)
    try:
        result = subprocess.run(
            command,
            env=ENVIRONMENT,
            shell=False,
            text=False,
            close_fds=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        raise AuditFailure("GIT_EXECUTION", True) from exc
    if result.returncode or result.stderr:
        raise AuditFailure("GIT_COMMAND_FAILURE")
    return result.stdout


def path_arg(value: Path, label: str, *, must_exist: bool = True) -> Path:
    if not value.is_absolute():
        raise AuditFailure(f"{label}_PATH", True)
    for ancestor in (value, *value.parents):
        if ancestor.is_symlink():
            raise AuditFailure(f"{label}_PATH", True)
    try:
        return value.resolve(strict=must_exist)
    except OSError as exc:
        raise AuditFailure(f"{label}_PATH", True) from exc


def tree_record(
    oid: str, raw: bytes, object_type: bytes, object_size: bytes
) -> tuple[dict[str, Any], str]:
    if object_type != b"tree\n" or object_size != f"{len(raw)}\n".encode():
        raise AuditFailure("TREE_OBJECT")
    record = {
        "schema": "root_gitlink_tree_record_v1",
        "native_tree_oid": oid,
        "tree_content_sha256": sha256(raw),
        "object_type": "tree",
        "byte_length": len(raw),
    }
    return record, sha256(canonical_bytes(record))


def parse_ls_tree(
    raw: bytes, expected_mode: bytes, expected_type: bytes, expected_path: bytes
) -> str:
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n") or b"\r" in raw:
        raise AuditFailure("TREE_ENTRY_FORMAT")
    rows = raw.splitlines()
    if len(rows) != 1:
        raise AuditFailure("TREE_ENTRY_COUNT")
    try:
        left, path = rows[0].split(b"\t", 1)
        mode, kind, oid = left.split(b" ")
    except ValueError as exc:
        raise AuditFailure("TREE_ENTRY_FORMAT") from exc
    try:
        oid_text = oid.decode("ascii")
    except UnicodeDecodeError as exc:
        raise AuditFailure("TREE_ENTRY_MISMATCH") from exc
    if (
        mode != expected_mode
        or kind != expected_type
        or path != expected_path
        or HEX40.fullmatch(oid_text) is None
    ):
        raise AuditFailure("TREE_ENTRY_MISMATCH")
    return oid_text


def parse_revision_output(raw: bytes, reason: str) -> str:
    if len(raw) != 41 or raw[-1:] != b"\n":
        raise AuditFailure(reason)
    try:
        oid = raw[:-1].decode("ascii")
    except UnicodeDecodeError as exc:
        raise AuditFailure(reason) from exc
    return lower_hex(oid, 40, reason)


def validate_publication(raw: bytes) -> dict[str, Any]:
    def reject_nonfinite(_: str) -> None:
        raise AuditFailure("PUBLICATION_NONFINITE")

    try:
        data = json.loads(raw, parse_constant=reject_nonfinite)
    except AuditFailure:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuditFailure("PUBLICATION_JSON") from exc
    try:
        canonical = canonical_bytes(data)
    except (TypeError, ValueError) as exc:
        raise AuditFailure("PUBLICATION_NONFINITE") from exc
    if canonical != raw:
        raise AuditFailure("PUBLICATION_NOT_CANONICAL")
    data = exact_keys(
        data,
        ("schema", "canonical_model_config", "checkpoint_source_descriptor"),
        "PUBLICATION_KEYS",
    )
    if data["schema"] != "root_gitlink_authority_publication_v1":
        raise AuditFailure("PUBLICATION_SCHEMA")
    return data


def checks_template() -> list[dict[str, Any]]:
    return [
        {"name": name, "status": "SKIPPED", "reason": "NOT_REACHED", "observed": {}}
        for name in CHECK_NAMES
    ]


def mark(checks: list[dict[str, Any]], name: str, observed: dict[str, Any]) -> None:
    row = checks[CHECK_NAMES.index(name)]
    row.update(status="PASS", reason="OK", observed=observed)


def guarded(checks: list[dict[str, Any]], name: str, operation: Any) -> Any:
    try:
        return operation()
    except AuditFailure as exc:
        row = checks[CHECK_NAMES.index(name)]
        row.update(status="FAIL", reason=exc.reason, observed={})
        setattr(exc, "checks", checks)
        raise


def audit(
    repo_root: Path,
    formal: str,
    child_git_dir: Path,
    identity: dict[str, Any],
    checks: list[dict[str, Any]],
) -> dict[str, Any]:
    root = guarded(
        checks,
        "root_commit",
        lambda: (lower_hex(formal, 40, "FORMAL_REVISION"), path_arg(repo_root, "ROOT"))[
            1
        ],
    )
    child = guarded(
        checks, "root_commit", lambda: path_arg(child_git_dir, "CHILD_GIT_DIR")
    )
    guarded(
        checks,
        "root_commit",
        lambda: (
            child.is_dir()
            or (_ for _ in ()).throw(AuditFailure("CHILD_GIT_DIR_PATH", True))
        ),
    )
    if (
        guarded(
            checks,
            "root_commit",
            lambda: run_git(root, None, ("cat-file", "-e", f"{formal}^{{commit}}")),
        )
        != b""
    ):
        exc = AuditFailure("ROOT_COMMIT_OUTPUT")
        checks[0].update(status="FAIL", reason=exc.reason, observed={})
        setattr(exc, "checks", checks)
        raise exc
    mark(checks, "root_commit", {"oid": formal, "type": "commit"})
    root_tree = (
        guarded(
            checks,
            "root_tree",
            lambda: parse_revision_output(
                run_git(root, None, ("rev-parse", f"{formal}^{{tree}}")),
                "ROOT_TREE_OUTPUT",
            ),
        )
    )
    mark(checks, "root_tree", {"oid": root_tree, "type": "tree"})
    root_raw = guarded(
        checks,
        "root_tree_record",
        lambda: run_git(root, None, ("cat-file", "tree", root_tree)),
    )
    root_record, root_record_sha = guarded(
        checks,
        "root_tree_record",
        lambda: tree_record(
            root_tree,
            root_raw,
            run_git(root, None, ("cat-file", "-t", root_tree)),
            run_git(root, None, ("cat-file", "-s", root_tree)),
        ),
    )
    mark(
        checks,
        "root_tree_record",
        {"sha256": root_record_sha, "byte_length": len(root_raw)},
    )
    gitlink = guarded(
        checks,
        "gitlink",
        lambda: parse_ls_tree(
            run_git(root, None, ("ls-tree", root_tree, "--", SUBMODULE_PATH)),
            b"160000",
            b"commit",
            SUBMODULE_PATH.encode(),
        ),
    )
    mark(checks, "gitlink", {"oid": gitlink, "path": SUBMODULE_PATH})
    blob = guarded(
        checks,
        "publication_blob",
        lambda: parse_ls_tree(
            run_git(root, None, ("ls-tree", root_tree, "--", PUBLICATION_PATH)),
            b"100644",
            b"blob",
            PUBLICATION_PATH.encode(),
        ),
    )
    publication_raw = guarded(
        checks,
        "publication_blob",
        lambda: run_git(root, None, ("cat-file", "blob", blob)),
    )
    mark(
        checks,
        "publication_blob",
        {
            "oid": blob,
            "sha256": sha256(publication_raw),
            "byte_length": len(publication_raw),
        },
    )
    publication = guarded(
        checks, "publication_json", lambda: validate_publication(publication_raw)
    )
    mark(checks, "publication_json", {"sha256": sha256(publication_raw)})
    _, config_sha = guarded(
        checks,
        "canonical_model_config",
        lambda: validate_config(publication["canonical_model_config"]),
    )
    mark(checks, "canonical_model_config", {"sha256": config_sha})
    _, source_sha = guarded(
        checks,
        "checkpoint_source_descriptor",
        lambda: validate_descriptor(publication["checkpoint_source_descriptor"]),
    )
    mark(checks, "checkpoint_source_descriptor", {"sha256": source_sha})
    if (
        guarded(
            checks,
            "child_commit",
            lambda: run_git(None, child, ("cat-file", "-e", f"{gitlink}^{{commit}}")),
        )
        != b""
    ):
        exc = AuditFailure("CHILD_COMMIT_OUTPUT")
        checks[CHECK_NAMES.index("child_commit")].update(
            status="FAIL", reason=exc.reason, observed={}
        )
        setattr(exc, "checks", checks)
        raise exc
    mark(checks, "child_commit", {"oid": gitlink, "type": "commit"})
    child_tree = (
        guarded(
            checks,
            "child_tree",
            lambda: parse_revision_output(
                run_git(None, child, ("rev-parse", f"{gitlink}^{{tree}}")),
                "CHILD_TREE_OUTPUT",
            ),
        )
    )
    mark(checks, "child_tree", {"oid": child_tree, "type": "tree"})
    child_raw = guarded(
        checks,
        "child_tree_record",
        lambda: run_git(None, child, ("cat-file", "tree", child_tree)),
    )
    child_record, child_record_sha = guarded(
        checks,
        "child_tree_record",
        lambda: tree_record(
            child_tree,
            child_raw,
            run_git(None, child, ("cat-file", "-t", child_tree)),
            run_git(None, child, ("cat-file", "-s", child_tree)),
        ),
    )
    mark(
        checks,
        "child_tree_record",
        {"sha256": child_record_sha, "byte_length": len(child_raw)},
    )
    record = {
        "schema": "root_gitlink_source_audit_record_v1",
        "formal_root_revision": formal,
        "root_tree_native_oid": root_tree,
        "submodule_path": SUBMODULE_PATH,
        "child_git_revision": gitlink,
        "child_tree_native_oid": child_tree,
        "publication_path": PUBLICATION_PATH,
        "publication_blob_native_oid": blob,
        "publication_blob_sha256": sha256(publication_raw),
        "verifier_schema": "root_gitlink_authority_publication_verifier_v1",
        "canonical_model_config_sha256": config_sha,
        "checkpoint_source_descriptor_sha256": source_sha,
        "root_tree_record_sha256": root_record_sha,
        "child_tree_record_sha256": child_record_sha,
    }
    guarded(
        checks,
        "audit_record",
        lambda: exact_keys(record, AUDIT_RECORD_KEYS, "AUDIT_RECORD_KEYS"),
    )
    record_sha = guarded(
        checks, "audit_record", lambda: sha256(canonical_bytes(record))
    )
    mark(checks, "audit_record", {"sha256": record_sha})
    return {
        "schema": "root_gitlink_source_audit_evidence_v1",
        "status": "PASS",
        "command_identity": identity,
        "checks": checks,
        "audit_record": record,
        "audit_record_sha256": record_sha,
        "tool_source_sha256": sha256(Path(__file__).read_bytes()),
    }


def failure(
    bootstrap: dict[str, Any],
    identity: dict[str, Any] | None,
    checks: list[dict[str, Any]],
    exit_code: int,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema": "root_gitlink_source_audit_failure_v1",
        "status": "FAIL",
        "exit_code": exit_code,
        "command_identity": identity,
        "checks": checks,
        "tool_source_sha256": sha256(Path(__file__).read_bytes()),
    }
    if bootstrap["status"] == "FAIL":
        result["bootstrap"] = bootstrap
    return result


def write_atomic(output: Path, payload: dict[str, Any]) -> None:
    temporary: Path | None = None
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            dir=output.parent, prefix=f".{output.name}.", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(canonical_bytes(payload))
        os.replace(temporary, output)
    except OSError as exc:
        raise AuditFailure("OUTPUT_WRITE", True) from exc
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


def main(argv: list[str] | None = None) -> int:
    parser = AuditArgumentParser(add_help=False)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--formal-root-revision", required=True)
    parser.add_argument("--child-git-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    checks = checks_template()
    bootstrap = bootstrap_git()
    identity = command_identity(bootstrap) if bootstrap["status"] == "READY" else None
    try:
        args = parser.parse_args(argv)
    except AuditFailure:
        print(canonical_bytes(failure(bootstrap, identity, checks, 3)).decode())
        return 3
    if bootstrap["status"] != "READY":
        print(canonical_bytes(failure(bootstrap, None, checks, 3)).decode())
        return 3
    try:
        output = path_arg(args.output, "OUTPUT", must_exist=False)
        evidence = audit(
            args.repo_root,
            args.formal_root_revision,
            args.child_git_dir,
            identity,
            checks,
        )
        write_atomic(output, evidence)
        print(
            canonical_bytes(
                {
                    "schema": "root_gitlink_source_audit_summary_v1",
                    "status": "PASS",
                    "audit_record_sha256": evidence["audit_record_sha256"],
                }
            ).decode()
        )
        return 0
    except AuditFailure as exc:
        code = 3 if exc.operational else 2
        print(
            canonical_bytes(
                failure(bootstrap, identity, getattr(exc, "checks", checks), code)
            ).decode()
        )
        return code


if __name__ == "__main__":
    raise SystemExit(main())
