#!/usr/bin/env python3
"""R09-B2 P5 exporter helpers; real export requires a separate approval."""

from __future__ import annotations

import hashlib
import dataclasses
import enum
import json
import math
import os
from pathlib import Path
import stat
import subprocess
import sys
import uuid
from collections.abc import Mapping
from typing import Any

from tools.g0.r09_b2_interpreter_provenance import (
    ProvenanceError,
    is_verified_loader_argv,
    sha256_file,
    verified_loader_argv,
)


SCHEMA = "r09_b2_p5_full_config_diff_v2"
FROZEN_OVERRIDES = ("trainer.max_iter=100", "trainer.save_zero_checkpoint=true")
FROZEN_PRODUCTION_ROOT = Path("/disk/rl/psm_wma_p4_d005_retry")
PYTHON_CHILD_LOCALE = {"LC_CTYPE": "C.UTF-8"}
FROZEN_CHILD_REQUEST_SHA256 = {
    "recurrent": "0871417b9e8898b7be2ab4215a88ee1546ec6019592fa084c3d96009747318ad",
    "ttt_fast_weight": "9c56140f1c3570c142f9bc219ef82e7880cde4fdc51082e375f796a4c4360bee",
}
CHILD_REQUEST_KEYS = {"backend", "root", "toml", "overrides", "command_argv", "cwd", "interpreter", "environment", "d005_sha256", "p4_record_sha256", "p4_verification_sha256", "p3_verifier_sha256", "source", "budget", "inputs", "outputs"}
LOADER_REQUEST_SCHEMA = "r09_b2_p5_verified_loader_request_v1"
LOADER_REQUEST_KEYS = {"schema_version", "child_request", "child_request_sha256", "child_output"}
BOOTSTRAP_RELATIVE = "tools/g0/export_r09_b2_p5_resolved_config.py"
P4_V4_PREFLIGHT_RELATIVE = Path("artifacts/g0/r09/b2/p4_execution_preflight_v4")
P4_V4_BACKENDS = ("recurrent", "ttt_fast_weight")
P5_FORBIDDEN_ENVIRONMENT = (
    "GLIBC_TUNABLES", "LD_AUDIT", "LD_ASSUME_KERNEL", "LD_BIND_NOT", "LD_DEBUG",
    "LD_DEBUG_OUTPUT", "LD_LIBRARY_PATH", "LD_ORIGIN_PATH", "LD_PRELOAD", "LD_PROFILE",
    "LD_SHOW_AUXV", "LD_TRACE_LOADED_OBJECTS", "LD_USE_LOAD_BIAS", "MASTER_ADDR",
    "MASTER_PORT", "PYTHONPATH", "RANK", "WORLD_SIZE", "LOCAL_RANK",
)


class CanonicalizationError(ValueError):
    """A resolved config value cannot be represented faithfully and deterministically."""


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256_json(value: object) -> str:
    import hashlib
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _read_json(path: Path) -> tuple[dict[str, Any], str]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"P4-v4 evidence must be a regular file: {path}")
    raw = path.read_bytes()
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"P4-v4 evidence JSON is malformed: {path}") from exc
    if not isinstance(value, dict) or canonical_bytes(value) != raw:
        raise ValueError(f"P4-v4 evidence is not canonical JSON: {path}")
    return value, hashlib.sha256(raw).hexdigest()


def _self_sha(value: Mapping[str, Any], key: str) -> bool:
    return isinstance(value.get(key), str) and value[key] == sha256_json({name: item for name, item in value.items() if name != key})


def _path_identity(value: object, *, kind: str) -> Path:
    if not isinstance(value, Mapping) or set(value) != {"root", "resolved_root", "kind", "identity_sha256"}:
        raise ValueError("P4-v4 path identity schema is malformed")
    if value.get("kind") != kind or not _self_sha(value, "identity_sha256"):
        raise ValueError("P4-v4 path identity kind or SHA differs")
    root, resolved = value.get("root"), value.get("resolved_root")
    if not isinstance(root, str) or not isinstance(resolved, str):
        raise ValueError("P4-v4 path identity path is malformed")
    path = Path(root)
    if not path.is_absolute() or path.is_symlink() or path.resolve() != path or resolved != str(path):
        raise ValueError("P4-v4 path identity is not canonical")
    return path


