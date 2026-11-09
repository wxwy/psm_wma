"""Bind native RGB-D colors to explicit source-GT geometry; never asset colors.

Original data is read in place. Revalidation cost is outside fusion/render timing.
GT objects, Room topology and sensor color have distinct, checkable identities.
"""
import argparse
import hashlib
import json
import shlex
from pathlib import Path
import shutil
import sys

import numpy as np
from g2.io import ContractError, canonical, digest, new_output, read_json, sha, verified_file, write_json
from .full_map import _file, _same_file, _native_modules, NATIVE_FILES

STATUS='MUJOCO_GT_STRUCTURE_NATIVE_RGBD_COLOR_PENDING_HUMAN'
COLOR_FILES={'observed_colors.txt','binding.json','worker_metrics.json','geometry_grid.raw','native_scene_graph.json'}
EVIDENCE={'source_inputs.json','source_proof.txt','source_gt_manifest.json','observed_manifest.json',
          'observed_binding.json','observed_worker_metrics.json','observed_color_complete.txt'}
PREFIX_PINNED={'g2/offline/color_ab.py': '11082a4539db8c612d0dfe140a48a75e4ac318c500cea5fac8f4b3a11efffed1', 'g2/offline/dataset.py': '70fd0d8ceeb5a322957d6ad5ce195c5bc4704c45701048e99da0dfd0a77b8b14', 'g2/offline/geometry.py': 'c0502861f830281eab5c2c1eb7a3671414dec7bc9aeea7024c67831ff191c233', 'g2/offline/replay_robocasa.py': '4cf36be426cfb0c17bb11eb284df3acfde43f25ac6bdeb109e330de59c687196'}


def _check(value, message):
    if not value:raise ContractError(message)


def check_worker(metrics,binding,frame,stamp):
    """Every integrated frame is from the recorded prefix; terminal counts balance."""
    _check(metrics.get('schema')=='nav_sg_color_worker_metrics_v1' and metrics.get('enabled') is True and
        metrics.get('projection_provider') in ('depth','depth_sdf_filtered') and metrics.get('projection_provider')==binding.get('projection_provider') and
        metrics.get('trace_truncated') is False and metrics.get('voxel_leaf_m')==binding['voxel_leaf_m'] and
        metrics.get('last_integrated_stamp_ns')==stamp,'missing/current native color telemetry required')
    rows=metrics.get('frames',[]);declared=binding.get('frames',[])
    _check(isinstance(declared,list) and 0<len(declared)<=100000 and
        all(type(r.get('frame_id')) is int and r['frame_id']==i and type(r.get('header_seq')) is int and r['header_seq']==i+1 and
            type(r.get('timestamp_ns')) is int and r['timestamp_ns']>0 for i,r in enumerate(declared)) and
        all(a['timestamp_ns']<b['timestamp_ns'] for a,b in zip(declared,declared[1:])),
        'recorded binding needs unique ordered frame/header/stamp identities')
    bound={r['timestamp_ns']:r for r in declared}
    _check(len(rows)==metrics.get('received') and [r.get('sequence') for r in rows]==list(range(1,len(rows)+1)),
        'native received trace does not close')
    outcomes={};integrated=[]
    for r in rows:
        outcome=r.get('outcome');outcomes[outcome]=outcomes.get(outcome,0)+1
        _check(outcome in ('INTEGRATED','SKIPPED','OVERWRITTEN_PENDING','CLEARED_PENDING','STOPPED_PENDING','REJECTED_ENQUEUE'),
            'native color snapshot has pending/unknown outcome')
        _check(type(r.get('source_header_seq')) is int and type(r.get('rgb_stamp_ns')) is int and r['rgb_stamp_ns']<=stamp,
            'future color observation forbidden')
        if outcome!='INTEGRATED':continue
        b=bound.get(r['rgb_stamp_ns']);_check(b is not None and b['frame_id']<=frame and r['source_header_seq']==b['header_seq'],
            'color stamp/header absent from recorded source prefix')
        for key,target in (('rgb_stamp_ns','timestamp_ns'),('depth_stamp_ns','timestamp_ns'),('pose_stamp_ns','timestamp_ns'),
                           ('rgb_sha256','rgb_sha256'),('depth_sha256','depth_sha256'),('pose_sha256','pose_sha256'),
                           ('intrinsics','intrinsics'),('rgb_encoding','rgb_encoding'),('depth_encoding','depth_encoding')):
            _check(r.get(key)==b[target],'native RGB-D/K/pose differs from actual recorded frame: '+key)
        for key in ('rgb_layout','depth_layout'):_check(r.get(key)==b.get(key) and isinstance(r.get(key),list) and len(r[key])==4,
            'native image shape/stride/endian differs: '+key)
        _check(0<r['input_wall_ns']<=r['dequeue_wall_ns']<=r['projection_start_wall_ns']<=r['projection_end_wall_ns']<=
            r['integration_start_wall_ns']<=r['integration_end_wall_ns']<=r['finish_wall_ns'],'native timing order differs')
        integrated.append(r)
    counts={'integrated':'INTEGRATED','skipped':'SKIPPED','overwritten_pending':'OVERWRITTEN_PENDING','rejected_enqueue':'REJECTED_ENQUEUE'}
    for key,outcome in counts.items():_check(metrics.get(key)==outcomes.get(outcome,0),'native counter/trace differs: '+key)
    _check(metrics.get('cleared_pending')==outcomes.get('CLEARED_PENDING',0)+outcomes.get('STOPPED_PENDING',0) and
        metrics.get('stopped_pending')==outcomes.get('STOPPED_PENDING',0) and
        metrics.get('dequeued')==metrics['integrated']+metrics['skipped'],'native terminal accounting differs')
    _check(integrated and bound[integrated[-1]['rgb_stamp_ns']]['frame_id']==frame and integrated[-1]['rgb_stamp_ns']==stamp and
        metrics.get('pending') is False,'current observed color prefix is not quiescent')
    return integrated[-1]


