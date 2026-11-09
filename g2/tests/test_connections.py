"""Own explicit native-wire certificates, not private scene acceptance."""
import copy
import csv
from pathlib import Path

import pytest

from g2.io import ContractError,write_json
from g2.nav_bridge.connections import bbox_gap,verify_connection_evidence
from g2.nav_bridge.snapshot import capture,validate_snapshot
from g2.views.render import render
from g2.views.render_connections import wall_directions

TRI=[[0,2,1],[1,2,3],[4,5,6],[5,7,6],[0,1,4],[1,5,4],[2,6,3],[3,6,7],[0,4,2],[2,4,6],[1,3,5],[3,7,5]]


def connection_case(*,floor=True,known=True):
    def box(i,kind,lo,hi):
        return {'id':'entity_'+str(i),'native_id':i,'kind':kind,'bbox_min':lo,'bbox_max':hi,
            'vertices':[[hi[a] if j&(1<<a) else lo[a] for a in range(3)] for j in range(8)],
            'triangles':copy.deepcopy(TRI),'room_uid':0 if kind=='object' else -1,'adjacent_room_uids':[0],
            'connection_relay_allowed':kind=='object' and i!=6,'root_affiliations':[],
            'floor_member':kind=='floor','upper_member':False,'island_id':None,'label':'robot' if i==6 else kind,
            'source_category_id':'robot' if i==6 else kind}
    entities=[box(0,'floor',[-2,-2,-.1],[2,2,0]),box(1,'wall',[-2,-2.1,0],[2,-2,3]),
        box(2,'object',[-.5,-.5,0],[.5,.5,.7]),box(3,'object',[-.1,-.1,.8],[.1,.1,1]),
        box(4,'object',[-.5,-1.9,1.5],[.5,-1.8,2]),box(5,'object',[1.3,1.3,0],[1.5,1.5,.3]),
        box(6,'object',[.7,.7,0],[1.1,1.1,.3]),box(7,'object',[-1.5,1.3,2],[-1.3,1.5,2.2])]
    if not floor:entities=entities[1:]
    by={e['id']:e for e in entities};roots={k:e for k,e in by.items() if e['kind']!='object'}
    components=[{'id':'component_0_entity_2','members':['entity_2','entity_3']}]
    components += [{'id':'component_0_entity_'+str(i),'members':['entity_'+str(i)]} for i in (4,5,7)]
    membership={k:c['id'] for c in components for k in c['members']}
    declared={2:[2,0],3:[3,2,0],4:[4,1],5:[5,0]};records=[]
    for i in range(2,8):
        key='entity_'+str(i);e=by[key];path=declared.get(i)
        if path and (not known or (path[-1]==0 and not floor)):path=None
        paths=[]
        if path:
            nodes=['entity_'+str(j) for j in path];root=nodes[-1]
            paths=[{'root_id':root,'kind':'DIRECT' if len(nodes)==2 else 'INDIRECT_OBJECT_CHAIN',
                'nodes':nodes,'distances_m':[bbox_gap(by[a],by[b]) for a,b in zip(nodes,nodes[1:])]}]
            e['root_affiliations']=[root]
        complete=known and floor
        fs='YES' if 'entity_0' in e['root_affiliations'] else 'NO' if complete and i!=6 else 'UNKNOWN'
        ws='YES' if 'entity_1' in e['root_affiliations'] else 'NO' if known and i!=6 else 'UNKNOWN'
        e.update(floor_member=fs=='YES',upper_member=fs=='NO')
        if fs=='YES' and ws=='NO':e['island_id']='island_0_'+('entity_2' if i in (2,3) else key)
        records.append({'entity_id':key,'component_id':membership.get(key),'relay_allowed':e['connection_relay_allowed'],
            'floor_state':fs,'any_wall_state':ws,'paths':paths,'rejected_or_unobserved_root_paths':[
                {'root_id':r,'direct_bbox_gap_m':bbox_gap(e,root),'reason':'NON_OBJECT_OR_ROBOT_RELAY_FORBIDDEN' if i==6 else
                    'NO_PATH_IN_DECLARED_OBJECT_GRAPH' if known else 'UNKNOWN_INCOMPLETE_OBSERVATIONS'}
                for r,root in roots.items() if r not in e['root_affiliations']]})
    s={'schema':'nav_sg_spatial_snapshot_v1','scene_id':'TEST_ONLY_CONNECTION_V2','source_sha256':'a'*64,
        'native_build_source_sha256':'b'*64,'frame_id':0,'timestamp_ns':0,'world_frame':'world',
        'completed_rgbd_observations':0,'last_rgbd_observation_timestamp_ns':0,'source_mode':'oracle_diagnostic',
        'geometry_source_mode':'ORACLE_GRID','object_frontend_status':'ORACLE_DIAGNOSTIC','color_voxel_leaf':.05,
        'bounds_min':[-3,-3,-1],'bounds_max':[3,3,4],'connection_distance':.3,'affiliations_complete':known and floor,
        'grid':{'origin':[-3,-3,-1],'resolution':1.,'dimensions':[6,6,5],'state_file':'grid_states.raw',
            'state_order':'xyz_z_fastest','states':{'unknown':0,'free':1,'occupied':2}},'structure_mode':'ORACLE_DIAGNOSTIC',
        'rooms':[{'uid':0,'center':[0,0,1],'frame_axes':'room_reference_axes',
            'reference_frame':{'origin_world':[0,0,0],'axes_world':[[1,0,0],[0,1,0],[0,0,1]],
                'source_sha256':'a'*64,'geometry_coordinates':'world','provenance':'NATIVE_SOURCE_WALL_GEOMETRY_REFERENCE',
                'reference_wall_ids':['entity_1']},
            'floor_reference':{'z_world':0 if floor else None,'source_entity_ids':['entity_0'] if floor else [],'is_classification_height_cut':False},
            'ceiling_reference':{'z_world':3,'normal_world':[0,0,1],'is_detected_ceiling':False,
                'is_classification_height_cut':False,'source_entity_ids':['entity_1'],'source_sha256':'a'*64,
                'provenance':'SOURCE_WALL_TOP_REFERENCE_NOT_DETECTED_CEILING'}}],
        'entities':entities,'relations':[],'surface_file':'surfaces.csv','connection_protocol':'NATIVE_BBOX_OBJECT_ROOT_CONNECTIONS_V2',
        'connections':{'metric':'WORLD_AABB_3D_EUCLIDEAN','comparison':'STRICT_LESS_THAN','threshold_m':.3,
            'roots_are_endpoints_only':True,'closed_world_within_declared_snapshot':known,'components':components,'objects':records,
            'rejected_structural_relays':[{'source':'entity_0','target':'entity_1','distance_m':0.,
                'reason':'STRUCTURAL_ROOT_RELAY_FORBIDDEN'}] if floor else [],
            'rejected_structural_relay_count':1 if floor else 0,'rejected_structural_examples_complete':True}}
    return s


