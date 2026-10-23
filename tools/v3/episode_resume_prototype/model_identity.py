"""READ-ONLY CPU design prototype; not wired into production evaluation.

Only checkpoint, num_steps, action_horizon and guidance are reuse invariants.
Source/runtime/config/plan observations are provenance, never a fifth equality.
No pickle is executed, no tensor/model is loaded and no manifest is written.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import pickletools
import re
import stat
import struct
from pathlib import Path

SCHEMA = "psm_eval_model_identity_v1"
LEGACY_SCHEMAS = {"psm_v3_eval_identity_v1", "psm_v3_eval_identity_vendor_v1"}
PARAMETERS = {"checkpoint", "num_steps", "action_horizon", "guidance"}
_SHA = re.compile(r"[0-9a-f]{64}\Z")


class IdentityInputError(ValueError):
    """Unreadable/corrupt input, distinct from a valid old/new parameter mismatch."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _canonical(value) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    except (TypeError, ValueError) as error:
        raise IdentityInputError("INVALID_JSON_VALUE", str(error)) from error


def _digest(value) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _scalar_parameters(num_steps, action_horizon, guidance) -> dict:
    for name, value in (("num_steps", num_steps), ("action_horizon", action_horizon)):
        if type(value) is not int or value <= 0:
            raise IdentityInputError("INVALID_MODEL_PARAMETER", f"{name} must be a positive integer; got {value!r}")
    if type(guidance) not in (int, float) or not math.isfinite(guidance):
        raise IdentityInputError("INVALID_MODEL_PARAMETER", f"guidance must be finite; got {guidance!r}")
    return {
        "num_steps": num_steps,
        "action_horizon": action_horizon,
        "guidance": 0.0 if guidance == 0 else float(guidance),
    }


def _stat_witness(value):
    return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns


def _snapshot(model: Path) -> dict:
    paths = [model / ".metadata", *sorted(model.glob("*.distcp"))]
    if len(paths) < 2:
        raise IdentityInputError("CHECKPOINT_INPUT_INVALID", "checkpoint model has no shard")
    snapshot = {}
    for path in paths:
        if path.is_symlink():
            raise IdentityInputError("CHECKPOINT_INPUT_INVALID", f"symlink model file: {path}")
        observed = path.stat()
        if not stat.S_ISREG(observed.st_mode) or observed.st_size <= 0:
            raise IdentityInputError("CHECKPOINT_INPUT_INVALID", f"missing/empty/nonregular model file: {path}")
        snapshot[path.name] = observed
    return snapshot


def _metadata_header(data: bytes) -> None:
    # Parse opcodes only. GLOBAL/REDUCE are never imported, instantiated or run.
    if len(data) < 3 or data[0] != 0x80 or not 2 <= data[1] <= 5:
        raise IdentityInputError("CHECKPOINT_HEADER_INVALID", "model .metadata lacks a supported pickle header")
    try:
        last = None
        for operation, _, position in pickletools.genops(data):
            last = operation.name, position
        if last != ("STOP", len(data) - 1):
            raise ValueError("metadata has trailing bytes or no STOP")
    except (ValueError, UnicodeError, IndexError) as error:
        raise IdentityInputError(
            "CHECKPOINT_HEADER_INVALID", f"malformed metadata pickle structure: {error}"
        ) from error


def _shard_header(header: bytes, size: int) -> None:
    # torch.save-based DCP shard containers start with a ZIP local-file header.
    # This is deliberately NOT a tensor/metadata-offset/CRC load validation.
    if len(header) < 30 or header[:4] != b"PK\x03\x04":
        raise IdentityInputError("CHECKPOINT_HEADER_INVALID", "model shard lacks a torch ZIP local-file header")
    fields = struct.unpack("<4s5H3I2H", header[:30])
    name_size, extra_size = fields[-2:]
    if name_size <= 0 or 30 + name_size + extra_size > size:
        raise IdentityInputError("CHECKPOINT_HEADER_INVALID", "model shard ZIP header exceeds file bounds")