def check_color(directory):
    root=Path(directory);m=read_json(root/'manifest.json')
    _check(m.get('schema')=='nav_sg_rgbd_color_snapshot_v1' and m.get('color_source')=='NATIVE_RGBD_FUSION_ONLY' and
        m.get('prescan_initialized') is False and m.get('training_ready') is False and set(m.get('files',{}))==COLOR_FILES,
        'explicit unmixed native RGB-D snapshot required')
    _check((root/'COLOR_OBSERVATION_COMPLETE').read_text()=='SOURCE_BOUND_NATIVE_RGBD_COLOR_NOT_ACCEPTANCE\n',
        'incomplete observed color snapshot')
    for name,r in m['files'].items():
        _check(r.get('path')==name,'observed color file identity differs');verified_file(root,r)
    b=read_json(root/'binding.json');w=read_json(root/'worker_metrics.json')
    _check(b.get('schema')=='nav_sg_rgbd_color_binding_v1' and b.get('input_kind')=='RECORDED_RGBD_K_POSE' and
        b.get('training_ready') is False,'recorded RGB-D binding required')
    for key in ('scene_id','source_sha256','world_frame','voxel_leaf_m','projection_provider'):_check(m.get(key)==b.get(key),'observed/binding identity differs')
    _check(type(m.get('frame_id')) is int and type(m.get('timestamp_ns')) is int and m['timestamp_ns']>0 and
        type(m.get('point_count')) is int and 0<m['point_count']<=5_000_000,'invalid observed point/frame budget')
    last=check_worker(w,b,m['frame_id'],m['timestamp_ns'])
    _check(last==m.get('last_integrated_input'),'observed manifest differs from full native trace')
    t=m['snapshot_timing'];_check(t.get('success') is True and t.get('prescan_initialized') is False and
        t.get('last_integrated_stamp_ns')==m['timestamp_ns'] and t.get('points')==m['point_count'],'observed snapshot timing/current stamp differs')
    return m,b,w


