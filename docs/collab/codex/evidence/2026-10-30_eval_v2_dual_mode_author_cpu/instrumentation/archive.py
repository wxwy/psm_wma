"""Archive a completed exact-Pair author check without re-executing project code."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

BASE=Path(__file__).parent
ROOT=Path('/workspace/work/psm-wma-dual-mode')
FORMAL=Path('/workspace/work/psm-wma-dual-mode-formal')
PAIR={'root':'d18b420c02cfc51a1b85e9f1d6ce5d26f7bd3163','child':'2f7334c4ada6ace1d21185985aae90539052bf18'}
DEST=ROOT/'docs/collab/codex/evidence/2026-10-30_eval_v2_dual_mode_author_cpu'
assert not DEST.exists()
TMP=BASE/'archive-staging'
TMP.mkdir()
meta=json.loads((BASE/'final/execution.json').read_text())
assert meta['shell_exit']==0 and meta['source_unchanged'] and meta['counts']['failures']==meta['counts']['errors']==meta['counts']['skipped']==0
assert meta['source_before']['root']==PAIR['root'] and meta['source_before']['child']==PAIR['child']
assert meta['source_before']['gitlink']==PAIR['child']
assert meta['source_before']['root_status']==meta['source_before']['child_status']==''
mapping=[]
def copy(source,target):
    target=TMP/target
    target.parent.mkdir(parents=True,exist_ok=True)
    raw=source.read_bytes()
    target.write_bytes(raw)
    mapping.append({'original':str(source),'published':str(target.relative_to(TMP)),
                    'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
for label in ('focused','focused2','focused3','focused4','startup-fix2','final'):
    for p in sorted((BASE/label).iterdir()):
        if p.is_file(): copy(p,Path('raw')/label/p.name)
for label in ('static-working','static-final'):
    for p in sorted((BASE/label).iterdir()):
        if p.is_file(): copy(p,Path('raw')/label/p.name)
for name in ('run_checks.py','static_checks.py','archive.py','queue_format_intermediate.diff'):
    copy(BASE/name,Path('instrumentation')/name)
# Only synthetic OS run evidence; exclude capability secrets/cache and pytest mini repos.
os_runs=[]
for directory in sorted((BASE/'final/tmp').iterdir()):
    if directory.is_symlink() or not directory.is_dir(): continue
    if directory.name.startswith(('test_real_OS_','test_owned_Server_death_')) and (directory/'run/manifest.json').is_file():
        run=directory/'run'
        for p in sorted(run.rglob('*')):
            if p.is_file() and p.suffix in ('.json','.jsonl','.log') and not p.is_symlink():
                if 'server_capabilities' not in p.parts and 'cache' not in p.parts:
                    copy(p,Path('os_runs')/directory.name/p.relative_to(run))
        manifest=json.loads((run/'manifest.json').read_text())
        calls=[]
        faults=[]
        for log in (run/'logs').glob('*_server.log'):
            for line in log.read_text().splitlines():
                for prefix,values in (('CPU_NATIVE_BATCH ',calls),('CPU_SERVER_FAULT ',faults)):
                    if line.startswith(prefix): values.append(json.loads(line.removeprefix(prefix)))
        rows=[]
        for p in (run/'_internal/scheduler').glob('*/*.json'):
            rows.append(json.loads(p.read_text()))
        os_runs.append({'name':directory.name,'local_memory_mode':manifest['protocol']['local_memory'],
                        'execution':manifest.get('execution'),
                        'Core_count':len(list(run.glob('tasks/*/episodes/*/result.json'))),
                        'requests':sum(c['size'] for c in calls),
                        'histogram':{str(n):sum(c['size']==n for c in calls) for n in range(1,9) if any(c['size']==n for c in calls)},
                        'server_model_PIDs':sorted({c['pid'] for c in calls}),
                        'faults':faults})
    if directory.name.startswith('test_public_CLI_Fresh_Resume_i') and (directory/'out/manifest.json').is_file():
        run=directory/'out'
        for p in sorted(run.rglob('*')):
            if p.is_file() and p.suffix in ('.json','.jsonl') and 'cache' not in p.parts and not p.is_symlink():
                copy(p,Path('cli_runs')/directory.name/p.relative_to(run))
    if directory.name.startswith(('test_real_small_DCP_','test_selected_DCP_tree_','test_public_server_constructor')):
        for p in sorted(directory.rglob('*')):
            if p.is_file() and (p.name=='.metadata' or p.suffix=='.distcp') and not p.is_symlink():
                assert p.stat().st_size < 1024**2
                copy(p,Path('tiny_synthetic_DCP')/directory.name/p.relative_to(directory))

def git(repo,*args): return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()
bindings={}
for name,sha in meta['source_after']['sha256'].items():
    in_child=name.startswith('cosmos-framework/')
    repo=FORMAL/'cosmos-framework' if in_child else FORMAL
    relative=name.removeprefix('cosmos-framework/') if in_child else name
    ref=PAIR['child'] if in_child else PAIR['root']
    bindings[name]={'commit':ref,'git_blob':git(repo,'rev-parse',ref+':'+relative),'sha256':sha}
cases=list(ET.parse(BASE/'final/junit.xml').getroot().iter('testcase'))
per_file={}
for c in cases:
    name=c.attrib['classname']
    per_file[name]=per_file.get(name,0)+1
summary={'scope':'AUTHOR_TARGETED_CPU_ONLY','status':'PASS','formal_pair':PAIR,'source_unchanged':True,
         'source_files_watched':len(bindings),'shell_exit':0,'counts':meta['counts'], 'per_file':per_file,
         'source_guard_smoke':json.loads((BASE/'static-final/source_guard_smoke.json').read_text()),
         'os_runs':os_runs,'GPU_and_real_Canary':'NOT_RUN','DS_independent_new_pair':'NOT_RUN',
         'GPT_new_pair_Code_Gate':'REQUESTED_NOT_SELF_APPROVED','old_435_or_900':'NOT_RUN',
         'intermediate_counts_not_added':True}
(TMP/'source_gitblob_bindings.json').write_text(json.dumps(bindings,indent=2)+'\n')
(TMP/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
(TMP/'original_to_published.json').write_text(json.dumps(mapping,indent=2)+'\n')
(TMP/'next_real_validation.json').write_text(json.dumps({
    'formal_pair':PAIR,'status':'PENDING_NEW_GPT_CODE_GATE_AND_OWNER_EXECUTION_SCOPE',
    'required_modes':['off','required'],
    'execution_profile':'phase_b','sims_per_gpu':2,'max_infer_batch_size':2,
    'checkpoint_and_config':'Separate mode-matched stable complete inputs and fresh independent run namespace per mode',
    'must_prove':['actual native B2 histogram','separate per-mode Episode/SR/Core/MP4 artifacts','owned-only cleanup'],
    'new_GPU_runs_authorized_by_this_handoff':False,'automatic_8_episodes':False,'formal_900':False,
    'training_or_shared_GPU_policy_changes':False},indent=2)+'\n')
DEST.parent.mkdir(parents=True,exist_ok=True)
TMP.rename(DEST)
print(json.dumps({'destination':str(DEST),'files':len(list(DEST.rglob('*'))),'originals':len(mapping),
                  'tests':meta['counts'],'os_runs':os_runs}))
