import ast
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path('/workspace/psm_wma')
OUT = pathlib.Path('/tmp/psm-v3-episode-resume-production-20261024/final')
BASE = 'db4ac8c690ba9f5971899d28768ac3caf7065108'
CHILD = '813a550dab5d6b5b5e3be90d38bb97527956b4dc'

def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', *args], cwd=cwd, text=True).strip()

files = sorted((ROOT/'scripts/robocasa_episode_resume').glob('*.py'))
files += [ROOT/'scripts'/name for name in ['robocasa_resume_cli.py','robocasa_resume_store.py',
    'robocasa_resume_execution.py','eval_robocasa_18task_queue.py']]
files += [ROOT/'tools/v3'/name for name in ['robocasa_resume_components_test.py',
    'robocasa_resume_store_test.py','robocasa_resume_execution_test.py',
    'robocasa_episode_resume_integration_test.py','eval_robocasa_queue_identity_test.py']]
assert len(files) == 15
for path in files:
    raw = path.read_bytes()
    compile(raw, str(path), 'exec')
    if path.is_relative_to(ROOT/'scripts'):
        for node in ast.walk(ast.parse(raw)):
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or '').startswith('tools.'), (path, node.module)
            if isinstance(node, ast.Import):
                assert not any(n.name.startswith('tools.') for n in node.names), path
protected = ['cosmos-framework','configs','third_party', 'tools/v3/episode_resume_prototype',
    'docs/collab/codex/designs','docs/collab/chatgpt/reviews',
    'docs/collab/codex/evidence/2026-10-23_flexible_episode_resume_design_author_cpu',
    'docs/collab/codex/evidence/2026-10-23_flexible_episode_resume_design_r2_author_cpu']
assert not git('diff','--name-only',BASE,'--',*protected)
assert git('rev-parse','HEAD',cwd=ROOT/'cosmos-framework') == CHILD
assert git('ls-tree','HEAD','cosmos-framework').split()[2] == CHILD
assert not git('status','--porcelain',cwd=ROOT/'cosmos-framework')
subprocess.run(['git','diff','--check'],cwd=ROOT,check=True)
assert 'def execute(' not in (ROOT/'scripts/eval_robocasa_18task_queue.py').read_text()
assert 'prepare_resume(resolve(' in (ROOT/'scripts/eval_robocasa_18task_queue.py').read_text()
hashes = {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
if (OUT/'frozen_source_sha256.json').exists():
    assert json.loads((OUT/'frozen_source_sha256.json').read_text()) == hashes, 'source changed during final Gate'
(OUT/'frozen_source_sha256.json').write_text(json.dumps(hashes,indent=2)+'\n')
result = {'status':'STATIC_PASS','baseline_root':BASE,'child':CHILD,'gitlink':CHILD,
    'python':sys.version,'ruff':subprocess.check_output(['/workspace/.venvs/psm-wma-cpu/bin/ruff','--version'],text=True).strip(),
    'syntax_files':len(files),'production_imports_prototype':False,'one_default_resume_path':True,
    'child_clean':True,'protected_paths_unchanged':True,'source_sha256':hashes}
(OUT/'static_checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({key:value for key,value in result.items() if key!='source_sha256'},indent=2))
