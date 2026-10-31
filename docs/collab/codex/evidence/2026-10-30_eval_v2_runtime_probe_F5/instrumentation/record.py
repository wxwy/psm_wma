"""Create the F5 narrow review handoff after the immutable evidence package."""

import hashlib
import json
from pathlib import Path

ROOT = Path("/workspace/work/psm-wma-runtime-evidence")
REL = "docs/collab/codex/evidence/2026-10-30_eval_v2_runtime_probe_F5"
DEST = ROOT / REL
FORMAL = "7c74dc26ac4837f193727ecf847b9b64554c18b2"
CHILD = "53c3c95202e14d3b72d236eee6899a80acf82989"
PARENT = "427b4d09cdd8070820a39b93ebf2ff832a23e359"
OLD_CHILD = "0ae313e329d290fc6b8a50fda1112820fb7ac485"
handoff = json.loads((DEST / "handoff.json").read_text())
assert handoff["formal_root"] == FORMAL and handoff["child_gitlink"] == CHILD
assert handoff["final"]["counts"] == {"tests": 85, "failures": 0, "errors": 0, "skipped": 0}
readme = f"""# EvalV2 F5-P1 — compact run identity and complete bounded probe Evidence

**Fresh narrow Code Gate request: APPROVE_CODE / REQUEST_CHANGES.** Formal Root `{FORMAL}`; Child/Gitlink `{CHILD}`. Parent source Pair `{PARENT}` / `{OLD_CHILD}`. Later evidence commit is bookkeeping, not the Formal Root. Authority is the Owner's bounded persistence-only instruction and official Review at `80583a82c578bf64bddf37bd18474c856b64366b`.

## Production change

Root changes only the public CLI persistence boundary. After the unchanged real `prepare()` has collected/verified the full vendor runtime and enforced the immutable Manifest, CLI appends a record containing `manifest_digest`, complete `evaluation_runtime` and complete `runtime_probe_evidence`. It projects the in-memory inputs for persistence and Runtime use: only `runtime` becomes `{{"digest": verified_runtime_digest}}` and raw probe evidence is removed; all model/stat/inventory, Task, library, clock and Root/Child identity fields remain. Each invocation records the sidecar's relative path and canonical SHA256. Fresh writes the compact anchor; Resume never rewrites it. Complete Evidence, anchor/cache and invocation persistence precede Runtime construction, so failed storage cannot launch an evaluation or manufacture a successful Episode.

Child changes only `store.py`, adding a 64MiB constant and `write_runtime_probe(path,value)`. The API accepts only `_internal/runtime_probe/<32-lowercase-hex>.json`, exposes no `limit` or `replace`, and uses existing safe/no-symlink/O_EXCL/NOFOLLOW/temporary-file fsync/link/directory fsync publication. Existing records cannot be overwritten. Ordinary `read`/`write` remain256KiB; `summary.json` report limit remains16MiB. Full old Store AST is identical after removing just the added constant/function. No generic JSON-limit escape hatch or truncation was introduced.

`identity.py`, `robocasa_vendor.py`, model identity/cache logic, Runtime, config and shared-GPU resources are byte-identical to the parent. Vendor per-asset SHA validation, actual runtime digest, derived Manifest runtime identity, checkpoint/source/Gitlink checks and strict Resume are unchanged. Root's other old test assertions are AST-identical; only two required runtime/probe fields were added to the existing synthetic prepare fixture. Root formal changes are CLI, that tiny fixture adjustment, one new regression module and Gitlink; Child has only the writer addition.

## Direct CPU evidence

| Run | Result | Meaning |
| --- | --- | --- |
| Old427b/0ae controlled RED | 1 FAIL, shell1 | Same new test copied untracked into old Pair; real public Fresh fails writing oversized `run_inputs.json` at Store `_publish`. Production bytes/Child unchanged; not a clean formal Gate. |
| Final7c74/53c3 focused | **85 PASS /0 failure/error/skip**, shell0 | 21 new persistence/identity/failure tests +15 existing entry +49 existing Store; clean exact Pair and10 source fingerprints unchanged. |
| Final static | **PASS** | Ruff check/format, syntax4, Root/Child diff checks; Store/fixture AST invariants, protected Blob equality, actual unmodified `verify_source()` and Child import origin. |

The public Fresh→Resume test uses150,000 deterministic synthetic asset path→SHA entries and the full `PSM_RUNTIME` stdout body. Actual sidecars are **37,200,840 and37,200,847 bytes**; compact `run_inputs.json` is **2,553 bytes**. The runtime body itself exceeds16MiB. Resume with the same verified runtime digest and only a different stdout warning appends a second full sidecar while preserving the first sidecar, anchor bytes/SHA, cache anchor binding and Core bytes. Runtime/model/config/dirty Root/committed Root/Child drift all reject before a new invocation/Runtime. Fresh/Resume storage failure does not construct Runtime, alter valid Core or create a success receipt; a failed Fresh namespace cannot be adopted and a separate new namespace succeeds. Negative cases cover ordinary256KiB reads/writes, dedicated64MiB overflow, bad paths, overwrite, leaf/parent symlinks, partial write, file fsync, link and directory fsync failures. A complete linked file surviving a failed directory fsync remains failed diagnostic residue, not successful publication.

Only the vendor/library probes and execution/physics/model boundaries are explicitly synthetic. The real `identity.prepare`, `verify_source` over mini Git fixtures, model headers/hashes/cache, public CLI, Store and Core persistence execute. The final static subprocess additionally exercises actual unmocked source admission against the clean final production Pair. These tests are not real assets, a real DCP/model load, GPU or Canary evidence. DS's reported20,989,831 bytes/123,363 assets remain DS_REPORTED; this archive does not independently attest those onsite numbers.

## Archive and disposition

Final results are `raw/final-formatted/`; `working` and pre-format `final` are clearly intermediate, not additive or the current source Pair. The initial Child condition-layout format failure is retained as debug; the final writer differs only in whitespace and its final checks pass. Old RED remains FAIL. Source diffs/bindings and protection proofs are included.

Both complete large sidecars are saved losslessly as deterministic `.json.gz` (mtime0, no filename metadata), with original/published byte counts and SHA256 plus decompressed JSON/canonical/invocation checks in `sidecar_lossless_gzip.json`. The original local JSON files are untouched. `original_to_published.json` distinguishes verbatim small/raw copies from gzip transport; decompressing reconstructs every original sidecar byte. Small anchor/cache/invocation/Manifest/Core originals are selected explicitly; whole temp/cache trees, mini Git repositories, fake checkpoints and real assets are excluded. Core before/after preservation is carried by the passed test and witness; no separate before snapshot was fabricated.

Request review of **this persistence increment only**. Do not re-review earlier435/shared-GPU63 approvals or change shared GPU/Queue/Batch/LocalTTT/NoTTT/training/checkpoint paths. The old435 Gate was not repeated. No Issue response or new formal GPT Review is generated by this author handoff; Canonical Inbox carries the request.

After fresh GPT source approval, DS may use a new independent clean exact Pair for only the originally scoped **1GPU ×2Sim ×B2 ×4 total Episode Canary**. Use a fresh output namespace, retain `verify_source`, and re-confirm that the chosen checkpoint is complete and stably readable; this is not permission to stop training, patch old SHA, expand JSON limits or run900 Episodes. Real Canary is still paused/pending approval and new execution evidence. No V3/Child production merge or real run is performed by this code publication.
"""
with (DEST / "README.md").open("x") as stream:
    stream.write(readme)
