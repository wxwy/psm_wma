"""CPU/static immutable source-collection algorithm under injected seams."""
from __future__ import annotations

import hashlib
import json
import stat
from dataclasses import dataclass, field
from typing import Mapping, Protocol

from tools.g0.audit_r09_b_ttt_root_gitlink_authority import AuditFailure, validate_config

SCHEMA = "immutable_source_collection_execution_evidence_v1"
SOURCE_PATHS = ("checkpoint", "config", "manifest", "metadata", "state")
COLLECTION_PATHS = (
    "docs/build/PSM-WMA_immutable_source_collection_v1.json",
    "docs/build/PSM-WMA_immutable_source_canonical_model_config_v1.json",
    "docs/build/PSM-WMA_immutable_source_input_descriptor_v1.json",
    "docs/build/PSM-WMA_immutable_source_manifest_v1.json",
    "docs/build/PSM-WMA_immutable_source_checkpoint_descriptor_v1.json",
)
RECEIPT_PATH = "docs/build/PSM-WMA_immutable_source_collection_receipt_v1.json"
SELECTION_PATH = "docs/build/PSM-WMA_immutable_source_selection_request_v1.json"
EVIDENCE_KEYS = frozenset(("schema", "status", "execution", "tool", "environment", "authority", "lineage", "source_entries", "handoff", "candidates", "collection", "receipt", "post_checks", "push_publication", "rollback", "evidence_sha256"))
CANDIDATE_KEYS = ("input_descriptor_sha256", "manifest_sha256", "identifier_sha256", "checkpoint_descriptor_sha256", "collection_sha256", "config_sha256")

class CollectionError(ValueError): pass
def _canonical(value: object) -> bytes: return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
def _digest(value: bytes) -> str: return hashlib.sha256(value).hexdigest()
def _sha(value: object) -> str: return _digest(_canonical(value))
def _is_sha(value: object) -> bool: return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)
def _null_rollback() -> dict[str, object]: return {"before_snapshot": None, "after_snapshot": None, "before_snapshot_sha256": None, "after_snapshot_sha256": None, "verified": None}
def _null_collection() -> dict[str, object]: return {"revision": None, "tree_native_oid": None, "parent_revision": None, "delta_paths": []}
def _null_receipt() -> dict[str, object]: return {**_null_collection(), "blob_native_oid": None}
SNAPSHOT_KEYS = ("target_ref", "target_ref_revision", "head_mode", "head_symbolic_ref", "head_revision", "index_tree_native_oid", "worktree_entries", "worktree_sha256")
SNAPSHOT_PATHS = tuple(sorted((*COLLECTION_PATHS, RECEIPT_PATH), key=lambda path: path.encode()))

@dataclass(frozen=True)
class EntryStat:
    device: int
    inode: int
    size: int
    mtime_ns: int
    ctime_ns: int
    mode: int = stat.S_IFREG | 0o600


class EntryHandle(Protocol):
    def stat(self) -> EntryStat: ...
    def read(self, size: int) -> bytes: ...
    def rewind(self) -> None: ...
    def close(self) -> None: ...
class RootFdOpener(Protocol):
    def open_regular(self, relative_path: str) -> EntryHandle: ...
class GitTransaction(Protocol):
    def resolve(self, revision: str) -> str: ...
    def parent(self, revision: str) -> str: ...
    def tree_entries(self, revision: str) -> Mapping[str, str]: ...
    def blob_bytes(self, oid: str) -> bytes: ...
    def gitlink_at(self, revision: str) -> str: ...
    def snapshot(self) -> Mapping[str, object]: ...
    def commit(self, paths: tuple[str, ...], parent: str | None) -> Mapping[str, str]: ...
    def lookup(self, revision: str) -> Mapping[str, str]: ...
    def rollback(self, snapshot: Mapping[str, object]) -> Mapping[str, object]: ...
class EvidenceSink(Protocol):
    def emit(self, record: Mapping[str, object]) -> None: ...

