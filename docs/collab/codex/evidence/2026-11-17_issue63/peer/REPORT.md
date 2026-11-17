# Issue63 local read-only peer review

Verdict: **LOCAL_REQUEST_CHANGES — one P2 finding**.

- Exact Root: `98172110677b7631f5b7974003ffae664bdd0b85`
- Exact Child/Gitlink: `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`
- Nav reference: `70eb7b447e65d793b0ebe18b258291ce46f057c1`
- Base: `d0bb45343a047fdf90d8e376acf4502fdf13fff4`
- Reviewer: independent local Agent `/root/issue63_peer_review`, after author entered REVIEW, as required by AGENTS.md. This is not GPT/server/capacity approval.

Read AGENTS.md, SESSION.md, canonical live CODEX_INBOX.md tail, TODO.md, MEMORY/DECISIONS.md and `docs/build/PSM-WMA_G2_source_capsule_issue63_2026-11-17.md`. Owner Issue63's local code/CPU/Draft then STOP boundary supersedes historical V2/MM/Kimi monitoring instructions. No fetch, checkout, reset, pull, source/test/old-evidence edit, install, server/private-data access, GPU/native/Wan/weights execution, training, deletion of original assets, publication or merge was performed. All permanent reviewer artifacts are in this peer directory. Own synthetic fixtures are in fresh `/tmp/g2_issue63_peer_*` namespaces; the mistakenly placed initial fixture tree was relocated intact to `/tmp/g2_issue63_peer_misplaced_98172110`.

## P2-63-PEER-1 — retirement proof fields are outside the SQL-bound capsule's checked hash graph

Primary location: `g2/latent_cache/final_source.py:176` through the receipt checks at line196. Collector consequence: `g2/latent_cache/ledger_archive.py:26` through line35, and archival at line196 onward.

The immutable capsule records `attestation.working_proof_sha256` and `attestation.work_cleanup_sha256`. Its `working_source` records both original source/READY hashes. However, `verify_reader_binding()` never compares those identities with `SOURCE_RETIREMENT.json`'s `working_proof`, `work_cleanup` or `retired_files`. The episode COMPLETE hash authenticates the receipt only through a field in COMPLETE that is outside the durable SQL capsule binding. After journal removal, `published_proof()` checks the SQL capsule SHA and scope, then accepts the inconsistent receipt and allows ledger GC.

Concrete independent reproduction, with actual acknowledged synthetic job and original verifiers:

1. Stop archival at `capsule_journal_removed`, after valid v2 publication and before active-ledger GC.
2. Leave the capsule and SQL `retirement` value unchanged.
3. Change exactly one retirement-receipt component: set `working_proof.source_id` to an unrelated hash; replace `work_cleanup` with `{"status":"kept_by_explicit_config"}`; or change `retired_files.spatial_source.json` to an unrelated hash.
4. Update only `COMPLETE.json.source_retirement_sha256` to the new receipt SHA.
5. Call the actual `spool.reap(job)`.

Expected: the original capsule attestation/working binding rejects the receipt and preserves the active job for diagnosis. Observed: all three variants are accepted and archived. `receipt.json` independently reads the resulting SQLite databases and tombstones: each has zero active jobs, one completed job and the exact original SQL-bound capsule SHA, while one corresponding immutable proof relation is false. These are three manifestations of one missing semantic-binding check.

Probe: `test_independent_protocol.py`, SHA256 `cbc86a7b29e529fd5ace678fe5a10a78303aaefe25d71e470c23df2959883a1f`. Raw RED: `independent.log` and `independent.xml` (three `DID NOT RAISE CacheError` failures). The probe is unchanged and can be replayed against the next fixed candidate.

Required narrow closure: verify the working-proof and cleanup fingerprints against the capsule's attestation; verify both retired-file hashes against the capsule's historical source/READY binding; check other duplicated receipt/capsule provenance fields for equivalent consistency. Place the shared enforcement in final reader/profile verification so both standalone validation and the acknowledged collector reject the inconsistent publication. Preserve original PT/product bytes and the SQL capsule anchor. Replaying the unchanged three cases should reject all three variants before ledger GC.

## Checks and results

