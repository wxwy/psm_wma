"""Temporary-only native Git adapter for authority-root CPU/static tests."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from tools.psm_wma.immutable_source_authority_root import (
    AuthorityGitTransaction,
    AuthorityRequest,
    EvidenceCleanupIncomplete,
    prepare_candidate,
    publish_candidate,
    validate_request,
    verify_candidate,
)
import tools.psm_wma.immutable_source_authority_root as authority_module
from tools.psm_wma.immutable_source_collection import (
    AUTHORITY_REF,
    TreeEntry,
    git_blob_oid,
    sha256_digest,
    validated_git_tree,
)


class NativeGitError(RuntimeError):
    pass


def _read_input_fd(descriptor: int) -> bytes:
    info = os.fstat(descriptor)
    if not stat.S_ISREG(info.st_mode):
        raise NativeGitError("input FD 必须为regular file")
    return os.pread(descriptor, info.st_size, 0)


@dataclass(frozen=True)
class ModuleIdentity:
    repo_path: str
    blob_native_oid: str
    raw_sha256: str


@dataclass(frozen=True)
class ExecutableIdentity:
    path: Path
    raw_sha256: str
    version: str


@dataclass(frozen=True)
class AuthorityAdapterInvocation:
    request: AuthorityRequest
    selection_raw_sha256: str
    config_raw_sha256: str
    adapter: ModuleIdentity
    authority_module: ModuleIdentity
    interpreter: ExecutableIdentity
    git_executable: ExecutableIdentity
    evidence_path: Path
    argv_sha256: str


def _is_sha1(value: str) -> bool:
    return len(value) == 40 and all(char in "0123456789abcdef" for char in value)


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _is_repo_path(value: str) -> bool:
    return bool(value) and not value.startswith("/") and "\0" not in value and all(
        part not in ("", ".", "..") for part in value.split("/")
    )


def _verify_module_identity(
    identity: ModuleIdentity,
    tree: Mapping[str, TreeEntry],
    transaction: AuthorityGitTransaction,
    cwd: Path,
) -> None:
    if (
        not _is_repo_path(identity.repo_path)
        or not _is_sha1(identity.blob_native_oid)
        or not _is_sha256(identity.raw_sha256)
        or tree.get(identity.repo_path) != ("100644", "blob", identity.blob_native_oid)
    ):
        raise NativeGitError("formal module identity 无效")
    path = cwd / identity.repo_path
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
        raise NativeGitError("adapter module 必须为regular non-symlink file")
    raw = path.read_bytes()
    if (
        sha256_digest(raw) != identity.raw_sha256
        or git_blob_oid(raw) != identity.blob_native_oid
        or transaction.blob_bytes(identity.blob_native_oid) != raw
    ):
        raise NativeGitError("formal module bytes 漂移")


def _tool_version(path: Path) -> str:
    completed = subprocess.run(
        [str(path), "--version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    if completed.returncode:
        raise NativeGitError("tool --version 失败")
    return (completed.stdout + completed.stderr).decode("utf-8", "replace").strip()


def _verify_executable_identity(identity: ExecutableIdentity) -> None:
    if not identity.path.is_absolute() or not _is_sha256(identity.raw_sha256) or not identity.version:
        raise NativeGitError("tool identity 无效")
    info = identity.path.lstat()
    if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
        raise NativeGitError("tool executable 必须为regular non-symlink file")
    if sha256_digest(identity.path.read_bytes()) != identity.raw_sha256:
        raise NativeGitError("tool executable bytes 漂移")
    if _tool_version(identity.path) != identity.version:
        raise NativeGitError("tool version 漂移")


def _verify_loaded_identity(
    invocation: AuthorityAdapterInvocation, cwd: Path
) -> None:
    expected_adapter = (cwd / invocation.adapter.repo_path).resolve()
    expected_authority = (cwd / invocation.authority_module.repo_path).resolve()
    if Path(sys.executable).resolve() != invocation.interpreter.path.resolve():
        raise NativeGitError("actual interpreter identity 漂移")
    if Path(__file__).resolve() != expected_adapter:
        raise NativeGitError("actual adapter module identity 漂移")
    if Path(authority_module.__file__).resolve() != expected_authority:
        raise NativeGitError("actual authority module identity 漂移")


def request_from_input_fds(
    formal_root: str,
    child_gitlink: str,
    selection_fd: int,
    config_fd: int,
    selection_raw_sha256: str,
    config_raw_sha256: str,
) -> AuthorityRequest:
    selection_raw = _read_input_fd(selection_fd)
    config_raw = _read_input_fd(config_fd)
    if (
        not _is_sha256(selection_raw_sha256)
        or not _is_sha256(config_raw_sha256)
        or sha256_digest(selection_raw) != selection_raw_sha256
        or sha256_digest(config_raw) != config_raw_sha256
    ):
        raise NativeGitError("input raw SHA-256 漂移")
    request = AuthorityRequest(formal_root, child_gitlink, selection_raw, config_raw)
    validate_request(request)
    return request


def preflight_authority_invocation(
    invocation: AuthorityAdapterInvocation,
    transaction: AuthorityGitTransaction,
    cwd: Path,
) -> None:
    request = invocation.request
    validate_request(request)
    if (
        sha256_digest(request.selection_raw) != invocation.selection_raw_sha256
        or sha256_digest(request.config_raw) != invocation.config_raw_sha256
    ):
        raise NativeGitError("request raw SHA-256 漂移")
    tree = validated_git_tree(transaction, request.materialization_formal_root)
    if tree.get("cosmos-framework") != (
        "160000", "commit", request.expected_child_gitlink,
    ):
        raise NativeGitError("formal root Gitlink 漂移")
    _verify_module_identity(invocation.adapter, tree, transaction, cwd)
    _verify_module_identity(invocation.authority_module, tree, transaction, cwd)
    _verify_executable_identity(invocation.interpreter)
    _verify_executable_identity(invocation.git_executable)
    _verify_loaded_identity(invocation, cwd)
    evidence_path = invocation.evidence_path
    guard = evidence_path.with_name(evidence_path.name + ".pending")
    if not evidence_path.is_absolute() or evidence_path.exists() or evidence_path.is_symlink() or guard.exists() or guard.is_symlink():
        raise NativeGitError("evidence destination 必须为fresh absent absolute path")
    if transaction.local_ref(AUTHORITY_REF) is not None:
        raise NativeGitError("fixed local ref 必须预先absent")
    if transaction.remote_ref(AUTHORITY_REF) is not None:
        raise NativeGitError("fixed remote ref 必须预先absent")


def _pass_evidence_record(
    invocation: AuthorityAdapterInvocation,
    transaction: "NativeAuthorityGit",
    candidate,
    binding,
) -> dict[str, object]:
    metadata = transaction.metadata
    authority = binding.as_mapping()
    revision = candidate.revision
    record: dict[str, object] = {
        "schema": "immutable_source_authority_root_materialization_evidence_v1",
        "status": "PASS",
        "execution": {
            "formal_root_revision": invocation.request.materialization_formal_root,
            "child_gitlink": invocation.request.expected_child_gitlink,
            "adapter": {
                "path": invocation.adapter.repo_path,
                "blob_native_oid": invocation.adapter.blob_native_oid,
                "raw_sha256": invocation.adapter.raw_sha256,
            },
            "authority_module": {
                "path": invocation.authority_module.repo_path,
                "blob_native_oid": invocation.authority_module.blob_native_oid,
                "raw_sha256": invocation.authority_module.raw_sha256,
            },
            "interpreter": {
                "path": str(invocation.interpreter.path),
                "raw_sha256": invocation.interpreter.raw_sha256,
                "version": invocation.interpreter.version,
            },
            "git_executable": {
                "path": str(invocation.git_executable.path),
                "raw_sha256": invocation.git_executable.raw_sha256,
                "version": invocation.git_executable.version,
            },
            "cwd": str(transaction.cwd),
            "sanitized_env_sha256": sha256_digest(json.dumps(transaction.env, sort_keys=True, separators=(",", ":")).encode()),
            "argv_sha256": invocation.argv_sha256,
            "commit_metadata": vars(metadata),
            "remote_identity_sha256": sha256_digest(transaction.remote.encode()),
            "fixed_ref": AUTHORITY_REF,
        },
        "authority": authority,
        "candidate": {
            "revision": revision,
            "parents": [invocation.request.materialization_formal_root],
            "tree_native_oid": transaction._run("rev-parse", f"{revision}^{{tree}}"),
            "verifier_pass": True,
            "binding_sha256": sha256_digest(json.dumps(authority, sort_keys=True, separators=(",", ":")).encode()),
        },
        "pre_publication": {
            "local_observation": {"state": "absent", "revision": None, "error": None},
            "remote_observation": {"state": "absent", "revision": None, "error": None},
            "both_absent": True,
        },
        "publication": {
            "local_create_attempted": True, "local_create_succeeded": True,
            "remote_create_attempted": True, "remote_create_succeeded": True,
            "local_owned": True, "remote_owned": True,
        },
        "post_publication": {
            "local_observation": {"state": "revision", "revision": revision, "error": None},
            "remote_observation": {"state": "revision", "revision": revision, "error": None},
            "both_candidate": True, "committed_binding_reverified": True,
        },
        "rollback": {
            "entered": False, "required": False,
            "remote_delete_attempted": False, "remote_delete_succeeded": False,
            "local_delete_attempted": False, "local_delete_succeeded": False,
            "final_local_observation": None, "final_remote_observation": None,
            "complete": False,
        },
        "failure": {
            "primary_phase": None, "primary_code": None,
            "rollback_phase": None, "rollback_code": None,
        },
    }
    record["evidence_sha256"] = sha256_digest(
        json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    )
    return record


def run_authority_cli(
    invocation: AuthorityAdapterInvocation,
    transaction: AuthorityGitTransaction,
    cwd: Path,
) -> str:
    """Preflight, then traverse the closed authority flow exactly once."""
    preflight_authority_invocation(invocation, transaction, cwd)
    candidate = prepare_candidate(invocation.request, transaction)
    binding = verify_candidate(invocation.request, candidate, transaction)
    def finalizer(_witness, commit):
        write_pending_evidence(
            invocation.evidence_path,
            _pass_evidence_record(invocation, transaction, candidate, binding),
            commit,
        )

    return publish_candidate(
        invocation.request, candidate, binding, transaction, finalizer=finalizer
    ).revision


@dataclass(frozen=True)
class CommitMetadata:
    author_name: str
    author_email: str
    author_date: str
    committer_name: str
    committer_email: str
    committer_date: str
    message: str

    def __post_init__(self) -> None:
        if not all(isinstance(value, str) and value for value in self.__dict__.values()):
            raise NativeGitError("commit metadata 必须为non-empty string")


_EVIDENCE_KEYS = frozenset((
    "schema", "status", "execution", "authority", "candidate",
    "pre_publication", "publication", "post_publication", "rollback",
    "failure", "evidence_sha256",
))
_EXECUTION_KEYS = frozenset((
    "formal_root_revision", "child_gitlink", "adapter", "authority_module",
    "interpreter", "git_executable", "cwd", "sanitized_env_sha256",
    "argv_sha256", "commit_metadata", "remote_identity_sha256", "fixed_ref",
))
_AUTHORITY_KEYS = (
    "root_revision", "selection_path", "selection_blob_native_oid",
    "selection_raw_sha256", "config_path", "config_blob_native_oid",
    "config_raw_sha256",
)
_CANDIDATE_KEYS = frozenset((
    "revision", "parents", "tree_native_oid", "verifier_pass", "binding_sha256",
))
_OBSERVATION_KEYS = frozenset(("state", "revision", "error"))
_PUBLICATION_KEYS = frozenset((
    "local_create_attempted", "local_create_succeeded", "remote_create_attempted",
    "remote_create_succeeded", "local_owned", "remote_owned",
))
_ROLLBACK_KEYS = frozenset((
    "entered", "required", "remote_delete_attempted", "remote_delete_succeeded",
    "local_delete_attempted", "local_delete_succeeded", "final_local_observation",
    "final_remote_observation", "complete",
))
_FAILURE_KEYS = frozenset((
    "primary_phase", "primary_code", "rollback_phase", "rollback_code",
))
_PHASES = frozenset((
    "preflight", "prepare", "verify", "pre_publication", "local_cas",
    "remote_cas", "post_publication", "binding_reverify", "evidence_write",
))


def _is_sha1(value: object) -> bool:
    return isinstance(value, str) and len(value) == 40 and all(
        char in "0123456789abcdef" for char in value
    )


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        char in "0123456789abcdef" for char in value
    )


def _is_ascii_code(value: object) -> bool:
    return isinstance(value, str) and bool(value) and value.isascii()


def _is_repo_path(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and not value.startswith("/")
        and "\0" not in value
        and all(part not in ("", ".", "..") for part in value.split("/"))
    )


def _exact_mapping(value: object, keys: frozenset[str] | tuple[str, ...], name: str) -> Mapping[str, object]:
    if not isinstance(value, dict) or set(value) != set(keys):
        raise NativeGitError(f"evidence {name} key 集合无效")
    return value


def _validate_observation(value: object, name: str) -> None:
    if value is None:
        return
    observation = _exact_mapping(value, _OBSERVATION_KEYS, name)
    state = observation["state"]
    revision, error = observation["revision"], observation["error"]
    if state == "absent" and revision is None and error is None:
        return
    if state == "revision" and _is_sha1(revision) and error is None:
        return
    if state == "unreadable" and revision is None and _is_ascii_code(error):
        return
    raise NativeGitError(f"evidence {name} observation 无效")


def _is_absent(value: object) -> bool:
    return isinstance(value, dict) and value.get("state") == "absent"


def _is_revision(value: object, revision: str) -> bool:
    return isinstance(value, dict) and value.get("state") == "revision" and value.get("revision") == revision


def _validate_execution(value: object) -> Mapping[str, object]:
    execution = _exact_mapping(value, _EXECUTION_KEYS, "execution")
    if not _is_sha1(execution["formal_root_revision"]) or not _is_sha1(execution["child_gitlink"]):
        raise NativeGitError("evidence execution revision 无效")
    if not isinstance(execution["cwd"], str) or not execution["cwd"] or not isinstance(execution["fixed_ref"], str) or not execution["fixed_ref"]:
        raise NativeGitError("evidence execution cwd/fixed_ref 无效")
    for field in ("sanitized_env_sha256", "argv_sha256", "remote_identity_sha256"):
        if not _is_sha256(execution[field]):
            raise NativeGitError(f"evidence execution {field} 无效")
    for field in ("adapter", "authority_module"):
        identity = _exact_mapping(execution[field], ("path", "blob_native_oid", "raw_sha256"), field)
        if not _is_repo_path(identity["path"]) or not _is_sha1(identity["blob_native_oid"]) or not _is_sha256(identity["raw_sha256"]):
            raise NativeGitError(f"evidence execution {field} identity 无效")
    for field in ("interpreter", "git_executable"):
        identity = _exact_mapping(execution[field], ("path", "raw_sha256", "version"), field)
        if not all(isinstance(identity[key], str) and identity[key] for key in ("path", "version")) or not _is_sha256(identity["raw_sha256"]):
            raise NativeGitError(f"evidence execution {field} identity 无效")
    metadata = _exact_mapping(execution["commit_metadata"], (
        "author_name", "author_email", "author_date", "committer_name",
        "committer_email", "committer_date", "message",
    ), "commit_metadata")
    if not all(isinstance(item, str) and item for item in metadata.values()):
        raise NativeGitError("evidence commit_metadata 无效")
    return execution


def _validate_authority(value: object) -> None:
    authority = _exact_mapping(value, _AUTHORITY_KEYS, "authority")
    if all(item is None for item in authority.values()):
        return
    if not (_is_sha1(authority["root_revision"]) and _is_repo_path(authority["selection_path"]) and _is_sha1(authority["selection_blob_native_oid"]) and _is_sha256(authority["selection_raw_sha256"]) and _is_repo_path(authority["config_path"]) and _is_sha1(authority["config_blob_native_oid"]) and _is_sha256(authority["config_raw_sha256"])):
        raise NativeGitError("evidence authority 无效")


def _validate_candidate(value: object, formal_root: str) -> Mapping[str, object]:
    candidate = _exact_mapping(value, _CANDIDATE_KEYS, "candidate")
    revision, parents = candidate["revision"], candidate["parents"]
    tree, passed, binding = candidate["tree_native_oid"], candidate["verifier_pass"], candidate["binding_sha256"]
    if (revision, parents, tree, passed, binding) == (None, None, None, False, None):
        return candidate
    if _is_sha1(revision) and parents is None and tree is None and passed is False and binding is None:
        return candidate
    if _is_sha1(revision) and parents == [formal_root] and _is_sha1(tree) and passed is True and _is_sha256(binding):
        return candidate
    raise NativeGitError("evidence candidate chronology 无效")


def _validate_failure(value: object, status: str) -> None:
    failure = _exact_mapping(value, _FAILURE_KEYS, "failure")
    primary_phase, primary_code = failure["primary_phase"], failure["primary_code"]
    rollback_phase, rollback_code = failure["rollback_phase"], failure["rollback_code"]
    if status == "PASS":
        if all(item is None for item in failure.values()):
            return
        raise NativeGitError("PASS evidence 不得含 failure")
    if primary_phase not in _PHASES or not _is_ascii_code(primary_code):
        raise NativeGitError("evidence primary failure 无效")
    if (rollback_phase is None) != (rollback_code is None):
        raise NativeGitError("evidence rollback failure nullability 无效")
    if rollback_phase is not None and (rollback_phase != "rollback" or not _is_ascii_code(rollback_code)):
        raise NativeGitError("evidence rollback failure 无效")
    if status == "FAIL" and rollback_phase is not None:
        raise NativeGitError("ordinary FAIL 不得含 rollback failure")
    if status == "ROLLBACK_INCOMPLETE" and rollback_phase != "rollback":
        raise NativeGitError("ROLLBACK_INCOMPLETE 必须保留 rollback failure")


def _all_false(mapping: Mapping[str, object]) -> bool:
    return all(value is False for value in mapping.values())


def _candidate_kind(candidate: Mapping[str, object]) -> str:
    if candidate["revision"] is None:
        return "empty"
    if candidate["verifier_pass"] is False:
        return "prepared"
    return "verified"


def _is_unreached(stage: Mapping[str, object]) -> bool:
    return all(value is None or value is False for value in stage.values())


def _validate_no_mutation_failure(
    record: Mapping[str, object],
    candidate: Mapping[str, object],
    pre: Mapping[str, object],
    publication: Mapping[str, object],
    post: Mapping[str, object],
    rollback: Mapping[str, object],
) -> None:
    phase = record["failure"]["primary_phase"]
    if phase not in ("preflight", "prepare", "verify"):
        return
    allowed_candidates = {
        "preflight": {"empty"},
        "prepare": {"empty", "prepared"},
        "verify": {"prepared"},
    }
    if (
        not all(value is None for value in record["authority"].values())
        or _candidate_kind(candidate) not in allowed_candidates[phase]
        or not _is_unreached(pre)
        or not _all_false(publication)
        or not _is_unreached(post)
        or rollback["entered"]
    ):
        raise NativeGitError(f"{phase} evidence 不得含 mutation witness")


def _validate_publication_failure(
    record: Mapping[str, object],
    candidate: Mapping[str, object],
    pre: Mapping[str, object],
    publication: Mapping[str, object],
    post: Mapping[str, object],
    rollback: Mapping[str, object],
) -> None:
    phase = record["failure"]["primary_phase"]
    shapes = {
        "pre_publication",
        "local_cas",
        "remote_cas",
        "post_publication",
        "binding_reverify",
        "evidence_write",
    }
    if phase not in shapes:
        return
    if (
        not all(value is not None for value in record["authority"].values())
        or _candidate_kind(candidate) != "verified"
        or not rollback["entered"]
    ):
        raise NativeGitError(f"{phase} authority/candidate/rollback chronology 无效")
    unreached_post = _is_unreached(post)
    all_publication = all(publication.values())
    if phase == "pre_publication":
        valid = not pre["both_absent"] and _all_false(publication) and unreached_post
    elif phase == "local_cas":
        valid = pre["both_absent"] and publication == {
            "local_create_attempted": True,
            "local_create_succeeded": False,
            "remote_create_attempted": False,
            "remote_create_succeeded": False,
            "local_owned": False,
            "remote_owned": False,
        } and unreached_post
    elif phase == "remote_cas":
        valid = pre["both_absent"] and publication == {
            "local_create_attempted": True,
            "local_create_succeeded": True,
            "remote_create_attempted": True,
            "remote_create_succeeded": False,
            "local_owned": True,
            "remote_owned": False,
        } and unreached_post
    elif phase == "post_publication":
        valid = pre["both_absent"] and all_publication and not post["both_candidate"]
    elif phase == "binding_reverify":
        valid = (
            pre["both_absent"]
            and all_publication
            and post["both_candidate"]
            and not post["committed_binding_reverified"]
        )
    else:
        valid = (
            pre["both_absent"]
            and all_publication
            and post["both_candidate"]
            and post["committed_binding_reverified"]
        )
    if not valid:
        raise NativeGitError(f"{phase} evidence witness shape 无效")


def verify_evidence_bytes(raw: bytes) -> Mapping[str, object]:
    """Validate the frozen evidence-v1 bytes without touching a repository."""
    try:
        value = json.loads(raw)
    except (TypeError, ValueError) as error:
        raise NativeGitError("evidence JSON 无效") from error
    if json.dumps(value, sort_keys=True, separators=(",", ":")).encode() != raw:
        raise NativeGitError("evidence 非canonical")
    record = _exact_mapping(value, _EVIDENCE_KEYS, "top-level")
    if record["schema"] != "immutable_source_authority_root_materialization_evidence_v1":
        raise NativeGitError("evidence schema 无效")
    status = record["status"]
    if status not in ("PASS", "FAIL", "ROLLBACK_INCOMPLETE"):
        raise NativeGitError("evidence status 无效")
    execution = _validate_execution(record["execution"])
    _validate_authority(record["authority"])
    candidate = _validate_candidate(record["candidate"], execution["formal_root_revision"])
    pre = _exact_mapping(record["pre_publication"], ("local_observation", "remote_observation", "both_absent"), "pre_publication")
    post = _exact_mapping(record["post_publication"], ("local_observation", "remote_observation", "both_candidate", "committed_binding_reverified"), "post_publication")
    publication = _exact_mapping(record["publication"], _PUBLICATION_KEYS, "publication")
    rollback = _exact_mapping(record["rollback"], _ROLLBACK_KEYS, "rollback")
    for name, observation in (("pre.local", pre["local_observation"]), ("pre.remote", pre["remote_observation"]), ("post.local", post["local_observation"]), ("post.remote", post["remote_observation"]), ("rollback.local", rollback["final_local_observation"]), ("rollback.remote", rollback["final_remote_observation"])):
        _validate_observation(observation, name)
    booleans = (
        ("pre.both_absent", pre["both_absent"]),
        ("post.both_candidate", post["both_candidate"]),
        ("post.committed_binding_reverified", post["committed_binding_reverified"]),
        *publication.items(),
        *((key, rollback[key]) for key in _ROLLBACK_KEYS if not key.startswith("final_")),
    )
    for name, item in booleans:
        if type(item) is not bool:
            raise NativeGitError(f"evidence {name} 必须为JSON boolean")
    if pre["both_absent"] != (_is_absent(pre["local_observation"]) and _is_absent(pre["remote_observation"])):
        raise NativeGitError("pre both_absent 与 observation 不一致")
    revision = candidate["revision"]
    if post["both_candidate"] != (isinstance(revision, str) and _is_revision(post["local_observation"], revision) and _is_revision(post["remote_observation"], revision)):
        raise NativeGitError("post both_candidate 与 observation 不一致")
    if publication["local_create_succeeded"] and not publication["local_create_attempted"] or publication["remote_create_succeeded"] and not publication["remote_create_attempted"] or publication["local_owned"] and not publication["local_create_succeeded"] or publication["remote_owned"] and not publication["remote_create_succeeded"]:
        raise NativeGitError("publication ownership chronology 无效")
    owned = publication["local_owned"] or publication["remote_owned"]
    if (rollback["entered"] and rollback["required"] != owned) or (not rollback["entered"] and rollback["required"]) or (rollback["remote_delete_attempted"] and not publication["remote_owned"]) or (rollback["local_delete_attempted"] and not publication["local_owned"]) or (rollback["remote_delete_succeeded"] and not rollback["remote_delete_attempted"]) or (rollback["local_delete_succeeded"] and not rollback["local_delete_attempted"]):
        raise NativeGitError("rollback ownership chronology 无效")
    if not rollback["entered"] and (rollback["required"] or rollback["complete"] or any(rollback[key] for key in ("remote_delete_attempted", "remote_delete_succeeded", "local_delete_attempted", "local_delete_succeeded")) or rollback["final_local_observation"] is not None or rollback["final_remote_observation"] is not None):
        raise NativeGitError("rollback 未进入时不得声明结果")
    if rollback["complete"] and not (_is_absent(rollback["final_local_observation"]) and _is_absent(rollback["final_remote_observation"])):
        raise NativeGitError("rollback complete 必须有双端 absent observation")
    _validate_failure(record["failure"], status)
    if status != "PASS":
        _validate_no_mutation_failure(
            record, candidate, pre, publication, post, rollback
        )
        _validate_publication_failure(
            record, candidate, pre, publication, post, rollback
        )
    if status == "PASS":
        if not all(item is not None for item in record["authority"].values()) or candidate["verifier_pass"] is not True or not (pre["both_absent"] and all(publication.values()) and post["both_candidate"] and post["committed_binding_reverified"]) or rollback["entered"]:
            raise NativeGitError("PASS evidence chronology 无效")
    publication_try = record["failure"]["primary_phase"] in {
        "pre_publication", "local_cas", "remote_cas", "post_publication",
        "binding_reverify", "evidence_write",
    }
    if status == "FAIL" and publication_try and not (
        rollback["entered"] and rollback["complete"]
    ):
        raise NativeGitError("publication FAIL 必须有完整终态证明")
    if status == "ROLLBACK_INCOMPLETE" and (
        not rollback["entered"] or rollback["complete"]
    ):
        raise NativeGitError("ROLLBACK_INCOMPLETE terminal 无效")
    without_digest = dict(record)
    digest = without_digest.pop("evidence_sha256")
    if not _is_sha256(digest) or hashlib.sha256(json.dumps(without_digest, sort_keys=True, separators=(",", ":")).encode()).hexdigest() != digest:
        raise NativeGitError("evidence_sha256 漂移")
    return value


def _read_regular_evidence(path: Path) -> bytes:
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    except OSError as error:
        raise NativeGitError("evidence final path 无法安全读取") from error
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise NativeGitError("evidence final path 必须为regular file")
        remaining = os.fstat(descriptor).st_size
        chunks: list[bytes] = []
        while remaining:
            chunk = os.read(descriptor, remaining)
            if not chunk:
                raise NativeGitError("evidence final path truncated")
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
    finally:
        os.close(descriptor)
    return raw


def verify_evidence_path(path: Path) -> Mapping[str, object]:
    """Accept a final record only when the sibling pending guard is absent."""
    guard = path.with_name(path.name + ".pending")
    if guard.exists() or guard.is_symlink():
        raise NativeGitError("evidence pending guard 仍存在")
    raw = _read_regular_evidence(path)
    return verify_evidence_bytes(raw)


def _fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_all(descriptor: int, payload: bytes) -> None:
    offset = 0
    while offset < len(payload):
        written = os.write(descriptor, payload[offset:])
        if written <= 0:
            raise NativeGitError("evidence write 未完整完成")
        offset += written


def _cleanup_pending_evidence(paths: tuple[Path, ...], directory: Path) -> None:
    failed = False
    for stale in paths:
        try:
            stale.unlink()
        except FileNotFoundError:
            pass
        except OSError:
            failed = True
    try:
        _fsync_directory(directory)
    except OSError:
        failed = True
    if failed:
        raise EvidenceCleanupIncomplete("evidence pre-commit cleanup 无法证明完成")


def write_pending_evidence(path: Path, record: Mapping[str, object], commit) -> None:
    """Write a verified PASS record; guard unlink is the final operation."""
    if path.exists() or path.is_symlink():
        raise NativeGitError("evidence final path 必须fresh absent")
    guard = path.with_name(path.name + ".pending")
    if guard.exists() or guard.is_symlink():
        raise NativeGitError("evidence guard 必须fresh absent")
    payload = json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    verified = verify_evidence_bytes(payload)
    if verified["status"] != "PASS":
        raise NativeGitError("writer 仅接受完整 PASS evidence")
    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    temporary = path.with_name(path.name + ".tmp")
    try:
        fd = os.open(guard, flags, 0o600)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        _fsync_directory(directory)
        fd = os.open(temporary, flags, 0o600)
        try:
            _write_all(fd, payload)
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(temporary, path)
        _fsync_directory(directory)
        if verify_evidence_bytes(_read_regular_evidence(path)) != verified:
            raise NativeGitError("evidence re-read drift")
        commit.seal_for_guard(guard, path, verified["evidence_sha256"])
    except BaseException:
        _cleanup_pending_evidence((temporary, path, guard), directory)
        raise
    try:
        commit.consume_by_unlink()
    except BaseException:
        if getattr(commit, "committed", False):
            raise
        _cleanup_pending_evidence((temporary, path, guard), directory)
        raise


class NativeAuthorityGit:
    """Explicit-identity Git transaction; callers must provide a temporary repository."""

    def __init__(self, git: Path, cwd: Path, remote: str, index: Path, metadata: CommitMetadata) -> None:
        if not git.is_absolute() or not cwd.is_absolute() or not index.is_absolute():
            raise NativeGitError("git/cwd/index 必须为绝对路径")
        self.git, self.cwd, self.remote, self.index = git, cwd, remote, index
        self.env = {"GIT_INDEX_FILE": str(index), "LC_ALL": "C", "LANG": "C", "GIT_AUTHOR_NAME": metadata.author_name, "GIT_AUTHOR_EMAIL": metadata.author_email, "GIT_AUTHOR_DATE": metadata.author_date, "GIT_COMMITTER_NAME": metadata.committer_name, "GIT_COMMITTER_EMAIL": metadata.committer_email, "GIT_COMMITTER_DATE": metadata.committer_date}
        self.metadata = metadata

    def _run(self, *args: str, input: bytes | None = None, check: bool = True) -> str:
        completed = subprocess.run(
            [str(self.git), *args], cwd=self.cwd, env=self.env, input=input,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, check=False,
        )
        if check and completed.returncode:
            raise NativeGitError(completed.stderr.decode("utf-8", "replace").strip())
        return completed.stdout.decode().strip()

    def _mutation_succeeded(self, *args: str, porcelain_flag: str | None = None) -> bool:
        completed = subprocess.run(
            [str(self.git), *args], cwd=self.cwd, env=self.env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, check=False,
        )
        if completed.returncode:
            return False
        if porcelain_flag is None:
            return True
        return any(
            line.startswith(porcelain_flag + "\t")
            for line in completed.stdout.decode("utf-8", "replace").splitlines()
        )

    def tree_entries(self, revision: str) -> Mapping[str, TreeEntry]:
        result: dict[str, TreeEntry] = {}
        for line in self._run("ls-tree", "-r", "-z", revision).split("\0"):
            if not line:
                continue
            meta, path = line.split("\t", 1)
            mode, kind, oid = meta.split()
            result[path] = (mode, kind, oid)
        return result

    def parents(self, revision: str) -> tuple[str, ...]:
        return tuple(self._run("show", "-s", "--format=%P", revision).split())

    def blob_bytes(self, oid: str) -> bytes:
        return subprocess.run([str(self.git), "cat-file", "blob", oid], cwd=self.cwd, env=self.env, stdout=subprocess.PIPE, check=True).stdout

    def gitlink_at(self, revision: str) -> str:
        return self.tree_entries(revision)["cosmos-framework"][2]

    def create_detached_commit(self, parent: str, blobs: Mapping[str, bytes]) -> str:
        self._run("read-tree", parent)
        for path, raw in blobs.items():
            oid = self._run("hash-object", "-w", "--stdin", input=raw)
            self._run("update-index", "--add", "--cacheinfo", f"100644,{oid},{path}")
        tree = self._run("write-tree")
        return self._run("commit-tree", tree, "-p", parent, input=self.metadata.message.encode())

    def local_ref(self, ref: str) -> str | None:
        value = self._run("rev-parse", "--verify", "-q", ref, check=False)
        return value or None

    def remote_ref(self, ref: str) -> str | None:
        value = self._run("ls-remote", self.remote, ref)
        return value.split()[0] if value else None

    def cas_create_local(self, ref: str, revision: str) -> bool:
        return self._mutation_succeeded("update-ref", ref, revision, "0" * 40) and self.local_ref(ref) == revision

    def cas_create_remote(self, ref: str, revision: str) -> bool:
        return self._mutation_succeeded("push", "--porcelain", f"--force-with-lease={ref}:", self.remote, f"{revision}:{ref}", porcelain_flag="*") and self.remote_ref(ref) == revision

    def cas_delete_local(self, ref: str, revision: str) -> bool:
        return self._mutation_succeeded("update-ref", "-d", ref, revision) and self.local_ref(ref) is None

    def cas_delete_remote(self, ref: str, revision: str) -> bool:
        return self._mutation_succeeded("push", "--porcelain", f"--force-with-lease={ref}:{revision}", self.remote, f":{ref}", porcelain_flag="-") and self.remote_ref(ref) is None


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="immutable authority-root materialization adapter"
    )
    parser.add_argument("--selection-fd", type=int, required=True)
    parser.add_argument("--config-fd", type=int, required=True)
    parser.add_argument("--formal-root", required=True)
    parser.add_argument("--child-gitlink", required=True)
    parser.add_argument("--selection-raw-sha256", required=True)
    parser.add_argument("--config-raw-sha256", required=True)
    parser.add_argument("--cwd", type=Path, required=True)
    parser.add_argument("--remote", required=True)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--evidence-path", type=Path, required=True)
    parser.add_argument("--git", type=Path, required=True)
    parser.add_argument("--git-raw-sha256", required=True)
    parser.add_argument("--git-version", required=True)
    parser.add_argument("--interpreter", type=Path, required=True)
    parser.add_argument("--interpreter-raw-sha256", required=True)
    parser.add_argument("--interpreter-version", required=True)
    for name in ("adapter", "authority-module"):
        parser.add_argument(f"--{name}-path", required=True)
        parser.add_argument(f"--{name}-blob-oid", required=True)
        parser.add_argument(f"--{name}-raw-sha256", required=True)
    parser.add_argument("--author-name", required=True)
    parser.add_argument("--author-email", required=True)
    parser.add_argument("--author-date", required=True)
    parser.add_argument("--committer-name", required=True)
    parser.add_argument("--committer-email", required=True)
    parser.add_argument("--committer-date", required=True)
    parser.add_argument("--commit-message", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run only an explicitly-identified authority-root invocation."""
    actual_argv = tuple(sys.argv[1:] if argv is None else argv)
    args = _parser().parse_args(actual_argv)
    request = request_from_input_fds(
        args.formal_root,
        args.child_gitlink,
        args.selection_fd,
        args.config_fd,
        args.selection_raw_sha256,
        args.config_raw_sha256,
    )
    metadata = CommitMetadata(
        args.author_name,
        args.author_email,
        args.author_date,
        args.committer_name,
        args.committer_email,
        args.committer_date,
        args.commit_message,
    )
    transaction = NativeAuthorityGit(args.git, args.cwd, args.remote, args.index, metadata)
    invocation = AuthorityAdapterInvocation(
        request,
        args.selection_raw_sha256,
        args.config_raw_sha256,
        ModuleIdentity(args.adapter_path, args.adapter_blob_oid, args.adapter_raw_sha256),
        ModuleIdentity(
            args.authority_module_path,
            args.authority_module_blob_oid,
            args.authority_module_raw_sha256,
        ),
        ExecutableIdentity(
            args.interpreter,
            args.interpreter_raw_sha256,
            args.interpreter_version,
        ),
        ExecutableIdentity(args.git, args.git_raw_sha256, args.git_version),
        args.evidence_path,
        sha256_digest(json.dumps(actual_argv, separators=(",", ":")).encode()),
    )
    print(run_authority_cli(invocation, transaction, args.cwd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
