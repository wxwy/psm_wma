"""Frozen stdlib-only authority-root launcher; executed only from reviewed ``-c`` bytes."""
import ast
import base64
import hashlib
import json
import os
import stat
import subprocess

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
ADAPTER = ("tools/psm_wma/materialize_immutable_source_authority_root.py",
           "da782754b8e8efa0f3cae973aa68602dcda1c237")
# These are the exact v0.2/v0.3 canonical bytes.  They are intentionally embedded:
# their historical document trees are not children of FORMAL.
RAW = (
    base64.b64decode("eyJlbnRyaWVzIjpbeyJvcmRpbmFsIjowLCJyZWxhdGl2ZV9wYXRoIjoibW9kZWwvLm1ldGFkYXRhIn0seyJvcmRpbmFsIjoxLCJyZWxhdGl2ZV9wYXRoIjoibW9kZWwvX18wXzAuZGlzdGNwIn0seyJvcmRpbmFsIjoyLCJyZWxhdGl2ZV9wYXRoIjoib3B0aW0vLm1ldGFkYXRhIn0seyJvcmRpbmFsIjozLCJyZWxhdGl2ZV9wYXRoIjoib3B0aW0vX18wXzAuZGlzdGNwIn0seyJvcmRpbmFsIjo0LCJyZWxhdGl2ZV9wYXRoIjoic2NoZWR1bGVyLy5tZXRhZGF0YSJ9LHsib3JkaW5hbCI6NSwicmVsYXRpdmVfcGF0aCI6InNjaGVkdWxlci9fXzBfMC5kaXN0Y3AifSx7Im9yZGluYWwiOjYsInJlbGF0aXZlX3BhdGgiOiJ0cmFpbmVyLy5tZXRhZGF0YSJ9LHsib3JkaW5hbCI6NywicmVsYXRpdmVfcGF0aCI6InRyYWluZXIvX18wXzAuZGlzdGNwIn1dLCJzY2hlbWEiOiJpbW11dGFibGVfc291cmNlX3NlbGVjdGlvbl9yZXF1ZXN0X3YxIiwic291cmNlX2tpbmQiOiJjaGVja3BvaW50X3NvdXJjZV9tYW5pZmVzdF92MSJ9"),
    base64.b64decode("eyJlbmFibGVfaW5wdXRfYmlhcyI6ZmFsc2UsImtfbG9jYWwiOjEsImxvY2FsX2V2aWRlbmNlX2ZlYXR1cmVfdmVyc2lvbiI6ImNhdXNhbF92aXN1YWw5Nl9leGVjdXRlZF9hY3Rpb24xMF92MSIsImxvY2FsX2Zhc3Rfc3RhdGVfZHR5cGUiOiJmcDMyIiwibG9jYWxfaGlzdG9yeV9iYWNrZW5kIjoidHR0X2Zhc3Rfd2VpZ2h0IiwibG9jYWxfaGlzdG9yeV9lbmFibGVkIjp0cnVlLCJsb2NhbF9oaXN0b3J5X2V2aWRlbmNlX2RpbSI6MTA2LCJsb2NhbF9oaXN0b3J5X3N0YXRlX2VuYWJsZWQiOmZhbHNlLCJsb2NhbF9tZW1vcnlfZGltIjozMiwibG9jYWxfbWVtb3J5X2VuYWJsZWQiOnRydWUsImxvY2FsX3J1bnRpbWVfcmVzdW1lX21vZGUiOiJzbG93X29ubHlfbm9fbWlkX2VwaXNvZGVfcmVzdW1lIiwibG9jYWxfdHR0X2VuYWJsZWQiOnRydWUsInNjaGVtYSI6ImNhbm9uaWNhbF9uYXRpdmVfbG9jYWxfdHR0X2NvbmZpZ192MiIsInR0dF9pbm5lcl9sciI6MC4xLCJ0dHRfdGJwdHRfc3RlcHMiOjE2fQ=="),
    base64.b64decode("WyItLXNlbGVjdGlvbi1mZCIsIjMiLCItLWNvbmZpZy1mZCIsIjQiLCItLWZvcm1hbC1yb290IiwiOWRkMmZiOGI2M2NjZDZhMzE5M2VlYzdhYjY1ODRjYzI0YTY4YTRhNSIsIi0tY2hpbGQtZ2l0bGluayIsIjkzYTg5YmE2MTMwNmQ4NDBhMDA4ODEzZjYyZjI2YTM0ZDU0ODUwZjQiLCItLXNlbGVjdGlvbi1yYXctc2hhMjU2IiwiOGZlNDU4NWYzNjZjYjY5YWQ5MTgxZTMwYzI1YjVmNGU5OTA0MGM4M2Q4ZmZlNjY0MjY4OTdiZmE5ZDMzMWVkZCIsIi0tY29uZmlnLXJhdy1zaGEyNTYiLCI0M2IzYjc3YjU5MzQxMDdjNTRiOGJlZTE1N2I0NmQwN2NiMTdiODVjYTg5MzA1YWQ2ZmI3NDA1MjM3ZTQyZDFkIiwiLS1jd2QiLCIvZGlzay9ybC9wc21fd21hLy5hdXRob3JpdHktcm9vdC1tYXRlcmlhbGl6YXRpb24tOWRkMmZiOCIsIi0tcmVtb3RlIiwiaHR0cHM6Ly9naXRodWIuY29tL3d4d3kvcHNtX3dtYS5naXQiLCItLWluZGV4IiwiL2Rpc2svcmwvcHNtX3dtYS8uYXV0aG9yaXR5LXJvb3QtbWF0ZXJpYWxpemF0aW9uLTlkZDJmYjgvLmF1dGhvcml0eS1yb290LmluZGV4IiwiLS1ldmlkZW5jZS1wYXRoIiwiL2Rpc2svcmwvcHNtX3dtYS9hcnRpZmFjdHMvZzAvcjA5L2F1dGhvcml0eV9yb290X21hdGVyaWFsaXphdGlvbl9ldmlkZW5jZV92MS5qc29uIiwiLS1naXQiLCIvdXNyL2Jpbi9naXQiLCItLWdpdC1yYXctc2hhMjU2IiwiNTg3ZWYyMTg2OGM5NDhiODgzOTkzZTIzMjA5Yjg2YTcyYTZkZGMwNmFhYjE1NDVjNjk3ZmZjMzEwNzVhY2Q0YSIsIi0tZ2l0LXZlcnNpb24iLCJnaXQgdmVyc2lvbiAyLjM0LjEiLCItLWludGVycHJldGVyIiwiL29wdC9jb25kYS9iaW4vcHl0aG9uMyIsIi0taW50ZXJwcmV0ZXItcmF3LXNoYTI1NiIsImYzZTNmNTYxYjQ3Mzk3NmJlNTVkOTM3NjE2OTE1ZDZjNTA3ZGVkY2IzOTUwYzNjYTcyZGY3ODZiMjhlOGVmZGMiLCItLWludGVycHJldGVyLXZlcnNpb24iLCJQeXRob24gMy4xMS45IiwiLS1ib290c3RyYXAtY29udHJhY3QtZmQiLCI1IiwiLS1ib290c3RyYXAtcHJvamVjdC1yb290IiwiL2Rpc2svcmwvcHNtX3dtYS8uYXV0aG9yaXR5LXJvb3QtbWF0ZXJpYWxpemF0aW9uLTlkZDJmYjgiLCItLWJvb3RzdHJhcC1tb2R1bGUiLCJ0b29scy5wc21fd21hLm1hdGVyaWFsaXplX2ltbXV0YWJsZV9zb3VyY2VfYXV0aG9yaXR5X3Jvb3QiLCItLWFkYXB0ZXItcGF0aCIsInRvb2xzL3BzbV93bWEvbWF0ZXJpYWxpemVfaW1tdXRhYmxlX3NvdXJjZV9hdXRob3JpdHlfcm9vdC5weSIsIi0tYWRhcHRlci1ibG9iLW9pZCIsImRhNzgyNzU0YjhlOGVmYTBmM2NhZTk3M2FhNjg2MDJkY2RhMWMyMzciLCItLWFkYXB0ZXItcmF3LXNoYTI1NiIsIjA5MWVhNjJkMGE4YjQ4NDI5YzY3MTAwYzEzOTVlNjJhMzAwZGM0N2E4ZDhmNjVjNzA0NmJhMDBmODIwNWI1ZTkiLCItLWF1dGhvcml0eS1tb2R1bGUtcGF0aCIsInRvb2xzL3BzbV93bWEvaW1tdXRhYmxlX3NvdXJjZV9hdXRob3JpdHlfcm9vdC5weSIsIi0tYXV0aG9yaXR5LW1vZHVsZS1ibG9iLW9pZCIsIjk5MzdmNzRjNDliMTRkNDg5ODIzYzczMWFhMjg1NmIwMGMxYTNkMDYiLCItLWF1dGhvcml0eS1tb2R1bGUtcmF3LXNoYTI1NiIsIjRlYmY5ZmI4YjA2MDViYzMwYzQ1ODAwYmRmYTdkMzY3NDQ0ZmY5N2RhZWU2OTkyNmViYTlhYTVjOTgxN2Y1ZDAiLCItLWNvbGxlY3Rpb24tbW9kdWxlLXBhdGgiLCJ0b29scy9wc21fd21hL2ltbXV0YWJsZV9zb3VyY2VfY29sbGVjdGlvbi5weSIsIi0tLWNvbGxlY3Rpb24tbW9kdWxlLWJsb2Itb2lkIiwiZWVmZGU0ZTViNWEwOTY1YmJkY2FhNTMzOTBiOTI4NmE0Yzc3ZjI2NjUiLCItLWNvbGxlY3Rpb24tbW9kdWxlLWJsb2ItcmF3LXNoYTI1NiIsIjFiMzM1M2IyMGJkMTM0MmYxNjg1MDYyZjk2MmE3Y2JjMWJhMGRiZjY5OWJkYzcyYzA5OWNhNDcwY2IwOWNjMzQwIiwiLS1hdWRpdC1tb2R1bGUtcGF0aCIsInRvb2xzL2cwL2F1ZGl0X3IwOV9iX3R0dF9yb290X2dpdGxpbmtfYXV0aG9yaXR5LnB5IiwiLS1hdWRpdC1tb2R1bGUtYmxvYi1vaWQiLCJkMDAyMGYwNjdiYWRmZTU5MTE1MmZhZmE2MzM2ZTIwYjQ4NWViNWJhIiwiLS1hdWRpdC1tb2R1bGUtcmF3LXNoYTI1NiIsIjNkYjYzNzZiMzUxNDFkOGNhNWRjNzJjMWJiMzgzNTk5NDM5NjFkYjkyNTQ1YTg4ZjMyMDYwMzEyMWRiNGMzOWUiLCItLWF1dGhvci1uYW1lIiwid3h3eSIsIi0tYXV0aG9yLWVtYWlsIiwiMTAzNjY0ODU4MUBxcS5jb20iLCItLWF1dGhvci1kYXRlIiwiMjAyNi0wOS0xMlQyMzowNzo0MyswODowMCIsIi0tY29tbWl0dGVyLW5hbWUiLCJ3eHd5IiwiLS1jb21taXR0ZXItZW1haWwiLCIxMDM2NjQ4NTgxQHFxLmNvbSIsIi0tY29tbWl0dGVyLWRhdGUiLCIyMDI2LTA5LTEyVDIzOjA3OjQzKzA4OjAwIiwiLS1jb21taXQtbWVzc2FnZSIsImNob3JlOiBtYXRlcmlhbGl6ZSBpbW11dGFibGUgc291cmNlIGF1dGhvcml0eSByb290Il0="),
)
# Reconstruct the third value from its exact compact JSON lexical form.  The
# preceding base64 copy remains inert and is overwritten so a single-character
# transcription error cannot become runtime authority.
RAW = RAW[:2] + (b'''["--selection-fd","3","--config-fd","4","--formal-root","9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5","--child-gitlink","93a89ba61306d840a008813f62f26a34d54850f4","--selection-raw-sha256","8fe4585f366cb69ad9181e30c25b5f4e99040c83d8ffe66426897bfa9d331edd","--config-raw-sha256","43b3b77b5934107c54b8bee157b46d07cb17b85ca89305ad6fb7405237e42d1d","--cwd","/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8","--remote","https://github.com/wxwy/psm_wma.git","--index","/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8/.authority-root.index","--evidence-path","/disk/rl/psm_wma/artifacts/g0/r09/authority_root_materialization_evidence_v1.json","--git","/usr/bin/git","--git-raw-sha256","587ef21868c948b883993e23209b86a72a6ddc06aab1545c697ffc31075acd4a","--git-version","git version 2.34.1","--interpreter","/opt/conda/bin/python3","--interpreter-raw-sha256","f3e3f561b473976be55d937616915d6c507dedcb3950c3ca72df786b28e8efdc","--interpreter-version","Python 3.11.9","--bootstrap-contract-fd","5","--bootstrap-project-root","/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8","--bootstrap-module","tools.psm_wma.materialize_immutable_source_authority_root","--adapter-path","tools/psm_wma/materialize_immutable_source_authority_root.py","--adapter-blob-oid","da782754b8e8efa0f3cae973aa68602dcda1c237","--adapter-raw-sha256","091ea62d0a8b48429c67100c1395e62a300dc47a8d8f65c7046ba00f8205b5e9","--authority-module-path","tools/psm_wma/immutable_source_authority_root.py","--authority-module-blob-oid","9937f74c49b14d489823c731aa2856b00c1a3d06","--authority-module-raw-sha256","4ebf9fb8b0605bc30c45800bdfa7d367444ff97daee69926eba9aa5c9817f5d0","--collection-module-path","tools/psm_wma/immutable_source_collection.py","--collection-module-blob-oid","eefde4e5b5a0965bbdcaa5390b9286a4c77f2665","--collection-module-raw-sha256","1b3353b0bd1342f1685062f962a7cbc1ba0dbf699bdc72c099ca470cb09cc340","--audit-module-path","tools/g0/audit_r09_b_ttt_root_gitlink_authority.py","--audit-module-blob-oid","d0020f067badfe591152fafa6336e20b485eb5ba","--audit-module-raw-sha256","3db6376b35141d8ca5dc72c1bb38359943961db92545a88f320603121db4c39e","--author-name","wxwy","--author-email","1036648581@qq.com","--author-date","2026-09-12T23:07:43+08:00","--committer-name","wxwy","--committer-email","1036648581@qq.com","--committer-date","2026-09-12T23:07:43+08:00","--commit-message","chore: materialize immutable source authority root"]''',)
EXPECTED = ((".authority-root.selection.json", 3, "8fe4585f366cb69ad9181e30c25b5f4e99040c83d8ffe66426897bfa9d331edd"),
            (".authority-root.config.json", 4, "43b3b77b5934107c54b8bee157b46d07cb17b85ca89305ad6fb7405237e42d1d"),
            (".authority-root.bootstrap-contract.json", 5, "62a7bbf5fcb609e52931639001e6db01df81f0de2a33afd41c0080eb8e903f68"))