@pytest.fixture
def native_connections(tmp_path):
    s=connection_case();native=tmp_path/'native';native.mkdir()
    write_json(native/'snapshot.json',s);(native/'grid_states.raw').write_bytes(bytes(180))
    (native/'SNAPSHOT_COMPLETE').write_text('nav_sg_spatial_snapshot_v1\n')
    with (native/'surfaces.csv').open('w') as stream:
        stream.write('x,y,z,red,green,blue,color_valid,entity_id\n')
        for e in s['entities']:
            for vertex in e['vertices']:stream.write(','.join(map(str,[*vertex,128,64,32,1,e['id']]))+'\n')
    return native,s


def test_object_only_paths_keep_floor_wall_and_up_independent():
    s=connection_case();validate_snapshot(s);result=verify_connection_evidence(s)
    assert result['components']==4
    by={e['id']:e for e in s['entities']}
    assert by['entity_3']['floor_member'] and by['entity_3']['island_id']=='island_0_entity_2'
    assert by['entity_4']['upper_member'] and not by['entity_4']['floor_member']
    assert by['entity_4']['root_affiliations']==['entity_1']
    assert by['entity_6']['island_id'] is None


@pytest.mark.parametrize('floor,known',[(False,True),(True,False),(False,False)])
def test_unobserved_floor_stays_unknown_without_a_ceiling_requirement(floor,known):
    s=connection_case(floor=floor,known=known);validate_snapshot(s)
    assert not any(e['upper_member'] or e['floor_member'] for e in s['entities'] if e['kind']=='object')


