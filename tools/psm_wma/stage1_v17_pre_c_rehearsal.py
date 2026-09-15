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
AUTHORITY_REF = AUTHORITY_ARGV[-1]
P0_OBJECTS = (
    ("base_source", "08d5828cdb4c12afa3b798ff01826c91ceb8755a",
     "docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py",
     "af19a9eb66ecaf8bd0b92a48ab1867f105026658"),
    ("replay_helper", "50b0bffeb4c94b0994d7c7bf705077fb51a9e48f",
     "tools/psm_wma/stage1_v17_launcher_replay.py", "74455fce6ca90ede8d9935d893a7a74f5667c687"),
    ("adapter", "08d5828cdb4c12afa3b798ff01826c91ceb8755a",
     "tools/psm_wma/materialize_immutable_source_authority_root.py",
     "4a51bddd15ec9a88883e3071cc550de85721599b"),
)
P0_IDENTITIES = (
    ("base_source", 18966, "8b0fad39857fb72e3a3eb317f4acf6f2d6e94e196935f52f07d6170e79c678dd"),
    ("replay_helper", 5582, "8f55dc32a77810d848c10ac55501754f741d42bd3ef3fbc386f0814b2a6d5e82"),
    ("adapter", 91814, "87e22fac98e61ba9fbf5e0c1adaf3f620365f35a04a266576c5bce4b83e9e816"),
)
P1_OBJECT_NAMES = ("selection", "config", "parser_argv", "bootstrap_argv", "bootstrap",
                   "bootstrap_contract", "outer", "adapter_source")
P1_IDENTITIES = (
    ("selection", 516, "8fe4585f366cb69ad9181e30c25b5f4e99040c83d8ffe66426897bfa9d331edd"),
    ("config", 508, "43b3b77b5934107c54b8bee157b46d07cb17b85ca89305ad6fb7405237e42d1d"),
    ("parser_argv", 2336, "1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333"),
    ("bootstrap_argv", 2341, "85ac67c8a062399dfbface5f9c42867401ffab45320f802697c704061be8df9d"),
    ("bootstrap", 9406, "ccd8ee2772d666707c919e6a20376c997771b9ff068fe0432fdaa96c686ab097"),
    ("bootstrap_contract", 182, "bec6a57aab61fd888ef0eedce37adce227a38a299a9faded53b252c8b5901702"),
    ("outer", 18875, "658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8"),
    ("adapter_source", 91814, "87e22fac98e61ba9fbf5e0c1adaf3f620365f35a04a266576c5bce4b83e9e816"),
)
PARSER_ROWS = (
    ("--formal-root", "9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5", "08d5828cdb4c12afa3b798ff01826c91ceb8755a"),
    ("--cwd", "/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8", "/proc/self/fd/8"),
    ("--index", "/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8/.authority-root.index", "/proc/self/fd/8/.authority-root.index"),
    ("--bootstrap-project-root", "/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8", "/proc/self/fd/8"),
    ("--adapter-blob-oid", "da782754b8e8efa0f3cae973aa68602dcda1c237", "4a51bddd15ec9a88883e3071cc550de85721599b"),
    ("--adapter-raw-sha256", "091ea62d0a8b48429c67100c1395e62a300dc47a8d8f65c7046ba00f8205b5e9", "87e22fac98e61ba9fbf5e0c1adaf3f620365f35a04a266576c5bce4b83e9e816"),
    ("--collection-module-blob-oid", "eefde4e5b5a0965bbdcaa5390b9286a4c77f2665", "4e9f51a52e822e7e57b67aa6ff5eaab8613566c1"),
    ("--collection-module-raw-sha256", "1b3353b0bd1342f1685062f962a7cbc1ba0dbf699bdc72c099ca470cb09cc340", "89eb3ee194f16665aea76ed4dcbaba803fc944d1e0b889d25be69d0831e68c67"),
)
SOURCE_ROWS = (
    ("9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5", "08d5828cdb4c12afa3b798ff01826c91ceb8755a"),
    (".authority-root-materialization-9dd2fb8", ".authority-root-materialization-08d5828"),
    ("da782754b8e8efa0f3cae973aa68602dcda1c237", "4a51bddd15ec9a88883e3071cc550de85721599b"),
    ("62a7bbf5fcb609e52931639001e6db01df81f0de2a33afd41c0080eb8e903f68", "bec6a57aab61fd888ef0eedce37adce227a38a299a9faded53b252c8b5901702"),
    ("7538", "9406"),
    ("7e1c0ecc2161984a88ea0d0eae82f9f7ced709ca919f0302f74a3a068e08c9b8", "ccd8ee2772d666707c919e6a20376c997771b9ff068fe0432fdaa96c686ab097"),
    ("2427", "2336"),
    ("72777bd7305c760c48c069eafd068f1a538383a6fdb8d40258acf3d8fc3b7ae2", "1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333"),
)
FROZEN_TARGETS = (
    ("cwd", "/proc/self/fd/8"),
    ("index", "/proc/self/fd/8/.authority-root.index"),
    ("evidence", "/disk/rl/psm_wma/artifacts/g0/r09/authority_root_materialization_evidence_v1.json"),
    ("json_output", PATHS[0]),
    ("markdown_output", PATHS[1]),
)


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
class RawFactV1:
    name: str
    raw: bytes
    byte_length: int
    sha256: str

    def identity_ok(self) -> bool:
        return bool(self.name) and self.byte_length == len(self.raw) and self.sha256 == _sha(self.raw)


