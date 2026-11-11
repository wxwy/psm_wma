"""Aggregate measured existing-map A/B runs without upgrading acceptance.

Private images, source paths and full traces stay beside their runs. Published
summaries contain aggregate metrics and evidence hashes, not source files.
"""
import argparse
import hashlib
from pathlib import Path
import statistics
import numpy as np
from g2.io import ContractError,canonical,digest,read_json,write_json


def distribution(values,scale=1):
    a=np.asarray(values,dtype=float)*scale
    return {'n':len(a),'p50':float(np.percentile(a,50)) if len(a) else None,
        'p95':float(np.percentile(a,95)) if len(a) else None,'max':float(a.max()) if len(a) else None}


def summarize(run_directory,view_directories=()):
    root=Path(run_directory);run=read_json(root/'run.json');report=read_json(root/'worker_final.json');w=report['worker']
    if w.get('trace_truncated') or w.get('pending') or w['received']!=len(w['frames']):raise ContractError('incomplete final color trace')
    integrated=[f for f in w['frames'] if f['outcome']=='INTEGRATED'];snapshots=[];navigation={};views=[]
    binding=read_json(next((root/'color_snapshots').glob('frame_*/binding.json')))
    frame_by_stamp={r['timestamp_ns']:r['frame_id'] for r in binding['frames']}
    for capture in run['captures']:
        if not capture['success']:continue
        folder=root/'color_snapshots'/('frame_'+str(capture['frame_id']));m=read_json(folder/'manifest.json');t=m['snapshot_timing']
        snapshots.append({'frame_id':capture['frame_id'],'to_point_cloud_wall_ns':t['to_point_cloud_wall_ns'],
            'to_point_cloud_cpu_ns':t['to_point_cloud_cpu_ns'],'export_wall_ns':m['export_wall_ns'],'export_cpu_ns':m['export_cpu_ns'],
            'points':m['point_count'],'manifest_sha256':digest(folder/'manifest.json')})
        navigation[str(capture['frame_id'])]={k:m['files'][k]['sha256'] for k in ('geometry_grid.raw','native_scene_graph.json')}
    for directory in view_directories:
        folder=Path(directory);v=read_json(folder/'views.json');entries=list(v['views'].values())
        views.append({'frame_id':v['frame_id'],'views_sha256':digest(folder/'views.json'),'render_timing':v['render_timing'],
            'directions':len(entries),'generated':sum(x['image_generated'] for x in entries),
            'skipped_no_object':sum(x['status']=='SKIPPED_NO_PROJECTABLE_OBJECT' for x in entries),
            'unknown_not_observed':sum(x['status']=='UNKNOWN_NOT_OBSERVED' for x in entries),
            'observed_object_pixels':sum(x['observed_object_color_pixels'] for x in entries),
            'observed_pixels':sum(x['observed_color_pixels'] for x in entries),'known_geometry_pixels':sum(x['known_geometry_pixels'] for x in entries),
            'meters_per_pixel':v['recipe']['meters_per_pixel']})
    timing={}
    for name,values in {
        'fusion_wall_ms':[r['integration_end_wall_ns']-r['integration_start_wall_ns'] for r in integrated],
        'fusion_thread_cpu_ms':[r['integration_cpu_ns'] for r in integrated],
        'projection_wall_ms':[r['projection_end_wall_ns']-r['projection_start_wall_ns'] for r in integrated],
        'projection_thread_cpu_ms':[r['projection_cpu_ns'] for r in integrated],
        'worker_total_thread_cpu_ms':[r['total_cpu_ns'] for r in w['frames'] if r['dequeue_wall_ns']],
        'input_hash_thread_cpu_ms':[r['hash_cpu_ns'] for r in integrated],
        'publication_to_point_cloud_wall_ms':[r['publication_to_pointcloud_wall_ns'] for r in integrated if r['publish_wall_ns']],
        'snapshot_to_point_cloud_wall_ms':[r['to_point_cloud_wall_ns'] for r in snapshots],
        'snapshot_to_point_cloud_thread_cpu_ms':[r['to_point_cloud_cpu_ns'] for r in snapshots],
        'color_export_wall_ms':[r['export_wall_ns'] for r in snapshots],
        'color_export_thread_cpu_ms':[r['export_cpu_ns'] for r in snapshots],
        'render_wall_ms':[r['render_timing']['wall_ns'] for r in views],
        'render_process_cpu_ms':[r['render_timing']['cpu_ns'] for r in views],
        'normal_native_export_wall_ms':[r['wall_ns'] for r in run.get('normal_native_captures',[])],
    }.items():timing[name]=distribution(values,1e-6)
    counters={k:w[k] for k in ('received','dequeued','integrated','skipped','overwritten_pending','cleared_pending','stopped_pending','rejected_enqueue','published','pending')}
    loss=w['overwritten_pending']+w['cleared_pending']+w['rejected_enqueue']+w['skipped']
    return {'schema':'g2_color_ab_summary_v1','scene_id':run['scene_id'],'leaf_m':run['leaf_m'],
        'native_build_source_sha256':report['native_build_source_sha256'],'binding_sha256':run['binding_sha256'],
        'common_inputs_sha256':hashlib.sha256(canonical({k:binding[k] for k in
            ('scene_id','source_sha256','world_frame','episode','camera','manifest_digests','min_depth','max_depth','projection_provider',
             'stamp_start_ns','frames')})).hexdigest(),
        'base_params_sha256':binding['base_params']['sha256'],
        'run_sha256':digest(root/'run.json'),'final_metrics_sha256':digest(root/'worker_final.json'),
        'counters':counters,'non_integrated_fraction':loss/w['received'] if w['received'] else None,
        'peak_rss_mib':w['peak_rss_kib']/1024,'final_sampled_voxels':w['last_sampled_voxels'],
        'integrated_source_frame_ids':[frame_by_stamp[r['rgb_stamp_ns']] for r in integrated],
        'snapshots':snapshots,'navigation_evidence':navigation,'views':views,'timing':timing,
        'requested_view_source_hz':run['requested_view_source_hz'],'publication_hz':w['publication_rate_hz'],
        'requested_capture_count':len(run['captures']),'successful_capture_count':len(snapshots),
        'normal_native_captures':run.get('normal_native_captures',[]),
        'replay_wall_s':run.get('replay_wall_ns',0)/1e9,'source_duration_s':run.get('source_duration_ns',0)/1e9,
        'achieved_capture_wall_interval_ms':distribution([b['finish_wall_ns']-a['finish_wall_ns'] for a,b in zip(run['captures'],run['captures'][1:])],1e-6),
        'live_realtime_rate_certified':False,'source_verification_in_fusion_timing':False,
        'six_view_clarity_human_gate':'PENDING','models_run':0,'training_ready':False}


