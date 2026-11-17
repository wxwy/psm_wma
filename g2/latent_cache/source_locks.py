"""Reader leases across source-index retirement; no renderer/VAE dependency."""

from __future__ import annotations

import fcntl
import os
import stat
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

from .contract import CacheError, contained

_WRITER = ContextVar("g2_source_retirement_writer", default=None)


def writer_owned(root):
    return _WRITER.get() == str(Path(root).absolute())


def lock_path(root):
    return Path(root).absolute() / "vae_cache" / ".source.lock"


def _open(path, *, create=False):
    flags = os.O_NOFOLLOW | (os.O_RDWR | os.O_CREAT if create else os.O_RDONLY)
    try:
        fd = os.open(path, flags, 0o600)
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            os.close(fd)
            raise CacheError("source reader lease must be a regular file")
        return fd
    except OSError as exc:
        raise CacheError("cannot open source reader lease") from exc


def _lock(fd, mode):
    try:
        fcntl.flock(fd, mode | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        os.close(fd)
        raise CacheError("source retirement/reader lease is busy") from exc
    return fd


def reader_lease(root):
    """An existing manifest is the bootstrap lock for legacy read-only data.

    The writer holds that inode exclusively while installing the permanent
    lock. A reader rechecks the permanent path after locking the old inode,
    avoiding the otherwise unsafe lock-file creation/swap race.
    """
    root = Path(root)
    if writer_owned(root):
        return None
    permanent = lock_path(root)
    if permanent.is_symlink():
        raise CacheError("symlink source reader lease")
    if permanent.exists():
        return _lock(_open(permanent), fcntl.LOCK_SH)
    manifest = contained(root, "vae_cache/manifest.json")
    fd = _lock(_open(manifest), fcntl.LOCK_SH)
    if permanent.exists() or permanent.is_symlink():
        os.close(fd)
        return reader_lease(root)
    return fd


def release_lease(fd):
    if fd is not None:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


@contextmanager
def writer_lease(root):
    permanent = lock_path(root)
    bootstrap = None
    fd = None
    token = None
    try:
        if not permanent.exists():
            bootstrap = _lock(
                _open(contained(root, "vae_cache/manifest.json")), fcntl.LOCK_EX
            )
        fd = _lock(_open(permanent, create=True), fcntl.LOCK_EX)
        token = _WRITER.set(str(Path(root).absolute()))
        yield
    finally:
        if token is not None:
            _WRITER.reset(token)
        release_lease(fd)
        release_lease(bootstrap)
