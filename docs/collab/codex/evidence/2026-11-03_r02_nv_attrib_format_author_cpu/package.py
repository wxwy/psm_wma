import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path('/workspace/psm-wma-eval-r02-format')
CHILD = ROOT / 'cosmos-framework'
OUT = Path('/tmp/psm-eval-v2-r02-format-20261103')
FORMAL_ROOT = '46c08127b2a13155bb22204069a1456cb01424d7'
FORMAL_CHILD = '1069fe78841228cadbbfbe6afbd767eaed6225da'
OLD_ROOT = '286573d2d592cbd7449930e6e93f188a3a9b037d'
OLD_CHILD = '37558dcc71682304f3de1848923e6cedb9b77837'
DOC_HEAD = 'c4d0a4281fb57797484a91b9c47387997b967f31'
EVIDENCE = ROOT / 'docs/collab/codex/evidence/2026-11-03_r02_nv_attrib_format_author_cpu'


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', *args], cwd=cwd)


def text_git(*args, cwd=ROOT):
    return git(*args, cwd=cwd).decode().strip()


def save(name, value):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    assert not path.exists(), path
    if not isinstance(value, str):
        value = json.dumps(value, indent=2, sort_keys=True) + '\n'
    path.write_text(value)


gate = json.loads((OUT / 'final/gate.json').read_text())
assert gate['root'] == FORMAL_ROOT and gate['child'] == gate['gitlink'] == FORMAL_CHILD
assert text_git('rev-parse', 'HEAD') == FORMAL_ROOT
assert text_git('rev-parse', 'HEAD', cwd=CHILD) == FORMAL_CHILD
assert not text_git('status', '--porcelain')
assert not text_git('status', '--porcelain', cwd=CHILD)
child_file = 'cosmos_framework/simulation/robocasa/render_devices.py'
root_file = 'tools/v3/eval_v2_batch_tests/render_devices_test.py'
child_scope = text_git('diff-tree', '--no-commit-id', '--name-only', '-r', FORMAL_CHILD, cwd=CHILD).splitlines()
root_scope = text_git('diff-tree', '--no-commit-id', '--name-only', '-r', FORMAL_ROOT).splitlines()
assert child_scope == [child_file], child_scope
assert root_scope == ['SESSION.md', 'TODO.md', 'cosmos-framework', root_file], root_scope
assert text_git('rev-parse', FORMAL_ROOT + '^') == DOC_HEAD
assert text_git('rev-parse', FORMAL_CHILD + '^', cwd=CHILD) == OLD_CHILD
save('static/scope.json', {
    'status': 'PASS', 'formal_root': FORMAL_ROOT, 'formal_child': FORMAL_CHILD,
    'root_parent': DOC_HEAD, 'child_parent': OLD_CHILD,
    'root_formal_changed_files': root_scope, 'child_formal_changed_files': child_scope,
    'root_other_source_unchanged': True, 'child_other_source_unchanged': True,
    'latest_review_documents_preserved': True, 'old_evidence_unchanged': True,
    'official_refs_not_modified': True, 'production_changes_are_format_only': True,
})

bindings = []
for repo, commit, name in [
    (ROOT, FORMAL_ROOT, root_file),
    (ROOT, FORMAL_ROOT, 'tools/v3/eval_v2_batch_tests/render_mapping_test.py'),
    (CHILD, FORMAL_CHILD, child_file),
    (CHILD, FORMAL_CHILD, '.ruff.toml'),
]:
    data = git('show', f'{commit}:{name}', cwd=repo)
    assert data == (repo / name).read_bytes()
    bindings.append({
        'repository': 'root' if repo == ROOT else 'child', 'commit': commit,
        'path': name, 'git_blob': text_git('rev-parse', f'{commit}:{name}', cwd=repo),
        'sha256': hashlib.sha256(data).hexdigest(),
    })
save('static/source_bindings.json', bindings)