def _validate_roster(run_root: Path, staging_root: Path, token: str, roster: object, manifest: object) -> None:
    if not isinstance(roster, Mapping) or set(roster) != {"entries", "sha256"} or not _self_sha(roster, "sha256"):
        raise ValueError("P4-v4 run-root roster schema or SHA differs")
    if not isinstance(manifest, Mapping) or set(manifest) != {"entries", "sha256"} or not _self_sha(manifest, "sha256"):
        raise ValueError("P4-v4 payload manifest schema or SHA differs")
    entries = roster["entries"]
    if not isinstance(entries, list) or not all(isinstance(item, Mapping) and set(item) == {"path", "type", "mode", "sha256"} for item in entries):
        raise ValueError("P4-v4 run-root roster entries are malformed")
    expected_files = {item["path"] for item in manifest["entries"] if isinstance(item, Mapping) and item.get("type") == "regular"}
    expected = {"import_staging", f"import_staging/{token}", "preflight.json"} | expected_files
    observed = {item["path"] for item in entries}
    if observed != expected or any(not isinstance(path, str) or path.startswith("/") or ".." in Path(path).parts for path in observed):
        raise ValueError("P4-v4 run-root roster path set differs")
    if staging_root != run_root / "import_staging" / token:
        raise ValueError("P4-v4 staging root differs from run-root token path")
    for item in entries:
        path = run_root / item["path"]
        mode = 0o555 if item["type"] == "directory" else 0o444
        if item["type"] not in {"directory", "regular"} or not path.exists() or path.is_symlink() or stat.S_IMODE(path.stat().st_mode) != mode:
            raise ValueError("P4-v4 run-root roster mode/type differs")
        if item["type"] == "regular" and (path.stat().st_nlink != 1 or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]):
            raise ValueError("P4-v4 run-root roster file identity differs")


def p5_effective_environment(recurrent: Mapping[str, Any], ttt: Mapping[str, Any]) -> dict[str, str]:
    """Construct the P5 child environment from empty, never ambient parent state."""
    def values(record: Mapping[str, Any]) -> dict[str, str]:
        environment = record.get("effective_environment")
        if not isinstance(environment, Mapping) or set(environment) != {"set", "unset", "inherit_allowlist", "sha256"} or not _self_sha(environment, "sha256"):
            raise ValueError("P4-v4 effective environment schema is malformed")
        if environment["inherit_allowlist"] != [] or tuple(environment["unset"]) != P5_FORBIDDEN_ENVIRONMENT:
            raise ValueError("P4-v4 environment grammar differs from P5 empty-environment contract")
        if not isinstance(environment["set"], Mapping):
            raise ValueError("P4-v4 effective environment set is malformed")
        native = record.get("native_loader_environment")
        if (not isinstance(native, Mapping) or set(native) != {"set", "unset", "inherit_allowlist", "sha256"}
                or not _self_sha(native, "sha256") or native["set"] != {}
                or native["inherit_allowlist"] != [] or tuple(native["unset"]) != P5_FORBIDDEN_ENVIRONMENT):
            raise ValueError("P4-v4 native-loader environment schema is malformed")
        return {str(key): str(value) for key, value in environment["set"].items()}
    left, right = values(recurrent), values(ttt)
    if left != right or set(left) & set(P5_FORBIDDEN_ENVIRONMENT):
        raise ValueError("P4-v4 backend environments cannot be projected into P5")
    return {**dict(sorted(left.items())), **PYTHON_CHILD_LOCALE}


