"""Synthetic CPU/static authority-root materialization under injected Git seams."""

from __future__ import annotations

import json
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Protocol

from tools.g0.audit_r09_b_ttt_root_gitlink_authority import (
    AuditFailure,
    validate_config,
)
from tools.psm_wma.immutable_source_collection import (
    AUTHORITY_REF,
    COLLECTION_PATHS,
    SELECTION_PATH,
    CollectionError,
    TreeEntry,
    canonical_json_bytes,
    git_blob_oid,
    sha256_digest,
    validated_git_tree,
)


class AuthorityRootError(CollectionError):
    pass


class RollbackIncomplete(AuthorityRootError):
    def __init__(self) -> None:
        super().__init__("ROLLBACK_INCOMPLETE")


class AuthorityGitTransaction(Protocol):
    def tree_entries(self, revision: str) -> Mapping[str, TreeEntry]: ...
    def parents(self, revision: str) -> tuple[str, ...]: ...
    def blob_bytes(self, oid: str) -> bytes: ...
    def gitlink_at(self, revision: str) -> str: ...
    def create_detached_commit(
        self, parent: str, blobs: Mapping[str, bytes]
    ) -> str: ...
    def local_ref(self, ref: str) -> str | None: ...
    def remote_ref(self, ref: str) -> str | None: ...
    def cas_create_local(self, ref: str, revision: str) -> bool: ...
    def cas_create_remote(self, ref: str, revision: str) -> bool: ...
    def cas_delete_local(self, ref: str, revision: str) -> bool: ...
    def cas_delete_remote(self, ref: str, revision: str) -> bool: ...


class _NonSerializable:
    def __copy__(self):
        raise AuthorityRootError("typed authority object 不可复制")

    def __deepcopy__(self, memo):
        raise AuthorityRootError("typed authority object 不可复制")

    def __reduce__(self):
        raise AuthorityRootError("typed authority object 不可序列化")


@dataclass(frozen=True)
class AuthorityRequest(_NonSerializable):
    materialization_formal_root: str
    expected_child_gitlink: str
    selection_raw: bytes
    config_raw: bytes


@dataclass(frozen=True)
class AuthorityCandidate(_NonSerializable):
    revision: str


class AuthorityBinding:
    __slots__ = ("_request", "_candidate", "_mapping", "_used")

    def __init__(
        self,
        request: AuthorityRequest,
        candidate: AuthorityCandidate,
        mapping: Mapping[str, str],
        token: object,
    ) -> None:
        if token is not _CAPABILITY_TOKEN:
            raise AuthorityRootError("verified capability 不可重建")
        self._request, self._candidate = request, candidate
        self._mapping = MappingProxyType(dict(mapping))
        self._used = False

    def as_mapping(self) -> dict[str, str]:
        return dict(self._mapping)

    def __copy__(self):
        raise AuthorityRootError("verified capability 不可复制")

    def __deepcopy__(self, memo):
        raise AuthorityRootError("verified capability 不可复制")

    def __reduce__(self):
        raise AuthorityRootError("verified capability 不可序列化")


@dataclass(frozen=True)
class PublicationWitness(_NonSerializable):
    revision: str
    local_created: bool
    remote_created: bool


_CAPABILITY_TOKEN = object()


def _sha1(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 40
        and all(c in "0123456789abcdef" for c in value)
    )


def _selection(raw: bytes) -> None:
    try:
        value = json.loads(raw)
        if (
            not isinstance(value, dict)
            or set(value) != {"schema", "source_kind", "entries"}
            or value["schema"] != "immutable_source_selection_request_v1"
            or value["source_kind"] != "checkpoint_source_manifest_v1"
            or canonical_json_bytes(value) != raw
            or not isinstance(value["entries"], list)
            or not value["entries"]
        ):
            raise AuthorityRootError("selection schema/canonical bytes 无效")
        paths = []
        for ordinal, entry in enumerate(value["entries"]):
            if (
                not isinstance(entry, dict)
                or set(entry) != {"ordinal", "relative_path"}
                or type(entry["ordinal"]) is not int
                or entry["ordinal"] != ordinal
            ):
                raise AuthorityRootError("selection ordinal/key 无效")
            path = entry["relative_path"]
            if (
                not isinstance(path, str)
                or "\0" in path
                or any(part in ("", ".", "..") for part in path.split("/"))
            ):
                raise AuthorityRootError("selection 路径不规范")
            paths.append(path)
        if paths != sorted(set(paths), key=lambda p: p.encode()):
            raise AuthorityRootError("selection 路径顺序或唯一性漂移")
    except (ValueError, TypeError, UnicodeError, AuditFailure) as exc:
        raise AuthorityRootError("selection 无效") from exc


def _config(raw: bytes) -> None:
    try:
        value, _ = validate_config(json.loads(raw))
        if canonical_json_bytes(value) != raw:
            raise AuthorityRootError("config bytes 非canonical")
    except (ValueError, TypeError, UnicodeError, AuditFailure) as exc:
        raise AuthorityRootError("config 无效") from exc


def _verify_request(request: AuthorityRequest) -> None:
    if not _sha1(request.materialization_formal_root) or not _sha1(
        request.expected_child_gitlink
    ):
        raise AuthorityRootError("request revision 无效")
    if not isinstance(request.selection_raw, bytes) or not isinstance(
        request.config_raw, bytes
    ):
        raise AuthorityRootError("request raw input 必须为bytes")
    _selection(request.selection_raw)
    _config(request.config_raw)


