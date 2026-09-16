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


def observe_and_assemble(*, root: Path, files: Mapping[str, Path], target_paths: Iterable[Path],
                         argv: list[str], env: Mapping[str, str], env_allowlist: Iterable[str],
                         git_repo: Path, git_ref: str, git_paths: Iterable[str],
                         bundle_builder) -> dict[str, object]:
    """Run one read-only observation and deterministically validate its flat bundle."""
    if not callable(bundle_builder):
        raise ObservationError(f"{BLOCKED_AUTHORITY_NOT_CLOSED}: bundle builder required")
    observation = observe_bundle(root=root, files=files, target_paths=target_paths,
                                argv=argv, env=env, env_allowlist=env_allowlist,
                                git_repo=git_repo, git_ref=git_ref, git_paths=git_paths)
    try:
        bundle = bundle_builder(observation)
    except Exception as exc:
        raise ObservationError(f"{BLOCKED_AUTHORITY_NOT_CLOSED}: bundle assembly failed") from exc
    if not isinstance(bundle, Mapping):
        raise ObservationError(f"{BLOCKED_AUTHORITY_NOT_CLOSED}: flat bundle required")
    return assemble_constructor_bundle(bundle)
