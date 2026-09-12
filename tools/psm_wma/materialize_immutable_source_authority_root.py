"""Temporary-only native Git adapter for authority-root CPU/static tests."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Mapping

from tools.psm_wma.immutable_source_collection import AUTHORITY_REF, TreeEntry


class NativeGitError(RuntimeError):
    pass


class NativeAuthorityGit:
    """Explicit-identity Git transaction; callers must provide a temporary repository."""

    def __init__(self, git: Path, cwd: Path, remote: str, index: Path) -> None:
        if not git.is_absolute() or not cwd.is_absolute() or not index.is_absolute():
            raise NativeGitError("git/cwd/index 必须为绝对路径")
        self.git, self.cwd, self.remote, self.index = git, cwd, remote, index
        self.env = {"GIT_INDEX_FILE": str(index), "LC_ALL": "C", "LANG": "C"}

    def _run(self, *args: str, input: bytes | None = None, check: bool = True) -> str:
        completed = subprocess.run(
            [str(self.git), *args], cwd=self.cwd, env=self.env, input=input,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, check=False,
        )
        if check and completed.returncode:
            raise NativeGitError(completed.stderr.decode("utf-8", "replace").strip())
        return completed.stdout.decode().strip()

    def tree_entries(self, revision: str) -> Mapping[str, TreeEntry]:
        result: dict[str, TreeEntry] = {}
        for line in self._run("ls-tree", "-r", "-z", revision).split("\0"):
            if not line:
                continue
            meta, path = line.split("\t", 1)
            mode, kind, oid = meta.split()
            result[path] = (mode, kind, oid)
        return result

    def parents(self, revision: str) -> tuple[str, ...]:
        return tuple(self._run("show", "-s", "--format=%P", revision).split())

    def blob_bytes(self, oid: str) -> bytes:
        return subprocess.run([str(self.git), "cat-file", "blob", oid], cwd=self.cwd, env=self.env, stdout=subprocess.PIPE, check=True).stdout

    def gitlink_at(self, revision: str) -> str:
        return self.tree_entries(revision)["cosmos-framework"][2]

    def create_detached_commit(self, parent: str, blobs: Mapping[str, bytes]) -> str:
        self._run("read-tree", parent)
        for path, raw in blobs.items():
            oid = self._run("hash-object", "-w", "--stdin", input=raw)
            self._run("update-index", "--add", "--cacheinfo", f"100644,{oid},{path}")
        tree = self._run("write-tree")
        return self._run("commit-tree", tree, "-p", parent)

    def local_ref(self, ref: str) -> str | None:
        value = self._run("rev-parse", "--verify", "-q", ref, check=False)
        return value or None

    def remote_ref(self, ref: str) -> str | None:
        value = self._run("ls-remote", self.remote, ref)
        return value.split()[0] if value else None

    def cas_create_local(self, ref: str, revision: str) -> bool:
        return not bool(self._run("update-ref", ref, revision, "0" * 40, check=False)) and self.local_ref(ref) == revision

    def cas_create_remote(self, ref: str, revision: str) -> bool:
        self._run("push", "--porcelain", f"--force-with-lease={ref}:", self.remote, f"{revision}:{ref}", check=False)
        return self.remote_ref(ref) == revision

    def cas_delete_local(self, ref: str, revision: str) -> bool:
        self._run("update-ref", "-d", ref, revision, check=False)
        return self.local_ref(ref) is None

    def cas_delete_remote(self, ref: str, revision: str) -> bool:
        self._run("push", "--porcelain", f"--force-with-lease={ref}:{revision}", self.remote, f":{ref}", check=False)
        return self.remote_ref(ref) is None
