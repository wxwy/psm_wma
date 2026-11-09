from pathlib import Path
import hashlib,json,shutil,subprocess,xml.etree.ElementTree as ET
from datetime import datetime
from zoneinfo import ZoneInfo
r=Path('/workspace/work/psm-wma-shared-vae-issue27');c=r/'cosmos-framework';src=Path(__file__).parent
formal='9b1756f9099955d6637743f8ad2fa0ee54987b7a';child='60b252d05157b2753d2caebae32b11c878504bbe';old='15dbc97bf13437905ec38247382834067e5341ae'
def git(d,*a):return subprocess.check_output(['git','-C',str(d),*a],text=True).strip()
assert git(r,'rev-parse','HEAD')==formal and git(c,'rev-parse','HEAD')==child and not git(c,'status','--porcelain')
gate=json.loads((src/'author-01/gate.json').read_text());assert gate['status']=='PASS' and gate['source_unchanged'] and gate['exact_pair_clean_after']
source_hashes=json.loads((src/'author-01/source_after.json').read_text())
assert all(hashlib.sha256((r/p).read_bytes()).hexdigest()==sha for p,sha in source_hashes.items())
assert git(r,'rev-parse',formal+':scripts')==git(r,'rev-parse',old+':scripts')
out=r/'docs/collab/codex/evidence/2026-11-09_issue27_streaming_m16_32_sessions';out.mkdir(parents=True,exist_ok=False)
def copy(f,target):target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target)
for name in ['development-01','development-02','development-03','author-01']:
 for f in sorted((src/name).iterdir()):
  if f.is_file() and f.suffix in ['.json','.xml','.log','.py']:copy(f,out/name/f.name)
for name in ['run_focused.py','archive_handoff.py']:copy(src/name,out/'runners'/name)
scenarios=[]
for f in sorted((src/'author-01/tmp').rglob('streaming_m16_evidence.json')):
 proof=json.loads(f.read_text());manifest_path=f.parent/'run/manifest.json';m=json.loads(manifest_path.read_text())
 assert proof['manifest_digest']==m['digest'] and proof['execution']==m['execution']
 assert proof['sims_per_server']==16 and proof['total_sim_sessions']==32 and len(set(proof['session_ids']))==32
 assert proof['worker_count']==proof['render_gpu_count'] and all(v==0 for v in proof['worker_returncodes'])
 assert len(proof['worker_ready_proofs'])==len(proof['worker_close_receipts'])==proof['worker_count']
 target=out/'author-01/scenarios'/f.parent.name
 copy(f,target/f.name);copy(manifest_path,target/'manifest.json')
 scenarios.append(dict(path=str(target.relative_to(out)),servers=2,sims_per_server=16,total_sessions=32,
  render_gpus=proof['render_gpu_count'],workers=proof['worker_count'],native_batch_sizes=proof['native_batch_sizes'],
  worker_acks=proof['worker_result_acks'],owner_ends=proof['scoped_ends'],native_ends=proof['native_ends'],
  worker_returncodes=proof['worker_returncodes'],external_survived=proof['external_process_survived']))
assert len(scenarios)==2 and sorted(x['workers'] for x in scenarios)==[1,2]
development={}
for name in ['development-01','development-02','development-03']:
 suites=list(ET.parse(src/name/'focused.xml').getroot().iter('testsuite'))
 development[name]={key:sum(int(s.get(key,'0')) for s in suites) for key in ['tests','failures','errors','skipped']}
identity=dict(formal_root=formal,child_gitlink=child,previous_formal_root=old,
 root_scripts_tree=git(r,'rev-parse',formal+':scripts'),previous_root_scripts_tree=git(r,'rev-parse',old+':scripts'),
 child_tree=git(c,'rev-parse','HEAD^{tree}'),root_production_byte_identical=True,child_worktree_clean=True,
 source_files_verified=len(source_hashes),python_test_scope=['tools/v3/eval_v2_batch_tests/'+x for x in [
 'shared_vae_routing_test.py','shared_vae_streaming_m16_test.py','shared_vae_daemon_fixture.py']])
(out/'production_identity.json').write_text(json.dumps(identity,indent=2)+'\n')
summary=dict(created_cst=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),formal_root=formal,child_gitlink=child,
 status='AUTHOR_M16_CPU_EVIDENCE_PASS_GPT_REVIEW_REQUIRED',focused=gate['junit'],static_python_files=3,
 source_unchanged=True,production_unchanged=True,scenarios=scenarios,development_results=development,
 previous_full_author_gate=dict(root=old,child=child,top_level=965,subtests=207,rerun_in_this_supplement=False),
 correction='2x16 means2PolicyServers x16Sim/Server =32total; previous2x8 remains16total historical evidence',
 limitations=['syntheticCPU encoder/generation/currentBoundary/env/physicalGPU/kernelClock','no GPU/realSim/SR/900EP/training/official merge','Issue28 not implemented'])
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
hashes={str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.rglob('*')) if f.is_file()}
(out/'artifact_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
print(json.dumps(dict(archive=str(out),files=len(hashes)+1,source_files=len(source_hashes),summary=summary),indent=2))
