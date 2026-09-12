"""Temporary-only authority seams for the reviewed v0.7 launcher contract."""
from __future__ import annotations

import os
import stat
from pathlib import Path


class WitnessFailure(RuntimeError):
    pass


def identity(value: os.stat_result) -> tuple[int, int, int]:
    return value.st_dev, value.st_ino, value.st_size


def regular_mode_0600(path: Path) -> tuple[int, int, int]:
    value = os.lstat(path)
    if stat.S_ISLNK(value.st_mode) or not stat.S_ISREG(value.st_mode):
        raise WitnessFailure("backing path is not regular")
    if stat.S_IMODE(value.st_mode) != 0o600:
        raise WitnessFailure("backing path mode")
    return identity(value)


def verify_handoff_path(path: Path, reader_fd: int, target_fd: int) -> None:
    """Reject replacement/mode drift after reader open and after target dup."""
    expected = regular_mode_0600(path)
    reader = identity(os.fstat(reader_fd))
    target = identity(os.fstat(target_fd))
    if expected != reader or reader != target:
        raise WitnessFailure("backing pathname identity drift")
    if regular_mode_0600(path) != expected:
        raise WitnessFailure("backing pathname post-handoff drift")


def require_commondir_absent(admin: Path) -> None:
    if os.path.lexists(admin / "commondir"):
        raise WitnessFailure("unbound commondir")


def classify_add_failure(clean: Path, listed: bool) -> str:
    """Only a proved no-residue state may be ordinary failure."""
    if os.path.lexists(clean) or listed:
        return "ROLLBACK_INCOMPLETE"
    return "FAIL"
