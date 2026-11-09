"""Own four-frame RGB-D -> native color -> GT geometry/observed color smoke.

Prepare in the MuJoCo Python environment, execute color_plan in the ROS overlay,
then prepare-spatial, run its two native plans and collect. No private assets,
model inference, GPU, historical or human acceptance is supplied by this test.
"""
import argparse
import gzip
import hashlib
import importlib
from pathlib import Path
import sys
import types
import numpy as np
from g2.io import digest,read_json,write_json
from g2.nav_bridge.full_map import _native_modules,_file
from g2.nav_bridge.observed_color import prepare,capture
from g2.sim.model_rebinding import create
from g2.views.render import render


def native_package(repo):
    for name,p in (('_g2_recorded_native',Path(repo)/'g2'),('_g2_recorded_native.offline',Path(repo)/'g2/offline')):
        m=types.ModuleType(name);m.__path__=[str(p)];sys.modules[name]=m
    return importlib.import_module('_g2_recorded_native.offline.color_ab')


def make(output,nav_repo,base_params):
    root=Path(output).resolve();root.mkdir(parents=True,exist_ok=False);producer,_=_native_modules(nav_repo)
    helper=native_package(nav_repo);own=importlib.import_module('_g2_recorded_native.offline.native_structure_smoke')
    dataset,episode,_,_,_,_=own.write_inputs(root,False)
    # A known visual plane just in front of an analytic source object.
    for path in dataset.rglob('chunk_000000.npz'):
        with np.load(path,allow_pickle=False) as a:arrays={k:a[k] for k in a.files}
        arrays['depth'][:]=1426;np.savez_compressed(path,**arrays)
    src=root/'scene_sources';src.mkdir()
    geoms=[('floor','floor','2 1.5 -.05','2 1.5 .05'),('south','wall','2 -.05 1.5','2.1 .05 1.5'),
        ('north','wall','2 3.05 1.5','2.1 .05 1.5'),('west','wall','-.05 1.5 1.5','.05 1.5 1.5'),
        ('east','wall','4.05 1.5 1.5','.05 1.5 1.5'),('cabinet','object','2 2.626 1.5','.4 .2 .4')]
    xml='<mujoco model="TEST_ONLY_F3"><worldbody>'+''.join('<geom name="'+n+'" type="box" pos="'+pos+'" size="'+size+'"/>' for n,_,pos,size in geoms)+'</worldbody></mujoco>'
    model_path=src/'scene.xml';model_path.write_text(xml);original=src/'model.xml.gz';original.write_bytes(gzip.compress(xml.encode(),mtime=0))
    model,sources=producer.load_model(model_path);states=src/'states.npz';np.savez(states,qpos=np.zeros((4,0)),time=np.arange(4)*.1)
    ep=src/'ep_meta.json';write_json(ep,{'fixtures':{},'object_cfgs':[]})
    meta=src/'gt_metadata.json';write_json(meta,{'schema':'nav_sg_gt_metadata_v1','scene_id':'TEST_ONLY_F3',
        'state_source':{'model_source_sha256':producer.model_source_hash(sources),'states_sha256':digest(states)},
        'geoms':{n:{'instance_id':n,'part_id':'whole','kind':k,'category_id':k} for n,k,*_ in geoms}})
    known=src/'known.json';write_json(known,{'schema':'nav_sg_known_region_v1','provenance':'OWN_TEST_ONLY_ANALYTIC_INTERIOR',
        'regions':[{'type':'box','min':[0,0,0],'max':[4,3,3]}]})
    for frame in (0,3):producer.export(model_path,meta,root/('gt_'+str(frame)),producer.Grid((44,34,34),(-.2,-.2,-.3),.1),
        states_path=states,frame=frame,known_region_path=known,ep_meta_path=ep)
    create(original,model_path,root/'proof',path_prefixes=[],states=states,ep_meta=ep,frames=[0,3])
    cache=dataset/episode/'manifest.json';m=read_json(cache);m['identity']={'source_files':[{'path':str(p),'sha256':digest(p)} for p in (original,states,ep)]};write_json(cache,m)
    params=read_json(base_params);gt=read_json(root/'gt_0/manifest.json');params['map_ros'].update(prescan_grid_file=str(root/'gt_0/grid.txt'),
        prescan_cloud_file='',spatial_scene_id=gt['scene_id'],spatial_source_sha256=gt['source_sha256'])
    config=root/'base_params.json';write_json(config,params);m=params['map_ros'];rows,digests,_=helper.source_rows(dataset,episode,'robot0_agentview_left',dataset,4,m['depth_filter_mindist'],m['depth_filter_maxdist'],1000000000)
    plan_dir=root/'color_plan';plan_dir.mkdir();binding={'schema':'nav_sg_rgbd_color_binding_v1','input_kind':'RECORDED_RGBD_K_POSE',
        'scene_id':gt['scene_id'],'source_sha256':gt['source_sha256'],'world_frame':'world','voxel_leaf_m':.05,'projection_provider':'depth',
        'geometry_context_source_sha256':gt['source_sha256'],'model_source_sha256':gt['source_identity']['model_source_sha256'],
        'navigation_manifest':_file(root/'gt_0/manifest.json'),'geometry_context_manifest':_file(root/'gt_0/manifest.json'),
        'dataset_root':str(dataset),'rgb_root':str(dataset),'episode':episode,'camera':'robot0_agentview_left','frames':rows,
        'manifest_digests':digests,'recorded_original_sources':m.get('identity',{}).get('source_files',[]),
        'min_depth':params['map_ros']['depth_filter_mindist'],'max_depth':params['map_ros']['depth_filter_maxdist'],
        'stamp_start_ns':1000000000,'base_params':_file(config),'training_ready':False}
    binding['recorded_original_sources']=read_json(cache)['identity']['source_files'];write_json(plan_dir/'binding.json',binding)
    write_json(plan_dir/'plan.json',{'schema':'nav_sg_color_ab_plan_v1','bindings':{'0.05':_file(plan_dir/'binding.json')},
        'base_params':_file(config),'snapshot_frame_indices':[0,3],'requested_view_source_hz':1.,'frames':4,'scene_id':gt['scene_id']})
    return {'status':'OWN_TEST_ONLY_PREPARED'}