def prepare_candidate(
    request: AuthorityRequest, git: AuthorityGitTransaction
) -> AuthorityCandidate:
    _verify_request(request)
    parent = request.materialization_formal_root
    before = validated_git_tree(git, parent)
    if SELECTION_PATH in before or COLLECTION_PATHS[1] in before:
        raise AuthorityRootError("formal root 已含fixed path")
    _formal_gitlink(before, request.expected_child_gitlink)
    revision = git.create_detached_commit(
        parent,
        {
            SELECTION_PATH: request.selection_raw,
            COLLECTION_PATHS[1]: request.config_raw,
        },
    )
    _candidate_mapping(request, revision, git)
    return AuthorityCandidate(revision)


def verify_candidate(
    request: AuthorityRequest,
    candidate: AuthorityCandidate,
    git: AuthorityGitTransaction,
) -> AuthorityBinding:
    _verify_request(request)
    mapping = _candidate_mapping(request, candidate.revision, git)
    return AuthorityBinding(request, candidate, mapping, _CAPABILITY_TOKEN)


def _formal_gitlink(tree: Mapping[str, TreeEntry], expected: str) -> None:
    if tree.get("cosmos-framework") != ("160000", "commit", expected):
        raise AuthorityRootError("formal root Gitlink结构漂移")


def _candidate_mapping(
    request: AuthorityRequest, revision: str, git: AuthorityGitTransaction
) -> dict[str, str]:
    parent = request.materialization_formal_root
    if not _sha1(revision) or git.parents(revision) != (parent,):
        raise AuthorityRootError("candidate必须精确单parent")
    before, after = validated_git_tree(git, parent), validated_git_tree(git, revision)
    paths = (SELECTION_PATH, COLLECTION_PATHS[1])
    if any(path in before for path in paths):
        raise AuthorityRootError("formal root 已含fixed path")
    changed = {p for p in set(before) | set(after) if before.get(p) != after.get(p)}
    if changed != set(paths) or any(
        after.get(p, ())[:2] != ("100644", "blob") for p in paths
    ):
        raise AuthorityRootError("candidate delta 漂移")
    _formal_gitlink(before, request.expected_child_gitlink)
    raws = (request.selection_raw, request.config_raw)
    for path, raw in zip(paths, raws):
        oid = after[path][2]
        observed = git.blob_bytes(oid)
        if observed != raw or git_blob_oid(observed) != oid:
            raise AuthorityRootError("candidate blob漂移")
    mapping = {
        "root_revision": revision,
        "selection_path": SELECTION_PATH,
        "selection_blob_native_oid": after[SELECTION_PATH][2],
        "selection_raw_sha256": sha256_digest(raws[0]),
        "config_path": COLLECTION_PATHS[1],
        "config_blob_native_oid": after[COLLECTION_PATHS[1]][2],
        "config_raw_sha256": sha256_digest(raws[1]),
    }
    return mapping


def _rollback(
    git: AuthorityGitTransaction,
    revision: str,
    local_created: bool,
    remote_created: bool,
) -> None:
    complete = True
    for endpoint, created in (("remote", remote_created), ("local", local_created)):
        if not created:
            continue
        try:
            current = getattr(git, endpoint + "_ref")(AUTHORITY_REF)
            if current != revision or not getattr(git, "cas_delete_" + endpoint)(
                AUTHORITY_REF, revision
            ):
                complete = False
        except Exception:
            complete = False
    local_absent = remote_absent = False
    try:
        local_absent = git.local_ref(AUTHORITY_REF) is None
    except Exception:
        complete = False
    try:
        remote_absent = git.remote_ref(AUTHORITY_REF) is None
    except Exception:
        complete = False
    complete = complete and local_absent and remote_absent
    if not complete:
        raise RollbackIncomplete()


def _observe_refs(git: AuthorityGitTransaction) -> tuple[str | None, str | None]:
    values = []
    errors = []
    for endpoint in ("local", "remote"):
        try:
            values.append(getattr(git, endpoint + "_ref")(AUTHORITY_REF))
        except Exception as exc:
            values.append(None)
            errors.append(exc)
    if errors:
        raise AuthorityRootError("fixed ref observation失败") from errors[0]
    return values[0], values[1]


def publish_candidate(
    request: AuthorityRequest,
    candidate: AuthorityCandidate,
    binding: AuthorityBinding,
    git: AuthorityGitTransaction,
) -> PublicationWitness:
    if (
        binding._request is not request
        or binding._candidate is not candidate
        or binding._used
    ):
        raise AuthorityRootError("verified capability identity/replay失败")
    binding._used = True
    expected = verify_candidate(request, candidate, git).as_mapping()
    if binding.as_mapping() != expected:
        raise AuthorityRootError("verified binding漂移")
    revision = candidate.revision
    local_created = remote_created = False
    try:
        local_before, remote_before = _observe_refs(git)
        if local_before is not None or remote_before is not None:
            raise AuthorityRootError("fixed ref 必须预先absent")
        if not git.cas_create_local(AUTHORITY_REF, revision):
            raise AuthorityRootError("local CAS conflict")
        local_created = True
        if not git.cas_create_remote(AUTHORITY_REF, revision):
            raise AuthorityRootError("remote CAS conflict")
        remote_created = True
        local_after, remote_after = _observe_refs(git)
        if local_after != revision or remote_after != revision:
            raise AuthorityRootError("post-CAS ref drift")
        if verify_candidate(request, candidate, git).as_mapping() != expected:
            raise AuthorityRootError("committed binding drift")
        return PublicationWitness(revision, True, True)
    except Exception as error:
        try:
            _rollback(git, revision, local_created, remote_created)
        except RollbackIncomplete:
            raise
        raise error