def verify_inputs(inputs, *, verify_recorded=True):
    _check(inputs.get('schema')=='g2_observed_color_inputs_v1' and inputs.get('training_ready') is False,
        'explicit source-GT/observed-color inputs required')
    files={k:_same_file(v) for k,v in inputs['files'].items()}
    _check(set(files)=={'native_manifest','grid','objects','color_manifest'},'observed input inventory differs')
    for name,expected in PREFIX_PINNED.items():
        _check(digest(Path(inputs['nav_repo'])/name)==expected,'native recorded verifier dependency differs: '+name)
    producer,verifier=_native_modules(inputs['nav_repo']);native=read_json(files['native_manifest'])
    _check(files['native_manifest']==files['grid'].parent/'manifest.json','actual GT export manifest required')
    verifier.verify(files['grid'],files['objects'],verify_sources=True)
    m,b,w=check_color(files['color_manifest'].parent)
    _check(m['scene_id']==native['scene_id'] and m['frame_id']==native['state']['frame_id'] and
        b['geometry_context_source_sha256']==native['source_sha256'] and
        b['model_source_sha256']==native['source_identity']['model_source_sha256'],'RGB-D and source-GT context differ')
    nav=read_json(_same_file(b['navigation_manifest']))
    _check(nav['source_sha256']==m['source_sha256'] and nav['scene_id']==native['scene_id'] and
        nav['source_identity']['model_source_sha256']==native['source_identity']['model_source_sha256'] and
        nav['state']['file_sha256']==native['state']['file_sha256'],'navigation and GT must share exact model/state archive')
    context=read_json(_same_file(b['geometry_context_manifest']))
    _check(context['source_sha256']==native['source_sha256'],'geometry context differs from bound source')
    identity=native['source_identity']
    for key in ('metadata','ep_meta','known_region'):
        r=native.get('auxiliary_sources',{}).get(key)
        _check((read_json(r['path']) if r else None)==identity.get(key),'actual GT auxiliary source differs')
    roots=[r for r in native['sources'] if r['logical_id']=='root.xml'];_check(len(roots)==1,'unique source root required')
    import mujoco
    _check(identity.get('mujoco_version')==mujoco.__version__,'actual MuJoCo compiler differs')
    model,sources=producer.load_model(roots[0]['path'],sorted({str(Path(r['path']).parent) for r in native['sources']}))
    _check(producer.model_source_hash(sources)==identity['model_source_sha256'],'actual model closure differs')
    data,state=producer.apply_state(model,native['state']['path'],m['frame_id'],native['state']['format'])
    _check(state==native['state'],'actual source state differs')
    far=producer.Grid((1,1,1),(1e8,1e8,1e8),identity['grid']['resolution'])
    _,entities,_,_=producer.extract(model,data,far,identity['metadata'],None,identity['geometry'])
    _check(entities==native['entities'],'actual GT entity geometry differs')
    # A proof can establish path-only derivation, never historical asset versions.
    proof_path=_same_file(inputs['model_rebinding_proof'])
    from g2.sim.model_rebinding import verify
    original=b.get('recorded_original_sources',[])
    if isinstance(original,dict):original=list(original.values())
    models=[r for r in original if isinstance(r,dict) and Path(r.get('path',r.get('file',''))).name.endswith('model.xml.gz')]
    _check(len(models)==1,'RGB-D cache must retain its original compressed Episode model')
    verify(proof_path,recorded_model_sha256=models[0]['sha256'])
    proof=read_json(proof_path);row={r['frame_id']:r for r in proof['frames']}.get(m['frame_id'])
    _check(proof['model_source_sha256']==identity['model_source_sha256'] and proof['states']['sha256']==state['file_sha256'] and
        proof['ep_meta']['sha256']==native['auxiliary_sources']['ep_meta']['sha256'] and row is not None and
        row['state_row_sha256']==state['row_sha256'] and row['timestamp']==state['timestamp'],
        'recorded Episode/model/state derivation differs')
    if verify_recorded:
        helper=_same_file(inputs['recorded_verifier'])
        _check(helper==Path(inputs['nav_repo']).resolve()/'g2/offline/color_ab.py','actual repository recorded verifier required')
        # Import only this reviewed, pinned native package under an isolated name;
        # never execute an interpreter/command supplied by an input artifact.
        import importlib.util
        import types
        package='_g2_recorded_native'
        for name,directory in ((package,Path(inputs['nav_repo'])/'g2'),(package+'.offline',Path(inputs['nav_repo'])/'g2/offline')):
            module=types.ModuleType(name);module.__path__=[str(directory)];sys.modules[name]=module
        spec=importlib.util.spec_from_file_location(package+'.offline.color_ab',helper)
        module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
        module.verify_binding(files['color_manifest'].parent/'binding.json',m['frame_id'])
    return native,m,b,w


