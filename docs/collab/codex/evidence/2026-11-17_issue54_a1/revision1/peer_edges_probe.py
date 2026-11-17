import copy
import json
import tempfile
from pathlib import Path
import numpy as np
from PIL import Image
from g2.io import digest, read_json, write_json
from g2.nav_bridge.connections import verify_connection_evidence
from g2.offline.atomic_6views_connections import compute
from g2.offline.output_profile import OutputProfile
from g2.offline.scene_view_event_index import SceneViewCursor
from g2.offline.stage_a import package_stage_a, validate_profile_episode
from g2.tests.test_stage_a_package import stage_case
from g2.views.render_connections import renderer_member_sets

root = Path(tempfile.mkdtemp(prefix='issue54_a1_peer_edges_', dir='/tmp'))
result = dict(root=str(root))

kwargs, _ = stage_case(root/'dimensions', OutputProfile(selection_top_variant='clean',marker_variants=False))
first=kwargs['rendered']/'state_000000_frame_000000'
image=first/'sixview/floor_top.png'
Image.new('RGB',(1,1),(230,220,210)).save(image)
for path in kwargs['rendered'].glob('state_*/direct_color_views.json'):
    report=read_json(path)
    for asset in report['views']:
        if asset['rgb_file']=='sixview/floor_top.png':asset['sha256']=digest(image)
    write_json(path,report)
target=root/'wrong_dimension_package'
manifest=package_stage_a(destination=target,**kwargs)
spatial=read_json(target/manifest['states'][0]['spatial_metadata'])
projection=spatial['views']['sixview/floor_top']['image_projection']
result['dimension_mismatch']=dict(actual_png_wh=list(Image.open(image).size),projection_wh=[projection['width_px'],projection['height_px']],profile_complete=manifest['profile_complete'],validator_accepts=validate_profile_episode(target)==manifest)

kwargs, snaps = stage_case(root/'disappearing_island', OutputProfile(selection_top_variant='clean'))
config=read_json(kwargs['inputs'])
plans=[]
for i,(row,base) in enumerate(zip(config['states'],snaps)):
    snapshot=copy.deepcopy(base)
    lift=.2998 if i==0 else .3002
    for entity in snapshot['entities']:
        if entity['id'] in ('entity_2','entity_3'):
            for field in ('bbox_min','bbox_max'):entity[field][2]+=lift
            for vertex in entity['vertices']:vertex[2]+=lift
    snapshot['connections'],snapshot['entities'],snapshot['affiliations_complete']=compute(snapshot['entities'],[0],connection_distance=snapshot['connection_distance'],known=True)
    verify_connection_evidence(snapshot)
    plans.append(renderer_member_sets(snapshot))
    for key in ('snapshot','scene_graph'):
        write_json(row[key]['path'],snapshot)
        row[key]['sha256']=digest(row[key]['path'])
write_json(kwargs['inputs'],config)
receipt_path=kwargs['rendered']/'episode_receipt.json'
receipt=read_json(receipt_path)
receipt['source_inputs_sha256']=digest(kwargs['inputs'])
write_json(receipt_path,receipt)
cursor=SceneViewCursor([11])
events=[]
for i,z in enumerate((.2998,.3002,.3002)):
    e=cursor.observe(i,i*10,np.array([[0.,0.,z]]),np.eye(3)[None],[.3 if i else 0.,0.,0.])
    events.append(dict(mode=e.mode,translation=e.object_translation_max_m))
try:
    package_stage_a(destination=root/'island_package',**kwargs)
    outcome=dict(accepted=True)
except Exception as exc:
    outcome=dict(accepted=False,error_type=type(exc).__name__,error=str(exc))
result['island_transition']=dict(connection_certificates_valid=True,initial_plan_has_island='rooms/0/islands/island_0_entity_2/plus_X' in plans[0],current_plan_has_island='rooms/0/islands/island_0_entity_2/plus_X' in plans[1],events=events,package=outcome)
(root/'probe.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
