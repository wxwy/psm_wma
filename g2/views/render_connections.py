"""Room-reference rendering of nav_sg V2 connection certificates.

All membership and Island identities are supplied by native nav_sg. Projection
directions and display planes do not classify objects or create physical walls.
"""
import hashlib
import html
import math
from pathlib import Path
import re

import numpy as np
from PIL import Image

from g2.io import ContractError,canonical,digest,new_output,write_json
from g2.nav_bridge.connections import verify_connection_evidence
from g2.nav_bridge.snapshot import iter_surfaces


def wall_directions(s,room):
    """Place actual adjacent wall meshes in four Room-frame direction slots."""
    axes=np.asarray(room['reference_frame']['axes_world']);origin=np.asarray(room['reference_frame']['origin_world'])
    result={key:[] for key in ('+X','-X','+Y','-Y')};evidence={};uncertain=[]
    for e in s['entities']:
        if e['kind']!='wall' or room['uid'] not in e.get('adjacent_room_uids',[]):continue
        vertices=(np.asarray(e['vertices'],float)-origin)@axes.T
        if len(vertices)<3 or not e['triangles']:uncertain.append(e['id']);continue
        xy=vertices[:,:2]-vertices[:,:2].mean(axis=0);values,vectors=np.linalg.eigh(xy.T@xy)
        if values[1]<=0:uncertain.append(e['id']);continue
        normal=vectors[:,0];dim=int(np.argmax(np.abs(normal)));center=vertices.mean(axis=0)
        if abs(center[dim])<1e-9:uncertain.append(e['id']);continue
        direction=('+' if center[dim]>0 else '-')+('X' if dim==0 else 'Y')
        result[direction].append(e['id']);evidence[e['id']]={'direction_room':direction,
            'horizontal_normal_room':normal.tolist(),'basis':'ACTUAL_ADJACENT_SOURCE_WALL_MESH'}
    return result,evidence,uncertain