def wire(inputs,n,m):
    values=[('scene_id',n['scene_id']),('source_sha256',n['source_sha256']),('frame_id',str(m['frame_id'])),
        ('world_frame',m['world_frame']),('native_manifest_file',inputs['files']['native_manifest']['path']),
        ('native_manifest_sha256',inputs['files']['native_manifest']['sha256']),('grid_sha256',inputs['files']['grid']['sha256']),
        ('objects_sha256',inputs['files']['objects']['sha256']),('cloud_sha256',m['files']['observed_colors.txt']['sha256']),
        ('timestamp_ns',str(round(n['state']['timestamp']*1e9))),('observed_color_manifest_sha256',inputs['files']['color_manifest']['sha256']),
        ('observed_color_binding_sha256',m['files']['binding.json']['sha256']),('observed_color_metrics_sha256',m['files']['worker_metrics.json']['sha256'])]
    _check(not any(any(ord(c)<32 for c in str(v)) for _,v in values),'control character in observed source proof')
    return 'NAV_SG_FULL_MAP_SOURCE_V2\n'+''.join(k+' '+json.dumps(v)+'\n' for k,v in values)


def prepare(native_manifest,color_manifest,*,nav_repo,ros_python,model_rebinding_proof,output,room_source='gvd',min_z=.15,max_z=1.8):
    ng=Path(native_manifest).resolve();pc=Path(color_manifest).resolve();repo=Path(nav_repo).resolve()
    out=new_output(output,[ng.parent,pc.parent,repo,model_rebinding_proof])
    inputs={'schema':'g2_observed_color_inputs_v1','nav_repo':str(repo),'ros_python':str(Path(ros_python).resolve()),
        'model_rebinding_proof':_file(model_rebinding_proof),'recorded_verifier':_file(repo/'g2/offline/color_ab.py'),
        'files':{k:_file(p) for k,p in {'native_manifest':ng,'grid':ng.parent/'grid.txt','objects':ng.parent/'objects.txt','color_manifest':pc}.items()},
        'training_ready':False}
    n,m,_,_=verify_inputs(inputs)
    binding=read_json(pc.parent/'binding.json')
    new_output(out,[Path(r['path']).parent for r in n['sources']]+[n['state']['path'],
        binding['dataset_root'],binding['rgb_root'],Path(model_rebinding_proof).parent])
    plan={'schema':'g2_observed_color_plan_v1','status':'PLAN_ONLY_NOT_EXECUTED','cwd':str(repo),
        'argv':['bash','g2/gt/native_gate.sh',str(ng.parent/'grid.txt'),str(ng.parent/'objects.txt'),str(out/'native_run'),room_source],
        'environment':{'G2_GT_FULL_MAP_FRAME0_PROOF':str(out/'source_proof.txt'),
            'G2_GT_PRESCAN_FRAME0':str(pc.parent/'observed_colors.txt'),'G2_GT_OBSERVED_COLOR_MANIFEST':str(pc),
            'G2_GT_EXPORT_SPATIAL':'true','G2_GT_MIN_ASSIGNED':'0','G2_GT_PROJECTION_MIN_Z':str(min_z),'G2_GT_PROJECTION_MAX_Z':str(max_z)},
        'source_gt_geometry':True,'model_observation':False,'training_ready':False}
    out.mkdir(parents=True);write_json(out/'source_inputs.json',inputs);(out/'source_proof.txt').write_text(wire(inputs,n,m));write_json(out/'plan.json',plan)
    return plan