@dataclass
class SyntheticEntry:
    data: bytes
    identity: EntryStat | None = None
    reads: list[bytes] = field(default_factory=list)
    stats: list[EntryStat] = field(default_factory=list)
    position: int = 0
    generation: int = 0
    closed: bool = False

    def stat(self) -> EntryStat:
        return self.stats.pop(0) if self.stats else (self.identity or EntryStat(1, 1, len(self.data), 0, 0))

    def read(self, size: int) -> bytes:
        if self.closed:
            raise CollectionError("descriptor 已关闭")
        data = self.reads[min(self.generation, len(self.reads) - 1)] if self.reads else self.data
        chunk = data[self.position:self.position + size]
        self.position += len(chunk)
        return chunk

    def rewind(self) -> None:
        self.position = 0
        self.generation += 1

    def close(self) -> None:
        self.closed = True
@dataclass(frozen=True)
class SyntheticRootFd:
    files: Mapping[str, SyntheticEntry | bytes]
    symlink_components: frozenset[str] = frozenset()
    def open_regular(self, path: str) -> EntryHandle:
        if not isinstance(path, str) or not path or path.startswith("/") or ".." in path.split("/"): raise CollectionError("source path escapes root FD")
        if any(component in self.symlink_components for component in path.split("/")): raise CollectionError("source component is a symlink")
        value = self.files.get(path)
        if isinstance(value, bytes): return SyntheticEntry(value)
        if isinstance(value, SyntheticEntry): return value
        raise CollectionError("source path is absent or non-regular")
@dataclass
class TemporaryGitFixture:
    revisions: Mapping[str, str]
    commits: list[Mapping[str, str]] = field(default_factory=list)
    state: Mapping[str, object] = field(default_factory=lambda: {"target": "synthetic"})
    parents: Mapping[str, str] = field(default_factory=dict)
    trees: Mapping[str, Mapping[str, str]] = field(default_factory=dict)
    blobs: Mapping[str, bytes] = field(default_factory=dict)
    gitlinks: Mapping[str, str] = field(default_factory=dict)

    def parent(self, revision: str) -> str:
        if revision not in self.parents:
            raise CollectionError("authority commit 不可达")
        return self.parents[revision]

    def tree_entries(self, revision: str) -> Mapping[str, str]:
        if revision not in self.trees:
            raise CollectionError("authority tree 不可达")
        return dict(self.trees[revision])

    def blob_bytes(self, oid: str) -> bytes:
        if oid not in self.blobs:
            raise CollectionError("authority blob 不可达")
        return self.blobs[oid]

    def gitlink_at(self, revision: str) -> str:
        if revision not in self.gitlinks:
            raise CollectionError("base Gitlink 不可达")
        return self.gitlinks[revision]
    def resolve(self, revision: str) -> str:
        if revision not in self.revisions: raise CollectionError("unbound Git revision")
        return self.revisions[revision]
    def snapshot(self) -> Mapping[str, object]: return dict(self.state)
    def commit(self, paths: tuple[str, ...], parent: str | None) -> Mapping[str, str]:
        if paths not in (COLLECTION_PATHS, (RECEIPT_PATH,)): raise CollectionError("transaction allowlist drift")
        row = {"revision": _digest((str(parent)+str(paths)).encode())[:40], "tree_native_oid": _digest(str(paths).encode())[:40], "parent_revision": parent or "0" * 40}; self.commits.append(row); return row
    def lookup(self, revision: str) -> Mapping[str, str]:
        for row in self.commits:
            if row["revision"] == revision: return dict(row)
        raise CollectionError("committed tree is absent")
    def rollback(self, snapshot: Mapping[str, object]) -> Mapping[str, object]: self.state = dict(snapshot); return self.snapshot()
class MemoryEvidenceSink:
    def __init__(self) -> None: self.records: list[dict[str, object]] = []
    def emit(self, record: Mapping[str, object]) -> None: verify_evidence(record); self.records.append(dict(record))
@dataclass(frozen=True)
class CandidateHandoff:
    authority: Mapping[str, str]
    lineage: Mapping[str, str]
    source_entries: tuple[Mapping[str, object], ...]
    candidates: Mapping[str, str]
    artifact_bytes: tuple[tuple[str, bytes], ...] = ()


