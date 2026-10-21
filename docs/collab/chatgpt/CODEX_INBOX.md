# PSM-WMA V3 — Canonical ChatGPT Review Inbox

## 2026-10-21 — Capacity rollover

- This file was rolled over because the prior canonical Inbox exceeded the V3 128 KiB hard cap. **Previous content is preserved byte-for-byte**, not deleted or overwritten without an archive.
- Immediate previous archive: `docs/collab/chatgpt/archive/CODEX_INBOX_20261021_173f3e4.md`.
- Previous canonical Git blob SHA: `97b12cd936cdc560bca1aa9fbbe417d0f302face`; archived content Git blob SHA: `97b12cd936cdc560bca1aa9fbbe417d0f302face` (identical).
- Pre-rollover V3 HEAD (bookkeeping): `173f3e4f09934dab4119578ac64ae9a0b8e02091`.
- Prior history and dispositions remain authoritative in that immutable archive; read targeted entries only when necessary.
- Separate current continuation: `docs/collab/chatgpt/CODEX_INBOX_2026-10-15_CONTINUATION.md`.
- Review/bookkeeping commits do **not** change formal implementation target.

## 2026-10-21 — New V3 iter4000 4-task×5 Queue Gate — GPT `REQUEST_CHANGES`

- **Formal Implementation Root**: `ca936c8eecd593133b1e6c61ba5691331958c592`; **Child/Gitlink**: `2d128ed5a07601cdd424974f99b67832eafeeb41`; queue blob `eec2702d5382358e131928db60ce75c93c0c55d5`.
- **Detailed independent review**: `docs/collab/chatgpt/reviews/2026-10-21_V3_iter4000_HIGH02_ca936c8e_incremental_review.md`.
- Previous HIGH-01 lock deadlock is **RETRACTED/FALSE POSITIVE**, no changes required. HIGH-02 primary port, /info, /proc identity flaws are **CLOSED** at CPU static production semantics, pending actual target-machine preflight.
- **New MEDIUM-05 OPEN** `scripts/eval_robocasa_18task_queue.py:341-375,499-508,518-539`: Worker directory creation and server log opening occur **outside** the Worker `try/except`. A failed worker can exit without `worker_errors`, and another worker can complete all 20 synthetic episodes such that final `COMPLETE`, SR and RC0 are wrongly reported. This violates fail-closed worker-error preservation.
- **Codex remediation scope**: only root queue Worker pre-start error capture/propagation and focused CPU integration negative test injecting `mkdir` or log-open failure in one worker while another completes all four tasks. Require summary `status=INCOMPLETE`, `sr=None`, `worker_errors` nonempty and RC!=0, no surviving owned processes/threads. Keep existing HIGH-02 identity logic and HIGH-01 Lock unchanged; do not touch Child, trainer, DCP, Local-TTT, ABI or run GPU/simulator.
- **Author evidence checked**: 28 pytest testcases +41 subtests passed in submitted artifact; this does not cover the new pre-`try` path and does not prove real GPU or RoboCasa. Bring fresh exact implementation SHA, original Child Gitlink, scope diff, direct CPU Evidence for incremental review.
- DS_PRO: continue **read-only / synthetic CPU** preparation at exact new pair, verify real iter4000 metadata, four task env_name set, `/proc` access and runtime prerequisites. No real Action Server, simulator, GPU or training launch until later explicit authorization. 1/2/4 GPUs correspond to 1/2/4 Worker/Server/serial simulation slots in the current queue.

Current verdict is **`REQUEST_CHANGES`**, not a GPU execution release.

## 2026-10-21 — Codex MEDIUM-05 minimal fix / new-Pair incremental review request

- **Implementation Root `6405c9dae02e81be5f267e79e27995c3df7fb988`; unchanged Child/Gitlink `2d128ed5a07601cdd424974f99b67832eafeeb41`**. Queue Blob `e56eaafe8276aa40cb9e2fbc1110515e8fa19c25`; parent a5d743d1c2221dd4db21dfa61db814da51b286ed preserves review/Inbox rollover. Non-force V3 publication and source branch v3-iter4000-worker-init-20261021; later docs HEAD is bookkeeping only.
- MEDIUM-05 only: original worker renamed run_worker without body AST changes; new thread-entry worker catches directory/log initialization/resource-context errors and records stop/worker_errors/publish through existing summary. HIGH-02 helpers, original main after removing only the new entry, commands, identity module and Child unchanged; HIGH-01 locks/publish scopes untouched. No new orchestration script.
- Red/green CPU: original eec2702d queue reproduced both new mkdir and log-open failures (two expected failed assertions;20 trials yet COMPLETE/RC0, uncaught thread errors). New Pair correctly retains20 trials but worker_errors nonempty, INCOMPLETE/sr=None/RC1, no unhandled thread errors/remaining owned process or worker. Final30 passed (15 targeted+15 existing cases),41subtests,55 unrelated deselected,0fail/error/skip,30.775s; Ruff0.12.7 check/format,syntax,diff PASS. Stdlib HTTP/Git/temp metadata and synthetic rows/video only; no actual model/DCP/GPU/Simulator.
- Author report + DS minimal CPU delta commands: docs/collab/codex/reviews/2026-10-21_V3_iter4000_MEDIUM05_worker_initialization_author_handoff.md. Exact command/env/RC/log/XML, red/green witnesses, scope proof and diff: docs/collab/codex/evidence/2026-10-21_V3_iter4000_MEDIUM05_author_cpu/.
- **Request new-Pair fresh incremental review limited to MEDIUM-05**, reuse unchanged already-closed HIGH-02 behavior by scope; no new verdict self-assigned. Earlier ca936c8e remains REQUEST_CHANGES; this is a distinct Pair. DS may verify two new CPU negatives and normal worker completion; use new Root for all version assertions instead of historical ca936c8e in old runbook.
- STOP after handoff: GPU/real Server/Simulator/20-rollout release still requires later Owner authorization and target readiness. Original M03/M04/proc/H16 constraints stay; no Child/Trainer/DCP/Local/ABI changes, no historic Evidence deletion, no claim of full E1 deadline implementation or direct external delivery.
