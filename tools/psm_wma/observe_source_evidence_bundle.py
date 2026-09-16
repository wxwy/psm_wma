"""Read-only provider for request-instance observation metadata."""

import hashlib
import json
import os
import stat
import subprocess
from collections.abc import Iterable, Mapping
from pathlib import Path


class ObservationError(RuntimeError):
    """Observation failed closed."""


BLOCKED_AUTHORITY_NOT_CLOSED = "BLOCKED_AUTHORITY_NOT_CLOSED"
OBSERVATION_SECTIONS = ("authority", "source", "executor", "producer", "record",
                        "receipt", "publication", "root_audit", "preflight", "execution")


def _file_identity(path: Path) -> dict[str, object]:
    if path.is_symlink():
        raise ObservationError(f"symlink rejected: {path}")
    try:
        fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    except OSError as exc:
        raise ObservationError(f"open failed: {path}") from exc
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise ObservationError(f"regular file required: {path}")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(fd)
        if (before.st_dev, before.st_ino, before.st_size) != (after.st_dev, after.st_ino, after.st_size):
            raise ObservationError(f"identity drift: {path}")
        return {"path": str(path), "dev": before.st_dev, "ino": before.st_ino,
                "size": before.st_size, "mode": stat.S_IMODE(before.st_mode),
                "uid": before.st_uid, "gid": before.st_gid,
                "raw_sha256": hashlib.sha256(b"".join(chunks)).hexdigest()}
    finally:
        os.close(fd)


