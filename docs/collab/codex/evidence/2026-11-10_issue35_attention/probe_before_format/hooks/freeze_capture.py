"""Native serialization preserves original tensor strides/storage aliases and bytes.

All raw payloads remain on the authorized server. This hook only records the
existing execution; no generation flags, checkpoints, mode/source checks change.
"""
import dataclasses
import functools
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import traceback

import numpy as np
import torch


def tensor_tree(value):
    aliases={}
    tensors={}
    def visit(v,path):
        if isinstance(v,torch.Tensor):
            local=v.to_local() if hasattr(v,'to_local') else v
            storage=local.untyped_storage()
            key=(str(local.device),storage.data_ptr())
            group=aliases.setdefault(key,len(aliases))
            raw=local.detach().cpu().contiguous().reshape(-1).view(torch.uint8).numpy().tobytes()
            tensors[path]=dict(shape=list(v.shape),dtype=str(v.dtype),device=str(v.device),
                               stride=list(local.stride()),storage_offset=local.storage_offset(),
                               alias_group=group,sha256=hashlib.sha256(raw).hexdigest())
        elif dataclasses.is_dataclass(v):
            for f in dataclasses.fields(v):visit(getattr(v,f.name),path+'.'+f.name)
        elif isinstance(v,dict):
            for k,x in v.items():visit(x,path+'['+str(k)+']')
        elif isinstance(v,(list,tuple)):
            for i,x in enumerate(v):visit(x,path+'['+str(i)+']')
    visit(value,'root')
    return tensors


def save_torch(path,payload):
    # torch.save itself copies device storage and retains views/aliases. Manual
    # detach().cpu().clone() here would change layout and invalidate the replay.
    with path.open('xb') as stream:
        os.chmod(path,0o600)
        torch.save(payload,stream)
        stream.flush()
        os.fsync(stream.fileno())


def save_json(path,value):
    with path.open('x') as stream:
        json.dump(value,stream,indent=2,allow_nan=False)
        stream.write('\n')


def install(service):
    directory=Path(os.environ['ISSUE35_CAPTURE_DIR'])
    directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    target=int(os.environ['ISSUE35_TARGET_SOURCE_STEP'])
    original_generate=service.model.generate_samples_from_batch
    original_prepare=service.model._prepare_inference_data
    active=None
    completed=[]
    save_json(directory/'installed.json',dict(pid=os.getpid(),target_source_step=target,
        seed=service.cfg.seed,num_steps=service.cfg.num_steps,guidance=service.cfg.guidance,
        local_memory_mode=service.local_memory_adapter.mode,
        cuda_uuid=str(torch.cuda.get_device_properties(0).uuid),
        model_class=type(service.model).__module__+'.'+type(service.model).__name__))

    @functools.wraps(original_prepare)
    def prepare(*args,**kwargs):
        value=original_prepare(*args,**kwargs)
        if active is not None:
            path=directory/('prepared_%04d.pt'%active['source_step'])
            save_torch(path,dict(prepared=value))
            save_json(path.with_suffix('.tensor_hashes.json'),tensor_tree(value))
        return value

    @functools.wraps(original_generate)
    def generate(*args,**kwargs):
        nonlocal active
        parent=sys._getframe(1)
        updates=parent.f_locals.get('updates')
        if not updates or len(updates)!=1:
            save_json(directory/'unsupported_parent.json',dict(function=parent.f_code.co_name,
                keys=sorted(parent.f_locals)))
            return original_generate(*args,**kwargs)
        update=updates[0].memory
        step=int(update.replacement.consumer_step)
        if step>target or step in completed:
            return original_generate(*args,**kwargs)
        active=dict(source_step=step)
        payload=dict(args=args,kwargs=kwargs,
            previous_fast_record=update.previous,candidate_fast_record=update.replacement,
            requests=parent.f_locals.get('reqs'),
            torch_cpu_rng=torch.get_rng_state(),torch_cuda_rng=torch.cuda.get_rng_state(),
            numpy_rng=np.random.get_state(),python_rng=random.getstate(),
            source_step=step,seed=service.cfg.seed,num_steps=service.cfg.num_steps,
            guidance=service.cfg.guidance,requires_state=service.requires_state)
        path=directory/('request_%04d.pt'%step)
        try:
            save_torch(path,payload)
            save_json(path.with_suffix('.tensor_hashes.json'),tensor_tree(payload))
            samples=original_generate(*args,**kwargs)
            raw=service._denormalize_action(samples['action'][0].float().squeeze(0))
            if service.requires_state:raw=raw[1:]
            save_torch(directory/('outputs_%04d.pt'%step),dict(samples=samples,raw15_action=raw))
            completed.append(step)
            save_json(directory/('complete_%04d.json'%step),dict(source_step=step,
                output_tensors=tensor_tree(samples),raw15_tensors=tensor_tree(raw)))
            if step==target:
                save_json(directory/'capture_ready.json',dict(target_source_step=target,
                    captured_source_steps=completed,pid=os.getpid(),status='CAPTURE_COMPLETE_STOP_DIAGNOSTIC_RUN'))
            return samples
        except BaseException:
            with (directory/('capture_error_%04d.txt'%step)).open('x') as stream:
                traceback.print_exc(file=stream)
            raise
        finally:
            active=None

    service.model._prepare_inference_data=prepare
    service.model.generate_samples_from_batch=generate
