"""Verify native connection/Room-reference certificates; never assign groups.

Room segmentation, component identities, affiliations and Island IDs must all
come from nav_sg. This verifier checks their supplied geometric certificates.
"""
import math

import numpy as np

from g2.io import ContractError

PROTOCOL='NATIVE_BBOX_OBJECT_ROOT_CONNECTIONS_V2'


def bbox_gap(a,b):
    return math.sqrt(sum(max(x-y,u-v,0.)**2 for x,y,u,v in
        zip(a['bbox_min'],b['bbox_max'],b['bbox_min'],a['bbox_max'])))


def _number(value):return type(value) in (int,float) and math.isfinite(value)


def verify_room_reference(s,room,by_id):
    f=room.get('reference_frame',{});axes=np.asarray(f.get('axes_world',[]),float)
    origin=np.asarray(f.get('origin_world',[]),float)
    if (axes.shape!=(3,3) or origin.shape!=(3,) or not np.isfinite(axes).all() or not np.isfinite(origin).all() or
            not np.allclose(axes@axes.T,np.eye(3),atol=1e-8,rtol=0) or
            not np.isclose(np.linalg.det(axes),1.,atol=1e-8,rtol=0) or
            not np.allclose(axes[2],[0,0,1],atol=1e-8,rtol=0) or
            not np.allclose(origin,[*room['center'][:2],0],atol=1e-8,rtol=0) or
            f.get('source_sha256')!=s['source_sha256'] or f.get('geometry_coordinates')!='world'):
        raise ContractError('native Room reference axes/source are invalid')
    walls=f.get('reference_wall_ids')
    if (not isinstance(walls,list) or len(set(walls))!=len(walls) or any(i not in by_id or
            by_id[i]['kind']!='wall' or room['uid'] not in by_id[i].get('adjacent_room_uids',[]) for i in walls)):
        raise ContractError('Room reference must use actual adjacent Wall entities')
    if set(walls)!={k for k,e in by_id.items() if e['kind']=='wall' and room['uid'] in e.get('adjacent_room_uids',[])}:
        raise ContractError('Room reference cannot omit an adjacent source Wall')
    if f.get('provenance')=='EXPLICIT_NATIVE_WORLD_GRID_REFERENCE':
        if not np.allclose(axes,np.eye(3),atol=1e-8,rtol=0):raise ContractError('configured world axes were changed')
    elif f.get('provenance')=='NATIVE_SOURCE_WALL_GEOMETRY_REFERENCE':
        candidates=[]
        for key in walls:
            vertices=np.asarray(by_id[key]['vertices'],float)
            if len(vertices)<3:continue
            centered=vertices[:,:2]-vertices[:,:2].mean(axis=0)
            values,vectors=np.linalg.eigh(centered.T@centered)
            if values[1]>0:candidates.append((values[1],vectors[:,1]))
        best=max((v[0] for v in candidates),default=0)
        if not any(abs(v-best)<=max(1e-8,best*1e-8) and abs(float(axis@axes[0,:2]))>=1-1e-8 for v,axis in candidates):
            raise ContractError('Room axes do not follow supplied source Wall geometry')
    else:raise ContractError('unknown native Room reference provenance')
    floor=room.get('floor_reference',{});up=room.get('ceiling_reference',{})
    floors=floor.get('source_entity_ids')
    if (not isinstance(floors,list) or len(set(floors))!=len(floors) or any(i not in by_id or
            by_id[i]['kind']!='floor' or room['uid'] not in by_id[i].get('adjacent_room_uids',[]) for i in floors) or
            floor.get('is_classification_height_cut') is not False):
        raise ContractError('floor display reference must retain real source/uncertainty')
    if set(floors)!={k for k,e in by_id.items() if e['kind']=='floor' and room['uid'] in e.get('adjacent_room_uids',[])}:
        raise ContractError('Room reference cannot omit an adjacent source Floor')
    expected=min((by_id[i]['bbox_max'][2] for i in floors),default=None)
    if floor.get('z_world')!=expected:raise ContractError('floor reference cannot be a Camera-Z classification line')
    ceiling=max((by_id[i]['bbox_max'][2] for i in walls),default=
        s['grid']['origin'][2]+s['grid']['dimensions'][2]*s['grid']['resolution'])
    provenance='SOURCE_WALL_TOP_REFERENCE_NOT_DETECTED_CEILING' if walls else 'CONFIGURED_GRID_UPPER_REFERENCE_NOT_DETECTED_CEILING'
    if (not _number(up.get('z_world')) or not math.isclose(up['z_world'],ceiling,abs_tol=1e-8,rel_tol=0) or
            up.get('source_entity_ids')!=walls or up.get('source_sha256')!=s['source_sha256'] or
            up.get('normal_world')!=[0,0,1] or up.get('is_detected_ceiling') is not False or
            up.get('is_classification_height_cut') is not False or up.get('provenance')!=provenance):
        raise ContractError('ceiling reference must be explicit and is not a detected-ceiling requirement')