def derive_candidates(entries: tuple[Mapping[str, object], ...], config_raw: bytes) -> tuple[tuple[tuple[str, bytes], ...], dict[str, str]]:
    """按冻结公式生成五个候选原始 blob；输入仅为已读取条目的摘要。"""
    if not entries:
        raise CollectionError("source entries 不能为空")
    for ordinal, entry in enumerate(entries):
        if (set(entry) != {"ordinal", "byte_length", "sha256"}
                or type(entry["ordinal"]) is not int or entry["ordinal"] != ordinal
                or type(entry["byte_length"]) is not int or entry["byte_length"] <= 0
                or not _is_sha(entry["sha256"])):
            raise CollectionError("source entry 字段或类型不符合冻结合同")
    try:
        config, config_sha = validate_config(json.loads(config_raw))
        if _canonical(config) != config_raw:
            raise CollectionError("config bytes 不是 canonical JSON")
    except (AuditFailure, ValueError, TypeError, UnicodeError) as exc:
        raise CollectionError("config schema 或 canonical bytes 无效") from exc
    source_kind = "checkpoint_source_manifest_v1"
    input_raw = _canonical({"schema": "immutable_source_input_descriptor_v1",
                            "source_kind": source_kind, "source_entries": list(entries)})
    input_sha = _digest(input_raw)
    manifest_raw = _canonical({"schema": "immutable_source_manifest_v1", "source_kind": source_kind,
                               "source_input_sha256": input_sha, "source_entries": list(entries)})
    manifest_sha = _digest(manifest_raw)
    identifier = _sha({"schema": "immutable_source_identifier_v1",
                       "source_manifest_sha256": manifest_sha, "source_input_sha256": input_sha})
    descriptor = {"schema": "root_gitlink_checkpoint_source_descriptor_v1", "source_kind": source_kind,
                  "immutable_source_identifier": identifier, "source_manifest_sha256": manifest_sha,
                  "source_input_sha256": input_sha}
    descriptor_raw = _canonical(descriptor)
    collection_raw = _canonical({**descriptor, "schema": "immutable_source_collection_v1",
                                 "checkpoint_source_descriptor_sha256": _digest(descriptor_raw)})
    artifacts = tuple(zip(COLLECTION_PATHS, (collection_raw, config_raw, input_raw, manifest_raw, descriptor_raw)))
    digests = dict(zip(CANDIDATE_KEYS, (input_sha, manifest_sha, identifier, _digest(descriptor_raw),
                                      _digest(collection_raw), config_sha)))
    return artifacts, digests
class OneShotHandoff:
    """同一次 executor activation 内的一次性能力；不提供公共 payload 构造入口。"""

    def __init__(self) -> None:
        raise CollectionError("handoff 只能由 source preflight 产生")

    def __reduce_ex__(self, protocol: int) -> object:
        raise CollectionError("handoff 不允许序列化或复制")

    def take(self, activation: object) -> CandidateHandoff:
        if activation is not self._activation:
            raise CollectionError("handoff activation 不匹配")
        if self._used:
            raise CollectionError("candidate handoff was already consumed")
        self._used = True
        logical = json.loads(self._logical_bytes)
        artifacts, digests = derive_candidates(tuple(logical["source_entries"]), dict(self._artifacts)[COLLECTION_PATHS[1]])
        if artifacts != self._artifacts or digests != self._digests:
            raise CollectionError("handoff candidate bytes 或 digest 漂移")
        if _digest(self._logical_bytes) != self.digest:
            raise CollectionError("handoff logical digest 漂移")
        return CandidateHandoff(logical["authority"], {}, tuple(logical["source_entries"]), digests, artifacts)


def _source_handoff(authority: Mapping[str, str], entries: tuple[Mapping[str, object], ...],
                    config_raw: bytes, activation: object) -> OneShotHandoff:
    """由已完成读取的 producer 创建；closure 不接受外部反序列化 payload。"""
    artifacts, digests = derive_candidates(entries, config_raw)
    logical = {
        "authority": dict(authority), "source_entries": list(entries),
        "artifacts": [{"path": path, "schema": json.loads(raw)["schema"], "sha256": _digest(raw)}
                      for path, raw in artifacts],
        "config_sha256": digests["config_sha256"],
    }
    handoff = object.__new__(OneShotHandoff)
    handoff._activation = activation
    handoff._used = False
    handoff._logical_bytes = _canonical(logical)
    handoff._artifacts = artifacts
    handoff._digests = dict(digests)
    handoff.digest = _digest(handoff._logical_bytes)
    return handoff

