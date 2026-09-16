"""Atomically publish an already validated request-instance pair."""

import hashlib
import json
import os
import stat
from pathlib import Path

from tools.psm_wma.build_source_evidence_closure_request_instance import verify_instance_bytes


class RealOutputWriteError(RuntimeError):
    """The request-instance pair could not be published safely."""


APPROVED_JSON_NAME = "PSM-WMA_Local_Memory_v0.3.5_source_evidence_closure_request_instance_v1.json"
APPROVED_MARKDOWN_NAME = APPROVED_JSON_NAME[:-5] + ".md"
APPROVED_STAGE_NAME = ".request_instance_stage"

def _parent_fd(directory: Path) -> int:
    return os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW)


def _readback(fd: int, parent_fd: int, raw: bytes, parent_identity: tuple[int, int], expected_sha: str,
              *, self_bound: bool = False) -> None:
    info = os.fstat(fd)
    if (not stat.S_ISREG(info.st_mode) or (info.st_mode & 0o777) != 0o644
            or (info.st_dev, info.st_ino) == (0, 0) or info.st_size != len(raw)):
        raise RealOutputWriteError("readback identity/mode/size failed")
    if info.st_uid != os.getuid() or info.st_gid != os.getgid():
        raise RealOutputWriteError("readback owner failed")
    parent = os.fstat(parent_fd)
    if (parent.st_dev, parent.st_ino) != parent_identity:
        raise RealOutputWriteError("readback parent identity failed")
    os.lseek(fd, 0, os.SEEK_SET)
    if os.read(fd, len(raw) + 1) != raw:
        raise RealOutputWriteError("readback bytes/self-bound SHA failed")
    if (verify_instance_bytes(raw) if self_bound else hashlib.sha256(raw).hexdigest()) != expected_sha:
        raise RealOutputWriteError("readback bytes/self-bound SHA failed")


def _stage(parent_fd: int, name: str, raw: bytes) -> None:
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
                 0o644, dir_fd=parent_fd)
    try:
        offset = 0
        while offset < len(raw):
            written = os.write(fd, raw[offset:])
            if written <= 0:
                raise RealOutputWriteError("staging short write")
            offset += written
        os.fsync(fd)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or (info.st_mode & 0o777) != 0o644:
            raise RealOutputWriteError("staging mode/type failed")
    finally:
        os.close(fd)
    os.fsync(parent_fd)


def write_request_pair(json_bytes: bytes, markdown_bytes: bytes, directory: Path,
                       *, expected_formal_root: str,
                       expected_child_gitlink: str,
                       expected_instance_sha256: str) -> dict[str, object]:
    """Publish JSON then Markdown, returning only structured residue on failure."""
    digest = verify_instance_bytes(json_bytes)
    value = json.loads(json_bytes)
    if value["formal_root"] != expected_formal_root:
        raise RealOutputWriteError("formal root drift")
    if value["child_gitlink"] != expected_child_gitlink:
        raise RealOutputWriteError("child gitlink drift")
    if digest != expected_instance_sha256:
        raise RealOutputWriteError("instance SHA drift")
    if digest.encode("ascii") not in markdown_bytes:
        raise RealOutputWriteError("markdown sibling SHA drift")
    directory = Path(directory)
    residue = {"terminal": "REAL_OUTPUT_WRITE_FAILED", "published": [],
               "stage_paths": [], "target_paths": [], "published_side": [],
               "failure": ""}
    names = ("request_instance.json", "request_instance.md")
    raws = (json_bytes, markdown_bytes)
    try:
        directory.mkdir(mode=0o700, parents=False, exist_ok=False)
    except OSError as exc:
        residue["failure"] = str(exc)
        return residue
    fd = -1
    staged = tuple(name + ".staged" for name in names)
    residue["stage_paths"] = [str(directory / name) for name in staged]
    residue["target_paths"] = [str(directory / name) for name in names]
    published: list[str] = []
    try:
        fd = _parent_fd(directory)
        parent = os.fstat(fd)
        parent_identity = (parent.st_dev, parent.st_ino)
        for stage, raw in zip(staged, raws):
            _stage(fd, stage, raw)
        for name, stage, raw in zip(names, staged, raws):
            try:
                os.link(stage, name, src_dir_fd=fd, dst_dir_fd=fd, follow_symlinks=False)
            except OSError as exc:
                raise RealOutputWriteError(f"publish {name} failed") from exc
            os.fsync(fd)
            check = os.open(name, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW, dir_fd=fd)
            try:
                _readback(check, fd, raw, parent_identity,
                          digest if name.endswith("json") else hashlib.sha256(raw).hexdigest(),
                          self_bound=name.endswith("json"))
            finally:
                os.close(check)
            published.append(name)
        for stage in staged:
            os.unlink(stage, dir_fd=fd)
        os.fsync(fd)
        os.close(fd)
        fd = -1
        return {"terminal": "PASS", "published": list(names), "instance_sha256": digest}
    except BaseException as exc:
        residue["published"] = published
        residue["published_side"] = list(published)
        residue["failure"] = str(exc)
        residue["residue"] = [{"path": path, "exists": Path(path).exists(),
                               "size": Path(path).stat().st_size if Path(path).is_file() else None,
                               "raw_sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest()
                               if Path(path).is_file() else None}
                              for path in residue["stage_paths"] + residue["target_paths"]]
        return residue
    finally:
        if fd >= 0:
            os.close(fd)