- Unchanged targeted author tests: **47 PASS, one deliberately deselected**, zero skips/failures/errors, 112.00s. This includes actual hard exits at22 transaction/ledger boundaries, two real fsynced atomic-temp exits, competing writers/readers, SQL final binding, retained work rejection and the actual supervisor stop/crash/resume path.
- Independent probes: **two PASS, three expected RED failures**, 16.62s. The two passing probes verify legacy readers make no write-mode open or new lock file, and a retired v2 post-hoc resume runs no Encode1 and rewrites no file.
- Source binding: all235 author-audited source hashes still match both current files and the exact frozen Git blobs. Root/Child still match the pair above. `receipt.json` and `receipt.log` record the verification and all raw evidence hashes.
- Initial harness-placement run: one PASS,46 fixture setup failures, one deselected,8.04s. Its `peer/pytest_tmp` was under the protected Git code root; production correctly refused that namespace. `focused.log/xml` are preserved separately. This is not a product defect or a candidate regression result.
- Static review covered final capsule projection/owner materialization, explicit v1/v2 schema dispatch, original payload-source adaptation, bootstrap/permanent reader leases, source-retirement policy/SQL intent/fsync/mutation order/recovery, managed-work cleanup, final tombstones/late events, production queue integration and read-only capacity/operator tools. No additional confirmed P1/P2 was identified in that scope.

The author counts, focused47 and independent probes overlap and must not be summed. The entire549-item author collection was not rerun. The positive optional archive test was deliberately deselected because its fixture creates an archive in `/dev/shm`; optional archive constraints and code were reviewed statically. No real169 Wan reencode,419 pixel comparisons, real file-size/read-latency measurement,18-task capacity audit,32-worker resource experiment or full9126 execution was performed or approved. Existing missing PyArrow/MuJoCo/Pandas dependencies were not installed.

## Actual commands

All project execution commands were announced before launch. Cwd for all commands was `/workspace/psm_wma_issue52`. Tests used the existing interpreter, synthetic CPU inputs and no network/GPU access.

```bash
mkdir -p docs/collab/codex/evidence/2026-11-17_issue63/peer
env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 COSMOS_DEVICE=cpu COSMOS_TRAINING=0 COSMOS_INTERNAL=0 PYTHONPATH=/workspace/psm_wma_issue52:/workspace/psm_wma_issue52/cosmos-framework /workspace/.venvs/g2-view-vae-52/bin/python -m pytest -q -p no:cacheprovider --tb=short -rs g2/tests/test_source_capsule.py g2/tests/test_source_capsule_entrypoints.py g2/tests/test_source_retirement_faults.py g2/tests/test_source_retirement_atomic.py -k 'not optional_full_audit_is_lossless_and_outside_output_filesystem' --basetemp=docs/collab/codex/evidence/2026-11-17_issue63/peer/pytest_tmp --junitxml=docs/collab/codex/evidence/2026-11-17_issue63/peer/focused.xml > docs/collab/codex/evidence/2026-11-17_issue63/peer/focused.log 2>&1
env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 COSMOS_DEVICE=cpu COSMOS_TRAINING=0 COSMOS_INTERNAL=0 PYTHONPATH=/workspace/psm_wma_issue52:/workspace/psm_wma_issue52/cosmos-framework /workspace/.venvs/g2-view-vae-52/bin/python -m pytest -q -p no:cacheprovider --tb=short -rs g2/tests/test_source_capsule.py g2/tests/test_source_capsule_entrypoints.py g2/tests/test_source_retirement_faults.py g2/tests/test_source_retirement_atomic.py -k 'not optional_full_audit_is_lossless_and_outside_output_filesystem' --basetemp=/tmp/g2_issue63_peer_98172110 --junitxml=docs/collab/codex/evidence/2026-11-17_issue63/peer/focused2.xml > docs/collab/codex/evidence/2026-11-17_issue63/peer/focused2.log 2>&1
mv docs/collab/codex/evidence/2026-11-17_issue63/peer/pytest_tmp /tmp/g2_issue63_peer_misplaced_98172110
env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 COSMOS_DEVICE=cpu COSMOS_TRAINING=0 COSMOS_INTERNAL=0 PYTHONPATH=/workspace/psm_wma_issue52:/workspace/psm_wma_issue52/cosmos-framework /workspace/.venvs/g2-view-vae-52/bin/python -m pytest -q -p no:cacheprovider --tb=short -rs docs/collab/codex/evidence/2026-11-17_issue63/peer/test_independent_protocol.py --basetemp=/tmp/g2_issue63_peer_protocol_98172110 --junitxml=docs/collab/codex/evidence/2026-11-17_issue63/peer/independent.xml > docs/collab/codex/evidence/2026-11-17_issue63/peer/independent.log 2>&1
env PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 CUDA_VISIBLE_DEVICES='' /workspace/.venvs/g2-view-vae-52/bin/python docs/collab/codex/evidence/2026-11-17_issue63/peer/collect_peer_receipt.py > docs/collab/codex/evidence/2026-11-17_issue63/peer/receipt.log 2>&1
```

The first test command exited1 for fixture placement; corrected focused command exited0; independent probe exited1 for the three reproduced contract failures; final source/observation audit exited0. No source fix was made by the reviewer. Review artifacts are uncommitted when this report is written.