def prepare_spatial(output,nav_repo,ros_python):
    root=Path(output);plans=[]
    for frame in (0,3):
        target=root/('spatial_'+str(frame));plan=prepare(root/('gt_'+str(frame))/'manifest.json',root/'color_run/color_snapshots'/('frame_'+str(frame))/'manifest.json',
            nav_repo=nav_repo,ros_python=ros_python,model_rebinding_proof=root/'proof/rebinding.json',output=target,min_z=.15,max_z=1.8)
        plans.append(str(target/'plan.json'))
    write_json(root/'spatial_plans.json',{'plans':plans});return {'status':'OWN_TEST_ONLY_SPATIAL_PREPARED'}


def collect(output):
    root=Path(output);results=[]
    for frame in (0,3):
        plan=root/('spatial_'+str(frame));native=plan/'native_run'/('frame_'+str(frame))/'spatial_snapshot'
        bundle=root/('bundle_'+str(frame));views=root/('views_'+str(frame))
        b=capture(native,plan,bundle);v=render(bundle,views,allow_full_map_mujoco=True,meters_per_pixel=.02)
        s=read_json(bundle/'snapshot.json');assert s['surface_color_source']=='NATIVE_RGBD_FUSION_ONLY'
        assert s['color_observation']['model_observation'] is False and not s['completed_rgbd_observations']
        assert any(r['image_generated'] for r in v['views'].values()),'own observed wall object should project'
        for name,r in v['views'].items():assert (views/name/'rgb.png').exists()==r['image_generated']
        results.append({'frame_id':frame,'points':b['surface_points'],'generated_images':sum(x['image_generated'] for x in v['views'].values()),
            'native_build_source_sha256':s['native_build_source_sha256'],'training_ready':False})
    write_json(root/'summary.json',{'status':'OWN_TEST_ONLY_OBSERVED_GT_ROUNDTRIP_PASS','runs':results});return results


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('prepare','prepare-spatial','collect'))
    p.add_argument('--output',required=True);p.add_argument('--nav-repo');p.add_argument('--base-params');p.add_argument('--ros-python');a=p.parse_args()
    result=make(a.output,a.nav_repo,a.base_params) if a.command=='prepare' else prepare_spatial(a.output,a.nav_repo,a.ros_python) if a.command=='prepare-spatial' else collect(a.output)
    print(result)

if __name__=='__main__':main()
