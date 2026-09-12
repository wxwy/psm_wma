"""Synthetic CPU/static authority-root materialization under injected Git seams."""

from __future__ import annotations

import fcntl
import json
import os
import hashlib
import stat
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Callable, Mapping, Protocol

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
    def __init__(self, outcome: "RollbackOutcome | None" = None) -> None:
        super().__init__("ROLLBACK_INCOMPLETE")
        self.outcome = outcome


@dataclass(frozen=True)
class RollbackOutcome:
    entered: bool
    required: bool
    remote_delete_attempted: bool
    remote_delete_succeeded: bool
    local_delete_attempted: bool
    local_delete_succeeded: bool
    final_local: str | None
    final_remote: str | None
    final_local_error: str | None
    final_remote_error: str | None
    complete: bool


@dataclass(frozen=True)
class PublicationFailure:
    phase: str
    error: BaseException
    local_created: bool
    remote_created: bool
    rollback: RollbackOutcome | None
    pre_local: str | None
    pre_remote: str | None
    post_local: str | None
    post_remote: str | None
    pre_local_error: str | None
    pre_remote_error: str | None
    post_local_error: str | None
    post_remote_error: str | None
    binding_reverified: bool
    cleanup_incomplete: bool


class EvidenceCleanupIncomplete(AuthorityRootError):
    """A writer cannot prove that pre-commit evidence cleanup completed."""


def _unlink_exact_regular(path: Path, identity: tuple[int, int]) -> bool:
    """Remove only an identity-bound regular file via a private same-directory handoff."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    if not stat.S_ISREG(info.st_mode) or (info.st_dev, info.st_ino) != identity:
        return False
    parking = Path(tempfile.mkdtemp(prefix=f".{path.name}.unlink-", dir=path.parent))
    parked = parking / "owned"
    restored = False
    try:
        os.rename(path, parked)
        parked_info = parked.lstat()
        if (
            not stat.S_ISREG(parked_info.st_mode)
            or (parked_info.st_dev, parked_info.st_ino) != identity
        ):
            try:
                path.lstat()
            except FileNotFoundError:
                os.rename(parked, path)
                restored = True
            return False
        os.unlink(parked)
        return True
    finally:
        if parked.exists() or parked.is_symlink():
            if not restored:
                raise AuthorityRootError("evidence owned path 无法安全恢复")
        try:
            parking.rmdir()
        except OSError:
            pass


@contextmanager
def _evidence_guard_lock(evidence_path: Path, *, exclusive: bool):
    descriptor = os.open(
        evidence_path,
        os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
    )
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise AuthorityRootError("evidence guard lock 必须绑定regular evidence FD")
        fcntl.flock(descriptor, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        yield descriptor, (info.st_dev, info.st_ino)
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _commit_exact_guard(path: Path, identity: tuple[int, int]) -> bool:
    """Move a guard only while writer/verifier serialization is held."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    if not stat.S_ISREG(info.st_mode) or (info.st_dev, info.st_ino) != identity:
        return False
    parking = Path(tempfile.mkdtemp(prefix=f".{path.name}.commit-", dir=path.parent))
    parked = parking / "owned"

    def restore_if_public_absent() -> bool:
        if not parked.exists() and not parked.is_symlink():
            return False
        if path.exists() or path.is_symlink():
            return False
        try:
            os.rename(parked, path)
        except OSError:
            return False
        return True

    try:
        os.rename(path, parked)
        parked_info = parked.lstat()
        if (
            not stat.S_ISREG(parked_info.st_mode)
            or (parked_info.st_dev, parked_info.st_ino) != identity
        ):
            restore_if_public_absent()
            return False
        if path.exists() or path.is_symlink():
            return False
        try:
            os.unlink(parked)
        except OSError:
            restore_if_public_absent()
            return False
        return True
    except OSError:
        restore_if_public_absent()
        return False
    finally:
        try:
            parking.rmdir()
        except OSError:
            pass


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


