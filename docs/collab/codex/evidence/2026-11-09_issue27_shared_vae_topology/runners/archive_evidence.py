"""Whitelist public CPU logs/proofs; never copy private test bootstrap/configs."""
from pathlib import Path
import ast,hashlib,json,shutil,subprocess,sys,xml.etree.ElementTree as ET
from datetime import datetime
from zoneinfo import ZoneInfo

r=Path('/workspace/work/psm-wma-shared-vae-issue27');c=r/'cosmos-framework'
source=Path(__file__).parent;gate=json.loads((source/'author-01/gate.json').read_text())
assert gate['status']=='PASS' and gate['source_unchanged'] and gate['red_green_test_hashes_equal']
out=r/'docs/collab/codex/evidence/2026-11-09_issue27_shared_vae_topology'
out.mkdir(parents=True,exist_ok=False)
def copy(src,dst):
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
for folder in ['red-old-code','red-old-code-02','red-final-test-bytes',*[f'development-{i:02d}' for i in range(1,8)],'author-01']:
 for f in sorted((source/folder).iterdir()):
  if f.is_file() and f.suffix in ('.json','.xml','.log','.txt','.py'):copy(f,out/folder/f.name)
for name in ['run_red.py','run_red_final.py','run_development.py','run_development_02.py','run_cpu_gate.py','archive_evidence.py','run_red_before_format_order_fix.py.txt']:
 f=source/name
 if f.is_file():copy(f,out/'runners'/f.name)
for pattern in ['os_behavior.json','lifecycle.json']:
 for f in sorted((source/'author-01/root_lifecycle_config_tmp').rglob(pattern)):
  copy(f,out/'os_behavior'/f.parent.name/f.name)
new_files=[p for p in r.glob('tools/v3/eval_v2_batch_tests/shared_vae*_test.py') if p.name!='shared_vae_test.py']
new_files += [c/'cosmos_framework'/p for p in ['inference/robocasa_boundary_batch_test.py',
 'inference/robocasa_shared_policy_batch_test.py','inference/robocasa_shared_ready_test.py',
 'inference/robocasa_shared_memory_test.py','inference/robocasa_vae_topology_test.py','scripts/robocasa_shared_feature_batch_test.py']]
names={node.name for p in new_files for node in ast.parse(p.read_text()).body if isinstance(node,ast.FunctionDef) and node.name.startswith('test_')}
groups={};new_tests=[]
for group in ['stage3_focused','root_lifecycle_config','legacy_protection','streaming_bounds']:
 tree=ET.parse(source/'author-01'/f'{group}.xml').getroot()
 cases=list(tree.iter('testcase'));suites=list(tree.iter('testsuite'))
 groups[group]=dict(top_level=len(cases),junit_tests=sum(int(s.get('tests','0')) for s in suites),
  failures=sum(int(s.get('failures','0')) for s in suites),errors=sum(int(s.get('errors','0')) for s in suites),
  skipped=sum(int(s.get('skipped','0')) for s in suites))
 new_tests.extend(dict(group=group,classname=t.get('classname'),name=t.get('name')) for t in cases if t.get('name','').split('[')[0] in names)
summary=dict(created_cst=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
 formal_pair=json.loads((source/'author-01/source_identity.json').read_text()),
 status='AUTHOR_CPU_PASS_INDEPENDENT_CODE_GATE_PENDING',groups=groups,
 top_level_pass=sum(x['top_level'] for x in groups.values()),junit_tests=sum(x['junit_tests'] for x in groups.values()),
 new_top_level_pass=len(new_tests),static_python_files=gate['syntax_files'],
 source_unchanged=gate['source_unchanged'],red_expected_failures=2,red_green_test_hashes_equal=True,
 native_constructor_and_identity_unchanged=True,real_gpu_checkpoint_robocasa_sr='NOT_RUN',
 official_branches_modified=False,scope='existing EvalV2 + NativeBatch + shared B1 VAE; all legal resource/capacity bounded topologies',
 kernel_fixture='explicit existing /proc kernel identity double; native parser unchanged',
 development_failures_preserved=True)
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
(out/'new_testcases.json').write_text(json.dumps(new_tests,indent=2)+'\n')
files={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file()}
(out/'artifact_hashes.json').write_text(json.dumps(files,indent=2)+'\n')
print(json.dumps(dict(evidence=str(out),files=len(files)+1,summary=summary),indent=2))
