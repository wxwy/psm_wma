import hashlib
import json
from pathlib import Path
import subprocess
root = Path('/workspace/psm_wma')
run = Path('/tmp/psm-v3-matched-no-ttt-20261025/final_after_c0')
files = ['cosmos-framework/cosmos_framework/trainer/matched_no_ttt.py',
 'cosmos-framework/cosmos_framework/trainer/matched_no_ttt_test.py',
 'cosmos-framework/examples/psm_wma_robocasa_matched_no_ttt.py',
 'cosmos-framework/examples/psm_wma_robocasa_matched_no_ttt_test.py',
 'cosmos-framework/examples/psm_wma_robocasa_corrected_phase5.py',
 'cosmos-framework/examples/psm_wma_robocasa_effective_config.py',
 'cosmos-framework/cosmos_framework/utils/training_audit.py',
 'scripts/serve_v3_matched_no_ttt.py', 'tools/v3/matched_no_ttt_entry_test.py']
ruff='/workspace/.venvs/psm-wma-cpu/bin/ruff'
commands = [ [ruff, '--version'],
 [ruff, 'check','--config','cosmos-framework/.ruff.toml',*files],
 [ruff, 'format','--check','--config','cosmos-framework/.ruff.toml',*files],
 ['bash','-n','scripts/train_v3_matched_no_ttt.sh'],
 ['git','diff','--check'], ['git','-C','cosmos-framework','diff','--check'] ]
results=[]
with (run/'static.log').open('x') as out:
    for command in commands:
        out.write('$ '+ ' '.join(command)+'\n'); out.flush()
        result=subprocess.run(command,cwd=root,stdout=out,stderr=subprocess.STDOUT)
        results.append({'argv':command,'exit_code':result.returncode})
        if result.returncode: raise SystemExit('static check failed')
    for name in files:
        compile((root/name).read_bytes(), name,'exec')
    frozen=json.loads((run/'source_sha256.json').read_text())
    assert all(hashlib.sha256((root/name).read_bytes()).hexdigest()==value for name,value in frozen.items())
    out.write('syntax 9 PASS; source hash freeze PASS\n')
(run/'static.json').write_text(json.dumps({'results':results,'syntax_files':files,'source_freeze':'PASS'},indent=2))
print('Ruff0.12.7 check+format9, syntax9, bash syntax and diff/frozen hashes PASS')