next_run = {"formal_root": FORMAL, "child_gitlink": CHILD,
            "scope": "Same original Canary only: 1GPU/2Sim/B=2/4 total Episodes",
            "required_before_execution": ["Fresh GPT narrow Code Gate approval for this Pair",
                                          "Independent clean exact source/Child/Gitlink",
                                          "New output namespace; never adopt prior failed Fresh",
                                          "DS re-confirms complete stable checkpoint"],
            "not_executed": True, "no_full435_replay_required_by_current_Owner_scope": True,
            "prohibited": ["V3/Child merge without separate authority", "old-SHA patch/bypass",
                           "source/vendor checks disabled", "shared GPU logic/config change",
                           "training/checkpoint mutation", "900 Episode expansion"]}
(DEST / "next_canary_handoff.json").write_text(json.dumps(next_run, indent=2) + "\n")
entry = f"""\n\n## 2026-10-30 — F5-P1 run_inputs oversize / new persistence-only Code Gate request\n\n- **Formal Root `{FORMAL}` / Child+Gitlink `{CHILD}`**, parent `{PARENT}` / `{OLD_CHILD}`. Owner-approved minimal persistence repair after direct exactReview80583a82/blob bfbfc5c3. This is fresh narrow APPROVE_CODE / REQUEST_CHANGES request, not realCanary evidence or prior435/sharedGPU re-review. Later docs/evidence HEAD is bookkeeping only.\n- RootCLI projection only: full verifiedruntime/probe+manifest binding→append-only internalEvidence, boundedrun_inputs keeps runtime.digest/allother identity fields; Resumeanchor neverrewritten, invocation sidecarrelativepath/canonicalSHA. ChildStore adds dedicated64MiB writer restricted _internal/runtime_probe/32hex.json, no replace/limit publicescape; existing256KiB read/write and16MiB summary +allordinaryStoreAST unchanged. Vendor/identity/verify_source/modelcache/Runtime/resources/config protectedBlobs unchanged. SharedGPU/Queue/Batch/NoTTT untouched.\n- Controlled oldRED1FAIL/shell1 hits realStore oversizedJSON; same newtesthash butoldworktree hasuntrackedtest, notformalcleanGate. **FinalexactcleanPair85PASS=21new+15entry+49Store,0fail/error/skip,shell0**, sourcehashes10unchanged; finalRuff/format/syntax4/diff/AST/protectedblob/actualunmockedsourceadmission PASS. Working/pre-format runs andinitialformatdebug retained separately, notaddedtotals.\n- RealpublicFresh→Resume onsynthetic150k assetSHA table: fullsidecars37,200,840/37,200,847B, smallanchor2,553B; fullruntime>16MiB, complete map/stdout retained, warning-onlyResumeappend andunchangedanchor/Core/cachebinding. Identitydrift/ordinary256KiB/private64MiB/path/symlink/overwrite/partial/fsync/link/fail-beforeRuntime negativesPASS. Vendor/library/execution CPUdoubles explicit; originalperassetverificationsourceunchanged. OnsiteDS21MB/123363 remainsDSreported, no realassetsaccess.\n- Evidence `{REL}/`: rawXML/log/env/commands/fingerprints, complete sidecars gzip-losslesswithoriginalSHA/bytes/invocationcanonicalchecks, smallCore/identity originals, sourcebindings/diffs anddeterministictests. No fulltmp/cache/fakecheckpoint/miniGit dump. No435replay/sharedGPUchange/GPU/realCanary/train/900/Issue response/V3merge.\n- Publish isolated **Child thenRoot** andreadback; STOP forGPT freshnarrow CodeGate. Afterapproved sourceonly nextnative action remainsoriginal1GPU×2Sim×B2×4Episode Canary innewcleanPair/newnamespace withcheckpoint availabilityrechecked byDS. Do notreuseoldfailedFreshorbypassverify_source.\n"""
inbox = ROOT / "docs/collab/chatgpt/CODEX_INBOX.md"
previous = inbox.read_bytes()
assert b"F5-P1 run_inputs oversize / new persistence-only Code Gate request" not in previous
assert len(previous) + len(entry.encode()) <= 131072
inbox.write_bytes(previous + entry.encode())
with (ROOT / "SESSION.md").open("a") as stream:
    stream.write(f"\n\n## 2026-10-30 — F5-P1 source freeze and narrow CPU handoff\n\n- FinalRoot{FORMAL}/Child-Gitlink{CHILD}, parent427b/0ae; productionCLI20+/1- andChildwriter10+ only, oldidentity/vendor/modelguard/runtime/resources/config bytesunchanged. OrdinaryStoreASTunchangedexceptnew64MiBwriter/constant; oldentryassertionsunchangedexceptfake_preparetwofields. Final85PASS=21new+15entry+49Store/0skip,shell0,cleanPair/source10hashstable; static5checks/syntax4/scopeproof/realverify_source PASS. OldRED1oversizedFAIL retained, working+preformat andformatdebug areintermediateonly.\n- Complete synthetic150kassetSHA publicFreshResume sidecars37,200,840/37,200,847B, anchor2553B; warning-onlyappend/runtimeDigeststable/anchorCore/cachebindingstable; allidentity/storagefailclosednegativesPASS. Evidence `{REL}/` includes losslessgz largeoriginals+SHA/bytes andrawsmall/JUnit/log/sourceproof. NoactualDSraw/realassets/GPU/training.\n- V3-EVAL-V2-F5-P1 REVIEW; CanonicalInbox requestsGPT fresh persistence-only CodeGate. IsolatedChildthenRootpublish/readbackSTOP; originalCanary1GPU2SimB2total4onlyafterapproval, newnamespace/checkpointavailabilitycheck. No435replay/DSrun/sharedGPUpatch/V3merge/Issue response/900.\n")
with (ROOT / "TODO.md").open("a") as stream:
    stream.write(f"\n- **V3-EVAL-V2-F5-P1** — REVIEW; Codex; FormalRoot{FORMAL}/Child{CHILD}. Finalnarrow85PASS/0fail,error,skip + static/scope/realSourceCheckPASS; oldoversizeRED1FAIL, synthetic150kMap37MBsidecars/2553Banchor FreshResumeverified. Evidence `{REL}/`; publishChild→Root thenGPTnarrowCodeGateSTOP. No435/sharedGPU/GPU/Canary/train/900/merge.\n")
hashes = {str(p.relative_to(DEST)): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in sorted(DEST.rglob("*")) if p.is_file() and p.name != "artifact_sha256.json"}
(DEST / "artifact_sha256.json").write_text(json.dumps(hashes, indent=2) + "\n")
print(json.dumps({"formal_root": FORMAL, "child": CHILD, "artifact_hashes": len(hashes),
                  "inbox_bytes": inbox.stat().st_size}, indent=2))