def compare(summaries):
    if len(summaries)!=3 or sorted(s['leaf_m'] for s in summaries)!=[.01,.02,.05] or len({s['scene_id'] for s in summaries})!=1:
        raise ContractError('same-scene 5/2/1cm run triple required')
    for key in ('common_inputs_sha256','base_params_sha256','native_build_source_sha256','requested_view_source_hz'):
        if len({s[key] for s in summaries})!=1:raise ContractError('A/B inputs/build/base configuration differ: '+key)
    source_ids=[s['integrated_source_frame_ids'] for s in summaries]
    frame_sets=[set(s['navigation_evidence']) for s in summaries]
    if not frame_sets[0] or any(x!=frame_sets[0] for x in frame_sets):raise ContractError('A/B capture frame inventory is missing or differs')
    frames=frame_sets[0]
    geometry={f:len({s['navigation_evidence'][f]['geometry_grid.raw'] for s in summaries})==1 for f in sorted(frames,key=int)}
    graph={f:len({s['navigation_evidence'][f]['native_scene_graph.json'] for s in summaries})==1 for f in sorted(frames,key=int)}
    return {'schema':'g2_color_ab_comparison_v1','scene_id':summaries[0]['scene_id'],'summaries':summaries,
        'same_integrated_source_frame_ids':all(x==source_ids[0] for x in source_ids),
        'navigation_grid_byte_equality_by_frame':geometry,'native_scene_graph_byte_equality_by_frame':graph,
        'comparison_complete':all(s['requested_capture_count']==s['successful_capture_count'] and s['successful_capture_count']>0 for s in summaries),
        'geometry_parameters_changed':False,'new_map_or_cache':False,'production_default_changed':False,
        'full_navigation_stability_acceptance':False,'training_ready':False,
        'status':'AUTHOR_MEASUREMENTS_PENDING_GPT_REPEAT_AND_HUMAN_CLARITY'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',action='append',required=True);p.add_argument('--output',required=True)
    p.add_argument('--views-root',action='append',default=[]);a=p.parse_args();summaries=[]
    for run in a.run:
        root=Path(run);view_roots=[Path(v) for v in a.views_root if Path(v).name==root.name]
        views=[p.parent for v in view_roots for p in v.rglob('views.json')]
        summaries.append(summarize(root,views))
    out=Path(a.output)
    if out.exists():raise ContractError('new aggregate output required')
    write_json(out,compare(summaries));print('AUTHOR_MEASUREMENTS_NOT_ACCEPTANCE')

if __name__=='__main__':main()
