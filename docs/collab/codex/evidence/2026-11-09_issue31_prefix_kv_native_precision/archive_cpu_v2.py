"""Freeze newly generated local CPU evidence; never read private server files."""
import ast
import hashlib
import importlib.metadata
import json
import shutil
import subprocess
from pathlib import Path

root = Path('/workspace/work/psm-wma-prefix-kv-issue31')
child = root / 'cosmos-framework'
source = Path(__file__).parent
formal_root = '5b89f3eddbfe27ee72c173696a386e0b756d7866'
formal_child = '4446be0f6dad9b6dc887ef90af52d0af754d4682'
base_root = 'ca3a08acf8697b5ff316fcc476c4f0820d8f3b13'
base_child = '4cd5fc8c43d6793745dbc4cac51c59ee8a020dbe'
archive_parent = root / 'docs/collab/codex/evidence'
out = archive_parent / '2026-11-09_issue31_prefix_kv_native_precision'


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


assert git(root, 'rev-parse', 'HEAD') == formal_root
assert git(child, 'rev-parse', 'HEAD') == formal_child
assert git(root, 'rev-parse', formal_root + ':cosmos-framework') == formal_child
assert not out.exists()
v1 = source / 'archived_v1_pending_publish'
v1_index = json.loads((v1 / 'index.json').read_text())
for name, record in v1_index['files'].items():
    value = (v1 / name).read_bytes()
    assert len(value) == record['bytes']
    assert hashlib.sha256(value).hexdigest() == record['sha256']
v1_target = archive_parent / '2026-11-09_issue31_prefix_kv'
assert not v1_target.exists()
shutil.copytree(v1, v1_target)
out.mkdir()

prod = ['model/generator/' + p for p in (
    'omni_mot_model.py', 'mot/inference_text_kv_memory.py', 'mot/unified_mot.py',
    'mot/cosmos3_vfm_network.py', 'mot/attention.py')]
allowed_child = {'cosmos_framework/' + p for p in prod}
test = 'cosmos_framework/model/generator/mot/prefix_text_kv_memory_test.py'
allowed_child.add(test)
changed_child = set(git(child, 'diff', '--name-only', base_child, formal_child).splitlines())
changed_root = set(git(root, 'diff', '--name-only', base_root, formal_root).splitlines())
assert changed_child == allowed_child
assert changed_root == {
    'SESSION.md', 'TODO.md', 'cosmos-framework',
    'tools/v3/benchmark_local_ttt_prefix_kv.py', 'tools/v3/prefix_kv_benchmark_test.py'}
network = 'cosmos_framework/model/generator/mot/cosmos3_vfm_network.py'
old = ast.parse(git(child, 'show', base_child + ':' + network))
new = ast.parse(git(child, 'show', formal_child + ':' + network))
methods = {}
for name in ('scan_local_memory', '_encode_action', '_decode_action'):
    a = next(n for n in ast.walk(old) if isinstance(n, ast.FunctionDef) and n.name == name)
    b = next(n for n in ast.walk(new) if isinstance(n, ast.FunctionDef) and n.name == name)
    encoded = ast.dump(a, include_attributes=False).encode()
    assert ast.dump(a, include_attributes=False) == ast.dump(b, include_attributes=False)
    methods[name] = hashlib.sha256(encoded).hexdigest()
save(out / 'scope.json', dict(
    status='PASS', formal_root=formal_root, formal_child=formal_child,
    base_root=base_root, base_child=base_child,
    changed_root=sorted(changed_root), changed_child=sorted(changed_child),
    unchanged_method_ast_sha256=methods,
    attention_scope='Private inference-only native materialized UND K/V capture. No backend change, pack-template reuse or precision/compile-limit change.',
    protected_paths='All other tracked Root/Child files unchanged by exact Git diff; training/VAE/Sim/Worker/config/Resume/memory_prefix.py preserved'))
