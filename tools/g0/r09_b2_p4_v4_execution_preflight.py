"""P4-v4 execution-preflight entry foundation; no execution is authorized here."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
from pathlib import Path


REQUEST_KEYS = {
    "schema_version", "entry", "source", "interpreter", "environment", "run", "candidates",
    "backends", "authorities", "execution_contract",
}
ENTRY_KEYS = {"tool_path", "root_revision", "git_blob_sha256", "current_sha256", "identity_sha256"}
ENTRY_TOOL_PATH = "tools/g0/r09_b2_p4_v4_execution_preflight.py"
SOURCE_KEYS = {"root", "root_revision", "gitlink", "entry_git_blob_sha256", "entry_current_sha256", "identity_sha256"}
_GIT_REVISION = re.compile(r"[0-9a-f]{40}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_EXECUTION_CONTRACT_ITEMS = (
    ("network", False),
    ("gpu", False),
    ("torch", False),
    ("model_data_checkpoint_io", False),
    ("one_shot", True),
    ("cleanup_retry_repair", False),
)


def read_execution_request(path: Path) -> bytes:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise ValueError("execution request requires O_NOFOLLOW")
    flags = os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(path, flags)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError("execution request must be a regular file")
        with os.fdopen(descriptor, "rb") as request_file:
            descriptor = -1
            return request_file.read()
    finally:
        if descriptor != -1:
            os.close(descriptor)


def load_execution_request(
    raw: bytes,
    _execution_contract_items: tuple[tuple[str, bool], ...] = _EXECUTION_CONTRACT_ITEMS,
) -> dict[str, object]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("execution request is not JSON") from exc
    canonical = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if not isinstance(value, dict) or raw != canonical:
        raise ValueError("execution request is not canonical JSON")
    if set(value) != REQUEST_KEYS or value.get("schema_version") != "r09_b2_p4_v4_execution_request_v1":
        raise ValueError("execution request schema differs")
    if not all(isinstance(value[key], dict) for key in REQUEST_KEYS - {"schema_version"}):
        raise ValueError("execution request section differs")
    if value["execution_contract"] != dict(_execution_contract_items):
        raise ValueError("execution request contract differs")
    validate_entry(value["entry"])
    validate_source(value["source"], value["entry"])
    return value


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    ).hexdigest()


def validate_entry(value: object) -> None:
    if not isinstance(value, dict) or set(value) != ENTRY_KEYS or not all(
        isinstance(item, str) for item in value.values()
    ):
        raise ValueError("execution request entry schema differs")
    if value["tool_path"] != ENTRY_TOOL_PATH:
        raise ValueError("execution request entry path differs")
    if _GIT_REVISION.fullmatch(value["root_revision"]) is None or any(
        _SHA256.fullmatch(value[key]) is None
        for key in ("git_blob_sha256", "current_sha256", "identity_sha256")
    ):
        raise ValueError("execution request entry digest differs")
    identity = {key: item for key, item in value.items() if key != "identity_sha256"}
    if value["identity_sha256"] != canonical_sha256(identity):
        raise ValueError("execution request entry identity differs")


def _git(root: Path, *args: str) -> bytes:
    try:
        return subprocess.run(("git", "-C", str(root), *args), check=True, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError("execution request source Git command differs") from exc


def _clean_git_root(root: Path) -> None:
    if root.is_symlink() or not root.is_dir() or _git(root, "rev-parse", "--show-toplevel").decode().strip() != str(root):
        raise ValueError("execution request source Git root differs")
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise ValueError("execution request source is not full-clean")


def validate_source(value: object, entry: dict[str, object]) -> None:
    if not isinstance(value, dict) or set(value) != SOURCE_KEYS or not all(isinstance(item, str) for item in value.values()):
        raise ValueError("execution request source schema differs")
    if (_GIT_REVISION.fullmatch(value["root_revision"]) is None or _GIT_REVISION.fullmatch(value["gitlink"]) is None
            or any(_SHA256.fullmatch(value[key]) is None for key in ("entry_git_blob_sha256", "entry_current_sha256", "identity_sha256"))):
        raise ValueError("execution request source digest differs")
    root = Path(value["root"])
    if not root.is_absolute() or root.is_symlink() or root.resolve(strict=True) != root:
        raise ValueError("execution request source root differs")
    identity = {key: item for key, item in value.items() if key != "identity_sha256"}
    if value["identity_sha256"] != canonical_sha256(identity):
        raise ValueError("execution request source identity differs")
    if any(value[key] != entry[entry_key] for key, entry_key in (("root_revision", "root_revision"), ("entry_git_blob_sha256", "git_blob_sha256"), ("entry_current_sha256", "current_sha256"))):
        raise ValueError("execution request source cross-binding differs")
    _clean_git_root(root)
    framework = root / "cosmos-framework"
    _clean_git_root(framework)
    if framework.is_symlink() or _git(root, "rev-parse", "HEAD").decode().strip() != value["root_revision"] or _git(root, "rev-parse", "--verify", f"{value['root_revision']}^{{commit}}").decode().strip() != value["root_revision"]:
        raise ValueError("execution request source checkout revision differs")
    tree = _git(root, "ls-tree", value["root_revision"], "cosmos-framework").decode().rstrip("\n").split("\t")
    if len(tree) != 2 or tree[1] != "cosmos-framework" or tree[0].split()[:2] != ["160000", "commit"] or tree[0].split()[2] != value["gitlink"] or _git(framework, "rev-parse", "HEAD").decode().strip() != value["gitlink"]:
        raise ValueError("execution request source Gitlink differs")
    entry_path = root / ENTRY_TOOL_PATH
    if entry_path.is_symlink() or not entry_path.is_file() or not stat.S_ISREG(entry_path.stat().st_mode):
        raise ValueError("execution request source entry path differs")
    _git(root, "ls-files", "--error-unmatch", "--", ENTRY_TOOL_PATH)
    blob = _git(root, "show", f"{value['root_revision']}:{ENTRY_TOOL_PATH}")
    if hashlib.sha256(blob).hexdigest() != value["entry_git_blob_sha256"] or hashlib.sha256(entry_path.read_bytes()).hexdigest() != value["entry_current_sha256"] or blob != entry_path.read_bytes() or value["entry_git_blob_sha256"] != value["entry_current_sha256"]:
        raise ValueError("execution request source entry bytes differ")


def request_sha256(raw: bytes) -> str:
    if not isinstance(raw, bytes):
        raise ValueError("execution request must be a regular file")
    return hashlib.sha256(raw).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--request-sha256", required=True)
    args = parser.parse_args(argv)
    raw = read_execution_request(args.request)
    if request_sha256(raw) != args.request_sha256:
        raise ValueError("execution request SHA256 differs")
    load_execution_request(raw)
    raise RuntimeError("P4-v4 execution requires a separately reviewed frozen execution request")


if __name__ == "__main__":
    main()