def load_p4_v4_preflight(evidence_root: Path) -> dict[str, dict[str, Any]]:
    """Load the only admissible P4→P5 handoff; historical D005 evidence is ignored."""
    root = evidence_root.resolve()
    result: dict[str, dict[str, Any]] = {}
    request_keys = {"schema_version", "backend", "production_source", "p4_run", "p4_staging", "request_defaults", "interpreter", "loader_argv", "effective_environment", "native_loader_environment", "payload_manifest", "producer"}
    result_keys = request_keys | {"status", "request_sha256", "native_closure", "pre_p5_run_root_roster"}
    result_keys.remove("schema_version")
    result_keys.add("schema_version")
    verification_keys = {"schema_version", "status", "backend", "request_sha256", "result_sha256", "checks", "verifier", "verification_sha256"}
    for backend in P4_V4_BACKENDS:
        directory = root / P4_V4_PREFLIGHT_RELATIVE / backend
        request, request_sha = _read_json(directory / "request.json")
        outcome, outcome_sha = _read_json(directory / "result.json")
        verification, _ = _read_json(directory / "verification.json")
        if (set(request) != request_keys or set(outcome) != result_keys or set(verification) != verification_keys
                or request.get("backend") != backend or outcome.get("backend") != backend or verification.get("backend") != backend
                or outcome.get("status") != "PASS" or verification.get("status") != "PASS"
                or outcome.get("request_sha256") != request_sha or verification.get("request_sha256") != request_sha
                or verification.get("result_sha256") != outcome_sha):
            raise ValueError("P4-v4 preflight schema, backend, status, or SHA chain differs")
        source = request["production_source"]
        if not isinstance(source, Mapping):
            raise ValueError("P4-v4 production source is malformed")
        source_root = _path_identity(source.get("identity"), kind="git_source")
        run_root = _path_identity(request["p4_run"].get("identity") if isinstance(request["p4_run"], Mapping) else None, kind="run_root")
        staging = request["p4_staging"]
        if not isinstance(staging, Mapping):
            raise ValueError("P4-v4 staging is malformed")
        staging_root = _path_identity(staging.get("identity"), kind="staging_root")
        token = request["p4_run"].get("run_token") if isinstance(request["p4_run"], Mapping) else None
        if not isinstance(token, str) or request["p4_run"] != outcome["p4_run"] or request["p4_staging"] != outcome["p4_staging"]:
            raise ValueError("P4-v4 run/staging result binding differs")
        if not (source_root / "cosmos-framework").is_dir() or staging.get("relative_path") != f"import_staging/{token}":
            raise ValueError("P4-v4 child cwd or staging relative path differs")
        roots, runtime = staging.get("payload_import_roots"), staging.get("runtime_sys_path")
        if (not isinstance(roots, list) or not roots or not all(isinstance(item, Mapping) and set(item) == {"relative_root", "subtree_manifest_sha256"} for item in roots)
                or not isinstance(runtime, list) or runtime != [str(staging_root / item["relative_root"]) for item in roots]
                or any(not isinstance(item["relative_root"], str) or not (staging_root / item["relative_root"]).is_dir() or (staging_root / item["relative_root"]).is_symlink() for item in roots)):
            raise ValueError("P4-v4 staging runtime sys.path differs from its import roots")
        _validate_roster(run_root, staging_root, token, outcome["pre_p5_run_root_roster"], request["payload_manifest"])
        result[backend] = {"request": request, "result": outcome, "verification": verification}
    p5_effective_environment(result["recurrent"]["request"], result["ttt_fast_weight"]["request"])
    return result


def _callable(value: object) -> dict[str, str]:
    module, qualname = getattr(value, "__module__", None), getattr(value, "__qualname__", None)
    if not isinstance(module, str) or not isinstance(qualname, str) or "<locals>" in qualname:
        raise CanonicalizationError(f"callable has no stable FQN: {type(value)!r}")
    return {"__psm_type__": "callable", "fqn": f"{module}.{qualname}"}