def _snapshot(snapshot: Mapping[str, object]) -> dict[str, object]:
    value = dict(snapshot)
    if set(value) != set(SNAPSHOT_KEYS) or value["head_mode"] not in {"symbolic", "detached"}:
        raise CollectionError("target_snapshot_v1 schema drift")
    for key in ("target_ref_revision", "head_revision", "index_tree_native_oid"):
        oid = value[key]
        if not isinstance(oid, str) or len(oid) != 40 or any(char not in "0123456789abcdef" for char in oid):
            raise CollectionError("snapshot Git OID 无效")
    if value["head_mode"] == "symbolic" and not isinstance(value["head_symbolic_ref"], str):
        raise CollectionError("symbolic snapshot head drift")
    if value["head_mode"] == "detached" and value["head_symbolic_ref"] is not None:
        raise CollectionError("detached snapshot head drift")
    entries = value["worktree_entries"]
    if not isinstance(entries, list) or [entry.get("path") for entry in entries if isinstance(entry, Mapping)] != list(SNAPSHOT_PATHS):
        raise CollectionError("snapshot worktree ordering drift")
    for entry in entries:
        if not isinstance(entry, Mapping) or set(entry) != {"path", "mode", "kind", "sha256"}:
            raise CollectionError("snapshot worktree entry schema drift")
        if entry["kind"] == "absent" and (entry["mode"] is not None or entry["sha256"] is not None):
            raise CollectionError("absent snapshot entry drift")
        if entry["kind"] == "regular" and (entry["mode"] not in {"100644", "100755"} or not _is_sha(entry["sha256"])):
            raise CollectionError("regular snapshot entry drift")
        if entry["kind"] not in {"absent", "regular"}:
            raise CollectionError("snapshot entry kind drift")
    if value["worktree_sha256"] != _sha(entries):
        raise CollectionError("snapshot worktree digest 漂移")
    return value

def verify_synthetic_rollback(before: Mapping[str, object], after: Mapping[str, object], *, completed: bool) -> dict[str, object]:
    """Model the retained live rollback witness without touching a worktree."""
    before_value, after_value = _snapshot(before), _snapshot(after)
    witness = {"before_snapshot": before_value, "after_snapshot": after_value, "before_snapshot_sha256": _sha(before_value), "after_snapshot_sha256": _sha(after_value), "verified": completed and before_value == after_value}
    if not witness["verified"]:
        raise CollectionError("ROLLBACK_INCOMPLETE")
    return witness

