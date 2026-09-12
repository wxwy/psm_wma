"""CPU/static-only immutable-source collection contract.

This module deliberately accepts injected dependencies.  It never opens a real
source root, invokes Git, or writes evidence outside the supplied test sink.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Mapping, Protocol


SCHEMA = "immutable_source_collection_execution_evidence_v1"
SOURCE_PATHS = ("checkpoint", "config", "manifest", "metadata", "state")


class CollectionError(ValueError):
    """The frozen collection contract cannot be established."""


class GitTransaction(Protocol):
    def resolve(self, revision: str) -> str: ...


class RootFdOpener(Protocol):
    def read_regular(self, relative_path: str) -> bytes: ...


class EvidenceSink(Protocol):
    def emit(self, record: Mapping[str, object]) -> None: ...


@dataclass(frozen=True)
class TemporaryGitFixture:
    """In-memory test double; production binding is separately approved."""

    revisions: Mapping[str, str]

    def resolve(self, revision: str) -> str:
        try:
            return self.revisions[revision]
        except KeyError as exc:
            raise CollectionError("unbound Git revision") from exc


@dataclass(frozen=True)
class SyntheticRootFd:
    """In-memory root-FD shim which rejects paths and types outside its map."""

    files: Mapping[str, bytes]

    def read_regular(self, relative_path: str) -> bytes:
        if (not isinstance(relative_path, str) or not relative_path or relative_path.startswith("/")
                or ".." in relative_path.split("/")):
            raise CollectionError("source path escapes root FD")
        try:
            value = self.files[relative_path]
        except KeyError as exc:
            raise CollectionError("source path is absent or non-regular") from exc
        if not isinstance(value, bytes):
            raise CollectionError("source path is non-regular")
        return value


class MemoryEvidenceSink:
    """Test-only sink; callers own all persistence decisions."""

    def __init__(self) -> None:
        self.records: list[dict[str, object]] = []

    def emit(self, record: Mapping[str, object]) -> None:
        self.records.append(dict(record))


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _exact_authority(authority: Mapping[str, str]) -> dict[str, str]:
    if set(authority) != {"formal_root", "formal_child", "base", "target"}:
        raise CollectionError("authority tuple has unknown or missing fields")
    if not all(isinstance(value, str) and value for value in authority.values()):
        raise CollectionError("authority tuple is malformed")
    return dict(authority)


def collect_synthetic(*, authority: Mapping[str, str], paths: Mapping[str, str], git: GitTransaction,
                      root_fd: RootFdOpener, sink: EvidenceSink) -> dict[str, object]:
    """Build one PASS-shaped in-memory record under the frozen DI seam."""
    bound = _exact_authority(authority)
    if set(paths) != set(SOURCE_PATHS) or len(set(paths.values())) != len(SOURCE_PATHS):
        raise CollectionError("source allowlist is not exact")
    if git.resolve("base") != bound["base"] or git.resolve("target") != bound["target"]:
        raise CollectionError("Git lineage drift")
    files = {name: root_fd.read_regular(paths[name]) for name in SOURCE_PATHS}
    # Re-read through the same injected FD boundary before hashing; any race/drift fails.
    if any(root_fd.read_regular(paths[name]) != files[name] for name in SOURCE_PATHS):
        raise CollectionError("same-FD source bytes drifted")
    record: dict[str, object] = {
        "schema_version": SCHEMA,
        "phase": "CPU_STATIC",
        "status": "PASS",
        "authority": bound,
        "candidate": {name: {"path": paths[name], "sha256": _digest(files[name])} for name in SOURCE_PATHS},
        "snapshot": {"retained": True, "rollback": None},
    }
    sink.emit(record)
    return record
