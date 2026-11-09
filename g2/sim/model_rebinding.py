"""Replay gzip/XML path rebinding without editing either original model.

This proves a particular path-only derivation and current asset closure. It
does not certify historical generator versions or source semantic labels.
"""
import argparse
import copy
import hashlib
from pathlib import Path, PurePosixPath
import tempfile
import xml.etree.ElementTree as ET
import zipfile

import numpy as np

from g2.io import ContractError,canonical,digest,new_output,read_json,sha,write_json
from .source_geometry import apply_state,load_model,model_source_hash,xml_payload

SCHEMA='g2_mjcf_path_rebinding_proof_v1'
PATH_KEYS=('assetdir','meshdir','texturedir')
FILE_TAGS={'include','mesh','texture','hfield','skin'}
XML_BYTE_LIMIT=32*1024*1024
ASSET_BYTE_LIMIT=256*1024*1024
CLOSURE_BYTE_LIMIT=512*1024*1024


def _hash_bytes(raw):return hashlib.sha256(raw).hexdigest()


def _rules(values):
    if not isinstance(values,list):raise ContractError('path-prefix rules must be a list')
    result=[]
    for rule in values:
        if not isinstance(rule,dict) or set(rule)!={'from','to'}:raise ContractError('invalid rebinding rule')
        for key in ('from','to'):
            p=rule[key]
            if (not isinstance(p,str) or not p.startswith('/') or p=='/' or str(PurePosixPath(p))!=p or
                    '..' in PurePosixPath(p).parts or '\\' in p or any(ord(c)<32 for c in p)):
                raise ContractError('rebinding prefix must be a canonical absolute directory')
        for before,_ in result:
            if before==rule['from'] or before.startswith(rule['from']+'/') or rule['from'].startswith(before+'/'):
                raise ContractError('overlapping original rebinding prefixes')
        result.append((rule['from'],rule['to']))
    return result


def _map(path,rules):
    value=str(path)
    for old,new in rules:
        if value==old or value.startswith(old+'/'):return Path(new+value[len(old):])
    return Path(value)


def _parse(raw):
    if len(raw)>32*1024*1024 or b'<!DOCTYPE' in raw.upper():raise ContractError('unsupported/oversized source XML')
    try:return ET.fromstring(raw)
    except ET.ParseError as error:raise ContractError('invalid source XML') from error


def _xml(path):
    if Path(path).stat().st_size>XML_BYTE_LIMIT:raise ContractError('source XML exceeds read budget')
    return xml_payload(path)


