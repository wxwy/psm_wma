"""Reproducible own MJCF -> actual native GT -> source-bound six-view smoke.

Run prepare in the G2 Python environment, execute the emitted plans in an
isolated native ROS overlay, then run collect. No private assets or GPU/model
inference are used. This is never Layout1/10 or human acceptance.
"""
import argparse
from pathlib import Path

import numpy as np

from g2.io import canonical,digest,read_json,write_json
from g2.nav_bridge.full_map import _native_modules,prepare,capture
from g2.sim.prescan import export as color_export
from g2.views.render import render
from g2.io import ContractError


def make_sources(output,nav_repo):
    output=Path(output);output.mkdir(parents=True,exist_ok=False);producer,_=_native_modules(nav_repo)
    plans=[]
    for shape in ('rectangular','notch'):
        root=output/shape;source=root/'source';source.mkdir(parents=True)
        geoms=[('floor','floor','0 0 -.05','2 1.5 .05','0.4 0.6 0.4 1'),
            ('south','wall','0 -1.6 1.5','2.1 .1 1.5','0.8 0.3 0.2 1'),
            ('north','wall','0 1.6 1.5','2.1 .1 1.5','0.2 0.3 0.8 1'),
            ('west','wall','-2.1 0 1.5','.1 1.5 1.5','0.6 0.6 0.6 1'),
            ('east','wall','2.1 0 1.5','.1 1.5 1.5','1 1 1 .5'),
            ('table','object','-.6 0 .35','.5 .4 .35','0.5 0.2 0.1 1'),
            ('cabinet','object','-.6 -1.35 1.8','.4 .1 .3','0.8 0.6 0.1 1'),
            ('island','object','1.1 .7 .15','.2 .2 .15','0.1 0.7 0.7 1')]
        if shape=='notch':geoms.append(('notch','wall','1.7 1.2 1.5','.3 .3 1.5','0.4 0.3 0.8 1'))
        dynamic='<body name="cup_body" pos="-.6 0 .82"><freejoint name="cup_joint"/><geom name="cup" type="box" size=".08 .08 .1" rgba=".7 .1 .7 1"/></body>'
        xml='<mujoco model="TEST_ONLY_F2_'+shape+'"><option gravity="0 0 0"/><worldbody>'+''.join(
            '<geom name="'+name+'" type="box" pos="'+pos+'" size="'+size+'" rgba="'+rgba+'"/>'
            for name,_,pos,size,rgba in geoms)+dynamic+'</worldbody></mujoco>'
        model_path=source/'scene.xml';model_path.write_text(xml);model,sources=producer.load_model(model_path)
        states=source/'states.npz';rows=np.repeat(model.qpos0[None,:],201,axis=0);rows[200,0]+=.15
        np.savez(states,qpos=rows,time=np.arange(201)*.01)
        ep=source/'ep_meta.json';write_json(ep,{'fixtures':{},'object_cfgs':[],'purpose':'OWN_TEST_ONLY'})
        binding={'model_source_sha256':producer.model_source_hash(sources),'states_sha256':digest(states)}
        scene='TEST_ONLY_F2_'+shape
        metadata={'schema':'nav_sg_gt_metadata_v1','scene_id':scene,'state_source':binding,'geoms':{}}
        for name,kind,*_ in geoms:
            metadata['geoms'][name]={'instance_id':name,'part_id':'whole','kind':kind,'category_id':kind}
        metadata['geoms']['cup']={'instance_id':'cup','part_id':'whole','kind':'object','category_id':'test_cup','joint_id':'cup_joint'}
        gt_meta=source/'gt_metadata.json';write_json(gt_meta,metadata)
        roles=source/'roles.json';write_json(roles,{'schema':'g2_sim_prescan_v1','scene_id':scene,'state_source':binding,
            'geoms':{name:{'role':'visual','source_kind':'mjcf','geom_name':name} for name in metadata['geoms']}})
        known=source/'known.json';regions=[{'type':'box','min':[-2,-1.5,0],'max':[2,1.5,3]}]
        write_json(known,{'schema':'nav_sg_known_region_v1','provenance':'OWN_TEST_ONLY_ANALYTIC_INTERIOR','regions':regions})
        for frame in (0,200):
            gt=root/('gt_'+str(frame));color=root/('color_'+str(frame));plan=root/('plan_'+str(frame))
            producer.export(model_path,gt_meta,gt,producer.Grid((44,34,34),(-2.2,-1.7,-.3),.1),
                states_path=states,frame=frame,known_region_path=known,ep_meta_path=ep)
            color_export(model_path,roles,color,states=states,frame=frame,spacing=.15,ep_meta=ep,
                native_manifest=gt/'manifest.json',world_frame='world',allow_partial_color=True)
            prepare(gt/'manifest.json',color/'manifest.json',nav_repo=nav_repo,output=plan,min_z=.15,max_z=1.8)
            plans.append(str(plan/'plan.json'))
    write_json(output/'plans.json',{'schema':'g2_own_full_map_smoke_v1','plans':plans,'private_layout_acceptance':False})
    return plans


