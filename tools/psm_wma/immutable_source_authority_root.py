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
    _blob_oid,
    _canonical,
    _digest,
    _tree,
)


class AuthorityRootError(CollectionError):
    pass


class RollbackIncomplete(AuthorityRootError):
    def __init__(self) -> None:
        super().__init__("ROLLBACK_INCOMPLETE")


class AuthorityGitTransaction(Protocol):
    def tree_entries(self, revision: str) -> Mapping[str, TreeEntry]: ...
    def parent(self, revision: str) -> str: ...
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


@dataclass(frozen=True)
class AuthorityRequest:
    materialization_formal_root: str
    expected_child_gitlink: str
    selection_raw: bytes
    config_raw: bytes


@dataclass(frozen=True)
class AuthorityCandidate:
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
class PublicationWitness:
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
            or _canonical(value) != raw
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
        if _canonical(value) != raw:
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
    before = _tree(git, parent)
    if SELECTION_PATH in before or COLLECTION_PATHS[1] in before:
        raise AuthorityRootError("formal root 已含fixed path")
    if git.gitlink_at(parent) != request.expected_child_gitlink:
        raise AuthorityRootError("formal root Gitlink 漂移")
    revision = git.create_detached_commit(
        parent,
        {
            SELECTION_PATH: request.selection_raw,
            COLLECTION_PATHS[1]: request.config_raw,
        },
    )
    if not _sha1(revision):
        raise AuthorityRootError("candidate revision 无效")
    return AuthorityCandidate(revision)


def verify_candidate(
    request: AuthorityRequest,
    candidate: AuthorityCandidate,
    git: AuthorityGitTransaction,
) -> AuthorityBinding:
    _verify_request(request)
    revision, parent = candidate.revision, request.materialization_formal_root
    if not _sha1(revision) or git.parent(revision) != parent:
        raise AuthorityRootError("candidate parent 漂移")
    before, after = _tree(git, parent), _tree(git, revision)
    paths = (SELECTION_PATH, COLLECTION_PATHS[1])
    changed = {p for p in set(before) | set(after) if before.get(p) != after.get(p)}
    if changed != set(paths) or any(
        after.get(p, ())[:2] != ("100644", "blob") for p in paths
    ):
        raise AuthorityRootError("candidate delta 漂移")
    if git.gitlink_at(parent) != request.expected_child_gitlink:
        raise AuthorityRootError("formal root Gitlink 漂移")
    raws = (request.selection_raw, request.config_raw)
    for path, raw in zip(paths, raws):
        oid = after[path][2]
        observed = git.blob_bytes(oid)
        if observed != raw or _blob_oid(observed) != oid:
            raise AuthorityRootError("candidate blob漂移")
    mapping = {
        "root_revision": revision,
        "selection_path": SELECTION_PATH,
        "selection_blob_native_oid": after[SELECTION_PATH][2],
        "selection_raw_sha256": _digest(raws[0]),
        "config_path": COLLECTION_PATHS[1],
        "config_blob_native_oid": after[COLLECTION_PATHS[1]][2],
        "config_raw_sha256": _digest(raws[1]),
    }
    return AuthorityBinding(request, candidate, mapping, _CAPABILITY_TOKEN)


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
    try:
        complete = (
            complete
            and git.local_ref(AUTHORITY_REF) is None
            and git.remote_ref(AUTHORITY_REF) is None
        )
    except Exception:
        complete = False
    if not complete:
        raise RollbackIncomplete()


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
        if (
            git.local_ref(AUTHORITY_REF) is not None
            or git.remote_ref(AUTHORITY_REF) is not None
        ):
            raise AuthorityRootError("fixed ref 必须预先absent")
        if not git.cas_create_local(AUTHORITY_REF, revision):
            raise AuthorityRootError("local CAS conflict")
        local_created = True
        if not git.cas_create_remote(AUTHORITY_REF, revision):
            raise AuthorityRootError("remote CAS conflict")
        remote_created = True
        if (
            git.local_ref(AUTHORITY_REF) != revision
            or git.remote_ref(AUTHORITY_REF) != revision
        ):
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