def verify_connection_evidence(s):
    if 'connection_protocol' not in s:return None
    if s['connection_protocol']!=PROTOCOL:raise ContractError('unknown native object connection protocol')
    packet=s.get('connections',{});threshold=packet.get('threshold_m')
    if (not _number(threshold) or threshold<=0 or threshold!=s['connection_distance'] or
            packet.get('metric')!='WORLD_AABB_3D_EUCLIDEAN' or packet.get('comparison')!='STRICT_LESS_THAN' or
            packet.get('roots_are_endpoints_only') is not True or
            type(packet.get('closed_world_within_declared_snapshot')) is not bool):
        raise ContractError('native connection threshold/metric/relay contract differs')
    by_id={e['id']:e for e in s['entities']};objects={k:e for k,e in by_id.items() if e['kind']=='object'}
    roots={k:e for k,e in by_id.items() if e['kind']!='object'}
    if len(objects)>5000 or len(roots)>1000 or len(objects)*len(roots)>50000:
        raise ContractError('native root path certificate exceeds budget')
    if any(e.get('connection_relay_allowed') is not False for e in roots.values()):
        raise ContractError('structural roots must be endpoints, never relays')
    if any(e.get('connection_relay_allowed') is not False for e in objects.values()
           if e.get('source_category_id') in ('robot','auxiliary') or e.get('label')=='robot'):
        raise ContractError('robot/auxiliary must not relay object connections')
    for room in s['rooms']:
        if room.get('frame_axes')!='room_reference_axes':raise ContractError('new views require explicit native Room reference axes')
        verify_room_reference(s,room,by_id)
    eligible={k:e for k,e in objects.items() if e.get('connection_relay_allowed') is True and e['room_uid']>=0}
    if any(type(e.get('connection_relay_allowed')) is not bool for e in by_id.values()):
        raise ContractError('native relay eligibility must be explicit')
    if s['source_mode']=='perception':
        from g2.io import sha
        for e in objects.values():
            status=e.get('connection_role_status')
            if status not in ('UNKNOWN_NATIVE_IDENTITY_NO_RELAY','SOURCE_BOUND_NATIVE_OBJECT',
                    'SOURCE_BOUND_NATIVE_ROBOT_NO_RELAY','SOURCE_BOUND_NATIVE_AUXILIARY_NO_RELAY'):
                raise ContractError('normal objects require explicit native identity uncertainty')
            if e['connection_relay_allowed']!=(status=='SOURCE_BOUND_NATIVE_OBJECT'):
                raise ContractError('unknown/robot native identity cannot relay')
            if status!='UNKNOWN_NATIVE_IDENTITY_NO_RELAY':sha(e.get('connection_role_evidence_sha256'))
    components=packet.get('components');records=packet.get('objects')
    if not isinstance(components,list) or len(components)>5000 or not isinstance(records,list) or len(records)!=len(objects):
        raise ContractError('invalid native component/connection inventory')
    membership={};component_rows={}
    for c in components:
        members=c.get('members');key=c.get('id')
        if not isinstance(members,list) or not members or len(members)>5000 or len(set(members))!=len(members):
            raise ContractError('invalid native component members')
        if any(k not in eligible or k in membership for k in members):raise ContractError('native component includes root/robot/unassigned/duplicate')
        uid=eligible[members[0]]['room_uid']
        if any(eligible[k]['room_uid']!=uid for k in members):raise ContractError('native component crosses Room identities')
        if key!='component_'+str(uid)+'_'+min(members) or key in component_rows:raise ContractError('native component identity differs')
        component_rows[key]=members;membership.update({k:key for k in members})
    if set(membership)!=set(eligible):raise ContractError('native component certificate omits eligible objects')
    # Check the supplied partition against actual bbox edges. This does not
    # assign a component or Island: inconsistent producer IDs are rejected.
    keys=sorted(eligible);parent=list(range(len(keys)))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    if keys:
        lo=np.asarray([eligible[k]['bbox_min'] for k in keys]);hi=np.asarray([eligible[k]['bbox_max'] for k in keys])
        for start in range(0,len(keys),128):
            gaps=np.maximum(np.maximum(lo[start:start+128,None,:]-hi[None,:,:],lo[None,:,:]-hi[start:start+128,None,:]),0)
            near=np.linalg.norm(gaps,axis=2)<threshold
            for offset,other in zip(*np.nonzero(near)):
                i=start+int(offset);j=int(other)
                if j<=i or eligible[keys[i]]['room_uid']!=eligible[keys[j]]['room_uid']:continue
                if membership[keys[i]]!=membership[keys[j]]:raise ContractError('native component omits an actual object bbox edge')
                parent[find(j)]=find(i)
        indices={key:i for i,key in enumerate(keys)}
        for members in component_rows.values():
            if len({find(indices[k]) for k in members})!=1:raise ContractError('native component would relay through a structural root')
    indexed={}
    for record in records:
        key=record.get('entity_id')
        if key not in objects or key in indexed:raise ContractError('native object connection identity differs')
        indexed[key]=record
    known=packet['closed_world_within_declared_snapshot'];walls_known=all(e['triangles'] for e in roots.values() if e['kind']=='wall')
    if s['source_mode']=='perception':
        meta=s.get('native_structures',{})
        if known!=bool(meta.get('boundary_coverage_complete') and meta.get('known_object_height_coverage')):
            raise ContractError('native connection certainty exceeds observed structure coverage')
    complete=known and any(e['kind']=='floor' for e in roots.values()) and walls_known
    if s['affiliations_complete']!=bool(complete):raise ContractError('native complete-coverage/connection status differs')
    nodes_count=0
    for key,e in objects.items():
        record=indexed[key];paths=record.get('paths')
        if record.get('relay_allowed')!=e['connection_relay_allowed'] or record.get('component_id')!=membership.get(key):
            raise ContractError('native relay/component provenance differs')
        if not isinstance(paths,list) or len(paths)>len(roots):raise ContractError('invalid native root paths')
        reached=set()
        for path in paths:
            root=path.get('root_id');nodes=path.get('nodes');distances=path.get('distances_m')
            if (root not in roots or root in reached or key not in eligible or not isinstance(nodes,list) or
                    not 2<=len(nodes)<=len(eligible)+1 or len(set(nodes))!=len(nodes) or nodes[0]!=key or nodes[-1]!=root or
                    not isinstance(distances,list) or len(distances)!=len(nodes)-1 or any(n not in eligible for n in nodes[:-1])):
                raise ContractError('native path uses invalid or structural intermediate relay')
            nodes_count+=len(nodes)
            if nodes_count>1000000:raise ContractError('native path node budget exceeded')
            if any(membership[n]!=membership[key] for n in nodes[:-1]):raise ContractError('native path crosses object components')
            for a,b,d in zip(nodes,nodes[1:],distances):
                actual=bbox_gap(by_id[a],by_id[b])
                if not _number(d) or d<0 or not d<threshold or not actual<threshold or not math.isclose(d,actual,abs_tol=1e-9,rel_tol=1e-9):
                    raise ContractError('native path violates strict three-dimensional bbox distance')
            if path.get('kind')!=('DIRECT' if len(nodes)==2 else 'INDIRECT_OBJECT_CHAIN'):raise ContractError('native path kind differs')
            reached.add(root)
        expected_roots=set()
        if key in eligible:
            for root,r in roots.items():
                observed=(known or 'native_structure_evidence' in r) and (r['kind']=='floor' or bool(r['triangles']))
                if observed and any(bbox_gap(eligible[k],r)<threshold for k in component_rows[membership[key]]):expected_roots.add(root)
        if reached!=expected_roots or set(e['root_affiliations'])!=reached:raise ContractError('native root closure/affiliation certificate differs')
        floor='YES' if any(roots[r]['kind']=='floor' for r in reached) else 'NO' if complete and key in eligible else 'UNKNOWN'
        wall='YES' if any(roots[r]['kind']=='wall' for r in reached) else 'NO' if known and walls_known and key in eligible else 'UNKNOWN'
        if record.get('floor_state')!=floor or record.get('any_wall_state')!=wall:
            raise ContractError('unobserved Floor/Wall membership cannot be asserted absent')
        if e['floor_member']!=(floor=='YES') or e['upper_member']!=(floor=='NO'):
            raise ContractError('BEV/UP membership must follow Floor connection, not a height or Ceiling test')
        island='island_'+str(e['room_uid'])+'_'+min(component_rows[membership[key]]) if floor=='YES' and wall=='NO' else None
        if e.get('island_id')!=island:raise ContractError('native Island requires Floor YES and real Wall NO')
        rejected=record.get('rejected_or_unobserved_root_paths')
        if not isinstance(rejected,list) or {v.get('root_id') for v in rejected}!=set(roots)-reached or len(rejected)!=len(roots)-len(reached):
            raise ContractError('missing native rejected/uncertain root paths')
        for item in rejected:
            d=item.get('direct_bbox_gap_m');actual=bbox_gap(e,roots[item['root_id']])
            reason='NON_OBJECT_OR_ROBOT_RELAY_FORBIDDEN' if not e['connection_relay_allowed'] else 'NO_PATH_IN_DECLARED_OBJECT_GRAPH' if known else 'UNKNOWN_INCOMPLETE_OBSERVATIONS'
            if not _number(d) or not math.isclose(d,actual,abs_tol=1e-9,rel_tol=1e-9) or item.get('reason')!=reason:
                raise ContractError('native rejected path distance/uncertainty differs')
    examples=packet.get('rejected_structural_relays');near_roots=set();root_keys=sorted(roots)
    for i,a in enumerate(root_keys):
        for b in root_keys[i+1:]:
            if bbox_gap(roots[a],roots[b])<threshold:near_roots.add((a,b))
    if (not isinstance(examples,list) or len(examples)!=min(len(near_roots),10000) or
            packet.get('rejected_structural_relay_count')!=len(near_roots) or
            packet.get('rejected_structural_examples_complete')!=(len(examples)==len(near_roots))):
        raise ContractError('native forbidden structural relay inventory differs')
    seen=set()
    for item in examples:
        edge=tuple(sorted((item.get('source',''),item.get('target',''))))
        if edge not in near_roots or edge in seen or item.get('reason')!='STRUCTURAL_ROOT_RELAY_FORBIDDEN' or not _number(item.get('distance_m')) or not math.isclose(
                item['distance_m'],bbox_gap(roots[edge[0]],roots[edge[1]]),abs_tol=1e-9,rel_tol=1e-9):
            raise ContractError('native forbidden structural relay evidence differs')
        seen.add(edge)
    return {'protocol':PROTOCOL,'objects':len(objects),'components':len(components),'paths':sum(len(r['paths']) for r in records)}
