"""Exact donor transfer/current canonical preservation. Git objects only."""

import hashlib
import json
import subprocess
from pathlib import Path

ROOT=Path('/workspace/psm-wma-nottt-port')
CHILD=ROOT/'cosmos-framework'
BASE='0ae313e329d290fc6b8a50fda1112820fb7ac485'
DONOR='224c5f3c0bd6911bb49cb6bb0895ba7da53ff822'
FORMAL='baf1b5bf46853e9849a91518803b9738fc216235'
ROOT_FORMAL='c66ade95b044d3664cd782d43d7917a604425db3'
ROOT_BASE='2bcc27e94576837167cacd190af7dc837e6129cd'

def git(where,*args):
    return subprocess.check_output(['git','-C',str(where),*args])

def tree(sha):
    return {line.split(b'\t',1)[1].decode():line.split(b'\t',1)[0].decode()
            for line in git(CHILD,'ls-tree','-r','--full-tree',sha).splitlines()}

inventory=json.loads((ROOT/'docs/build/PSM-WMA_V3_NoTTT_Async_Lazy_Port_inventory_2026-10-31.json').read_text())
before,donor,after=(tree(sha) for sha in (BASE,DONOR,FORMAL))
allowed=set(inventory['files'])
changed={name for name in before.keys()|after.keys() if before.get(name)!=after.get(name)}
assert changed==allowed,(changed-allowed,allowed-changed)
for name,row in inventory['files'].items():
    assert after[name]==donor[name],name
    assert hashlib.sha256(git(CHILD,'show',FORMAL+':'+name)).hexdigest()==row['sha256'],name
outside=set(before)|set(after)
outside-=allowed
assert all(before.get(name)==after.get(name) for name in outside)
protected={}
for name in ('cosmos_framework/evaluation','cosmos_framework/inference','cosmos_framework/simulation',
             'cosmos_framework/model','cosmos_framework/checkpoint','cosmos_framework/configs','packages','uv.lock'):
    left=git(CHILD,'rev-parse',BASE+':'+name).decode().strip()
    right=git(CHILD,'rev-parse',FORMAL+':'+name).decode().strip()
    assert left==right,name
    protected[name]=right
training_equal={}
for name in ('cosmos_framework/trainer','cosmos_framework/data','cosmos_framework/model',
             'cosmos_framework/checkpoint','cosmos_framework/utils','cosmos_framework/configs','examples','uv.lock'):
    left=git(CHILD,'rev-parse',DONOR+':'+name).decode().strip()
    right=git(CHILD,'rev-parse',FORMAL+':'+name).decode().strip()
    assert left==right,name
    training_equal[name]=right
assert git(ROOT,'rev-parse',ROOT_FORMAL+':cosmos-framework').decode().strip()==FORMAL
root_delta=git(ROOT,'diff','--name-only',ROOT_BASE,ROOT_FORMAL).decode().splitlines()
assert all(name in ('SESSION.md','TODO.md','cosmos-framework','tools/v3/no_ttt_async_port_test.py')
           or name.startswith('docs/build/PSM-WMA_V3_NoTTT_Async_Lazy_') for name in root_delta)
launchers={}
for name in ('scripts/train_v3_matched_no_ttt.sh','scripts/train_v3_matched_no_ttt_4gpu.sh'):
    base_blob=git(ROOT,'rev-parse',ROOT_BASE+':'+name).decode().strip()
    current=git(ROOT,'rev-parse',ROOT_FORMAL+':'+name).decode().strip()
    approved=git(ROOT,'rev-parse','fd9021b0908b4b2763b3d02508b1f34df377dc97:'+name).decode().strip()
    assert base_blob==current==approved,name
    launchers[name]=current
assert git(ROOT,'ls-tree',ROOT_FORMAL,'scripts/no_ttt_console.py')==b''
result=dict(status='PASS_AUTHOR_GIT_OBJECT_EQUIVALENCE',root=ROOT_FORMAL,child=FORMAL,
    canonical_base_child=BASE,approved_donor_child=DONOR,exact_donor_paths=len(allowed),
    production_paths=6,test_support_paths=7,outside_allowlist_objects_preserved=len(outside),
    protected_canonical_trees=protected,whole_training_trees_equal_donor=training_equal,
    root_changed_paths=root_delta,root_launchers_equal_both_base_and_donor=launchers,
    issue13_not_included=True,real_training_or_dcp_gpu_rerun=False)
Path('/tmp/psm-nottt-port-20261031/audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