def _read_hash(path: Path, expected, *, metadata: bool) -> str:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        before = os.fstat(stream.fileno())
        if _stat_witness(before) != _stat_witness(expected):
            raise IdentityInputError("CHECKPOINT_CHANGED_DURING_READ", f"model changed before read: {path}")
        digest, payload, header = hashlib.sha256(), [], b""
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
            if not header:
                header = chunk[:30]
            if metadata:
                payload.append(chunk)
        after = os.fstat(stream.fileno())
    if path.is_symlink() or _stat_witness(after) != _stat_witness(before):
        raise IdentityInputError("CHECKPOINT_CHANGED_DURING_READ", f"model changed during read: {path}")
    if metadata:
        _metadata_header(b"".join(payload))
    else:
        _shard_header(header, before.st_size)
    return digest.hexdigest()


def build_model_identity(*, checkpoint: Path, num_steps: int, action_horizon: int, guidance: float) -> dict:
    """Read all model bytes to establish a new strong baseline, without tensor loads.

    `observed_checkpoint_stats` is a fresh legacy-bridge observation outside the
    hard digest. New full-hash identities are stable under metadata timestamp
    changes when all model bytes and the actual checkpoint path are unchanged.
    Header checks do not prove a real DCP is semantically loadable or complete.
    """
    scalar = _scalar_parameters(num_steps, action_horizon, guidance)
    try:
        checkpoint = Path(checkpoint).resolve(strict=True)
        model = checkpoint / "model"
        if not model.is_dir() or model.is_symlink():
            raise IdentityInputError("CHECKPOINT_INPUT_INVALID", "checkpoint must contain an ordinary model/ directory")
        before = _snapshot(model)
        metadata_hash = _read_hash(model / ".metadata", before[".metadata"], metadata=True)
        shards = [
            {
                "name": name,
                "bytes": info.st_size,
                "sha256": _read_hash(model / name, info, metadata=False),
            }
            for name, info in before.items()
            if name != ".metadata"
        ]
        after = _snapshot(model)
        if {name: _stat_witness(value) for name, value in before.items()} != {
            name: _stat_witness(value) for name, value in after.items()
        }:
            raise IdentityInputError("CHECKPOINT_CHANGED_DURING_READ", "model file inventory changed during hashing")
    except OSError as error:
        raise IdentityInputError("CHECKPOINT_INPUT_INVALID", f"checkpoint input unavailable: {error}") from error
    parameters = {
        "checkpoint": {
            "path": str(checkpoint),
            "scope": "full_model_sha256_v1",
            "metadata_sha256": metadata_hash,
            "shards": shards,
        },
        **scalar,
    }
    body = {"schema": SCHEMA, "parameters": parameters}
    return {
        **body,
        "digest": _digest(body),
        "observed_checkpoint_stats": [
            [name, value.st_size, value.st_mtime_ns, value.st_ctime_ns]
            for name, value in after.items()
            if name != ".metadata"
        ],
        "validation_scope": "full_byte_hash_plus_nonexecuting_headers_not_tensor_load_or_DCP_completeness",
    }


def _checked(identity: dict) -> dict:
    if not isinstance(identity, dict) or identity.get("schema") != SCHEMA:
        raise IdentityInputError("MODEL_IDENTITY_INVALID", "unknown model identity schema")
    parameters = identity.get("parameters")
    if not isinstance(parameters, dict) or set(parameters) != PARAMETERS:
        raise IdentityInputError("MODEL_IDENTITY_INVALID", "model identity requires exactly the four parameters")
    scalar = _scalar_parameters(parameters["num_steps"], parameters["action_horizon"], parameters["guidance"])
    if scalar != {key: parameters[key] for key in scalar}:
        raise IdentityInputError("MODEL_IDENTITY_INVALID", "noncanonical scalar parameters")
    checkpoint = parameters["checkpoint"]
    if (
        not isinstance(checkpoint, dict)
        or set(checkpoint) != {"path", "scope", "metadata_sha256", "shards"}
        or not isinstance(checkpoint["path"], str)
        or not Path(checkpoint["path"]).is_absolute()
        or checkpoint["scope"] != "full_model_sha256_v1"
        or not isinstance(checkpoint["metadata_sha256"], str)
        or not _SHA.fullmatch(checkpoint["metadata_sha256"])
        or not isinstance(checkpoint["shards"], list)
        or not checkpoint["shards"]
    ):
        raise IdentityInputError("MODEL_IDENTITY_INVALID", "invalid checkpoint content identity")
    names = []
    for row in checkpoint["shards"]:
        if (
            not isinstance(row, dict)
            or set(row) != {"name", "bytes", "sha256"}
            or not isinstance(row["name"], str)
            or Path(row["name"]).name != row["name"]
            or not row["name"].endswith(".distcp")
            or type(row["bytes"]) is not int
            or row["bytes"] <= 0
            or not isinstance(row["sha256"], str)
            or not _SHA.fullmatch(row["sha256"])
        ):
            raise IdentityInputError("MODEL_IDENTITY_INVALID", "invalid model shard content identity")
        names.append(row["name"])
    if names != sorted(set(names)):
        raise IdentityInputError("MODEL_IDENTITY_INVALID", "duplicate/noncanonical shard inventory")
    if identity.get("digest") != _digest({"schema": SCHEMA, "parameters": parameters}):
        raise IdentityInputError("MODEL_IDENTITY_INVALID", "model identity digest mismatch")
    return parameters


