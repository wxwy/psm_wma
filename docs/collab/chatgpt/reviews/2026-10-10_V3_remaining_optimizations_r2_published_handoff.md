# V3 remaining optimizations r2 — published code handoff

Date 2026-10-10. **Implementation candidate; not a technical APPROVE or Gate closure.**

## Formal implementation pair
- Root `cf0c92731197bfdd0de073a4c07ca93194f58968` on `wxwy/psm_wma:V3`
- Child/Gitlink `d41be4f5485dcd9321318840c8c278c1f7487924` on `wxwy/cosmos-framework:v3-local-ttt`
- Earlier Root `2d45bcbe075f27b860aaf0749370f01aabaa4c8a`, Child `95c82d12d6780fedf8becda18cbd36d550adaadf`
- Accepted original Formal30k Child `71e03c8501c94a2ad5fed60955af657d3f945b85`
- New Inbox/review bookkeeping commit is a successor and does NOT change this implementation pair.

## Source delivery
13 Child changed files: compact cached uint8 [3,17,H,W] one-byte backing with prior tensor shape semantics, rank-local single-flight cache and async read integration, consumer/task lineage, fast-state and optimizer storage audit, monitor, same-input Local intervention, per-action/per-episode evaluation error and video evidence. Ten Root regular files and Gitlink: evaluation identity/strict task result reuse, partial/full SR distinction, evaluation launchers, legacy LIBERO guards, CPU validation runner/tests and pre-publication candidate docs.

All 50 anchored edits in 12 existing files were matched to the fixed remote base and new paths checked absent before Git object submission. During publication, a missing Trainer observer argument declaration/forwarding was fixed. Child and Root commits and Gitlink were then verified equal. Historical pre-publication drafts containing 'UNPUBLISHED' are earlier snapshots only.

## Evidence boundary
Prior local bundle reported **83 isolated CPU tests** (stubbed source reader, toy generator); it did not import/test the full remote integration or the callback correction. No fresh full-project Ruff, py_compile across all files, LeRobot/Arrow/HF semantic parity, real DCP, distributed GPU, strict same-job Resume, real-policy Local on/off, simulator 48/128 step, or 18-task screen is established. Those gates remain open.

Next: run the exact pair CPU/static Gate read-only on DS_PRO training host; stop on first failure, preserve raw evidence, no DS production edits. Original `formal_verified_index_30k` job remains stopped; last complete checkpoint iteration unknown. Do not fresh-start, resume, or alter DCP. Expected historical config digest `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37` requires real preflight verification. No formal Gate verdict granted here.
