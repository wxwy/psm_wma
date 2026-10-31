"""Package only small synthetic Issue13 evidence and exact source bindings."""

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

root=Path('/workspace/psm-wma-nottt-console')
task=Path('/tmp/psm-nottt-console-20261031')
out=root/'docs/collab/codex/evidence/2026-10-31_nottt_issue13_progress_console_author_cpu'
formal='24dbb677f7a60eeab6934c44352c7e00fa6d9b36'
child='0ae313e329d290fc6b8a50fda1112820fb7ac485'
base='3332d1825de8778e3d6dbb7e9ba98cbffff487c6'
gate=json.loads((task/'final/gate.json').read_text())
assert gate['status']=='PASS' and gate['source_unchanged']
assert gate['totals']==dict(tests=49,failures=0,errors=0,skipped=0)
assert gate['identities']==dict(root=formal,child=child,gitlink=child)
out.mkdir(parents=True,exist_ok=False)

def copy(source,target):
    path=out/target
    path.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,path)

def save(name,value):
    (out/name).write_text(json.dumps(value,indent=2)+'\n')

def git(*words):
    return subprocess.check_output(['git','-C',str(root),*words])

for name in ('final','first','exploratory02'):
    for file in (task/name).iterdir():
        if file.is_file():
            copy(file,('final/' if name=='final' else 'history/'+name+'/')+file.name)
for name in ('exit0','exit7'):
    for file in (task/'demos'/name).iterdir():
        if file.is_file():
            copy(file,'examples/'+name+'/'+file.name)
for source,target in (('audit.py','audit.py'),('audit.json','audit.json'),('audit.log','audit.log'),
                      ('run_gate.py','run_gate.py'),('demo.py','raw_demo.py'),('package.py','packaging_script.py')):
    copy(task/source,target)
(out/'root.diff').write_bytes(git('diff','--binary',base,formal))
(out/'changed_files.txt').write_bytes(git('diff','--name-status',base,formal))
hashes=json.loads((task/'final/source_sha256.json').read_text())
bindings={}
for name,sha256 in hashes.items():
    blob=git('rev-parse',f'{formal}:{name}').decode().strip()
    raw=git('show',f'{formal}:{name}')
    assert hashlib.sha256(raw).hexdigest()==sha256
    bindings[name]=dict(commit=formal,git_blob=blob,sha256=sha256)
save('formal_source_bindings.json',bindings)
save('formal_pair.json',dict(formal_root=formal,child=child,gitlink=child,baseline_root=base,
     branch='v3-nottt-progress-console-20261031',child_changed=False,scope='Root NoTTT output only'))
save('STATUS.json',dict(status='AUTHOR_SHELL_SYNTHETIC_CPU_PASS',formal_root=formal,child=child,
     tests=49,failures=0,errors=0,skipped=0,new_cases=21,existing_launcher_cases=28,
     raw_examples=2,raw_examples_are_additional_test_counts=False,
     bash_syntax_scripts=2,shellcheck_version='0.10.0',ruff_version='0.12.7',python_static_files=4,
     source_unchanged=True,child_changed=False,existing_assertions_retained=46,
     old_cpu58_301_rerun=False,gpu=False,real_training=False,real_dcp=False,
     C12200_AB_accessed_or_changed=False,canonical_promotion=False,GPT_code_verdict='REQUESTED'))
save('commands.json',dict(outer=[
 '/workspace/.venvs/psm-wma-cpu/bin/python',str(task/'run_gate.py'),'--root',str(root),
 '--expected-root',formal,'--expected-child',child,'--shellcheck',str(task/'tools/bin/shellcheck'),
 '--evidence',str(task/'final')],subcommands=gate['steps']))
(out/'README.md').write_text('''# Issue13 author synthetic shell evidence

Formal Root `24dbb677f7a60eeab6934c44352c7e00fa6d9b36`; unchanged Child/Gitlink
`0ae313e329d290fc6b8a50fda1112820fb7ac485`. Baseline3332d182. Isolated only.

`final/gate.json` / `final/junit.xml` / `final/pytest.log`: final clean exact-SHA
49 unique PASS (21 new +28 selected old launcher cases), zero fail/error/skip,
source unchanged. Two individual Bash syntax commands, ShellCheck0.10.0,
Ruff0.12.7 check+format and AST4. Original command argv/env tests use fake Python;
none executes real torchrun or model/data/Checkpoint/CUDA. Old CPU58/301 not run.
Child and the entire training/Checkpoint/Loader/Journal code are unchanged.

`examples/exit0` and `examples/exit7` contain ACTUALLY captured stdout, stderr,
raw full_launch.log, fake source and command/status. They are tiny additional
raw demonstrations, not added to the49 unittest count. Exit0 console shows one
startup path and only progress; exit7 additionally shows explicit failure/tail.
Never call these real training/model logs.

`audit.json` is AUTHOR Git/AST evidence: only3 Root production files; every
original shell training-command character/admission/export/cwd block preserved;
all46 old test assertions retained. Process scans only in shutdown cleanup,
stdlib helper imports, no Torch/device import or per-step instrumentation.
This is not independent GPT/DS execution or native GPU performance acceptance.

`history/first` contains the earlier17 PASS, `history/exploratory02` the precommit
49 PASS. These are not additional final tests and are not relabeled clean-Pair
runs. No test failures occurred. Tool setup used isolated /tmp shellcheck-py
0.10.0.1 (binary0.10.0); pip was unavailable, uv installed it outside the repo.

`run_gate.py` is the standalone source-frozen author replay helper (stdlib,
existing pytest/Ruff plus ShellCheck). Export it OUTSIDE a clean Formal checkout
before invoking; the later Evidence commit is not Formal Root. Use a new external
evidence directory. Original commands and safe-only env overrides are recorded.
Raw diffs are byte-exact; whitespace in their context-empty lines is intentional.
No private credentials, cache trees or training assets are packaged.

Post-publication STOP for GPT incremental Code Gate. No canonical merge, DS
dispatch, current C12200 A/B change, GPU/real training/DCP or benchmark replay.
''')
manifest={str(path.relative_to(out)):hashlib.sha256(path.read_bytes()).hexdigest()
          for path in sorted(out.rglob('*')) if path.is_file()}
save('artifact_sha256.json',manifest)
print(json.dumps(dict(status='PACKAGED',files=len(manifest),source_bindings=len(bindings))))
