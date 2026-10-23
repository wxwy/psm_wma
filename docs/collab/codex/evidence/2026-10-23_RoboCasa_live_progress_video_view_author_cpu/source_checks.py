import ast
import hashlib
import json
import subprocess
from pathlib import Path

root = Path('/workspace/psm_wma')
base = '07cd858ee7dd4edabfa1a7b694745c80e4c86bad'
child_base = 'c9f21040f462a114d597fc83773cb9b6a9e96214'
files = [
 'scripts/eval_robocasa_18task_queue.py', 'scripts/robocasa_eval_config.py',
 'scripts/robocasa_eval_progress.py', 'scripts/robocasa_eval_video_view.py',
 'tools/v3/eval_robocasa_queue_identity_test.py', 'tools/v3/robocasa_eval_config_test.py',
 'tools/v3/robocasa_eval_progress_test.py', 'tools/v3/robocasa_eval_video_view_test.py',
 'cosmos-framework/cosmos_framework/simulation/robocasa/closed_loop_eval.py',
 'cosmos-framework/cosmos_framework/utils/rollout_progress.py',
 'cosmos-framework/cosmos_framework/utils/rollout_progress_test.py',
]
def show(directory, ref, path):
 return subprocess.check_output(['git', 'show', f'{ref}:{path}'], cwd=directory)
def function(source, name):
 return next(node for node in ast.walk(ast.parse(source)) if isinstance(node, ast.FunctionDef) and node.name == name)
def tree(node):
 return ast.dump(node, include_attributes=False)
old = show(root, base, files[0])
new = (root/files[0]).read_bytes()
checks = {}
for name in ['server_argv', 'validate_server_info', 'wait_server', 'task_result', 'task_video_files']:
 checks[name + '_unchanged'] = tree(function(old, name)) == tree(function(new, name))
def protocol(source):
 call = next(node for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'build_verified_evaluation_identity')
 return next(item.value for item in call.keywords if item.arg == 'protocol')
checks['protocol_AST_unchanged'] = tree(protocol(old)) == tree(protocol(new))
for path in ['scripts/robocasa_processes.py', 'scripts/robocasa_eval_results.py', 'scripts/v3_evaluation_identity.py', 'scripts/robocasa_vendor.py', 'third_party/robosuite_patches/vendor.lock.json']:
 checks[path + '_unchanged'] = show(root, base, path) == (root/path).read_bytes()
child = root/'cosmos-framework'
for path in ['cosmos_framework/utils/rollout_evidence.py', 'cosmos_framework/simulation/robocasa/local_memory_client.py']:
 checks[path + '_unchanged'] = show(child, child_base, path) == (child/path).read_bytes()
checks['authoritative_episode_emit_AST_unchanged'] = tree(function(show(child,child_base,'cosmos_framework/simulation/robocasa/closed_loop_eval.py'), 'emit')) == tree(function((child/'cosmos_framework/simulation/robocasa/closed_loop_eval.py').read_bytes(), 'emit'))
assert all(checks.values()), checks
payload = {'baseline_root':base,'baseline_child':child_base,'checks':checks,'source_sha256':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in files},'limitations':'Static boundary checks plus focused CPU evidence; not whole-repository, GPU, policy-load, simulator or DS acceptance.'}
Path('/tmp/psm-v3-live-progress-20261023/source_checks.json').write_text(json.dumps(payload,indent=2)+'\n')
print(json.dumps({'static_contract_checks':len(checks),'passed':all(checks.values()),'python_sources':len(files)}))
