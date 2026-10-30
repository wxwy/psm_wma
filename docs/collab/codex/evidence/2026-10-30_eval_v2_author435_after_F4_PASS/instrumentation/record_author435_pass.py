"""Record completed author acceptance only after the guarded raw package exists."""

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path("/workspace/work/psm-wma-inflight-snapshot")
FORMAL_TREE = Path("/workspace/work/psm-wma-inflight-snapshot-formal")
REL = "docs/collab/codex/evidence/2026-10-30_eval_v2_author435_after_F4_PASS"
DEST = ROOT / REL
FORMAL = "a139b5a35877a79e0a56c2208f3002f731972b11"
CHILD = "0ae313e329d290fc6b8a50fda1112820fb7ac485"


def read(path):
    return json.loads(path.read_text())


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


gate = read(DEST / "raw/gate.json")
assert gate["status"] == "PASS" and gate["source_unchanged"] is True
assert gate["junit"] == {"tests": 435, "failures": 0, "errors": 0, "skipped": 0}
assert gate["identities"] == {"root": FORMAL, "child": CHILD, "gitlink": CHILD}
assert (DEST / "raw/shell-exit.txt").read_text().strip() == "0"
before = read(DEST / "raw/source_sha256.json")
after = {name: hashlib.sha256((FORMAL_TREE / name).read_bytes()).hexdigest() for name in before}
assert len(after) == 54 and before == after
state = {"root": git(FORMAL_TREE, "rev-parse", "HEAD"),
         "child": git(FORMAL_TREE / "cosmos-framework", "rev-parse", "HEAD"),
         "gitlink": git(FORMAL_TREE, "rev-parse", "HEAD:cosmos-framework")}
assert state == gate["identities"]
assert git(FORMAL_TREE, "status", "--porcelain=v1") == ""
assert git(FORMAL_TREE / "cosmos-framework", "status", "--porcelain=v1") == ""
with (DEST / "source_after_independent.json").open("x") as stream:
    stream.write(json.dumps({"role": "DERIVED independent post-run verification; original Gate unchanged",
                             "identities": state, "root_status": "", "child_status": "",
                             "source_sha256": after, "all_equal_original_gate_before": True}, indent=2) + "\n")
readme = f"""# Author full CPU Gate after F4-P1 approval — PASS435

Formal Root `{FORMAL}`; Child/Gitlink `{CHILD}`. Executed the Owner-authorized existing unified Gate **exactly once** in the clean detached formal worktree, after directly reading GPT F4-P1 Code Gate at commit `8944539165b297ba426cfa203a5d0a95b02d5d38`. This publication is evidence bookkeeping and does not create a new source Pair.

| Group | Tests | Failure / error / skip |
| --- | ---: | --- |
| inference | 145 | 0 / 0 / 0 |
| Phase A | 256 | 0 / 0 / 0 |
| Phase B | 34 | 0 / 0 / 0 |
| Total | **435** | **0 / 0 / 0** |

Shell exit0, raw `gate.json.status=PASS`, raw `source_unchanged=true`, six completed steps exit0, exact identities and Child import origin. New progress snapshot regression and original synthetic900 are present in the full PhaseA JUnit. All54 original Gate source fingerprints match the independently recomputed after-state and both trees remain clean. Gate Ruff/format/syntax coverage follows its unchanged30-file static list; the new PhaseA regression's dedicated Ruff/format/AST proof is in the approved focused evidence at `1193e4106026f314ce89ef6ed433a6291e572b47`, not misrepresented as part of that static list.

`raw/` preserves the complete original Gate/environment/overrides/hashes, combined and three group JUnit files, import/static/group logs, wrapper console, shell exit and exact launcher. `os/` contains explicit public-file allowlists from three success OS topologies plus the two-Slot Server-death test. `os_summary.json` derives process topology, actual native batch histogram/request counts, mapping/Session evidence, independent Sim overlap and D5 ordering/barriers from those raw files. B2 is mandatory only in G1/N2/E2; other legal dynamic partial batches remain valid. F3 preserves two active Slot/Session tickets, cap1 fault marker, actual Server exit23, fault ownership, no valid Core publication and all owned process cleanup receipts. Foreign process survival and completed Resume are carried by the passed original test assertions; no separate raw artifact is fabricated for them. Store concurrency preserves two distinct UUID fault records.

All original selected bytes are mapped in `original_to_published.json`, source GitBlob bindings in `source_gitblob_bindings.json`, artifacts in `artifact_sha256.json`. Test-owned private capability values are used only in memory for leakage checks and are excluded, along with caches, whole temp trees, assignment/actor configs, runtime proofs and fake checkpoint containers.

**Request GPT author-Evidence validation only; do not reopen approved Batch/F1/F2/F3/Store/READY/F4 source reviews.** DS independent CPU remains NOT_RUN/OPEN, and this author PASS is not independent acceptance. Per the formal Review, author PASS → GPT evidence check → DS_PRO independent clean exact-Pair full Gate. No automatic DS dispatch, V3/Child merge, real GPU/Cosmos/RoboCasa/EGL/DCP/Canary/formal900/training action. The original old-Pair full434 FAIL and single diagnostic INCONCLUSIVE remain immutable historical evidence; this success does not establish that old failure's original throw-site.
"""
with (DEST / "README.md").open("x") as stream:
    stream.write(readme)
