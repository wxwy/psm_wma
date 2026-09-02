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

from tools.g0.r09_b2_interpreter_provenance import (
    ProvenanceError,
    is_verified_loader_argv,
    lexical_interpreter,
    parse_elf_dynamic_raw,
    verified_loader_argv,
)


REQUEST_KEYS = {
    "schema_version", "entry", "source", "interpreter", "environment", "run", "candidates",
    "backends", "authorities", "execution_contract",
}
ENTRY_KEYS = {"tool_path", "root_revision", "git_blob_sha256", "current_sha256", "identity_sha256"}
ENTRY_TOOL_PATH = "tools/g0/r09_b2_p4_v4_execution_preflight.py"
SOURCE_KEYS = {"root", "root_revision", "gitlink", "entry_git_blob_sha256", "entry_current_sha256", "identity_sha256"}
INTERPRETER_KEYS = {"lexical_interpreter", "host_git", "loader_argv", "identity_sha256"}
HOST_GIT_KEYS = {"path", "elf_sha256", "closure_sha256"}
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


def _read_regular_nofollow(path: Path, error: str) -> bytes:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise ValueError(error)
    flags = os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ValueError(error) from exc
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError(error)
        with os.fdopen(descriptor, "rb") as request_file:
            descriptor = -1
            return request_file.read()
    finally:
        if descriptor != -1:
            os.close(descriptor)


def _read_strict_regular_nofollow(path: Path, error: str, *, executable: bool = True) -> tuple[Path, bytes]:
    if not path.is_absolute() or path.is_symlink() or path.resolve(strict=True) != path:
        raise ValueError(error)
    raw = _read_regular_nofollow(path, error)
    if executable and not os.access(path, os.X_OK):
        raise ValueError(error)
    return path, raw


def _read_canonical_regular_nofollow(path: Path, error: str) -> tuple[Path, bytes]:
    try:
        canonical = path.resolve(strict=True)
    except OSError as exc:
        raise ValueError(error) from exc
    if canonical.is_symlink() or not canonical.is_absolute():
        raise ValueError(error)
    return canonical, _read_regular_nofollow(canonical, error)


def read_execution_request(path: Path) -> bytes:
    return _read_regular_nofollow(path, "execution request must be a regular file")


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
    validate_interpreter(value["interpreter"], value["source"])
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
    _git(root, "ls-files", "--error-unmatch", "--", ENTRY_TOOL_PATH)
    blob = _git(root, "show", f"{value['root_revision']}:{ENTRY_TOOL_PATH}")
    current_raw = _read_regular_nofollow(entry_path, "execution request source entry path differs")
    if hashlib.sha256(blob).hexdigest() != value["entry_git_blob_sha256"] or hashlib.sha256(current_raw).hexdigest() != value["entry_current_sha256"] or blob != current_raw or value["entry_git_blob_sha256"] != value["entry_current_sha256"]:
        raise ValueError("execution request source entry bytes differ")


def _library_search_paths(owner: Path, metadata: dict[str, object]) -> list[Path]:
    expanded: list[Path] = []
    for item in [*metadata["rpath"], *metadata["runpath"]]:
        if not isinstance(item, str):
            raise ValueError("execution request host Git ELF search path differs")
        for token in item.split(":"):
            candidate = token.replace("${ORIGIN}", str(owner.parent)).replace("$ORIGIN", str(owner.parent))
            if "$" in candidate or not candidate:
                raise ValueError("execution request host Git ELF search path differs")
            expanded.append(Path(candidate))
    defaults = (Path("/lib"), Path("/usr/lib"), Path("/lib64"), Path("/usr/lib64"))
    for prefix in defaults:
        if prefix.is_dir():
            expanded.append(prefix)
            expanded.extend(sorted(item for item in prefix.glob("*-linux-gnu") if item.is_dir()))
    return expanded


