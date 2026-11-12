"""Explicit source-GT preview through nav_sg's existing native GT backend.

This route needs no invented RGB-D/model observations. It replays the actual
MJCF/state entity geometry before accepting an existing native GT export, and
keeps source GT, sensor observations and human acceptance separate.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shutil
import sys

import numpy as np

from g2.io import ContractError, canonical, digest, new_output, read_json, sha, verified_file, write_json
from g2.sim.color_evidence import verify_color_evidence
from g2.sim.source_scope import audit_summary

STATUS='MUJOCO_FULL_MAP_GT_PENDING_HUMAN'
PINNED={'mujoco_scene.py':'d6495ed3a5bab351870508b22eb89ae22358034d7a564ec23aee16ea456eb550',
        'verify_export.py':'64b2bb8e25411700e406609242bfd0c0b2f7d69a6e614047e24915868a4ba276'}
NATIVE_FILES={'snapshot.json','surfaces.csv','grid_states.raw','SNAPSHOT_COMPLETE'}
EVIDENCE_FILES={'source_inputs.json','source_proof.txt','source_gt_manifest.json',
                'source_color_manifest.json','source_color_audit.npz'}


def _native_modules(repo):
    result=[]
    for file,expected in PINNED.items():
        path=Path(repo)/'g2/gt'/file
        if digest(path)!=expected:raise ContractError('Full Map source verifier version differs: '+file)
        name='_g2_full_map_'+file[:-3]
        spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
        sys.modules[name]=module;spec.loader.exec_module(module);result.append(module)
    return result


def _file(path):
    path=Path(path).resolve(strict=True)
    if not path.is_file() or path.stat().st_size>512*1024*1024:raise ContractError('source file exceeds bounded size')
    return {'path':str(path),'sha256':digest(path),'bytes':path.stat().st_size}


def _same_file(record):
    actual=_file(record['path'])
    if actual!=record:raise ContractError('Full Map source input changed')
    return Path(actual['path'])


def verify_inputs(inputs):
    if inputs.get('schema')!='g2_full_map_inputs_v1' or inputs.get('source_mode')!='FULL_MAP_MUJOCO_SOURCE':
        raise ContractError('explicit Full Map source inputs required')
    producer,verifier=_native_modules(inputs['nav_repo'])
    paths={key:_same_file(value) for key,value in inputs['files'].items()}
    if set(paths)!={'native_manifest','grid','objects','color_manifest','cloud','color_audit'}:
        raise ContractError('Full Map input inventory differs')
    verifier.verify(paths['grid'],paths['objects'],verify_sources=True)
    native=read_json(paths['native_manifest']);color=read_json(paths['color_manifest'])
    if paths['native_manifest']!=paths['grid'].parent/'manifest.json':
        raise ContractError('Full Map requires the source GT export manifest')
    if (color.get('schema')!='g2_prescan_manifest_v1' or color.get('status') not in ('COMPLETE','PARTIAL_COLOR') or
            color.get('completion_scope')!='DECLARED_VISUAL_GEOMS_ONLY' or color.get('training_ready') is not False or
            color.get('world_frame') not in ('world','map') or type(color.get('unclassified_geom_count')) is not int or
            color['unclassified_geom_count']!=0):
        raise ContractError('Full Map needs classified source color with original uncertainty')
    rows=color.get('geom_audit');n=color.get('compiled_geom_count')
    if (not isinstance(rows,list) or type(n) is not int or not rows or len(rows)!=n or
            [r.get('geom_id') for r in rows]!=list(range(n)) or len({r.get('geom_name') for r in rows})!=n):
        raise ContractError('Full Map requires every actual compiled geom identity')
    summary=audit_summary(rows)
    if (summary!=color.get('source_audit') or summary['role_counts'].get('UNCLASSIFIED',0) or
            hashlib.sha256(canonical(rows)).hexdigest()!=color.get('geom_audit_sha256')):
        raise ContractError('Full Map geom role audit is incomplete or inconsistent')
    marker=paths['color_manifest'].parent/'COMPLETE'
    if color['status']=='COMPLETE':
        if marker.read_text()!='VISUAL_SURFACE_EXPORT_ONLY\n':raise ContractError('missing color subset completion marker')
    elif marker.exists():raise ContractError('partial color must not carry COMPLETE')
    if (hashlib.sha256(canonical(color.get('source_identity'))).hexdigest()!=sha(color.get('visual_source_sha256')) or
            color.get('native_geometry_binding',{}).get('sha256')!=digest(paths['native_manifest']) or
            color.get('scene_id')!=native['scene_id'] or color.get('source_sha256')!=native['source_sha256'] or
            color.get('frame_id')!=native['state']['frame_id'] or type(color.get('frame_id')) is not int or
            color.get('state')!=native['state']):
        raise ContractError('Full Map visual/geometry source, state or frame differs')
    if verified_file(paths['color_manifest'].parent,color['file'])!=paths['cloud']:
        raise ContractError('Full Map cloud differs from source manifest')
    header=verifier.header(paths['cloud'],'NAV_SG_PRECOLORED_CLOUD_V1','data')
    if (header.get('scene_id')!=[color['scene_id']] or header.get('source_sha256')!=[color['source_sha256']] or
            header.get('frame_id')!=[str(color['frame_id'])] or header.get('world_frame')!=[color['world_frame']] or
            header.get('points')!=[str(color['point_count'])]):
        raise ContractError('Full Map actual cloud header differs')
    if verified_file(paths['color_manifest'].parent,color['color_audit_file'])!=paths['color_audit']:
        raise ContractError('Full Map point audit differs from source manifest')
    verify_color_evidence(paths['color_manifest'].parent,color,paths['cloud'])
    identity=native['source_identity'];roots=[r for r in native['sources'] if r['logical_id']=='root.xml']
    import mujoco
    if identity.get('mujoco_version')!=mujoco.__version__ or color['source_identity'].get('mujoco_version')!=mujoco.__version__:
        raise ContractError('Full Map actual MuJoCo compiler version differs')
    for key in ('metadata','ep_meta','known_region'):
        record=native.get('auxiliary_sources',{}).get(key)
        if (read_json(record['path']) if record else None)!=identity.get(key):
            raise ContractError('Full Map source identity differs from actual auxiliary source bytes')
    for key in ('metadata','ep_meta'):
        record=color.get('input_files',{}).get(key)
        if record:
            if digest(record['path'])!=record['sha256']:raise ContractError('Full Map color auxiliary source bytes changed')
        if (read_json(record['path']) if record else None)!=color['source_identity'].get(key):
            raise ContractError('Full Map visual source identity differs from original metadata/ep_meta')
    if len(roots)!=1:raise ContractError('unique original source root required')
    asset_roots=sorted({str(Path(r['path']).parent) for r in native['sources']})
    model,sources=producer.load_model(roots[0]['path'],asset_roots)
    closure=producer.model_source_hash(sources)
    if (closure!=identity['model_source_sha256'] or closure!=producer.model_source_hash(color.get('sources',[])) or
            closure!=color['source_identity'].get('model_source_sha256') or model.ngeom!=n):
        raise ContractError('Full Map actual compiled asset closure differs')
    state=native['state'];state_path=state.get('path') if state['format']!='mjcf_default' else None
    data,actual_state=producer.apply_state(model,state_path,state['frame_id'],state['format'])
    if actual_state!=state:raise ContractError('Full Map actual restored state differs')
    from g2.sim.prescan import geom_audit_row,geometry_type_names
    from g2.sim.source_roles import verify_embedded_role_evidence
    declared=color['source_identity'].get('metadata',{}).get('geoms',{})
    if set(declared)!={r['geom_name'] for r in rows} or summary['surface_points']!=color['point_count']:
        raise ContractError('Full Map full geom roster differs from source declarations')
    for row in rows:
        name=mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_GEOM,row['geom_id']) or 'geom_'+str(row['geom_id'])
        actual=geom_audit_row(model,data,row['geom_id'],name,declared[row['geom_name']],geometry_type_names(),color['source_identity'].get('ep_meta'))
        if any(row.get(k)!=v for k,v in actual.items() if k!='color_status'):
            raise ContractError('Full Map geom audit differs from actual compiled source/state/role')
        verify_embedded_role_evidence(color,row,declared[row['geom_name']])
    # Recompute source entities without voxelizing the entire room again. Room
    # segmentation remains solely native. Occupancy bytes retain their export
    # hashes, and still require GPT's independent server geometry review.
    far=producer.Grid((1,1,1),(1e8,1e8,1e8),identity['grid']['resolution'])
    _,entities,_,_=producer.extract(model,data,far,identity['metadata'],None,identity['geometry'])
    if entities!=native['entities']:raise ContractError('source GT entities differ from actual MuJoCo geometry')
    timestamp=state.get('timestamp')
    if type(timestamp) not in (int,float) or not math.isfinite(timestamp) or timestamp<0:
        raise ContractError('Full Map requires actual source state time')
    ep=native.get('auxiliary_sources',{}).get('ep_meta')
    if color.get('input_files',{}).get('ep_meta')!=ep:
        raise ContractError('Full Map official ep_meta binding differs')
    derivation=None
    if inputs.get('model_rebinding_proof'):
        from g2.sim.model_rebinding import verify
        proof=_same_file(inputs['model_rebinding_proof']);derivation=verify(proof,prescan=color)
    if inputs.get('training_ready') is not False:raise ContractError('Full Map is not training acceptance')
    return native,color,derivation


def _wire(inputs,native,color):
    values=[('scene_id',native['scene_id']),('source_sha256',native['source_sha256']),
            ('frame_id',str(native['state']['frame_id'])),('world_frame',color['world_frame']),
            ('native_manifest_file',inputs['files']['native_manifest']['path']),
            ('native_manifest_sha256',inputs['files']['native_manifest']['sha256']),
            ('grid_sha256',inputs['files']['grid']['sha256']),('objects_sha256',inputs['files']['objects']['sha256']),
            ('cloud_sha256',inputs['files']['cloud']['sha256']),('timestamp_ns',str(round(native['state']['timestamp']*1e9)))]
    if any(any(ord(c)<32 for c in str(value)) for _,value in values):raise ContractError('control character in source proof')
    return 'NAV_SG_FULL_MAP_SOURCE_V1\n'+''.join(key+' '+json.dumps(value,ensure_ascii=False)+'\n' for key,value in values)


def prepare(native_manifest,color_manifest,*,nav_repo,output,room_source='gvd',min_z=.15,max_z=1.8,
            model_rebinding_proof=None):
    if room_source not in ('gvd','esdf_grid') or not all(math.isfinite(v) for v in (min_z,max_z)) or min_z>=max_z:
        raise ContractError('invalid native Room/slab configuration')
    ng=Path(native_manifest).resolve();pc=Path(color_manifest).resolve()
    sources=[ng.parent,pc.parent,Path(nav_repo).resolve()]
    if model_rebinding_proof:sources.append(Path(model_rebinding_proof).resolve())
    out=new_output(output,sources)
    inputs={'schema':'g2_full_map_inputs_v1','source_mode':'FULL_MAP_MUJOCO_SOURCE','nav_repo':str(Path(nav_repo).resolve()),
        'files':{key:_file(path) for key,path in {'native_manifest':ng,'grid':ng.parent/'grid.txt',
            'objects':ng.parent/'objects.txt','color_manifest':pc,'cloud':pc.parent/'precolored.txt',
            'color_audit':pc.parent/'color_audit.npz'}.items()},'training_ready':False}
    if model_rebinding_proof:inputs['model_rebinding_proof']=_file(model_rebinding_proof)
    native,color,derivation=verify_inputs(inputs)
    # Include all original sources in output overlap checks, not just manifests.
    protected=[Path(r['path']).parent for r in native['sources']]
    protected += [Path(r['path']) for r in native.get('auxiliary_sources',{}).values()]
    if 'path' in native['state']:protected.append(native['state']['path'])
    new_output(out,protected)
    plan={'schema':'g2_full_map_plan_v1','status':'PLAN_ONLY_NOT_EXECUTED','source_mode':'FULL_MAP_MUJOCO_SOURCE',
        'source_scope':{'status':STATUS,'historical_model_derivation':derivation,
            'historical_generator_revision_certified':False,'full_scene_source_certified':False},
        'cwd':str(Path(nav_repo).resolve()),'argv':['bash','g2/gt/native_gate.sh',str(ng.parent/'grid.txt'),
            str(ng.parent/'objects.txt'),str(out/'native_run'),room_source],
        'environment':{'G2_GT_FULL_MAP_FRAME0_PROOF':str(out/'source_proof.txt'),
            'G2_GT_PRESCAN_FRAME0':str(pc.parent/'precolored.txt'),'G2_GT_EXPORT_SPATIAL':'true',
            'G2_GT_MIN_ASSIGNED':'0','G2_GT_PROJECTION_MIN_Z':str(min_z),'G2_GT_PROJECTION_MAX_Z':str(max_z)},
        'source_labels_are_native_detections':False,'training_ready':False,'human_gate':'PENDING'}
    out.mkdir(parents=True);write_json(out/'source_inputs.json',inputs)
    (out/'source_proof.txt').write_text(_wire(inputs,native,color),encoding='utf-8');write_json(out/'plan.json',plan)
    return plan


def _verify_snapshot(native_dir,s,inputs,proof):
    from .snapshot import iter_surfaces,validate_snapshot,_read_native_grid
    validate_snapshot(s);native,color,_=verify_inputs(inputs)
    if proof.read_text()!=_wire(inputs,native,color):raise ContractError('Full Map source proof cannot be resealed or substituted')
    if (s['source_mode']!='full_map_mujoco_source' or s['source_sha256']!=native['source_sha256'] or
            s['scene_id']!=native['scene_id'] or s['frame_id']!=native['state']['frame_id'] or
            s['world_frame']!=color['world_frame'] or s['timestamp_ns']!=round(native['state']['timestamp']*1e9) or
            s['full_map_source']['native_manifest_sha256']!=inputs['files']['native_manifest']['sha256'] or
            s['full_map_source']['source_proof_sha256']!=digest(proof) or s['color_voxel_leaf']!=.05):
        raise ContractError('native Full Map identity/source proof differs')
    g=s['grid'];expected=native['grid']
    if g['dimensions']!=expected['dims'] or g['origin']!=expected['origin'] or g['resolution']!=expected['resolution']:
        raise ContractError('Full Map native grid geometry differs')
    raw=_read_native_grid(s,native_dir/'grid_states.raw')
    if raw!=(Path(inputs['files']['grid']['path']).parent/'occupancy.raw').read_bytes():
        raise ContractError('Full Map native grid states differ from source export')
    original={(e['instance_id'],e['part_id']):e for e in native['entities']}
    current={(e['source_instance_id'],e['source_part_id']):e for e in s['entities']}
    if len(current)!=len(s['entities']) or set(original)!=set(current):raise ContractError('Full Map source entity inventory differs')
    for key,e in current.items():
        source=original[key]
        for k,v in {'kind':'kind','geometry_sha256':'geometry_sha256','vertices':'vertices','triangles':'triangles',
                    'bbox_min':'bounds_min','bbox_max':'bounds_max','source_category_id':'category_id',
                    'source_joint_id':'joint_id'}.items():
            if e[k]!=source[v]:raise ContractError('Full Map native geometry/source identity changed: '+k)
    from .surface_ownership import SurfaceOwnerVerifier
    owner_check=SurfaceOwnerVerifier(s['entities'],s['color_voxel_leaf']*.9)
    cloud=Path(inputs['files']['cloud']['path']);count=0;positions=[];owners=[]
    with cloud.open() as stream:
        for _ in range(7):next(stream)
        for row in iter_surfaces(native_dir/'surfaces.csv',{e['id'] for e in s['entities']}):
            fields=next(stream).split();xyz=np.asarray([float(x) for x in fields[:3]],dtype=np.float32).astype(float)
            if (not np.allclose(row[:3],xyz,atol=1e-7,rtol=1e-9) or
                    tuple(row[3:7])!=tuple(int(x) for x in fields[3:])):
                raise ContractError('Full Map surface RGB/invalid mask/XYZ row changed')
            count+=1
            positions.append(xyz);owners.append(row[7])
            if len(positions)==4096:owner_check.verify(positions,owners);positions=[];owners=[]
        if stream.read().strip() or count!=color['point_count']:raise ContractError('Full Map surface row count changed')
    if positions:owner_check.verify(positions,owners)
    return count


def capture(native_directory,prepared,output,*,expected_build_source_sha256=None):
    from .snapshot import validate_snapshot
    native_dir=Path(native_directory).resolve();prepared=Path(prepared).resolve()
    out=new_output(output,[native_dir,prepared]);inputs=read_json(prepared/'source_inputs.json')
    s=validate_snapshot(read_json(native_dir/'snapshot.json'))
    original=read_json(inputs['files']['native_manifest']['path'])
    new_output(out,[Path(r['path']).parent for r in original['sources']]+[
        Path(record['path']).parent for record in inputs['files'].values()])
    if expected_build_source_sha256 and s['native_build_source_sha256']!=sha(expected_build_source_sha256):
        raise ContractError('native build source mismatch')
    if (native_dir/'SNAPSHOT_COMPLETE').read_text()!='nav_sg_spatial_snapshot_v1\n':raise ContractError('incomplete native snapshot')
    count=_verify_snapshot(native_dir,s,inputs,prepared/'source_proof.txt')
    source={name:native_dir/name for name in NATIVE_FILES}
    source.update({'source_inputs.json':prepared/'source_inputs.json','source_proof.txt':prepared/'source_proof.txt',
        'source_gt_manifest.json':Path(inputs['files']['native_manifest']['path']),
        'source_color_manifest.json':Path(inputs['files']['color_manifest']['path']),
        'source_color_audit.npz':Path(inputs['files']['color_audit']['path'])})
    files={name:{'path':name,'bytes':p.stat().st_size,'sha256':digest(p)} for name,p in source.items()}
    out.mkdir(parents=True)
    for name,p in source.items():shutil.copyfile(p,out/name);verified_file(out,files[name])
    result={key:s[key] for key in ('scene_id','source_sha256','frame_id','timestamp_ns','world_frame',
        'source_mode','native_build_source_sha256','geometry_source_mode')}
    result.update(schema='g2_native_bundle_v1',source_scope={'status':STATUS,'full_scene_source_certified':False},
        semantic_stage='MUJOCO_GT_SOURCE_NOT_MODEL_PREDICTIONS',structural_stage='SOURCE_GT_NATIVE_ROOM_GRAPH',
        native_structure_proof=None,observation_witness=None,surface_points=count,files=files,training_ready=False)
    result['version_sha256']=hashlib.sha256(canonical(result)).hexdigest()
    write_json(out/'bundle.json',result)
    # _verify_snapshot already audited every original grid, point, color,
    # label and owner above. Each copied file was verified against the
    # ORIGINAL byte digest. Repeating the millions-of-points audit here adds
    # minutes but cannot strengthen an identical-byte source-bound copy.
    # External load_bundle/verify_bundle always retain their full deep audit.
    _verify_sealed_copy(out,result,source)
    (out/'BUNDLE_COMPLETE').write_text('SOURCE_BOUND_NATIVE_SNAPSHOT\n');return result


def _verify_sealed_copy(root, manifest, originals):
    """Seal copies of already fully audited source bytes without re-parsing them.

    Caller must have run _verify_snapshot on the source and checked each
    original's SHA before construction. Rejects changed copies and references.
    Never sets training_ready. Ordinary verify_bundle remains the deep API.
    """
    root=Path(root).resolve()
    if (manifest.get('schema')!='g2_native_bundle_v1' or
            manifest.get('source_scope')!={'status':STATUS,'full_scene_source_certified':False} or
            manifest.get('training_ready') is not False or
            manifest.get('structural_stage')!='SOURCE_GT_NATIVE_ROOM_GRAPH' or
            manifest.get('semantic_stage')!='MUJOCO_GT_SOURCE_NOT_MODEL_PREDICTIONS' or
            manifest.get('observation_witness') is not None or
            set(manifest.get('files',{}))!=NATIVE_FILES|EVIDENCE_FILES or
            set(originals)!=set(manifest['files'])):
        raise ContractError('invalid source-bound sealed copy manifest')
    sealed=dict(manifest)
    expected=sealed.pop('version_sha256',None)
    if expected!=hashlib.sha256(canonical(sealed)).hexdigest():
        raise ContractError('source bundle version digest differs')
    if read_json(root/'bundle.json')!=manifest:
        raise ContractError('source bundle manifest bytes changed')
    for name,original in originals.items():
        record=manifest['files'][name]
        if record.get('path')!=name or record['sha256']!=digest(original):
            raise ContractError('source attachment identity changed during copy')
        verified_file(root,record)
    s=read_json(root/'snapshot.json')
    for k in ('scene_id','source_sha256','frame_id','timestamp_ns','world_frame',
              'source_mode','native_build_source_sha256','geometry_source_mode'):
        if s.get(k)!=manifest.get(k):
            raise ContractError('source bundle copy snapshot identity changed')
    return True


def verify_bundle(root,manifest):
    from .snapshot import validate_snapshot
    if (manifest.get('schema')!='g2_native_bundle_v1' or
            manifest.get('source_scope')!={'status':STATUS,'full_scene_source_certified':False} or
            manifest.get('structural_stage')!='SOURCE_GT_NATIVE_ROOM_GRAPH' or manifest.get('native_structure_proof') is not None or
            set(manifest.get('files',{}))!=NATIVE_FILES|EVIDENCE_FILES or manifest.get('training_ready') is not False or
            manifest.get('observation_witness') is not None or manifest.get('semantic_stage')!='MUJOCO_GT_SOURCE_NOT_MODEL_PREDICTIONS' or
            manifest['source_scope'].get('full_scene_source_certified') is not False):
        raise ContractError('Full Map bundle cannot assert perception/training/source certification')
    for name,record in manifest['files'].items():
        if record.get('path')!=name:raise ContractError('Full Map file identity differs')
        verified_file(root,record)
    inputs=read_json(root/'source_inputs.json');s=validate_snapshot(read_json(root/'snapshot.json'))
    for key in ('scene_id','source_sha256','frame_id','timestamp_ns','world_frame','source_mode','native_build_source_sha256','geometry_source_mode'):
        if manifest[key]!=s[key]:raise ContractError('Full Map bundle source/frame differs')
    copies={'source_gt_manifest.json':'native_manifest','source_color_manifest.json':'color_manifest','source_color_audit.npz':'color_audit'}
    for name,key in copies.items():
        if digest(root/name)!=inputs['files'][key]['sha256']:raise ContractError('Full Map source attachment differs')
    if _verify_snapshot(root,s,inputs,root/'source_proof.txt')!=manifest['surface_points']:
        raise ContractError('Full Map sealed surface count differs')
    return manifest,s


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('prepare');a.add_argument('--native-manifest',required=True);a.add_argument('--color-manifest',required=True)
    a.add_argument('--nav-repo',required=True);a.add_argument('--output',required=True);a.add_argument('--model-rebinding-proof')
    a.add_argument('--room-source',choices=('gvd','esdf_grid'),default='gvd')
    a.add_argument('--min-z',type=float,default=.15);a.add_argument('--max-z',type=float,default=1.8)
    a=sub.add_parser('capture');a.add_argument('--native-directory',required=True);a.add_argument('--prepared',required=True)
    a.add_argument('--output',required=True);a.add_argument('--expected-build-source-sha256')
    args=vars(p.parse_args());command=args.pop('command')
    result=prepare(**args) if command=='prepare' else capture(**args)
    print(result.get('status',result.get('semantic_stage')))


if __name__=='__main__':main()
