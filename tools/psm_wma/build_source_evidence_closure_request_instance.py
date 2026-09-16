"""CPU/static construction and verification of a source-evidence request instance."""

import hashlib
import json
from collections.abc import Mapping


TOP_LEVEL_KEYS = (
    "schema", "formal_root", "child_gitlink", "authority", "source", "executor",
    "producer", "record", "receipt", "publication", "root_audit", "preflight",
    "execution", "sha256",
)
SCHEMA = "root_source_evidence_closure_request_instance_v1"


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8") + b"\n"


def _exact_object(value, keys, name):
    if not isinstance(value, Mapping) or tuple(value) != tuple(keys):
        raise ValueError(f"{name}: exact keys required")
    return dict(value)


def build_request_instance(bundle):
    """Build canonical bytes from a fully observed in-memory bundle; never performs I/O."""
    if not isinstance(bundle, Mapping):
        raise TypeError("bundle must be a mapping")
    obj = dict(bundle)
    if set(obj) != set(TOP_LEVEL_KEYS) or len(obj) != len(TOP_LEVEL_KEYS) or obj.get("schema") != SCHEMA:
        raise ValueError("instance: exact top-level schema required")
    if not isinstance(obj["sha256"], str) or obj["sha256"] != "":
        raise ValueError("instance: sha256 placeholder must be empty")
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
    digest = hashlib.sha256(_canonical({k: value[k] for k in TOP_LEVEL_KEYS if k != "sha256"})).hexdigest()
    if value.get("sha256") != digest:
        raise ValueError("instance: sha256 mismatch")
    return digest