def write_approved_request_pair(json_bytes: bytes, markdown_bytes: bytes, build_directory: Path,
                               *, expected_formal_root: str,
                               expected_child_gitlink: str,
                               expected_instance_sha256: str) -> dict[str, object]:
    """Publish the approved versioned siblings using a separate staging directory."""
    digest = verify_instance_bytes(json_bytes)
    value = json.loads(json_bytes)
    if (value["formal_root"] != expected_formal_root
            or value["child_gitlink"] != expected_child_gitlink
            or digest != expected_instance_sha256
            or digest.encode("ascii") not in markdown_bytes):
        raise RealOutputWriteError("approved identity or Markdown SHA drift")
    build_directory = Path(build_directory)
    names = (APPROVED_JSON_NAME, APPROVED_MARKDOWN_NAME)
    targets = tuple(build_directory / name for name in names)
    stage_dir = build_directory / APPROVED_STAGE_NAME
    residue: dict[str, object] = {"terminal": "REAL_OUTPUT_WRITE_FAILED", "published": [],
                                  "published_side": [], "target_paths": [str(path) for path in targets],
                                  "stage_paths": [str(stage_dir / (name + ".staged")) for name in names]}
    if not build_directory.is_dir() or any(path.exists() or path.is_symlink() for path in targets):
        residue["failure"] = "approved target directory/targets preflight failed"
        return residue
    try:
        stage_dir.mkdir(mode=0o700, exist_ok=False)
    except OSError as exc:
        residue["failure"] = str(exc)
        return residue
    target_fd = stage_fd = -1
    published: list[str] = []
    try:
        target_fd = _parent_fd(build_directory)
        stage_fd = _parent_fd(stage_dir)
        stage_names = tuple(name + ".staged" for name in names)
        for stage_name, raw in zip(stage_names, (json_bytes, markdown_bytes)):
            _stage(stage_fd, stage_name, raw)
        for name, stage_name, raw in zip(names, stage_names, (json_bytes, markdown_bytes)):
            try:
                os.link(stage_name, name, src_dir_fd=stage_fd, dst_dir_fd=target_fd,
                        follow_symlinks=False)
            except OSError as exc:
                raise RealOutputWriteError(f"publish {name} failed") from exc
            os.fsync(target_fd)
            check = os.open(name, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW, dir_fd=target_fd)
            try:
                parent = os.fstat(target_fd)
                _readback(check, target_fd, raw, (parent.st_dev, parent.st_ino),
                          digest if name.endswith("json") else hashlib.sha256(raw).hexdigest(),
                          self_bound=name.endswith("json"))
            finally:
                os.close(check)
            published.append(name)
        for stage_name in stage_names:
            os.unlink(stage_name, dir_fd=stage_fd)
        os.fsync(stage_fd)
        os.close(stage_fd)
        stage_fd = -1
        stage_dir.rmdir()
        return {"terminal": "PASS", "published": list(names), "published_side": "both",
                "instance_sha256": digest}
    except BaseException as exc:
        residue["published"] = published
        residue["published_side"] = ("none" if not published else "json" if len(published) == 1 else "both")
        residue["failure"] = str(exc)
        residue["residue"] = [{"path": path, "exists": Path(path).exists(),
                               "size": Path(path).stat().st_size if Path(path).is_file() else None,
                               "raw_sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest()
                               if Path(path).is_file() else None}
                              for path in residue["stage_paths"] + residue["target_paths"]]
        return residue
    finally:
        if stage_fd >= 0:
            os.close(stage_fd)
        if target_fd >= 0:
            os.close(target_fd)