@dataclass(frozen=True)
class SourceObjectV1:
    name: str
    root: str
    path: str
    blob_oid: str
    raw: RawFactV1

    def identity_ok(self) -> bool:
        return (self.raw.name == self.name and self.raw.identity_ok() and
                _blob(self.raw.raw) == self.blob_oid)


@dataclass(frozen=True)
class FrozenTargetV1:
    name: str
    path: str


@dataclass(frozen=True)
class ReplayBindingV1:
    formal_parent: str
    base_path: str
    base_blob_oid: str
    base_raw_sha256: str
    base_bytes: int
    owner_fd_flag: str
    owner_fd_value: int
    parser_argv_items: tuple[str, ...]
    parser_rows: tuple[tuple[str, str, str], ...]
    source_rows: tuple[tuple[str, str], ...]

    def identity_ok(self) -> bool:
        return (self.formal_parent == P0_OBJECTS[0][1] and self.base_path == P0_OBJECTS[0][2] and
                self.base_blob_oid == P0_OBJECTS[0][3] and self.base_raw_sha256 == P0_IDENTITIES[0][2] and
                self.base_bytes == 18966 and self.owner_fd_flag == "--bootstrap-owner-root-fd" and
                self.owner_fd_value == 8 and bool(self.parser_argv_items) and
                all(isinstance(item, str) for item in self.parser_argv_items) and
                self.parser_rows == PARSER_ROWS and self.source_rows == SOURCE_ROWS)


@dataclass(frozen=True)
class AuthorityAbsenceV1:
    target: str
    raw: bytes
    predicate: str
    byte_length: int
    sha256: str

    def identity_ok(self) -> bool:
        return (self.target == AUTHORITY_REF and self.predicate == "authority_absent" and
                self.byte_length == len(self.raw) and self.sha256 == _sha(self.raw))


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
    git_identity: RawFactV1
    config_raw: RawFactV1
    local_v2_raw: RawFactV1
    remote_v2: QueryFactV1
    authority_ref: QueryFactV1
    local_authority_absence: AuthorityAbsenceV1
    remote_authority_absence: AuthorityAbsenceV1
    output_absences: tuple[AbsenceObservationV1, AbsenceObservationV1]
    designated_absences: tuple[AbsenceObservationV1, AbsenceObservationV1, AbsenceObservationV1, AbsenceObservationV1]
    p0_objects: tuple[SourceObjectV1, SourceObjectV1, SourceObjectV1]
    p1_objects: tuple[RawFactV1, RawFactV1, RawFactV1, RawFactV1, RawFactV1, RawFactV1, RawFactV1, RawFactV1]
    replay_binding: ReplayBindingV1
    targets: tuple[FrozenTargetV1, FrozenTargetV1, FrozenTargetV1, FrozenTargetV1, FrozenTargetV1]


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


class FreshnessLeaseV1:
    """Host-bound local freshness lease; it exposes no closure reconstruction input."""
    __slots__ = ("_domain", "_locked")

    def __init__(self, domain: tuple[tuple[str, str, str, int, str], ...]) -> None:
        self._domain = domain; self._locked = True

    def __setattr__(self, name, value):
        if getattr(self, "_locked", False): _fail("lease_mutation")
        object.__setattr__(self, name, value)

    def __copy__(self): _fail("lease_copy")
    def __deepcopy__(self, memo): _fail("lease_copy")
    def __reduce_ex__(self, protocol): _fail("lease_serialize")


class FreshnessGuardV1:
    """Pre-C injected opaque guard; no path, query or ClosureV1 is accepted by C."""
    __slots__ = ("provider", "module", "path", "blob_sha256", "callable_qualname", "abi",
                 "transport", "guard_opaque_v1", "_locked")

    def __init__(self, provider: str, module: str, path: str, blob_sha256: str,
                 callable_qualname: str, abi: str, transport: str,
                 guard_opaque_v1: Callable[[FreshnessLeaseV1, DescriptorV1,
                                            tuple[tuple[str, str, str, int, str], ...]], str]) -> None:
        self.provider, self.module, self.path = provider, module, path
        self.blob_sha256, self.callable_qualname = blob_sha256, callable_qualname
        self.abi, self.transport, self.guard_opaque_v1 = abi, transport, guard_opaque_v1
        self._locked = True

    def __setattr__(self, name, value):
        if getattr(self, "_locked", False): _fail("guard_mutation")
        object.__setattr__(self, name, value)

    def __copy__(self): _fail("guard_copy")
    def __deepcopy__(self, memo): _fail("guard_copy")
    def __reduce_ex__(self, protocol): _fail("guard_serialize")