_CAPABILITY_TOKEN = object()


class _FinalizerActivation:
    __slots__ = ("active",)

    def __init__(self) -> None:
        self.active = True


@dataclass(frozen=True)
class _AuthorityTerminalState:
    accepted: bool
    rollback_enabled: bool
    preserve_refs: bool
    witness_returnable: bool


_PENDING_TERMINAL_STATE = _AuthorityTerminalState(
    accepted=False,
    rollback_enabled=True,
    preserve_refs=False,
    witness_returnable=False,
)
_ACCEPTED_TERMINAL_STATE = _AuthorityTerminalState(
    accepted=True,
    rollback_enabled=False,
    preserve_refs=True,
    witness_returnable=True,
)


class _AuthorityTerminalCell:
    __slots__ = ("state",)

    def __init__(self) -> None:
        self.state = _PENDING_TERMINAL_STATE


class _AcceptedPass(_NonSerializable):
    __slots__ = ("_witness", "_activation", "_terminal", "_token")

    def __init__(self, witness: "PublicationWitness", token: object) -> None:
        if token is not _CAPABILITY_TOKEN:
            raise AuthorityRootError("accepted pass 不可重建")
        self._witness = witness
        self._activation = witness._activation
        self._terminal = witness._terminal
        self._token = token

    def consume(self, witness: "PublicationWitness") -> None:
        if (
            witness is not self._witness
            or not self._activation.active
            or not self._terminal.state.accepted
        ):
            raise AuthorityRootError("accepted pass 无效")


class PublicationWitness(_NonSerializable):
    __slots__ = (
        "revision", "local_created", "remote_created", "_request", "_candidate",
        "_binding", "_activation", "_terminal", "_token",
    )

    def __init__(
        self,
        revision: str,
        request: AuthorityRequest,
        candidate: AuthorityCandidate,
        binding: AuthorityBinding,
        activation: _FinalizerActivation,
        terminal: _AuthorityTerminalCell,
        token: object,
    ) -> None:
        if token is not _CAPABILITY_TOKEN:
            raise AuthorityRootError("publication witness 不可重建")
        self.revision = revision
        self.local_created = self.remote_created = True
        self._request, self._candidate, self._binding = request, candidate, binding
        self._activation, self._terminal = activation, terminal
        self._token = token


