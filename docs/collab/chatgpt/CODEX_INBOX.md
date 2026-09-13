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

## Remediation review request — causal owner identity v0.1

- Formal root: `64b706b7d8dc3fd470a27c5ea093426c84f2df15`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Resolves prior HIGHs by preserving frozen ROOT/CLEAN/argv paths, rooting identity in ROOT FD, freezing FD6 vs `{3,4,5}`, requiring clean-FD-relative handoff and final absolute-path identity revalidation.
- Requested verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_OWNER_IDENTITY_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- No real materialization/source I-O/child/GPU/training.

## Replacement review request — causal owner identity v0.1 (correct formal SHA)

- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-EXECUTION-DESIGN`
- Supersedes only the malformed full root in the immediately preceding request (`64b706b7d8dc3fd470a27c5ea093426c84f2df15` does not resolve). The formal root is exactly `64b706b7b97451fd90cb6e9292100e512952f28a`; child/Gitlink is exactly `93a89ba61306d840a008813f62f26a34d54850f4`.
- Formal scope: this root changes only `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_owner_identity_execution_design_v0.1.md`. It resolves the prior ChatGPT HIGHs by retaining the frozen `ROOT`/`CLEAN` absolute-path and argv contract; using inherited `root_fd=6` only for native Git while reserving `{3,4,5}` for the frozen backing ABI; requiring every backing operation relative to non-inherited `clean_fd`; and revalidating the root-FD absolute CLEAN entry against `clean_fd` before handoff and exec. It additionally requires a fixture proof for the post-validation-before-handoff replacement.
- Evidence/requested scope: docs-only remediation review. On unanimous approval, the next action is limited to root-only stdlib temporary-fixture CPU/static implementation and tests. No actual materialization/source or checkpoint I/O/project authority artifacts/child changes/GPU/training/evaluation/inference/LIBERO4IN1.
- Exact verdict requested: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_OWNER_IDENTITY_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## Replacement review request — causal owner identity v0.2 exec-continuity refreeze

- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-EXECUTION-DESIGN`
- Formal root: `de1d12f194030067a4afa656379378713b151734`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Formal scope: new docs-only v0.2 design plus task records. It closes the three final reviews for `64b706b...`: distinct long-lived executor `root_authority_fd=7`, Git-only `git_root_fd=6` duplicate and explicit fstat/CLOEXEC/pass_fds lifetime; no `parent_fd`; CLEAN-only rather than ROOT cleanup; and final bootstrap owner root as inherited `bootstrap_clean_fd=8`, refreezing child ABI from `{3,4,5}` to exact `{3,4,5,8}`. Bootstrap must resolve root/module files exclusively through `/proc/self/fd/8`; no global absolute CLEAN fallback. A temporary-fixture actual exec/bootstrap seam replacement witness is mandatory.
- Evidence/limits: formal tree changes only `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_owner_identity_execution_design_v0.2.md`, `SESSION.md`, and `TODO.md`; `git diff --cached --check` passed before commit. Requested authorization, if unanimous, remains only root-only stdlib temporary-fixture CPU/static implementation/tests.
- Explicitly prohibited: production/main execution; real materialization; project worktree/backing/index/candidate/ref/evidence creation; source/checkpoint I/O; collection/receipt/publication; child/runtime; GPU, training, evaluation, inference, LIBERO4IN1.
- Exact verdict requested: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_OWNER_IDENTITY_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## Remediation review request — causal owner identity v0.3 collision-free adapter argv

- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-EXECUTION-DESIGN`
- Formal root: `781824f4ed2682b1347126a58f645ef0702117bd`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Formal scope: this docs-only remediation changes only `PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_owner_identity_execution_design_v0.3.md`, `SESSION.md`, and `TODO.md`. It closes the v0.2 ChatGPT HIGHs by reserving FDs 3--9 before mutation; keeping root/Git/clean-owner/bootstrap capabilities collision-free at 7/6/9/8; binding every capability by temporary-open → dup/rebind → fstat identity proof → source close; and freezing final child inheritance to exactly `{3,4,5,8}`. It additionally freezes the actual adapter boundary: all post-exec `--cwd`, `--index`, and `--bootstrap-project-root` bytes must derive from `/proc/self/fd/8`, with mandatory `--bootstrap-owner-root-fd 8`, parser/raw-argv verification, no `Path.resolve()` global reintroduction, and a real isolated bootstrap→adapter replacement seam witness.
- Evidence: formal-tree scope was verified with `git diff-tree`; Gitlink was verified with `git ls-tree`; design blob SHA-256 is `7fc23178e07f060dc2cfb882bfbecfb52073d5ba13982cf81ee1e42d111760d6`; `git diff --check` passed before the formal commit.
- Requested authorization, only if unanimous: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_OWNER_IDENTITY_CPU_STATIC`, limited to root-only stdlib temporary-fixture launcher/adapter tests and implementation. Or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: production/main execution; all real materialization; source/checkpoint I/O; project worktree/backing/index/candidate/ref/evidence creation; collection/receipt/publication; child/runtime changes; GPU, training, evaluation, inference, and LIBERO4IN1.