def collect(output):
    output=Path(output);runs=[]
    for record in read_json(output/'plans.json')['plans']:
        path=Path(record);plan=read_json(path);native_root=Path(plan['argv'][4])
        frame=read_json(path.parent/'source_inputs.json')['files']['native_manifest']['path']
        frame_id=read_json(frame)['state']['frame_id'];native=native_root/('frame_'+str(frame_id))/'spatial_snapshot'
        artifacts=path.parent.parent/('collected_'+str(frame_id));bundle=artifacts/'bundle';preview=artifacts/'views'
        result=capture(native,path.parent,bundle)
        images=render(bundle,preview,allow_full_map_mujoco=True,meters_per_pixel=.08)
        snapshot=read_json(native/'snapshot.json');by_source={e['source_instance_id']:e for e in snapshot['entities']}
        assert by_source['table']['floor_member'] and by_source['cup']['floor_member']
        assert by_source['cabinet']['upper_member'] and not by_source['cabinet']['floor_member']
        assert by_source['cabinet']['root_affiliations']
        assert by_source['table']['island_id']
        # In the notch variant, that source block is .1m from the extra actual
        # Wall, so it correctly ceases to be an Island. A name is not a role.
        if 'notch' in by_source:assert by_source['island']['island_id'] is None
        else:assert by_source['island']['island_id']
        assert result['observation_witness'] is None and result['training_ready'] is False
        runs.append({'scene_id':snapshot['scene_id'],'frame_id':frame_id,'source_sha256':snapshot['source_sha256'],
            'native_build_source_sha256':snapshot['native_build_source_sha256'],'snapshot_sha256':digest(native/'snapshot.json'),
            'surfaces_sha256':digest(native/'surfaces.csv'),'points':result['surface_points'],
            'status':images['status'],'views':len(images['views']),'islands':len(images['islands']),
            'rooms':len(snapshot['rooms']),'reference_image':'NOT_SUPPLIED','training_ready':False})
    summary={'schema':'g2_own_full_map_smoke_result_v1','runs':runs,'private_layout_acceptance':False,'human_gate':'PENDING'}
    write_json(output/'author_summary.json',summary);return summary


def negative_bundles(output):
    """Resealed corrupt certificates must still fail against actual source."""
    import hashlib
    import shutil
    from g2.nav_bridge.snapshot import load_bundle
    from g2.nav_bridge.full_map import verify_inputs
    root=Path(output);source=root/'rectangular/collected_0/bundle';out=root/'negative_cases'
    out.mkdir(exist_ok=False);results=[]
    for fault in ('owner_swap','owner_drop','ambiguous_owner','scope_claim','structure_claim','structure_proof'):
        copy=out/fault;shutil.copytree(source,copy);manifest=read_json(copy/'bundle.json')
        if fault.startswith('owner') or fault=='ambiguous_owner':
            path=copy/'surfaces.csv';rows=path.read_text().splitlines();entities=read_json(copy/'snapshot.json')['entities']
            for i in range(1,len(rows)):
                fields=rows[i].split(',');old=fields[-1]
                if (old=='unknown')!=(fault=='ambiguous_owner'):continue
                fields[-1]='unknown' if fault=='owner_drop' else next(e['id'] for e in entities if e['id']!=old)
                rows[i]=','.join(fields);break
            else:raise AssertionError('own fixture needs both ambiguous and unique colors')
            path.write_text('\n'.join(rows)+'\n');manifest['files']['surfaces.csv'].update(bytes=path.stat().st_size,sha256=digest(path))
        elif fault=='scope_claim':manifest['source_scope']['invented_approved_role']='FULL_SCENE'
        elif fault=='structure_claim':manifest['structural_stage']='SENSOR_STRUCTURE_HUMAN_APPROVED'
        else:manifest['native_structure_proof']={'fake':True}
        manifest.pop('version_sha256');manifest['version_sha256']=hashlib.sha256(canonical(manifest)).hexdigest()
        write_json(copy/'bundle.json',manifest)
        try:load_bundle(copy)
        except ContractError as error:results.append({'case':fault,'status':'REJECTED','reason':str(error)})
        else:raise AssertionError('corrupt bundle accepted: '+fault)
    for fault in ('compiled_geom_position','original_role_metadata'):
        copy=out/fault;copy.mkdir();inputs=read_json(source/'source_inputs.json');color_root=copy/'colors';color_root.mkdir()
        for name,key in (('manifest.json','color_manifest'),('precolored.txt','cloud'),('color_audit.npz','color_audit')):
            shutil.copyfile(inputs['files'][key]['path'],color_root/name)
            inputs['files'][key].update(path=str(color_root/name))
        m=read_json(color_root/'manifest.json')
        if fault=='compiled_geom_position':
            m['geom_audit'][0]['world_position'][0]+=.1
            m['geom_audit_sha256']=hashlib.sha256(canonical(m['geom_audit'])).hexdigest()
        else:
            m['source_identity']['metadata']['geoms']['floor']['role']='collision'
            m['visual_source_sha256']=hashlib.sha256(canonical(m['source_identity'])).hexdigest()
        write_json(color_root/'manifest.json',m)
        inputs['files']['color_manifest'].update(sha256=digest(color_root/'manifest.json'),bytes=(color_root/'manifest.json').stat().st_size)
        try:verify_inputs(inputs)
        except ContractError as error:results.append({'case':fault,'status':'REJECTED','reason':str(error)})
        else:raise AssertionError('corrupt source accepted: '+fault)
    body={'schema':'g2_own_full_map_resealed_negatives_v1','results':results,'private_layout_acceptance':False}
    write_json(out/'summary.json',body);return body


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',choices=('prepare','collect','negative'))
    p.add_argument('--output',required=True);p.add_argument('--nav-repo');args=p.parse_args()
    result=make_sources(args.output,args.nav_repo) if args.stage=='prepare' else collect(args.output) if args.stage=='collect' else negative_bundles(args.output)
    print(len(result) if isinstance(result,list) else len(result.get('runs',result.get('results'))))


if __name__=='__main__':main()
