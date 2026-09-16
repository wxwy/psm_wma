"""CPU/static construction and verification of a source-evidence request instance."""

import hashlib
import json
import re
from collections.abc import Mapping
from tools.psm_wma.immutable_source_collection import SOURCE_PACKAGE_KEYS, SOURCE_WITNESS_KEYS


TOP_LEVEL_KEYS = (
    "schema", "formal_root", "child_gitlink", "authority", "source", "executor",
    "producer", "record", "receipt", "publication", "root_audit", "preflight",
    "execution", "sha256",
)
SCHEMA = "root_source_evidence_closure_request_instance_v1"
SECTION_KEYS = {
    "authority": ("fixed_ref", "candidate_revision", "selection_path", "selection_blob_native_oid", "selection_raw_sha256", "config_path", "config_blob_native_oid", "config_raw_sha256", "local_ref_revision", "remote_ref_revision"),
    "source": ("root_fd", "source_kind", "selection_raw_sha256", "selected_paths", "root_identity"),
    "executor": ("module_path", "module_blob_native_oid", "module_raw_sha256", "interpreter_path", "interpreter_raw_sha256", "git_path", "git_raw_sha256", "argv", "cwd", "index_path", "evidence_path", "sanitized_env_sha256"),
    "producer": ("module_path", "module_blob_native_oid", "module_raw_sha256", "callables", "one_shot_abi"),
    "record": ("path", "schema", "keys", "source_digest_receipt_mapping"),
    "receipt": ("path", "schema", "keys", "parent_root_revision", "child_gitlink", "post_commit_boundary"),
    "publication": ("package_schema", "package_keys", "witness_schema", "witness_keys", "package_path", "witness_path", "verifier_identity"),
    "root_audit": ("module_path", "module_blob_native_oid", "module_raw_sha256", "argv", "pass_predicate"),
    "preflight": ("absent_paths", "absent_refs", "head_revision", "index_tree_native_oid", "worktree_snapshot_sha256", "zero_mutation"),
    "execution": ("order", "one_shot", "no_retry", "pass_hard_stop", "failure_rollback"),
}
RECORD_KEYS = ("schema", "source_kind", "immutable_source_identifier", "source_manifest_sha256", "source_input_sha256", "checkpoint_source_descriptor_sha256")
RECEIPT_KEYS = ("schema", "collection_formal_root_revision", "collection_artifact_path", "collection_artifact_schema", "collection_artifact_sha256", "collection_artifact_blob_native_oid", "immutable_source_identifier", "source_manifest_sha256", "source_input_sha256", "checkpoint_source_descriptor_sha256", "canonical_model_config_sha256", "canonical_model_config_artifact_path", "canonical_model_config_artifact_sha256")


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8") + b"\n"


def _exact_object(value, keys, name):
    if not isinstance(value, Mapping) or set(value) != set(keys) or len(value) != len(keys):
        raise ValueError(f"{name}: exact keys required")
    return dict(value)


def _validate_sections(obj):
    for name, keys in SECTION_KEYS.items():
        section = _exact_object(obj[name], keys, name)
        if name == "record" and tuple(section["keys"]) != RECORD_KEYS:
            raise ValueError("record: fixed keys required")
        if name == "receipt" and tuple(section["keys"]) != RECEIPT_KEYS:
            raise ValueError("receipt: fixed keys required")
        if name == "record" and section["source_digest_receipt_mapping"] != {
            key: key for key in RECORD_KEYS[2:]
        }:
            raise ValueError("record: digest mapping required")
        for key, value in section.items():
            if key in ("keys", "callables", "argv", "order", "absent_paths", "absent_refs", "selected_paths", "package_keys", "witness_keys"):
                if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
                    raise ValueError(f"{name}.{key}: ordered string array required")
            elif key in ("zero_mutation", "one_shot", "no_retry", "pass_hard_stop"):
                if not isinstance(value, bool):
                    raise ValueError(f"{name}.{key}: boolean required")
            elif not isinstance(value, (str, bool, int, dict)):
                raise ValueError(f"{name}.{key}: invalid value type")
            elif isinstance(value, str) and ("sha256" in key or key in ("module_blob_native_oid", "selection_blob_native_oid", "candidate_revision", "parent_root_revision", "child_gitlink")):
                size = 64 if "sha256" in key else 40
                if not re.fullmatch(r"[0-9a-f]{%d}" % size, value):
                    raise ValueError(f"{name}.{key}: lowercase hex identity required")
        if name == "publication" and (tuple(section["package_keys"]) != SOURCE_PACKAGE_KEYS or tuple(section["witness_keys"]) != SOURCE_WITNESS_KEYS):
            raise ValueError("publication: fixed package/witness keys required")
        if name == "execution" and tuple(section["order"]) != ("collection", "producer", "record", "receipt", "root_audit"):
            raise ValueError("execution: fixed order required")


def build_request_instance(bundle):
    """Build canonical bytes from a fully observed in-memory bundle; never performs I/O."""
    if not isinstance(bundle, Mapping):
        raise TypeError("bundle must be a mapping")
    obj = dict(bundle)
    if set(obj) != set(TOP_LEVEL_KEYS) or len(obj) != len(TOP_LEVEL_KEYS) or obj.get("schema") != SCHEMA:
        raise ValueError("instance: exact top-level schema required")
    if not isinstance(obj["sha256"], str) or obj["sha256"] != "":
        raise ValueError("instance: sha256 placeholder must be empty")
    _validate_sections(obj)
    obj["sha256"] = hashlib.sha256(_canonical({k: obj[k] for k in TOP_LEVEL_KEYS if k != "sha256"})).hexdigest()
    raw = _canonical(obj)
    if verify_instance_bytes(raw) != obj["sha256"]:
        raise ValueError("instance: digest round-trip failed")
    return raw


def verify_instance_bytes(raw):
    """Strictly verify canonical bytes and return the self-excluding instance digest."""
    if not isinstance(raw, bytes) or not raw.endswith(b"\n"):
        raise ValueError("instance: canonical UTF-8 bytes required")
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("instance: invalid JSON") from exc
    if _canonical(value) != raw or set(value) != set(TOP_LEVEL_KEYS) or len(value) != len(TOP_LEVEL_KEYS) or value.get("schema") != SCHEMA:
        raise ValueError("instance: non-canonical or non-exact")
    _validate_sections(value)
    digest = hashlib.sha256(_canonical({k: value[k] for k in TOP_LEVEL_KEYS if k != "sha256"})).hexdigest()
    if value.get("sha256") != digest:
        raise ValueError("instance: sha256 mismatch")
    return digest
