"""受控发布已构造的 Stage-1 request pair 字节。

本模块不构造 payload，不访问 Git/网络，也不读取凭据；调用者必须先完成
冻结输入和 ``build_pair``，这里只负责两文件的安全发布与回读校验。
"""
from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path


class PairPublicationError(RuntimeError):
    """pair 发布或回读校验失败。"""


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _regular(path: Path) -> None:
    value = path.lstat()
    if not value.is_file() or value.is_symlink():
        raise PairPublicationError(f"unsafe pair path: {path}")


def publish_verified_pair(
    json_path: Path, markdown_path: Path, json_raw: bytes, markdown_raw: bytes
) -> None:
    """以可恢复事务发布一对已验证的 canonical bytes。

    已存在的 pair 必须与输入逐字节一致；否则在任何写入前拒绝。
    """
    if json_path.parent != markdown_path.parent:
        raise PairPublicationError("pair paths must share a parent")
    parent = json_path.parent
    parent.mkdir(parents=True, exist_ok=True)
    previous: dict[Path, bytes | None] = {}
    for path, raw in ((json_path, json_raw), (markdown_path, markdown_raw)):
        if path.exists() or path.is_symlink():
            _regular(path)
            previous[path] = path.read_bytes()
            if previous[path] != raw:
                raise PairPublicationError(f"divergent existing pair member: {path}")
        else:
            previous[path] = None
    staged: list[tuple[Path, Path]] = []
    try:
        for path, raw in ((json_path, json_raw), (markdown_path, markdown_raw)):
            fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=parent)
            temporary = Path(name)
            staged.append((path, temporary))
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
                if temporary.read_bytes() != raw or _digest(temporary.read_bytes()) != _digest(raw):
                    raise PairPublicationError("staged pair bytes drift")
            except BaseException:
                temporary.unlink(missing_ok=True)
                raise
        for path, temporary in staged:
            os.replace(temporary, path)
        if json_path.read_bytes() != json_raw or markdown_path.read_bytes() != markdown_raw:
            raise PairPublicationError("published pair bytes drift")
    except BaseException as error:
        for path, _ in staged:
            if previous[path] is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(previous[path])
        for _, temporary in staged:
            temporary.unlink(missing_ok=True)
        if isinstance(error, PairPublicationError):
            raise
        raise PairPublicationError("pair publication failed") from error
