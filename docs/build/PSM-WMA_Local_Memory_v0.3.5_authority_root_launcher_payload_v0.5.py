"""Frozen stdlib-only launcher payload; it is executed only via reviewed ``-c`` bytes."""
import ast
import hashlib
import json
import os
import re
import stat
import subprocess
import sys

ROOT = "/disk/rl/psm_wma"
FORMAL = "9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5"
GIT = "/usr/bin/git"
PYTHON = "/opt/conda/bin/python3"
CLEAN = ROOT + "/.authority-root-materialization-9dd2fb8"
PREFIX = (GIT, "--no-replace-objects", "-c", "core.hooksPath=/dev/null", "-c",
          "core.attributesFile=/dev/null", "-c", "filter.lfs.process=", "-c",
          "protocol.file.allow=never")
ENV = {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1",
       "GIT_CONFIG_SYSTEM": "/dev/null", "GIT_NO_REPLACE_OBJECTS": "1",
       "LANG": "C", "LC_ALL": "C"}
INPUT_DOC = ("docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_execution_snapshot_annex_v0.2.md",
             "6510d6b546cb855839e4a1dd414025aacac0ce59")
ARGV_DOC = ("docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_execution_snapshot_annex_v0.3.md",
            "332beb80023b71470d7be452f0af33edb266064f")
ADAPTER = ("tools/psm_wma/materialize_immutable_source_authority_root.py",
           "da782754b8e8efa0f3cae973aa68602dcda1c237")
EXPECTED = (
    (".authority-root.selection.json", 3,
     "8fe4585f366cb69ad9181e30c25b5f4e99040c83d8ffe66426897bfa9d331edd"),
    (".authority-root.config.json", 4,
     "43b3b77b5934107c54b8bee157b46d07cb17b85ca89305ad6fb7405237e42d1d"),
    (".authority-root.bootstrap-contract.json", 5,
     "62a7bbf5fcb609e52931639001e6db01df81f0de2a33afd41c0080eb8e903f68"),
)


class Stop(RuntimeError):
    pass


