from pathlib import Path
import os,subprocess
root=Path('/workspace/psm_wma');raw=Path('/tmp/psm-v3-watchdog-f01-20261024')
files=['tools/v3/robocasa_resume_components_test.py','tools/v3/robocasa_resume_store_test.py','tools/v3/robocasa_resume_execution_test.py','tools/v3/robocasa_episode_resume_integration_test.py','tools/v3/eval_robocasa_queue_identity_test.py']
assert len(files)==len(set(files))==5
cmd=['/workspace/.venvs/psm-wma-cpu/bin/python','-m','pytest','--noconftest','-c','/dev/null','--rootdir='+str(root),'-p','no:cacheprovider','-q','-s',*files,'--junitxml='+str(raw/'final/junit.xml')]
(raw/'final/command.json').write_text(__import__('json').dumps(cmd,indent=2)+'\n')
with (raw/'final/pytest.log').open('w') as f:
 raise SystemExit(subprocess.call(cmd,cwd=root,stdout=f,stderr=subprocess.STDOUT))
