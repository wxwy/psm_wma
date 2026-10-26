import importlib.metadata as m,json,platform,sys
from pathlib import Path
names=['torch','torchvision','pytest','pytest-subtests','ruff','numpy','pandas','pyarrow','omegaconf','hydra-core','lerobot','transformers','accelerate']
versions={}
for name in names:
 try:versions[name]=m.version(name)
 except m.PackageNotFoundError:versions[name]=None
lerobot_origin=json.loads(m.distribution('lerobot').read_text('direct_url.json') or '{}').get('vcs_info',{})
out={'lerobot_vcs_info':lerobot_origin,'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'packages':versions,'GPU_used':False,'real_assets_used':False,'fixture_scope':'Synthetic files and CPU Torch only; no production datasets/checkpoint/cache IO'}
Path('/tmp/psm-v3-nottt-mp-20261026/environment.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