def _normalise(path,raw,roots,rules,*,original):
    """Normalise only file/directory spelling, retaining every other XML value."""
    root_doc=_parse(raw);compiler=root_doc.find('compiler')
    dirs={k:compiler.get(k,'') if compiler is not None else '' for k in PATH_KEYS}
    base=path.parent;active=set();documents=[];assets={};budget=[0,0,0];replayed={};aliases={}
    def resolve(reference,parent,tag):
        value=Path(reference)
        prefix=dirs['meshdir' if tag=='mesh' else 'texturedir'] if tag in ('mesh','texture') else ''
        prefix=prefix or (dirs['assetdir'] if tag!='include' else '')
        candidates=[value] if value.is_absolute() else [base/Path(prefix)/value,parent/value,*[r/value for r in roots]]
        pairs={}
        for candidate in candidates:
            target=_map(candidate,rules) if original else candidate
            if target.is_file():pairs.setdefault(target.resolve(),[]).append(candidate)
        if len(pairs)!=1:raise ContractError('missing/ambiguous rebound source reference')
        target,original_paths=next(iter(pairs.items()))
        if not any(target==r or r in target.parents for r in roots):raise ContractError('rebound asset escapes approved roots')
        if tag!='include' and target.stat().st_size>ASSET_BYTE_LIMIT:raise ContractError('source asset exceeds byte budget')
        existing={p.resolve() for p in original_paths if p.is_file()}
        if original and existing:
            if tag=='include' and any(p.stat().st_size>XML_BYTE_LIMIT for p in [target,*existing]):
                raise ContractError('source include XML exceeds read budget')
            if tag!='include' and any(p.stat().st_size>ASSET_BYTE_LIMIT for p in existing):
                raise ContractError('original asset exceeds byte budget')
            if len(existing)!=1 or digest(next(iter(existing)))!=digest(target):
                # XML includes can differ only by replaying the same path rule.
                if tag!='include':raise ContractError('rebinding would substitute original asset bytes')
        return target,next(iter(existing)) if len(existing)==1 else None
    def visit(document,payload):
        budget[0]+=1
        if budget[0]>512 or document in active:raise ContractError('cyclic/oversized XML closure')
        budget[1]+=len(payload)
        if budget[1]>64*1024*1024:raise ContractError('expanded XML closure exceeds byte budget')
        alias=aliases.setdefault(document,'replay_%06d.xml'%len(aliases))
        active.add(document);doc=_parse(payload);rewritten=copy.deepcopy(doc)
        includes={}
        def node_value(node):
            attrs=dict(node.attrib)
            if node.tag=='compiler':
                for key in PATH_KEYS:attrs.pop(key,None)
            include_hash=None
            if 'file' in attrs:
                if node.tag not in FILE_TAGS:raise ContractError('unrecognised source file reference')
                target,old=resolve(attrs['file'],document.parent,node.tag)
                if node.tag=='include':
                    if original and old is None:raise ContractError('original include bytes required for replay proof')
                    child=old if original else target
                    child_canonical,_,child_alias=visit(child,_xml(child));includes[id(node)]=child_alias
                    include_hash=_hash_bytes(canonical(child_canonical))
                else:
                    if str(target) not in assets:
                        budget[2]+=target.stat().st_size
                        if budget[2]>CLOSURE_BYTE_LIMIT:raise ContractError('asset closure exceeds byte budget')
                        assets[str(target)]={'path':str(target),'sha256':digest(target),'bytes':target.stat().st_size}
                    if len(assets)>10000:raise ContractError('asset closure budget exceeded')
                attrs['file']=str(target)
            return {'tag':node.tag,'attributes':attrs,'text':(node.text or '').strip(),
                'tail':(node.tail or '').strip(),'include_canonical_sha256':include_hash,
                'children':[node_value(child) for child in node]}
        value=node_value(doc)
        for source_node,node in zip(doc.iter(),rewritten.iter()):
            if node.tag=='compiler':
                for key in PATH_KEYS:node.attrib.pop(key,None)
            if 'file' in node.attrib:
                node.set('file',includes[id(source_node)] if node.tag=='include' else str(resolve(node.get('file'),document.parent,node.tag)[0]))
        documents.append({'path':str(document),'sha256':digest(document),'expanded_sha256':_hash_bytes(payload)})
        result=ET.tostring(rewritten,encoding='utf-8');replayed[alias]=result
        active.remove(document);return value,result,alias
    value,rewritten,root_alias=visit(path,raw)
    return value,rewritten,documents,list(assets.values()),replayed,root_alias


def _compiled(model,data):
    h=hashlib.sha256()
    for name in ('geom_type','geom_bodyid','geom_size','geom_pos','geom_quat','geom_contype','geom_conaffinity',
            'geom_matid','geom_rgba','mesh_vert','mesh_face','mesh_texcoord','mesh_pos','mesh_quat','mesh_scale',
            'mat_rgba','mat_texid','tex_data'):
        a=np.asarray(getattr(model,name));h.update(name.encode()+b'\0'+canonical([str(a.dtype),list(a.shape)]))
        h.update(a.astype(a.dtype.newbyteorder('<'),copy=False).tobytes())
    for name in ('geom_xpos','geom_xmat','xpos','xquat'):
        a=np.asarray(getattr(data,name));h.update(name.encode()+b'\0'+a.astype('<f8').tobytes())
    return h.hexdigest()