entry = f"""\n\n## 2026-10-30 — Author full435 once after F4-P1 approval: PASS / Evidence review request\n\n- Formal Pair unchanged Root `{FORMAL}` / Child+Gitlink `{CHILD}`. Fresh official89445391 exactPair APPROVE_CODE directly read; Owner-authorized existing fullCPU Gate executed exactly once in clean formal WT with NEW external evidence. No test/source/Gitlink edits, no retry. This evidence commit is bookkeeping only.\n- **435PASS =145 inference+256 PhaseA+34 PhaseB, zero failures/errors/skips, shell0, rawGate PASS/source_unchanged=true.** Allsix steps exit0/importcorrect;54 source hashes unchanged and cleanPair. New F4 and originalsynthetic900 included in actualfullPhaseA. Existing Gate static30 unchanged; newtest staticproof remains separately approvedfocused1193e410, not exaggerated.\n- Full originalJUnit/logs/Gate/environment/console/exit plus public original OS topology/B2/F3exit23/twoactiveSlot/cleanup/D5/Session/overlap receipts and StorefaultUUIDs are at `{REL}/`. Byte mappings/hashmanifest/sourceGitBlobbindings and separate independentpostsourcecheck included; private test capability/config/cache/temp excluded. No standalone foreign/Resume artifact is invented beyond passed original assertions.\n- **Request GPT new author-Evidence check only**, then independentDS exactPair once per formalReview sequence. No repeat source review/Issue reply. DS NOT_RUN/OPEN; no V3/Child merge/GPU/real900/Canary/training. Prior old434FAIL and diagnosticINCONCLUSIVE not replaced or reattributed by this PASS.\n"""
inbox = ROOT / "docs/collab/chatgpt/CODEX_INBOX.md"
previous = inbox.read_bytes()
assert b"Author full435 once after F4-P1 approval: PASS" not in previous
assert len(previous) + len(entry.encode()) <= 131072
inbox.write_bytes(previous + entry.encode())
with (ROOT / "SESSION.md").open("a") as stream:
    stream.write(f"\n\n## 2026-10-30 — Author435 exactly-once PASS / raw Evidence handoff\n\n- NewPair {FORMAL}/{CHILD}, official89445391 CodeAPPROVE sourceCLOSED; exactoneexisting unifiedGate PASS435=145+256+34,0fail/error/skip/shell0/source_unchanged=true. FormalPair unchanged,54 hashes equal/clean. No retry or codechanges.\n- Evidence `{REL}/`, complete rawJUnit/log/env/Gate/OS selected originals, sourcebindings/mapping/hashmanifest and independentaftercheck. NewF4 and original900casePASS; syntheticCPU only. Gate static30coverage distinguished from priorfocusednewteststatic.\n- Task V3-EVAL-V2-AUTHOR435-AFTER-F4 REVIEW (author executionPASS; GPT newEvidence check requested). DS NOT_RUN until evidence disposition/independent execution. Sourceold434FAIL/single900INCONCLUSIVE preserved, oldactualthrow-site not claimed. No V3/Child merge/GPU/real900/Canary/training/Issue action. Publishbookkeeping/readback thenhandoff.\n")
with (ROOT / "TODO.md").open("a") as stream:
    stream.write(f"\n- **V3-EVAL-V2-AUTHOR435-AFTER-F4** — REVIEW; Codex; exactlyone fullauthorGate PASS435=145+256+34/zero failures,errors,skips/shell0/rawPASS/sourceunchanged; exact{FORMAL}/{CHILD} unchanged/clean54hash. RawEvidence `{REL}/`; GPT authorEvidence validation next, then DS independentGate. No automatic DS/merge/GPU/Canary/real900/training.\n")
hashes = {str(p.relative_to(DEST)): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in sorted(DEST.rglob("*")) if p.is_file() and p.name != "artifact_sha256.json"}
(DEST / "artifact_sha256.json").write_text(json.dumps(hashes, indent=2) + "\n")
print(json.dumps({"formal_root": FORMAL, "artifact_hashes": len(hashes), "junit": gate["junit"],
                  "source_hashes": len(after), "inbox_bytes": inbox.stat().st_size}, indent=2))