class EvidenceCommit(_NonSerializable):
    __slots__ = (
        "_witness", "_activation", "_terminal", "_sealed", "_guard",
        "_evidence_path", "_evidence_sha256", "_guard_identity",
        "_evidence_identity", "_record_sha256", "_pre_unlink", "_token",
    )

    def __init__(
        self,
        witness: PublicationWitness,
        pre_unlink: Callable[[], None],
        accepted_pass: _AcceptedPass,
        token: object,
    ) -> None:
        if token is not _CAPABILITY_TOKEN:
            raise AuthorityRootError("evidence commit 不可重建")
        self._witness, self._activation = witness, witness._activation
        self._terminal, self._token = witness._terminal, token
        self._accepted_pass = accepted_pass
        self._sealed = False
        self._guard: Path | None = None
        self._evidence_path: Path | None = None
        self._evidence_sha256: str | None = None
        self._guard_identity: tuple[int, int] | None = None
        self._evidence_identity: tuple[int, int] | None = None
        self._record_sha256: str | None = None
        self._pre_unlink = pre_unlink

    @property
    def committed(self) -> bool:
        return self._terminal.state.accepted

    def seal_for_guard(
        self,
        witness: PublicationWitness,
        guard: Path,
        evidence_path: Path,
        evidence_sha256: str,
    ) -> None:
        if (
            self._sealed
            or self.committed
            or witness is not self._witness
            or witness._activation is not self._activation
            or not self._activation.active
            or witness._token is not _CAPABILITY_TOKEN
            or not isinstance(guard, Path)
            or not isinstance(evidence_path, Path)
            or guard != evidence_path.with_name(evidence_path.name + ".pending")
            or not isinstance(evidence_sha256, str)
            or len(evidence_sha256) != 64
            or any(char not in "0123456789abcdef" for char in evidence_sha256)
        ):
            raise AuthorityRootError("evidence commit seal 无效")
        try:
            guard_info = guard.lstat()
            evidence_info = evidence_path.lstat()
            descriptor = os.open(evidence_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
            try:
                opened_info = os.fstat(descriptor)
                raw = b""
                remaining = opened_info.st_size
                while remaining:
                    chunk = os.read(descriptor, remaining)
                    if not chunk:
                        raise OSError("evidence truncated")
                    raw += chunk
                    remaining -= len(chunk)
            finally:
                os.close(descriptor)
            value = json.loads(raw)
        except (OSError, ValueError, TypeError) as error:
            raise AuthorityRootError("evidence commit seal evidence 无效") from error
        if (
            not stat.S_ISREG(guard_info.st_mode)
            or not stat.S_ISREG(evidence_info.st_mode)
            or not stat.S_ISREG(opened_info.st_mode)
            or (guard_info.st_dev, guard_info.st_ino)
            != (guard.lstat().st_dev, guard.lstat().st_ino)
            or (evidence_info.st_dev, evidence_info.st_ino)
            != (opened_info.st_dev, opened_info.st_ino)
            or not isinstance(value, dict)
            or value.get("evidence_sha256") != evidence_sha256
        ):
            raise AuthorityRootError("evidence commit seal guard/digest 无效")
        self._guard, self._evidence_path = guard, evidence_path
        self._evidence_sha256 = evidence_sha256
        self._guard_identity = (guard_info.st_dev, guard_info.st_ino)
        self._evidence_identity = (evidence_info.st_dev, evidence_info.st_ino)
        self._record_sha256 = hashlib.sha256(raw).hexdigest()
        self._sealed = True

    def consume_by_unlink(self) -> None:
        if (
            not self._sealed
            or self.committed
            or self._guard is None
            or self._evidence_path is None
            or self._guard_identity is None
            or self._evidence_identity is None
            or self._record_sha256 is None
            or not self._activation.active
        ):
            raise AuthorityRootError("evidence commit 未seal或已消费")
        with _evidence_guard_lock(self._evidence_path, exclusive=True) as (
            descriptor,
            locked_identity,
        ):
            try:
                guard_info = self._guard.lstat()
                evidence_info = self._evidence_path.lstat()
                chunks: list[bytes] = []
                remaining = os.fstat(descriptor).st_size
                while remaining:
                    chunk = os.read(descriptor, remaining)
                    if not chunk:
                        raise OSError("evidence truncated")
                    chunks.append(chunk)
                    remaining -= len(chunk)
                raw = b"".join(chunks)
            except OSError as error:
                raise AuthorityRootError("evidence commit identity 无效") from error
            if (
                not stat.S_ISREG(guard_info.st_mode)
                or not stat.S_ISREG(evidence_info.st_mode)
                or (guard_info.st_dev, guard_info.st_ino) != self._guard_identity
                or (evidence_info.st_dev, evidence_info.st_ino) != self._evidence_identity
                or locked_identity != self._evidence_identity
                or hashlib.sha256(raw).hexdigest() != self._record_sha256
            ):
                raise AuthorityRootError("evidence commit identity/digest 漂移")
            try:
                self._pre_unlink()
            except Exception as error:
                raise AuthorityRootError("evidence commit fixed ref 漂移") from error
            if not _commit_exact_guard(self._guard, self._guard_identity):
                raise AuthorityRootError("evidence commit guard identity 漂移")
            self._terminal.state = _ACCEPTED_TERMINAL_STATE
            self._accepted_pass.consume(self._witness)


class PostCommitFinalizerError(AuthorityRootError):
    pass


class _PreCommitFinalizerError(AuthorityRootError):
    def __init__(self, error: BaseException | None) -> None:
        super().__init__("FINALIZER_EXCEPTION" if error else "FINALIZER_DID_NOT_COMMIT")
        self.callback_error = error


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


def validate_request(request: AuthorityRequest) -> None:
    """Validate an authority request without creating candidate objects or refs."""
    _verify_request(request)


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
) -> RollbackOutcome:
    complete = True
    remote_delete_attempted = remote_delete_succeeded = False
    local_delete_attempted = local_delete_succeeded = False
    for endpoint, created in (("remote", remote_created), ("local", local_created)):
        if not created:
            continue
        if endpoint == "remote":
            remote_delete_attempted = True
        else:
            local_delete_attempted = True
        try:
            current = getattr(git, endpoint + "_ref")(AUTHORITY_REF)
            succeeded = current == revision and getattr(git, "cas_delete_" + endpoint)(
                AUTHORITY_REF, revision
            )
            if endpoint == "remote":
                remote_delete_succeeded = succeeded
            else:
                local_delete_succeeded = succeeded
            if not succeeded:
                complete = False
        except Exception:
            complete = False
    local_absent = remote_absent = False
    final_local = final_remote = None
    final_local_error = final_remote_error = None
    try:
        final_local = git.local_ref(AUTHORITY_REF)
        local_absent = final_local is None
    except Exception as error:
        final_local_error = type(error).__name__.upper()
        complete = False
    try:
        final_remote = git.remote_ref(AUTHORITY_REF)
        remote_absent = final_remote is None
    except Exception as error:
        final_remote_error = type(error).__name__.upper()
        complete = False
    complete = complete and local_absent and remote_absent
    outcome = RollbackOutcome(
        entered=True,
        required=local_created or remote_created,
        remote_delete_attempted=remote_delete_attempted,
        remote_delete_succeeded=remote_delete_succeeded,
        local_delete_attempted=local_delete_attempted,
        local_delete_succeeded=local_delete_succeeded,
        final_local=final_local,
        final_remote=final_remote,
        final_local_error=final_local_error,
        final_remote_error=final_remote_error,
        complete=complete,
    )
    if not complete:
        raise RollbackIncomplete(outcome)
    return outcome