def _derive(config):
    if not isinstance(config,dict) or set(config)!={'path_prefixes','original_gzip','rebased_xml','asset_roots','frames','states','ep_meta','state_format'}:
        raise ContractError('invalid source rebinding configuration')
    if config['state_format'] not in ('qpos','mujoco_fullphysics') or not isinstance(config['asset_roots'],list):
        raise ContractError('unsupported source rebinding state/asset configuration')
    rules=_rules(config['path_prefixes'])
    original=Path(config['original_gzip']).resolve(strict=True);rebased=Path(config['rebased_xml']).resolve(strict=True)
    if original.stat().st_size>32*1024*1024:raise ContractError('compressed source XML exceeds byte budget')
    with original.open('rb') as stream:magic=stream.read(2)
    if not original.name.endswith('.gz') or magic!=b'\x1f\x8b':
        raise ContractError('original compressed gzip identity required')
    roots=[rebased.parent,*[Path(r).resolve(strict=True) for r in config['asset_roots']]]
    if any(not r.is_dir() for r in roots):raise ContractError('asset root is not a directory')
    expected,payload,original_xml,original_assets,replayed_xml,root_alias=_normalise(original,_xml(original),roots,rules,original=True)
    actual,_,rebound_xml,rebound_assets,_,_=_normalise(rebased,_xml(rebased),roots,(),original=False)
    if expected!=actual:raise ContractError('original to rebound XML differs beyond the declared path-only transformation')
    if sorted(original_assets,key=lambda r:r['path'])!=sorted(rebound_assets,key=lambda r:r['path']):
        raise ContractError('original/rebound complete asset closures differ')
    model,sources=load_model(rebased,roots)
    frames=config['frames']
    if not isinstance(frames,list) or not frames or len(frames)>64 or any(type(n) is not int or n<0 for n in frames) or frames!=sorted(set(frames)):
        raise ContractError('invalid selected rebinding frames')
    states=Path(config['states']).resolve(strict=True);ep=Path(config['ep_meta']).resolve(strict=True)
    try:
        with zipfile.ZipFile(states) as archive:
            if sum(e.file_size for e in archive.infolist())>CLOSURE_BYTE_LIMIT:
                raise ContractError('expanded state archive exceeds byte budget')
    except zipfile.BadZipFile as error:raise ContractError('invalid original state archive') from error
    metadata=read_json(ep)
    if not isinstance(metadata,dict):raise ContractError('official ep_meta must be an object')
    rows=[]
    with tempfile.TemporaryDirectory(prefix='g2_rebinding_replay_') as folder:
        for alias,document in replayed_xml.items():(Path(folder)/alias).write_bytes(document)
        rewritten=Path(folder)/root_alias
        # Includes were compared recursively before compilation. Their original
        # counterparts must exist; missing historical XML cannot be guessed.
        replayed,_=load_model(rewritten,roots)
        for frame in frames:
            d,state=apply_state(model,states,frame,config['state_format'])
            original_data,original_state=apply_state(replayed,states,frame,config['state_format'])
            fingerprint=_compiled(model,d)
            if fingerprint!=_compiled(replayed,original_data) or state['row_sha256']!=original_state['row_sha256']:
                raise ContractError('compiled source geometry/state differs after rebinding replay')
            rows.append({'frame_id':frame,'state_row_sha256':state['row_sha256'],'compiled_geometry_state_sha256':fingerprint,
                'timestamp':state['timestamp'],'timestamp_source':state['timestamp_source']})
    return {'schema':SCHEMA,'configuration':config,
        'original_compressed':{'path':str(original),'sha256':digest(original),'bytes':original.stat().st_size},
        'original_expanded_sha256':_hash_bytes(_xml(original)),
        'rebased':{'path':str(rebased),'sha256':digest(rebased),'bytes':rebased.stat().st_size},
        'normalised_xml_sha256':_hash_bytes(canonical(actual)),
        'transformation_rule_sha256':_hash_bytes(canonical(config['path_prefixes'])),
        'model_source_sha256':model_source_hash(sources),'sources':sources,
        'original_xml_closure':original_xml,'rebased_xml_closure':rebound_xml,
        'assets':sorted(rebound_assets,key=lambda r:r['path']),
        'states':{'path':str(states),'sha256':digest(states)},'ep_meta':{'path':str(ep),'sha256':digest(ep)},
        'frames':rows,'historical_generator_revision_certified':False,'training_ready':False}