def verify_evidence(record: Mapping[str, object]) -> None:
    if set(record) != EVIDENCE_KEYS or record.get("schema") != SCHEMA or record.get("status") not in {"PASS", "FAIL"}: raise CollectionError("evidence key set or status is not canonical")
    unsigned = dict(record); digest = unsigned.pop("evidence_sha256")
    if not isinstance(digest, str) or digest != _sha(unsigned): raise CollectionError("evidence digest drift")
    _verify_evidence_sections(record)
    execution = record["execution"]
    if record["status"] == "PASS":
        if not isinstance(execution, Mapping) or set(execution) != {"approval_formal_root", "command_argv", "interpreter", "phase"} or execution["phase"] != "complete": raise CollectionError("PASS execution drift")
        if record["rollback"] != _null_rollback() or record["push_publication"] != {"pushed": False, "published": False}: raise CollectionError("PASS terminal drift")
        entries = record["source_entries"]
        if not isinstance(entries, list) or not entries or [x.get("ordinal") for x in entries if isinstance(x, Mapping)] != list(range(len(entries))): raise CollectionError("source entry drift")
    else:
        phases = {"tool_identity", "environment", "authority", "lineage", "source_read", "candidate_construction", "candidate_verification", "collection", "receipt", "post_check", "push_publication"}
        if not isinstance(execution, Mapping) or set(execution) != {"approval_formal_root", "command_argv", "interpreter", "phase", "failure_code"} or execution.get("phase") not in phases or not isinstance(execution.get("failure_code"), str) or not execution["failure_code"]:
            raise CollectionError("FAIL execution drift")
        phase = execution["phase"]
        if phase in {"tool_identity", "environment", "authority", "lineage", "source_read", "candidate_construction", "candidate_verification"} and record["rollback"] != _null_rollback():
            raise CollectionError("pre-live FAIL rollback drift")
        if phase in {"tool_identity", "environment", "authority", "lineage"}:
            if record["source_entries"] != [] or record["collection"] != _null_collection() or record["receipt"] != _null_receipt():
                raise CollectionError("early FAIL nullability drift")
        if phase == "source_read" and not isinstance(record["source_entries"], list):
            raise CollectionError("source-read prefix drift")
        candidates = record["candidates"]
        if not isinstance(candidates, Mapping) or set(candidates) != set(CANDIDATE_KEYS):
            raise CollectionError("candidate key order drift")
        seen_null = False
        for key in CANDIDATE_KEYS:
            value = candidates[key]
            seen_null = seen_null or value is None
            if (value is None and not seen_null) or (value is not None and (seen_null or not _is_sha(value))):
                raise CollectionError("candidate prefix drift")
        checks = record["post_checks"]
        check_keys = ("authority", "lineage", "derivation", "collection", "receipt")
        if not isinstance(checks, Mapping) or set(checks) != set(check_keys):
            raise CollectionError("post-check key order drift")
        if phase == "post_check":
            values = [checks[key] for key in check_keys]
            failures = [index for index, value in enumerate(values) if value is False]
            if len(failures) != 1 or any(value is not True for value in values[:failures[0]]) or any(value is not None for value in values[failures[0]+1:]):
                raise CollectionError("post-check prefix drift")
        push = record["push_publication"]
        if not isinstance(push, Mapping) or set(push) != {"pushed", "published"}:
            raise CollectionError("push-publication schema drift")
        if phase == "push_publication" and not any(value is True for value in push.values()):
            raise CollectionError("push-publication observation drift")
        if phase in {"collection", "receipt"} and record["rollback"] == _null_rollback():
            raise CollectionError("live FAIL requires rollback witness")

EVIDENCE_PHASES = ("tool_identity", "environment", "authority", "lineage", "source_read",
                   "candidate_construction", "candidate_verification", "collection", "receipt",
                   "post_check", "push_publication", "complete")
SECTION_KEYS = {
    "tool": ("path", "blob_native_oid", "raw_sha256"),
    "environment": ("workdir", "python_executable", "cpu_only", "no_network", "sanitized_env_sha256"),
    "authority": ("root_revision", "selection_path", "selection_blob_native_oid", "selection_raw_sha256",
                  "config_path", "config_blob_native_oid", "config_raw_sha256"),
    "lineage": ("target_ref", "expected_base_root_revision", "expected_child_gitlink", "authority_approval_formal_root_revision"),
    "handoff": ("candidate_handoff_sha256", "consumed_once"),
    "candidates": CANDIDATE_KEYS,
    "collection": tuple(_null_collection()), "receipt": tuple(_null_receipt()),
    "post_checks": ("authority", "lineage", "derivation", "collection", "receipt"),
    "push_publication": ("pushed", "published"), "rollback": tuple(_null_rollback()),
}


def _exact_section(value: object, keys: tuple[str, ...]) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or set(value) != set(keys):
        raise CollectionError("evidence nested key 集合不符合合同")
    return value


def _null_section(value: Mapping[str, object]) -> bool:
    return all(item is None for item in value.values())


