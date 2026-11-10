"""Run on the authorized server. Print derived scalars/hashes only, no raw files."""
import hashlib
import json
import statistics
import subprocess
from pathlib import Path

base = Path('/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_codex_issue31_prefix_kv_20261109')
p = base / 'gpu05'
r = json.loads((p / 'result.json').read_text())
assert r['status'] == 'PASS' and r['source_unchanged']
rows = [json.loads(s) for s in (p / 'measurements.jsonl').read_text().splitlines()]
assert len(rows) == 60


def percentile(values, fraction):
    values = sorted(values)
    at = (len(values) - 1) * fraction
    lo = int(at)
    hi = min(lo + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (at - lo)


def stats(values):
    return dict(n=len(values), mean=statistics.mean(values), min=min(values),
                p50=percentile(values, .5), p95=percentile(values, .95),
                p99=percentile(values, .99), max=max(values))


audit = json.loads((p / 'audit.json').read_text())
assert all(len(audit[mode]['layers']) == 28 for mode in ('baseline', 'optimized', 'changed_prefix', 'repeated_original'))
assert audit['baseline']['output_sha256']['action'] != audit['changed_prefix']['output_sha256']['action']
measured_errors = {key: max(e['max_abs'] for row in rows for e in row['errors_from_baseline'][key])
                   for key in ('vision', 'action')}
assert measured_errors == dict(vision=0., action=0.)
paired = []
for i in range(30):
    pair = {row['mode']: row for row in rows[2*i:2*i+2]}
    paired.append(pair['baseline']['native_generate_gpu_ms'] - pair['optimized']['native_generate_gpu_ms'])
kernel_counts = json.loads((p / 'kernel_counts.json').read_text())
kernel_summary = {}
for mode, counts in kernel_counts.items():
    kernel_summary[mode] = dict(
        launches=sum(counts.values()), distinct_kernel_names=len(counts),
        names_sha256=hashlib.sha256(json.dumps(counts, sort_keys=True).encode()).hexdigest(),
        top_kernels=sorted(counts.items(), key=lambda row: row[1], reverse=True)[:12])
diagnostics = {}
for name in ('gpu_diag01', 'gpu_diag02'):
    d = json.loads((base / name / 'diagnostic.json').read_text())
    # Preserve only identities and numeric shape/error metadata, never tensors.
    diagnostics[name] = dict(
        status=d['status'], root=d['root']['root'], child=d['root']['child'],
        source_unchanged=d['source_unchanged'], recompile_limit=d['recompile_limit'],
        velocity_errors=d['velocity_errors'],
        layout={k:v for k,v in d['layout'][0].items() if not k.endswith('indices')},
        max_und_k_change=max(row['k']['max_abs'] for row in d['und_kv_timestep_changes']),
        max_und_v_change=max(row['v']['max_abs'] for row in d['und_kv_timestep_changes']),
        changed_und_layers=[row['layer'] for row in d['und_kv_timestep_changes']
                            if not row['k']['equal'] or not row['v']['equal']])
failures = {}
for name in ('gpu01', 'gpu02', 'gpu03', 'gpu04'):
    f = base / name / 'result.json'
    if f.exists():
        old = json.loads(f.read_text())
        failures[name] = dict(status=old.get('status'), error_type=str(old.get('error', '')).split('(')[0],
                             root=old.get('identity', {}).get('root'),
                             child=old.get('identity', {}).get('child'))
raw_hashes = {}
for name in ('gpu01', 'gpu02', 'gpu03', 'gpu04', 'gpu05', 'gpu_diag01', 'gpu_diag02'):
    directory = base / name
    if not directory.exists():
        continue
    for path in sorted(directory.glob('*')):
        if path.is_file():
            h = hashlib.sha256()
            with path.open('rb') as stream:
                for chunk in iter(lambda: stream.read(1024*1024), b''):
                    h.update(chunk)
            raw_hashes[str(path.relative_to(base))] = dict(bytes=path.stat().st_size, sha256=h.hexdigest())
    log = base / (name + '.log')
    if log.exists():
        raw_hashes[log.name] = dict(bytes=log.stat().st_size, sha256=hashlib.sha256(log.read_bytes()).hexdigest())
remaining_model_pids = []
for proc in Path('/proc').iterdir():
    if proc.name.isdigit():
        try:
            args = (proc / 'cmdline').read_bytes().split(b'\0')
            if (b'tools/v3/benchmark_local_ttt_prefix_kv.py' in args or
                str(base / 'diagnose_velocity.py').encode() in args):
                remaining_model_pids.append(int(proc.name))
        except (PermissionError, FileNotFoundError, ProcessLookupError):
            pass
assert not remaining_model_pids
git = lambda repo, *args: subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()
root = base / 'root5'
after = dict(root=git(root, 'rev-parse', 'HEAD'), child=git(root / 'cosmos-framework', 'rev-parse', 'HEAD'),
             gitlink=git(root, 'rev-parse', 'HEAD:cosmos-framework'),
             root_status=git(root, 'status', '--porcelain'), child_status=git(root / 'cosmos-framework', 'status', '--porcelain'))
assert after == r['identity']
result = dict(
    kind='DERIVED_STATISTICS_AND_HASHES_ONLY_NO_PRIVATE_SERVER_FILE_EXPORT',
    formal_pair=r['identity'], status=r['status'], independent_approval='NOT_CLAIMED',
    benchmark_exit_code=0, source_unchanged=r['source_unchanged'], post_exit_identity=after,
    correctness=r['correctness'], max_abs_measured_error=measured_errors,
    audit_output_errors=r['audit_output_errors'], repeated_request_errors=r['repeat_request_errors'],
    uninstrumented_output_errors=r['uninstrumented_output_errors'],
    prefix_sensitivity=True, fresh_cache_refill_each_request=True,
    layers=28, denoising_steps=30,
    layer_audit={mode:dict(distinct_counters=[dict(zip(audit[mode]['layers'][0].keys(), values))
                       for values in sorted({tuple(row.values()) for row in audit[mode]['layers']})])
                 for mode in audit},
    layer_hooks_removed_before_measurement=r['layer_hooks_removed_before_measurement'],
    recompile_limit=r['recompile_limit'], validate_model_mode_and_dcp_inventory=r['validate_model_mode_and_dcp_inventory'],
    torch=r['torch'], cuda=r['cuda'], checkpoint_metadata_sha256=r['checkpoint_metadata_sha256'],
    checkpoint_config_sha256=r['checkpoint_config_sha256'], fixed_inputs_sha_and_shapes=r['fixed_inputs'],
    warmup_pairs=3, clean_warmup_pairs=3, measurement_pairs=30,
    measurements=r['measurements'],
    additional_gpu_ms={mode:stats([row['native_generate_gpu_ms'] for row in rows if row['mode']==mode])
                       for mode in ('baseline', 'optimized')},
    slowest_three={mode:[dict(tag=row['tag'], gpu_ms=row['native_generate_gpu_ms'],
                             wall_ms=row['native_generate_wall_ms'], current_vae_gpu_ms=row['current_vae_gpu_ms'])
                        for row in sorted((row for row in rows if row['mode']==mode),
                                          key=lambda row:row['native_generate_gpu_ms'], reverse=True)[:3]]
                   for mode in ('baseline', 'optimized')},
    optimized_faster_pairs=sum(value>0 for value in paired),
    paired_gpu_ms_savings=stats(paired),
    speedup_p50=r['speedup_p50'], p50_latency_reduction_fraction=1-1/r['speedup_p50'],
    performance=r['performance'], current_vae_included_in_generation=True,
    history_updates_excluded_from_generation_timing=True, pack_template_reuse_with_prefix=False,
    kernel_summary=kernel_summary, previous_failures=failures, teacher_forced_diagnostics=diagnostics,
    raw_server_only_hashes=raw_hashes,
    remaining_owned_model_pids=remaining_model_pids,
    gpu_after_process_exit=subprocess.check_output(['nvidia-smi', '-i', '6', '--query-gpu=index,uuid,name,memory.used,utilization.gpu', '--format=csv,noheader,nounits'], text=True).strip(),
    server_only_artifact_directory=str(p),
    limitation='Synthetic composite/history; fixed Local iter15000, B1/two_way/30-step UniPC. Background gpu_load_sim unchanged. No Sim/Worker/SR/900EP/NoTTT causal comparison or independent review claimed.')
print(json.dumps(result, separators=(',', ':'), allow_nan=False))
