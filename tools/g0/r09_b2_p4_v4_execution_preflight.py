"""P4-v4 execution-preflight entry foundation; no execution is authorized here."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
from pathlib import Path

from tools.g0.r09_b2_interpreter_provenance import (
    ProvenanceError,
    is_verified_loader_argv,
    lexical_interpreter,
    parse_elf_dynamic_raw,
    verified_loader_argv,
)
from tools.g0.export_r09_b2_p5_resolved_config import (
    P5_FORBIDDEN_ENVIRONMENT,
    P5_P3_BACKEND_ENVIRONMENT,
)
from tools.g0.verify_r09_b2_p4_d005 import (
    RANK_ENV,
    REQUIRED_ENV,
    SANITIZED_ENV,
    verify_pair as verify_d005_pair,
)


REQUEST_KEYS = {
    "schema_version", "entry", "source", "interpreter", "environment", "run", "candidates",
    "backends", "authorities", "execution_contract",
}
ENTRY_KEYS = {"tool_path", "root_revision", "git_blob_sha256", "current_sha256", "identity_sha256"}
ENTRY_TOOL_PATH = "tools/g0/r09_b2_p4_v4_execution_preflight.py"
SOURCE_KEYS = {"root", "root_revision", "gitlink", "entry_git_blob_sha256", "entry_current_sha256", "identity_sha256"}
INTERPRETER_KEYS = {"lexical_interpreter", "host_git", "loader_argv", "identity_sha256"}
HOST_GIT_KEYS = {"path", "elf_sha256", "closure_sha256"}
ENVIRONMENT_KEYS = {"effective_environment", "native_loader_environment", "d005_projection", "identity_sha256"}
ENVIRONMENT_OBJECT_KEYS = {"set", "unset", "inherit_allowlist", "sha256"}
D005_PROJECTION_KEYS = {"backend", "d005_sha256", "input_set_sha256", "excluded_keys", "projected_set_sha256", "sha256"}
D005_EXCLUDED_ENVIRONMENT_KEYS = ["IMAGINAIRE_OUTPUT_ROOT", "PYTHONPATH"]
AUTHORITIES_KEYS = {"d005_pair", "identity_sha256"}
AUTHORITIES_PAIR_KEYS = {"model", "recurrent", "ttt_fast_weight", "verification", "historical_source", "historical_verifier", "identity_sha256"}
RUN_KEYS = {"recurrent", "ttt_fast_weight"}
RUN_ITEM_KEYS = {"identity", "run_token", "roster_sha256"}
RUN_IDENTITY_KEYS = {"root", "resolved_root", "kind", "identity_sha256"}
CANDIDATES_KEYS = {"root", "attempt_id", "recurrent", "ttt_fast_weight", "identity_sha256"}
CANDIDATE_ROOT_KEYS = RUN_IDENTITY_KEYS
CANDIDATE_ITEM_KEYS = {"backend", "candidate_root", "run", "identity_sha256"}
_HISTORICAL_REVISION = "ddb4e0eae97fb545d5239c1ddb6d4387170f3780"
_HISTORICAL_GITLINK = "21d064f2b7c7aeeb67cfee50ac8d6722a944eddb"
_HISTORICAL_ARTIFACTS = {
    "recurrent": ("artifacts/g0/r09/b2/p4_launch_d005/recurrent.json", "2d04c5040c5836249bcab78e7904c2cf8a475c4fcf5925942ebb496985cd3190"),
    "ttt_fast_weight": ("artifacts/g0/r09/b2/p4_launch_d005/ttt_fast_weight.json", "8890bbec61a808d5964657806cf01166c893ff66abc2fdf64ea3cd201a03274e"),
    "verification": ("artifacts/g0/r09/b2/p4_launch_d005/verification.json", "8618488f9c8cbbcdda2ea9d513f1f76a0154798fe386ce19dcbeac78fcff4080"),
}
_HISTORICAL_VERIFIER = ("tools/g0/verify_r09_b2_p4_d005.py", "2c94f28a7779f7e74a2798124a0d85e57bafa8aab739b6072ef6790a91c9a4e6")
_VERIFICATION_BACKEND_KEYS = {"argv", "budget", "command_digest", "cwd", "env_assets_bound", "environment", "inputs", "non_executable", "outputs", "record_digest", "schema", "source"}
_GIT_REVISION = re.compile(r"[0-9a-f]{40}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_EXECUTION_CONTRACT_ITEMS = (
    ("network", False),
    ("gpu", False),
    ("torch", False),
    ("model_data_checkpoint_io", False),
    ("one_shot", True),
    ("cleanup_retry_repair", False),
)


def _read_regular_nofollow(path: Path, error: str) -> bytes:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise ValueError(error)
    flags = os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ValueError(error) from exc
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError(error)
        with os.fdopen(descriptor, "rb") as request_file:
            descriptor = -1
            return request_file.read()
    finally:
        if descriptor != -1:
            os.close(descriptor)


def _read_strict_regular_nofollow(path: Path, error: str, *, executable: bool = True) -> tuple[Path, bytes]:
    if not path.is_absolute() or path.is_symlink() or path.resolve(strict=True) != path:
        raise ValueError(error)
    raw = _read_regular_nofollow(path, error)
    if executable and not os.access(path, os.X_OK):
        raise ValueError(error)
    return path, raw


def _read_canonical_regular_nofollow(path: Path, error: str) -> tuple[Path, bytes]:
    try:
        canonical = path.resolve(strict=True)
    except OSError as exc:
        raise ValueError(error) from exc
    if canonical.is_symlink() or not canonical.is_absolute():
        raise ValueError(error)
    return canonical, _read_regular_nofollow(canonical, error)


def read_execution_request(path: Path) -> bytes:
    return _read_regular_nofollow(path, "execution request must be a regular file")


def load_execution_request(
    raw: bytes,
    _execution_contract_items: tuple[tuple[str, bool], ...] = _EXECUTION_CONTRACT_ITEMS,
) -> dict[str, object]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("execution request is not JSON") from exc
    canonical = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if not isinstance(value, dict) or raw != canonical:
        raise ValueError("execution request is not canonical JSON")
    if set(value) != REQUEST_KEYS or value.get("schema_version") != "r09_b2_p4_v4_execution_request_v1":
        raise ValueError("execution request schema differs")
    if not all(isinstance(value[key], dict) for key in REQUEST_KEYS - {"schema_version"}):
        raise ValueError("execution request section differs")
    if value["execution_contract"] != dict(_execution_contract_items):
        raise ValueError("execution request contract differs")
    validate_entry(value["entry"])
    interpreter = value["interpreter"]
    if not isinstance(interpreter, dict):
        raise ValueError("execution request interpreter schema differs")
    git_path = validate_host_git(interpreter.get("host_git"))
    validate_source(value["source"], value["entry"], git_path)
    validate_interpreter(interpreter, value["source"], git_path)
    validate_run_pair(value["run"], value["source"])
    validate_candidates(value["candidates"], value["source"], value["run"])
    return value


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    ).hexdigest()


def _identity(value: dict[str, object], name: str) -> None:
    if not isinstance(value.get("identity_sha256"), str) or value["identity_sha256"] != canonical_sha256({key: item for key, item in value.items() if key != "identity_sha256"}):
        raise ValueError(f"execution request {name} identity differs")


def _historical_source() -> dict[str, str]:
    value = {"root_revision": _HISTORICAL_REVISION, "gitlink_revision": _HISTORICAL_GITLINK, "submodule_revision": _HISTORICAL_GITLINK}
    return {**value, "identity_sha256": canonical_sha256(value)}


def _historical_verifier() -> dict[str, str]:
    value = {"relative_path": _HISTORICAL_VERIFIER[0], "root_revision": _HISTORICAL_REVISION, "git_blob_sha256": _HISTORICAL_VERIFIER[1]}
    return {**value, "identity_sha256": canonical_sha256(value)}


def _historical_binding(name: str) -> dict[str, str]:
    path, digest = _HISTORICAL_ARTIFACTS[name]
    return {"relative_path": path, "sha256": digest}


def _read_historical_artifact(root: Path, binding: object, expected: dict[str, str], name: str) -> tuple[bytes, dict[str, object]]:
    if binding != expected:
        raise ValueError(f"execution request historical {name} binding differs")
    relative = Path(expected["relative_path"])
    if relative.is_absolute() or not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
        raise ValueError(f"execution request historical {name} path differs")
    lexical = root / relative
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise ValueError(f"execution request historical {name} path differs")
    flags = os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(lexical, flags)
    except OSError as exc:
        raise ValueError(f"execution request historical {name} path differs") from exc
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError(f"execution request historical {name} path differs")
        try:
            canonical = Path(f"/proc/self/fd/{descriptor}").resolve(strict=True)
        except OSError as exc:
            raise ValueError(f"execution request historical {name} path differs") from exc
        if not canonical.is_relative_to(root):
            raise ValueError(f"execution request historical {name} path differs")
        with os.fdopen(descriptor, "rb") as handle:
            descriptor = -1
            raw = handle.read()
    finally:
        if descriptor != -1:
            os.close(descriptor)
    if hashlib.sha256(raw).hexdigest() != expected["sha256"]:
        raise ValueError(f"execution request historical {name} bytes differ")
    try:
        return raw, json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"execution request historical {name} JSON differs") from exc


def _validate_historical_verification(value: object) -> None:
    if not isinstance(value, dict) or set(value) != {"checks", "schema_version", "status"} or value["schema_version"] != "r09_b2_p4_d005_verifier_v2" or value["status"] != "PASS":
        raise ValueError("execution request historical verification schema differs")
    checks = value["checks"]
    if not isinstance(checks, dict) or set(checks) != {"distinct_outputs", "matched", "recurrent", "ttt_fast_weight"} or checks["distinct_outputs"] is not True:
        raise ValueError("execution request historical verification checks differ")
    matched = checks["matched"]
    if not isinstance(matched, dict) or set(matched) != {"budget", "external_assets", "p1_manifest", "p3_sha256", "source"} or any(item is not True for item in matched.values()):
        raise ValueError("execution request historical verification matched differs")
    for backend in ("recurrent", "ttt_fast_weight"):
        item = checks[backend]
        if not isinstance(item, dict) or set(item) != _VERIFICATION_BACKEND_KEYS or any(flag is not True for flag in item.values()):
            raise ValueError("execution request historical verification backend differs")


def validate_authorities_pair(authorities: object, request: dict[str, object], root: Path, git_executable: Path) -> None:
    """Validate the fixed historical D005 authority without invoking its verifier."""
    if not isinstance(authorities, dict) or set(authorities) != AUTHORITIES_KEYS:
        raise ValueError("execution request authorities schema differs")
    _identity(authorities, "authorities")
    pair = authorities["d005_pair"]
    if not isinstance(pair, dict) or set(pair) != AUTHORITIES_PAIR_KEYS or pair.get("model") != "historical_d005_v2":
        raise ValueError("execution request authorities pair schema differs")
    _identity(pair, "authorities pair")
    if pair.get("historical_source") != _historical_source() or pair.get("historical_verifier") != _historical_verifier():
        raise ValueError("execution request historical source differs")
    if not git_executable.is_absolute() or Path(request.get("interpreter", {}).get("host_git", {}).get("path", "")) != git_executable:
        raise ValueError("execution request historical host Git differs")
    records: dict[str, dict[str, object]] = {}
    paths: set[str] = set()
    for backend in ("recurrent", "ttt_fast_weight"):
        binding = _historical_binding(backend)
        raw, record = _read_historical_artifact(root, pair.get(backend), binding, backend)
        source = {"root_revision": _HISTORICAL_REVISION, "gitlink_revision": _HISTORICAL_GITLINK, "submodule_revision": _HISTORICAL_GITLINK}
        digest = {key: item for key, item in record.items() if key != "d005_sha256"}
        if raw != (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode() or record.get("backend") != backend or record.get("schema_version") != "r09_b2_p4_launch_d005_v2" or record.get("status") != "FROZEN_NOT_EXECUTED" or record.get("source") != source or record.get("d005_sha256") != canonical_sha256(digest):
            raise ValueError("execution request historical record differs")
        paths.add(binding["relative_path"]); records[backend] = record
    if len(paths) != 2:
        raise ValueError("execution request historical artifact path differs")
    _, verification = _read_historical_artifact(root, pair.get("verification"), _historical_binding("verification"), "verification")
    _validate_historical_verification(verification)
    blob = _git(root, "show", f"{_HISTORICAL_REVISION}:{_HISTORICAL_VERIFIER[0]}", git_executable=git_executable)
    if hashlib.sha256(blob).hexdigest() != _HISTORICAL_VERIFIER[1]:
        raise ValueError("execution request historical verifier bytes differ")
    _validate_environment_sections(request.get("environment"), records)


def validate_entry(value: object) -> None:
    if not isinstance(value, dict) or set(value) != ENTRY_KEYS or not all(
        isinstance(item, str) for item in value.values()
    ):
        raise ValueError("execution request entry schema differs")
    if value["tool_path"] != ENTRY_TOOL_PATH:
        raise ValueError("execution request entry path differs")
    if _GIT_REVISION.fullmatch(value["root_revision"]) is None or any(
        _SHA256.fullmatch(value[key]) is None
        for key in ("git_blob_sha256", "current_sha256", "identity_sha256")
    ):
        raise ValueError("execution request entry digest differs")
    identity = {key: item for key, item in value.items() if key != "identity_sha256"}
    if value["identity_sha256"] != canonical_sha256(identity):
        raise ValueError("execution request entry identity differs")


def _git(root: Path, *args: str, git_executable: Path | None = None) -> bytes:
    try:
        return subprocess.run((str(git_executable) if git_executable is not None else "git", "-C", str(root), *args), check=True, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError("execution request source Git command differs") from exc


def _clean_git_root(root: Path, git_executable: Path) -> None:
    if root.is_symlink() or not root.is_dir() or _git(root, "rev-parse", "--show-toplevel", git_executable=git_executable).decode().strip() != str(root):
        raise ValueError("execution request source Git root differs")
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all", git_executable=git_executable):
        raise ValueError("execution request source is not full-clean")


def validate_source(value: object, entry: dict[str, object], git_executable: Path) -> None:
    if not isinstance(value, dict) or set(value) != SOURCE_KEYS or not all(isinstance(item, str) for item in value.values()):
        raise ValueError("execution request source schema differs")
    if (_GIT_REVISION.fullmatch(value["root_revision"]) is None or _GIT_REVISION.fullmatch(value["gitlink"]) is None
            or any(_SHA256.fullmatch(value[key]) is None for key in ("entry_git_blob_sha256", "entry_current_sha256", "identity_sha256"))):
        raise ValueError("execution request source digest differs")
    root = Path(value["root"])
    if not root.is_absolute() or root.is_symlink() or root.resolve(strict=True) != root:
        raise ValueError("execution request source root differs")
    identity = {key: item for key, item in value.items() if key != "identity_sha256"}
    if value["identity_sha256"] != canonical_sha256(identity):
        raise ValueError("execution request source identity differs")
    if any(value[key] != entry[entry_key] for key, entry_key in (("root_revision", "root_revision"), ("entry_git_blob_sha256", "git_blob_sha256"), ("entry_current_sha256", "current_sha256"))):
        raise ValueError("execution request source cross-binding differs")
    _clean_git_root(root, git_executable)
    framework = root / "cosmos-framework"
    _clean_git_root(framework, git_executable)
    if framework.is_symlink() or _git(root, "rev-parse", "HEAD", git_executable=git_executable).decode().strip() != value["root_revision"] or _git(root, "rev-parse", "--verify", f"{value['root_revision']}^{{commit}}", git_executable=git_executable).decode().strip() != value["root_revision"]:
        raise ValueError("execution request source checkout revision differs")
    tree = _git(root, "ls-tree", value["root_revision"], "cosmos-framework", git_executable=git_executable).decode().rstrip("\n").split("\t")
    if len(tree) != 2 or tree[1] != "cosmos-framework" or tree[0].split()[:2] != ["160000", "commit"] or tree[0].split()[2] != value["gitlink"] or _git(framework, "rev-parse", "HEAD", git_executable=git_executable).decode().strip() != value["gitlink"]:
        raise ValueError("execution request source Gitlink differs")
    entry_path = root / ENTRY_TOOL_PATH
    _git(root, "ls-files", "--error-unmatch", "--", ENTRY_TOOL_PATH, git_executable=git_executable)
    blob = _git(root, "show", f"{value['root_revision']}:{ENTRY_TOOL_PATH}", git_executable=git_executable)
    current_raw = _read_regular_nofollow(entry_path, "execution request source entry path differs")
    if hashlib.sha256(blob).hexdigest() != value["entry_git_blob_sha256"] or hashlib.sha256(current_raw).hexdigest() != value["entry_current_sha256"] or blob != current_raw or value["entry_git_blob_sha256"] != value["entry_current_sha256"]:
        raise ValueError("execution request source entry bytes differ")


def _library_search_paths(owner: Path, metadata: dict[str, object]) -> list[Path]:
    expanded: list[Path] = []
    for item in [*metadata["rpath"], *metadata["runpath"]]:
        if not isinstance(item, str):
            raise ValueError("execution request host Git ELF search path differs")
        for token in item.split(":"):
            candidate = token.replace("${ORIGIN}", str(owner.parent)).replace("$ORIGIN", str(owner.parent))
            if "$" in candidate or not candidate:
                raise ValueError("execution request host Git ELF search path differs")
            expanded.append(Path(candidate))
    defaults = (Path("/lib"), Path("/usr/lib"), Path("/lib64"), Path("/usr/lib64"))
    for prefix in defaults:
        if prefix.is_dir():
            expanded.append(prefix)
            expanded.extend(sorted(item for item in prefix.glob("*-linux-gnu") if item.is_dir()))
    return expanded


def _resolve_needed(owner: Path, metadata: dict[str, object], name: str) -> Path:
    if "/" in name:
        candidate = Path(name)
        if not candidate.is_absolute():
            raise ValueError("execution request host Git ELF dependency differs")
        return candidate
    candidates = [directory / name for directory in _library_search_paths(owner, metadata)]
    found = {str(candidate.resolve()): candidate for candidate in candidates if candidate.exists()}
    if len(found) != 1:
        raise ValueError("execution request host Git ELF dependency differs")
    return next(iter(found.values()))


def _host_git_closure(path: Path, raw: bytes) -> str:
    pending: list[tuple[Path, bytes | None]] = [(path, raw)]
    scheduled = {str(path)}
    objects: dict[str, str] = {}
    while pending:
        current, current_raw = pending.pop()
        if current == path:
            canonical = path
        else:
            canonical, current_raw = _read_canonical_regular_nofollow(
                current, "execution request host Git object differs",
            )
        if str(canonical) in objects:
            if objects[str(canonical)] != hashlib.sha256(current_raw).hexdigest():
                raise ValueError("execution request host Git object differs")
            continue
        try:
            metadata = parse_elf_dynamic_raw(canonical, current_raw)
        except ProvenanceError as exc:
            raise ValueError("execution request host Git ELF differs") from exc
        objects[str(canonical)] = str(metadata["sha256"])
        dependencies = list(metadata["dt_needed"])
        interpreter = metadata["pt_interp"]
        if interpreter is not None:
            dependencies.append(interpreter)
        for dependency in dependencies:
            if not isinstance(dependency, str):
                raise ValueError("execution request host Git ELF dependency differs")
            dependency_path = _resolve_needed(canonical, metadata, dependency)
            try:
                dependency_path = dependency_path.resolve(strict=True)
            except OSError as exc:
                raise ValueError("execution request host Git ELF dependency differs") from exc
            if str(dependency_path) not in scheduled:
                scheduled.add(str(dependency_path))
                pending.append((dependency_path, None))
    return canonical_sha256({"objects": [{"path": name, "sha256": digest} for name, digest in sorted(objects.items())]})


def _environment_object(value: object, *, native: bool) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != ENVIRONMENT_OBJECT_KEYS:
        raise ValueError("execution request environment object schema differs")
    items = {key: item for key, item in value.items() if key != "sha256"}
    if value["sha256"] != canonical_sha256(items) or value["inherit_allowlist"] != [] or value["unset"] != list(P5_FORBIDDEN_ENVIRONMENT):
        raise ValueError("execution request environment object identity differs")
    values = value["set"]
    if not isinstance(values, dict) or not all(isinstance(key, str) and isinstance(item, str) for key, item in values.items()):
        raise ValueError("execution request environment set differs")
    if set(values) & set(P5_FORBIDDEN_ENVIRONMENT):
        raise ValueError("execution request environment forbidden key differs")
    if native and values != {}:
        raise ValueError("execution request native loader environment differs")
    return value


def _project_d005_environment(record: dict[str, object], backend: str) -> tuple[dict[str, str], dict[str, object]]:
    environment = record.get("environment")
    if record.get("backend") != backend or not isinstance(environment, dict) or not isinstance(environment.get("set"), dict):
        raise ValueError("execution request D005 environment differs")
    values = environment["set"]
    expected = set(REQUIRED_ENV) | set(P5_P3_BACKEND_ENVIRONMENT)
    if (set(values) != expected or not all(isinstance(key, str) and isinstance(item, str) for key, item in values.items())
            or set(values) & (RANK_ENV | SANITIZED_ENV)):
        raise ValueError("execution request D005 environment differs")
    projected = {key: item for key, item in values.items() if key not in D005_EXCLUDED_ENVIRONMENT_KEYS}
    if set(values) - set(projected) != set(D005_EXCLUDED_ENVIRONMENT_KEYS):
        raise ValueError("execution request D005 projection differs")
    expected_backend = P5_P3_BACKEND_ENVIRONMENT["PSM_R09_B1_TTT_ENABLED"][backend]
    if values.get("PSM_R09_B1_TTT_ENABLED") != expected_backend:
        raise ValueError("execution request D005 backend differs")
    projection = {"backend": backend, "d005_sha256": record.get("d005_sha256"),
                  "input_set_sha256": canonical_sha256(values), "excluded_keys": D005_EXCLUDED_ENVIRONMENT_KEYS,
                  "projected_set_sha256": canonical_sha256(projected)}
    if not isinstance(projection["d005_sha256"], str):
        raise ValueError("execution request D005 digest differs")
    projection["sha256"] = canonical_sha256(projection)
    return projected, projection


def _validate_environment_sections(value: object, records: dict[str, dict[str, object]]) -> None:
    if not isinstance(value, dict) or set(value) != {"recurrent", "ttt_fast_weight"}:
        raise ValueError("execution request environment pair schema differs")
    sections: dict[str, dict[str, object]] = {}
    for backend, record in records.items():
        section = value[backend]
        if not isinstance(section, dict) or set(section) != ENVIRONMENT_KEYS:
            raise ValueError("execution request environment schema differs")
        identity = {key: item for key, item in section.items() if key != "identity_sha256"}
        if section["identity_sha256"] != canonical_sha256(identity):
            raise ValueError("execution request environment identity differs")
        effective = _environment_object(section["effective_environment"], native=False)
        native = _environment_object(section["native_loader_environment"], native=True)
        projected, projection = _project_d005_environment(record, backend)
        projection_value = section["d005_projection"]
        if (not isinstance(projection_value, dict) or set(projection_value) != D005_PROJECTION_KEYS
                or any(not isinstance(projection_value[key], str) for key in (
                    "backend", "d005_sha256", "input_set_sha256", "projected_set_sha256", "sha256"
                ))
                or any(_SHA256.fullmatch(projection_value[key]) is None for key in (
                    "d005_sha256", "input_set_sha256", "projected_set_sha256", "sha256"
                ))
                or effective["set"] != projected or projection_value != projection):
            raise ValueError("execution request D005 projection differs")
        sections[backend] = {"effective": effective, "native": native}
    if sections["recurrent"]["native"] != sections["ttt_fast_weight"]["native"]:
        raise ValueError("execution request native loader pair differs")
    left, right = sections["recurrent"]["effective"]["set"], sections["ttt_fast_weight"]["effective"]["set"]
    different = {key for key in set(left) | set(right) if left.get(key) != right.get(key)}
    if different != set(P5_P3_BACKEND_ENVIRONMENT) or any(
        left.get(key) != values["recurrent"] or right.get(key) != values["ttt_fast_weight"]
        for key, values in P5_P3_BACKEND_ENVIRONMENT.items()
    ):
        raise ValueError("execution request environment backend difference differs")


def validate_environment_pair(value: object, recurrent: dict[str, object], ttt: dict[str, object], root: Path) -> None:
    """Validate the D005-bound, empty-parent environment pair without launching anything."""
    if verify_d005_pair(recurrent, ttt, root).get("status") != "PASS":
        raise ValueError("execution request D005 pair is not verified")
    _validate_environment_sections(value, {"recurrent": recurrent, "ttt_fast_weight": ttt})


def _future_lexical_path(value: object, name: str) -> Path:
    if not isinstance(value, str) or not value or not os.path.isabs(value) or value.startswith("//"):
        raise ValueError(f"execution request {name} path differs")
    path = Path(value)
    if os.path.normpath(value) != value or any(part in {".", ".."} for part in path.parts):
        raise ValueError(f"execution request {name} path differs")
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        try:
            mode = os.lstat(current).st_mode
        except FileNotFoundError:
            break
        except OSError as exc:
            raise ValueError(f"execution request {name} path differs") from exc
        if stat.S_ISLNK(mode):
            raise ValueError(f"execution request {name} path differs")
    return path


def _lexically_overlaps(left: Path, right: Path) -> bool:
    return left == right or left in right.parents or right in left.parents


def _validate_run_item(value: object, source_root: Path, backend: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != RUN_ITEM_KEYS:
        raise ValueError("execution request run item schema differs")
    identity = value.get("identity")
    if not isinstance(identity, dict) or set(identity) != RUN_IDENTITY_KEYS:
        raise ValueError("execution request run identity schema differs")
    if identity.get("kind") != "run_root" or not isinstance(identity.get("identity_sha256"), str):
        raise ValueError("execution request run identity differs")
    root = _future_lexical_path(identity.get("root"), f"run {backend}")
    resolved_root = _future_lexical_path(identity.get("resolved_root"), f"run {backend}")
    if root != resolved_root or identity["identity_sha256"] != canonical_sha256(
        {key: item for key, item in identity.items() if key != "identity_sha256"}
    ):
        raise ValueError("execution request run identity differs")
    if any(_SHA256.fullmatch(value.get(key, "")) is None for key in ("run_token", "roster_sha256")):
        raise ValueError("execution request run digest differs")
    if _lexically_overlaps(root, source_root) or _lexically_overlaps(root, source_root / "cosmos-framework"):
        raise ValueError("execution request run source overlap differs")
    return value


def validate_run_pair(value: object, source: object) -> None:
    """Validate only the non-executable future run-root pair contract."""
    if not isinstance(value, dict) or set(value) != RUN_KEYS or not isinstance(source, dict):
        raise ValueError("execution request run pair schema differs")
    source_root = _future_lexical_path(source.get("root"), "source")
    recurrent = _validate_run_item(value["recurrent"], source_root, "recurrent")
    ttt = _validate_run_item(value["ttt_fast_weight"], source_root, "ttt_fast_weight")
    if any(recurrent[key] == ttt[key] for key in RUN_ITEM_KEYS):
        raise ValueError("execution request run pair reuse differs")


def validate_candidates(value: object, source: object, run: object) -> None:
    """Validate the static, non-materializing candidate namespace binding."""
    if not isinstance(value, dict) or set(value) != CANDIDATES_KEYS or not isinstance(source, dict) or not isinstance(run, dict):
        raise ValueError("execution request candidates schema differs")
    _identity(value, "candidates")
    if (not isinstance(value.get("attempt_id"), str)
            or _SHA256.fullmatch(value["attempt_id"]) is None or set(run) != RUN_KEYS
            or any(not isinstance(run[backend], dict) for backend in RUN_KEYS)):
        raise ValueError("execution request candidates attempt differs")
    root_identity = value["root"]
    if not isinstance(root_identity, dict) or set(root_identity) != CANDIDATE_ROOT_KEYS or root_identity.get("kind") != "candidate_root":
        raise ValueError("execution request candidates root schema differs")
    _identity(root_identity, "candidates root")
    root = _future_lexical_path(root_identity.get("root"), "candidates root")
    if root != _future_lexical_path(root_identity.get("resolved_root"), "candidates root"):
        raise ValueError("execution request candidates root differs")
    source_root = _future_lexical_path(source.get("root"), "source")
    if _lexically_overlaps(root, source_root) or _lexically_overlaps(root, source_root / "cosmos-framework"):
        raise ValueError("execution request candidates source overlap differs")
    seen: set[str] = set()
    for backend in ("recurrent", "ttt_fast_weight"):
        item = value[backend]
        run_item = run[backend]
        if (not isinstance(item, dict) or set(item) != CANDIDATE_ITEM_KEYS or item.get("backend") != backend
                or item.get("run") != run_item):
            raise ValueError("execution request candidates backend differs")
        _identity(item, "candidates backend")
        candidate_root = _future_lexical_path(item.get("candidate_root"), f"candidates {backend}")
        if candidate_root != root / value["attempt_id"] / backend:
            raise ValueError("execution request candidates path differs")
        for other in ("recurrent", "ttt_fast_weight"):
            run_root = _future_lexical_path(run[other].get("identity", {}).get("root"), f"run {other}")
            if _lexically_overlaps(root, run_root) or _lexically_overlaps(candidate_root, run_root):
                raise ValueError("execution request candidates run overlap differs")
        run_identity = canonical_sha256(item["run"])
        if (value["attempt_id"] == run_item.get("run_token")
                or item["candidate_root"] in seen
                or item["identity_sha256"] in seen
                or run_identity in seen):
            raise ValueError("execution request candidates reuse differs")
        seen.update((item["candidate_root"], item["identity_sha256"], run_identity))


def validate_host_git(value: object) -> Path:
    if not isinstance(value, dict) or set(value) != HOST_GIT_KEYS or not all(isinstance(value[key], str) for key in HOST_GIT_KEYS):
        raise ValueError("execution request host Git schema differs")
    git_path, git_raw = _read_strict_regular_nofollow(Path(value["path"]), "execution request host Git path differs")
    if (_SHA256.fullmatch(value["elf_sha256"]) is None or _SHA256.fullmatch(value["closure_sha256"]) is None
            or hashlib.sha256(git_raw).hexdigest() != value["elf_sha256"]
            or _host_git_closure(git_path, git_raw) != value["closure_sha256"]):
        raise ValueError("execution request host Git identity differs")
    return git_path


def validate_interpreter(value: object, source: dict[str, object], git_path: Path | None = None) -> None:
    if not isinstance(value, dict) or set(value) != INTERPRETER_KEYS:
        raise ValueError("execution request interpreter schema differs")
    lexical, host_git, argv, identity_sha256 = (value["lexical_interpreter"], value["host_git"], value["loader_argv"], value["identity_sha256"])
    if not isinstance(lexical, dict) or not isinstance(host_git, dict) or not isinstance(argv, list) or not isinstance(identity_sha256, str):
        raise ValueError("execution request interpreter schema differs")
    identity = {key: item for key, item in value.items() if key != "identity_sha256"}
    if _SHA256.fullmatch(identity_sha256) is None or identity_sha256 != canonical_sha256(identity):
        raise ValueError("execution request interpreter identity differs")
    try:
        if lexical_interpreter(Path(lexical.get("path", ""))) != lexical:
            raise ValueError("execution request lexical interpreter differs")
    except (OSError, ProvenanceError, ValueError) as exc:
        raise ValueError("execution request lexical interpreter differs") from exc
    if git_path is None:
        git_path = validate_host_git(host_git)
    elif git_path != Path(host_git["path"]):
        raise ValueError("execution request host Git identity differs")
    root = Path(source["root"])
    if not is_verified_loader_argv(argv) or Path(argv[8]) != root:
        raise ValueError("execution request loader argv differs")
    try:
        expected = verified_loader_argv(lexical, Path(argv[6]), argv[7], root, argv[9], argv[10], git_executable=git_path)
    except (OSError, ProvenanceError, ValueError) as exc:
        raise ValueError("execution request loader argv differs") from exc
    if argv != expected:
        raise ValueError("execution request loader argv differs")


def request_sha256(raw: bytes) -> str:
    if not isinstance(raw, bytes):
        raise ValueError("execution request must be a regular file")
    return hashlib.sha256(raw).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--request-sha256", required=True)
    args = parser.parse_args(argv)
    raw = read_execution_request(args.request)
    if request_sha256(raw) != args.request_sha256:
        raise ValueError("execution request SHA256 differs")
    load_execution_request(raw)
    raise RuntimeError("P4-v4 execution requires a separately reviewed frozen execution request")


if __name__ == "__main__":
    main()