def _verify_evidence_sections(record: Mapping[str, object]) -> None:
    """由首个失败 phase 导出每个 section 的已到达/未到达状态。"""
    passed = record["status"] == "PASS"
    execution_keys = ("approval_formal_root", "command_argv", "interpreter", "phase")
    execution = _exact_section(record["execution"], execution_keys if passed else execution_keys + ("failure_code",))
    phase = execution["phase"]
    if phase not in EVIDENCE_PHASES or passed != (phase == "complete"):
        raise CollectionError("evidence status/phase 矛盾")
    stage = EVIDENCE_PHASES.index(phase)
    argv = execution["command_argv"]
    if not isinstance(argv, list) or any(not isinstance(arg, str) for arg in argv):
        raise CollectionError("execution command_argv 类型错误")
    if not passed:
        code = execution["failure_code"]
        if not isinstance(code, str) or not code or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_" for c in code):
            raise CollectionError("failure_code 必须是稳定标识符")
    sections = {name: _exact_section(record[name], keys) for name, keys in SECTION_KEYS.items()}
    for index, name in enumerate(("tool", "environment", "authority", "lineage")):
        value = sections[name]
        if stage <= index:
            if not _null_section(value):
                raise CollectionError("未到达的 identity section 必须为 null")
            continue
        for key, item in value.items():
            if key.endswith("sha256"):
                valid = _is_sha(item)
            elif key.endswith(("oid", "revision", "gitlink")):
                valid = isinstance(item, str) and len(item) == 40 and all(c in "0123456789abcdef" for c in item)
            elif key in ("cpu_only", "no_network"):
                valid = item is True
            else:
                valid = isinstance(item, str) and bool(item)
            if not valid:
                raise CollectionError("已到达的 identity section 类型无效")
    entries = record["source_entries"]
    if not isinstance(entries, list) or (stage < 4 and entries) or (stage > 4 and not entries):
        raise CollectionError("source_entries 到达状态错误")
    for ordinal, entry in enumerate(entries):
        entry = _exact_section(entry, ("ordinal", "byte_length", "sha256"))
        if (type(entry["ordinal"]) is not int or entry["ordinal"] != ordinal
                or type(entry["byte_length"]) is not int or entry["byte_length"] <= 0
                or not _is_sha(entry["sha256"])):
            raise CollectionError("source_entries 类型/前缀错误")
    candidates = [sections["candidates"][key] for key in CANDIDATE_KEYS]
    if stage < 5:
        valid_candidates = all(value is None for value in candidates)
    elif stage == 5:
        count = next((i for i, value in enumerate(candidates) if value is None), 6)
        valid_candidates = count < 6 and all(_is_sha(v) for v in candidates[:count]) and all(v is None for v in candidates[count:])
    else:
        valid_candidates = all(_is_sha(v) for v in candidates)
    if not valid_candidates:
        raise CollectionError("candidate construction 前缀或到达状态错误")
    handoff = sections["handoff"]
    if stage < 6:
        valid_handoff = _null_section(handoff)
    else:
        valid_handoff = _is_sha(handoff["candidate_handoff_sha256"]) and type(handoff["consumed_once"]) is bool
    if not valid_handoff or (passed and handoff["consumed_once"] is not True):
        raise CollectionError("handoff 到达状态错误")
    for index, name, paths in ((7, "collection", COLLECTION_PATHS), (8, "receipt", (RECEIPT_PATH,))):
        value = sections[name]
        if stage <= index:
            expected = _null_collection() if name == "collection" else _null_receipt()
            if dict(value) != expected:
                raise CollectionError("未完成 commit 必须为 exact null record")
        else:
            for key, item in value.items():
                if key == "delta_paths":
                    valid = item == list(paths)
                else:
                    valid = isinstance(item, str) and len(item) == 40 and all(c in "0123456789abcdef" for c in item)
                if not valid:
                    raise CollectionError("commit record 类型或 delta_paths 无效")
    checks = [sections["post_checks"][key] for key in SECTION_KEYS["post_checks"]]
    if stage < 9:
        valid_checks = all(v is None for v in checks)
    elif stage == 9:
        failures = [i for i, v in enumerate(checks) if v is False]
        valid_checks = len(failures) == 1 and all(v is True for v in checks[:failures[0]]) and all(v is None for v in checks[failures[0] + 1:])
    else:
        valid_checks = all(v is True for v in checks)
    if not valid_checks:
        raise CollectionError("post_checks 前缀或到达状态错误")
    push = list(sections["push_publication"].values())
    if stage < 10:
        valid_push = all(v is None for v in push)
    else:
        valid_push = all(type(v) is bool for v in push) and (not any(push) if passed else any(push))
    if not valid_push:
        raise CollectionError("push/publication 观测错误")
    rollback = sections["rollback"]
    if passed or stage < 7:
        if not _null_section(rollback):
            raise CollectionError("无需 rollback 时必须为 exact null record")
    else:
        before, after = _snapshot(rollback["before_snapshot"]), _snapshot(rollback["after_snapshot"])
        if rollback["before_snapshot_sha256"] != _sha(before) or rollback["after_snapshot_sha256"] != _sha(after):
            raise CollectionError("rollback snapshot digest 漂移")
        verified = rollback["verified"]
        if type(verified) is not bool or (verified and before != after):
            raise CollectionError("rollback equality witness 无效")
        if not verified and execution["failure_code"] != "ROLLBACK_INCOMPLETE":
            raise CollectionError("未完成 rollback 必须 fail-stop")


