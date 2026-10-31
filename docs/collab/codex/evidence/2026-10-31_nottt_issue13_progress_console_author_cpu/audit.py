"""Author-only read-only Git/AST scope proof."""

import ast
import collections
import json
import subprocess
from pathlib import Path

ROOT=Path('/workspace/psm-wma-nottt-console')
BASE='3332d1825de8778e3d6dbb7e9ba98cbffff487c6'
FORMAL='24dbb677f7a60eeab6934c44352c7e00fa6d9b36'

def git(*words):
    return subprocess.check_output(['git','-C',str(ROOT),*words],text=True).strip()

def source(sha,name):
    return subprocess.check_output(['git','-C',str(ROOT),'show',f'{sha}:{name}'],text=True)

changed=git('diff','--name-only',BASE,FORMAL).splitlines()
assert set(changed)=={'scripts/no_ttt_console.py','scripts/train_v3_matched_no_ttt.sh',
 'scripts/train_v3_matched_no_ttt_4gpu.sh','tools/v3/no_ttt_console_test.py',
 'tools/v3/no_ttt_workers_entry_test.py','tools/v3/matched_no_ttt_entry_test.py',
 'SESSION.md','TODO.md','docs/build/PSM-WMA_V3_NoTTT_Issue13_Default_Progress_Console_2026-10-31.md'}
assert git('rev-parse',BASE+':cosmos-framework')==git('rev-parse',FORMAL+':cosmos-framework')=='0ae313e329d290fc6b8a50fda1112820fb7ac485'
tails={}
for name in ('scripts/train_v3_matched_no_ttt.sh','scripts/train_v3_matched_no_ttt_4gpu.sh'):
    before,after=source(BASE,name),source(FORMAL,name)
    old_tail=before[before.index('exec "')+len('exec '):]
    new_tail=after[after.index(' -- \\\n')+len(' -- \\\n'):].lstrip(' ')
    assert old_tail==new_tail,name
    assert before[:before.index('exec "')]==after[:after.index('exec python3')],name
    tails[name]={'all_training_command_text_identical':True,'all_prior_admission_exports_cwd_identical':True}
retained={}
for name in ('tools/v3/no_ttt_workers_entry_test.py','tools/v3/matched_no_ttt_entry_test.py'):
    def assertions(sha):
        return collections.Counter(ast.dump(node) for node in ast.walk(ast.parse(source(sha,name))) if isinstance(node,ast.Assert))
    old,new=assertions(BASE),assertions(FORMAL)
    assert not (old-new),name
    retained[name]=sum(old.values())
tree=ast.parse(source(FORMAL,'scripts/no_ttt_console.py'))
imports=[node.module.split('.')[0] if isinstance(node,ast.ImportFrom) else alias.name.split('.')[0]
         for node in tree.body if isinstance(node,(ast.Import,ast.ImportFrom))
         for alias in ([None] if isinstance(node,ast.ImportFrom) else node.names)]
assert set(imports)<={'__future__','ctypes','os','selectors','signal','subprocess','sys','tempfile','time','pathlib'}
callers=[node.name for node in tree.body if isinstance(node,ast.FunctionDef)
         if any(isinstance(call,ast.Call) and isinstance(call.func,ast.Name) and call.func.id=='_owned' for call in ast.walk(node))]
assert callers==['_cleanup']
result=dict(status='PASS_AUTHOR_READONLY_SCOPE',formal_root=FORMAL,child_gitlink='0ae313e329d290fc6b8a50fda1112820fb7ac485',
 changed_root_files=changed,training_commands=tails,original_assertions_retained=retained,
 all_child_objects_unchanged=True,helper_imports=imports,process_scan_callers=callers,
 real_training_or_DCP_GPU_run=False)
out=Path('/tmp/psm-nottt-console-20261031/audit.json')
out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