def canonicalize(value: Any, seen: set[int] | None = None) -> Any:
    """Convert the complete resolved tree without repr(), omission, or address leakage."""
    seen = set() if seen is None else seen
    if value is None or isinstance(value, (bool, str, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise CanonicalizationError("non-finite float")
        return value
    if isinstance(value, Path):
        return {"__psm_type__": "path", "value": value.as_posix()}
    if isinstance(value, enum.Enum):
        cls = type(value)
        return {"__psm_type__": "enum", "fqn": f"{cls.__module__}.{cls.__qualname__}", "name": value.name}
    if callable(value):
        return _callable(value)
    identity = id(value)
    if identity in seen:
        raise CanonicalizationError("cycle in resolved config")
    if isinstance(value, Mapping):
        seen.add(identity)
        try:
            if not all(isinstance(key, str) for key in value):
                raise CanonicalizationError("non-string mapping key")
            return {key: canonicalize(value[key], seen) for key in sorted(value)}
        finally:
            seen.remove(identity)
    if isinstance(value, (list, tuple)):
        seen.add(identity)
        try:
            return [canonicalize(item, seen) for item in value]
        finally:
            seen.remove(identity)
    if hasattr(type(value), "__attrs_attrs__"):
        return canonicalize({field.name: getattr(value, field.name) for field in type(value).__attrs_attrs__}, seen)
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return canonicalize(dataclasses.asdict(value), seen)
    if "${" in str(value):
        raise CanonicalizationError("unresolved interpolation")
    raise CanonicalizationError(f"unsupported resolved-config value: {type(value)!r}")


def parse_d005_command(record: Mapping[str, Any]) -> tuple[str, list[str]]:
    """Derive, never recreate, the production TOML and exact trailing overrides.

    P4 v4 freezes these as request defaults because its D005 no longer admits a
    direct Python/module argv.  The legacy branch remains parser-only so old,
    already-closed evidence can still be inspected; it is not an executable
    launch admission path.
    """
    template = record.get("interpreter_provenance_template")
    if isinstance(template, Mapping):
        defaults = template.get("request_defaults")
        if not isinstance(defaults, Mapping):
            raise ValueError("P4 v4 request defaults are malformed")
        toml, overrides = defaults.get("toml"), defaults.get("overrides")
        if not isinstance(toml, str) or not isinstance(overrides, list) or not all(isinstance(item, str) for item in overrides):
            raise ValueError("P4 v4 request defaults are malformed")
        if tuple(overrides) != FROZEN_OVERRIDES:
            raise ValueError("P4 v4 request defaults must be the frozen ordered 100-update pair")
        return toml, list(overrides)
    command = record.get("command")
    if not isinstance(command, Mapping) or command.get("executable") is not False:
        raise ValueError("P5 requires a non-executable P4 D005 command")
    argv = command.get("argv")
    if not isinstance(argv, list) or not all(isinstance(token, str) for token in argv):
        raise ValueError("D005 argv must be a string token array")
    toml_tokens = [token for token in argv if token.startswith("--sft-toml=")]
    if len(toml_tokens) != 1:
        raise ValueError("D005 argv must contain exactly one --sft-toml=<path>")
    index = argv.index(toml_tokens[0])
    overrides = argv[index + 1 :]
    if tuple(overrides) != FROZEN_OVERRIDES:
        raise ValueError("D005 trailing overrides must be the frozen ordered 100-update pair")
    if any("=" not in item for item in overrides):
        raise ValueError("D005 trailing token is not a Hydra override")
    return toml_tokens[0].split("=", 1)[1], overrides


def sanitized_environment(contract: Mapping[str, Any], parent: Mapping[str, str]) -> dict[str, str]:
    """Build the child environment from D005 and freeze Python's locale coercion."""
    required = {"set", "unset", "inherit_allowlist"}
    if not required.issubset(contract) or not isinstance(contract["set"], Mapping):
        raise ValueError("malformed D005 environment contract")
    allow = contract["inherit_allowlist"]
    unset = contract["unset"]
    if not isinstance(allow, list) or not isinstance(unset, list) or not all(isinstance(x, str) for x in allow + unset):
        raise ValueError("malformed D005 allowlist/unset list")
    if set(allow) & set(unset):
        raise ValueError("D005 environment allowlist conflicts with unset")
    result = {key: parent[key] for key in allow if key in parent}
    result.update({str(key): str(value) for key, value in contract["set"].items()})
    if set(result) & set(unset):
        raise ValueError("D005 set conflicts with unset")
    if set(PYTHON_CHILD_LOCALE) & set(unset):
        raise ValueError("D005 cannot unset the Python child locale")
    for key, value in PYTHON_CHILD_LOCALE.items():
        result.setdefault(key, value)
    return result


def _git_clean(root: Path) -> bool:
    return subprocess.run(["git", "-C", str(root), "diff", "--quiet", "HEAD", "--"], check=False).returncode == 0


def validate_root_isolation(*roots: Path) -> tuple[Path, ...]:
    """Reject equal, symlink-equivalent, and nested roots before any export work."""
    canonical = tuple(root.resolve() for root in roots)
    if len(set(canonical)) != len(canonical):
        raise ValueError("P5 production/evidence/exporter roots must be distinct canonical directories")
    for index, root in enumerate(canonical):
        if not root.is_dir():
            raise ValueError("P5 root is not a directory")
        for other in canonical[index + 1 :]:
            if root.is_relative_to(other) or other.is_relative_to(root):
                raise ValueError("P5 roots must not be ancestor/descendant overlapping directories")
    return canonical


def validate_production_root(recurrent: Mapping[str, Any], ttt: Mapping[str, Any], production_root: Path) -> Path:
    """Enforce the absolute P4 D005 worktree identity; revision equality is insufficient."""
    roots = {Path(record["command"]["cwd"]).resolve().parent for record in (recurrent, ttt)}
    if (len(roots) != 1 or production_root.resolve() != next(iter(roots))
            or production_root.resolve() != FROZEN_PRODUCTION_ROOT.resolve()):
        raise ValueError("production_root must exactly equal the common D005 worktree root")
    root = production_root.resolve()
    framework = root / "cosmos-framework"
    if not _git_clean(root) or not _git_clean(framework):
        raise ValueError("production_root and its cosmos-framework submodule must be tracked-clean")
    for record in (recurrent, ttt):
        env = record["environment"]["set"]
        stream_asset = record["inputs"]["external_assets"]["stream_manifest"]
        for value in (record["command"]["cwd"], env["PYTHONPATH"], env["PSM_R09_B2_STREAM_MANIFEST_ROOT"], stream_asset["path"], stream_asset["realpath"]):
            if not Path(value).resolve().is_relative_to(root):
                raise ValueError("D005 worktree path escapes the frozen production root")
        source = record["source"]
        root_revision = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
        gitlink = subprocess.check_output(["git", "-C", str(root), "ls-tree", "HEAD", "cosmos-framework"], text=True).split()[2]
        submodule_revision = subprocess.check_output(["git", "-C", str(root / "cosmos-framework"), "rev-parse", "HEAD"], text=True).strip()
        if source != {"root_revision": root_revision, "submodule_revision": submodule_revision, "gitlink_revision": gitlink}:
            raise ValueError("production_root Git source differs from frozen D005 source")
    return root


def build_child_request(record: Mapping[str, Any], *, production_root: Path, backend: str, p3_verifier_sha256: str, p4_record_sha256: str, p4_verification_sha256: str) -> dict[str, Any]:
    """Bind one child request to its verified D005; the child never accepts loose inputs."""
    if record.get("backend") != backend:
        raise ValueError("D005 backend does not match requested export")
    toml, overrides = parse_d005_command(record)
    command, environment = record["command"], record["environment"]
    cwd = Path(command["cwd"]).resolve()
    interpreter = Path(command["interpreter"]["path"])
    if cwd != (production_root / "cosmos-framework").resolve() or not interpreter.is_absolute() or interpreter.resolve() != Path(command["interpreter"]["realpath"]):
        raise ValueError("D005 cwd/interpreter is not canonical for this root")
    return {"backend": backend, "root": str(production_root.resolve()), "toml": toml, "overrides": overrides, "command_argv": command["argv"],
            "cwd": str(cwd), "interpreter": dict(command["interpreter"]),
            "environment": {"contract": environment, "effective": sanitized_environment(environment, os.environ)},
            "d005_sha256": record["d005_sha256"], "p4_record_sha256": p4_record_sha256, "p4_verification_sha256": p4_verification_sha256, "p3_verifier_sha256": p3_verifier_sha256, "source": record["source"], "budget": record["budget"], "inputs": record["inputs"], "outputs": record["outputs"]}


def validate_child_request(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    """Require one immutable parent/verifier-owned D005 request before any compose import."""
    backend = payload.get("backend")
    if set(payload) != CHILD_REQUEST_KEYS or backend not in FROZEN_CHILD_REQUEST_SHA256:
        raise ValueError("P5 child request schema/backend is not verifier-owned")
    if sha256_json(payload) != FROZEN_CHILD_REQUEST_SHA256[backend]:
        raise ValueError("P5 child request is not a frozen D005-bound identity")
    return payload


def build_loader_request(child_request: Mapping[str, Any], child_output: Path) -> dict[str, Any]:
    """Wrap one D005-bound compose request for the verified lexical loader."""
    payload = dict(validate_child_request(child_request))
    output = child_output.resolve()
    if not output.is_absolute() or output.exists() or not output.parent.is_dir():
        raise ValueError("P5 verified-loader output must be a fresh file in an existing directory")
    return {"schema_version": LOADER_REQUEST_SCHEMA, "child_request": payload,
            "child_request_sha256": sha256_json(payload), "child_output": str(output)}


def validate_loader_request(payload: Mapping[str, Any]) -> tuple[Mapping[str, Any], Path]:
    """Accept only one SHA-bound P5 request delivered by the verified loader."""
    if set(payload) != LOADER_REQUEST_KEYS or payload.get("schema_version") != LOADER_REQUEST_SCHEMA:
        raise ValueError("P5 verified-loader request schema is malformed")
    child_request = payload.get("child_request")
    child_sha256 = payload.get("child_request_sha256")
    output = payload.get("child_output")
    if (not isinstance(child_request, Mapping) or not isinstance(child_sha256, str)
            or sha256_json(child_request) != child_sha256 or not isinstance(output, str)):
        raise ValueError("P5 verified-loader request binding differs from its child request")
    output_path = Path(output)
    if not output_path.is_absolute() or output_path.resolve() != output_path or output_path.exists() or not output_path.parent.is_dir():
        raise ValueError("P5 verified-loader output is not a fresh canonical path")
    return validate_child_request(child_request), output_path


def build_pair_requests(recurrent: Mapping[str, Any], ttt: Mapping[str, Any], *, production_root: Path, evidence_root: Path) -> dict[str, dict[str, Any]]:
    """Reject the retired P4-v2 admission path before any future child can spawn.

    The v0.8 execution request adapter is deliberately not allowed to infer
    fields from the caller's historical D005 records.  It must be constructed
    only after `load_p4_v4_preflight()` has independently verified the future
    P4-v4 evidence; until that adapter is implemented this is a hard stop.
    """
    del recurrent, ttt, production_root
    load_p4_v4_preflight(evidence_root)
    raise RuntimeError("P5 v4 preflight request adapter is required; historical P4-v2 admission is retired")


def bound_exporter_source(exporter_root: Path) -> tuple[dict[str, Any], Any]:
    """Ensure the parent, child script, and verifier are exactly exporter_root-owned code."""
    root = exporter_root.resolve()
    exporter_path = (root / "tools/g0/export_r09_b2_p5_resolved_config.py").resolve()
    verifier_path = (root / "tools/g0/verify_r09_b2_p5_full_config_diff.py").resolve()
    if Path(__file__).resolve() != exporter_path:
        raise ValueError("executing P5 exporter is not owned by exporter_root")
    from tools.g0 import verify_r09_b2_p5_full_config_diff as verifier
    if Path(verifier.__file__).resolve() != verifier_path:
        raise ValueError("executing P5 verifier is not owned by exporter_root")
    source = verifier._exporter_source(root)
    if source["tool_sha256"] != {
        "tools/g0/export_r09_b2_p5_resolved_config.py": hashlib.sha256(exporter_path.read_bytes()).hexdigest(),
        "tools/g0/verify_r09_b2_p5_full_config_diff.py": hashlib.sha256(verifier_path.read_bytes()).hexdigest(),
    }:
        raise ValueError("executing P5 exporter/verifier SHA differs from exporter_root")
    return source, verifier.verify_pair


def assemble_envelope(request: Mapping[str, Any], resolved_config: Mapping[str, Any], *, exporter_source: Mapping[str, Any]) -> dict[str, Any]:
    """Construct the complete verifier-owned envelope from one D005-bound child result."""
    record = request
    command = record["interpreter"]
    return {"schema_version": SCHEMA, "backend": record["backend"],
            "provenance": {"production_source": record["source"], "exporter_source": exporter_source,
                           "inputs": {"p4_record_sha256": record["p4_record_sha256"], "p4_d005_sha256": record["d005_sha256"], "p4_verification_sha256": record["p4_verification_sha256"],
                                      "p3_inventory_path": record["inputs"]["p3_inventory"]["path"], "p3_inventory_sha256": record["inputs"]["p3_inventory"]["sha256"], "p3_verifier_sha256": record["p3_verifier_sha256"]}},
            "effective_launch": {"command": {"argv": record["command_argv"], "cwd": record["cwd"], "interpreter": command, "toml": record["toml"], "trailing_overrides": record["overrides"]},
                                  "environment": {**record["environment"]["contract"], "effective": record["environment"]["effective"]}, "world_size": record["budget"]["world_size"], "budget": record["budget"],
                                  "p1_p3_d005_bindings": {"p1_manifest": record["inputs"]["p1_manifest"], "p3_inventory": record["inputs"]["p3_inventory"]}, "derived_job_path_local": record["outputs"]["run_root"]},
            "resolved_config": resolved_config}


def run_parent_export(recurrent: Mapping[str, Any], ttt: Mapping[str, Any], *, production_root: Path, evidence_root: Path, exporter_root: Path, output_dir: Path) -> dict[str, Any]:
    """Future approved path: two D005-bound fresh children, envelope assembly, then verifier."""
    production_root, evidence_root, exporter_root = validate_root_isolation(production_root, evidence_root, exporter_root)
    requests = build_pair_requests(recurrent, ttt, production_root=production_root, evidence_root=evidence_root)
    if output_dir.exists():
        raise FileExistsError(f"canonical P5 output already exists: {output_dir}")
    attempt_dir = output_dir.parent / f".{output_dir.name}.attempt-{uuid.uuid4().hex}"
    attempt_dir.mkdir(parents=True, exist_ok=False)
    try:
        exporter_source, verify_pair = bound_exporter_source(exporter_root)
        envelopes: dict[str, Any] = {}
        for backend, request in requests.items():
            request_path, tree_path = attempt_dir / f"{backend}.request.json", attempt_dir / f"{backend}.tree.json"
            loader_request = build_loader_request(request, tree_path)
            request_path.write_bytes(canonical_bytes(loader_request))
            try:
                argv = verified_loader_argv(
                    request["interpreter"], request_path, sha256_file(request_path), exporter_root,
                    BOOTSTRAP_RELATIVE, sha256_file(exporter_root / BOOTSTRAP_RELATIVE),
                )
            except (OSError, ProvenanceError) as exc:
                raise RuntimeError("P5 child must use the verified lexical loader") from exc
            if not is_verified_loader_argv(argv):
                raise RuntimeError("P5 child launcher differs from the verified lexical-loader grammar")
            subprocess.run(argv, cwd=request["cwd"], env=request["environment"]["effective"], check=True)
            envelopes[backend] = assemble_envelope(request, json.loads(tree_path.read_text()), exporter_source=exporter_source)
        result = verify_pair(envelopes["recurrent"], envelopes["ttt_fast_weight"], evidence_root, exporter_root)
        if result["status"] != "PASS":
            raise RuntimeError("P5 parent refuses to write an envelope pair that fails its verifier")
        for backend, envelope in envelopes.items():
            (attempt_dir / f"{backend}_resolved.json").write_bytes(canonical_bytes(envelope))
        (attempt_dir / "verification.json").write_bytes(canonical_bytes(result))
        attempt_dir.rename(output_dir)
        return result
    except Exception as exc:
        (attempt_dir / "failure.json").write_bytes(canonical_bytes({"schema_version": SCHEMA, "status": "FAIL", "stage": "parent_export", "error_type": type(exc).__name__, "error": str(exc)}))
        raise


def _child_payload(payload: Mapping[str, Any], output: Path) -> None:
    """Approved later only: compose one backend without launch/validate/instantiate."""
    payload = validate_child_request(payload)
    if Path.cwd().resolve() != Path(payload["cwd"]).resolve() or Path(os.path.abspath(sys.executable)) != Path(payload["interpreter"]["path"]):
        raise RuntimeError("P5 child cwd/interpreter differs from D005-bound request")
    if dict(os.environ) != payload["environment"]["effective"]:
        raise RuntimeError("P5 child environment differs from D005-bound request")
    if any(name.startswith("cosmos_framework.configs.base.experiment") for name in sys.modules):
        raise RuntimeError("experiment was imported before P5 child compose")
    try:
        from hydra.core.global_hydra import GlobalHydra
        if GlobalHydra.instance().is_initialized():
            raise RuntimeError("Hydra was initialized before P5 child compose")
    except ModuleNotFoundError:
        pass
    from cosmos_framework.configs.toml_config.sft_config import load_experiment_from_toml
    config = load_experiment_from_toml(payload["toml"], extra_overrides=payload["overrides"])
    if config.model.config.local_history_backend != ("ttt_fast_weight" if payload["backend"] == "ttt_fast_weight" else "recurrent"):
        raise RuntimeError("P5 composed backend differs from its D005-bound request")
    import torch
    if torch.cuda.is_initialized():
        raise RuntimeError("P5 static compose initialized CUDA")
    output.write_bytes(canonical_bytes(canonicalize(config.to_dict())))


def _verified_bootstrap(payload: Mapping[str, Any]) -> None:
    """The frozen loader is the only admitted P5 child entrypoint."""
    child_request, output = validate_loader_request(payload)
    _child_payload(child_request, output)


def main() -> None:
    raise SystemExit("direct P5 exporter-script execution is permanently rejected; use the verified lexical loader")


if __name__ == "__psm_verified_bootstrap__":
    _verified_bootstrap(PSM_REQUEST)
elif __name__ == "__main__":
    main()