def _observe_refs(
    git: AuthorityGitTransaction,
) -> tuple[str | None, str | None, str | None, str | None]:
    values: list[str | None] = []
    errors: list[str | None] = []
    for endpoint in ("local", "remote"):
        try:
            values.append(getattr(git, endpoint + "_ref")(AUTHORITY_REF))
        except Exception as exc:
            values.append(None)
            errors.append(type(exc).__name__.upper())
        else:
            errors.append(None)
    return values[0], values[1], errors[0], errors[1]


def publish_candidate(
    request: AuthorityRequest,
    candidate: AuthorityCandidate,
    binding: AuthorityBinding,
    git: AuthorityGitTransaction,
    *,
    finalizer: Callable[[PublicationWitness, EvidenceCommit], object] | None = None,
    failure_reporter: Callable[[PublicationFailure], None] | None = None,
) -> PublicationWitness:
    if (
        binding._request is not request
        or binding._candidate is not candidate
        or binding._used
    ):
        raise AuthorityRootError("verified capability identity/replay失败")
    if finalizer is None:
        raise AuthorityRootError("publication 必须提供accepted pass finalizer")
    binding._used = True
    expected = verify_candidate(request, candidate, git).as_mapping()
    if binding.as_mapping() != expected:
        raise AuthorityRootError("verified binding漂移")
    revision = candidate.revision
    local_created = remote_created = False
    witness: PublicationWitness | None = None
    post_commit_error: BaseException | None = None
    phase = "pre_publication"
    pre_local = pre_remote = post_local = post_remote = None
    pre_local_error = pre_remote_error = post_local_error = post_remote_error = None
    binding_reverified = False
    try:
        local_before, remote_before, local_error, remote_error = _observe_refs(git)
        pre_local, pre_remote = local_before, remote_before
        pre_local_error, pre_remote_error = local_error, remote_error
        if local_error is not None or remote_error is not None:
            raise AuthorityRootError("fixed ref pre-publication observation失败")
        if local_before is not None or remote_before is not None:
            raise AuthorityRootError("fixed ref 必须预先absent")
        phase = "local_cas"
        if not git.cas_create_local(AUTHORITY_REF, revision):
            raise AuthorityRootError("local CAS conflict")
        local_created = True
        phase = "remote_cas"
        if not git.cas_create_remote(AUTHORITY_REF, revision):
            raise AuthorityRootError("remote CAS conflict")
        remote_created = True
        phase = "post_publication"
        local_after, remote_after, local_error, remote_error = _observe_refs(git)
        post_local, post_remote = local_after, remote_after
        post_local_error, post_remote_error = local_error, remote_error
        if local_error is not None or remote_error is not None:
            raise AuthorityRootError("fixed ref post-publication observation失败")
        if local_after != revision or remote_after != revision:
            raise AuthorityRootError("post-CAS ref drift")
        phase = "binding_reverify"
        if verify_candidate(request, candidate, git).as_mapping() != expected:
            raise AuthorityRootError("committed binding drift")
        binding_reverified = True
        activation = _FinalizerActivation()
        terminal = _AuthorityTerminalCell()
        witness = PublicationWitness(
            revision, request, candidate, binding, activation, terminal, _CAPABILITY_TOKEN
        )
        phase = "evidence_write"
        def pre_unlink() -> None:
            local, remote, local_error, remote_error = _observe_refs(git)
            if (
                local_error is not None or remote_error is not None
                or local != revision or remote != revision
            ):
                raise AuthorityRootError("evidence commit fixed ref drift")

        accepted_pass = _AcceptedPass(witness, _CAPABILITY_TOKEN)
        commit = EvidenceCommit(witness, pre_unlink, accepted_pass, _CAPABILITY_TOKEN)
        callback_error: BaseException | None = None
        try:
            finalizer(witness, commit)
        except BaseException as error:
            callback_error = error
        finally:
            activation.active = False
        if not commit.committed:
            raise _PreCommitFinalizerError(callback_error)
        post_commit_error = callback_error
    except Exception as error:
        callback_error = (
            error.callback_error
            if isinstance(error, _PreCommitFinalizerError)
            else error
        )
        cleanup_incomplete = isinstance(callback_error, EvidenceCleanupIncomplete)
        outcome: RollbackOutcome | None = None
        try:
            outcome = _rollback(git, revision, local_created, remote_created)
        except RollbackIncomplete as rollback_error:
            outcome = rollback_error.outcome
            if failure_reporter is not None:
                failure_reporter(PublicationFailure(
                    phase, error, local_created, remote_created, outcome,
                    pre_local, pre_remote, post_local, post_remote,
                    pre_local_error, pre_remote_error, post_local_error,
                    post_remote_error, binding_reverified, cleanup_incomplete,
                ))
            raise
        if failure_reporter is not None:
            failure_reporter(PublicationFailure(
                phase, error, local_created, remote_created, outcome,
                pre_local, pre_remote, post_local, post_remote,
                pre_local_error, pre_remote_error, post_local_error,
                post_remote_error, binding_reverified, cleanup_incomplete,
            ))
        if isinstance(callback_error, EvidenceCleanupIncomplete):
            raise RollbackIncomplete() from error
        if isinstance(error, _PreCommitFinalizerError) and error.callback_error:
            raise error.callback_error
        raise error
    if post_commit_error is not None:
        raise PostCommitFinalizerError("post-commit finalizer failure") from post_commit_error
    if witness is None:
        raise AuthorityRootError("publication witness 缺失")
    return witness
