"""Package synthetic author evidence; never copy test datasets or cache trees."""

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path('/workspace/psm-wma-nottt-coldstart')
CHILD = ROOT / 'cosmos-framework'
TASK = Path('/tmp/psm-nottt-coldstart-20261030')
OUT = ROOT / 'docs/collab/codex/evidence/2026-10-30_nottt_issue12_worker_coldstart_author_cpu'
FORMAL_ROOT = 'fd9021b0908b4b2763b3d02508b1f34df377dc97'
FORMAL_CHILD = '224c5f3c0bd6911bb49cb6bb0895ba7da53ff822'
BASE_ROOT = '2260f2a6f89368301ba50a686676994af90a2ca5'
BASE_CHILD = 'f6a92d47b6dac7998ddc58b3da26ef93f8068dc7'

def git(where, *args):
    return subprocess.check_output(['git', '-C', str(where), *args])

def save(name, value):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')

def copy(src, dst):
    path = OUT / dst
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, path)

gate = json.loads((TASK / 'final01/gate.json').read_text())
assert gate['status'] == 'PASS' and gate['totals'] == dict(tests=58, failures=0, errors=0, skipped=0)
assert gate['source_unchanged'] is True
assert gate['identities'] == dict(root=FORMAL_ROOT, child=FORMAL_CHILD, gitlink=FORMAL_CHILD)
OUT.mkdir(parents=True, exist_ok=False)
for file in (TASK / 'final01').iterdir():
    if file.is_file():
        copy(file, 'final/' + file.name)
for file in (TASK / 'final01/timelines').glob('*.json'):
    copy(file, 'final/timelines/' + file.name)
for file in (TASK / 'final01/async_tmp').rglob('*_witness.json'):
    copy(file, 'witnesses/' + file.name)
for file in (TASK / 'final01/regression_tmp').rglob('worker_*.json'):
    copy(file, 'witnesses/cleanup/' + file.name)
for attempt in ('exploratory01', 'exploratory02', 'exploratory03', 'focused04', 'focused05', 'focused06'):
    for file in (TASK / attempt).glob('*'):
        if file.is_file():
            copy(file, 'history/' + attempt + '/' + file.name)
for src, dst in (
    ('run_gate.py', 'run_gate.py'), ('audit.py', 'protected/audit.py'),
    ('protected/audit.json', 'protected/audit.json'), ('audit_console.log', 'protected/console.log'),
    ('trainer_collection.log', 'history/trainer_collection.log'), ('package.py', 'packaging_script.py')
):
    copy(TASK / src, dst)
for where, baseline, formal, label in ((ROOT, BASE_ROOT, FORMAL_ROOT, 'root'), (CHILD, BASE_CHILD, FORMAL_CHILD, 'child')):
    (OUT / f'{label}.diff').write_bytes(git(where, 'diff', '--binary', baseline, formal))
    (OUT / f'{label}_changed_files.txt').write_bytes(git(where, 'diff', '--name-status', baseline, formal))
save('formal_pair.json', dict(formal_root=FORMAL_ROOT, child=FORMAL_CHILD, gitlink=FORMAL_CHILD,
    baseline_root=BASE_ROOT, baseline_child=BASE_CHILD,
    approved_previous_implementation_root='e0fe911dfb9fd34957234828195cf051713f6c3d',
    branch='v3-nottt-lerobot-coldstart-20261030',
    latest_directive_root='9344198a5abf4964a4997bf7e9268b8e5ccc73e8',
    author_cpu_only=True, canonical_merge=False, gpu_run=False, real_data_run=False, real_dcp_run=False))
watched = json.loads((TASK / 'final01/source_sha256.json').read_text())
protected = json.loads((TASK / 'protected/audit.json').read_text())['unchanged_blob_bindings']
paths = set(watched) | {'cosmos-framework/' + name for name in protected}
bindings = {}
for name in sorted(paths):
    child = name.startswith('cosmos-framework/')
    relative = name.removeprefix('cosmos-framework/') if child else name
    where, sha = (CHILD, FORMAL_CHILD) if child else (ROOT, FORMAL_ROOT)
    blob = git(where, 'rev-parse', f'{sha}:{relative}').decode().strip()
    raw = git(where, 'show', f'{sha}:{relative}')
    bindings[name] = dict(commit=sha, git_blob=blob, sha256=hashlib.sha256(raw).hexdigest())
