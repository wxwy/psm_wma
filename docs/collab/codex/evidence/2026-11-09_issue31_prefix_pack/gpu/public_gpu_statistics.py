"""Run on authorized server: print derived statistics/hashes, no raw file export."""
import hashlib
import json
import statistics
import subprocess
from pathlib import Path

base=Path('/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_codex_issue31_prefix_pack_20261109')
p=base/'gpu02'
r=json.loads((p/'result.json').read_text())
assert r['status'] in ('PASS','CORRECTNESS_PASS_PERFORMANCE_NOT_MET') and r['correctness']=='PASS' and r['source_unchanged']
assert r['optimization']=='prefix_pack' and r['baseline_text_kv_cache']
rows=[json.loads(line) for line in (p/'measurements.jsonl').read_text().splitlines()]
assert len(rows)==60
def percentile(values,q):
 values=sorted(values);a=(len(values)-1)*q;i=int(a);j=min(i+1,len(values)-1)
 return values[i]+(values[j]-values[i])*(a-i)
def stats(values):
 return dict(n=len(values),mean=statistics.mean(values),min=min(values),max=max(values),
             p50=percentile(values,.5),p95=percentile(values,.95),p99=percentile(values,.99))
errors={key:max(error['max_abs'] for row in rows for error in row['errors_from_baseline'][key])
        for key in ('vision','action')}
assert errors==dict(vision=0.,action=0.)
audit=json.loads((p/'audit.json').read_text())
assert audit['baseline']['native_pack_calls']==31 and audit['optimized']['native_pack_calls']==2
for mode in audit:
 assert len(audit[mode]['layers'])==28
 assert all(row==dict(forwards=30,gen_only=29,prefix_context=30,prefix_kv_projection=30)
            for row in audit[mode]['layers'])
assert audit['baseline']['output_sha256']['action']!=audit['changed_prefix']['output_sha256']['action']
assert audit['optimized']['output_sha256']==audit['repeated_original']['output_sha256']
savings=[]
for i in range(30):
 pair={row['mode']:row for row in rows[2*i:2*i+2]}
 savings.append(pair['baseline']['native_generate_gpu_ms']-pair['optimized']['native_generate_gpu_ms'])
kernels=json.loads((p/'kernel_counts.json').read_text())
hashes={}
for name in ('gpu01','gpu02'):
 for path in sorted((base/name).glob('*')):
  if path.is_file():
   h=hashlib.sha256()
   with path.open('rb') as stream:
    for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
   hashes[str(path.relative_to(base))]=dict(bytes=path.stat().st_size,sha256=h.hexdigest())
 log=base/(name+'.log')
 if log.exists():hashes[log.name]=dict(bytes=log.stat().st_size,sha256=hashlib.sha256(log.read_bytes()).hexdigest())
root=base/'root2'
git=lambda repo,*args:subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()
identity=dict(root=git(root,'rev-parse','HEAD'),child=git(root/'cosmos-framework','rev-parse','HEAD'),
 gitlink=git(root,'rev-parse','HEAD:cosmos-framework'),root_status=git(root,'status','--porcelain'),
 child_status=git(root/'cosmos-framework','status','--porcelain'))
assert identity==r['identity']
remaining=[]
for proc in Path('/proc').iterdir():
 if proc.name.isdigit():
  try:
   args=(proc/'cmdline').read_bytes().split(b'\0')
   if b'tools/v3/benchmark_local_ttt_prefix_kv.py' in args and str(root).encode() in args:remaining.append(int(proc.name))
  except (PermissionError,FileNotFoundError,ProcessLookupError):pass
assert not remaining
old=json.loads((base/'gpu01/result.json').read_text())
public=dict(kind='DERIVED_STATISTICS_AND_HASHES_ONLY_NO_PRIVATE_SERVER_FILE_EXPORT',
 status=r['status'],independent_approval='NOT_CLAIMED',benchmark_exit_code=0 if r['status']=='PASS' else 2,
 formal_pair=identity,source_unchanged=True,recompile_limit=r['recompile_limit'],
 optimization=r['optimization'],text_kv_on_both_sides=True,
 input_kind='Fixed synthetic composite/history; real Local iter15000 DCP, raw15/H16/4x32Prefix/B1/30-step UniPC/guidance1',
 validate_model_mode_and_dcp_inventory=r['validate_model_mode_and_dcp_inventory'],
 torch=r['torch'],cuda=r['cuda'],checkpoint_config_sha256=r['checkpoint_config_sha256'],
 checkpoint_metadata_sha256=r['checkpoint_metadata_sha256'],fixed_inputs_sha_and_shapes=r['fixed_inputs'],
 max_abs_measured_error=errors,audit_output_errors=r['audit_output_errors'],
 repeated_request_errors=r['repeat_request_errors'],uninstrumented_output_errors=r['uninstrumented_output_errors'],
 all28layers_each_mode=dict(forwards=30,gen_only=29,prefix_context=30,prefix_kv_projection=30),
 native_total_pack_calls=dict(baseline=31,optimized=2),native_preparation_pack_calls=1,
 denoising_pack_calls=dict(baseline=30,optimized=1),
 prefix_sensitivity=True,fresh_cache_and_template_per_request=True,
 layer_hooks_removed_before_measurement=r['layer_hooks_removed_before_measurement'],
 pack_audit_removed_before_measurement=r['pack_audit_removed_before_measurement'],
 warmup_pairs=3,clean_warmup_pairs=3,measurement_pairs=30,
 measurements=r['measurements'],
 gpu_ms={mode:stats([row['native_generate_gpu_ms'] for row in rows if row['mode']==mode]) for mode in ('baseline','optimized')},
 paired_gpu_ms_savings=stats(savings),optimized_faster_pairs=sum(x>0 for x in savings),
 slowest_three={mode:[dict(tag=row['tag'],gpu_ms=row['native_generate_gpu_ms'],
 wall_ms=row['native_generate_wall_ms'],current_vae_gpu_ms=row['current_vae_gpu_ms'])
 for row in sorted((row for row in rows if row['mode']==mode),key=lambda row:row['native_generate_gpu_ms'],reverse=True)[:3]]
 for mode in ('baseline','optimized')},
 speedup_p50=r['speedup_p50'],p50_latency_reduction_fraction=1-1/r['speedup_p50'],performance=r['performance'],
 current_vae_included_in_generation=True,history_updates_excluded_from_generation_timing=True,
 kernel_summary={mode:dict(cuda_events_including_memcpy=sum(v.values()),distinct_names=len(v),
 sha256=hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()) for mode,v in kernels.items()},
 previous_gpu01=dict(status=old['status'],root=old['identity']['root'],child=old['identity']['child'],
 error=old['error'],audit_errors=old['audit_output_errors'],
 disposition='Benchmark counted one native preparation pack as well. Expected totals corrected31->2; production and Child unchanged.'),
 raw_server_only_hashes=hashes,server_only_artifact_directory=str(p),remaining_owned_model_pids=remaining,
 gpu_after_process_exit=subprocess.check_output(['nvidia-smi','-i','6','--query-gpu=index,uuid,name,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip(),
 limitation='Existing gpu_load_sim unchanged; fixed synthetic model-only paired workload, no Sim/Worker/SR/900EP or exclusive-GPU/NoTTT comparison. Stage1 P99 outlier remains unresolved independently of this run.')
print(json.dumps(public,separators=(',',':'),allow_nan=False))
