"""Read-only provider for request-instance observation metadata."""

import hashlib
import json
import os
import stat
from collections.abc import Iterable, Mapping
from pathlib import Path


class ObservationError(RuntimeError):
    """Observation failed closed."""


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


def observe_bundle(*, root: Path, files: Mapping[str, Path], target_paths: Iterable[Path],
                   argv: list[str], env: Mapping[str, str], env_allowlist: Iterable[str]) -> dict[str, object]:
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
    return {"root": {"path": str(root), "dev": root_stat.st_dev, "ino": root_stat.st_ino,
                      "mode": stat.S_IMODE(root_stat.st_mode), "uid": root_stat.st_uid, "gid": root_stat.st_gid},
            "files": identities, "target_paths": targets, "argv": list(argv),
            "sanitized_env_sha256": _env_digest(env, env_allowlist)}