def render_v2(root,manifest,s,output,*,meters_per_pixel=.05,reference_image=None):
    from .render import AXES,CARDINAL,rasterize
    verify_connection_evidence(s)
    if type(meters_per_pixel) not in (int,float) or not math.isfinite(meters_per_pixel) or meters_per_pixel<=0:
        raise ContractError('invalid view resolution')
    out=new_output(output,[root]+([reference_image] if reference_image else []))
    by_id={e['id']:e for e in s['entities']};numeric={name:i for i,name in enumerate(sorted(by_id))}
    records={r['entity_id']:r for r in s['connections']['objects']};n=manifest['surface_points']
    xyz=np.empty((n,3));rgb=np.empty((n,3),np.uint8);valid=np.empty(n,bool);owners=np.empty(n,np.int32);count=0
    for i,row in enumerate(iter_surfaces(root/'surfaces.csv',set(by_id))):
        if i>=n:raise ContractError('bundle surface count differs')
        xyz[i]=row[:3];rgb[i]=row[3:6];valid[i]=row[6];owners[i]=numeric.get(row[7],-1);count+=1
    if count!=n:raise ContractError('bundle surface count differs')
    out.mkdir(parents=True);views={};room_refs={};island_refs={};wall_evidence={}
    for room in s['rooms']:
        uid=room['uid'];axes=np.asarray(room['reference_frame']['axes_world']);origin=np.asarray(room['reference_frame']['origin_world'])
        points=(xyz-origin)@axes.T
        meshes=[(numeric[e['id']],((np.asarray(e['vertices'],float).reshape(-1,3)-origin)@axes.T).tolist(),e['triangles']) for e in s['entities']]
        room_objects={e['id'] for e in s['entities'] if e['kind']=='object' and e['room_uid']==uid}
        adjacent={e['id'] for e in s['entities'] if e['kind']!='object' and uid in e.get('adjacent_room_uids',[])}
        directions,proof,uncertain=wall_directions(s,room);wall_evidence[str(uid)]={'walls':proof,'unresolved_wall_direction_ids':uncertain}
        # A projection crop is not a wall or a geometric classifier.
        ids=room_objects|adjacent
        lo_world=np.min([by_id[k]['bbox_min'] for k in ids],axis=0) if ids else np.asarray(s['bounds_min'])
        hi_world=np.max([by_id[k]['bbox_max'] for k in ids],axis=0) if ids else np.asarray(s['bounds_max'])
        corners=np.asarray([[x,y,z] for x in (lo_world[0],hi_world[0]) for y in (lo_world[1],hi_world[1]) for z in (lo_world[2],hi_world[2])])
        bounds=(corners-origin)@axes.T;lo=bounds.min(axis=0);hi=bounds.max(axis=0)
        def emit(name,axis,members,low=lo,high=hi,boundary='not_applicable'):
            data=rasterize(points,rgb,valid,owners,{numeric[k] for k in members},low,high,axis,
                meters_per_pixel=meters_per_pixel,meshes=meshes,surface_tolerance=s['color_voxel_leaf']*.5+1e-7)
            image,mask,geom,depth,owner,meta=data;folder=out/name;folder.mkdir(parents=True)
            Image.fromarray(image).save(folder/'rgb.png');Image.fromarray(mask.astype(np.uint8)*255).save(folder/'color_valid.png')
            Image.fromarray(geom.astype(np.uint8)*255).save(folder/'geometry_valid.png')
            np.savez_compressed(folder/'geometry.npz',depth=depth.astype(np.float32),native_entity_index=owner)
            for key in ('right_world','up_world','forward_world'):meta[key]=(np.asarray(meta[key])@axes).tolist()
            meta.update(coordinate_frame='NATIVE_ROOM_REFERENCE',reference_frame=room['reference_frame'],
                uv_min_room=meta.pop('uv_min_world'),room_bounds_min=meta.pop('world_bounds_min'),
                room_bounds_max=meta.pop('world_bounds_max'),depth_kind='signed_room_dot_forward',
                color_support=s.get('surface_color_source','NATIVE_COLOR_MAP_AND_OBJECT_GEOMETRY'),
                native_entity_ids=sorted(members),boundary_type=boundary,
                observed_color_pixels=int(mask.sum()),known_geometry_pixels=int(geom.sum()),
                status=boundary if not members else 'SOURCE_BOUND_PARTIAL_SURFACES',
                unassigned_points_excluded=int(np.count_nonzero(owners==-1)))
            write_json(folder/'view.json',meta);views[name]=meta
        bev={k for k in room_objects if records[k]['floor_state']=='YES'}|{k for k in adjacent if by_id[k]['kind']=='floor'}
        up={k for k in room_objects if records[k]['floor_state']=='NO'}
        prefix='rooms/'+str(uid);refs=[prefix+'/floor_top',prefix+'/upper_up']
        emit(refs[0],'floor_top',bev);emit(refs[1],'upper_up',up)
        for axis in CARDINAL:
            walls=set(directions[axis]);members=walls|{k for k in room_objects if walls.intersection(by_id[k]['root_affiliations'])}
            name=prefix+'/'+axis.replace('+','plus_').replace('-','minus_')
            boundary='PHYSICAL_SOURCE_WALL' if walls else 'OPEN_NO_SOURCE_WALL' if s['connections']['closed_world_within_declared_snapshot'] and not uncertain else 'UNKNOWN_WALL_OBSERVATION'
            emit(name,axis,members,boundary=boundary);refs.append(name)
        room_refs[str(uid)]={'views':refs,'reference_frame':room['reference_frame'],
            'floor_reference':room['floor_reference'],'ceiling_reference':room['ceiling_reference'],
            'unknown_floor_entity_ids':sorted(k for k in room_objects if records[k]['floor_state']=='UNKNOWN'),
            'islands':[]}
        supplied={by_id[k]['island_id'] for k in room_objects if by_id[k].get('island_id')}
        for island in sorted(supplied):
            if not re.fullmatch(r'island_[0-9]+_entity_[0-9]+',island):raise ContractError('unsafe native Island ID')
            members={k for k in room_objects if by_id[k].get('island_id')==island}
            vertices=np.asarray([[x,y,z] for k in members for x in (by_id[k]['bbox_min'][0],by_id[k]['bbox_max'][0])
                for y in (by_id[k]['bbox_min'][1],by_id[k]['bbox_max'][1]) for z in (by_id[k]['bbox_min'][2],by_id[k]['bbox_max'][2])])
            local=(vertices-origin)@axes.T;padding=max(meters_per_pixel,s['color_voxel_leaf']*.5+1e-7)
            record={'room_uid':uid,'member_entity_ids':sorted(members),'views':[],'native_id':island}
            for axis in CARDINAL:
                name=prefix+'/islands/'+island+'/'+axis.replace('+','plus_').replace('-','minus_')
                emit(name,axis,members,local.min(axis=0)-padding,local.max(axis=0)+padding);record['views'].append(name)
            island_refs[island]=record;room_refs[str(uid)]['islands'].append(island)
    full=s['source_mode']=='full_map_mujoco_source';oracle=s['source_mode']=='oracle_diagnostic'
    recipe={'schema':'g2_six_island_recipe_v2','connection_protocol':s['connection_protocol'],
        'meters_per_pixel':meters_per_pixel,'membership':'NATIVE_OBJECT_ONLY_PATH_CERTIFICATE',
        'bev':'FLOOR_YES','up':'FLOOR_NO_WITHOUT_CEILING_REQUIREMENT','unknown_floor':'EXCLUDED_AND_RECORDED',
        'wall_views':'ONLY_ACTUAL_WALL_ROOT_PATHS_IN_NATIVE_ROOM_REFERENCE','islands_in_room_cardinals':False,
        'reference_planes_are_height_classifiers':False,'occlusion':'NEAREST_SELECTED_SOURCE_GEOMETRY_WITH_INVALID_COLOR_MASK'}
    result={'schema':'g2_spatial_views_v2','status':'MUJOCO_FULL_MAP_GT_PENDING_HUMAN' if full else 'ORACLE_DIAGNOSTIC_ONLY' if oracle else
            'RECORDED_SPATIAL_PREVIEW' if s['affiliations_complete'] else 'PARTIAL_NATIVE_STRUCTURES',
        'source_mode':s['source_mode'],'source_scope':manifest['source_scope'],'scene_id':s['scene_id'],
        'source_sha256':s['source_sha256'],'frame_id':s['frame_id'],'native_bundle_version_sha256':manifest['version_sha256'],
        'entity_index_to_native_id':sorted(by_id),'native_entity_index_sentinels':{'background':-2,'unassigned_source':-1},
        'recipe':recipe,'recipe_sha256':hashlib.sha256(canonical(recipe)).hexdigest(),'room_six_refs':room_refs,
        'islands':island_refs,'wall_direction_evidence':wall_evidence,'views':views,'connections':s['connections'],
        'full_scene_source_certified':False,'training_ready':False,'temporal_video':False,'private_layout_human_gate':'PENDING',
        'reference_comparison':{'status':'NOT_PROVIDED'}}
    if not full and not oracle and s['geometry_source_mode']=='PRESCAN_PREBUILT':
        from g2.sim.source_scope import REVIEWED_SCOPE
        if manifest['source_scope'].get('status')!=REVIEWED_SCOPE:result['status']='BLOCKED_FULL_SCENE_SOURCE_REVIEW'
    if reference_image:
        path=Path(reference_image)
        if path.stat().st_size>32*1024*1024:raise ContractError('reference image exceeds budget')
        with Image.open(path) as image:image.verify()
        name='mujoco_reference'+path.suffix.lower();shutil_path=out/name
        import shutil
        shutil.copyfile(path,shutil_path)
        result['reference_comparison']={'status':'PROVIDED_NOT_HUMAN_APPROVED','file':name,'sha256':digest(shutil_path)}
    cards=''.join('<figure><figcaption>'+html.escape(name)+'</figcaption><img loading="lazy" src="'+html.escape(name)+'/rgb.png"></figure>' for name in views)
    reference=result['reference_comparison'].get('file');head='<h2>MuJoCo source reference</h2><img src="'+html.escape(reference)+'">' if reference else '<p>MuJoCo reference image not supplied. Human comparison pending.</p>'
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>G2 native spatial preview</title><style>body{font:16px sans-serif;background:#eee}main{display:flex;flex-wrap:wrap}figure{background:white;padding:12px}img{max-width:640px;image-rendering:pixelated}</style><h1>'+html.escape(result['status'])+'</h1><p>Source: '+html.escape(s['source_mode'])+'; frame '+str(s['frame_id'])+'. Training acceptance: false. <a href="views.json">Evidence</a></p>'+head+'<main>'+cards+'</main>',encoding='utf-8')
    result['files']={str(p.relative_to(out)):{'sha256':digest(p),'bytes':p.stat().st_size} for p in sorted(out.rglob('*')) if p.is_file()}
    write_json(out/'views.json',result);(out/'PREVIEW_COMPLETE').write_text('SPATIAL_VIEWS_NOT_TRAINING_ACCEPTANCE\n')
    return result
