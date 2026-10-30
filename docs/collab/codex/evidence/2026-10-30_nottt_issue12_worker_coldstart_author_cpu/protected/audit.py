"""Read-only Git/AST scope audit; author evidence, not independent review."""

import ast
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path('/workspace/psm-wma-nottt-coldstart')
CHILD = ROOT / 'cosmos-framework'
OUT = Path('/tmp/psm-nottt-coldstart-20261030/protected')
BASE = 'f6a92d47b6dac7998ddc58b3da26ef93f8068dc7'
FORMAL = '224c5f3c0bd6911bb49cb6bb0895ba7da53ff822'

def git(where, *args):
    return subprocess.check_output(['git', '-C', str(where), *args])

changed = git(CHILD, 'diff', '--name-only', BASE, FORMAL).decode().splitlines()
expected = [f'cosmos_framework/trainer/{name}.py' for name in (
    'no_ttt_async_recipe', 'no_ttt_async_recipe_test', 'no_ttt_worker_source', 'no_ttt_worker_source_test')]
assert sorted(changed) == sorted(expected)

protected = [
    'cosmos_framework/trainer/matched_no_ttt.py',
    'cosmos_framework/trainer/no_ttt_async_loader.py',
    'cosmos_framework/trainer/no_ttt_cpu_loader.py',
    'cosmos_framework/utils/no_ttt_loader_profile.py',
    'cosmos_framework/model/generator/mot/robocasa_exact_window_local.py',
    'cosmos_framework/data/generator/action/datasets/robocasa_exact_window_source.py',
    'cosmos_framework/data/generator/action/datasets/robocasa_verified_index.py',
    'cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cached_sft.py',
    'cosmos_framework/data/generator/action/utils/transforms.py',
    'cosmos_framework/data/generator/augmentors/text_tokenizer.py',
    'cosmos_framework/checkpoint/dcp.py',
    'uv.lock',
]
same = {}
for name in protected:
    old, new = (git(CHILD, 'rev-parse', f'{sha}:{name}').decode().strip() for sha in (BASE, FORMAL))
    assert old == new, name
    same[name] = new

name = 'cosmos_framework/trainer/no_ttt_async_recipe_test.py'
old = ast.parse(git(CHILD, 'show', f'{BASE}:{name}'))
new = ast.parse(git(CHILD, 'show', f'{FORMAL}:{name}'))
new_nodes = {node.name: node for node in new.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
retained = []
for node in old.body:
    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
        assert ast.dump(node) == ast.dump(new_nodes[node.name]), node.name
        retained.append(node.name)

name = 'cosmos_framework/trainer/no_ttt_async_recipe.py'
def members(sha):
    tree = ast.parse(git(CHILD, 'show', f'{sha}:{name}'))
    result = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            result[node.name] = ast.dump(node)
        elif isinstance(node, ast.ClassDef):
            for method in node.body:
                if isinstance(method, ast.FunctionDef):
                    result[f'{node.name}.{method.name}'] = ast.dump(method)
            result[f'{node.name}:fields'] = [ast.dump(n) for n in node.body if isinstance(n, ast.AnnAssign)]
    return result
before, after = members(BASE), members(FORMAL)
assert before.keys() == after.keys()
altered = [key for key in before if before[key] != after[key]]
assert altered == ['AsyncRecipe.build'], altered

root_changed = git(ROOT, 'diff', '--name-only', '2260f2a6f89368301ba50a686676994af90a2ca5',
                   'fd9021b0908b4b2763b3d02508b1f34df377dc97').decode().splitlines()
assert all(name in {'cosmos-framework', 'SESSION.md', 'TODO.md'} or name.startswith('docs/') for name in root_changed)
assert git(ROOT, 'rev-parse', 'fd9021b0908b4b2763b3d02508b1f34df377dc97:cosmos-framework').decode().strip() == FORMAL
OUT.mkdir(exist_ok=False)
result = dict(status='PASS', scope='AUTHOR_READONLY_GIT_AST', baseline_child=BASE, formal_child=FORMAL,
              changed_child_files=changed, unchanged_blob_bindings=same, original_test_definitions_retained=retained,
              unchanged_recipe_members=[key for key in before if key not in altered], changed_recipe_members=altered,
              root_changed_files=root_changed)
(OUT / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(dict(status='PASS', protected_blobs=len(same), old_test_definitions_retained=len(retained),
                      only_modified_recipe_member=altered)))
