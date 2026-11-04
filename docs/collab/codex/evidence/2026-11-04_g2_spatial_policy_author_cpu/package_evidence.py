import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

root=Path('/workspace/psm-wma-g2-spatial-policy')
base=Path('/tmp/psm-g2-spatial-policy-20261104')
out=root/'docs/collab/codex/evidence/2026-11-04_g2_spatial_policy_author_cpu'
formal='3eb8b334150018212ae1f51afb5e954b83fa1186'
child='1069fe78841228cadbbfbe6afbd767eaed6225da'
parent='f63454610ec2b95617c670444875339034c3c1c7'
def git(*args):return subprocess.check_output(['git',*args],cwd=root,text=True).strip()
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
assert git('rev-parse','HEAD')==formal and git('rev-parse','HEAD:cosmos-framework')==child
assert not git('status','--porcelain')
identity=json.loads((base/'final_cpu/identity_before.json').read_text())
assert identity['root']==formal and identity['child']==identity['gitlink']==child
assert not identity['status'] and not identity['child_status']
out.mkdir(parents=True)
for name in ['final_cpu','red_old_contract','static_final']:
    target=out/name;target.mkdir()
    for path in (base/name).iterdir():
        if path.is_file() and path.suffix in ('.json','.xml','.log'):
            shutil.copy2(path,target/path.name)
shutil.copytree(base/'frozen',out/'frozen35')
for name in ['contract_and_scope_proof.json','runbook_syntax.json','run_cpu.py','static_gate.py','package_evidence.py']:
    shutil.copy2(base/name,out/name)
new=json.loads((out/'final_cpu/summary.json').read_text())
old=json.loads((out/'red_old_contract/summary.json').read_text())
assert new['tests']==new['distinct']==121 and new['returncode']==new['failures']==new['errors']==new['skipped']==0
assert old['tests']==35 and old['failures']==31 and old['returncode']==1
cases=ET.parse(out/'final_cpu/junit.xml').findall('.//testcase')
assert len({(c.get('classname'),c.get('name')) for c in cases})==121
files=sorted((root/'tools/g2').rglob('*.py'))+[
    root/'tools/g2/README.md',root/'docs/build/PSM-WMA_G2_Spatial_Acceptance_v2_and_GateC_Plan_2026-11-04.md']
bindings=[]
for path in files:
    relative=str(path.relative_to(root))
    blob=git('rev-parse',formal+':'+relative)
    assert blob==git('hash-object',relative)
    bindings.append(dict(path=relative,git_blob=blob,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
dump(out/'source_bindings.json',dict(formal_root=formal,child_gitlink=child,files=bindings))
protected=['tools/g2/rgbd_pose','tools/g2/export_robocasa_rgbd_pose.py','tools/g2/test_replay_render_visibility.py',
    'cosmos-framework','scripts','configs','third_party','tools/g0']
scope={p:dict(before=git('rev-parse',parent+':'+p),after=git('rev-parse',formal+':'+p)) for p in protected}
assert all(v['before']==v['after'] for v in scope.values())
changed=git('diff-tree','--no-commit-id','--name-only','-r',formal).splitlines()
assert len(changed)==7
dump(out/'scope.json',dict(parent=parent,formal_root=formal,changed=changed,protected=scope,
    production_changed=['tools/g2/verify_robocasa_rgbd_pose.py'],old_native24_not_rerun=True))
(out/'source_diff.patch').write_text(subprocess.check_output(['git','diff',parent,formal,'--','tools/g2'],cwd=root,text=True))
examples=[]
for path in (base/'final_cpu/pytest_tmp').rglob('new_spatial_report.json'):
    value=json.loads(path.read_text())
    if value.get('photometric_diagnostic',{}).get('status')=='FAIL':
        examples.append(dict(fixture_kind='SYNTHETIC_NATIVE_PROTOCOL_BOUNDARY_DOUBLE_NOT_SERVER',
            source_test_artifact=str(path),artifact_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            owner_reference_is_inert_test_input_not_attested_for_fixture=True,report=value))
assert len(examples)==1
dump(out/'synthetic_native_protocol_example.json',examples[0])
dump(out/'gate.json',dict(formal_root=formal,child=child,gitlink=child,
    status='AUTHOR_CPU_PASS_SPATIAL_V2_NOT_SERVER_ACCEPTANCE',acceptance_policy='g2_stage1_spatial_v2',
    owner_policy_authority=parent,tests=121,distinct_tests=121,legacy_tests=83,policy_tests=38,
    failures=0,errors=0,skipped=0,frozen35_old_contract=dict(expected_red=True,failures=31,passed=4),
    unchanged_old_assertions=68,intentional_legacy_status_assertion_updates=1,
    ruff_version='0.12.7',ruff_check='PASS',ruff_format='PASS',ast_compile_files=11,
    prior_native24_source_unchanged_not_rerun=True,
    owner_visual_review_mode='EXTERNAL_REFERENCE_ONLY_NEVER_AUTOMATIC_PASS',
    real_renderer_or_robocasa_or_server_data_used=False,new_server_report='NOT_EXECUTED',
    gate_c='PLAN_ONLY_PENDING_APPROVAL_AND_EXACT_3_TO_5_TASK_SELECTION',n100_or_v3_promotion=False,
    limits=['Prior six-frame geometry/Owner visual evidence remains separate from this author test result',
        'Old RGB photometric FAIL metrics and legacy physical verdicts are unchanged',
        'Old-contract RED is expected under a superseded Owner policy, not evidence old geometry was wrong',
        'Synthetic native-kind CLI fixture tests protocol only; does not authenticate an Owner or a real renderer',
        'No new hardware/DS independent result or GateC closure is claimed']))
dump(out/'artifact_manifest.json',{str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest()
    for p in sorted(out.rglob('*')) if p.is_file()})
print(json.dumps(dict(artifacts=len(json.loads((out/'artifact_manifest.json').read_text())),
    source_bindings=len(bindings),formal_root=formal,child=child,tests=121),indent=2))
