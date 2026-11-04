import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

ROOT=Path('/workspace/psm-wma-g2-rgbd-stage1')
BASE=Path('/tmp/psm-g2-rgbd-stage1-20261104')
FORMAL='3d163e91d42802efe487deb89286637cc91ed74c'
PARENT='083b36ac27ad43b6f5127d9a58aed4fac02eaaa7'
CHILD='1069fe78841228cadbbfbe6afbd767eaed6225da'
DEST=ROOT/'docs/collab/codex/evidence/2026-11-04_g2_rgbd_stage1_author_gate_a'
def git(*args,cwd=ROOT):
    return subprocess.check_output(['git',*args],cwd=cwd)
def txt(*args,cwd=ROOT):
    return git(*args,cwd=cwd).decode().strip()
assert txt('rev-parse','HEAD')==FORMAL and txt('rev-parse','HEAD^')==PARENT
assert txt('rev-parse','HEAD:cosmos-framework')==CHILD
assert txt('rev-parse','HEAD',cwd=ROOT/'cosmos-framework')==CHILD
assert not txt('status','--porcelain') and not txt('status','--porcelain',cwd=ROOT/'cosmos-framework')
identity=json.loads((BASE/'final_cpu/identity_after.json').read_text())
summary=json.loads((BASE/'final_cpu/summary.json').read_text())
assert identity['root']==FORMAL and identity['gitlink']==identity['child']==CHILD
assert summary['tests']==82 and summary['failures']==summary['errors']==summary['skips']==0
assert summary['source_unchanged']
assert not DEST.exists()
DEST.mkdir(parents=True)
for label in ['dev001','dev002','dev003','dev004','final_cpu']:
    target=DEST/label; target.mkdir()
    for path in sorted((BASE/label).iterdir()):
        if path.is_file() and path.suffix in {'.json','.xml','.log'}:
            shutil.copyfile(path,target/path.name)
for label in ['pre_static','final_static']:
    target=DEST/label; target.mkdir()
    for path in sorted((BASE/label).iterdir()):
        if path.is_file() and path.suffix in {'.json','.log'}:
            shutil.copyfile(path,target/path.name)
for name in ['run_gate_a.py','static_gate.py','package_gate_a.py']:
    shutil.copyfile(BASE/name,DEST/name)
ray_dir=DEST/'synthetic_native_cpu_ray'; ray_dir.mkdir()
for path in (BASE/'final_cpu/pytest_tmp').rglob('native_cpu_ray.json'):
    value=json.loads(path.read_text())
    assert value['synthetic_scene'] and not value['real_renderer_executed']
    (ray_dir/(value['violation']+'.json')).write_text(json.dumps(value,indent=2)+'\n')
assert len(list(ray_dir.iterdir()))==4

changes=txt('diff-tree','--no-commit-id','--name-only','-r',FORMAL).splitlines()
assert len(changes)==17
assert all(p in ['SESSION.md','TODO.md'] or p.startswith('tools/g2/')
           or p.startswith('docs/collab/codex/requests/2026-11-04_G2_Stage1_')
           or p=='docs/build/PSM-WMA_G2_Stage1_RGBD_Pose_Cache_r1_2026-11-04.md' for p in changes)
protected={}
for path in ['scripts','configs','cosmos-framework','third_party','tools/g0','tools/v3','.codex','MEMORY']:
    before,after=(txt('rev-parse',ref+':'+path) for ref in [PARENT,FORMAL])
    assert before==after,path
    protected[path]={'before':before,'after':after,'unchanged':True}
(DEST/'scope.json').write_text(json.dumps({'formal_root':FORMAL,'parent':PARENT,'child_gitlink':CHILD,
    'changed_files':changes,'protected_trees':protected,'status':'PASS'},indent=2)+'\n')
bindings=[]
for path in sorted(p for p in changes if p.startswith('tools/g2/'))+['tools/g0/robocasa_work_queue.py']:
    data=git('show',FORMAL+':'+path)
    assert data==(ROOT/path).read_bytes()
    bindings.append({'path':path,'root_commit':FORMAL,'git_blob':txt('rev-parse',FORMAL+':'+path),
                     'sha256':hashlib.sha256(data).hexdigest()})
