# Issue63 narrow local peer closure

Verdict: **LOCAL_CODE_REVIEW_PASS**. Finding **P2-63-PEER-1 is CLOSED** on the exact corrected pair below. No additional P1/P2 was confirmed within this narrow increment.

- Root: `a169fea07016b80b3639646cc9925ac70b6525a8`
- Unchanged Child/Gitlink: `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`
- Unchanged nav reference: `70eb7b447e65d793b0ebe18b258291ce46f057c1`
- Previously rejected Root: `98172110677b7631f5b7974003ffae664bdd0b85`
- Reviewer: local independent Agent `/root/issue63_peer_review`.

This closes the concrete code finding from `peer/REPORT.md`; it is not GPT independent/server approval or authorization for real production, capacity acceptance or merge.

## Correction and independent closure

Tree comparison confirms the only changed product file since the rejected Root is `g2/latent_cache/final_source.py`; the only changed project test file is `g2/tests/test_source_retirement_faults.py`. Other changes are documentation/evidence. The correction adds shared receipt checks at `final_source.py:151`–180:

- exact retirement-receipt top-level fields;
- working-proof and cleanup fingerprints equal the capsule attestation;
- both original source and original READY hashes equal the capsule working-source binding, with an exact retired-file map;
- archive reference equals the capsule reference and disposition equals the defined retirement value.

Existing schema/source/episode/recipe/capsule/attestation checks and actual final-file hash checks remain in the same function. `open_episode_index`, full profile verification and the collector all reach this shared verifier. A receipt+COMPLETE rewrite can no longer detach those historical claims from the original SQL-bound capsule. The correction introduces no PT, product, recipe, capsule schema, encoding, queue, lease or retirement transaction change.

The **original unchanged five-case independent probe passed:5 PASS,0 failures/errors/skips,13.93s**, exit0. Probe SHA256 remains `cbc86a7b29e529fd5ace678fe5a10a78303aaefe25d71e470c23df2959883a1f`.

All three formerly RED coordinated mutations are now rejected by the actual collector. A separate standard-library read of their SQLite files confirms **one active job and zero completed jobs in each case**, while the original SQL capsule binding is preserved. The two positive cases still verify no write-mode open/new lock for a legacy reader and no encoding/file rewrite on retired-v2 post-hoc resume. Static review also confirms equivalent enforcement of the second retired hash, archive and disposition fields.

`receipt.json`/`receipt.log` verify all235 current source hashes against the corrected formal Git blobs and author revision2 before/after snapshots. The fixed-source binding file also matches the corrected Root and all235 source identities. The previous report, original probe, RED logs/JUnit and original receipt were hash-checked and remain unchanged. No broad test collection was rerun; author542PASS/13 inherited skips is author evidence and is not an independent closure count.

## Actual execution and artifacts

Cwd: `/workspace/psm_wma_issue52`. Both commands were announced before execution. Existing interpreter only; synthetic CPU data in a fresh `/tmp` namespace; no GPU, network, server/private assets or dependency installation.

```bash
mkdir docs/collab/codex/evidence/2026-11-17_issue63/peer_closure
env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 COSMOS_DEVICE=cpu COSMOS_TRAINING=0 COSMOS_INTERNAL=0 PYTHONPATH=/workspace/psm_wma_issue52:/workspace/psm_wma_issue52/cosmos-framework /workspace/.venvs/g2-view-vae-52/bin/python -m pytest -q -p no:cacheprovider --tb=short -rs docs/collab/codex/evidence/2026-11-17_issue63/peer/test_independent_protocol.py --basetemp=/tmp/g2_issue63_peer_closure_a169fea0 --junitxml=docs/collab/codex/evidence/2026-11-17_issue63/peer_closure/probe.xml > docs/collab/codex/evidence/2026-11-17_issue63/peer_closure/probe.log 2>&1
env PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 CUDA_VISIBLE_DEVICES='' /workspace/.venvs/g2-view-vae-52/bin/python docs/collab/codex/evidence/2026-11-17_issue63/peer_closure/collect_closure_receipt.py > docs/collab/codex/evidence/2026-11-17_issue63/peer_closure/receipt.log 2>&1
```

The probe and source/observation audit each exited0. `probe.log/xml` contain raw GREEN results; `collect_closure_receipt.py` is a read-only standard-library evidence collector; `receipt.json/log` contain pair/source/evidence hashes and actual preserved-ledger observations. Permanent closure files are confined to this new `peer_closure/` directory. Production, formal tests, original peer artifacts and old evidence were not edited by the reviewer. Closure artifacts are uncommitted when written.

Real169 Wan reencode,419 pixel comparisons, representative file-size/read-latency measurement,18-task capacity,32-worker resources and full9126 remain NOT_RUN by this reviewer and require the separate GPT/Owner gates. The positive external archive test was not rerun in this narrow closure. No server access, private transfer, native/GPU/Wan/weights execution, install, original-data deletion, training, publication or merge was performed.