def _mismatch(parameter: str, old, new, reason: str) -> dict:
    return {"parameter": parameter, "reason": reason, "old": copy.deepcopy(old), "new": copy.deepcopy(new)}


def compare_model_identity(old: dict, new: dict) -> dict:
    """Return explicit old/new errors; source, runtime and invocation are not compared."""
    old_parameters, new_parameters = _checked(old), _checked(new)
    errors = [
        _mismatch(name, old_parameters[name], new_parameters[name], "hard model parameter changed")
        for name in ("checkpoint", "num_steps", "action_horizon", "guidance")
        if old_parameters[name] != new_parameters[name]
    ]
    return {"status": "MODEL_MISMATCH" if errors else "MATCH", "errors": errors, "warnings": []}


def _legacy_projection(identity: dict) -> dict:
    protocol = identity.get("protocol")
    if not isinstance(protocol, dict):
        raise IdentityInputError("LEGACY_MANIFEST_INVALID", "legacy protocol missing")
    try:
        scalar = _scalar_parameters(protocol["num_steps"], protocol["R"], protocol["guidance"])
        checkpoint = identity["checkpoint"]
        metadata_hash = identity["model_metadata_sha256"]
        shards = identity["model_shard_stat_witnesses"]
    except KeyError as error:
        raise IdentityInputError(
            "LEGACY_MANIFEST_INVALID", f"legacy four-parameter authority missing: {error}"
        ) from error
    if (
        not isinstance(checkpoint, str)
        or not Path(checkpoint).is_absolute()
        or not isinstance(metadata_hash, str)
        or not _SHA.fullmatch(metadata_hash)
        or not isinstance(shards, list)
        or not shards
    ):
        raise IdentityInputError("LEGACY_MANIFEST_INVALID", "legacy checkpoint authority missing")
    names = []
    for row in shards:
        if (
            not isinstance(row, list)
            or len(row) != 4
            or not isinstance(row[0], str)
            or Path(row[0]).name != row[0]
            or not row[0].endswith(".distcp")
            or any(type(value) is not int for value in row[1:])
            or row[1] <= 0
        ):
            raise IdentityInputError("LEGACY_MANIFEST_INVALID", "invalid legacy shard stat witness")
        names.append(row[0])
    if names != sorted(set(names)):
        raise IdentityInputError("LEGACY_MANIFEST_INVALID", "duplicate/noncanonical legacy shard inventory")
    return {
        "checkpoint": {
            "path": checkpoint,
            "metadata_sha256": metadata_hash,
            "model_shard_stat_witnesses": copy.deepcopy(shards),
            "scope": "legacy_metadata_sha256_and_shard_stats_not_payload_hash",
        },
        **scalar,
    }