def _env_digest(env: Mapping[str, str], allowed: Iterable[str]) -> str:
    safe = {key: env[key] for key in sorted(set(allowed)) if key in env}
    return hashlib.sha256(json.dumps(safe, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def read_git_metadata(repo: Path, *, ref: str, paths: Iterable[str]) -> dict[str, object]:
    """Read fixed Git identities without fetch, mutation, or network access."""
    repo = Path(repo)

    def run(*args: str) -> str:
        try:
            result = subprocess.run(("git", "-C", str(repo), *args), check=True,
                                    capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.SubprocessError) as exc:
            raise ObservationError(f"{BLOCKED_AUTHORITY_NOT_CLOSED}: git read failed") from exc
        return result.stdout.strip()

    head = run("rev-parse", "HEAD")
    try:
        subprocess.run(("git", "-C", str(repo), "diff", "--cached", "--quiet"),
                       check=True, capture_output=True, timeout=10)
    except subprocess.CalledProcessError as exc:
        raise ObservationError(f"{BLOCKED_AUTHORITY_NOT_CLOSED}: dirty index") from exc
    except (OSError, subprocess.SubprocessError) as exc:
        raise ObservationError(f"{BLOCKED_AUTHORITY_NOT_CLOSED}: index read failed") from exc
    index_tree = run("rev-parse", "HEAD^{tree}")
    if len(head) != 40 or len(index_tree) != 40:
        raise ObservationError(f"{BLOCKED_AUTHORITY_NOT_CLOSED}: invalid git identity")
    blobs = {}
    for path in paths:
        line = run("ls-tree", head, "--", path)
        fields = line.split()
        if len(fields) != 4 or fields[1] != "blob":
            raise ObservationError(f"{BLOCKED_AUTHORITY_NOT_CLOSED}: blob identity missing: {path}")
        blobs[path] = fields[2]
    return {"head_revision": head, "index_tree_native_oid": index_tree,
            "ref_revision": run("rev-parse", ref), "blob_oids": blobs}


def observe_bundle(*, root: Path, files: Mapping[str, Path], target_paths: Iterable[Path],
                   argv: list[str], env: Mapping[str, str], env_allowlist: Iterable[str],
                   git_repo: Path | None = None, git_ref: str = "HEAD",
                   git_paths: Iterable[str] = ()) -> dict[str, object]:
    """Return an in-memory, payload-free observation bundle; never writes or mutates."""
    root = Path(root)
    root_stat = root.stat()
    if not stat.S_ISDIR(root_stat.st_mode) or root.is_symlink():
        raise ObservationError("root must be a non-symlink directory")
    identities = {name: _file_identity(Path(path)) for name, path in files.items()}
    targets = []
    for path in target_paths:
        path = Path(path)
        if path.exists() or path.is_symlink():
            raise ObservationError(f"target must be absent: {path}")
        targets.append(str(path))
    current_root = root.stat()
    if (root_stat.st_dev, root_stat.st_ino) != (current_root.st_dev, current_root.st_ino):
        raise ObservationError("root identity drift")
    git_metadata = None
    if git_repo is not None:
        git_metadata = read_git_metadata(git_repo, ref=git_ref, paths=git_paths)
    return {"root": {"path": str(root), "dev": root_stat.st_dev, "ino": root_stat.st_ino,
                      "mode": stat.S_IMODE(root_stat.st_mode), "uid": root_stat.st_uid, "gid": root_stat.st_gid},
            "files": identities, "target_paths": targets, "argv": list(argv),
            "cwd": str(Path.cwd()),
            "sanitized_env_sha256": _env_digest(env, env_allowlist), "git": git_metadata}


def build_observation_bundle(*, sections: Mapping[str, Mapping[str, object]],
                             metadata: Mapping[str, object]) -> dict[str, object]:
    """Combine provider observations into the exact ten-section in-memory contract."""
    if tuple(sections) != OBSERVATION_SECTIONS or any(not isinstance(value, Mapping)
                                                       for value in sections.values()):
        raise ObservationError(f"{BLOCKED_AUTHORITY_NOT_CLOSED}: ten sections required")
    required = {"head_revision", "index_tree_native_oid", "formal_root", "child_gitlink",
                "cwd", "interpreter", "git", "sanitized_env_sha256", "argv"}
    if set(metadata) != required:
        raise ObservationError(f"{BLOCKED_AUTHORITY_NOT_CLOSED}: metadata contract mismatch")
    return {"sections": {name: dict(sections[name]) for name in OBSERVATION_SECTIONS},
            "metadata": dict(metadata)}


def assemble_constructor_bundle(bundle: Mapping[str, object]) -> dict[str, object]:
    """Validate and return the flat constructor bundle without performing I/O."""
    from tools.psm_wma.build_source_evidence_closure_request_instance import (
        TOP_LEVEL_KEYS, build_request_instance,
    )
    if not isinstance(bundle, Mapping) or set(bundle) != set(TOP_LEVEL_KEYS):
        raise ObservationError(f"{BLOCKED_AUTHORITY_NOT_CLOSED}: flat schema bundle required")
    candidate = dict(bundle)
    candidate["sha256"] = ""
    try:
        raw = build_request_instance(candidate)
    except (TypeError, ValueError) as exc:
        raise ObservationError(f"{BLOCKED_AUTHORITY_NOT_CLOSED}: constructor contract failed") from exc
    import json as _json
    return _json.loads(raw)


def observation_to_bundle(template: Mapping[str, object], observation: Mapping[str, object],
                         *, formal_root: str, child_gitlink: str) -> dict[str, object]:
    """Deterministically bind observed identities into a complete constructor template."""
    if set(template) != {"schema", "formal_root", "child_gitlink", "authority", "source", "executor",
                          "producer", "record", "receipt", "publication", "root_audit", "preflight",
                          "execution", "sha256"} or set(observation) != {"root", "files", "target_paths", "argv",
                                                                         "cwd", "sanitized_env_sha256", "git"}:
        raise ObservationError(f"{BLOCKED_AUTHORITY_NOT_CLOSED}: observation/template contract mismatch")
    git = observation["git"]
    if not isinstance(git, Mapping) or set(git) != {"head_revision", "index_tree_native_oid", "ref_revision", "blob_oids"}:
        raise ObservationError(f"{BLOCKED_AUTHORITY_NOT_CLOSED}: git observation missing")
    result = json.loads(json.dumps(template))
    files = observation["files"]
    if not isinstance(files, Mapping):
        raise ObservationError(f"{BLOCKED_AUTHORITY_NOT_CLOSED}: file observation missing")

    def identity(*names: str) -> dict[str, object]:
        for name in names:
            value = files.get(name)
            if isinstance(value, Mapping):
                return dict(value)
        raise ObservationError(f"{BLOCKED_AUTHORITY_NOT_CLOSED}: observed file missing: {names[0]}")

    def blob_for(file_identity: Mapping[str, object]) -> str:
        path = str(file_identity["path"])
        blobs = git["blob_oids"]
        if path in blobs:
            return str(blobs[path])
        basename = Path(path).name
        if basename in blobs:
            return str(blobs[basename])
        raise ObservationError(f"{BLOCKED_AUTHORITY_NOT_CLOSED}: observed blob missing: {path}")

    module = identity("module")
    result["executor"]["module_path"] = module["path"]
    result["executor"]["module_raw_sha256"] = module["raw_sha256"]
    result["producer"]["module_path"] = module["path"]
    result["producer"]["module_raw_sha256"] = module["raw_sha256"]
    result["root_audit"]["module_path"] = module["path"]
    result["root_audit"]["module_raw_sha256"] = module["raw_sha256"]
    for section in ("executor", "producer", "root_audit"):
        result[section]["module_blob_native_oid"] = blob_for(module)

    def bind_file(section: str, path_key: str, raw_key: str, oid_key: str, *names: str) -> None:
        value = identity(*names)
        result[section][path_key] = value["path"]
        result[section][raw_key] = value["raw_sha256"]
        result[section][oid_key] = blob_for(value)

    if any(name in files for name in ("selection", "selection_path")):
        selection = identity("selection", "selection_path")
        result["authority"]["selection_path"] = selection["path"]
        result["authority"]["selection_raw_sha256"] = selection["raw_sha256"]
        result["authority"]["selection_blob_native_oid"] = blob_for(selection)
        result["source"]["selection_raw_sha256"] = selection["raw_sha256"]
    if any(name in files for name in ("config", "config_path")):
        bind_file("authority", "config_path", "config_raw_sha256", "config_blob_native_oid",
                  "config", "config_path")
    if any(name in files for name in ("interpreter", "interpreter_path")):
        interpreter = identity("interpreter", "interpreter_path")
        result["executor"]["interpreter_path"] = interpreter["path"]
        result["executor"]["interpreter_raw_sha256"] = interpreter["raw_sha256"]
    if "git" in files:
        git_file = identity("git")
        result["executor"]["git_path"] = git_file["path"]
        result["executor"]["git_raw_sha256"] = git_file["raw_sha256"]
    result["executor"]["cwd"] = observation["cwd"]
    result["executor"]["argv"] = list(observation["argv"])
    result["executor"]["sanitized_env_sha256"] = observation["sanitized_env_sha256"]
    result["formal_root"] = formal_root
    result["child_gitlink"] = child_gitlink
    result["preflight"]["head_revision"] = git["head_revision"]
    result["preflight"]["index_tree_native_oid"] = git["index_tree_native_oid"]
    result["authority"]["local_ref_revision"] = git["ref_revision"]
    result["authority"]["remote_ref_revision"] = git["ref_revision"]
    result["preflight"]["absent_paths"] = list(observation["target_paths"])
    result["sha256"] = ""
    return result


def observe_and_assemble(*, root: Path, files: Mapping[str, Path], target_paths: Iterable[Path],
                         argv: list[str], env: Mapping[str, str], env_allowlist: Iterable[str],
                         git_repo: Path, git_ref: str, git_paths: Iterable[str],
                         bundle_template: Mapping[str, object], formal_root: str,
                         child_gitlink: str) -> dict[str, object]:
    """Run one read-only observation and deterministically validate its flat bundle."""
    observation = observe_bundle(root=root, files=files, target_paths=target_paths,
                                argv=argv, env=env, env_allowlist=env_allowlist,
                                git_repo=git_repo, git_ref=git_ref, git_paths=git_paths)
    try:
        bundle = observation_to_bundle(bundle_template, observation,
                                       formal_root=formal_root, child_gitlink=child_gitlink)
    except Exception as exc:
        raise ObservationError(f"{BLOCKED_AUTHORITY_NOT_CLOSED}: bundle assembly failed") from exc
    if not isinstance(bundle, Mapping):
        raise ObservationError(f"{BLOCKED_AUTHORITY_NOT_CLOSED}: flat bundle required")
    return assemble_constructor_bundle(bundle)
