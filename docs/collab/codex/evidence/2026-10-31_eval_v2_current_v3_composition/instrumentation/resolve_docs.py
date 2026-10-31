"""Resolve append-only ledger conflicts while preserving canonical V3 bytes."""
from pathlib import Path
import hashlib,json,subprocess
root=Path('/workspace/work/psm-wma-v3-eval-merge')
out=Path(__file__).parent/'merge-doc-originals'
out.mkdir()
def git(*args):return subprocess.check_output(['git','-C',str(root),*args])
records=[]
for name in ('SESSION.md','TODO.md','docs/collab/chatgpt/CODEX_INBOX.md'):
    base=git('show',':1:'+name)
    ours=git('show',':2:'+name)
    theirs=git('show',':3:'+name)
    canonical=git('show','369f3f4d82b8694b7efee5d5b16589d82aa00547:'+name)
    assert theirs.startswith(base),name+' candidate did not append'
    assert ours.startswith(canonical),name+' task claim did not append'
    suffix=theirs[len(base):]
    claim=ours[len(canonical):]
    result=canonical+b'\n\n<!-- Historical F5 candidate entries imported byte-for-byte; current approval and Owner merge directive supersede their old pending status. -->\n'+suffix+claim
    assert result.startswith(canonical)
    assert suffix in result
    assert name!='docs/collab/chatgpt/CODEX_INBOX.md' or len(result)<=131072
    (root/name).write_bytes(result)
    for label,raw in (('base',base),('ours',ours),('theirs',theirs),('canonical',canonical),('resolved',result)):
        p=out/(Path(name).name+'.'+label)
        p.write_bytes(raw)
    records.append({'path':name,'canonical_prefix_preserved':True,'candidate_suffix_preserved':True,
                    'canonical_sha256':hashlib.sha256(canonical).hexdigest(),
                    'result_sha256':hashlib.sha256(result).hexdigest(),'result_bytes':len(result)})
(out/'resolution.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(records))
