"""受控发布已构造的 Stage-1 request pair 字节。

本模块不构造 payload，不访问 Git/网络，也不读取凭据；调用者必须先完成
冻结输入和 ``build_pair``，这里只负责两文件的安全发布与回读校验。
"""
from __future__ import annotations

import hashlib
import argparse
import json
import os
import stat
import tempfile
from pathlib import Path

from tools.psm_wma.build_stage1_request_pair import build_pair, verify_pair


class PairPublicationError(RuntimeError):
    """pair 发布或回读校验失败。"""


_BASE_ENV = frozenset(("GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM", "GIT_CONFIG_SYSTEM", "GIT_NO_REPLACE_OBJECTS", "LANG", "LC_ALL"))
_HELPER_ENV = frozenset(("GIT_CONFIG_COUNT", "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0"))
_FORBIDDEN_ENV = frozenset(("HOME", "GH_TOKEN", "GITHUB_TOKEN", "GIT_ASKPASS"))
_GH_ENV = {"GH_CONFIG_DIR": "/root/.config/gh"}


def validate_pair_environment(environment: dict[str, str]) -> None:
    """验证 pair 中可公开记录的 Git 环境描述，不接收任何凭据。"""
    keys = frozenset(environment)
    if _FORBIDDEN_ENV & keys or not _BASE_ENV <= keys or not keys <= _BASE_ENV | _HELPER_ENV:
        raise PairPublicationError("pair environment allowlist")
    if keys & _HELPER_ENV:
        descriptor = {
            **{key: environment[key] for key in _BASE_ENV},
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "credential.https://github.com.helper",
            "GIT_CONFIG_VALUE_0": "!/usr/bin/gh auth git-credential",
        }
        if environment not in (descriptor, {**descriptor, **_GH_ENV}):
            raise PairPublicationError("pair credential helper descriptor")


def produce_pair(
    json_path: Path,
    markdown_path: Path,
    payload: dict[str, object],
) -> tuple[bytes, bytes]:
    """构造并发布一个已通过 canonical 校验的 request pair。"""
    environment = payload.get("environment")
    if not isinstance(environment, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in environment.items()
    ):
        raise PairPublicationError("pair environment descriptor")
    validate_pair_environment(environment)
    json_raw, markdown_raw = build_pair(json_path, payload)
    verify_pair(json_path, json_raw, markdown_raw)
    publish_verified_pair(json_path, markdown_path, json_raw, markdown_raw)
    return json_raw, markdown_raw


def main() -> None:
    parser = argparse.ArgumentParser(description="publish one frozen Stage-1 request pair")
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--json", dest="json_path", type=Path, required=True)
    parser.add_argument("--markdown", dest="markdown_path", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.payload.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PairPublicationError("payload must be an object")
    produce_pair(args.json_path, args.markdown_path, payload)


if __name__ == "__main__":
    main()


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _regular(path: Path) -> None:
    value = path.lstat()
    if stat.S_ISLNK(value.st_mode) or not stat.S_ISREG(value.st_mode):
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
