import ast
import collections
import hashlib
import json
import pathlib
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = pathlib.Path('/workspace/psm_wma')
OUT = pathlib.Path('/tmp/psm-v3-episode-resume-design-r2-20261023')
BASE = '50ed1fdc87d1380be6b95219ea12b9d379f7edc7'
CHILD = '813a550dab5d6b5b5e3be90d38bb97527956b4dc'

def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', *args], cwd=cwd, text=True).strip()

files = sorted((ROOT / 'tools/v3/episode_resume_prototype').glob('*.py'))
for path in files:
    compile(path.read_bytes(), str(path), 'exec')
assert len(files) == 11
child = git('rev-parse', 'HEAD', cwd=ROOT / 'cosmos-framework')
gitlink = git('ls-tree', 'HEAD', 'cosmos-framework').split()[2]
assert child == gitlink == CHILD
assert not git('status', '--porcelain', cwd=ROOT / 'cosmos-framework')
protected = ['scripts', 'configs', 'cosmos-framework', 'third_party',
    'tools/v3/episode_resume_prototype/model_identity.py',
    'tools/v3/episode_resume_prototype/model_identity_test.py',
    'docs/collab/codex/designs/2026-10-23_V3_RoboCasa_flexible_episode_resume_design_r1.md',
    'docs/collab/codex/evidence/2026-10-23_flexible_episode_resume_design_author_cpu']
assert not git('diff', '--name-only', BASE, '--', *protected)
changed = set(git('diff', '--name-only', BASE).splitlines())
changed.update(git('ls-files', '--others', '--exclude-standard').splitlines())
allowed = {'SESSION.md', 'TODO.md'}
assert all(path in allowed or path.startswith(('tools/v3/episode_resume_prototype/',
    'docs/collab/codex/designs/')) for path in changed), sorted(changed)
subprocess.run(['git', 'diff', '--check'], cwd=ROOT, check=True)
tree = ET.parse(OUT / 'junit.xml')
counts = collections.Counter()
test_modules = {}
for path in files:
    if path.name == 'model_identity_test.py' or not path.name.endswith('_test.py'):
        continue
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
            assert node.name not in test_modules, node.name
            test_modules[node.name] = path.name
for case in tree.iter('testcase'):
    assert case.find('failure') is None and case.find('error') is None and case.find('skipped') is None
    counts[test_modules[case.attrib['name'].split('[', 1)[0]]] += 1
assert sum(counts.values()) == 185
result = {'status': 'DESIGN_PROTOTYPE_AUTHOR_CPU_PASS', 'baseline_root': BASE,
    'child': child, 'gitlink': gitlink, 'counts': dict(counts), 'tests': sum(counts.values()),
    'failures': 0, 'errors': 0, 'skipped': 0, 'syntax_files': len(files),
    'python': sys.version, 'ruff': subprocess.check_output([
        '/workspace/.venvs/psm-wma-cpu/bin/ruff', '--version'], text=True).strip(),
    'production_diff_empty': True, 'child_clean': True, 'old_evidence_unchanged': True,
    'unchanged_model_identity_tests_not_rerun': 45, 'changed_paths': sorted(changed),
    'limitations': ['isolated synthetic CPU evidence', 'not production Resume integration',
        'not independent DS evidence', 'not GPU/model/simulator/DCP validation'],
    'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(OUT / 'checks.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({key: result[key] for key in ['status', 'counts', 'tests', 'syntax_files', 'ruff',
    'production_diff_empty', 'child_clean']}, indent=2))
