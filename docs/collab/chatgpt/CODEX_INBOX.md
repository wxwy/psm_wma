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
