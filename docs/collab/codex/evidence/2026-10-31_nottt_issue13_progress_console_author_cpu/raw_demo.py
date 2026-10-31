"""Persist two real raw console/file examples from fake training, not GPU tests."""

import json
import subprocess
import sys
from pathlib import Path

root=Path('/workspace/psm-wma-nottt-console')
base=Path('/tmp/psm-nottt-console-20261031/demos')
base.mkdir(exist_ok=False)
raw=(b'initializing fake model\n[rank1] warning\n[NoTTT][cpu_loader] {"wait_ms":3}\n'
     b'[CorrectedV3][progress] step=1/30000 loss=1.25\n[CorrectedV3][train] {"iteration":1}\n'
     b'[CorrectedV3][checkpoint] synthetic save event\n')
for code in (0,7):
    out=base/f'exit{code}'
    out.mkdir()
    fake=out/'fake_training.py'
    fake.write_text(f'import os\nos.write(1,{raw!r})\nos.write(2,b"stderr Traceback: fake diagnostic\\n")\nraise SystemExit({code})\n')
    command=[sys.executable,str(root/'scripts/no_ttt_console.py'),str(out/'output'),
             'no_ttt_raw_demo','--',sys.executable,str(fake)]
    result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15)
    (out/'console.stdout').write_bytes(result.stdout)
    (out/'console.stderr').write_bytes(result.stderr)
    full=next((out/'output/_launch_logs/no_ttt_raw_demo').glob('*.log'))
    (out/'full_launch.log').write_bytes(full.read_bytes())
    assert result.returncode==code
    assert full.read_bytes()==raw+b'stderr Traceback: fake diagnostic\n'
    assert result.stdout.splitlines()[1:]==[b'[CorrectedV3][progress] step=1/30000 loss=1.25']
    (out/'result.json').write_text(json.dumps(dict(status='PASS_FAKE_RAW_DEMO',exit_code=result.returncode,
        command=command,formal_root='24dbb677f7a60eeab6934c44352c7e00fa6d9b36',real_training=False),indent=2)+'\n')
print('2 raw fake-training examples saved; not added to pytest49 count')