def _entry(opener: RootFdOpener, path: str, ordinal: int) -> dict[str, int | str]:
    handle = opener.open_regular(path)
    try:
        before = handle.stat()
        if not isinstance(before, EntryStat) or not stat.S_ISREG(before.mode) or before.size <= 0:
            raise CollectionError("最终 descriptor 不是非空 regular file")
        first = _hash_handle(handle)
        middle = handle.stat()
        handle.rewind()
        second = _hash_handle(handle)
        after = handle.stat()
        if before != middle or before != after or first != second or first[0] != before.size:
            raise CollectionError("same-opened-FD identity or hash drift")
        # 原始 source bytes 不跨越读取阶段，仅移交长度和摘要。
        return {"ordinal": ordinal, "byte_length": first[0], "sha256": first[1]}
    finally:
        handle.close()


def _hash_handle(handle: EntryHandle) -> tuple[int, str]:
    digest = hashlib.sha256()
    length = 0
    while True:
        chunk = handle.read(65536)
        if not isinstance(chunk, bytes):
            raise CollectionError("descriptor read 必须返回 bytes")
        if not chunk:
            return length, digest.hexdigest()
        length += len(chunk)
        digest.update(chunk)

def _blob_oid(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def _bound_source_inputs(authority: Mapping[str, str], lineage: Mapping[str, str],
                         paths: Mapping[str, str], git: GitTransaction) -> tuple[tuple[str, ...], bytes]:
    """只从指定 commit tree/blob 复算 authority，再绑定 source transport。"""
    authority_keys = ("root_revision", "selection_path", "selection_blob_native_oid", "selection_raw_sha256", "config_path", "config_blob_native_oid", "config_raw_sha256")
    lineage_keys = ("target_ref", "expected_base_root_revision", "expected_child_gitlink", "authority_approval_formal_root_revision")
    if set(authority) != set(authority_keys) or set(lineage) != set(lineage_keys): raise CollectionError("authority or lineage tuple drift")
    for values in (authority, lineage):
        for key, value in values.items():
            if key.endswith(("revision", "oid", "gitlink")):
                if not isinstance(value, str) or len(value) != 40 or any(c not in "0123456789abcdef" for c in value):
                    raise CollectionError("authority/lineage Git SHA 格式无效")
            if key.endswith("sha256") and not _is_sha(value):
                raise CollectionError("authority SHA-256 格式无效")
    if authority["selection_path"] != SELECTION_PATH or authority["config_path"] != COLLECTION_PATHS[1]:
        raise CollectionError("authority 固定路径漂移")
    revision = authority["root_revision"]
    if git.parent(revision) != lineage["authority_approval_formal_root_revision"]:
        raise CollectionError("authority parent 漂移")
    if git.resolve(lineage["target_ref"]) != lineage["expected_base_root_revision"]:
        raise CollectionError("target ref/base 漂移")
    if git.gitlink_at(lineage["expected_base_root_revision"]) != lineage["expected_child_gitlink"]:
        raise CollectionError("base child Gitlink 漂移")
    tree = git.tree_entries(revision)
    if set(tree) != {SELECTION_PATH, COLLECTION_PATHS[1]}:
        raise CollectionError("authority tree 必须仅含两个固定 blob")
    raw_values = {}
    for prefix in ("selection", "config"):
        path, oid = authority[prefix + "_path"], authority[prefix + "_blob_native_oid"]
        if tree[path] != oid:
            raise CollectionError("authority tree/blob 绑定漂移")
        raw = git.blob_bytes(oid)
        if not isinstance(raw, bytes) or _blob_oid(raw) != oid or _digest(raw) != authority[prefix + "_raw_sha256"]:
            raise CollectionError("authority blob/raw bytes 漂移")
        raw_values[prefix] = raw
    config_raw = raw_values["config"]
    try:
        config, _ = validate_config(json.loads(config_raw))
        if _canonical(config) != config_raw:
            raise CollectionError("authority config bytes 不是 canonical JSON")
    except (AuditFailure, ValueError, TypeError, UnicodeError) as exc:
        raise CollectionError("authority config 无效") from exc
    try:
        selection = json.loads(raw_values["selection"])
        if (not isinstance(selection, dict) or set(selection) != {"schema", "source_kind", "entries"}
                or selection["schema"] != "immutable_source_selection_request_v1"
                or selection["source_kind"] != "checkpoint_source_manifest_v1"
                or _canonical(selection) != raw_values["selection"]):
            raise CollectionError("selection schema/canonical bytes 无效")
        selected = selection["entries"]
        if not isinstance(selected, list) or not selected:
            raise CollectionError("selection entries 必须非空")
        ordered = []
        for ordinal, entry in enumerate(selected):
            if (not isinstance(entry, dict) or set(entry) != {"ordinal", "relative_path"}
                    or type(entry["ordinal"]) is not int or entry["ordinal"] != ordinal):
                raise CollectionError("selection ordinal/key 无效")
            path = entry["relative_path"]
            if (not isinstance(path, str) or "\0" in path
                    or any(component in ("", ".", "..") for component in path.split("/"))):
                raise CollectionError("selection 路径不规范")
            ordered.append(path)
        if ordered != sorted(set(ordered), key=lambda path: path.encode("utf-8")):
            raise CollectionError("selection 路径顺序或唯一性漂移")
        if len(paths) != len(ordered) or set(paths.values()) != set(ordered):
            raise CollectionError("source transport 与 selection 不一致")
    except (ValueError, TypeError, UnicodeError) as exc:
        raise CollectionError("selection 无效") from exc
    return tuple(ordered), config_raw


def collect_synthetic(*, authority: Mapping[str, str], lineage: Mapping[str, str], paths: Mapping[str, str], git: GitTransaction, root_fd: RootFdOpener, sink: EvidenceSink) -> dict[str, object]:
    ordered, config_raw = _bound_source_inputs(authority, lineage, paths, git)
    entries = tuple(_entry(root_fd, path, i) for i, path in enumerate(ordered))
    activation = object()
    handoff = _source_handoff(authority, tuple(entries), config_raw, activation)
    payload = handoff.take(activation)
    candidates = dict(payload.candidates)
    collection = dict(git.commit(COLLECTION_PATHS, None))
    if dict(git.lookup(collection["revision"])) != collection: raise CollectionError("collection committed-tree post-check drift")
    receipt = dict(git.commit((RECEIPT_PATH,), collection["revision"]))
    if dict(git.lookup(receipt["revision"])) != receipt or receipt["parent_revision"] != collection["revision"]: raise CollectionError("receipt committed-tree post-check drift")
    handoff_bytes = json.loads(handoff._logical_bytes)
    record: dict[str, object] = {"schema": SCHEMA, "status": "PASS", "execution": {"approval_formal_root": authority["root_revision"], "command_argv": ["synthetic"], "interpreter": "test", "phase": "complete"}, "tool": {"path": "tools/psm_wma/immutable_source_collection.py", "blob_native_oid": "0"*40, "raw_sha256": "0"*64}, "environment": {"workdir": "synthetic", "python_executable": "test", "cpu_only": True, "no_network": True, "sanitized_env_sha256": "0"*64}, "authority": dict(authority), "lineage": dict(lineage), "source_entries": list(entries), "handoff": {"candidate_handoff_sha256": _sha(handoff_bytes), "consumed_once": True}, "candidates": candidates, "collection": {**collection, "delta_paths": list(COLLECTION_PATHS)}, "receipt": {**receipt, "delta_paths": [RECEIPT_PATH], "blob_native_oid": "0"*40}, "post_checks": {key: True for key in ("authority", "lineage", "derivation", "collection", "receipt")}, "push_publication": {"pushed": False, "published": False}, "rollback": _null_rollback()}
    record["evidence_sha256"] = _sha(record); sink.emit(record); return record
