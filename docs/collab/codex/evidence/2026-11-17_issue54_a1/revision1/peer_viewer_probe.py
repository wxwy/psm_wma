import json
import re
import subprocess
import tempfile
from pathlib import Path
from g2.io import read_json
from g2.offline.output_profile import OutputProfile
from g2.offline.stage_a import package_stage_a, validate_profile_episode
from g2.tests.test_stage_a_package import stage_case

root = Path(tempfile.mkdtemp(prefix='issue54_a1_peer_probe_', dir='/tmp'))
kwargs, _ = stage_case(root / 'fixture', OutputProfile(selection_top_variant='clean'))
target = root / 'package'
manifest = package_stage_a(destination=target, **kwargs)
validated = validate_profile_episode(target)
complete = read_json(target / 'COMPLETE.json')
viewer = Path('g2/viewer/viewer.js').read_text()
start = viewer.index('      if (complete.complete !== true ||')
end = viewer.index('      // Keep source timestamps aligned', start)
check = viewer[start:end]
node = "const data=JSON.parse(require('fs').readFileSync(0,'utf8')); const {complete,manifest,item}=data; try {\n" + check + "\nconsole.log(JSON.stringify({accepted:true})); } catch (e) { console.log(JSON.stringify({accepted:false,error:e.message})); }"
result = subprocess.run(['node', '-e', node], input=json.dumps(dict(complete=complete, manifest=manifest, item=dict(global_id=0))), text=True, capture_output=True, check=True)
evidence = dict(root=str(root), python_validator_pass=validated==manifest, complete_keys=sorted(complete), viewer_check=check, viewer_result=json.loads(result.stdout))
(root/'probe.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(evidence, ensure_ascii=False, indent=2))