def check_snapshot(directory,s,inputs,proof):
    from .snapshot import validate_snapshot,_read_native_grid,iter_surfaces
    from .surface_ownership import SurfaceOwnerVerifier
    validate_snapshot(s);n,m,b,w=verify_inputs(inputs)
    _check(proof.read_text()==wire(inputs,n,m),'source proof substituted')
    expected={'kind':'NATIVE_RGBD_FUSION_ONLY','geometry_is_source_gt':True,'model_observation':False,
        'navigation_source_sha256':m['source_sha256'],'manifest_sha256':inputs['files']['color_manifest']['sha256'],
        'binding_sha256':m['files']['binding.json']['sha256'],'worker_metrics_sha256':m['files']['worker_metrics.json']['sha256'],
        'timestamp_ns':m['timestamp_ns'],'frame_id':m['frame_id'],'voxel_leaf_m':m['voxel_leaf_m'],
        'native_build_source_sha256':m['native_build_source_sha256'],'prescan_initialized':False}
    _check(s.get('color_observation')==expected and s['surface_color_source']=='NATIVE_RGBD_FUSION_ONLY' and
        s['source_mode']=='full_map_mujoco_source' and s['source_sha256']==n['source_sha256'] and
        s['scene_id']==n['scene_id'] and s['frame_id']==m['frame_id'] and s['world_frame']==m['world_frame'] and
        s['timestamp_ns']==round(n['state']['timestamp']*1e9) and s['color_voxel_leaf']==m['voxel_leaf_m'] and
        s['full_map_source']['native_manifest_sha256']==inputs['files']['native_manifest']['sha256'] and
        s['full_map_source']['source_proof_sha256']==digest(proof) and s['native_build_source_sha256']==m['native_build_source_sha256'],
        'native GT/RGB-D identities or distinct clock evidence differ')
    g=s['grid'];_check(g['dimensions']==n['grid']['dims'] and g['origin']==n['grid']['origin'] and g['resolution']==n['grid']['resolution'],
        'source-GT grid parameters changed')
    _check(_read_native_grid(s,directory/'grid_states.raw')==(Path(inputs['files']['grid']['path']).parent/'occupancy.raw').read_bytes(),
        'source-GT grid states changed')
    original={(e['instance_id'],e['part_id']):e for e in n['entities']}
    current={(e['source_instance_id'],e['source_part_id']):e for e in s['entities']}
    _check(len(current)==len(s['entities']) and set(current)==set(original),'source-GT entity roster changed')
    for key,e in current.items():
        for a,c in {'kind':'kind','geometry_sha256':'geometry_sha256','vertices':'vertices','triangles':'triangles',
            'bbox_min':'bounds_min','bbox_max':'bounds_max','source_category_id':'category_id','source_joint_id':'joint_id'}.items():
            _check(e[a]==original[key][c],'source-GT mesh/identity changed: '+a)
    check=SurfaceOwnerVerifier(s['entities'],s['color_voxel_leaf']*.9);count=0;positions=[];owners=[]
    cloud=Path(inputs['files']['color_manifest']['path']).parent/'observed_colors.txt'
    with cloud.open() as stream:
        header=[shlex.split(next(stream)) for _ in range(7)]
        _check(header==[['NAV_SG_PRECOLORED_CLOUD_V1'],['scene_id',m['scene_id']],['source_sha256',m['source_sha256']],
            ['frame_id',str(m['frame_id'])],['world_frame',m['world_frame']],['points',str(m['point_count'])],['data']],
            'observed color cloud header differs')
        for row in iter_surfaces(directory/'surfaces.csv',{e['id'] for e in s['entities']}):
            fields=next(stream).split();xyz=np.array([float(x) for x in fields[:3]],dtype=np.float32).astype(float)
            _check(len(fields)==7 and fields[6]=='1' and np.allclose(row[:3],xyz,atol=1e-7,rtol=1e-9) and
                tuple(row[3:7])==tuple(int(x) for x in fields[3:]),'native observed surface XYZ/RGB/mask changed')
            positions.append(xyz);owners.append(row[7]);count+=1
            if len(positions)==4096:check.verify(positions,owners);positions=[];owners=[]
        _check(not stream.read().strip() and count==m['point_count'],'native observed surface count differs')
    if positions:check.verify(positions,owners)
    return count