parity = []
for index, (repo, old, new, name) in enumerate([
    (CHILD, OLD_CHILD, FORMAL_CHILD, child_file),
    (ROOT, OLD_ROOT, FORMAL_ROOT, root_file),
]):
    before = git('show', f'{old}:{name}', cwd=repo)
    after = git('show', f'{new}:{name}', cwd=repo)
    ast_before = ast.dump(ast.parse(before), include_attributes=False)
    ast_after = ast.dump(ast.parse(after), include_attributes=False)
    assert ast_before == ast_after
    saved_index = index
    assert (OUT / f'before/source_{saved_index}.txt').read_bytes() == before
    assert (OUT / f'after/source_{saved_index}.txt').read_bytes() == after
    assert (OUT / f'before/ast_{saved_index}.txt').read_text() == ast_before + '\n'
    assert (OUT / f'after/ast_{saved_index}.txt').read_text() == ast_after + '\n'
    compile(before, name, 'exec')
    compile(after, name, 'exec')
    parity.append({'repository': 'root' if repo == ROOT else 'child', 'path': name,
                   'ast_exactly_equal': True, 'syntax_compile_before_after': 'PASS',
                   'before_ast_sha256': hashlib.sha256(ast_before.encode()).hexdigest(),
                   'after_ast_sha256': hashlib.sha256(ast_after.encode()).hexdigest()})
save('static/git_object_ast_parity.json', {'status': 'PASS', 'files': parity})
save('static/root_format.patch', git('diff', '--binary', DOC_HEAD, FORMAL_ROOT, '--', root_file).decode())
save('static/child_format.patch', git('diff', '--binary', OLD_CHILD, FORMAL_CHILD, '--', child_file, cwd=CHILD).decode())
for label, repo, old, new in [('root', ROOT, DOC_HEAD, FORMAL_ROOT), ('child', CHILD, OLD_CHILD, FORMAL_CHILD)]:
    command = ['git', 'diff', '--check', old, new]
    result = subprocess.run(command, cwd=repo, capture_output=True, text=True)
    save(f'static/{label}_committed_diff_check.log', result.stdout + result.stderr)
    assert result.returncode == 0

save('static/child_ruff_config.txt', (CHILD / '.ruff.toml').read_text())
command = ['/workspace/.venvs/psm-wma-cpu/bin/ruff', 'format', '--verbose', '--check',
           'cosmos-framework/' + child_file, root_file]
result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                        env={**__import__('os').environ, 'RUFF_CACHE_DIR': str(OUT / 'cache/ruff')})
save('static/formatter_configuration.log', result.stdout + result.stderr)
save('static/formatter_configuration.command.json', {'args': command, 'cwd': str(ROOT), 'returncode': result.returncode})
assert result.returncode == 0

assert not EVIDENCE.exists(), EVIDENCE
EVIDENCE.mkdir(parents=True)
for name in ['before', 'format', 'after', 'final', 'static']:
    shutil.copytree(OUT / name, EVIDENCE / name)
for name in ['environment.json', 'verify.py', 'package.py']:
    shutil.copyfile(OUT / name, EVIDENCE / name)
artifacts = {str(p.relative_to(EVIDENCE)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(EVIDENCE.rglob('*')) if p.is_file()}
(EVIDENCE / 'artifact_manifest.json').write_text(json.dumps({
    'formal_root': FORMAL_ROOT, 'formal_child_gitlink': FORMAL_CHILD,
    'author_cpu_only': True, 'sha256': artifacts,
}, indent=2, sort_keys=True) + '\n')
print(json.dumps({'artifacts': len(artifacts), 'root': FORMAL_ROOT,
                  'child_gitlink': FORMAL_CHILD, 'source_bindings': len(bindings),
                  'ast_identity_files': len(parity), 'tests': gate['tests'],
                  'evidence': str(EVIDENCE)}, indent=2))