def _resolve_needed(owner: Path, metadata: dict[str, object], name: str) -> Path:
    if "/" in name:
        candidate = Path(name)
        if not candidate.is_absolute():
            raise ValueError("execution request host Git ELF dependency differs")
        return candidate
    candidates = [directory / name for directory in _library_search_paths(owner, metadata)]
    found = {str(candidate.resolve()): candidate for candidate in candidates if candidate.exists()}
    if len(found) != 1:
        raise ValueError("execution request host Git ELF dependency differs")
    return next(iter(found.values()))


def _host_git_closure(path: Path, raw: bytes) -> str:
    pending = [(path, raw)]
    objects: dict[str, str] = {}
    while pending:
        current, current_raw = pending.pop()
        canonical, current_raw = _read_strict_regular_nofollow(
            current, "execution request host Git object differs", executable=current == path,
        )
        if str(canonical) in objects:
            if objects[str(canonical)] != hashlib.sha256(current_raw).hexdigest():
                raise ValueError("execution request host Git object differs")
            continue
        try:
            metadata = parse_elf_dynamic_raw(canonical, current_raw)
        except ProvenanceError as exc:
            raise ValueError("execution request host Git ELF differs") from exc
        objects[str(canonical)] = str(metadata["sha256"])
        dependencies = list(metadata["dt_needed"])
        interpreter = metadata["pt_interp"]
        if interpreter is not None:
            dependencies.append(interpreter)
        for dependency in dependencies:
            if not isinstance(dependency, str):
                raise ValueError("execution request host Git ELF dependency differs")
            dependency_path = _resolve_needed(canonical, metadata, dependency)
            dependency_path, dependency_raw = _read_canonical_regular_nofollow(dependency_path, "execution request host Git object differs")
            pending.append((dependency_path, dependency_raw))
    return canonical_sha256({"objects": [{"path": name, "sha256": digest} for name, digest in sorted(objects.items())]})


def validate_interpreter(value: object, source: dict[str, object]) -> None:
    if not isinstance(value, dict) or set(value) != INTERPRETER_KEYS:
        raise ValueError("execution request interpreter schema differs")
    lexical, host_git, argv, identity_sha256 = (value["lexical_interpreter"], value["host_git"], value["loader_argv"], value["identity_sha256"])
    if not isinstance(lexical, dict) or not isinstance(host_git, dict) or not isinstance(argv, list) or not isinstance(identity_sha256, str):
        raise ValueError("execution request interpreter schema differs")
    if set(host_git) != HOST_GIT_KEYS or not all(isinstance(host_git[key], str) for key in HOST_GIT_KEYS):
        raise ValueError("execution request host Git schema differs")
    identity = {key: item for key, item in value.items() if key != "identity_sha256"}
    if _SHA256.fullmatch(identity_sha256) is None or identity_sha256 != canonical_sha256(identity):
        raise ValueError("execution request interpreter identity differs")
    try:
        if lexical_interpreter(Path(lexical.get("path", ""))) != lexical:
            raise ValueError("execution request lexical interpreter differs")
    except (OSError, ProvenanceError, ValueError) as exc:
        raise ValueError("execution request lexical interpreter differs") from exc
    git_path, git_raw = _read_strict_regular_nofollow(Path(host_git["path"]), "execution request host Git path differs")
    if (_SHA256.fullmatch(host_git["elf_sha256"]) is None or _SHA256.fullmatch(host_git["closure_sha256"]) is None
            or hashlib.sha256(git_raw).hexdigest() != host_git["elf_sha256"]
            or _host_git_closure(git_path, git_raw) != host_git["closure_sha256"]):
        raise ValueError("execution request host Git identity differs")
    root = Path(source["root"])
    if not is_verified_loader_argv(argv) or Path(argv[8]) != root:
        raise ValueError("execution request loader argv differs")
    try:
        expected = verified_loader_argv(lexical, Path(argv[6]), argv[7], root, argv[9], argv[10])
    except (OSError, ProvenanceError, ValueError) as exc:
        raise ValueError("execution request loader argv differs") from exc
    if argv != expected:
        raise ValueError("execution request loader argv differs")


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
