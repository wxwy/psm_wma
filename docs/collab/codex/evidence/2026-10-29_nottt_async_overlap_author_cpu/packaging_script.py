from pathlib import Path
import hashlib,json,shutil,subprocess,ast
BASE=Path('/tmp/psm-nottt-async-overlap-20261029')
ROOT=Path('/workspace/psm-wma-nottt-async'); CHILD=ROOT/'cosmos-framework'
FR='e0fe911dfb9fd34957234828195cf051713f6c3d'; FC='f6a92d47b6dac7998ddc58b3da26ef93f8068dc7'
BR='3d5806a2b702b42d3f24e7645aa7cec9cd70b0c7'; BC='746c5cf2f2324104a62fb71510343aa40d3976c5'
OUT=BASE/'publication'
def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args])
def put(name,value):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2)+'\n')
def copy_files(source,target):
 if not source.exists():return
 for path in sorted(source.iterdir()):
  if path.is_file() and path.suffix in ('.json','.xml','.log','.md','.py'):
   dest=OUT/target/path.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
gate=json.loads((BASE/'locked03/gate.json').read_text())
assert gate['status']=='PASS' and gate['identities']=={'root':FR,'child':FC,'gitlink':FC}
assert gate['source_unchanged'] is True
assert not OUT.exists()
OUT.mkdir()
copy_files(BASE/'locked03','final');copy_files(BASE/'locked03/timelines','final/timelines')
copy_files(BASE/'locked02','history/locked02_failed_legacy_fixtures');copy_files(BASE/'locked02/timelines','history/locked02_failed_legacy_fixtures/timelines')
copy_files(BASE/'locked01','history/locked01_failed_fixture');copy_files(BASE/'locked01/timelines','history/locked01_failed_fixture/timelines')
for name in ('loader01','negatives02','focused03','focused04','trainer01','trainer02','fixture05','fixture06','fixture07'):
 copy_files(BASE/name,'preliminary/'+name)
for n in range(1,5):
 for suffix in ('xml','log'):
  p=Path(f'/tmp/psm-nottt-async-recipe-test{n:02d}.{suffix}')
  if p.is_file():
   d=OUT/'preliminary/recipe'/p.name;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,d)
copy_files(BASE/'protected_audit_release','protected')
for repo,a,b,name in ((ROOT,BR,FR,'root_increment'),(CHILD,BC,FC,'child_increment')):
 (OUT/(name+'.diff')).write_bytes(git(repo,'diff','--binary',a,b))
 (OUT/(name+'_files.txt')).write_bytes(git(repo,'diff','--name-status',a,b))
watched=json.loads((BASE/'locked03/source_sha256.json').read_text())
bindings=[]
for name,expected in watched.items():
 is_child=name.startswith('cosmos-framework/')
 repo=CHILD if is_child else ROOT;ref=FC if is_child else FR;path=name.removeprefix('cosmos-framework/') if is_child else name
 data=git(repo,'show',f'{ref}:{path}'); digest=hashlib.sha256(data).hexdigest();assert digest==expected
 bindings.append(dict(repository='child' if is_child else 'root',formal_sha=ref,path=path,git_blob=git(repo,'rev-parse',f'{ref}:{path}').decode().strip(),sha256=digest))
put('formal_source_bindings.json',bindings)
put('formal_pair.json',dict(root=FR,child=FC,gitlink=FC,baseline_root=BR,baseline_child=BC,branch='v3-nottt-async-overlap-20261029'))
put('STATUS.json',dict(author_cpu=gate['status'],totals=gate['totals'],formal_root=FR,child_gitlink=FC,code_gate='REQUESTED_NOT_APPROVED',ds_cpu='NOT_RUN',real_gpu='NOT_RUN',real_dcp_resume='NOT_RUN',active_job='UNTOUCHED',canonical_merge='NOT_PERFORMED'))
(OUT/'README.md').write_text('''# Author CPU evidence — Issue #9\n\nFinal exact Pair is in formal_pair.json; final/gate.json + raw JUnit/logs are authoritative for author CPU only. Native GPU overlap/performance and real DCP Resume are NOT executed.\n\n`history/locked01_failed_fixture` is the initial 66986d5f / 5124a2b7 Pair: 55 passed / 1 failed, stopped before regression. The new per-GA fixture assertion incorrectly selected initial frontier instead of pending lazy-Restore frontier; no production checkpoint change was needed. The correction preserves all frontier assertions. Additional final changes freeze resolved roots and report comparable fake-compute wall intervals. This RED is never relabeled as GREEN.\n\n`history/locked02_failed_legacy_fixtures` binds e8c49c07 / d64e5c1d: new async72PASS; regression122PASS/1FAIL/1SKIP before stop. Existing namespace config fixture used unsupported SimpleNamespace plus missing receipt, and another strict semantic test targeted the Owner-exempt historical Job. New fixtures use supported structured records/receipt and an ordinary strict Job with all prior assertions retained. Exactly one forbidden real-data debug node is explicitly deselected by the final synthetic-only gate; its source is preserved and it is not counted as PASS.

`preliminary/` contains separate exploratory passes and available setup failures; their sums are not added to final totals, and their sources were not all identical to the final Pair. Initial recipe pytest invocation needed disabling repository addopts in the isolated CPU environment.\n\nTimeline uses actual worker-owned CPU Source/Transform and a CPU-only hash-compute callback, not CUDA. It proves overlap and no early commit, not GPU acceleration. Three-Window timing includes spawn cold start; asynchronous total wall can exceed the serial control. The unchanged old RAW backend has an expected RED target witness.\n\nTemporary checkpoint/cache containers, pytest basetemp trees and model-like fixtures are not published. Only whitelisted logs, JSON, JUnit, diffs, static audit and source bindings are copied. Protected audit is internal author review, not GPT or independent DS.\n''')
copy_files(BASE/'bounds_probe','bounds')
if (BASE/'cpu_bounds_probe.py').is_file():shutil.copyfile(BASE/'cpu_bounds_probe.py',OUT/'bounds_probe.py')
manifest={str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.rglob('*')) if p.is_file()}
put('artifact_sha256.json',manifest)
print(json.dumps(dict(output=str(OUT),artifacts=len(manifest),source_bindings=len(bindings),totals=gate['totals'])))