(DEST/'source_bindings.json').write_text(json.dumps(bindings,indent=2)+'\n')
(DEST/'source_diff.patch').write_bytes(git('diff','--binary',PARENT,FORMAL,'--','tools/g2'))
(DEST/'diffstat.txt').write_bytes(git('diff','--stat',PARENT,FORMAL))
check=subprocess.run(['git','diff','--check',PARENT,FORMAL],cwd=ROOT,capture_output=True,text=True)
(DEST/'committed_diff_check.log').write_text(check.stdout+check.stderr)
assert check.returncode==0

# Parse only the owned documentation's shell blocks. No server command is run.
blocks=re.findall(r'```bash\n(.*?)```',(ROOT/'docs/build/PSM-WMA_G2_Stage1_RGBD_Pose_Cache_r1_2026-11-04.md').read_text(),re.S)
for i,block in enumerate(blocks):
    path=BASE/f'runbook_block_{i}.sh';path.write_text(block)
    result=subprocess.run(['bash','-n',str(path)],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
(DEST/'runbook_bash_syntax.json').write_text(json.dumps({'status':'PASS','blocks':len(blocks),
    'server_commands_executed':False},indent=2)+'\n')

urls={
 'robocasa_env_utils.py':'https://github.com/robocasa/robocasa/blob/6f90063c0ec2b9916bbd977368b54c98d9c2d908/robocasa/utils/env_utils.py',
 'robocasa_playback_dataset_hdf5.py':'https://github.com/robocasa/robocasa/blob/6f90063c0ec2b9916bbd977368b54c98d9c2d908/robocasa/scripts/dataset_scripts/playback_dataset_hdf5.py',
 'robocasa_lerobot_utils.py':'https://github.com/robocasa/robocasa/blob/6f90063c0ec2b9916bbd977368b54c98d9c2d908/robocasa/utils/lerobot_utils.py',
 'robosuite_camera_utils.py':'https://github.com/ARISE-Initiative/robosuite/blob/824ac14cefcfb7ec125fe5eb2e0bad7364466154/robosuite/utils/camera_utils.py',
 'robosuite_binding_utils.py':'https://github.com/ARISE-Initiative/robosuite/blob/824ac14cefcfb7ec125fe5eb2e0bad7364466154/robosuite/utils/binding_utils.py',
}
(DEST/'public_reference_bindings.json').write_text(json.dumps([{'url':url,
    'sha256':hashlib.sha256((BASE/'references'/name).read_bytes()).hexdigest()} for name,url in urls.items()],indent=2)+'\n')
gate={'status':'AUTHOR_GATE_A_PASS','formal_root':FORMAL,'child_gitlink':CHILD,'tests':82,
      'distinct_testcases':82,'failures':0,'errors':0,'skips':0,'static':'PASS','syntax_files':9,
      'help_and_lazy_imports':'PASS','source_binding_count':len(bindings),'scope':'ROOT_ONLY_G2_STAGE1',
      'synthetic_cpu_mujoco_ray':'PASS_WITH_EXPECTED_NEGATIVES','real_rasterizer_executed':False,
      'real_server_data_accessed_or_transferred':False,'gpu_or_training_started':False,
      'server_skill_read':False,'server_tests':'PENDING_REMOTE_EXECUTION_TOOL_UNAVAILABLE',
      'actual_depth_replay_gate_b':'PENDING','full_episodes_gate_c':'PENDING',
      'actual_n100_training_membership':'UNCONFIRMED_NO_BATCH_EXPORT',
      'not_GPT_or_DS_acceptance':True,'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(DEST/'gate.json').write_text(json.dumps(gate,indent=2)+'\n')
allowed={'.json','.xml','.log','.txt','.patch','.py'}
for path in DEST.rglob('*'):
    if path.is_file(): assert path.suffix in allowed,path
hashes={str(p.relative_to(DEST)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(DEST.rglob('*')) if p.is_file()}
(DEST/'artifact_manifest.json').write_text(json.dumps({'formal_root':FORMAL,'child_gitlink':CHILD,'sha256':hashes,
    'text_only_no_recordings_or_cache_payloads':True},indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':'PACKAGED','artifacts':len(hashes),'bindings':len(bindings),
    'tests':82,'formal_root':FORMAL,'child_gitlink':CHILD,'evidence':str(DEST)},indent=2))
