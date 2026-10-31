"""Prove the isolated merge is a union of approved Git objects, no source edits."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path('/workspace/work/psm-wma-v3-eval-merge')
CHILD=ROOT/'cosmos-framework'
BASE=Path(__file__).parent
V3='369f3f4d82b8694b7efee5d5b16589d82aa00547'
EVAL='d18b420c02cfc51a1b85e9f1d6ce5d26f7bd3163'
TRAIN='baf1b5bf46853e9849a91518803b9738fc216235'
EC='2f7334c4ada6ace1d21185985aae90539052bf18'
MERGE='4139ad245b73cc1c16c9d4954241cecb81478992'
MC='6c83596d6a259e89c4cd3e79424024983426ac3d'
def run(repo,*args): return subprocess.check_output(['git','-C',str(repo),*args])
def tree(repo,ref):
    result={}
    for raw in run(repo,'ls-tree','-rz','--full-tree',ref).split(b'\0'):
        if raw:
            fields,path=raw.split(b'\t',1)
            mode,kind,sha=fields.decode().split()
            result[path.decode()]={'mode':mode,'type':kind,'sha':sha}
    return result

def composition(repo,left,right,actual,ledgers=(),gitlink=None):
    common=run(repo,'merge-base',left,right).decode().strip()
    base,a,b,c=(tree(repo,ref) for ref in (common,left,right,actual))
    change_a={k for k in set(a)|set(base) if a.get(k)!=base.get(k)}
    change_b={k for k in set(b)|set(base) if b.get(k)!=base.get(k)}
    overlap=(change_a&change_b)-set(ledgers)
    if gitlink: overlap.discard('cosmos-framework')
    assert not overlap,overlap
    want=dict(a)
    for key in change_b-set(ledgers)-({'cosmos-framework'} if gitlink else set()):
        if key in b: want[key]=b[key]
        else: want.pop(key,None)
    if gitlink: want['cosmos-framework']={'mode':'160000','type':'commit','sha':gitlink}
    for k in (set(want)|set(c))-set(ledgers):
        assert want.get(k)==c.get(k),k
    records=[]
    for key in ledgers:
        old=run(repo,'show',left+':'+key)
        new=run(repo,'show',actual+':'+key)
        assert new.startswith(old),key
        records.append({'path':key,'canonical_bytes_prefix_preserved':True,'before_sha256':hashlib.sha256(old).hexdigest()})
    assert run(repo,'merge-base','--is-ancestor',left,actual)==b''
    assert run(repo,'merge-base','--is-ancestor',right,actual)==b''
    return {'base':common,'canonical_parent':left,'approved_candidate':right,'composed':actual,
            'canonical_changed_paths':sorted(change_a),'candidate_changed_paths':sorted(change_b),
            'unresolved_source_overlap':sorted(overlap),'tree_objects':len(c),'union_object_match':True,
            'ledger_prefixes':records}
child=composition(CHILD,TRAIN,EC,MC)
root=composition(ROOT,V3,EVAL,MERGE,('SESSION.md','TODO.md','docs/collab/chatgpt/CODEX_INBOX.md'),MC)
for repo in (ROOT,CHILD):
    assert run(repo,'status','--porcelain=v1')==b''
proof={'status':'PASS','root':root,'child':child,'canonical_publication':'NOT_DONE',
       'exact_original_Child_target':'2f7334c4 cannot also retain newly promoted baf1b5bf; Owner confirmation pending',
       'checked_out_root':run(ROOT,'rev-parse','HEAD').decode().strip(),
       'checked_out_child':run(CHILD,'rev-parse','HEAD').decode().strip()}
(BASE/'object_audit.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps({'status':proof['status'],'root_objects':root['tree_objects'],'child_objects':child['tree_objects'],
                  'child_nonoverlap':True,'source_objects_exact_union':True,'root':MERGE,'child':MC}))
