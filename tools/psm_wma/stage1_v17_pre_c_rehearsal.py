"""Pure in-memory Stage-1 v1.7 pre-C rehearsal; intentionally no I/O entrypoint."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Callable, Mapping


class PreCRehearsalError(RuntimeError):
    pass


def _fail(category: str) -> None:
    raise PreCRehearsalError(f"BLOCKED_PRE_C:{category}")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _identity(raw: bytes) -> tuple[int, str]:
    return len(raw), _sha(raw)


@dataclass(frozen=True)
class OpaquePatchCapabilityV1:
    """Test-only host capability; its callable is injected, never resolved by name."""

    provider: str
    module: str
    path: str
    blob_sha256: str
    abi: str
    transport: str
    apply_opaque_v1: Callable[[bytes, str], str]


@dataclass(frozen=True)
class RehearsalInputV1:
    capability: OpaquePatchCapabilityV1
    descriptor: bytes
    json_raw: bytes
    markdown_raw: bytes
    patch_raw: bytes
    output_paths: tuple[str, str]
    six_key_environment: tuple[tuple[str, str], ...]
    frozen_snapshot: tuple[tuple[str, str], ...]
    designated_absences: tuple[str, ...]
    dry_run: Callable[[bytes, tuple[str, str]], bool]
    post_write_verify: Callable[[bytes, bytes, tuple[str, str]], bool]


@dataclass(frozen=True)
class SealedPreCPlanV1:
    capability: OpaquePatchCapabilityV1
    descriptor: bytes
    json_raw: bytes
    markdown_raw: bytes
    patch_raw: bytes
    patch_text: str
    output_paths: tuple[str, str]
    six_key_environment: tuple[tuple[str, str], ...]
    frozen_snapshot: tuple[tuple[str, str], ...]
    designated_absences: tuple[str, ...]
    post_write_verify: Callable[[bytes, bytes, tuple[str, str]], bool]
    identities: tuple[tuple[str, int, str], ...]


_FORBIDDEN = ("v0.3", "v0.4")
_SIX_KEYS = frozenset(("git", "local_v2", "remote_v2", "authority_ref", "config", "project_root"))


def _reject_forbidden(*values: object) -> None:
    if any(token in str(value) for value in values for token in _FORBIDDEN):
        _fail("forbidden_v03_v04")


def rehearse_v05(value: RehearsalInputV1) -> SealedPreCPlanV1:
    """Validate and seal every C input without invoking the capability or writing anything."""
    cap = value.capability
    if (not callable(cap.apply_opaque_v1) or not all((cap.provider, cap.module, cap.path,
            cap.blob_sha256, cap.abi, cap.transport))):
        _fail("capability")
    if (len(value.output_paths) != 2 or len(set(value.output_paths)) != 2
            or len(value.six_key_environment) != 6
            or frozenset(key for key, _ in value.six_key_environment) != _SIX_KEYS):
        _fail("closure_shape")
    if not value.descriptor or not value.json_raw or not value.markdown_raw or not value.patch_raw:
        _fail("empty")
    _reject_forbidden(value.output_paths, value.frozen_snapshot, value.designated_absences)
    try:
        patch_text = value.patch_raw.decode("utf-8", "strict")
    except UnicodeDecodeError:
        _fail("patch_utf8")
    if patch_text.encode("utf-8") != value.patch_raw:
        _fail("patch_roundtrip")
    if not value.dry_run(value.patch_raw, value.output_paths):
        _fail("dry_run")
    names = ("descriptor", "json_raw", "markdown_raw", "patch_raw")
    raws = (value.descriptor, value.json_raw, value.markdown_raw, value.patch_raw)
    identities = tuple((name, *_identity(raw)) for name, raw in zip(names, raws))
    return SealedPreCPlanV1(cap, *raws, patch_text, value.output_paths,
        value.six_key_environment, value.frozen_snapshot, value.designated_absences,
        value.post_write_verify, identities)


def consume_once_v05(plan: SealedPreCPlanV1, current_snapshot: Mapping[str, str]) -> str:
    """The fixed C sequence: compare, one opaque call, byte verifier, then terminal stop."""
    if tuple(current_snapshot.items()) != plan.frozen_snapshot:
        _fail("freshness")
    outcome = plan.capability.apply_opaque_v1(plan.descriptor, plan.patch_text)
    if outcome != "APPLIED":
        _fail("consumer_outcome")
    if not plan.post_write_verify(plan.json_raw, plan.markdown_raw, plan.output_paths):
        _fail("post_write")
    return "HARD_STOP_PENDING_INDEPENDENT_REVIEW"