## Repair delivery request — execution-authority CPU/static remediation closure

- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`
- Formal root: `cc36db3a6b863d86d57f5eb0e3fcefb5aef3376d`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: incremental root-only remediation limited to `tools/psm_wma/materialize_immutable_source_authority_root.py`, its direct stdlib temporary-fixture CPU tests, and task records. It moves the four-project-module formal-tree/raw identity closure ahead of `sys.path.insert()` and `runpy`, and adds isolated-interpreter import-side-effect, endpoint, replace-ref, ambient-config, and Evidence remote-identity witnesses. Formal verification reported 92/92 CPU tests, `py_compile`, Ruff, and `git diff --check` PASS.
- Exact final verdict requested: `APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_EXECUTION_AUTHORITY_CPU_STATIC_IMPLEMENTATION`, or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: all real materialization; source/checkpoint I/O; project worktree/backing/index/candidate/ref/evidence creation; collection/receipt/publication; child/runtime changes; GPU, training, evaluation, inference, and LIBERO4IN1.

## Remediation review request — causal owner identity v0.4 consumer authority

- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-EXECUTION-DESIGN`
- Formal root: `76210e7bcbdc606e39775e2dae258542cf3c0d38`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: docs-only v0.4 replacement for v0.3. It closes ChatGPT's two HIGH requirements by freezing every post-exec FD8 consumer (bootstrap Git probes plus each `NativeAuthorityGit` Git subprocess) to `close_fds=True, pass_fds=(8,)`, with pre/post FD8 identity barriers and an actual temporary-Git FD8-index replacement seam. It also freezes no-follow, dirfd-anchored replacement semantics for every procfd-affected bootstrap/module/loaded-module/repository/config check, preserving raw/blob, anti-symlink, route and common-config authority without canonicalizing back to global CLEAN pathnames.
- Evidence: exact formal diff only changes v0.4 design, `SESSION.md`, and `TODO.md`; exact Gitlink remains `93a89ba...`; `git diff --cached --check` passed before formal commit.
- Exact verdict requested: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_OWNER_IDENTITY_CPU_STATIC`, or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: production/main execution; all real materialization; source/checkpoint I/O; project worktree/backing/index/candidate/ref/evidence creation; collection/receipt/publication; child/runtime changes; GPU, training, evaluation, inference, and LIBERO4IN1.

## Implementation review request — causal owner FD8 bootstrap and no-follow traversal

- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-CPU-STATIC-IMPLEMENTATION`
- Formal root: `5a2a3207853cdbbe4dc8135080cd5fe5050b7787`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Scope: only `tools/psm_wma/materialize_immutable_source_authority_root.py`, its direct stdlib temporary-fixture CPU test, and task records. The adapter now binds final bootstrap argv to FD8 (`cwd/index/project-root` procfd ABI plus `--bootstrap-owner-root-fd=8`), passes the retained owner capability to every Git consumer, begins module/loaded-module reads directly from the owner `dir_fd`, and prevents the owner branch from resolving procfd paths back to global CLEAN. Configuration authority retains the FD owner boundary without `cwd.resolve()`.
- Evidence: root formal tree is exactly the four files above; Gitlink is unchanged. Temporary-only witnesses cover FD8 bootstrap with local/bare Git preflight, global root replacement while reading through held FD, actual Git pre-consumer index replacement rejection, and owner configuration. `python3 -m unittest tools.psm_wma.test_materialize_immutable_source_authority_root` = 62/62 PASS; `py_compile` and `git diff --check` PASS.
- Exact verdict requested: `APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_OWNER_IDENTITY_CPU_STATIC_IMPLEMENTATION`, or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: production/main execution; all real materialization; source/checkpoint I/O; project worktree/backing/index/candidate/ref/evidence creation; collection/receipt/publication; child/runtime changes; GPU, training, evaluation, inference, and LIBERO4IN1.