def fail(message):
    raise Stop(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def regular(path):
    value = os.lstat(path)
    if stat.S_ISLNK(value.st_mode) or not stat.S_ISREG(value.st_mode):
        fail("non-regular authority path")
    return value


def route_snapshot():
    if sha(open(GIT, "rb").read()) != "587ef21868c948b883993e23209b86a72a6ddc06aab1545c697ffc31075acd4a":
        fail("git identity")
    admin = ROOT + "/.git"
    value = os.lstat(admin)
    if stat.S_ISLNK(value.st_mode) or not stat.S_ISDIR(value.st_mode):
        fail("parent git route")
    config = admin + "/config"
    saved = regular(config)
    raw = open(config, "rb").read()
    if os.path.lexists(admin + "/config.worktree"):
        fail("parent config.worktree")
    allowed = {"core.repositoryformatversion", "core.filemode", "core.bare",
               "core.logallrefupdates", "core.worktree", "extensions.worktreeconfig"}
    section = None
    seen = set()
    for line in raw.decode("utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip().lower()
            if not section or '"' in section or "." in section:
                fail("config section")
            continue
        if section is None or "=" not in line:
            fail("config grammar")
        key, value = (part.strip() for part in line.split("=", 1))
        key = section + "." + key.lower()
        if key not in allowed or key in seen:
            fail("config allowlist")
        seen.add(key)
        if ((key == "core.repositoryformatversion" and value != "0") or
                (key == "core.bare" and value != "false") or
                (key in ("core.filemode", "core.logallrefupdates") and value not in ("true", "false")) or
                (key == "extensions.worktreeconfig" and value != "false") or
                (key == "core.worktree" and value != ROOT)):
            fail("config value")
    return (admin, (saved.st_dev, saved.st_ino, saved.st_size), raw)


def check_route(snapshot):
    admin, identity, raw = snapshot
    value = os.lstat(admin)
    config = regular(admin + "/config")
    if stat.S_ISLNK(value.st_mode) or not stat.S_ISDIR(value.st_mode):
        fail("parent git route drift")
    if (config.st_dev, config.st_ino, config.st_size) != identity or open(admin + "/config", "rb").read() != raw:
        fail("parent config drift")
    if os.path.lexists(admin + "/config.worktree"):
        fail("parent config.worktree drift")


def git(snapshot, *argv, input=None):
    check_route(snapshot)
    result = subprocess.run([*PREFIX, "-C", ROOT, *argv], env=ENV, input=input,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    check_route(snapshot)
    if result.returncode:
        fail("native git")
    return result.stdout


def frozen_blob(snapshot, path, oid):
    listing = git(snapshot, "ls-tree", FORMAL, "--", path).decode().strip().split("\t", 1)
    if len(listing) != 2 or listing[0].split() != ["100644", "blob", oid] or listing[1] != path:
        fail("formal blob identity")
    return git(snapshot, "cat-file", "blob", oid)


def fenced(raw, heading):
    marker = heading.encode() if isinstance(heading, str) else heading
    match = re.search(marker + rb"[\s\S]*?```json\n(.*?)\n```", raw)
    if not match:
        fail("frozen document grammar")
    return match.group(1)


def bootstrap(adapter):
    tree = ast.parse(adapter.decode("utf-8"))
    node = next((item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == "bootstrap_payload"), None)
    if node is None or not isinstance(node.body[-1], ast.Return):
        fail("bootstrap AST")
    value = node.body[-1].value
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        raw = value.value.encode()
    elif isinstance(value, ast.Tuple):
        raw = "".join(item.value for item in value.elts if isinstance(item, ast.Constant) and isinstance(item.value, str)).encode()
    else:
        fail("bootstrap constants")
    if len(raw) != 7538 or sha(raw) != "7e1c0ecc2161984a88ea0d0eae82f9f7ced709ca919f0302f74a3a068e08c9b8":
        fail("bootstrap identity")
    return raw.decode("utf-8")


def absent(path):
    if os.path.lexists(path):
        fail("fresh path")


def main():
    snapshot = route_snapshot()
    for path in (CLEAN, CLEAN + "/.authority-root.index",
                 ROOT + "/artifacts/g0/r09/authority_root_materialization_evidence_v1.json",
                 ROOT + "/artifacts/g0/r09/authority_root_materialization_evidence_v1.json.pending"):
        absent(path)
    inputs = frozen_blob(snapshot, *INPUT_DOC)
    argv_doc = frozen_blob(snapshot, *ARGV_DOC)
    adapter = frozen_blob(snapshot, *ADAPTER)
    selection = fenced(inputs, b"selection raw UTF-8")
    config = fenced(inputs, b"config raw UTF-8")
    actual = json.loads(fenced(argv_doc, "唯一 `actual_argv` raw UTF-8".encode()))
    boot = bootstrap(adapter)
    contract = json.dumps({"bootstrap_argv_sha256": sha(json.dumps(["--", *actual], separators=(",", ":"), ensure_ascii=False).encode()),
                           "bootstrap_raw_sha256": sha(boot.encode())}, sort_keys=True, separators=(",", ":")).encode()
    data = (selection, config, contract)
    if any(sha(raw) != item[2] for raw, item in zip(data, EXPECTED)):
        fail("input identity")
    git(snapshot, "worktree", "add", "--detach", CLEAN, FORMAL)
    readers = []
    try:
        for raw, (name, target, digest) in zip(data, EXPECTED):
            path = CLEAN + "/" + name
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
            try:
                offset = 0
                while offset < len(raw):
                    written = os.write(fd, raw[offset:])
                    if written <= 0:
                        fail("writer short write")
                    offset += written
                os.fsync(fd)
                value = os.fstat(fd)
                if not stat.S_ISREG(value.st_mode) or stat.S_IMODE(value.st_mode) != 0o600:
                    fail("writer identity")
            finally:
                os.close(fd)
            rd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
            if sha(os.pread(rd, len(raw), 0)) != digest:
                fail("reader bytes")
            os.dup2(rd, target); os.close(rd); os.lseek(target, 0, os.SEEK_SET); readers.append(target)
        os.execve(PYTHON, [PYTHON, "-I", "-S", "-B", "-c", boot, "--", *actual], ENV)
    finally:
        for fd in readers:
            try: os.close(fd)
            except OSError: pass
        git(snapshot, "worktree", "remove", "--force", CLEAN)


if __name__ == "__main__":
    main()
