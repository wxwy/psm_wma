import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

root=Path('/workspace/psm-wma-g2-gateb-fix')
base=Path('/tmp/psm-g2-gateb-replay-20261104')
out=root/'docs/collab/codex/evidence/2026-11-04_g2_gateb_replay_author_cpu'
formal='a9ffd313770c5344195f415425124a5075e62b2b'
child='1069fe78841228cadbbfbe6afbd767eaed6225da'
parent='992cfc2adb3150c573d19206e176bd8a52574949'
def git(*args):return subprocess.check_output(['git',*args],cwd=root,text=True).strip()
def dump(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
assert git('rev-parse','HEAD')==formal and git('rev-parse','HEAD:cosmos-framework')==child
assert all(line.startswith('?? docs/collab/codex/evidence/2026-11-04_g2_gateb_replay_author_cpu/')
    for line in git('status','--porcelain').splitlines())
out.mkdir(parents=True,exist_ok=True)
for dirname in ['legacy83_final','final24','red_frozen20','static_final']:
    target=out/dirname;target.mkdir(exist_ok=True)
    for path in (base/dirname).iterdir():
        if path.is_file() and path.suffix in ('.json','.xml','.log'):
            shutil.copy2(path,target/path.name)
# Retain the first corrected-source failure without rebinding it to final source.
target=out/'superseded_development_3fail';target.mkdir(exist_ok=True)
for name in ['pytest.log','junit.xml','summary.json','source_before.json','invocation.json']:
    shutil.copy2(base/'green_frozen20'/name,target/name)
shutil.copytree(base/'frozen',out/'frozen20',dirs_exist_ok=True)
for name in ['assertion_preservation.json','native_render_summary.json','run_checks.py','static_checks.py','render_summary.py']:
    shutil.copy2(base/name,out/name)
shutil.copy2(base/'native/download.json',out/'osmesa_package.json')
probe=Path('/tmp/g2_ray_audit_20261104')
target=out/'independent_synthetic_probes';target.mkdir(exist_ok=True)
for name in ['probe.py','probe.json','boundary_probe.py','boundary_probe.json','mt_probe.py','mt_probe.json','native_sim_fixture.py','probe.freeze.json']:
    shutil.copy2(probe/name,target/name)
files=sorted((root/'tools/g2').rglob('*.py'))+[root/'docs/build/PSM-WMA_G2_GateB_Replay_Visibility_Followup_2026-11-04.md']
bindings=[]
for path in files:
    relative=str(path.relative_to(root))
    blob=git('rev-parse',f'{formal}:{relative}')
    assert blob==git('hash-object',relative)
    bindings.append(dict(path=relative,git_blob=blob,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
dump(out/'source_bindings.json',dict(formal_root=formal,child_gitlink=child,files=bindings))
protected=['cosmos-framework','scripts','configs','examples','third_party']
scope=dict(parent=parent,formal_root=formal,changed=git('diff-tree','--no-commit-id','--name-only','-r',formal).splitlines(),
    protected={p:dict(before=git('ls-tree',parent,'--',p) or 'ABSENT',
        after=git('ls-tree',formal,'--',p) or 'ABSENT') for p in protected})
assert all(v['before']==v['after'] for v in scope['protected'].values())
dump(out/'scope.json',scope)
(out/'source_diff.patch').write_text(subprocess.check_output(['git','diff',parent,formal,'--','tools/g2'],cwd=root,text=True))
all_cases=[]
for dirname,expected in [('legacy83_final',83),('final24',24)]:
    ident=json.loads((out/dirname/'identity_before.json').read_text())
    assert ident['root']==formal and ident['child']==ident['gitlink']==child
    assert not ident['status'] and not ident['child_status']
    summary=json.loads((out/dirname/'summary.json').read_text())
    assert summary['tests']==expected and summary['returncode']==summary['failures']==summary['errors']==summary['skipped']==0
    assert summary['source_unchanged'] and summary['identity_unchanged']
    all_cases.extend((c.get('classname'),c.get('name')) for c in ET.parse(out/dirname/'junit.xml').findall('.//testcase'))
assert len(all_cases)==len(set(all_cases))==107
red=json.loads((out/'red_frozen20/summary.json').read_text())
assert red['tests']==20 and red['failures']==9 and red['returncode']==1
dump(out/'gate.json',dict(formal_root=formal,child=child,gitlink=child,status='AUTHOR_CPU_PASS_NOT_PHYSICAL_ACCEPTANCE',
    tests=107,distinct_tests=107,legacy=83,native_software_render=24,failures=0,errors=0,skipped=0,
    frozen20_baseline=dict(tests=20,failed=9,passed=11,expected_red=True),
    ruff_version='0.12.7',ruff_check='PASS',ruff_format='PASS',ast_compile_files=10,
    legacy_assertions_unchanged=True,server_gate_b='FAIL_PRESERVED_NOT_RERUN',
    server_rgb_root_cause='UNRESOLVED_DIAGNOSTICS_ADDED',
    actual_gpu_or_robocasa_or_server_data=False,
    evidence_limits=['CPU Mesa software synthetic scenes only; no DS/GPT independent test pass',
        'Eligibility and front-face mesh protocol require fresh Code Gate',
        'No proof that synthetic artifacts explain all six real Gate B failures',
        'No source RGB rendering parameter changes or threshold relaxation',
        'No V3 promotion, GateC, N100, server replay or training authorization']))
artifacts={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest()
    for p in sorted(out.rglob('*')) if p.is_file()}
dump(out/'artifact_manifest.json',artifacts)
print(json.dumps(dict(artifacts=len(artifacts),source_bindings=len(bindings),tests=107,
    formal_root=formal,child=child,output=str(out)),indent=2))