def _provenance_warnings(old: dict, new: dict | None) -> list[dict]:
    new = new or {}
    warnings = []
    for keys, label in (
        (("root_sha", "child_sha"), "SOURCE"),
        (("evaluation_runtime",), "RUNTIME"),
        (("config_sha256",), "CONFIG"),
    ):
        old_values = {key: old.get(key) for key in keys}
        new_values = {key: new.get(key) for key in keys}
        unknown = any(value is None for value in (*old_values.values(), *new_values.values()))
        if unknown or old_values != new_values:
            warnings.append(
                {
                    "code": f"{label}_PROVENANCE_UNKNOWN" if unknown else f"{label}_PROVENANCE_CHANGED",
                    "old": copy.deepcopy(old_values),
                    "new": copy.deepcopy(new_values),
                    "reuse_blocked": False,
                    "comparability": "UNASSESSED_CONVENIENCE_AGGREGATE_NOT_SAME_CONDITION_BENCHMARK",
                }
            )
    return warnings


def legacy_ingest(manifest: dict, current_identity: dict, *, current_provenance: dict | None = None) -> dict:
    """Verify an old manifest without rewriting its digest or historical evidence.

    `current_identity` must be a freshly read build_model_identity() observation.
    A legacy stat bridge cannot retrospectively attest historical payload bytes;
    it never invents an old payload hash from current files. Individual episodes
    still require validation against original_identity/original_manifest_digest.
    """
    current = _checked(current_identity)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("identity"), dict):
        raise IdentityInputError("LEGACY_MANIFEST_INVALID", "legacy manifest must contain identity")
    original = manifest["identity"]
    if original.get("schema") not in LEGACY_SCHEMAS or manifest.get("digest") != _digest(original):
        raise IdentityInputError("LEGACY_MANIFEST_INVALID", "unknown or corrupt legacy manifest identity")
    old = _legacy_projection(original)
    observed = current_identity.get("observed_checkpoint_stats")
    if (
        not isinstance(observed, list)
        or any(
            not isinstance(row, list)
            or len(row) != 4
            or not isinstance(row[0], str)
            or any(type(value) is not int for value in row[1:])
            for row in observed
        )
        or [row[0] for row in observed] != [row["name"] for row in current["checkpoint"]["shards"]]
        or [row[1] for row in observed] != [row["bytes"] for row in current["checkpoint"]["shards"]]
    ):
        raise IdentityInputError("CURRENT_OBSERVATION_INVALID", "fresh legacy-bridge stat observation missing")
    current_bridge = {
        "path": current["checkpoint"]["path"],
        "metadata_sha256": current["checkpoint"]["metadata_sha256"],
        "model_shard_stat_witnesses": observed,
        "scope": old["checkpoint"]["scope"],
    }
    errors = []
    if old["checkpoint"] != current_bridge:
        errors.append(_mismatch("checkpoint", old["checkpoint"], current_bridge, "legacy checkpoint witness changed"))
    for name in ("num_steps", "action_horizon", "guidance"):
        if old[name] != current[name]:
            errors.append(_mismatch(name, old[name], current[name], "hard model parameter changed"))
    warnings = [
        {
            "code": "LEGACY_PAYLOAD_HASH_NOT_RETROSPECTIVELY_AVAILABLE",
            "reuse_blocked": False,
            "scope": old["checkpoint"]["scope"],
            "message": "Only historical metadata SHA and shard size/mtime/ctime match; current full hashes are a NEW baseline.",
        },
        *_provenance_warnings(original, current_provenance),
    ]
    return {
        "schema": "psm_legacy_episode_ingest_decision_v1",
        "status": "MODEL_MISMATCH" if errors else "LEGACY_STAT_BRIDGE_MATCH",
        "errors": errors,
        "warnings": warnings,
        "original_manifest_digest": manifest["digest"],
        "original_identity": copy.deepcopy(original),
        "legacy_model_parameters": old,
        "current_model_identity_ref": current_identity["digest"],
        "checkpoint_binding_scope": old["checkpoint"]["scope"],
        "historical_payload_sha256": None,
        "original_provenance": {
            "root_sha": original.get("root_sha"),
            "child_sha": original.get("child_sha"),
            "config_sha256": original.get("config_sha256"),
            "evaluation_runtime": copy.deepcopy(original.get("evaluation_runtime")),
        },
        "original_invocation_plan": copy.deepcopy(original.get("protocol")),
        "episode_validation": "REQUIRED_USING_ORIGINAL_MANIFEST_NOT_RELABELED_WITH_CURRENT_DIGEST",
    }
