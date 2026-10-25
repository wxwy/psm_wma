import json
import sys
import os
from pathlib import Path
import pytest
base=Path('/tmp/psm-v3-matched-no-ttt-20261025/final_after_c0')
spec=json.loads((base/'command.json').read_text())
os.environ.update(spec['env']); os.chdir(spec['cwd'])
sys.path[:0] = spec['env']['PYTHONPATH'].split(os.pathsep)
class Capture:
    def pytest_collection_finish(self, session):
        rows=[{'nodeid':item.nodeid,'name':item.name,'file':str(item.path)} for item in session.items]
        (base/'collected_nodes.json').write_text(json.dumps(rows,indent=2))
args=spec['argv'][3:]
args=[arg for arg in args if not arg.startswith('--junitxml=')]
args += ['--collect-only','--rootdir=/workspace/psm_wma']
raise SystemExit(pytest.main(args, plugins=[Capture()]))