save('formal_source_bindings.json', bindings)
save('STATUS.json', dict(status='AUTHOR_TARGETED_SYNTHETIC_CPU_PASS', formal_root=FORMAL_ROOT,
    child=FORMAL_CHILD, gitlink=FORMAL_CHILD, tests=58, failures=0, errors=0, skipped=0,
    groups={'source_recipe':47, 'selected_regression':11}, old_301_rerun=False,
    ruff='0.12.7', static_files=4, source_unchanged=True, new_code_review='REQUESTED_NOT_YET_VERDICT',
    ds_new_cpu='NOT_RUN', real_first_packet_under_120s='NOT_MEASURED',
    gpu_performance='NOT_RUN_FOR_NEW_PAIR', real_dcp_resume='NOT_RUN_FOR_NEW_PAIR',
    running_formal_job='NOT_ACCESSED_OR_MODIFIED', source_timeout_changed=False,
    old_issue12_gpu_failure='UNCHANGED: B first materialize120s timeout / zero commits / performance inconclusive'))
save('commands.json', dict(outer_command=[
    '/workspace/.venvs/psm-wma-cpu/bin/python', str(TASK / 'run_gate.py'), '--root-worktree', str(ROOT),
    '--expected-root', FORMAL_ROOT, '--expected-child', FORMAL_CHILD, '--evidence-dir', str(TASK / 'final01')],
    actual_subcommands=gate['steps']))
(OUT / 'README.md').write_text('''# Issue12 narrow worker cold-start author evidence

Formal Root `fd9021b0908b4b2763b3d02508b1f34df377dc97`, Child/Gitlink
`224c5f3c0bd6911bb49cb6bb0895ba7da53ff822`. Isolated candidate only.

`final/gate.json` binds the exact clean source; `async.xml` 47 and
`regression.xml` 11 unique PASS cases, no failure/error/skip. Combined58.
Ruff0.12.7 check/format/AST4 and import origin pass. These are author synthetic
CPU results, not GPT/DS execution or a full repository gate. Old CPU301 not rerun.
`run_gate.py` is the frozen standalone author replay helper, adapted from the
prior exact-pair runner; no new production launcher. It requires a NEW external
evidence directory and the exact clean Formal checkout, not this evidence HEAD.
The helper itself and all published artifacts are hash-bound.

`witnesses/` reports actual small synthetic source build/read and owned spawn PID,
not the DS real source. `final/timelines/` reuses the unchanged synthetic loader
overlap oracle. Do not compare these milliseconds to the DS193s real cold start
or claim real GPU acceleration/first-packet success. GPU/native DCP tests NOT RUN.
RAM retained Arrow cap is an extra independent worker cache, not RSS prediction.

`protected/` is a read-only internal AUTHOR Git/AST audit: only two production
files change; 12 protected blobs and all10 original recipe-test definitions are
unchanged. Check root.diff and child.diff for the complete formal deltas.

History is retained and excluded from the final PASS count: exploratory01 pytest
dependency-hook collection error; exploratory02 9PASS/1FAIL new regex expected
the wrong guard (original strict SourceReader rejected correctly); exploratory03
46PASS before the final spawn integration; focused04 rejected the new test's
B1/GA2 fixture by the unchanged B8/GA4 guard; focused05 the new recipe proxy
omitted rate/caption/token fields; focused06 1PASS after fixing only the fixture.
No original assertions or native-profile checks were relaxed.

Raw warnings are retained: pynvml deprecation, CPU affinity advisory for nw8,
and resource_tracker cleanup of two registered semaphores after worker shutdown.
Tests explicitly verify owned worker PIDs are reaped and foreign processes
survive. This does not claim a broad native resource qualification.

No test datasets, cache trees, .pt payloads, credentials, or production assets
are copied into this package. Canonical V3/Child, formal training, DCP, Config,
Job identity, old evidence and the separate EvalV2 line were not updated.
''')
hashes = {str(path.relative_to(OUT)): hashlib.sha256(path.read_bytes()).hexdigest()
          for path in sorted(OUT.rglob('*')) if path.is_file()}
save('artifact_sha256.json', hashes)
print(json.dumps(dict(output=str(OUT), artifacts=len(hashes), bindings=len(bindings), status='PACKAGED')))