class Stop(RuntimeError): pass
def fail(reason): raise Stop(reason)
def digest(raw): return hashlib.sha256(raw).hexdigest()
def ident(value): return (value.st_dev, value.st_ino, value.st_size)
def nofollow(path, flags=os.O_RDONLY):
    fd = os.open(path, flags | os.O_NOFOLLOW | os.O_CLOEXEC)
    value = os.fstat(fd)
    if not stat.S_ISREG(value.st_mode): os.close(fd); fail("non-regular authority")
    return fd, value, os.pread(fd, value.st_size, 0)

def route_snapshot():
    g = os.lstat(GIT)
    if stat.S_ISLNK(g.st_mode) or not stat.S_ISREG(g.st_mode) or digest(open(GIT, "rb").read()) != "587ef21868c948b883993e23209b86a72a6ddc06aab1545c697ffc31075acd4a": fail("git identity")
    admin = ROOT + "/.git"; value = os.lstat(admin)
    if stat.S_ISLNK(value.st_mode) or not stat.S_ISDIR(value.st_mode): fail("linked parent route unsupported")
    adfd = os.open(admin, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC); ads = os.fstat(adfd)
    cfd, cs, raw = nofollow(admin + "/config")
    if os.path.lexists(admin + "/config.worktree"): fail("config.worktree")
    allowed = {"core.repositoryformatversion":"0", "core.bare":"false", "extensions.worktreeconfig":"false", "core.worktree":ROOT}
    bools = {"core.filemode", "core.logallrefupdates"}; section = None; seen = set()
    for line in raw.decode("utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith(("#", ";")): continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip().lower()
            if not section or '"' in section or "." in section: fail("config section")
            continue
        if section is None or "=" not in line: fail("config grammar")
        key, value = (item.strip() for item in line.split("=", 1)); key = section + "." + key.lower()
        if key in seen or (key not in allowed and key not in bools): fail("config allowlist")
        seen.add(key)
        if (key in allowed and value != allowed[key]) or (key in bools and value not in ("true", "false")): fail("config value")
    return (admin, adfd, ads, cfd, cs, raw)

def check_route(s):
    admin, adfd, ads, cfd, cs, raw = s; a = os.lstat(admin); af = os.fstat(adfd); c = os.lstat(admin + "/config"); cf = os.fstat(cfd)
    if (stat.S_ISLNK(a.st_mode) or not stat.S_ISDIR(a.st_mode) or (a.st_dev,a.st_ino)!=(ads.st_dev,ads.st_ino) or (af.st_dev,af.st_ino)!=(ads.st_dev,ads.st_ino) or stat.S_ISLNK(c.st_mode) or not stat.S_ISREG(c.st_mode) or ident(c)!=ident(cs) or ident(cf)!=ident(cs) or os.pread(cfd,cs.st_size,0)!=raw or os.path.lexists(admin + "/config.worktree")): fail("route drift")

def run(s, *argv, cwd=ROOT):
    check_route(s); p = subprocess.run([*PREFIX, "-C", cwd, *argv], env=ENV, stdout=subprocess.PIPE, stderr=subprocess.PIPE); check_route(s)
    if p.returncode: fail("native git")
    return p.stdout

def boot(s):
    path, oid = ADAPTER; row = run(s, "ls-tree", FORMAL, "--", path).decode().strip().split("\t", 1)
    if len(row) != 2 or row[0].split() != ["100644", "blob", oid] or row[1] != path: fail("adapter tree")
    source = run(s, "cat-file", "blob", oid).decode(); tree = ast.parse(source); node = next((x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=="bootstrap_payload"),None)
    if node is None or not isinstance(node.body[-1],ast.Return): fail("bootstrap AST")
    value=node.body[-1].value; raw=(value.value if isinstance(value,ast.Constant) else "".join(x.value for x in value.elts)).encode()
    if len(raw)!=7538 or digest(raw)!="7e1c0ecc2161984a88ea0d0eae82f9f7ced709ca919f0302f74a3a068e08c9b8": fail("bootstrap identity")
    return raw.decode()

def absent(path):
    if os.path.lexists(path): fail("fresh path")
def assert_worktree(s, owned):
    value=os.lstat(CLEAN)
    if not stat.S_ISDIR(value.st_mode) or (value.st_dev,value.st_ino)!=(owned.st_dev,owned.st_ino): fail("clean-root ownership")
    if run(s,"-C",CLEAN,"rev-parse","HEAD").decode().strip()!=FORMAL or run(s,"-C",CLEAN,"status","--porcelain","--untracked-files=no","--ignore-submodules=all"): fail("worktree postcondition")
    rows=run(s,"worktree","list","--porcelain").decode().splitlines()
    if "worktree "+CLEAN not in rows: fail("worktree listing")

def cleanup(s, owned, paths):
    try:
        assert_worktree(s, owned); run(s,"worktree","remove","--force",CLEAN)
        if any(os.path.lexists(x) for x in paths): fail("cleanup residue")
        if ("worktree "+CLEAN) in run(s,"worktree","list","--porcelain").decode().splitlines(): fail("cleanup listing")
    except BaseException as error:
        raise Stop("ROLLBACK_INCOMPLETE") from error

def handoff(raw, name, target, expected):
    path=CLEAN+"/"+name; w=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
    try:
        offset=0
        while offset<len(raw):
            written=os.write(w,raw[offset:])
            if written<=0: fail("writer short write")
            offset+=written
        os.fsync(w); ws=os.fstat(w)
    finally: os.close(w)
    rd, rs, got=nofollow(path)
    if digest(got)!=expected or ident(rs)!=ident(ws): os.close(rd); fail("reader identity")
    if rd!=target: os.dup2(rd,target); os.close(rd)
    ts=os.fstat(target)
    if ident(ts)!=ident(rs) or digest(os.pread(target,ts.st_size,0))!=expected: fail("target identity")
    os.lseek(target,0,os.SEEK_SET); os.set_inheritable(target,True)

def main():
    if len(RAW[0])!=516 or len(RAW[1])!=508 or len(RAW[2])!=2427 or tuple(digest(x) for x in RAW)!=EXPECTED[0][2:]+EXPECTED[1][2:]+("72777bd7305c760c48c069eafd068f1a538383a6fdb8d40258acf3d8fc3b7ae2",): fail("embedded authority")
    s=route_snapshot(); paths=(CLEAN,CLEAN+"/.authority-root.index",ROOT+"/artifacts/g0/r09/authority_root_materialization_evidence_v1.json",ROOT+"/artifacts/g0/r09/authority_root_materialization_evidence_v1.json.pending")
    try:
        for path in paths: absent(path)
        actual=json.loads(RAW[2]); b=boot(s); contract=json.dumps({"bootstrap_argv_sha256":digest(json.dumps(["--",*actual],separators=(",",":"),ensure_ascii=False).encode()),"bootstrap_raw_sha256":digest(b.encode())},sort_keys=True,separators=(",",":")).encode(); data=(RAW[0],RAW[1],contract)
        if tuple(digest(x) for x in data)!=tuple(x[2] for x in EXPECTED): fail("contract identity")
        run(s,"worktree","add","--detach",CLEAN,FORMAL); owned=os.lstat(CLEAN); assert_worktree(s,owned)
        for raw,(name,target,expected) in zip(data,EXPECTED): handoff(raw,name,target,expected)
        keep={3,4,5}
        for entry in os.listdir("/proc/self/fd"):
            fd=int(entry)
            if fd not in keep:
                try: os.close(fd)
                except OSError: pass
        if {int(x) for x in os.listdir("/proc/self/fd")} != keep: fail("fd closure")
        os.execve(PYTHON,[PYTHON,"-I","-S","-B","-c",b,"--",*actual],ENV)
    except BaseException:
        if 'owned' in locals(): cleanup(s,owned,paths)
        raise

if __name__ == "__main__": main()
