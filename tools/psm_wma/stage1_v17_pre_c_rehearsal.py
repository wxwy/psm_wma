"""Pure in-memory Stage-1 v1.7 pre-C rehearsal; intentionally no I/O entrypoint."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Callable


class PreCRehearsalError(RuntimeError):
    pass


def _fail(category: str) -> None:
    raise PreCRehearsalError(f"BLOCKED_PRE_C:{category}")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _blob(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()


PATHS = (
    "docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.5.json",
    "docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.5.md",
)
ENV = (("GIT_CONFIG_GLOBAL", "/dev/null"), ("GIT_CONFIG_NOSYSTEM", "1"),
       ("GIT_CONFIG_SYSTEM", "/dev/null"), ("GIT_NO_REPLACE_OBJECTS", "1"),
       ("LANG", "C"), ("LC_ALL", "C"))
CANON = "utf-8; recursive sorted keys; compact separators; exactly one terminal LF"
DESIGNATED_ABSENCES = (
    "/disk/rl/psm_wma/.authority-root-materialization-08d5828",
    "/disk/rl/psm_wma/.authority-root-materialization-08d5828/.authority-root.index",
    "/disk/rl/psm_wma/artifacts/g0/r09/authority_root_materialization_evidence_v1.json",
    "/disk/rl/psm_wma/artifacts/g0/r09/authority_root_materialization_evidence_v1.json.pending",
)
REMOTE_V2_ARGV = ("git", "ls-remote", "origin", "refs/heads/V2")
AUTHORITY_ARGV = ("git", "ls-remote", "origin",
                  "refs/heads/authority/r09-b-ttt-v035-immutable-source-v1")


@dataclass(frozen=True)
class DescriptorV1:
    abi: str = "psm.stage1.request-patch-consumer/v1"
    operation: str = "add_two_exact_files"
    paths: tuple[str, str] = PATHS
    encoding: str = "utf-8-strict"
    transport: str = "opaque-patch-text-handoff/v1"


@dataclass(frozen=True)
class QueryFactV1:
    argv: tuple[str, ...]
    timeout_s: int
    return_code: int
    stdout: bytes
    stderr: bytes
    predicate: str
    advertised_v2: bytes = b""
    stdout_length: int = 0
    stdout_sha256: str = ""
    stderr_length: int = 0
    stderr_sha256: str = ""
    advertised_length: int = 0
    advertised_sha256: str = ""

    def identity_ok(self) -> bool:
        return (self.timeout_s == 30 and self.return_code == 0 and
                self.stdout_length == len(self.stdout) and self.stdout_sha256 == _sha(self.stdout) and
                self.stderr_length == len(self.stderr) and self.stderr_sha256 == _sha(self.stderr) and
                self.advertised_length == len(self.advertised_v2) and self.advertised_sha256 == _sha(self.advertised_v2))


@dataclass(frozen=True)
class AuthorityAbsenceV1:
    target: str
    raw: bytes
    predicate: str
    byte_length: int
    sha256: str

    def identity_ok(self) -> bool:
        return self.byte_length == len(self.raw) and self.sha256 == _sha(self.raw)


@dataclass(frozen=True)
class AbsenceObservationV1:
    path: str
    lexists: bool
    raw: bytes
    predicate: str
    byte_length: int
    sha256: str

    def identity_ok(self) -> bool:
        return (not self.lexists and self.predicate == "lexists_false" and
                self.raw == _absence_raw(self.path) and
                self.byte_length == len(self.raw) and self.sha256 == _sha(self.raw))


def _absence_raw(path: str) -> bytes:
    return json.dumps({"lexists": False, "path": path, "predicate": "lexists_false"},
                      sort_keys=True, separators=(",", ":")).encode() + b"\n"


@dataclass(frozen=True)
class ReadbackV1:
    json_raw: bytes
    markdown_raw: bytes


@dataclass(frozen=True)
class ClosureV1:
    git_identity: bytes
    config_raw: bytes
    local_v2_raw: bytes
    remote_v2: QueryFactV1
    authority_ref: QueryFactV1
    local_authority_absence: AuthorityAbsenceV1
    remote_authority_absence: AuthorityAbsenceV1
    output_absences: tuple[AbsenceObservationV1, AbsenceObservationV1]
    designated_absences: tuple[AbsenceObservationV1, AbsenceObservationV1, AbsenceObservationV1, AbsenceObservationV1]


class OpaquePatchCapabilityV1:
    """Host-injected capability; neither copyable nor serializable."""
    __slots__ = ("provider", "module", "path", "blob_sha256", "callable_qualname", "abi",
                 "transport", "apply_opaque_v1", "_token", "_locked")

    def __init__(self, provider: str, module: str, path: str, blob_sha256: str,
                 callable_qualname: str, abi: str, transport: str,
                 apply_opaque_v1: Callable[[DescriptorV1, str], str]) -> None:
        self.provider, self.module, self.path = provider, module, path
        self.blob_sha256, self.callable_qualname = blob_sha256, callable_qualname
        self.abi, self.transport, self.apply_opaque_v1 = abi, transport, apply_opaque_v1
        self._token = object(); self._locked = True

    def __setattr__(self, name, value):
        if getattr(self, "_locked", False): _fail("capability_mutation")
        object.__setattr__(self, name, value)

    def __copy__(self): _fail("capability_copy")
    def __deepcopy__(self, memo): _fail("capability_copy")
    def __reduce_ex__(self, protocol): _fail("capability_serialize")


@dataclass(frozen=True)
class RehearsalInputV1:
    capability: OpaquePatchCapabilityV1
    descriptor: DescriptorV1
    json_raw: bytes
    markdown_raw: bytes
    patch_raw: bytes
    environment: tuple[tuple[str, str], ...]
    closure: ClosureV1
    post_write_verify: Callable[[bytes, bytes, tuple[str, str]], ReadbackV1]
    post_write_qualname: str


@dataclass
class _RetirementV1:
    consumed: bool = False


@dataclass(frozen=True)
class SealedPreCPlanV1:
    capability: OpaquePatchCapabilityV1
    descriptor: DescriptorV1
    json_raw: bytes
    markdown_raw: bytes
    patch_text: str
    closure: ClosureV1
    post_write_verify: Callable[[bytes, bytes, tuple[str, str]], ReadbackV1]
    post_write_qualname: str
    identities: tuple[tuple[str, int, str], ...]
    _retirement: _RetirementV1 = field(default_factory=_RetirementV1, init=False, repr=False, compare=False)

    def __copy__(self): _fail("plan_copy")
    def __deepcopy__(self, memo): _fail("plan_copy")
    def __reduce_ex__(self, protocol): _fail("plan_serialize")


def _reject(*values: object) -> None:
    if any(re.search(r"v0\.(?:3|4)(?![0-9.])", str(value)) for value in values):
        _fail("forbidden_v03_v04")


def _validate_json(raw: bytes) -> None:
    try:
        value = json.loads(raw.decode("utf-8", "strict"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        _fail("json_canonical")
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode() + b"\n"
    if raw != canonical or b"\r" in raw: _fail("json_canonical")


def _validate_markdown(raw: bytes, json_raw: bytes) -> None:
    try: text = raw.decode("utf-8", "strict")
    except UnicodeDecodeError: _fail("markdown_utf8")
    if b"\r" in raw or not text.endswith("\n") or text.endswith("\n\n"): _fail("markdown_terminal_lf")
    fields = dict(line.split(": ", 1) for line in text.splitlines() if ": " in line)
    expected = ("json_filename", "json_bytes", "json_sha256", "canonicalization", "json_git_blob_oid")
    if tuple(fields) != expected or len(fields) != 5: _fail("markdown_five_field")
    if (fields["json_filename"], fields["json_bytes"], fields["json_sha256"],
        fields["canonicalization"], fields["json_git_blob_oid"]) != (
            PATHS[0], str(len(json_raw)), _sha(json_raw), CANON, _blob(json_raw)):
        _fail("markdown_sibling")


def _validate_patch(raw: bytes) -> str:
    try: text = raw.decode("utf-8", "strict")
    except UnicodeDecodeError: _fail("patch_utf8")
    if b"\r" in raw or not raw.endswith(b"\n") or b"".join(
            line.encode("utf-8") for line in text.splitlines(keepends=True)) != raw:
        _fail("line_witness")
    headers = tuple(line for line in text.splitlines() if line.startswith("--- ") or line.startswith("+++ "))
    expected = ("--- /dev/null", f"+++ b/{PATHS[0]}", "--- /dev/null", f"+++ b/{PATHS[1]}")
    if headers != expected or any(line.startswith("-") and line != "--- /dev/null" for line in text.splitlines()):
        _fail("patch_add_only")
    return text


def _expected_patch(json_raw: bytes, markdown_raw: bytes) -> bytes:
    def add(raw: bytes) -> bytes:
        return b"".join(b"+" + line for line in raw.splitlines(keepends=True))
    return (b"--- /dev/null\n+++ b/" + PATHS[0].encode() + b"\n" + add(json_raw) +
            b"--- /dev/null\n+++ b/" + PATHS[1].encode() + b"\n" + add(markdown_raw))


def _validate_closure(closure: ClosureV1) -> None:
    _reject(closure)
    if not all((closure.git_identity, closure.config_raw, closure.local_v2_raw,
                closure.local_authority_absence.raw, closure.remote_authority_absence.raw)):
        _fail("closure_empty")
    if (tuple(item.path for item in closure.output_absences) != PATHS or
            tuple(item.path for item in closure.designated_absences) != DESIGNATED_ABSENCES or
            not all(item.identity_ok() for item in closure.output_absences + closure.designated_absences)):
        _fail("closure_absence")
    if ((closure.remote_v2.argv, closure.remote_v2.timeout_s, closure.remote_v2.return_code, closure.remote_v2.predicate) !=
            (REMOTE_V2_ARGV, 30, 0, "remote_v2_ancestor") or
            (closure.authority_ref.argv, closure.authority_ref.timeout_s, closure.authority_ref.return_code,
             closure.authority_ref.predicate) != (AUTHORITY_ARGV, 30, 0, "authority_absent") or
            not closure.remote_v2.identity_ok() or not closure.authority_ref.identity_ok() or
            not closure.remote_v2.advertised_v2 or closure.authority_ref.advertised_v2 or
            closure.remote_v2.stderr or closure.authority_ref.stderr or closure.authority_ref.stdout or
            closure.local_authority_absence.predicate != "authority_absent" or
            closure.remote_authority_absence.predicate != "authority_absent" or
            not closure.local_authority_absence.target or not closure.remote_authority_absence.target or
            not closure.local_authority_absence.identity_ok() or not closure.remote_authority_absence.identity_ok()):
        _fail("closure_query")


def rehearse_v05(value: RehearsalInputV1) -> SealedPreCPlanV1:
    """Seal all C inputs purely in memory, without invoking the capability."""
    cap = value.capability
    identity = f"{cap.apply_opaque_v1.__module__}.{cap.apply_opaque_v1.__qualname__}"
    if (value.descriptor != DescriptorV1() or not callable(cap.apply_opaque_v1) or
        cap.callable_qualname != identity or len(cap.blob_sha256) != 64 or
        any(char not in "0123456789abcdef" for char in cap.blob_sha256) or
        (cap.abi, cap.transport) != (value.descriptor.abi, value.descriptor.transport) or
        not all((cap.provider, cap.module, cap.path))): _fail("capability_identity")
    if value.environment != ENV: _fail("six_key_environment")
    verifier_identity = f"{value.post_write_verify.__module__}.{value.post_write_verify.__qualname__}"
    if not callable(value.post_write_verify) or value.post_write_qualname != verifier_identity:
        _fail("verifier_identity")
    _reject(value.descriptor, value.json_raw, value.markdown_raw, value.patch_raw)
    _validate_json(value.json_raw); _validate_markdown(value.markdown_raw, value.json_raw)
    patch_text = _validate_patch(value.patch_raw)
    if value.patch_raw != _expected_patch(value.json_raw, value.markdown_raw): _fail("patch_inverse")
    _validate_closure(value.closure)
    identities = tuple((name, len(raw), _sha(raw)) for name, raw in (
        ("json_raw", value.json_raw), ("markdown_raw", value.markdown_raw), ("patch_raw", value.patch_raw)))
    return SealedPreCPlanV1(cap, value.descriptor, value.json_raw, value.markdown_raw, patch_text,
                             value.closure, value.post_write_verify, value.post_write_qualname, identities)


def consume_once_v05(plan: SealedPreCPlanV1, current_closure: ClosureV1) -> str:
    """Fixed C: freshness, exactly one opaque call, byte verification, hard stop."""
    if plan._retirement.consumed: _fail("already_consumed")
    plan._retirement.consumed = True
    if current_closure != plan.closure: _fail("freshness")
    try: outcome = plan.capability.apply_opaque_v1(plan.descriptor, plan.patch_text)
    except Exception: _fail("consumer_exception")
    if outcome == "REJECTED_NO_WRITE": _fail("rejected_no_write")
    if outcome == "PARTIAL_OR_UNKNOWN": _fail("partial_or_unknown")
    if outcome != "APPLIED": _fail("consumer_outcome")
    readback = plan.post_write_verify(plan.json_raw, plan.markdown_raw, PATHS)
    if not isinstance(readback, ReadbackV1) or (readback.json_raw, readback.markdown_raw) != (plan.json_raw, plan.markdown_raw):
        _fail("post_write")
    _validate_json(readback.json_raw); _validate_markdown(readback.markdown_raw, readback.json_raw)
    return "HARD_STOP_PENDING_INDEPENDENT_REVIEW"