for label, repo, base, head in [
    ('root', root, base_root, formal_root), ('child', child, base_child, formal_child)]:
    (out / (label + '.diff')).write_bytes(subprocess.check_output([
        'git', '-C', str(repo), 'diff', '--binary', base, head]))
for name in ('cpu_gate.py', 'archive_cpu_v2.py', 'diagnose_velocity.py'):
    shutil.copyfile(source / name, out / name)
for directory in ('author06', 'native_dev', 'native_compiled', 'native_compiled02', 'native_red'):
    for path in sorted((source / directory).glob('*')):
        if path.is_file() and path.suffix in ('.log', '.json', '.xml'):
            target = out / 'raw' / directory / path.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
save(out / 'cpu_versions.json', {
    name: importlib.metadata.version(name) for name in ('torch', 'pytest', 'ruff', 'omegaconf')})
gate = json.loads((out / 'raw/author06/gate.json').read_text())
assert gate['status'] == 'PASS' and gate['junit'] == dict(tests=187, failures=0, errors=0, skipped=0)
assert gate['source_unchanged'] and gate['identity']['root'] == formal_root
assert gate['identity']['child'] == formal_child
red = Path('/workspace/work/issue31-native-red-child')
assert (child / test).read_bytes() == (red / test).read_bytes()
assert git(red, 'diff', '--name-only') == test
save(out / 'controlled_native_reproduction.json', dict(
    red_production_child=git(red, 'rev-parse', 'HEAD'),
    red_worktree_status=git(red, 'status', '--porcelain'),
    new_production_child=formal_child,
    test_sha256=hashlib.sha256((child / test).read_bytes()).hexdigest(),
    red='raw/native_red/focused.xml', green='raw/author06/focused.xml',
    old='1 deterministic expected FAIL: no native materialized buffer capture',
    new='Same native operand/padding test PASS, included in final187',
    note='Red worktree contains same new regression file; all production bytes exact old9f6cf6a1. Earlier native_dev two fixture failures retained; actual production padding fixes the fixture.'))
baseline = Path('/workspace/work/issue31-baseline-child')
legacy_paths = ['cosmos_framework/model/generator/mot/' + n for n in (
    'inference_text_kv_memory.py', 'unified_mot.py', 'attention.py')]
ruff = ['/workspace/.venvs/psm-wma-cpu/bin/ruff', 'check', '--output-format', 'concise', *legacy_paths]
r = subprocess.run(ruff, cwd=baseline, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
assert r.returncode == 1 and r.stdout.count('I001') == 3
target = out / 'raw/baseline_import_order.log'
target.write_text(r.stdout)
save(out / 'raw/baseline_import_order.command.json', dict(
    argv=ruff, cwd=str(baseline), exit_code=r.returncode,
    baseline=git(baseline, 'rev-parse', 'HEAD'), status=git(baseline, 'status', '--porcelain')))
payload = {}
for path in sorted(out.rglob('*')):
    if path.is_file():
        content = path.read_bytes()
        payload[str(path.relative_to(out))] = dict(
            bytes=len(content), sha256=hashlib.sha256(content).hexdigest(),
            git_blob_sha1=hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest())
save(out / 'index.json', dict(
    kind='Codex author focused CPU/static evidence; independent approval NOT_CLAIMED',
    formal_root=formal_root, formal_child=formal_child, files=payload,
    private_server_files_exported=False,
    previous_immutable_archive='../2026-11-09_issue31_prefix_kv/index.json',
    previous_payloads_verified=len(v1_index['files']),
    final_cpu='187 PASS,0 failure/error/skip;1 explicitly deselected preexisting W0 assertion retained with clean-baseline reproduction',
    inherited_ruff='three baseline I001 findings retained; all other scoped diagnostics and format passed'))
print(json.dumps(dict(status='PASS', output=str(out), files=len(payload),
    previous_archive_payloads_verified=len(v1_index['files']), scope='PASS'), indent=2))
