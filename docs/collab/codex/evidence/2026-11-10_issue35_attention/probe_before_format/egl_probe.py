"""Read-only native physical EGL mapping check; no scene/model/compute job."""
import json,os,subprocess,sys
from pathlib import Path
import yaml

base=Path('/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_codex_issue35_attention_20261109')
root=Path('/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_codex_issue31_prefix_pack_20261109/root2')
cfg=yaml.safe_load((base/'capture01/k1/config.yaml').read_text())
actor=next((base/'capture01/k1/run/_internal/actor_configs').glob('*.json'))
code='''import json,sys
from pathlib import Path
from cosmos_framework.simulation.robocasa.render_devices import EGLDevices,cuda_pci_map,configure
p=json.loads(Path(sys.argv[1]).read_text())['rendering']
devices=EGLDevices().inventory()
mapping=cuda_pci_map()
result=dict(expected_render_gpu=p['render_gpu_id'],expected_pci=p['expected_device']['pci_bus_id'],
            egl_device_count=len(devices),cuda_mapping_count=len(mapping),
            described_pci_count=sum(d['pci_bus_id'] is not None for d in devices),
            cuda_handle_count=sum(d['cuda_device'] is not None for d in devices))
try:
 proof=configure(p)
 result.update(status='MAPPING_PASS_NO_CONTEXT',selected_egl_index=proof['egl_device_index'])
except Exception as error:
 result.update(status='BLOCKED',error=repr(error),
   matching_drm_indices=[d['egl_device_index'] for d in devices if d['pci_bus_id']==p['expected_device']['pci_bus_id']],
   matching_cuda_indices=[i for i,d in enumerate(devices) if mapping.get(d['cuda_device'])==p['expected_device']['pci_bus_id']])
print(json.dumps(result))
'''
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',MUJOCO_GL='egl',PYOPENGL_PLATFORM='egl',
         __EGL_VENDOR_LIBRARY_FILENAMES=cfg['sim_shared_vae']['egl_vendor_json'],
         PYTHONPATH=str(root)+':'+str(root/'cosmos-framework')+':'+str(root/'scripts'))
if '--unset-library-path' in sys.argv:env.pop('LD_LIBRARY_PATH',None)
else:env['LD_LIBRARY_PATH']=''
r=subprocess.run([cfg['sim_python'],'-c',code,str(actor)],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
print(r.stdout,end='')
if r.returncode:print(json.dumps(dict(returncode=r.returncode,error_tail=r.stderr.splitlines()[-3:])))
raise SystemExit(r.returncode)