@pytest.mark.parametrize('fault',['structural_relay','distance_31','distance_30','fake_distance','robot_relay',
    'component_merge','component_split','floor_to_up','island_wall','fake_ceiling','wrong_room_axes','missing_rejection'])
def test_forged_connection_or_reference_certificates_are_rejected(fault):
    s=connection_case();rows=s['connections']['objects'];by={e['id']:e for e in s['entities']}
    if fault=='structural_relay':rows[2]['paths'][0]['nodes']=['entity_4','entity_1','entity_0']
    elif fault.startswith('distance_'):
        z=.31 if fault=='distance_31' else .30
        by['entity_5']['bbox_min'][2]=z;by['entity_5']['bbox_max'][2]=z+.1
        rows[3]['paths'][0]['distances_m']=[z]
    elif fault=='fake_distance':rows[1]['paths'][0]['distances_m'][0]=.01
    elif fault=='robot_relay':by['entity_6']['connection_relay_allowed']=True
    elif fault=='component_merge':s['connections']['components'][0]['members'].append('entity_5');s['connections']['components'].pop(2)
    elif fault=='component_split':s['connections']['components'][0]['members'].pop()
    elif fault=='floor_to_up':by['entity_3']['upper_member']=True
    elif fault=='island_wall':by['entity_4']['island_id']='island_0_entity_4'
    elif fault=='fake_ceiling':s['rooms'][0]['ceiling_reference']['is_detected_ceiling']=True
    elif fault=='wrong_room_axes':s['rooms'][0]['reference_frame']['axes_world']=[[0,1,0],[-1,0,0],[0,0,1]]
    else:rows[0]['rejected_or_unobserved_root_paths']=[]
    with pytest.raises(ContractError):validate_snapshot(s)


def test_029_floor_gap_is_connected_but_full_3d_031_is_not():
    s=connection_case();e=s['entities'][5];row=s['connections']['objects'][3]
    e['bbox_min'][2]=.29;e['bbox_max'][2]=.39;row['paths'][0]['distances_m']=[.29]
    validate_snapshot(s)
    assert bbox_gap({'bbox_min':[0,0,0],'bbox_max':[1,1,1]},
                    {'bbox_min':[1.2,1.2,1.2],'bbox_max':[2,2,2]})>.3


def test_non_axis_wall_uses_native_room_reference_without_world_axis_guess():
    import numpy as np
    s=connection_case();angle=.37;rotation=np.array([[np.cos(angle),-np.sin(angle),0],[np.sin(angle),np.cos(angle),0],[0,0,1]])
    # Rotation-specific projection test only: source mesh reference is verified
    # independently; this does not rewrite connection bbox distances.
    for e in s['entities']:
        e['vertices']=(np.asarray(e['vertices'])@rotation.T).tolist()
    room=s['rooms'][0];room['reference_frame']['axes_world']=rotation.T.tolist()
    from g2.nav_bridge.connections import verify_room_reference
    verify_room_reference(s,room,{e['id']:e for e in s['entities']})
    directions,_,unknown=wall_directions(s,room)
    assert directions['-Y']==['entity_1'] and not unknown


def test_new_six_views_keep_up_open_walls_and_room_islands_separate(native_connections,tmp_path):
    native,s=native_connections;capture(native,tmp_path/'bundle',allow_oracle_diagnostic=True)
    result=render(tmp_path/'bundle',tmp_path/'views',allow_oracle_diagnostic=True,meters_per_pixel=.2)
    assert result['schema']=='g2_spatial_views_v2' and len(result['room_six_refs']['0']['views'])==6
    assert len(result['islands'])==2 and len(result['views'])==14
    up=result['views']['rooms/0/upper_up']['native_entity_ids']
    assert up==['entity_4','entity_7']
    assert 'entity_4' not in result['views']['rooms/0/floor_top']['native_entity_ids']
    assert result['views']['rooms/0/plus_Y']['boundary_type']=='OPEN_NO_SOURCE_WALL'
    assert all('/islands/' in view for record in result['islands'].values() for view in record['views'])
    assert (tmp_path/'views/index.html').is_file() and result['training_ready'] is False
