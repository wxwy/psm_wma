# CODEX_INBOX — live review ledger

## Rollover continuity

- Immediate immutable archive: `docs/collab/chatgpt/archive/CODEX_INBOX_2026-09-13_5ff4df5.md`
- Archive blob SHA: `91a5e1e3cbe5d8a94ccddc6bd672ae2027535911` (byte-for-byte preserved)
- Pre-rollover HEAD: `5ff4df58cc8e17644aab945de3de6d74b8b2967c`
- Current unresolved Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`
- Latest resolved formal pair: `bf852c233b2c2e31eb33dc859188a9a4b41c50df` / `93a89ba61306d840a008813f62f26a34d54850f4`; effective verdicts: ChatGPT/Kimi `REQUEST_CHANGES`, MM `APPROVE_TO_MATERIALIZE`.
- Latest formal review: `docs/collab/chatgpt/reviews/2026-09-13_R09_B_TTT_v035_authority_root_materialization_execution_request_launcher_v07_bf852c2_93a89ba.md`.

## New review request — v0.8 static-witness closure

- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`
- Formal root: `5ff4df58cc8e17644aab945de3de6d74b8b2967c`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Scope: only v0.8 immutable launcher, annex/request, and CPU-only temporary Git/FD witnesses. Evidence: payload and `...v0.8_witness_test.py`; `py_compile`, 11/11 witness PASS, `git diff --check` PASS.
- Exact review ask: `APPROVE_TO_PREPARE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_EXECUTION_WITNESS_CLOSURE`, or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: all real materialization; source/checkpoint I/O; project worktree/backing/index/candidate/ref/evidence creation; collection/receipt/publication; child/runtime modifications; GPU, training, evaluation, inference and LIBERO4IN1.
