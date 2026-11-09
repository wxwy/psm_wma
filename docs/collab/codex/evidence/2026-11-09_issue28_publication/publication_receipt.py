"""Record verified PR/source/evidence availability; documentation-only changes."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo

root=Path('/workspace/work/psm-wma-history-k-issue28')
child=root/'cosmos-framework'
src=Path(__file__).parent
pair=dict(root='050e45d87fe5faf3a830bcaf4629fd7d16ba47a7',child='59746af006748488a678aa9a55dfc3e200668219')
head='f30c9750ba28a674e8381648360eef3a68f570e7'
branch='v3-local-ttt-history-k-issue28-20261109'
base='v3-shared-vae-topology-issue27-20261109'
def git(repo,*args):
 return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()
assert git(root,'rev-parse','HEAD')==head and git(child,'rev-parse','HEAD')==pair['child']
assert not git(root,'status','--porcelain') and not git(child,'status','--porcelain')
checks=json.loads((src/'remote_file_readback.json').read_text())
prs=json.loads((src/'pr_readback.json').read_text())['checks']
assert len(checks['checks'])==52 and all(p['match'] for p in checks['checks'])
assert all(p['body_matches'] and p['draft'] and not p['merged'] for p in prs)
def advertised(repo,names):
 lines=git(repo,'ls-remote','origin',*['refs/heads/'+n for n in names]).splitlines()
 return {line.split()[1].removeprefix('refs/heads/'):line.split()[0] for line in lines}
root_refs=advertised(root,['V3',base,branch])
child_refs=advertised(child,['v3-local-ttt',base,branch])
assert root_refs=={'V3':'e58cef1f53d2382d39c871ce5a50e4acdd5ce268',base:'73d8644df3096e192a83fff2f2d8098a4ac11e64',branch:head}
assert child_refs=={'v3-local-ttt':'b0dbd115d03e801ec4d0788c30ee0b0e9655d4db',base:'60b252d05157b2753d2caebae32b11c878504bbe',branch:pair['child']}
assert git(root,'rev-parse','origin/'+branch)==head
assert git(child,'rev-parse','origin/'+branch)==pair['child']
assert git(root,'rev-parse','origin/'+branch+':cosmos-framework')==pair['child']
subprocess.check_call(['git','merge-base','--is-ancestor',pair['root'],'origin/'+branch],cwd=root)
subprocess.check_call(['git','diff','--exit-code',pair['root'],'origin/'+branch,'--','scripts','tools','cosmos-framework'],cwd=root)
fingerprints=json.loads((src/'author03/source_before.json').read_text())
assert all(hashlib.sha256((root/p).read_bytes()).hexdigest()==h for p,h in fingerprints.items())
folder=root/'docs/collab/codex/evidence/2026-11-09_issue28_publication'
folder.mkdir(parents=True,exist_ok=False)
for name in ('remote_file_readback.json','pr_readback.json','publication_expectations.json','publication_receipt.py'):
 shutil.copyfile(src/name,folder/name)
stamp=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
receipt=dict(timestamp=stamp,formal_pair=pair,gitlink=pair['child'],evidence_head=head,
 source_and_evidence_files_checked=52,all_remote_blob_shas_match=True,root_advertised=root_refs,child_advertised=child_refs,
 fetched_refs_and_gitlink_match=True,formal_root_is_ancestor=True,source_same_since_author_Gate=True,
 source_fingerprint_files=len(fingerprints),new_prs=prs[:2],qualified_prior_prs_unchanged=prs[2:],
 author_tests=631,author_subtests=207,author_junit=838,independent_approval='NOT_CLAIMED',
 GPU_remote_server_files_training_simulation_SR_900_V3_merge='NOT_RUN')
(folder/'publication_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
handoff=root/'docs/collab/codex/reviews/2026-11-09_Issue28_HistoryK_050e45d8_59746af0_Code_Review_Request.md'
with handoff.open('a') as f:
 f.write(f'''\n## Publication readback — {stamp}\n\nNew independent Draft [Root PR #30](https://github.com/wxwy/psm_wma/pull/30)
and [Child PR #9](https://github.com/wxwy/cosmos-framework/pull/9) are open,
unmerged. Stacked bases are qualified #27 branches; no merge into those bases is
authorized. Retarget after #27 lands and approvals permit it. Prior PR29/8 heads,
bodies and state are unchanged. Remote readback52/52 source/test/raw evidence/
Gate/JUnit/provenance/OS/Inbox/approval/archive Blob SHAs match local Git; fresh
advertised and fetched refs/Gitlink match, source matches final author Gate.
Receipt: `docs/collab/codex/evidence/2026-11-09_issue28_publication/publication_receipt.json`.
This publication ledger is a docs descendant, not a new implementation Pair or
independent verdict. Formal pair remains Root `{pair['root']}` / Child
`{pair['child']}`. Fresh GPT code/evidence review requested.\n''')
inbox=root/'docs/collab/chatgpt/CODEX_INBOX.md'
entry=f'''\n\n### {stamp} — Issue28 publication receipt, same review request\n
Formal Root `{pair['root']}` / Child-Gitlink `{pair['child']}` unchanged.
New Draft RootPR30 https://github.com/wxwy/psm_wma/pull/30 and ChildPR9
https://github.com/wxwy/cosmos-framework/pull/9 open/unmerged; qualified#27
stacked bases only, no base/V3 merge. Readback52/52 remote source/test/raw
evidence/Gate/JUnit/proofs/Inbox/archive Blob SHAs match; fetched/advertised refs
andGitlink match, source identical to final authorGate. PriorPR29/8 heads/bodies
unchanged; officialV3 e58cef1f/Childofficialb0dbd115 unchanged at this check.
Receipt docs/collab/codex/evidence/2026-11-09_issue28_publication/publication_receipt.json.
631tests+207subtests/838JUnit authorPASS is evidence, no independent code/hardware
approval inferred. TaskREVIEW; fresh GPT incremental Gate requested.\n'''
old=inbox.read_bytes()
assert len(old)+len(entry.encode())<=131072
inbox.write_bytes(old+entry.encode())
session=root/'SESSION.md'
session.write_text(f'''# {stamp} — Issue28 new Draft PRs published;52 remote file readbacks match

Formal Root {pair['root']} / Child-Gitlink {pair['child']} unchanged. New open
Draft RootPR30 https://github.com/wxwy/psm_wma/pull/30 and ChildPR9
https://github.com/wxwy/cosmos-framework/pull/9; narrow stacked#27 review bases.
No merge into bases/V3; retarget only after #27 lands/approvals. PriorPR29/8
head/body unchanged, officialRootV3 e58cef1f/Childofficialb0dbd115 unchanged at
this observation. Fresh git fetch/advertised/tracking,Gitlink,ancestor and source
tree checks passed.52/52 remote source/test/rawJUnit/Gate/fingerprints/OS proof/
handoff/Inbox/oldapproval/archive Blob SHAs equal local. Receipt under
docs/collab/codex/evidence/2026-11-09_issue28_publication/; all source fingerprints
still match final author03. Publication/evidence headf30c9750 is docs descendant,
not implementation authority. Final631tests+207subtests=838JUnit authorPASS,
shell0/gatePASS/sourceunchanged/static21/denseK16 CPU parity; original failures
and controlledRED8/GREEN8 retained. TaskREVIEW; fresh GPT incremental review
requested, independent approval not claimed. No GPU/remote server files/realSim/
SR/900EP/training/live eval/running-job or official merge operations. Only final
publication ledger push/readback remains; source/test work is complete.

'''+session.read_text())
receipt['canonical_inbox_before_bytes']=len(old)
receipt['canonical_inbox_after_bytes']=inbox.stat().st_size
(folder/'publication_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(status='PUBLICATION_VERIFIED',remote_files=52,root_pr=30,child_pr=9,
 formal_pair=pair,inbox_bytes=inbox.stat().st_size),indent=2))