def capture(native_directory,prepared,output,expected_build_source_sha256=None):
    from .snapshot import validate_snapshot
    directory=Path(native_directory).resolve();prepared=Path(prepared).resolve();inputs=read_json(prepared/'source_inputs.json')
    s=validate_snapshot(read_json(directory/'snapshot.json'));out=new_output(output,[directory,prepared])
    if expected_build_source_sha256:_check(s['native_build_source_sha256']==sha(expected_build_source_sha256),'native build differs')
    _check((directory/'SNAPSHOT_COMPLETE').read_text()=='nav_sg_spatial_snapshot_v1\n','incomplete native snapshot')
    count=check_snapshot(directory,s,inputs,prepared/'source_proof.txt')
    pc=Path(inputs['files']['color_manifest']['path']).parent
    source_native=read_json(inputs['files']['native_manifest']['path']);binding=read_json(pc/'binding.json')
    new_output(out,[Path(r['path']).parent for r in source_native['sources']]+[source_native['state']['path'],
        binding['dataset_root'],binding['rgb_root'],Path(inputs['model_rebinding_proof']['path']).parent])
    sources={name:directory/name for name in NATIVE_FILES}
    sources.update({'source_inputs.json':prepared/'source_inputs.json','source_proof.txt':prepared/'source_proof.txt',
        'source_gt_manifest.json':Path(inputs['files']['native_manifest']['path']),'observed_manifest.json':pc/'manifest.json',
        'observed_binding.json':pc/'binding.json','observed_worker_metrics.json':pc/'worker_metrics.json',
        'observed_color_complete.txt':pc/'COLOR_OBSERVATION_COMPLETE'})
    new_output(out,[Path(r['path']).parent for r in inputs['files'].values()]);out.mkdir(parents=True)
    files={}
    for name,p in sources.items():
        shutil.copyfile(p,out/name);files[name]={'path':name,'sha256':digest(p),'bytes':p.stat().st_size}
    result={k:s[k] for k in ('scene_id','source_sha256','frame_id','timestamp_ns','world_frame','source_mode','native_build_source_sha256','geometry_source_mode')}
    result.update(schema='g2_native_bundle_v1',source_scope={'status':STATUS,'full_scene_source_certified':False},
        structural_stage='SOURCE_GT_NATIVE_ROOM_GRAPH',semantic_stage='MUJOCO_GT_SOURCE_NOT_MODEL_PREDICTIONS',
        observation_witness=None,native_structure_proof=None,training_ready=False,surface_points=count,files=files)
    result['version_sha256']=hashlib.sha256(canonical(result)).hexdigest();write_json(out/'bundle.json',result)
    (out/'BUNDLE_COMPLETE').write_text('SOURCE_BOUND_NATIVE_SNAPSHOT\n');return result


def verify_bundle(root,manifest):
    from .snapshot import validate_snapshot
    _check(manifest.get('schema')=='g2_native_bundle_v1' and manifest.get('source_scope')=={'status':STATUS,'full_scene_source_certified':False} and
        set(manifest.get('files',{}))==NATIVE_FILES|EVIDENCE and manifest.get('training_ready') is False and
        manifest.get('structural_stage')=='SOURCE_GT_NATIVE_ROOM_GRAPH' and manifest.get('semantic_stage')=='MUJOCO_GT_SOURCE_NOT_MODEL_PREDICTIONS' and
        manifest.get('observation_witness') is None and manifest.get('native_structure_proof') is None,'observed bundle cannot claim model/training acceptance')
    for name,r in manifest['files'].items():
        _check(r['path']==name,'observed sealed file differs');verified_file(root,r)
    inputs=read_json(root/'source_inputs.json');s=validate_snapshot(read_json(root/'snapshot.json'))
    for k in ('scene_id','source_sha256','frame_id','timestamp_ns','world_frame','source_mode','native_build_source_sha256','geometry_source_mode'):
        _check(manifest[k]==s[k],'observed bundle frame/source differs')
    copies={'source_gt_manifest.json':'native_manifest','observed_manifest.json':'color_manifest'}
    for name,k in copies.items():_check(digest(root/name)==inputs['files'][k]['sha256'],'observed source attachment differs')
    m=read_json(root/'observed_manifest.json')
    for name,key in (('observed_binding.json','binding.json'),('observed_worker_metrics.json','worker_metrics.json')):
        _check(digest(root/name)==m['files'][key]['sha256'],'observed evidence attachment differs')
    _check((root/'observed_color_complete.txt').read_text()=='SOURCE_BOUND_NATIVE_RGBD_COLOR_NOT_ACCEPTANCE\n','observed marker differs')
    _check(check_snapshot(root,s,inputs,root/'source_proof.txt')==manifest['surface_points'],'sealed observed surface count differs')
    return manifest,s


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('prepare')
    for key in ('native-manifest','color-manifest','nav-repo','ros-python','model-rebinding-proof','output'):q.add_argument('--'+key,required=True)
    q.add_argument('--room-source',choices=('gvd','esdf_grid'),default='gvd');q.add_argument('--min-z',type=float,default=.15);q.add_argument('--max-z',type=float,default=1.8)
    q=sub.add_parser('capture')
    for key in ('native-directory','prepared','output'):q.add_argument('--'+key,required=True)
    q.add_argument('--expected-build-source-sha256');a=vars(p.parse_args());cmd=a.pop('command')
    result=prepare(**a) if cmd=='prepare' else capture(**a);print(result.get('status',result.get('source_scope')))

if __name__=='__main__':main()
