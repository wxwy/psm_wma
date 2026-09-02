"""P4-v4 execution-preflight entry foundation; no execution is authorized here."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
import re
import stat
import weakref
import subprocess
from pathlib import Path

from tools.g0.r09_b2_interpreter_provenance import (
    ProvenanceError,
    is_verified_loader_argv,
    lexical_interpreter,
    parse_elf_dynamic_raw,
    verified_loader_argv,
)
from tools.g0.export_r09_b2_p5_resolved_config import (
    P5_FORBIDDEN_ENVIRONMENT,
    P5_P3_BACKEND_ENVIRONMENT,
)
from tools.g0.verify_r09_b2_p4_d005 import (
    RANK_ENV,
    REQUIRED_ENV,
    SANITIZED_ENV,
    verify_pair as verify_d005_pair,
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
ENVIRONMENT_KEYS = {"effective_environment", "native_loader_environment", "d005_projection", "identity_sha256"}
ENVIRONMENT_OBJECT_KEYS = {"set", "unset", "inherit_allowlist", "sha256"}
D005_PROJECTION_KEYS = {"backend", "d005_sha256", "input_set_sha256", "excluded_keys", "projected_set_sha256", "sha256"}
D005_EXCLUDED_ENVIRONMENT_KEYS = ["IMAGINAIRE_OUTPUT_ROOT", "PYTHONPATH"]
AUTHORITIES_KEYS = {"d005_pair", "identity_sha256"}
AUTHORITIES_PAIR_KEYS = {"model", "recurrent", "ttt_fast_weight", "verification", "historical_source", "historical_verifier", "identity_sha256"}
RUN_KEYS = {"recurrent", "ttt_fast_weight"}
RUN_ITEM_KEYS = {"identity", "run_token", "roster_sha256"}
RUN_IDENTITY_KEYS = {"root", "resolved_root", "kind", "identity_sha256"}
CANDIDATES_KEYS = {"root", "attempt_id", "recurrent", "ttt_fast_weight", "identity_sha256"}
CANDIDATE_ROOT_KEYS = RUN_IDENTITY_KEYS
CANDIDATE_ITEM_KEYS = {"backend", "candidate_root", "run", "identity_sha256"}
LOCK_AUTHORITY_KEYS = {
    "schema_version", "source_root", "source_commit", "source_tree_oid", "gitlink",
    "spec_path", "spec_git_blob_sha256", "spec_current_sha256", "spec_raw_sha256",
    "output_parent", "output_basename",
}
LOCK_SPEC_KEYS = {
    "schema_version", "entry", "source", "interpreter", "environment", "authorities",
    "backends", "execution_contract", "planned_run", "planned_candidates",
    "payload_manifest", "lock_spec_sha256",
}
PLANNED_RUN_ITEM_KEYS = {"identity", "run_token", "identity_sha256"}
PLANNED_CANDIDATE_ITEM_KEYS = {
    "backend", "candidate_root", "run_identity", "run_token", "identity_sha256",
}
PLANNED_COMMITMENT_KEYS = {
    "schema_version", "entry", "source", "interpreter", "environment", "authorities",
    "backends", "execution_contract", "planned", "commitment_sha256",
}
PLANNED_KEYS = {"root", "attempt_id", "recurrent", "ttt_fast_weight", "identity_sha256"}
STAGING_PROJECTION_KEYS = {"entries", "projection_sha256"}
BACKENDS_KEYS = {"recurrent", "ttt_fast_weight", "identity_sha256"}
BACKEND_ITEM_KEYS = {"backend", "p3_contract", "identity_sha256"}
P3_CONTRACT_KEYS = {"artifact_sha256", "verifier_sha256", "backend_contract", "identity_sha256"}
P3_CORE_KEYS = P3_CONTRACT_KEYS - {"identity_sha256"}
BACKEND_CONTRACT_KEYS = {"selector_keys", "optimizer_membership_sha256"}
_HISTORICAL_REVISION = "ddb4e0eae97fb545d5239c1ddb6d4387170f3780"
_HISTORICAL_GITLINK = "21d064f2b7c7aeeb67cfee50ac8d6722a944eddb"
_HISTORICAL_ARTIFACTS = {
    "recurrent": ("artifacts/g0/r09/b2/p4_launch_d005/recurrent.json", "2d04c5040c5836249bcab78e7904c2cf8a475c4fcf5925942ebb496985cd3190"),
    "ttt_fast_weight": ("artifacts/g0/r09/b2/p4_launch_d005/ttt_fast_weight.json", "8890bbec61a808d5964657806cf01166c893ff66abc2fdf64ea3cd201a03274e"),
    "verification": ("artifacts/g0/r09/b2/p4_launch_d005/verification.json", "8618488f9c8cbbcdda2ea9d513f1f76a0154798fe386ce19dcbeac78fcff4080"),
}
_HISTORICAL_VERIFIER = ("tools/g0/verify_r09_b2_p4_d005.py", "2c94f28a7779f7e74a2798124a0d85e57bafa8aab739b6072ef6790a91c9a4e6")
P3_SNAPSHOT_AUTHORITY = {
    "historical_d005_revision": _HISTORICAL_REVISION,
    "historical_d005_verifier_blob_sha256": _HISTORICAL_VERIFIER[1],
    "recurrent_d005_sha256": _HISTORICAL_ARTIFACTS["recurrent"][1],
    "ttt_fast_weight_d005_sha256": _HISTORICAL_ARTIFACTS["ttt_fast_weight"][1],
    "p3_artifact_sha256": "5dd5253cabaa5efa54f3ddc8891f632e3b05e515bf91c8055108e037f69b684d",
    "p3_verifier_sha256": "e9700cd63e9626ce88969b2d21682c186af7dfe0c7489f88795de1301d5b64f8",
}
P3_CORE_SNAPSHOTS = {
    "recurrent": {
        "artifact_sha256": P3_SNAPSHOT_AUTHORITY["p3_artifact_sha256"],
        "verifier_sha256": P3_SNAPSHOT_AUTHORITY["p3_verifier_sha256"],
        "backend_contract": {
            "selector_keys": ["moe_gen", "time_embedder", "vae2llm", "llm2vae", "action2llm", "llm2action", "action_modality_embed", "local_memory2llm", "local_memory_modality_embed", "local_history_runtime"],
            "optimizer_membership_sha256": "31f5e455485b2c471c47da2d2c1819214372967ad1c76311e79bfe7865ec15fd",
        },
    },
    "ttt_fast_weight": {
        "artifact_sha256": P3_SNAPSHOT_AUTHORITY["p3_artifact_sha256"],
        "verifier_sha256": P3_SNAPSHOT_AUTHORITY["p3_verifier_sha256"],
        "backend_contract": {
            "selector_keys": ["local_history_runtime.encoder", "local_memory2llm", "local_memory_modality_embed"],
            "optimizer_membership_sha256": "379abd364d8a741adeafca441736c034fc3d93250d5ca8685630d18872867404",
        },
    },
}
_VERIFICATION_BACKEND_KEYS = {"argv", "budget", "command_digest", "cwd", "env_assets_bound", "environment", "inputs", "non_executable", "outputs", "record_digest", "schema", "source"}
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
_BACKEND_ORDER = ("recurrent", "ttt_fast_weight")
AUTHORIZED_P4_V4_LOCK_SPEC: dict[str, str] | None = None


class _AdmittedRequest:
    """Opaque, one-shot capability issued only by full request admission."""

    __slots__ = ("raw", "request_sha256", "_consumed", "_locked", "__weakref__")

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("P4-v4 admitted request is factory-only")

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_locked", False):
            raise AttributeError("P4-v4 admitted request is immutable")
        object.__setattr__(self, name, value)


@dataclass(frozen=True, slots=True)
class ReservationResult:
    status: str
    created_paths: tuple[Path, ...]


class ReservationPoisonedError(RuntimeError):
    def __init__(self, created_paths: tuple[Path, ...], failed_path: Path, cause: OSError):
        super().__init__(f"P4-v4 reservation poisoned at {failed_path}")
        self.created_paths, self.failed_path, self.cause = created_paths, failed_path, cause


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
    interpreter = value["interpreter"]
    if not isinstance(interpreter, dict):
        raise ValueError("execution request interpreter schema differs")
    git_path = validate_host_git(interpreter.get("host_git"))
    validate_source(value["source"], value["entry"], git_path)
    validate_interpreter(interpreter, value["source"], git_path)
    validate_run_pair(value["run"], value["source"])
    validate_candidates(value["candidates"], value["source"], value["run"])
    validate_backends(value["backends"])
    source_root = Path(value["source"]["root"])
    validate_authorities_pair(value["authorities"], value, source_root, git_path)
    return value


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    ).hexdigest()


def _p5_canonical_sha256(value: object) -> str:
    """Use the frozen P5 JSON spelling only for the planned v2 projection."""
    return hashlib.sha256(
        (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
    ).hexdigest()


def _open_absolute_directory_chain(value: object, error: str) -> int:
    if not isinstance(value, str) or not value or not os.path.isabs(value) or value.startswith("//"):
        raise ValueError(error)
    path = Path(value)
    if os.path.normpath(value) != value or any(part in {"", ".", ".."} for part in path.parts[1:]):
        raise ValueError(error)
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(path.anchor, flags)
    except OSError as exc:
        raise ValueError(error) from exc
    try:
        for component in path.parts[1:]:
            child = os.open(component, flags, dir_fd=descriptor)
            try:
                if not stat.S_ISDIR(os.fstat(child).st_mode):
                    raise ValueError(error)
            except BaseException:
                os.close(child)
                raise
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _lock_relative_components(value: object, error: str) -> tuple[str, ...]:
    if not isinstance(value, str) or not value or os.path.isabs(value) or "//" in value:
        raise ValueError(error)
    parts = tuple(value.split("/"))
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError(error)
    return parts


def _read_lock_spec_at(source_fd: int, relative: object) -> bytes:
    parts = _lock_relative_components(relative, "P4-v4 lock spec path differs")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    parent_fd = os.dup(source_fd)
    try:
        for component in parts[:-1]:
            child = os.open(component, flags, dir_fd=parent_fd)
            try:
                if not stat.S_ISDIR(os.fstat(child).st_mode):
                    raise ValueError("P4-v4 lock spec path differs")
            except BaseException:
                os.close(child)
                raise
            os.close(parent_fd)
            parent_fd = child
        descriptor = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0), dir_fd=parent_fd)
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise ValueError("P4-v4 lock spec must be a regular file")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    return b"".join(chunks)
                chunks.append(chunk)
        finally:
            os.close(descriptor)
    except OSError as exc:
        raise ValueError("P4-v4 lock spec path differs") from exc
    finally:
        os.close(parent_fd)


def _identity_exact(value: object, keys: set[str], error: str, *, key: str = "identity_sha256") -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys or not isinstance(value.get(key), str):
        raise ValueError(error)
    if value[key] != canonical_sha256({name: item for name, item in value.items() if name != key}):
        raise ValueError(error)
    return value


def _validate_payload_manifest(value: object) -> dict[str, object]:
    manifest = _identity_exact(value, {"entries", "sha256"}, "P4-v4 lock payload manifest differs", key="sha256")
    entries = manifest["entries"]
    if not isinstance(entries, list) or not entries:
        raise ValueError("P4-v4 lock payload manifest differs")
    seen: set[str] = set()
    for item in entries:
        if (not isinstance(item, dict) or set(item) != {"path", "type", "sha256"}
                or not isinstance(item["path"], str) or not item["path"]
                or item["path"].startswith("/") or "//" in item["path"]
                or any(part in {"", ".", ".."} for part in item["path"].split("/"))
                or item["type"] != "regular"
                or not isinstance(item["sha256"], str) or _SHA256.fullmatch(item["sha256"]) is None
                or item["path"] in seen):
            raise ValueError("P4-v4 lock payload manifest differs")
        seen.add(item["path"])
    if [item["path"] for item in entries] != sorted(seen):
        raise ValueError("P4-v4 lock payload manifest order differs")
    return manifest


def _planned_projection(manifest: dict[str, object], token: str) -> dict[str, object]:
    entries = [
        {"path": "import_staging", "type": "directory", "mode": "0555", "sha256": ""},
        {"path": f"import_staging/{token}", "type": "directory", "mode": "0555", "sha256": ""},
    ]
    entries.extend({"path": item["path"], "type": "regular", "mode": "0444", "sha256": item["sha256"]} for item in manifest["entries"])
    entries.sort(key=lambda item: item["path"])
    return {"entries": entries, "projection_sha256": _p5_canonical_sha256({"entries": entries})}


def build_planned_roster_commitment(raw: bytes) -> dict[str, object]:
    """Validate a planned-only lock spec and derive its non-executable commitment."""
    try:
        spec = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("P4-v4 lock spec is not JSON") from exc
    if (not isinstance(spec, dict) or raw != (json.dumps(spec, sort_keys=True, separators=(",", ":")) + "\n").encode()
            or set(spec) != LOCK_SPEC_KEYS or spec.get("schema_version") != "r09_b2_p4_v4_lock_spec_v3"):
        raise ValueError("P4-v4 lock spec schema differs")
    _identity_exact(spec, LOCK_SPEC_KEYS, "P4-v4 lock spec identity differs", key="lock_spec_sha256")
    if any(key in spec for key in ("run", "candidates", "roster_sha256")):
        raise ValueError("P4-v4 lock spec final request field differs")
    validate_entry(spec["entry"])
    git_path = validate_host_git(spec["interpreter"].get("host_git") if isinstance(spec["interpreter"], dict) else None)
    validate_source(spec["source"], spec["entry"], git_path)
    validate_interpreter(spec["interpreter"], spec["source"], git_path)
    validate_backends(spec["backends"])
    validate_authorities_pair(spec["authorities"], spec, Path(spec["source"]["root"]), git_path)
    planned_run = spec["planned_run"]
    candidates = spec["planned_candidates"]
    if not isinstance(planned_run, dict) or set(planned_run) != RUN_KEYS:
        raise ValueError("P4-v4 lock planned run schema differs")
    if not isinstance(candidates, dict) or set(candidates) != CANDIDATES_KEYS:
        raise ValueError("P4-v4 lock planned candidates schema differs")
    _identity_exact(candidates, CANDIDATES_KEYS, "P4-v4 lock planned candidates identity differs")
    root = _identity_exact(candidates["root"], CANDIDATE_ROOT_KEYS, "P4-v4 lock planned root differs")
    if root.get("kind") != "candidate_root":
        raise ValueError("P4-v4 lock planned root differs")
    root_path = _future_lexical_path(root.get("root"), "planned candidates root")
    if root_path != _future_lexical_path(root.get("resolved_root"), "planned candidates root"):
        raise ValueError("P4-v4 lock planned root differs")
    attempt = candidates.get("attempt_id")
    if not isinstance(attempt, str) or _SHA256.fullmatch(attempt) is None:
        raise ValueError("P4-v4 lock planned attempt differs")
    manifest = _validate_payload_manifest(spec["payload_manifest"])
    planned: dict[str, object] = {"root": root, "attempt_id": attempt}
    seen: set[str] = set()
    for backend in _BACKEND_ORDER:
        run = _identity_exact(planned_run[backend], PLANNED_RUN_ITEM_KEYS, "P4-v4 lock planned run differs")
        run_identity = _identity_exact(run["identity"], RUN_IDENTITY_KEYS, "P4-v4 lock planned run identity differs")
        token = run.get("run_token")
        if (run_identity.get("kind") != "run_root" or not isinstance(token, str)
                or _SHA256.fullmatch(token) is None or token in seen or attempt == token):
            raise ValueError("P4-v4 lock planned run differs")
        candidate = _identity_exact(candidates[backend], PLANNED_CANDIDATE_ITEM_KEYS, "P4-v4 lock planned candidate differs")
        candidate_root = candidate.get("candidate_root")
        if (candidate.get("backend") != backend or candidate.get("run_identity") != run_identity
                or candidate.get("run_token") != token or not isinstance(candidate_root, str)
                or _future_lexical_path(candidate_root, f"planned candidate {backend}") != root_path / attempt / backend):
            raise ValueError("P4-v4 lock planned candidate mapping differs")
        item = {
            "backend": backend, "run_identity": run_identity, "run_token": token,
            "candidate_root": candidate_root, "staging_projection": _planned_projection(manifest, token),
        }
        item["identity_sha256"] = canonical_sha256(item)
        planned[backend] = item
        seen.update((token, candidate_root, item["identity_sha256"]))
    if len(seen) != 6:
        raise ValueError("P4-v4 lock planned pair reuse differs")
    planned["identity_sha256"] = canonical_sha256(planned)
    commitment = {key: spec[key] for key in (
        "entry", "source", "interpreter", "environment", "authorities", "backends", "execution_contract",
    )}
    commitment = {"schema_version": "r09_b2_p4_v4_planned_roster_commitment_v1", **commitment, "planned": planned}
    commitment["commitment_sha256"] = canonical_sha256(commitment)
    return commitment


def lock_authorized_planned_roster_commitment() -> Path:
    """Write the single approved planned commitment, or fail before output creation."""
    authority = AUTHORIZED_P4_V4_LOCK_SPEC
    if authority is None:
        raise ValueError("P4-v4 lock authority is absent")
    if not isinstance(authority, dict) or set(authority) != LOCK_AUTHORITY_KEYS:
        raise ValueError("P4-v4 lock authority schema differs")
    if authority.get("schema_version") != "r09_b2_p4_v4_lock_authority_v1":
        raise ValueError("P4-v4 lock authority schema differs")
    if (any(not isinstance(authority[key], str) for key in LOCK_AUTHORITY_KEYS)
            or _GIT_REVISION.fullmatch(authority["source_commit"]) is None
            or _GIT_REVISION.fullmatch(authority["source_tree_oid"]) is None
            or _GIT_REVISION.fullmatch(authority["gitlink"]) is None
            or any(_SHA256.fullmatch(authority[key]) is None for key in ("spec_git_blob_sha256", "spec_current_sha256", "spec_raw_sha256"))
            or "/" in authority["output_basename"] or not authority["output_basename"]):
        raise ValueError("P4-v4 lock authority differs")
    source_fd = _open_absolute_directory_chain(authority["source_root"], "P4-v4 lock source root differs")
    try:
        raw = _read_lock_spec_at(source_fd, authority["spec_path"])
    finally:
        os.close(source_fd)
    if hashlib.sha256(raw).hexdigest() != authority["spec_raw_sha256"]:
        raise ValueError("P4-v4 lock spec raw SHA differs")
    try:
        spec = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("P4-v4 lock spec is not JSON") from exc
    source_root = Path(authority["source_root"])
    if (not isinstance(spec, dict) or not isinstance(spec.get("source"), dict)
            or spec["source"].get("root") != authority["source_root"]):
        raise ValueError("P4-v4 lock source binding differs")
    interpreter = spec.get("interpreter")
    git_path = validate_host_git(interpreter.get("host_git") if isinstance(interpreter, dict) else None)
    _clean_git_root(source_root, git_path)
    if (_git(source_root, "rev-parse", "HEAD", git_executable=git_path).decode().strip() != authority["source_commit"]
            or _git(source_root, "rev-parse", f"{authority['source_commit']}^{{tree}}", git_executable=git_path).decode().strip() != authority["source_tree_oid"]):
        raise ValueError("P4-v4 lock source revision differs")
    tree = _git(source_root, "ls-tree", authority["source_commit"], "cosmos-framework", git_executable=git_path).decode().rstrip("\n").split("\t")
    if len(tree) != 2 or tree[1] != "cosmos-framework" or tree[0].split()[:2] != ["160000", "commit"] or tree[0].split()[2] != authority["gitlink"]:
        raise ValueError("P4-v4 lock Gitlink differs")
    blob = _git(source_root, "show", f"{authority['source_commit']}:{authority['spec_path']}", git_executable=git_path)
    if hashlib.sha256(blob).hexdigest() != authority["spec_git_blob_sha256"] or hashlib.sha256(raw).hexdigest() != authority["spec_current_sha256"] or blob != raw:
        raise ValueError("P4-v4 lock spec Git/current binding differs")
    commitment = build_planned_roster_commitment(raw)
    output_parent_fd = _open_absolute_directory_chain(authority["output_parent"], "P4-v4 lock output parent differs")
    try:
        flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        descriptor = os.open(authority["output_basename"], flags, 0o600, dir_fd=output_parent_fd)
        try:
            payload = (json.dumps(commitment, sort_keys=True, separators=(",", ":")) + "\n").encode()
            os.write(descriptor, payload); os.fsync(descriptor); os.lseek(descriptor, 0, os.SEEK_SET)
            if os.read(descriptor, len(payload) + 1) != payload:
                raise RuntimeError("P4-v4 lock output is POISONED_NOT_LOCKED")
            os.fchmod(descriptor, 0o444)
            if stat.S_IMODE(os.fstat(descriptor).st_mode) != 0o444:
                raise RuntimeError("P4-v4 lock output is POISONED_NOT_LOCKED")
        except BaseException as exc:
            if isinstance(exc, RuntimeError):
                raise
            raise RuntimeError("P4-v4 lock output is POISONED_NOT_LOCKED") from exc
        finally:
            os.close(descriptor)
    except FileExistsError as exc:
        raise ValueError("P4-v4 lock output is NOT_LOCKED") from exc
    finally:
        os.close(output_parent_fd)
    return Path(authority["output_parent"]) / authority["output_basename"]


def _identity(value: dict[str, object], name: str) -> None:
    if not isinstance(value.get("identity_sha256"), str) or value["identity_sha256"] != canonical_sha256({key: item for key, item in value.items() if key != "identity_sha256"}):
        raise ValueError(f"execution request {name} identity differs")


def _historical_source() -> dict[str, str]:
    value = {"root_revision": _HISTORICAL_REVISION, "gitlink_revision": _HISTORICAL_GITLINK, "submodule_revision": _HISTORICAL_GITLINK}
    return {**value, "identity_sha256": canonical_sha256(value)}


def _historical_verifier() -> dict[str, str]:
    value = {"relative_path": _HISTORICAL_VERIFIER[0], "root_revision": _HISTORICAL_REVISION, "git_blob_sha256": _HISTORICAL_VERIFIER[1]}
    return {**value, "identity_sha256": canonical_sha256(value)}


def _historical_binding(name: str) -> dict[str, str]:
    path, digest = _HISTORICAL_ARTIFACTS[name]
    return {"relative_path": path, "sha256": digest}


def _read_historical_artifact(root: Path, binding: object, expected: dict[str, str], name: str) -> tuple[bytes, dict[str, object]]:
    if binding != expected:
        raise ValueError(f"execution request historical {name} binding differs")
    relative = Path(expected["relative_path"])
    if relative.is_absolute() or not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
        raise ValueError(f"execution request historical {name} path differs")
    lexical = root / relative
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise ValueError(f"execution request historical {name} path differs")
    flags = os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(lexical, flags)
    except OSError as exc:
        raise ValueError(f"execution request historical {name} path differs") from exc
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError(f"execution request historical {name} path differs")
        try:
            canonical = Path(f"/proc/self/fd/{descriptor}").resolve(strict=True)
        except OSError as exc:
            raise ValueError(f"execution request historical {name} path differs") from exc
        if not canonical.is_relative_to(root):
            raise ValueError(f"execution request historical {name} path differs")
        with os.fdopen(descriptor, "rb") as handle:
            descriptor = -1
            raw = handle.read()
    finally:
        if descriptor != -1:
            os.close(descriptor)
    if hashlib.sha256(raw).hexdigest() != expected["sha256"]:
        raise ValueError(f"execution request historical {name} bytes differ")
    try:
        return raw, json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"execution request historical {name} JSON differs") from exc


def _validate_historical_verification(value: object) -> None:
    if not isinstance(value, dict) or set(value) != {"checks", "schema_version", "status"} or value["schema_version"] != "r09_b2_p4_d005_verifier_v2" or value["status"] != "PASS":
        raise ValueError("execution request historical verification schema differs")
    checks = value["checks"]
    if not isinstance(checks, dict) or set(checks) != {"distinct_outputs", "matched", "recurrent", "ttt_fast_weight"} or checks["distinct_outputs"] is not True:
        raise ValueError("execution request historical verification checks differ")
    matched = checks["matched"]
    if not isinstance(matched, dict) or set(matched) != {"budget", "external_assets", "p1_manifest", "p3_sha256", "source"} or any(item is not True for item in matched.values()):
        raise ValueError("execution request historical verification matched differs")
    for backend in ("recurrent", "ttt_fast_weight"):
        item = checks[backend]
        if not isinstance(item, dict) or set(item) != _VERIFICATION_BACKEND_KEYS or any(flag is not True for flag in item.values()):
            raise ValueError("execution request historical verification backend differs")


def validate_authorities_pair(authorities: object, request: dict[str, object], root: Path, git_executable: Path) -> None:
    """Validate the fixed historical D005 authority without invoking its verifier."""
    if not isinstance(authorities, dict) or set(authorities) != AUTHORITIES_KEYS:
        raise ValueError("execution request authorities schema differs")
    _identity(authorities, "authorities")
    pair = authorities["d005_pair"]
    if not isinstance(pair, dict) or set(pair) != AUTHORITIES_PAIR_KEYS or pair.get("model") != "historical_d005_v2":
        raise ValueError("execution request authorities pair schema differs")
    _identity(pair, "authorities pair")
    if pair.get("historical_source") != _historical_source() or pair.get("historical_verifier") != _historical_verifier():
        raise ValueError("execution request historical source differs")
    if not git_executable.is_absolute() or Path(request.get("interpreter", {}).get("host_git", {}).get("path", "")) != git_executable:
        raise ValueError("execution request historical host Git differs")
    records: dict[str, dict[str, object]] = {}
    paths: set[str] = set()
    for backend in ("recurrent", "ttt_fast_weight"):
        binding = _historical_binding(backend)
        raw, record = _read_historical_artifact(root, pair.get(backend), binding, backend)
        source = {"root_revision": _HISTORICAL_REVISION, "gitlink_revision": _HISTORICAL_GITLINK, "submodule_revision": _HISTORICAL_GITLINK}
        digest = {key: item for key, item in record.items() if key != "d005_sha256"}
        if raw != (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode() or record.get("backend") != backend or record.get("schema_version") != "r09_b2_p4_launch_d005_v2" or record.get("status") != "FROZEN_NOT_EXECUTED" or record.get("source") != source or record.get("d005_sha256") != canonical_sha256(digest):
            raise ValueError("execution request historical record differs")
        paths.add(binding["relative_path"]); records[backend] = record
    if len(paths) != 2:
        raise ValueError("execution request historical artifact path differs")
    _, verification = _read_historical_artifact(root, pair.get("verification"), _historical_binding("verification"), "verification")
    _validate_historical_verification(verification)
    blob = _git(root, "show", f"{_HISTORICAL_REVISION}:{_HISTORICAL_VERIFIER[0]}", git_executable=git_executable)
    if hashlib.sha256(blob).hexdigest() != _HISTORICAL_VERIFIER[1]:
        raise ValueError("execution request historical verifier bytes differ")
    _validate_environment_sections(request.get("environment"), records)


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


def _git(root: Path, *args: str, git_executable: Path | None = None) -> bytes:
    try:
        return subprocess.run((str(git_executable) if git_executable is not None else "git", "-C", str(root), *args), check=True, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError("execution request source Git command differs") from exc


def _clean_git_root(root: Path, git_executable: Path) -> None:
    if root.is_symlink() or not root.is_dir() or _git(root, "rev-parse", "--show-toplevel", git_executable=git_executable).decode().strip() != str(root):
        raise ValueError("execution request source Git root differs")
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all", git_executable=git_executable):
        raise ValueError("execution request source is not full-clean")


def validate_source(value: object, entry: dict[str, object], git_executable: Path) -> None:
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
    _clean_git_root(root, git_executable)
    framework = root / "cosmos-framework"
    _clean_git_root(framework, git_executable)
    if framework.is_symlink() or _git(root, "rev-parse", "HEAD", git_executable=git_executable).decode().strip() != value["root_revision"] or _git(root, "rev-parse", "--verify", f"{value['root_revision']}^{{commit}}", git_executable=git_executable).decode().strip() != value["root_revision"]:
        raise ValueError("execution request source checkout revision differs")
    tree = _git(root, "ls-tree", value["root_revision"], "cosmos-framework", git_executable=git_executable).decode().rstrip("\n").split("\t")
    if len(tree) != 2 or tree[1] != "cosmos-framework" or tree[0].split()[:2] != ["160000", "commit"] or tree[0].split()[2] != value["gitlink"] or _git(framework, "rev-parse", "HEAD", git_executable=git_executable).decode().strip() != value["gitlink"]:
        raise ValueError("execution request source Gitlink differs")
    entry_path = root / ENTRY_TOOL_PATH
    _git(root, "ls-files", "--error-unmatch", "--", ENTRY_TOOL_PATH, git_executable=git_executable)
    blob = _git(root, "show", f"{value['root_revision']}:{ENTRY_TOOL_PATH}", git_executable=git_executable)
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
    pending: list[tuple[Path, bytes | None]] = [(path, raw)]
    scheduled = {str(path)}
    objects: dict[str, str] = {}
    while pending:
        current, current_raw = pending.pop()
        if current == path:
            canonical = path
        else:
            canonical, current_raw = _read_canonical_regular_nofollow(
                current, "execution request host Git object differs",
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
            try:
                dependency_path = dependency_path.resolve(strict=True)
            except OSError as exc:
                raise ValueError("execution request host Git ELF dependency differs") from exc
            if str(dependency_path) not in scheduled:
                scheduled.add(str(dependency_path))
                pending.append((dependency_path, None))
    return canonical_sha256({"objects": [{"path": name, "sha256": digest} for name, digest in sorted(objects.items())]})


def _environment_object(value: object, *, native: bool) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != ENVIRONMENT_OBJECT_KEYS:
        raise ValueError("execution request environment object schema differs")
    items = {key: item for key, item in value.items() if key != "sha256"}
    if value["sha256"] != canonical_sha256(items) or value["inherit_allowlist"] != [] or value["unset"] != list(P5_FORBIDDEN_ENVIRONMENT):
        raise ValueError("execution request environment object identity differs")
    values = value["set"]
    if not isinstance(values, dict) or not all(isinstance(key, str) and isinstance(item, str) for key, item in values.items()):
        raise ValueError("execution request environment set differs")
    if set(values) & set(P5_FORBIDDEN_ENVIRONMENT):
        raise ValueError("execution request environment forbidden key differs")
    if native and values != {}:
        raise ValueError("execution request native loader environment differs")
    return value


def _project_d005_environment(record: dict[str, object], backend: str) -> tuple[dict[str, str], dict[str, object]]:
    environment = record.get("environment")
    if record.get("backend") != backend or not isinstance(environment, dict) or not isinstance(environment.get("set"), dict):
        raise ValueError("execution request D005 environment differs")
    values = environment["set"]
    expected = set(REQUIRED_ENV) | set(P5_P3_BACKEND_ENVIRONMENT)
    if (set(values) != expected or not all(isinstance(key, str) and isinstance(item, str) for key, item in values.items())
            or set(values) & (RANK_ENV | SANITIZED_ENV)):
        raise ValueError("execution request D005 environment differs")
    projected = {key: item for key, item in values.items() if key not in D005_EXCLUDED_ENVIRONMENT_KEYS}
    if set(values) - set(projected) != set(D005_EXCLUDED_ENVIRONMENT_KEYS):
        raise ValueError("execution request D005 projection differs")
    expected_backend = P5_P3_BACKEND_ENVIRONMENT["PSM_R09_B1_TTT_ENABLED"][backend]
    if values.get("PSM_R09_B1_TTT_ENABLED") != expected_backend:
        raise ValueError("execution request D005 backend differs")
    projection = {"backend": backend, "d005_sha256": record.get("d005_sha256"),
                  "input_set_sha256": canonical_sha256(values), "excluded_keys": D005_EXCLUDED_ENVIRONMENT_KEYS,
                  "projected_set_sha256": canonical_sha256(projected)}
    if not isinstance(projection["d005_sha256"], str):
        raise ValueError("execution request D005 digest differs")
    projection["sha256"] = canonical_sha256(projection)
    return projected, projection


def _validate_environment_sections(value: object, records: dict[str, dict[str, object]]) -> None:
    if not isinstance(value, dict) or set(value) != {"recurrent", "ttt_fast_weight"}:
        raise ValueError("execution request environment pair schema differs")
    sections: dict[str, dict[str, object]] = {}
    for backend, record in records.items():
        section = value[backend]
        if not isinstance(section, dict) or set(section) != ENVIRONMENT_KEYS:
            raise ValueError("execution request environment schema differs")
        identity = {key: item for key, item in section.items() if key != "identity_sha256"}
        if section["identity_sha256"] != canonical_sha256(identity):
            raise ValueError("execution request environment identity differs")
        effective = _environment_object(section["effective_environment"], native=False)
        native = _environment_object(section["native_loader_environment"], native=True)
        projected, projection = _project_d005_environment(record, backend)
        projection_value = section["d005_projection"]
        if (not isinstance(projection_value, dict) or set(projection_value) != D005_PROJECTION_KEYS
                or any(not isinstance(projection_value[key], str) for key in (
                    "backend", "d005_sha256", "input_set_sha256", "projected_set_sha256", "sha256"
                ))
                or any(_SHA256.fullmatch(projection_value[key]) is None for key in (
                    "d005_sha256", "input_set_sha256", "projected_set_sha256", "sha256"
                ))
                or effective["set"] != projected or projection_value != projection):
            raise ValueError("execution request D005 projection differs")
        sections[backend] = {"effective": effective, "native": native}
    if sections["recurrent"]["native"] != sections["ttt_fast_weight"]["native"]:
        raise ValueError("execution request native loader pair differs")
    left, right = sections["recurrent"]["effective"]["set"], sections["ttt_fast_weight"]["effective"]["set"]
    different = {key for key in set(left) | set(right) if left.get(key) != right.get(key)}
    if different != set(P5_P3_BACKEND_ENVIRONMENT) or any(
        left.get(key) != values["recurrent"] or right.get(key) != values["ttt_fast_weight"]
        for key, values in P5_P3_BACKEND_ENVIRONMENT.items()
    ):
        raise ValueError("execution request environment backend difference differs")


def validate_environment_pair(value: object, recurrent: dict[str, object], ttt: dict[str, object], root: Path) -> None:
    """Validate the D005-bound, empty-parent environment pair without launching anything."""
    if verify_d005_pair(recurrent, ttt, root).get("status") != "PASS":
        raise ValueError("execution request D005 pair is not verified")
    _validate_environment_sections(value, {"recurrent": recurrent, "ttt_fast_weight": ttt})


def _future_lexical_path(value: object, name: str) -> Path:
    if not isinstance(value, str) or not value or not os.path.isabs(value) or value.startswith("//"):
        raise ValueError(f"execution request {name} path differs")
    path = Path(value)
    if os.path.normpath(value) != value or any(part in {".", ".."} for part in path.parts):
        raise ValueError(f"execution request {name} path differs")
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        try:
            mode = os.lstat(current).st_mode
        except FileNotFoundError:
            break
        except OSError as exc:
            raise ValueError(f"execution request {name} path differs") from exc
        if stat.S_ISLNK(mode):
            raise ValueError(f"execution request {name} path differs")
    return path


def _lexically_overlaps(left: Path, right: Path) -> bool:
    return left == right or left in right.parents or right in left.parents


def _validate_run_item(value: object, source_root: Path, backend: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != RUN_ITEM_KEYS:
        raise ValueError("execution request run item schema differs")
    identity = value.get("identity")
    if not isinstance(identity, dict) or set(identity) != RUN_IDENTITY_KEYS:
        raise ValueError("execution request run identity schema differs")
    if identity.get("kind") != "run_root" or not isinstance(identity.get("identity_sha256"), str):
        raise ValueError("execution request run identity differs")
    root = _future_lexical_path(identity.get("root"), f"run {backend}")
    resolved_root = _future_lexical_path(identity.get("resolved_root"), f"run {backend}")
    if root != resolved_root or identity["identity_sha256"] != canonical_sha256(
        {key: item for key, item in identity.items() if key != "identity_sha256"}
    ):
        raise ValueError("execution request run identity differs")
    if any(_SHA256.fullmatch(value.get(key, "")) is None for key in ("run_token", "roster_sha256")):
        raise ValueError("execution request run digest differs")
    if _lexically_overlaps(root, source_root) or _lexically_overlaps(root, source_root / "cosmos-framework"):
        raise ValueError("execution request run source overlap differs")
    return value


def validate_run_pair(value: object, source: object) -> None:
    """Validate only the non-executable future run-root pair contract."""
    if not isinstance(value, dict) or set(value) != RUN_KEYS or not isinstance(source, dict):
        raise ValueError("execution request run pair schema differs")
    source_root = _future_lexical_path(source.get("root"), "source")
    recurrent = _validate_run_item(value["recurrent"], source_root, "recurrent")
    ttt = _validate_run_item(value["ttt_fast_weight"], source_root, "ttt_fast_weight")
    if any(recurrent[key] == ttt[key] for key in RUN_ITEM_KEYS):
        raise ValueError("execution request run pair reuse differs")


def validate_candidates(value: object, source: object, run: object) -> None:
    """Validate the static, non-materializing candidate namespace binding."""
    if not isinstance(value, dict) or set(value) != CANDIDATES_KEYS or not isinstance(source, dict) or not isinstance(run, dict):
        raise ValueError("execution request candidates schema differs")
    _identity(value, "candidates")
    if (not isinstance(value.get("attempt_id"), str)
            or _SHA256.fullmatch(value["attempt_id"]) is None or set(run) != RUN_KEYS
            or any(not isinstance(run[backend], dict) for backend in RUN_KEYS)):
        raise ValueError("execution request candidates attempt differs")
    root_identity = value["root"]
    if not isinstance(root_identity, dict) or set(root_identity) != CANDIDATE_ROOT_KEYS or root_identity.get("kind") != "candidate_root":
        raise ValueError("execution request candidates root schema differs")
    _identity(root_identity, "candidates root")
    root = _future_lexical_path(root_identity.get("root"), "candidates root")
    if root != _future_lexical_path(root_identity.get("resolved_root"), "candidates root"):
        raise ValueError("execution request candidates root differs")
    source_root = _future_lexical_path(source.get("root"), "source")
    if _lexically_overlaps(root, source_root) or _lexically_overlaps(root, source_root / "cosmos-framework"):
        raise ValueError("execution request candidates source overlap differs")
    seen: set[str] = set()
    for backend in ("recurrent", "ttt_fast_weight"):
        item = value[backend]
        run_item = run[backend]
        if (not isinstance(item, dict) or set(item) != CANDIDATE_ITEM_KEYS or item.get("backend") != backend
                or item.get("run") != run_item):
            raise ValueError("execution request candidates backend differs")
        _identity(item, "candidates backend")
        candidate_root = _future_lexical_path(item.get("candidate_root"), f"candidates {backend}")
        if candidate_root != root / value["attempt_id"] / backend:
            raise ValueError("execution request candidates path differs")
        for other in ("recurrent", "ttt_fast_weight"):
            run_root = _future_lexical_path(run[other].get("identity", {}).get("root"), f"run {other}")
            if _lexically_overlaps(root, run_root) or _lexically_overlaps(candidate_root, run_root):
                raise ValueError("execution request candidates run overlap differs")
        run_identity = canonical_sha256(item["run"])
        if (value["attempt_id"] == run_item.get("run_token")
                or item["candidate_root"] in seen
                or item["identity_sha256"] in seen
                or run_identity in seen):
            raise ValueError("execution request candidates reuse differs")
        seen.update((item["candidate_root"], item["identity_sha256"], run_identity))


def validate_backends(value: object) -> None:
    """Validate the verifier-owned P3 core snapshots without reading any evidence."""
    if not isinstance(value, dict) or set(value) != BACKENDS_KEYS:
        raise ValueError("execution request backends schema differs")
    _identity(value, "backends")
    records: dict[str, dict[str, object]] = {}
    identities: set[str] = set()
    for backend in ("recurrent", "ttt_fast_weight"):
        record = value[backend]
        if not isinstance(record, dict) or set(record) != BACKEND_ITEM_KEYS or record.get("backend") != backend:
            raise ValueError("execution request backends record differs")
        record_identity = record.get("identity_sha256")
        if not isinstance(record_identity, str):
            _identity(record, "backends record")
        if record_identity in identities:
            raise ValueError("execution request backends reuse differs")
        _identity(record, "backends record")
        identities.add(record_identity)
        contract = record["p3_contract"]
        if not isinstance(contract, dict) or set(contract) != P3_CONTRACT_KEYS:
            raise ValueError("execution request P3 contract schema differs")
        _identity(contract, "P3 contract")
        core = {key: contract[key] for key in P3_CORE_KEYS}
        if (not all(isinstance(core[key], str) and _SHA256.fullmatch(core[key]) is not None for key in ("artifact_sha256", "verifier_sha256"))
                or not isinstance(core["backend_contract"], dict) or set(core["backend_contract"]) != BACKEND_CONTRACT_KEYS):
            raise ValueError("execution request P3 contract digest differs")
        backend_contract = core["backend_contract"]
        selectors = backend_contract["selector_keys"]
        membership = backend_contract["optimizer_membership_sha256"]
        if (not isinstance(selectors, list) or not selectors or not all(isinstance(item, str) for item in selectors)
                or len(selectors) != len(set(selectors)) or not isinstance(membership, str)
                or _SHA256.fullmatch(membership) is None):
            raise ValueError("execution request P3 backend contract differs")
        if core != P3_CORE_SNAPSHOTS[backend]:
            raise ValueError("execution request P3 snapshot differs")
        records[backend] = core
    if (records["recurrent"]["artifact_sha256"] != records["ttt_fast_weight"]["artifact_sha256"]
            or records["recurrent"]["verifier_sha256"] != records["ttt_fast_weight"]["verifier_sha256"]):
        raise ValueError("execution request P3 pair binding differs")


def validate_host_git(value: object) -> Path:
    if not isinstance(value, dict) or set(value) != HOST_GIT_KEYS or not all(isinstance(value[key], str) for key in HOST_GIT_KEYS):
        raise ValueError("execution request host Git schema differs")
    git_path, git_raw = _read_strict_regular_nofollow(Path(value["path"]), "execution request host Git path differs")
    if (_SHA256.fullmatch(value["elf_sha256"]) is None or _SHA256.fullmatch(value["closure_sha256"]) is None
            or hashlib.sha256(git_raw).hexdigest() != value["elf_sha256"]
            or _host_git_closure(git_path, git_raw) != value["closure_sha256"]):
        raise ValueError("execution request host Git identity differs")
    return git_path


def validate_interpreter(value: object, source: dict[str, object], git_path: Path | None = None) -> None:
    if not isinstance(value, dict) or set(value) != INTERPRETER_KEYS:
        raise ValueError("execution request interpreter schema differs")
    lexical, host_git, argv, identity_sha256 = (value["lexical_interpreter"], value["host_git"], value["loader_argv"], value["identity_sha256"])
    if not isinstance(lexical, dict) or not isinstance(host_git, dict) or not isinstance(argv, list) or not isinstance(identity_sha256, str):
        raise ValueError("execution request interpreter schema differs")
    identity = {key: item for key, item in value.items() if key != "identity_sha256"}
    if _SHA256.fullmatch(identity_sha256) is None or identity_sha256 != canonical_sha256(identity):
        raise ValueError("execution request interpreter identity differs")
    try:
        if lexical_interpreter(Path(lexical.get("path", ""))) != lexical:
            raise ValueError("execution request lexical interpreter differs")
    except (OSError, ProvenanceError, ValueError) as exc:
        raise ValueError("execution request lexical interpreter differs") from exc
    if git_path is None:
        git_path = validate_host_git(host_git)
    elif git_path != Path(host_git["path"]):
        raise ValueError("execution request host Git identity differs")
    root = Path(source["root"])
    if not is_verified_loader_argv(argv) or Path(argv[8]) != root:
        raise ValueError("execution request loader argv differs")
    try:
        expected = verified_loader_argv(lexical, Path(argv[6]), argv[7], root, argv[9], argv[10], git_executable=git_path)
    except (OSError, ProvenanceError, ValueError) as exc:
        raise ValueError("execution request loader argv differs") from exc
    if argv != expected:
        raise ValueError("execution request loader argv differs")


def request_sha256(raw: bytes) -> str:
    if not isinstance(raw, bytes):
        raise ValueError("execution request must be a regular file")
    return hashlib.sha256(raw).hexdigest()


def _admission_authority() -> tuple[
    callable,
    callable,
]:
    """Keep admission bytes and one-shot state outside the capability object."""
    admitted_requests: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()

    def admit(raw: bytes) -> _AdmittedRequest:
        load_execution_request(raw)
        admitted = object.__new__(_AdmittedRequest)
        digest = request_sha256(raw)
        object.__setattr__(admitted, "raw", raw)
        object.__setattr__(admitted, "request_sha256", digest)
        object.__setattr__(admitted, "_consumed", False)
        object.__setattr__(admitted, "_locked", True)
        admitted_requests[admitted] = (raw, digest, False)
        return admitted

    def consume(admitted: _AdmittedRequest) -> tuple[bytes, str]:
        if not isinstance(admitted, _AdmittedRequest):
            raise ValueError("P4-v4 reservation requires an admitted request")
        try:
            raw, digest, consumed = admitted_requests[admitted]
        except KeyError as exc:
            raise ValueError("P4-v4 reservation requires an admitted request") from exc
        if consumed:
            raise ValueError("P4-v4 reservation capability is consumed")
        admitted_requests[admitted] = (raw, digest, True)
        return raw, digest

    return admit, consume


_admit_execution_request, _consume_admitted_request = _admission_authority()


def _reservation_plan(admitted: _AdmittedRequest, namespace: Path) -> tuple[Path, ...]:
    raw, admitted_sha256 = _consume_admitted_request(admitted)
    if request_sha256(raw) != admitted_sha256:
        raise ValueError("P4-v4 admitted request SHA differs")
    if (not namespace.is_absolute() or namespace == Path("/")
            or any(part in ("", ".", "..") for part in namespace.parts[1:])):
        raise ValueError("P4-v4 reservation namespace differs")
    paths: list[Path] = []
    for backend in _BACKEND_ORDER:
        try:
            request = json.loads(raw)
            if (not isinstance(request, dict)
                    or (json.dumps(request, sort_keys=True, separators=(",", ":")) + "\n").encode() != raw):
                raise ValueError("P4-v4 admitted request bytes differ")
            run = request["run"][backend]
            root = Path(run["identity"]["root"])
            token = run["run_token"]
        except (KeyError, TypeError) as exc:
            raise ValueError("P4-v4 admitted run differs") from exc
        if root.parent != namespace or not isinstance(token, str):
            raise ValueError("P4-v4 reservation root differs")
        paths.extend((root, root / "import_staging", root / "import_staging" / token))
    if len(set(paths)) != len(paths):
        raise ValueError("P4-v4 reservation overlap differs")
    for index, path in enumerate(paths):
        expected_parent = namespace if index % 3 == 0 else paths[index - 1]
        if path.parent != expected_parent:
            raise ValueError("P4-v4 reservation path differs")
    return tuple(paths)


def _open_namespace_anchor(namespace: Path) -> int:
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open("/", flags)
    try:
        for component in namespace.parts[1:]:
            child = os.open(component, flags, dir_fd=descriptor)
            try:
                if not stat.S_ISDIR(os.fstat(child).st_mode):
                    raise ValueError("P4-v4 reservation namespace differs")
            except BaseException:
                os.close(child)
                raise
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _open_created_directory(name: str, parent_fd: int) -> int:
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    child = os.open(name, flags, dir_fd=parent_fd)
    try:
        if not stat.S_ISDIR(os.fstat(child).st_mode):
            raise OSError("reservation target is not a directory")
        return child
    except BaseException:
        os.close(child)
        raise


def _reserve_staging(admitted: _AdmittedRequest, namespace: Path) -> ReservationResult:
    paths = _reservation_plan(admitted, namespace)
    try:
        namespace_fd = _open_namespace_anchor(namespace)
    except OSError as exc:
        raise ValueError("P4-v4 reservation namespace differs") from exc
    created: list[Path] = []
    try:
        for backend in _BACKEND_ORDER:
            try:
                os.stat(backend, dir_fd=namespace_fd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                raise ValueError("P4-v4 reservation path already exists")
        for backend_index, backend in enumerate(_BACKEND_ORDER):
            root, middle, leaf = paths[backend_index * 3:backend_index * 3 + 3]
            parent_fd = namespace_fd
            try:
                for path, name in ((root, backend), (middle, "import_staging"), (leaf, leaf.name)):
                    try:
                        os.mkdir(name, dir_fd=parent_fd)
                    except OSError as exc:
                        raise ReservationPoisonedError(tuple(created), path, exc) from exc
                    created.append(path)
                    try:
                        child_fd = _open_created_directory(name, parent_fd)
                    except OSError as exc:
                        raise ReservationPoisonedError(tuple(created), path, exc) from exc
                    if parent_fd != namespace_fd:
                        os.close(parent_fd)
                    parent_fd = child_fd
            finally:
                if parent_fd != namespace_fd:
                    os.close(parent_fd)
        return ReservationResult("RESERVED", tuple(created))
    finally:
        os.close(namespace_fd)


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