def create(original_gzip,rebased_xml,output,*,path_prefixes,states,ep_meta,asset_roots=(),frames=(0,200),state_format='qpos'):
    config={'original_gzip':str(Path(original_gzip).resolve()),'rebased_xml':str(Path(rebased_xml).resolve()),
        'asset_roots':[str(Path(r).resolve()) for r in asset_roots],'path_prefixes':path_prefixes,
        'states':str(Path(states).resolve()),'ep_meta':str(Path(ep_meta).resolve()),'frames':list(frames),'state_format':state_format}
    body=_derive(config);body['version_sha256']=_hash_bytes(canonical(body))
    protected=[Path(original_gzip).parent,Path(rebased_xml).parent,states,ep_meta,*asset_roots]
    protected.extend(Path(row['path']).parent for row in body['original_xml_closure']+body['rebased_xml_closure'])
    out=new_output(output,protected);out.mkdir(parents=True)
    write_json(out/'rebinding.json',body);verify(out/'rebinding.json')
    (out/'REBINDING_COMPLETE').write_text(body['version_sha256']+'\n')
    return body


def verify(proof,*,prescan=None,recorded_model_sha256=None):
    path=Path(proof).resolve(strict=True);value=read_json(path);claimed=value.pop('version_sha256',None)
    if _hash_bytes(canonical(value))!=sha(claimed) or value.get('schema')!=SCHEMA:
        raise ContractError('model rebinding proof identity differs')
    actual=_derive(value['configuration'])
    if actual!=value:raise ContractError('model rebinding replay/source evidence differs')
    if recorded_model_sha256 is not None and actual['original_compressed']['sha256']!=recorded_model_sha256:
        raise ContractError('rebinding proof belongs to another original compressed episode model')
    if prescan is not None:
        roots=[r for r in prescan.get('sources',[]) if r.get('logical_id')=='root.xml']
        rows={r['frame_id']:r for r in actual['frames']};state=prescan.get('state',{})
        if (len(roots)!=1 or roots[0]['sha256']!=actual['rebased']['sha256'] or
                prescan.get('source_identity',{}).get('model_source_sha256')!=actual['model_source_sha256'] or
                model_source_hash(prescan.get('sources',[]))!=actual['model_source_sha256'] or
                state.get('file_sha256')!=actual['states']['sha256'] or
                type(prescan.get('frame_id')) is not int or prescan['frame_id']!=state.get('frame_id') or
                state.get('format')!=actual['configuration']['state_format'] or
                type(state.get('frame_id')) is not int or state['frame_id'] not in rows or
                state.get('row_sha256')!=rows[state['frame_id']]['state_row_sha256'] or
                (state.get('timestamp') is not None and type(state['timestamp']) not in (int,float)) or
                state.get('timestamp')!=rows[state['frame_id']]['timestamp'] or
                state.get('timestamp_source')!=rows[state['frame_id']]['timestamp_source'] or
                prescan.get('input_files',{}).get('ep_meta',{}).get('sha256')!=actual['ep_meta']['sha256']):
            raise ContractError('pre-scan source/state/ep_meta differs from actual rebinding proof')
    return {'path':str(path),'sha256':digest(path),'version_sha256':claimed,
        'original_compressed_sha256':actual['original_compressed']['sha256'],
        'rebased_xml_sha256':actual['rebased']['sha256'],'model_source_sha256':actual['model_source_sha256'],
        'transformation_rule_sha256':actual['transformation_rule_sha256']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('create','verify'));p.add_argument('--proof');p.add_argument('--original-gzip')
    p.add_argument('--rebased-xml');p.add_argument('--states');p.add_argument('--ep-meta');p.add_argument('--output')
    p.add_argument('--rules',help='server-local JSON list of exact original/current directory prefixes')
    p.add_argument('--asset-root',action='append',default=[]);p.add_argument('--frames',nargs='+',type=int,default=[0,200])
    p.add_argument('--state-format',choices=('qpos','mujoco_fullphysics'),default='qpos');a=p.parse_args()
    if a.action=='verify':result=verify(a.proof)
    else:result=create(a.original_gzip,a.rebased_xml,a.output,path_prefixes=read_json(a.rules),
        states=a.states,ep_meta=a.ep_meta,asset_roots=a.asset_root,frames=a.frames,state_format=a.state_format)
    print(result.get('version_sha256'))


if __name__=='__main__':main()