@dataclass(frozen=True)
class ContractV05:
    """唯一的纯内存 pre-C 合同；C 只能消费由它密封的 plan。"""
    capability: OpaquePatchCapabilityV1
    descriptor: DescriptorV1
    json_raw: bytes
    markdown_raw: bytes
    patch_raw: bytes
    environment: tuple[tuple[str, str], ...]
    closure: ClosureV1
    freshness_guard: FreshnessGuardV1
    freshness_lease: FreshnessLeaseV1
    post_write_verify: Callable[[bytes, bytes, tuple[str, str]], ReadbackV1]
    post_write_qualname: str


# 保留已冻结的测试/调用端名称，避免在本次收口中扩大接口变更。
RehearsalInputV1 = ContractV05


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
    freshness_guard: FreshnessGuardV1
    freshness_lease: FreshnessLeaseV1
    freshness_identities: tuple[tuple[str, str, str, int, str], ...]
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
    # 冻结源码可保留历史 v0.3/v0.4 字面量；下方精确 identity 将其限定为数据。
    if not all((closure.git_identity.identity_ok(), closure.config_raw.identity_ok(),
                closure.local_v2_raw.identity_ok(), closure.local_authority_absence.raw,
                closure.remote_authority_absence.raw)):
        _fail("closure_empty")
    try:
        parser_argv_items = tuple(json.loads(closure.p1_objects[2].raw.decode("utf-8", "strict")))
    except (IndexError, UnicodeDecodeError, json.JSONDecodeError, TypeError):
        _fail("closure_inherited")
    if (tuple((item.name, item.root, item.path, item.blob_oid) for item in closure.p0_objects) != P0_OBJECTS or
            tuple((item.raw.name, item.raw.byte_length, item.raw.sha256) for item in closure.p0_objects) != P0_IDENTITIES or
            tuple((item.name, item.byte_length, item.sha256) for item in closure.p1_objects) != P1_IDENTITIES or
            not all(item.identity_ok() for item in closure.p0_objects + closure.p1_objects) or
            not closure.replay_binding.identity_ok() or closure.replay_binding.parser_argv_items != parser_argv_items or
            tuple((item.name, item.path) for item in closure.targets) != FROZEN_TARGETS):
        _fail("closure_inherited")
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
            not closure.local_authority_absence.identity_ok() or not closure.remote_authority_absence.identity_ok()):
        _fail("closure_query")


def rehearse_v05(value: ContractV05) -> SealedPreCPlanV1:
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
    guard = value.freshness_guard
    guard_identity = f"{guard.guard_opaque_v1.__module__}.{guard.guard_opaque_v1.__qualname__}"
    if (not callable(guard.guard_opaque_v1) or guard.callable_qualname != guard_identity or
            len(guard.blob_sha256) != 64 or any(char not in "0123456789abcdef" for char in guard.blob_sha256) or
            (guard.abi, guard.transport) != ("psm.stage1.request-freshness-guard/v1",
                                               "opaque-sealed-freshness-guard/v1") or
            not all((guard.provider, guard.module, guard.path))): _fail("guard_identity")
    local = (value.closure.git_identity, value.closure.config_raw, value.closure.local_v2_raw)
    lease_domain = tuple((item.name, "", "", item.byte_length, item.sha256) for item in local) + tuple(
        (f"output_absence:{index}", item.path, item.predicate, item.byte_length, item.sha256)
        for index, item in enumerate(value.closure.output_absences)) + tuple(
        (f"designated_absence:{index}", item.path, item.predicate, item.byte_length, item.sha256)
        for index, item in enumerate(value.closure.designated_absences))
    if value.freshness_lease._domain != lease_domain: _fail("lease_domain")
    identities = tuple((name, len(raw), _sha(raw)) for name, raw in (
        ("json_raw", value.json_raw), ("markdown_raw", value.markdown_raw), ("patch_raw", value.patch_raw)))
    return SealedPreCPlanV1(cap, value.descriptor, value.json_raw, value.markdown_raw, patch_text,
                             value.closure, guard, value.freshness_lease, lease_domain,
                             value.post_write_verify, value.post_write_qualname, identities)


def consume_once_v05(plan: SealedPreCPlanV1) -> str:
    """Fixed C: freshness, exactly one opaque call, byte verification, hard stop."""
    if plan._retirement.consumed: _fail("already_consumed")
    plan._retirement.consumed = True
    try:
        freshness = plan.freshness_guard.guard_opaque_v1(
            plan.freshness_lease, plan.descriptor, plan.freshness_identities)
    except Exception: _fail("freshness_unknown")
    if freshness == "STALE": _fail("freshness")
    if freshness != "FRESH": _fail("freshness_unknown")
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
