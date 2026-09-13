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

## Remediation review request — v0.8 add-to-owner continuity fail-close

- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`
- Formal root: `145f0d4af0b75165569e7b241841cd078e8359dd`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Scope: only the root v0.8 launcher, its CPU-only temporary native-Git witness, v0.8 annex/request, and task records.  This resolves the prior exact-pair ChatGPT HIGH at payload v0.8:90: native Git returns no created-directory inode, so `add_and_capture()` now fail-closes as `ROLLBACK_INCOMPLETE` before accepting any post-add pathname as owner authority.  The new direct temporary-native-Git witness runs a successful add, renames its CLEAN and installs a Git-valid copied replacement before any owner bind; it proves terminal fail-close and leaves the foreign replacement untouched.  `py_compile`, 12/12 witness PASS, payload bytes/SHA (`13969`, `b7923b212f40bba8580711793a5b9a5ef5ab2c2b1f62b0b44c6d6ee93882d666`), and `git diff --check` PASS.
- Exact review ask: `APPROVE_TO_PREPARE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_EXECUTION_WITNESS_CLOSURE`, or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: all real materialization; source/checkpoint I/O; project worktree/backing/index/candidate/ref/evidence creation; collection/receipt/publication; child/runtime modifications; GPU, training, evaluation, inference and LIBERO4IN1.

## Design review request — causal owner identity execution-capable mechanism

- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-EXECUTION-DESIGN`
- Formal root: `5bf6e3d033d2ad6d9f68483c629f2d852f6a8b9d`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Scope: root docs-only design `PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_owner_identity_execution_design_v0.1.md`.  It replaces post-add pathname ownership inference with executor precreation and retention of an empty CLEAN directory FD, native Git population via an inherited parent-FD `/proc/self/fd/<fd>/CLEAN` target, and mandatory parent-entry/FD revalidation.  A local temporary Git probe verified the current Git accepts a precreated empty directory; future implementation must re-prove this only in fixtures.
- Exact review ask: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_OWNER_IDENTITY_CPU_STATIC`, or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: all real materialization; source/checkpoint I/O; project worktree/backing/index/candidate/ref/evidence creation; collection/receipt/publication; child/runtime modifications; GPU, training, evaluation, inference and LIBERO4IN1.
