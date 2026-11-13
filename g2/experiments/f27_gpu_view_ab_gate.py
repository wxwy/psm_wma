"""Partial real-GPU A/B certificate: compare completed states with same marker recipe.
Never modify original accepted source; normalizer writes only under /tmp.
"""
from pathlib import Path
import json,hashlib,sys,collections
import numpy as np
from PIL import Image
from g2.io import write_json
from g2.views.direct_color import export_white_views
from g2.views.robot_pose_marker import MarkerAppearance,overlay_final_top_views

# Runtime paths are CLI arguments; no production server path is embedded.
BASE=None
CAND=None
NORMAL=None

def digest(f):
    with open(f,'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()
TIMING_KEYS={'projection_wall_ns','projection_cpu_ns','GPU_upload_dispatch_readback_s',
 'GPU_kernel_s','gpu_render_and_export_s','hit_and_material_s',
 'prepare_geometry_tiles_s','render_timing','actual_wall_s',
 'first_state_s','state_latency_p50_s','state_latency_p95_s',
 'state_wall_s','view_render_s','total_wall_s','dynamic_preplan_s',
 'stage_prepare_s','gpu_color_kernel_s','gpu_color_selection_wall_s',
 'gpu_source_first_upload_s','source_mesh_time_s','elapsed_s',
 'source_model_load_s','gpu_raster_time_s'}

def scrub(v):
 if isinstance(v,dict):
  return {k:scrub(x) for k,x in v.items() if k not in TIMING_KEYS}
 if isinstance(v,list):return [scrub(a) for a in v]
 return v

def normalized_baseline(s):
 target=NORMAL/s.name
 if not target.is_dir():
  assert not target.exists()
  target.mkdir(parents=True)
  (target/'g2_original_gpu').symlink_to((s/'g2_original_gpu').resolve())
  original=json.loads((s/'direct_color_views.json').read_text())
  rendered=json.loads((s/'g2_original_gpu/views.json').read_text())
  original['views']=export_white_views(rendered,s/'g2_original_gpu',target)
  pose=original['robot_pose_marker']['pose']
  original.pop('robot_pose_marker',None)
  write_json(target/'direct_color_views.json',original)
  overlay_final_top_views(target,pose,style='game_arrow',appearance=MarkerAppearance())
 return target

def main(expected,allow_partial):
 b={x.name:x for x in BASE.glob('state_*') if (x/'direct_color_views.json').is_file()}
 c={x.name:x for x in CAND.glob('state_*') if (x/'direct_color_views.json').is_file()}
 todo=[(b[k],c[k]) for k in sorted(set(b)&set(c))]
 assert todo,'No completed candidate states'
 assert expected>0 and expected==len(b),'original baseline state count differs'
 assert set(c)<=set(b),'candidate includes an unknown state identity'
 assert len(todo)<=expected
 if not allow_partial:
  assert len(todo)==expected,'full Episode gate cannot pass incomplete states'
 cnt=collections.Counter();issues=[]
 for old,new in todo:
  bn=normalized_baseline(old)
  aa={str(f.relative_to(old)):f for f in old.rglob('*') if f.is_file()}
  bb={str(f.relative_to(new)):f for f in new.rglob('*') if f.is_file()}
  if aa.keys()!=bb.keys():
   issues.append((old.name,'files',str(set(aa)^set(bb))))
   continue
  for rel,p in aa.items():
   q=bb[rel]
   if rel=='sixview/floor_top.png':
    if digest(bn/rel)!=digest(q):issues.append((old.name,rel,'MARKER_STYLE_NORMALIZED_MISMATCH'))
    cnt['final_marker_png_normalized_sha_equal']+=1
   elif p.suffix.lower()=='.png':
    if digest(p)!=digest(q):issues.append((old.name,rel,'PNG_SHA_DIFF'))
    cnt['raw_and_unmarked_png_sha_equal']+=1
   elif p.suffix.lower()=='.npz':
    with np.load(p,allow_pickle=False) as x,np.load(q,allow_pickle=False) as y:
     if set(x.files)!=set(y.files):issues.append((old.name,rel,'ARRAY_KEYS'))
     else:
      for key in x.files:
       a=np.asarray(x[key]);z=np.asarray(y[key])
       same=np.array_equal(a,z,equal_nan=True) if a.dtype.kind in 'fc' else np.array_equal(a,z)
       if not same:issues.append((old.name,rel,'ARRAY',key))
       cnt['npz_fields_equal']+=1
     cnt['npz_files']+=1
   elif p.suffix.lower()=='.json':
    if rel=='g2_original_gpu/views.json':
     x=scrub(json.loads(p.read_text()));y=scrub(json.loads(q.read_text()))
     x.pop('files',None);y.pop('files',None)
     if x!=y:issues.append((old.name,rel,'PREVIEW_INDEX'))
    elif rel=='direct_color_views.json':
     x=scrub(json.loads((bn/rel).read_text()))
     y=scrub(json.loads(q.read_text()))
     x["views"]=sorted(x["views"],key=lambda a:a["native_view"])
     y["views"]=sorted(y["views"],key=lambda a:a["native_view"])
     if x!=y:issues.append((old.name,rel,'COLOR_REPORT'))
    else:
     x=scrub(json.loads(p.read_text()));y=scrub(json.loads(q.read_text()))
     if x!=y:issues.append((old.name,rel,'SEMANTIC_JSON'))
     if rel.endswith('scene_graph.json') or rel.endswith('surface_registry.json'):
      if digest(p)!=digest(q):issues.append((old.name,rel,'SOURCE_SHA'))
      cnt['sg_registry_sha_equal']+=1
    cnt['semantic_json_equal']+=1
   else:
    if digest(p)!=digest(q):issues.append((old.name,rel,'OTHER_SHA'))
    cnt['other_files_sha_equal']+=1
  print('STATE_PARITY',old.name,'FILES',len(aa),flush=True)
 print('COUNTS',dict(cnt))
 print('MISMATCH_COUNT',len(issues))
 for x in issues[:20]:print('MISMATCH',x)
 if issues:raise SystemExit(1)
 print('REAL_GPU_A_B_'+('FULL_PASS' if len(todo)==expected else 'PARTIAL_PASS'),
       len(todo),'OF',expected,'STATES',flush=True)

if __name__=='__main__':
 import argparse
 import tempfile
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--baseline-f27',type=Path,required=True)
 parser.add_argument('--candidate-f27',type=Path,required=True)
 parser.add_argument('--expected-states',type=int,required=True)
 parser.add_argument('--allow-partial',action='store_true')
 args=parser.parse_args()
 BASE=args.baseline_f27.resolve(strict=True)
 CAND=args.candidate_f27.resolve(strict=True)
 assert (BASE/'episode_receipt.json').is_file(), 'accepted baseline receipt missing'
 br=json.loads((BASE/'episode_receipt.json').read_text())
 assert br.get('complete') and br.get('spatial_state_count')==args.expected_states
 candidate_receipt=CAND/'episode_receipt.json'
 if not args.allow_partial:
  assert candidate_receipt.is_file(), 'full GPU gate requires complete candidate episode receipt'
 if candidate_receipt.is_file():
  cr=json.loads(candidate_receipt.read_text())
  assert cr.get('complete') and cr.get('spatial_state_count')==args.expected_states
  assert cr.get('source_inputs_sha256')==br.get('source_inputs_sha256'), 'source input identity differs'
 with tempfile.TemporaryDirectory(prefix='g2-f27-ab-marker-') as td:
  NORMAL=Path(td)
  main(args.expected_states,args.allow_partial)

