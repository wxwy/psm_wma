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

## Remediation review request — mandatory FD8 admission and bootstrap closure

- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-CPU-STATIC-IMPLEMENTATION`
- Formal root: `c8aafca005ff061788114281e47fd1a4e2b6a843`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only remediation of the same adapter and direct stdlib temporary-fixture CPU tests, plus task records. It makes the owner argument mandatory; production admission accepts only FD8 and exact `/proc/self/fd/8` cwd/index/bootstrap-root fields; bootstrap verifies all formal project modules by FD8-started component-by-component no-follow traversal before `sys.path`/`runpy`; and loaded adapter/authority module identities are checked against FD8-relative object identities rather than SHA alone. A real bootstrap witness replaces an intermediate project-module directory with an external symlink and must fail before import.
- Evidence: `python3 -m unittest tools.psm_wma.test_materialize_immutable_source_authority_root` = 63/63 PASS; `py_compile` and `git diff --check` PASS. Formal Gitlink remains exact child above. Scope excludes all real materialization/source-checkpoint I/O, project artifacts, collection/receipt/publication, child/runtime changes, GPU, training, evaluation, inference and LIBERO4IN1.
- Exact final verdict requested: `APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_OWNER_IDENTITY_CPU_STATIC_IMPLEMENTATION`, or `REQUEST_CHANGES(file:line)`.

## Remediation review request — FD8 consumer barriers and direct witnesses

- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-CPU-STATIC-IMPLEMENTATION`
- Formal root: `e88a9a9dd989e6a00e74d51ee9848b8ad241caa1`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only minimal remediation of `tools/psm_wma/materialize_immutable_source_authority_root.py`, its direct stdlib temporary-fixture CPU test, and task records. It rejects every production construction where `owner_fd != 8` before accepting pathname authority; bootstrap captures FD8 owner/index identities and revalidates both before and after every `grun()` Git consumer.
- Evidence: direct CPU witnesses reject production `owner_fd=None`, non-8, and mismatched cwd/index; reject bootstrap non-8/cwd/index/project-root ABI fields; inject an index replacement immediately after the first bootstrap Git probe to prove the post-consumer barrier fails closed; reject a same-bytes foreign loaded adapter by owner-object identity; and rename the former missing-owner-flag test to its actual seam. `py_compile`, 67/67 direct stdlib CPU tests, and `git diff --check` PASS. Fixtures use only TemporaryDirectory and local/bare Git; no external network or real materialization/source-checkpoint I/O.
- Exact final verdict requested: `APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_OWNER_IDENTITY_CPU_STATIC_IMPLEMENTATION`, or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: production/main execution; real materialization; source/checkpoint I/O; project worktree/backing/index/candidate/ref/evidence creation; collection/receipt/publication; child/runtime changes; GPU, training, evaluation, inference, and LIBERO4IN1.

## Remediation review request — bootstrap index regular-file admission

- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-CPU-STATIC-IMPLEMENTATION`
- Formal root: `aba42f3c077629074f3f8c03420bc8a01bc1ebd7`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: minimal root-only remediation of `tools/psm_wma/materialize_immutable_source_authority_root.py`, its direct stdlib temporary-fixture CPU test, and task records. It addresses the exact ChatGPT HIGH in review `2026-09-13_R09_B_TTT_v035_authority_root_causal_owner_identity_cpu_static_remediation_e88a9a9_93a89ba.md`: initial FD8-relative `.authority-root.index` capture and every subsequent `ownerbarrier()` now require `stat.S_ISREG` before accepting identity. The new direct temporary fixture replaces the index with a directory, injects a marker immediately before the first possible Git `subprocess.run`, and proves bootstrap rejects without launching any `grun()` consumer or creating evidence.
- Formal-tree scope: exactly `SESSION.md`, `TODO.md`, the adapter, and its direct test; `cosmos-framework` remains mode `160000` at the exact child above. Evidence: `py_compile`, `python3 -m unittest tools.psm_wma.test_materialize_immutable_source_authority_root` = `68/68 PASS`, and `git diff --check` PASS. Fixtures use only `TemporaryDirectory` and local/bare Git; no external network.
- Exact final verdict requested: `APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_OWNER_IDENTITY_CPU_STATIC_IMPLEMENTATION`, or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: production/main execution; real materialization; source/checkpoint I/O; project worktree/backing/index/candidate/ref/evidence creation; collection/receipt/publication; child/runtime changes; GPU, training, evaluation, inference, and LIBERO4IN1.

## Design review request — v0.3.5 single-GPU smoke execution path

- Gate: `G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-DESIGN`
- Formal root: `ee5d895043222763849ab60aa17d782f3c1596fd`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Formal scope: exactly the new root docs-only design `docs/build/PSM-WMA_Local_Memory_v0.3.5_single_gpu_smoke_design_v0.1.md` plus `SESSION.md` and `TODO.md`; formal Gitlink is unchanged. Design SHA-256: `40b50a1f9384b78115167cd8bc3702166098ba3d3d3dc6c41099c5cfa30adc19`.
- Review focus: verify that source-evidence post-commit receipt is the sole real-input prerequisite (with no new horizontal provenance Gate), that the canonical chronology/GA-window transaction is unambiguous, and that world-size-1/no-torchrun/no-resume/num_workers=0 admission, bounded ≤100-step scope, artifacts, PASS and stop conditions are sufficient before a later execution-runbook Gate.
- Exact verdict requested: `APPROVE_TO_DESIGN_R09_B_TTT_V035_SINGLE_GPU_SMOKE_EXECUTION`, or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: writing/reading real source, checkpoint, manifest, data or cache; source-evidence record/receipt/publication; child/runtime/config changes; GPU/CUDA/torchrun; training, evaluation, inference or LIBERO4IN1. An approval authorizes only the next docs-only single-GPU smoke execution runbook/command design.

## Remediation review request — v0.3.5 single-GPU smoke world-size predicate

- Gate: `G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-DESIGN`
- Formal root: `e75c8c12c8573d445e91f2b9c9b4d95d98b1d5f8`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Formal scope: exactly one root docs-only line in `docs/build/PSM-WMA_Local_Memory_v0.3.5_single_gpu_smoke_design_v0.1.md`; its SHA-256 is `de480cdf3f9b742a0b69cbe4d3d3a0c00d6fdf68858ac60ce9b2698153e76d1e`. The Gitlink is unchanged.
- Remediation: ChatGPT's original exact-pair review identified the contradictory STOP wording “非零 world size” while §§3--4 require `world_size=1`. §5 now says precisely ``world_size != 1``; thus the only permitted single-GPU value passes admission and every other value fails. No other design semantics changed.
- Review focus: verify this correction completely resolves that HIGH and does not weaken the no-torchrun/no-resume/`num_workers=0`, bounded ≤100-step, source-evidence prerequisite, chronology, artifact, PASS, or stop-condition boundaries.
- Exact verdict requested: `APPROVE_TO_DESIGN_R09_B_TTT_V035_SINGLE_GPU_SMOKE_EXECUTION`, or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: writing/reading real source, checkpoint, manifest, data or cache; source-evidence record/receipt/publication; child/runtime/config changes; GPU/CUDA/torchrun; training, evaluation, inference or LIBERO4IN1. Approval authorizes only the next docs-only single-GPU smoke execution runbook/command design.

## Design review request — v0.3.5 single-GPU smoke execution runbook

- Gate: `G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-EXECUTION-RUNBOOK-DESIGN`
- Formal root: `5912e7d06c53e8a0cf650d4b2886f10cd72e3311`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Formal scope: root-only docs design `docs/build/PSM-WMA_Local_Memory_v0.3.5_single_gpu_smoke_execution_runbook_design_v0.1.md` plus task records; Gitlink unchanged. Design SHA-256: `94db5f6a2572b994f70b2c09ab8da2ed76e6a64240c2504bc87f6f3d8774a024`.
- Review focus: verify receipt-derived authority tuple, non-overridable request schema, no-shell command grammar, exactly-one-GPU/no-torchrun admission, v0.3.5 chronology/GA failure transaction, bounded 1..100 steps, write allowlist, PASS/FAIL/MANUAL_STOP, and that no real I/O or execution is authorized by this design.
- Exact verdict requested: `APPROVE_TO_DESIGN_R09_B_TTT_V035_SINGLE_GPU_SMOKE_EXECUTION_REQUEST`, or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: creation or execution of an execution request; real source/checkpoint/manifest/data/cache I/O; collection/receipt/source-evidence/publication; child/runtime/config changes; GPU/CUDA/torchrun; training, evaluation, inference, LIBERO4IN1, matched smoke, sidecar, checkpoint write, or formal training. Approval authorizes only a later receipt-bound execution-request design/review.

## Remediation review request — smoke runbook terminal-status ABI

- Gate: `G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-EXECUTION-RUNBOOK-DESIGN`
- Formal root: `5053ed40065bfa0b8e1d755756b0565bd2d5ef31`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Formal scope: root-only docs remediation of the runbook and session record; Gitlink unchanged. Runbook SHA-256: `b348d43053903697d62d81ecb979d7c5604ea0b2f9acc821baa0aebed156c4a1`.
- Remediation: resolves ChatGPT HIGH at prior runbook line 127 by freezing terminal statuses `PASS|FAIL|BLOCKED|MANUAL_STOP`, defining `MANUAL_STOP` as a distinct non-PASS terminal, requiring `failure.json` for `FAIL|BLOCKED|MANUAL_STOP`, freezing its exact key set and summary-status equality, and requiring the final committed transaction identity for manual stop.
- Exact verdict requested: `APPROVE_TO_DESIGN_R09_B_TTT_V035_SINGLE_GPU_SMOKE_EXECUTION_REQUEST`, or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: creation or execution of an execution request; real source/checkpoint/manifest/data/cache I/O; collection/receipt/source-evidence/publication; child/runtime/config changes; GPU/CUDA/torchrun; training, evaluation, inference, LIBERO4IN1, matched smoke, sidecar, checkpoint write, or formal training.

## Design review request — receipt-bound smoke execution request instance

- Gate: `G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-EXECUTION-REQUEST-DESIGN`
- Formal root: `86c3276f5fd08c9a028e549c27ce7fe2989d0f4d`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Scope: root-only docs design `PSM-WMA_Local_Memory_v0.3.5_single_gpu_smoke_execution_request_design_v0.1.md` and session record; Gitlink unchanged. SHA-256: `a288956c535c145b30c830efc1640fd4edcc60281adde1d72a8e6992791d6806`.
- Review focus: receipt-only authority derivation, exact canonical request schema and self-hash, non-shell argv, bind-before-read ordering, fixed single-GPU runtime, terminal ABI inheritance, and the explicit prohibition on creating/using a request instance at this Gate.
- Verdict: `APPROVE_TO_DESIGN_R09_B_TTT_V035_SINGLE_GPU_SMOKE_EXECUTION_REQUEST_INSTANCE`, or `REQUEST_CHANGES(file:line)`.
- Prohibited: request creation/execution, real I/O, child/runtime/config changes, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1, sidecar, checkpoint write, or formal training.

## Correction — exact formal root for receipt-bound smoke execution request instance

- Gate: `G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-EXECUTION-REQUEST-DESIGN`.
- The immediately preceding request contains a root-SHA transcription error and is superseded for review routing only: `86c3276f5fd08c9a028e549c27ce7fe2989d0f4d` is not a Git object. The sole correct formal root is `86c3276f1f8a6071659316e8c190f97fd622c0a7` (`docs: design smoke execution request instance`); child/Gitlink remains `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope and evidence are unchanged: root-only docs design `docs/build/PSM-WMA_Local_Memory_v0.3.5_single_gpu_smoke_execution_request_design_v0.1.md`, its task record, unchanged Gitlink, and design SHA-256 `a288956c535c145b30c830efc1640fd4edcc60281adde1d72a8e6992791d6806`.
- Request an exact-pair formal final verdict: `APPROVE_TO_DESIGN_R09_B_TTT_V035_SINGLE_GPU_SMOKE_EXECUTION_REQUEST_INSTANCE`, or `REQUEST_CHANGES(file:line)`.
- Prohibited: request creation/execution, real source/checkpoint/manifest/data/cache I/O, child/runtime/config changes, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1, sidecar, checkpoint write, and formal training. This correction does not authorize any execution.

## Remediation review request — v2 unique smoke request ABI

- Gate: `G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-EXECUTION-REQUEST-DESIGN`.
- Formal root: `0874bb153ba81ee29eee84f0bde311bbf2d1ebe0`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only docs remediation `docs/build/PSM-WMA_Local_Memory_v0.3.5_single_gpu_smoke_execution_request_design_v0.2.md` plus task records; unchanged child. It resolves the exact ChatGPT/Kimi v0.1 findings by explicitly superseding only approved runbook §3 with a versioned v2 ABI, freezing all top-level and relevant nested contract fields, and defining this Gate as design-only while allowing exactly one receipt-closed instance only in a later independently reviewed construction Gate.
- Evidence: no real I/O/child/GPU execution; `git diff --check` and new-file no-index diff-check PASS; design SHA-256 `bead03f9e5959674393b21b9d77fb359bd46b40e4e0d9a0dd7a00748f9f9c8e6`.
- Exact final verdict requested: `APPROVE_TO_DESIGN_R09_B_TTT_V035_SINGLE_GPU_SMOKE_EXECUTION_REQUEST_INSTANCE`, or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: instance creation/execution; real source/checkpoint/manifest/data/cache I/O; child/runtime/config changes; GPU/CUDA/torchrun; training/evaluation/inference/LIBERO4IN1; sidecar; checkpoint write; formal training.

## Remediation review request — v0.3 acyclic request approval

- Gate: `G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-EXECUTION-REQUEST-DESIGN`; formal root: `aad59ce762c694d77aab646ae72cfa8c6ef27cdd`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only docs v0.3. It moves exact-instance reviews outside hashed request bytes, and authorizes only receipt-blob/root-tree/Gitlink read-only lookup for later construction. No execution or payload I/O.
- Request final verdict: `APPROVE_TO_DESIGN_R09_B_TTT_V035_SINGLE_GPU_SMOKE_EXECUTION_REQUEST_INSTANCE` or `REQUEST_CHANGES(file:line)`.

## Design review request — consolidated source-evidence closure execution request

- Gate: `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-DESIGN`.
- Formal root: `88d11170db2cd058567af175c69152231917360a`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only docs design `docs/build/PSM-WMA_Local_Memory_v0.3.5_source_evidence_closure_execution_request_design_v0.1.md`, plus task/session records; Gitlink unchanged. It consolidates the already-approved authority materializer, collection/receipt, source-evidence producer/record/receipt, publication verifier and root-audit sequence into one future controlled request, without opening another provenance branch.
- Review focus: no-worktree-discovery input binding; one activation's ordered materialize→collection/receipt→source-evidence/publication→root-audit transaction; pre-bind/post-commit checks; rollback fail-stop; release of only the receipt triple; and the boundary that this Gate designs, but does not create or execute, the request.
- Evidence: staged root-only diff-check PASS; no project code, real source/checkpoint/manifest/data/cache I/O, child change, GPU or training was run.
- Exact final verdict requested: `APPROVE_TO_DESIGN_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_EXECUTION_REQUEST`, or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: construction/execution of the request; real source/checkpoint/manifest/data/cache I/O; authority/collection/receipt/record/package/publication mutation; child/runtime/config changes; GPU/CUDA/torchrun; training, evaluation, inference, LIBERO4IN1, sidecar and checkpoint write.

## Remediation review request — preserve independent receipt-root authority

- Gate: `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-DESIGN`.
- Formal root: `9a8ef4195ebf3e6a0bf5f1a76f6a8f819e5db546`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only docs remediation `docs/build/PSM-WMA_Local_Memory_v0.3.5_source_evidence_closure_execution_request_design_v0.2.md` plus task/session records; unchanged child. It resolves ChatGPT v0.1 HIGH by requiring activation to stop after machine-verifying the next independent receipt root; exact receipt-root review must bind parent source-evidence root and receipt path/blob before receipt triple may enter smoke-instance construction.
- Evidence: `git diff --check` PASS; no project code, real I/O, child, GPU, or training executed.
- Exact final verdict requested: `APPROVE_TO_DESIGN_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_EXECUTION_REQUEST`, or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: construction/execution of the request; real source/checkpoint/manifest/data/cache I/O; authority/collection/receipt/record/package/publication mutation; child/runtime/config changes; GPU/CUDA/torchrun; training, evaluation, inference, LIBERO4IN1, sidecar and checkpoint write.

## Design review request — immutable-source collection real adapter

- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-IMPLEMENTATION-DESIGN`.
- Formal root: `782ad2a14dd67d40c84dcd8e4adf4e887ce081f0`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only docs design `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_real_adapter_implementation_design_v0.1.md` plus task/session records; formal tree leaves the child unchanged. The design SHA-256 is `b954c60850e4302cffe094f29976a40fe14f966b61b43454d2403d14622726c9`.
- Rationale: read-only instance-preflight confirmed the existing `immutable_source_collection.py` exposes only injected `collect_synthetic` and has no production CLI, native Git transaction, FD-root opener or controlled evidence sink. This design supplies the minimal real-adapter CPU/static implementation route for that already-frozen seam; it does not add a provenance branch.
- Review focus: confirm the two-file adapter/test allowlist, reuse-not-duplicate algorithm boundary, FD/no-follow and same-FD failure closure, native Git/evidence transaction restrictions, import-free argv categories, rollback semantics, and that the subsequent request instance remains non-executing.
- Exact final verdict requested: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_REAL_ADAPTER_CPU_STATIC`, or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: real source/checkpoint/manifest/data/cache I/O; authority/collection/receipt/record/package/publication mutation; child/runtime/config changes; GPU/CUDA/torchrun; training, evaluation, inference, LIBERO4IN1, sidecar and checkpoint write. Approval only permits the listed root CPU/static adapter implementation and its temporary fixtures.

## Remediation review request — preserve unique collection executor identity

- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-IMPLEMENTATION-DESIGN`; formal root: `6ec9d2db564102c7546ceb1c44bc06ccb3c8de31`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only v0.2 docs remediation. It resolves ChatGPT HIGH by retaining `tools/psm_wma/immutable_source_collection.py` as the sole production executor and limiting future CPU/static changes to it and its direct test; no new entrypoint is allowed.
- Request final verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_REAL_ADAPTER_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Prohibited: implementation/execution, real I/O, authority/collection/receipt/publication mutation, child/GPU/training.

## Remediation implementation review request — collection adapter CPU/static

- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-CPU-STATIC`.
- Formal root: `24253e0c3789d46c0807944ec75d6dff108824f3`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Remediation scope: only existing `tools/psm_wma/immutable_source_collection.py` and its direct stdlib test. It closes ChatGPT findings on isolated preflight index, descriptor-safe intermediate no-follow traversal, exact `target_snapshot_v1` tracked/mode/porcelain/type semantics, and no-replace evidence publication.
- Evidence: `python3 -m unittest tools.psm_wma.test_immutable_source_collection`=`44/44 PASS`; `python3 -m py_compile tools/psm_wma/immutable_source_collection.py tools/psm_wma/test_immutable_source_collection.py`; `git diff --check` PASS.
- Request exact final verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_REAL_ADAPTER_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: real source/checkpoint/manifest/data/cache I/O; collection/receipt/publication mutation; request execution; child/runtime/config changes; GPU/CUDA/torchrun; training, evaluation, inference and LIBERO4IN1.

## Remediation implementation review request — fail-closed authority races

- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-CPU-STATIC`.
- Formal root: `a0e9d294320ad37cb127d45118b3f67107bfef7f`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: only `tools/psm_wma/immutable_source_collection.py` and its direct stdlib test; Gitlink unchanged. This remediation closes prior findings with component-by-component ancestor continuity revalidation, staged/published inode+byte verification, request-parent authority drift fail-close, and a native intermediate-directory replacement witness.
- Evidence: `python3 -m unittest tools.psm_wma.test_immutable_source_collection`=`51/51 PASS`; `python3 -m py_compile tools/psm_wma/immutable_source_collection.py tools/psm_wma/test_immutable_source_collection.py` PASS; `git diff --check` PASS. All fixtures use TemporaryDirectory/local Git only.
- Request exact final verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_REAL_ADAPTER_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: real source/checkpoint/manifest/data/cache I/O; collection/receipt/publication mutation; request execution; child/runtime/config changes; GPU/CUDA/torchrun; training, evaluation, inference and LIBERO4IN1.

## Implementation review request — collection adapter CPU/static

- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-CPU-STATIC`.
- Formal root: `34cedc9ff227c35b387666ae824d282b14d2b1f5`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: only the existing `tools/psm_wma/immutable_source_collection.py` executor and its direct stdlib test. The implementation adds NativeRootFd, same-FD regular-file reads, AtomicFileEvidenceSink, NativeCollectionGit transaction seams, fail-closed native binding/CLI grammar and temporary Git regressions; canonical injected algorithm remains unchanged.
- Evidence: `python3 -m unittest tools.psm_wma.test_immutable_source_collection`=`40/40 PASS`; `python3 -m py_compile tools/psm_wma/immutable_source_collection.py tools/psm_wma/test_immutable_source_collection.py`; `git diff --check` PASS.
- Request exact final verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_REAL_ADAPTER_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: real source/checkpoint/manifest/data/cache I/O; collection/receipt/publication mutation; request execution; child/runtime/config changes; GPU/CUDA/torchrun; training, evaluation, inference and LIBERO4IN1. Approval is limited to this root CPU/static implementation review.

## Remediation implementation review request — descriptor-stable collection adapter

- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-CPU-STATIC`.
- Formal root: `99bafeb060054da29052fcc4bd1121f075e85ad5`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: only `tools/psm_wma/immutable_source_collection.py` and `tools/psm_wma/test_immutable_source_collection.py`; Gitlink unchanged. `NativeCollectionGit.snapshot()` now opens the worktree root and every present allowlisted file through retained no-follow directory/file FDs, deriving type/identity/bytes from the same FD. `AtomicFileEvidenceSink` binds its parent directory FD before staging and publishes/cleans up exclusively relative to that FD.
- Evidence: `python3 -m unittest tools.psm_wma.test_immutable_source_collection` = `50/50 PASS`; `python3 -m py_compile tools/psm_wma/immutable_source_collection.py tools/psm_wma/test_immutable_source_collection.py` PASS; `git diff --check` PASS. Temporary-only witnesses cover 100644/100755, intermediate/final symlink and directory rejection, replacement after FD open, evidence-parent symlink/replacement, and direct `NativeCollectionGit` + `NativeRootFd` `collect_synthetic()` PASS plus native rollback equality.
- Request exact final verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_REAL_ADAPTER_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: real source/checkpoint/manifest/data/cache I/O; collection/receipt/publication mutation; request execution; child/runtime/config changes; GPU/CUDA/torchrun; training, evaluation, inference and LIBERO4IN1.

## Remediation implementation review request — snapshot continuity and publication cleanup

- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-CPU-STATIC`.
- Formal root: `831be4b99f8564bb3695e445dcdfeb1770d7e7f0`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: only `tools/psm_wma/immutable_source_collection.py` and its direct stdlib test; Gitlink unchanged. This remediation makes optional snapshot absence conditional on retained-guard continuity revalidation, closes opened descriptors on post-open drift, revalidates the frozen evidence-parent pathname after link and before return, and removes only the identity-proven final link created by this emission on post-link failure.
- Direct temporary-fixture witnesses: native snapshot ancestor disappearance fails rather than returns an authoritative absent state; visible preflight snapshot leak fails and restores the snapshot; staged `.pending` replacement leaves no final residue; parent relocation fails and leaves no accepted destination in either relocated or replacement parent.
- Evidence: `python3 -m py_compile tools/psm_wma/immutable_source_collection.py tools/psm_wma/test_immutable_source_collection.py && python3 -m unittest tools.psm_wma.test_immutable_source_collection && git diff --check` = `54/54 PASS`, py_compile PASS, diff-check PASS. Fixtures use only TemporaryDirectory/local Git.
- Request exact final verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_REAL_ADAPTER_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: real source/checkpoint/manifest/data/cache I/O; collection/receipt/publication mutation; request execution; child/runtime/config changes; GPU/CUDA/torchrun; training, evaluation, inference and LIBERO4IN1.

## Remediation implementation review request — retained staging authority and final cleanup continuity

- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-CPU-STATIC`.
- Formal root: `77564a85c07a6c936c52fd0b63810994a879b5fc`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: only `tools/psm_wma/immutable_source_collection.py` and its direct stdlib test; Gitlink unchanged. Staging identity is now captured from the original `O_CREAT|O_EXCL` write/fsync FD, retained through publication verification; pending cleanup is followed by the final frozen-parent and published-leaf identity/bytes validation.
- Direct temporary-fixture witnesses: same-byte foreign hardlink replacement between write-FD close and pathname identity capture fails with no destination residue; parent relocation during final `.pending` cleanup fails with no accepted destination at replacement or relocated paths.
- Evidence: `python3 -m py_compile tools/psm_wma/immutable_source_collection.py tools/psm_wma/test_immutable_source_collection.py && python3 -m unittest tools.psm_wma.test_immutable_source_collection && git diff --check` = `55/55 PASS`, py_compile PASS, diff-check PASS. Fixtures use only TemporaryDirectory/local Git.
- Request exact final verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_REAL_ADAPTER_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: real source/checkpoint/manifest/data/cache I/O; collection/receipt/publication mutation; request execution; child/runtime/config changes; GPU/CUDA/torchrun; training, evaluation, inference and LIBERO4IN1.

## Remediation implementation review request — final leaf validation path continuity

- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-CPU-STATIC`.
- Formal root: `d806a9c8bcd04a57fe705c5716fe79e554e4d590`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: only `tools/psm_wma/immutable_source_collection.py` and direct stdlib test. After final retained-parent leaf inode/byte validation, the sink now performs the final global frozen-parent continuity check immediately before success.
- Direct witness: relocates/replaces the parent after the final leaf is opened for validation; emit must fail and leave no evidence under either the replacement or relocated parent.
- Evidence: `python3 -m py_compile tools/psm_wma/immutable_source_collection.py tools/psm_wma/test_immutable_source_collection.py && python3 -m unittest tools.psm_wma.test_immutable_source_collection && git diff --check` = `56/56 PASS`, py_compile PASS, diff-check PASS; fixtures only TemporaryDirectory/local Git.
- Request exact final verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_REAL_ADAPTER_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: real source/checkpoint/manifest/data/cache I/O; collection/receipt/publication mutation; request execution; child/runtime/config changes; GPU/CUDA/torchrun; training, evaluation, inference and LIBERO4IN1.

## Design review request — authority-root causal worktree identity

- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-DESIGN`.
- Formal root: `0dedec97f1d5e2c62ec980b6daffb7f9da472cda`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only docs design `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_worktree_identity_design_v0.1.md`. It resolves v0.8's native-Git post-add directory identity gap by precreating an empty clean root through a retained parent FD, retaining clean FD identity through Git fill, and requiring parent-FD/clean-FD/path identity agreement before any later stage.
- Review focus: whether precreated-empty-directory Git semantics, retained FD continuity, ownership-limited cleanup, replacement/symlink/nonempty/metadata-drift rejection, and legacy v0.8 negative-route preservation are sufficient; confirm no materialization execution is implied.
- Request exact final verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_WORKTREE_IDENTITY_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: real worktree/materialization/source/checkpoint/manifest/data/cache I/O; collection/receipt/publication mutation; child/runtime/config changes; GPU/CUDA/torchrun; training, evaluation, inference and LIBERO4IN1.

## Remediation design review request — capability-derived Git worktree target

- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-DESIGN`.
- Formal root: `c6ac4639d2abb6bb19263e1ee923902419844fd5`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only docs remediation `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_worktree_identity_design_v0.2.md`, plus task/session records; child unchanged. It supersedes v0.1 after the formal HIGH that Git consumed a mutable absolute CLEAN target.
- Review focus: exact `mkdirat -> clean_fd -> inherited parent FD6 -> /proc/self/fd/6/<clean_name>` target chain; `close_fds=True` / `pass_fds=(6,)` / CLOEXEC and descendant lifetime; no global-path fallback; administrative metadata and cleanup fail-close; and the actual temporary-Git target-resolution race witness proving foreign replacement is not mutated.
- Evidence: `git diff --check` PASS; formal-tree Gitlink is `93a89ba61306d840a008813f62f26a34d54850f4`; no project code, real Git/worktree/materialization, source/checkpoint/manifest/data/cache I/O, child change, GPU or training ran.
- Request exact final verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_WORKTREE_IDENTITY_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: real worktree/materialization/source/checkpoint/manifest/data/cache I/O; collection/receipt/publication mutation; child/runtime/config changes; GPU/CUDA/torchrun; training, evaluation, inference and LIBERO4IN1.

## Remediation design review request — leaf-capability Git worktree target

- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-DESIGN`.
- Formal root: `56acad8f39241c8c03fa770aa39468a3e71a2349`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only docs remediation `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_worktree_identity_design_v0.3.md`, plus task/session records; child unchanged. It supersedes v0.2 after its formal HIGH that parent-FD target still re-resolved a mutable clean leaf entry.
- Review focus: exact retained leaf contract `clean_fd -> git_target_fd=6 -> /proc/self/fd/6`; FD7/FD9 owner mapping; `close_fds=True` / `pass_fds=(6,)` / CLOEXEC and re-dup cleanup lifetime; no parent-derived or global fallback; and actual temporary-Git same-parent leaf-replacement witness proving foreign B is never mutated.
- Evidence: `git diff --check` PASS; formal-tree Gitlink is `93a89ba61306d840a008813f62f26a34d54850f4`; no project code, real Git/worktree/materialization, source/checkpoint/manifest/data/cache I/O, child change, GPU or training ran.
- Request exact final verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_WORKTREE_IDENTITY_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: real worktree/materialization/source/checkpoint/manifest/data/cache I/O; collection/receipt/publication mutation; child/runtime/config changes; GPU/CUDA/torchrun; training, evaluation, inference and LIBERO4IN1.

## Remediation design review request — leaf capability metadata spelling

- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-DESIGN`.
- Formal root: `bfa10d34a130a3616e351ccd1aaecaa6a3dc0e95`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only docs v0.4. It narrows v0.3 target spelling to `/proc/self/fd/6/.`; an isolated temporary local-Git probe showed this preserves leaf entry authority and canonical `worktree list/remove` metadata behavior. No implementation draft is in formal scope.
- Request exact verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_WORKTREE_IDENTITY_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Prohibited: real worktree/materialization/source/checkpoint/manifest/data/cache I/O, collection/receipt/publication, child/runtime/config, GPU/CUDA/torchrun, training/eval/inference/LIBERO4IN1.

### Formal-root correction

The preceding request's root SHA was transcribed incorrectly. Its sole valid formal root is
`bfa10d345f2003a3a123f69dc836462fe05959d9`; child/Gitlink remains
`93a89ba61306d840a008813f62f26a34d54850f4`. Please bind any verdict only to this corrected pair.

## Remediation design review request — non-destructive leaf cleanup fail-close

- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-DESIGN`.
- Formal root: `019643a9b17ebdda8f74b5c5fac90cb37c23f18f`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only docs remediation `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_worktree_identity_design_v0.5.md`, plus task/session records; child unchanged. It supersedes v0.4 cleanup after HIGH-1: global `<clean>` is no longer a permitted destructive native-Git target. Add remains exact retained-leaf `/proc/self/fd/6/.`; if post-add failure needs cleanup, no Git remove or namespace mutation may occur and result is `ROLLBACK_INCOMPLETE` with A/metadata/B preserved.
- Review focus: confirm that the native fixture fact (`git worktree remove --force /proc/self/fd/6/.` rejected by Git 2.34.1) makes this fail-close contract preferable to any global fallback; verify retained-FD-only proof, no destructive cleanup consumer, explicit future recovery Gate, and required same-parent cleanup-resolution-race witness preserving foreign B.
- Evidence: formal-tree scope is only this design plus `SESSION.md`/`TODO.md`; `git ls-tree` confirms child Gitlink unchanged; `git diff --check` PASS. The probe used only an isolated `mktemp` local Git repository and did not access project origin/source/checkpoint/manifest/data/cache, child, GPU or training.
- Request exact final verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_WORKTREE_IDENTITY_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: real worktree/materialization/source/checkpoint/manifest/data/cache I/O; collection/receipt/publication mutation; child/runtime/config changes; GPU/CUDA/torchrun; training, evaluation, inference and LIBERO4IN1.

## Implementation review request — fail-closed leaf worktree witness

- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-CPU-STATIC-IMPLEMENTATION`.
- Formal root: `94103f9e3b464541a027594f7858b87dc0110538`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: only `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py`, its direct witness, and task/session records; child unchanged. The launcher now precreates/retains leaf A, uses exact add target `/proc/self/fd/6/.` with inherited FD6 only, compares directory identity by `(st_dev,st_ino,S_IFMT)`, and turns all cleanup paths into retained-FD revalidation plus non-destructive `ROLLBACK_INCOMPLETE` (no `worktree remove`, global path, or namespace mutation).
- Review focus: exact FD inheritance/target, directory proof that permits legitimate Git fill but rejects replacement, normal residue and same-parent foreign-B preservation, no production cleanup Git consumer, and diagnostic-only native leaf-remove fixture. Note: leaf-remove can succeed when registration was created by leaf add; implementation does not use that fact as cleanup authority and retains the approved fail-closed production contract.
- Evidence: `python3 -m py_compile ...v0.8.py ...v0.8_witness_test.py && python3 ...v0.8_witness_test.py && git diff --check` PASS; `13 tests OK`. All fixtures are local `TemporaryDirectory`/Git only; no project origin/source/checkpoint/manifest/data/cache, child, GPU or training access.
- Request exact final verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_WORKTREE_IDENTITY_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: real worktree/materialization/source/checkpoint/manifest/data/cache I/O; collection/receipt/publication mutation; child/runtime/config changes; GPU/CUDA/torchrun; training, evaluation, inference and LIBERO4IN1.

## Remediation implementation review request — fixed causal owner capability ABI

- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-CPU-STATIC-IMPLEMENTATION`.
- Formal root: `85a39d6243bb4bcc3e260ba3eb4279c52508d79f`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: only the existing root payload, its direct temporary stdlib/local-Git witness, `SESSION.md` and `TODO.md`; child unchanged. This remediation addresses the exact HIGH-1 in the prior review: retained parent is now fixed FD7; retained clean leaf is FD9; each Git consumer derives transient FD6 only from FD9 with exact `/proc/self/fd/6/.`, `close_fds=True`, `pass_fds=(6,)`, identity/CLOEXEC proof and closure after return. Owner binding is temporary-open → `F_DUPFD_CLOEXEC` ≥10 → source close → `dup2` fixed owner → identity proof; backing FD3/4/5 is constrained separately.
- Review focus: fixed FD7/FD9 ABI and collision handling; FD6 child-only lifecycle including post-add validation; no direct FD9 inheritance; handoff cannot target owner FDs; direct low-FD occupancy witness; preservation of the approved non-destructive `ROLLBACK_INCOMPLETE` cleanup and foreign-B safety.
- Evidence: `python3 -m py_compile ...v0.8.py ...v0.8_witness_test.py && python3 ...v0.8_witness_test.py -v && git diff --check` PASS; `14 tests OK`. Fixtures are only `TemporaryDirectory`/local Git or forked descriptor checks. No project origin/source/checkpoint/manifest/data/cache, child, GPU or training access.
- Request exact final verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_WORKTREE_IDENTITY_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: real worktree/materialization/source/checkpoint/manifest/data/cache I/O; collection/receipt/publication mutation; child/runtime/config changes; GPU/CUDA/torchrun; training, evaluation, inference and LIBERO4IN1.

## Remediation implementation review request — per-child FD6 and pre-exec owner lifetime

- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-CPU-STATIC-IMPLEMENTATION`.
- Formal root: `71c4a2524e350509f8048bfb65ea1cc8180a1c57`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: existing root payload and direct temporary stdlib/local-Git witness only; child unchanged. Each `assert_worktree()` Git call now independently leases `FD9 -> FD6 -> child(pass_fds=(6,)) -> close FD6`; `prepare_exec_fds()` preserves non-inheritable owners FD7/FD9 through `execve`, so a failed exec reaches non-destructive cleanup with retained identity proof.
- Evidence: `py_compile`, verbose direct witness=`16 tests OK`, and `git diff --check` PASS. New witnesses assert FD6 absent before/after each of the two validation child leases, and that pre-exec FD preparation preserves FD7/FD9 for fail-close cleanup. Temporary local fixtures only; no real project I/O, child, GPU, or training.
- Request exact final verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_WORKTREE_IDENTITY_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: real worktree/materialization/source/checkpoint/manifest/data/cache I/O; collection/receipt/publication, child/runtime/config, GPU/CUDA/torchrun, training/eval/inference/LIBERO4IN1.

## Witness-only remediation review request — real handoff before forced exec failure

- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-CPU-STATIC-IMPLEMENTATION`.
- Formal root: `b3595395427114f73ff53a19a0c2b9180e39905f`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: direct root witness only; child unchanged. The existing forked pre-exec test now completes real fixture `handoff()` for all backing FD3/4/5, prepares pre-exec FDs, calls a deliberately nonexistent `execve`, catches `FileNotFoundError`, verifies retained FD7/FD9 identity/non-inheritance, then observes non-destructive `ROLLBACK_INCOMPLETE` cleanup.
- Evidence: `py_compile`, full witness suite=`16 tests OK`, `git diff --check` PASS; only temporary fixture paths/fork, no project source/data/cache/GPU/child/training.
- Request exact final verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_WORKTREE_IDENTITY_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Prohibited: all real materialization/source/checkpoint/manifest/data/cache I/O, collection/publication, child/runtime/config, GPU/CUDA/torchrun, training/eval/inference/LIBERO4IN1.

## Exact execution request review — immutable authority-root materialization v0.9

- Gate: `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-INSTANCE-CONSTRUCTION-AND-REVIEW`.
- Formal root: `57ef3d32452d990af98fda5edfe485376b772723`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only docs request `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_execution_request_v0.9.md`, with `SESSION.md` and `TODO.md`; child unchanged. The request binds the closed b359 authority parent, FD8 bootstrap ABI, four-module pre-import closure, parser/bootstrap/contract SHA identities and a byte-addressed v0.8 launcher-payload overlay. It adds no design/provenance Gate and does not execute anything.
- Evidence: v0.9 raw SHA-256=`eb21ba3d47bf2675a4bfddb9de5aea9478d0d344929193604114e1cdf92ad57e`; `git diff --check` and new-file no-index diff-check PASS. No worktree/backing/index/candidate/ref/evidence was created; no real source/checkpoint/manifest/data/cache I/O, collection/receipt/publication, child/runtime change, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1 ran.
- Review focus: confirm the exact request is the controlling two-stage progression's immediate request (not another Gate); formal b359/child and full pre-import closure are bound; byte overlay is sufficient to derive one unambiguous launcher; expected-zero/freshness, one-shot stop and downstream prohibitions remain fail-closed.
- Request exact final verdict: `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT` or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited before/without that approval: all real materialization/source/checkpoint/manifest/data/cache I/O, authority/collection/receipt/source-evidence/publication mutation, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference and LIBERO4IN1.

## Design-refreeze review request — source-evidence closure stage split v0.3

- Gate: `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-DESIGN-REFREEZE`.
- Formal root: `5a668ad8871798a0c252ce9c05dbf167c36ba839`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only docs `docs/build/PSM-WMA_Local_Memory_v0.3.5_source_evidence_closure_execution_request_design_v0.3.md`, `SESSION.md`, `TODO.md`; child unchanged. It responds to the exact v0.9 formal HIGH: current root has materializer and collection executors but no production source-evidence producer/record/receipt/publication/root-audit entrypoint, so a stage-1-only request cannot be represented as v0.2's complete transaction.
- Review focus: verify v0.3 explicitly and narrowly supersedes v0.2 activation granularity; Stage 1 authority-root materialization hard-stops after independent tuple binding; Stage 2 keeps the v0.2 collection→producer→receipt→audit semantics and cannot begin before required production entrypoints plus independent approvals. Confirm this is the necessary explicit refreeze allowed by the v0.9 ChatGPT exact acceptance, not a silent provenance expansion.
- Evidence: docs-only; `git diff --check` and new-file no-index diff-check PASS; document SHA-256=`339a0cf827cca4f6a0e037459e369818741e4fa1b432147175ce8b4dd97f0c16`. No real I/O, authority/ref/evidence mutation, child/runtime change, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1 ran.
- Request exact final verdict: `APPROVE_TO_DESIGN_R09_B_TTT_V035_STAGE1_AUTHORITY_ROOT_MATERIALIZATION_REQUEST` or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: Stage-1/Stage-2 request construction or execution; real source/checkpoint/manifest/data/cache I/O; authority/collection/receipt/source-evidence/publication mutation; child/runtime/config changes; GPU/CUDA/torchrun; training, evaluation, inference and LIBERO4IN1.

## Exact request review — Stage-1 authority-root materialization v1.0

- Gate: `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-INSTANCE-CONSTRUCTION-AND-REVIEW`.
- Formal root: `d474849d7bf3bf556886f2887b2325aaab36a868`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only request `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_authority_root_materialization_request_v1.0.md`; Gitlink unchanged. It is the v0.3-approved Stage-1 request construction, not a new design Gate and not an execution.
- Exact bindings: closed parent `b3595395427114f73ff53a19a0c2b9180e39905f`, fixed ref `refs/heads/authority/r09-b-ttt-v035-immutable-source-v1`, selection/config raw SHA pair, Git/Python raw SHA pair, local/remote fixed-ref absence snapshot, and the inherited v0.9 FD3/4/5/8, pre-import closure, argv/bootstrap/contract and canonical whole-request fail-close contract.
- Review focus: verify that v1.0 is a fully fresh-bound, fail-closed Stage-1-only request under the approved v0.3 split; identify any field that must be explicit in the reviewable formal request rather than deferred to pre-exec binding; verify a PASS creates only an authority tuple then hard-stops.
- Request exact final verdict: `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_STAGE1_AUTHORITY_ROOT` or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: execution before all same-pair final approvals; all collection/receipt/source-evidence/record/package/publication; real source/checkpoint/manifest/data/cache I/O; child/runtime/config changes; GPU/CUDA/torchrun; training, evaluation, inference and LIBERO4IN1.

## Remediation request review — Stage-1 authority-root materialization v1.1

- Gate: `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-INSTANCE-CONSTRUCTION-AND-REVIEW`.
- Formal root: `3802c51bb156636d53842cefa8e4519f6dfabe81`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only v1.1 request Markdown plus its canonical JSON instance and session record; Gitlink unchanged. This is the exact remediation for ChatGPT v1.0 HIGH-1, not an execution.
- Evidence: canonical JSON `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_authority_root_materialization_request_v1.1.json` is 7,262 bytes with SHA-256 `7ba87345383657884024f9c0dd0c60489aac1ae7d6436df9340df8d3f08a95c1`; stdlib static verifier confirms canonical JSON, literal selection/config/bootstrap raw hashes, full parser argv SHA and four-module closure; diff-check PASS.
- Review focus: confirm the formal instance now itself carries the immutable raw inputs, FD3/4/5/8 contract, complete parser argv, outer isolated prefix/payload byte address, six-key environment, metadata, closure, route/absence snapshot and whole request bytes/SHA; runtime checks may only reject this instance. Confirm Stage-1 hard-stop and all downstream prohibitions remain intact.
- Request exact final verdict: `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_STAGE1_AUTHORITY_ROOT` or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: execution before all same-pair final approvals; all materialization/source/checkpoint/manifest/data/cache I/O; collection/receipt/source-evidence/record/package/publication; child/runtime/config changes; GPU/CUDA/torchrun; training, evaluation, inference and LIBERO4IN1.

## Payload-binding correction review — Stage-1 authority-root materialization v1.2

- Gate: `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-INSTANCE-CONSTRUCTION-AND-REVIEW`.
- Formal root: `08917d6dba3bde5ab284fd57d00b35b337fd1ea1`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only docs `PSM-WMA_Local_Memory_v0.3.5_stage1_authority_root_materialization_request_v1.2.md` and its canonical JSON, plus task/session ledger; Gitlink unchanged. This is a new docs-only request instance, not materialization.
- Reason: v1.1's approved literal payload binding was pre-exec replayed from the formal base with zero mutation and proved non-reproducible. v1.2 freezes the only mechanically reproducible ordered replay: parser-first splice, then literal source mappings, yielding parser `2336/f50e925c55fc3e953649fe5311a300f1fd67fd35ceb5bd1a93ef202b99f821c8`, bootstrap observed argv `2341/2b4fa86035a8d6a90e602ec496e54ee39fcdf97e894cabfcc8f6b8db98716861`, contract `182/2b8ccfa6b5f3ed5c2a812749f915f965771d4c740875f30aee34d766e90a1580`, and payload `17389/f3171fc64911e33be643a392854c3dc20c808c9dd1b02f5e091769655806f9a9`.
- Evidence: v1.2 canonical JSON is compact sorted UTF-8+LF, `8427 bytes`, SHA-256 `56780b494ed03cc15a07d0b16690ef6f9434fb2621a0659420a0ebd5a1e365b3`; stdlib replay verifier recomputed all four pairs; `json.tool` and `git diff --check` PASS. No launcher/project code, materialization/worktree/backing/index/ref/evidence, source/checkpoint/manifest/data/cache I/O, child, GPU or training ran.
- Review focus: verify ordered replay is complete and deterministic from formal base `615d6b117f810c4cb8c9459971caa32589352c93`; verify v1.2's canonical JSON remains a fully pre-frozen request and runtime can only reject drift; verify the Stage-1 tuple-only hard stop and downstream prohibitions remain intact.
- Request exact final verdict: `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_STAGE1_AUTHORITY_ROOT` or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: Stage-1 execution before all same-pair final approvals; all materialization/source/checkpoint/manifest/data/cache I/O; collection/receipt/source-evidence/record/package/publication; child/runtime/config changes; GPU/CUDA/torchrun; training, evaluation, inference and LIBERO4IN1.

## Remediation review — Stage-1 authority-root materialization v1.3

- Formal root: `f2d3f8c6790540b1fc604ef5f9d47870a9fd115a`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only docs v1.3 Markdown/JSON plus session ledger; no production or child change.
- Resolves v1.2: fresh snapshot now reobserved; `.git` binds stable dev/inode/type only (directory size excluded as legitimate Git-bookkeeping mutable); parser array applies adapter/collection mappings before canonicalization, so literal argv/replay/payload are consistent: `51a82.../3227.../a434.../4b85...`.
- Evidence: canonical JSON `7775 bytes` SHA `82f3103518ea953f6295e955f1d1f24e7945287dd19c1a47365647ca5fc22f7a`; stdlib JSON/parser verifier and diff-check PASS.
- Request verdict: `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_STAGE1_AUTHORITY_ROOT` or `REQUEST_CHANGES(file:line)`.
- Prohibited: all Stage-1 execution/materialization, source/checkpoint/manifest/data/cache I/O, downstream collection/receipt/publication, child, GPU and training.

## Design review request — authority-root config grammar CPU/static remediation v0.1

- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CONFIG-GRAMMAR-CPU-STATIC-REMEDIATION-DESIGN`.
- Formal root: `bf34641f2451b43c3c335bb747ef3c842768a382`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only docs design `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_config_grammar_cpu_static_remediation_design_v0.1.md`; child unchanged. It responds to the one approved v1.3 Stage-1 attempt failing before any mutation at `route_snapshot()` because its parser rejected the same frozen real `.git/config` quoted subsections it was intended to validate.
- Review focus: verify the proposed lexical grammar accepts only explicit ordinary/quoted Git sections needed by the frozen route, preserves raw-digest/descriptor/anti-symlink/config.worktree/commondir checks, and limits exact allowlisted section/key/value semantics rather than broadening Git config authority. Confirm both outer payload and bootstrap parser must share it, and that all tests are temporary CPU/static witnesses.
- Evidence: v1.3 attempt fail-close was recorded at root `0dd79aee`; post-failure inspection showed no clean root, index, ref, evidence or pending evidence. This formal commit is docs-only; `git diff --check` and no-index diff-check PASS. No retry, source/checkpoint/manifest/data/cache I/O, child/runtime/config edit, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1 ran.
- Request exact final verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CONFIG_GRAMMAR_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Explicitly prohibited: real materialization/retry; source/checkpoint/manifest/data/cache I/O; collection/receipt/record/package/publication; child/runtime/config changes; GPU/CUDA/torchrun; training, evaluation, inference and LIBERO4IN1.

## Remediation design review request — authority-root config grammar v0.2

- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CONFIG-GRAMMAR-CPU-STATIC-REMEDIATION-DESIGN`.
- Formal root: `9a0d48efc59d6e50e3d0ed2e80f670779d3fad64`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only v0.2 docs design. It closes all same-pair v0.1 findings: explicit case-preserving `(section, subsection, variable, value)` tuples; the exact 14 frozen real-config triples, including `[branch "V2"]` and the ghfast submodule URL; independently inline-equivalent outer/bootstrap parsers plus byte-identical canonical-output/failure witnesses.
- Review focus: verify that exact tuple preservation avoids case-collapsing authority, the table is complete/no broader than frozen config, and no import, route-defense weakening, retry or production activity is implied.
- Evidence: docs-only; no project code or child changed and no retry/materialization/source I/O/GPU/training ran.
- Request exact final verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CONFIG_GRAMMAR_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Prohibited: implementation before same-pair approvals; real materialization/retry, source/checkpoint/manifest/data/cache I/O, all downstream mutation, child/runtime/config changes, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.

## 2026-09-14 — Request: authority-root config grammar CPU/static implementation close review

- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CONFIG-GRAMMAR-CPU-STATIC-REMEDIATION`.
- Formal root: `cb4760ba050a05edd18ed08e1e33b2ea12dfc11c`.
- Formal child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Evidence: `tools/psm_wma/materialize_immutable_source_authority_root.py`, frozen outer `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py`, direct test `tools/psm_wma/test_materialize_immutable_source_authority_root.py`; `python3 -m py_compile ... && python3 -m unittest tools.psm_wma.test_materialize_immutable_source_authority_root && git diff --check` = py_compile PASS, 69/69 PASS, diff-check PASS.
- Scope: exact 14-tuple config grammar in both inline parsers; section/variable ASCII lowercase, quoted subsection bytes/case preserved, exact one ASCII separator in quoted headers, complete allowlist fail-close, and temporary local-Git fixtures only. Existing raw digest, descriptor/no-symlink/route barriers and Git-view drift check remain.
- Forbidden: no Stage-1 retry/materialization, no production source/checkpoint/manifest/data/cache I/O, no child/runtime change, GPU/CUDA/torchrun, training/eval/inference/LIBERO4IN1.
- Requested final verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_CONFIG_GRAMMAR_CPU_STATIC_IMPLEMENTATION` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — Bootstrap witness remediation close review

- Formal root: `8aa5e519d9778a94f228a1050433327c00433020`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only direct bootstrap config-category witness for the prior exact ChatGPT HIGH; it drives temporary fixture `v2` and escaped subsection config through the isolated bootstrap payload and compares its frozen `config-*` stderr category to runtime parser output.
- Evidence: adapter 70/70 PASS; outer witness 17/17 PASS; py_compile/diff-check PASS. No real I/O, child, GPU, or training.
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_CONFIG_GRAMMAR_CPU_STATIC_IMPLEMENTATION` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — Remediation request: authority-root config grammar CPU/static implementation close review

- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CONFIG-GRAMMAR-CPU-STATIC-REMEDIATION`.
- Formal root: `f709832e523cc250e9b751594bee5e4bb086f0d2`.
- Formal child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Resolves exact prior review: outer fixture now uses the frozen 14-tuple config; outer and runtime parsers expose/compare ordered tuples and frozen `config-*` categories for valid and `V2/v2`/escape/dot/path cases; bootstrap emits the same category taxonomy.
- Evidence: runtime unittest 69/69 PASS; outer frozen launcher witness 17/17 PASS; py_compile and diff-check PASS; all fixtures are temporary local Git only.
- Forbidden: Stage-1 retry/materialization, real source/checkpoint/manifest/data/cache I/O, child/runtime mutation, GPU/CUDA/torchrun, training/eval/inference/LIBERO4IN1.
- Requested final verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_CONFIG_GRAMMAR_CPU_STATIC_IMPLEMENTATION` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — Bootstrap full-corpus remediation close review

- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CONFIG-GRAMMAR-CPU-STATIC-REMEDIATION`.
- Formal root: `08d5828cdb4c12afa3b798ff01826c91ceb8755a`; formal child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Scope: root-only direct stdlib CPU/static test remediation for the exact `8aa5e519` review finding. `bootstrap_payload()` remains unmodified; the test extracts its emitted inline config-parser segment and executes it in an isolated temporary namespace. It compares the exact frozen 14-tuple canonical bytes with the frozen outer and runtime parsers, then compares their `config-*` failure categories for `v2`, escaped/dotted/path subsection, quoted-header spacing, unknown key, duplicate triple, remote/submodule URL drift and include. Existing real isolated `-I -S -B -c` bootstrap CLI witnesses remain for `v2` and escaped subsection.
- Evidence: `python3 -m py_compile tools/psm_wma/materialize_immutable_source_authority_root.py tools/psm_wma/test_materialize_immutable_source_authority_root.py && python3 -m unittest tools.psm_wma.test_materialize_immutable_source_authority_root && python3 docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8_witness_test.py && git diff --check` = py_compile PASS, root unittest 70/70 PASS, frozen outer witness 17/17 PASS, diff-check PASS. Formal tree changes only `SESSION.md`, `TODO.md`, and the direct root test; Gitlink unchanged.
- Requested final verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_CONFIG_GRAMMAR_CPU_STATIC_IMPLEMENTATION` or `REQUEST_CHANGES(file:line)`.
- Forbidden: no Stage-1 retry/materialization, production source/checkpoint/manifest/data/cache I/O, child/runtime change, GPU/CUDA/torchrun, training/eval/inference/LIBERO4IN1.

## 2026-09-14 — Stage-1 authority parent rebind design review

- Gate: `G0-R09-B-TTT-V035-STAGE1-AUTHORITY-PARENT-REBIND-DESIGN`.
- Formal root: `3e0c1657644b2b3c03f93c25ad910fa5d50a9ebd`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: docs-only v0.1 design. It records that old Stage-1 parent `b359...` contains adapter blob `70b292...` and old bootstrap grammar, whereas closed grammar root `08d...` is its descendant with blob `4a51bd...`; therefore a new Stage-1 request must rebind its parent and freshly rederive all parent-dependent identities. No request is constructed or executed.
- Request: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_REBOUND_STAGE1_AUTHORITY_ROOT_REQUEST` or `REQUEST_CHANGES(file:line)`.
- Forbidden: materialization/retry, real source/checkpoint/manifest/data/cache I/O, collection/receipt/publication, child/runtime, GPU/CUDA/torchrun, training/eval/inference/LIBERO4IN1.

## 2026-09-14 — Remediation delivery record: Stage-1 authority parent rebind design review

- Gate: `G0-R09-B-TTT-V035-STAGE1-AUTHORITY-PARENT-REBIND-DESIGN`.
- Formal root: `1ee147e5cbee13f447fd4d93ed464d3e5e8136ee`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only docs-only amendment to `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_authority_parent_rebind_design_v0.1.md`; child unchanged. It closes the prior design HIGH by requiring the next request to bind the rebound `08d5828cdb4c12afa3b798ff01826c91ceb8755a` tree's launcher `payload.base_path`, blob OID, raw SHA-256 and byte length, with ordered replay consuming only those base bytes and fail-closing on mismatch. Old-parent base, overlay fallback and mixed-parent reconstruction are prohibited.
- Evidence: formal-tree scope is exactly the design document; Gitlink resolves to the stated child. This is documentation only; no request construction or execution, materialization/retry, source/checkpoint/manifest/data/cache I/O, collection/receipt/record/package/publication, child/runtime mutation, GPU/CUDA/torchrun, training/evaluation/inference or LIBERO4IN1 occurred.
- Review focus: confirm the rebound-parent launcher base is now first-class authority; all parent-dependent values must be freshly rederived rather than copied; Stage-1 PASS remains tuple-only/hard-stop; approval authorizes only construction of one new docs-only request instance, followed by independent review.
- Requested final verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_REBOUND_STAGE1_AUTHORITY_ROOT_REQUEST` or `REQUEST_CHANGES(file:line)`.
- This append repairs the missing canonical same-pair Inbox delivery record noted by ChatGPT's formal review; it does not alter that review's formal target or authorize execution.

## 2026-09-14 — Exact request review: rebound Stage-1 authority-root materialization v1.4

- Gate: `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-INSTANCE-CONSTRUCTION-AND-REVIEW`.
- Formal root: `08cf3f7b15b743ba536bfc7f02b00e1d594e3e0d`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only docs `PSM-WMA_Local_Memory_v0.3.5_stage1_authority_root_materialization_request_v1.4.{md,json}` plus ledger updates; child unchanged. This is an exact docs-only request instance, not execution.
- Authority: formal parent is `08d5828cdb4c12afa3b798ff01826c91ceb8755a`; new-parent launcher base is path `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py`, blob `af19a9eb66ecaf8bd0b92a48ab1867f105026658`, SHA-256 `8b0fad39857fb72e3a3eb317f4acf6f2d6e94e196935f52f07d6170e79c678dd`, bytes `18966`. Ordered replay permits only that base, requires one owner-FD pair, and rejects old-base/fallback/mixed-parent input.
- Evidence: canonical JSON `8482 bytes`, SHA-256 `831f9d8a246029333c07621debd197ff0ac8bdf1ccf7c9da4215ce8bf7c14b85`; stdlib canonical-field/single-FD verifier and `git diff --check` PASS. No materializer, real source/checkpoint/manifest/data/cache I/O, collection/receipt/record/package/publication, child/runtime, GPU/CUDA/torchrun, training/evaluation/inference or LIBERO4IN1 ran.
- Requested verdict: `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_STAGE1_AUTHORITY_ROOT` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — Design review: Stage-1 v1.7 launcher freeze

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`.
- Formal root: `47801113f90348304a2843ff215d48240a490d7e`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only docs design. It proposes a SHA-verified stdlib launcher-replay module and temporary CPU/static tests after v1.6's pre-exec wrapper SHA mismatch; no implementation or retry.
- Review focus: fixed formal Git-blob replay, zero preexisting owner-FD, unique adjacent insertion, outer-payload verification before exec, drift test matrix, and strict no-real-I/O boundary.
- Requested verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_LAUNCHER_FREEZE_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Prohibited: execution before all same-pair approvals; even then Stage-1 PASS is authority-tuple-only hard stop. No downstream mutation, child, GPU or training is authorized.

## 2026-09-14 — Remediation request review: rebound Stage-1 authority-root materialization v1.6

- Gate: `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-INSTANCE-CONSTRUCTION-AND-REVIEW`.
- Formal root: `ea6d75f659cfbc978f0180ffcfc266792f85854e`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only v1.6 Markdown/JSON and records; child unchanged. This is a docs-only fix for the v1.5 post-approval execution-boundary ambiguity.
- Delta: §5 now grants only after unanimous same-pair approval exactly one Stage-1 attempt for this exact request; pre-mutation request/base/freshness/FD/path/ref drift is `BLOCKED_AUTHORITY_NOT_CLOSED` with zero mutation; PASS emits only authority tuple then hard-stops; failed/consumed attempt needs a new request and approval. Retry/second attempt, Stage-2/downstream, child, GPU and training remain prohibited.
- Evidence: canonical JSON=`8622 bytes / 2a82314c9b8594230229ef2c875b0611e2131377bbe267b589c762a588fd4421`; JSON static canonicalization and diff-check PASS. No execution, real I/O, child/runtime change, GPU or training occurred.
- Requested verdict: `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_STAGE1_AUTHORITY_ROOT` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — Remediation request review: rebound Stage-1 authority-root materialization v1.5

- Gate: `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-INSTANCE-CONSTRUCTION-AND-REVIEW`.
- Formal root: `29f6c6a5120fa1d0397a0a21ea9e37024e79768a`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only docs `PSM-WMA_Local_Memory_v0.3.5_stage1_authority_root_materialization_request_v1.5.{md,json}` plus task/session record; child unchanged. This is an exact docs-only v1.4 remediation request, not execution.
- Resolves all v1.4 blockers: (1) exact new-parent RAW[2] must contain zero owner-FD flags, then inserts exactly one adjacent `--bootstrap-owner-root-fd,8` after bootstrap-project-root value and replays parser byte-identically; (2) records a new 2026-09-14 15:59 CST zero-mutation observation of `.git`, `.git/config`, local/remote fixed ref and four absence paths; (3) formal Markdown directly binds sibling canonical JSON=`8618 bytes / 6579bca17667803ddcd14cc49a5522ef0b9538753dd3ca3e872258a5848d1f30` and requires runtime recomputation before freshness/FD checks.
- Evidence: `json.tool`, canonical JSON + owner-FD static assertions, parser replay byte-identity (`2336 / 1a9543ec...`), and `git diff --check` PASS. No launcher/materializer, real source/checkpoint/manifest/data/cache I/O, collection/receipt/record/package/publication, child/runtime, GPU/CUDA/torchrun, training/evaluation/inference or LIBERO4IN1 ran.
- Requested verdict: `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_STAGE1_AUTHORITY_ROOT` or `REQUEST_CHANGES(file:line)`.
- Prohibited: execution before all same-pair approvals; even then Stage-1 PASS is authority-tuple-only hard stop. No downstream mutation, child, GPU or training is authorized.

## 2026-09-14 — Remediation design review: Stage-1 v1.7 launcher freeze v0.2

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`.
- Formal root: `699e8567669187faadf1c46b36bff02eabb0206e`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Scope: root-only docs-only remediation of the v0.1 design findings. v0.2 supersedes v0.1, corrects the formal Gate, explicitly requests the positive CPU/static implementation verdict, and freezes a no-I/O pure `replay_outer_payload(base_source, binding)` API, ordered substitution inputs, output bytes/SHA records, and `AuthorityReplayError("BLOCKED_AUTHORITY_NOT_CLOSED:<category>")` failure contract. It also records the complete v1.6 base/parser/outer identities and mandates fresh v1.7 observation.
- Evidence: formal tree is only `SESSION.md`, `TODO.md`, v0.1 supersession notice and v0.2; Gitlink unchanged; `git diff --check` PASS. No launcher module/test implementation, request construction, Stage-1 retry/materialization, real source/checkpoint/data/cache I/O, child/runtime mutation, GPU/CUDA/torchrun, training/eval/inference/LIBERO4IN1 occurred.
- Requested final verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_LAUNCHER_FREEZE_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — Remediation design review: Stage-1 v1.7 launcher freeze v0.3

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`.
- Formal root: `cb00b8ae9702a8c8739673bc90ae287d1282ced6`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Scope: docs-only minimal remedy to v0.2 same-pair final findings. v0.3 supersedes v0.2 and freezes the two exact allowed future paths, a flag/adjacent-value-aware parser table (so `--cwd` and `--bootstrap-project-root` independently replace their equal old values), the full canonical parser/source replacement tables, pure API and fail-close contract.
- Evidence: formal tree only changes `SESSION.md`, `TODO.md`, v0.2 supersession notice and v0.3; Gitlink unchanged; `git diff --check` PASS. No module/test implementation, request construction, Stage-1 retry/materialization, real source/checkpoint/data/cache I/O, child/runtime mutation, GPU/CUDA/torchrun, training/eval/inference/LIBERO4IN1 occurred.
- Requested final verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_LAUNCHER_FREEZE_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — Remediation design review: Stage-1 v1.7 launcher freeze v0.4

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`; formal root=`5acb0bdadcc5ecbc22b720e5eeac6a3c95780bdc`; child/Gitlink=`93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root docs-only v0.3 High remedy. v0.4 appends exactly four missing source self-check replacements: bootstrap bytes/SHA and parser bytes/SHA; it requires exact surrounding-literal targeting, canonical outer bytes/SHA witness, and per-literal drift negatives. No implementation or real I/O.
- Evidence: formal tree only `SESSION.md`/`TODO.md`/v0.4; Gitlink unchanged; diff-check PASS. Forbidden: request construction, Stage-1 retry/materialization, source/checkpoint/data/cache I/O, child/runtime, GPU/CUDA/torchrun, training/eval/inference/LIBERO4IN1.
- Requested final verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_LAUNCHER_FREEZE_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — Implementation close review: Stage-1 v1.7 launcher replay

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`; formal root=`97020af908d55d39349c9a7426b960e63a72f4eb`; child/Gitlink=`93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: only approved root paths `tools/psm_wma/stage1_v17_launcher_replay.py` and `tools/psm_wma/test_stage1_v17_launcher_replay.py`, plus SESSION record. Pure injected-bytes replay; no main/Git/path/FD/network/exec I/O.
- Evidence: `python3 -m py_compile ... && python3 -m unittest tools.psm_wma.test_stage1_v17_launcher_replay && git diff --check` PASS; unittest=5/5. No request construction, retry/materialization, real source/checkpoint/data/cache I/O, child/runtime, GPU or training.
- Requested final verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_LAUNCHER_FREEZE_CPU_STATIC_IMPLEMENTATION` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — Remediation close review: Stage-1 v1.7 launcher replay

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`; root=`56ea8c7cfc36375a784aff2e30c07c2516e0adfe`; child/Gitlink=`93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: only the two approved root paths. Addresses prior HIGHs: context-aware four self-check source guards, ordered parser targets, canonical v1.6 Git-blob injected CPU witness with exact parser/outer identities, and four self-check drift negatives.
- Evidence: py_compile, direct unittest=8/8, diff-check PASS. No main/production I/O, request/retry, child, GPU, or training.
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_LAUNCHER_FREEZE_CPU_STATIC_IMPLEMENTATION` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — No-I/O remediation close review: Stage-1 v1.7 launcher replay

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`; root=`467e6665b95be450ca5900c6aa6ce14e94f759d5`; child/Gitlink=`93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: only approved two root files. Removes test `git show`/path I/O by embedded gzip/base64 frozen 18966-byte base with SHA assertion; source self-check rows now replace exact surrounding spans, not naked global strings.
- Evidence: py_compile, unittest=8/8, diff-check PASS; no real I/O/request/retry/child/GPU/training.
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_LAUNCHER_FREEZE_CPU_STATIC_IMPLEMENTATION` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — Failure-matrix close review: Stage-1 v1.7 launcher replay

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`; root=`98a7b0c746770eef767ac67321fc43aa6c6b6d9e`; child/Gitlink=`93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: only approved test path. Adds direct canonical base identity/raw-shape negatives and each source table rows 0–3 drift; prior 4–7 drift, relocation, order, owner and adjacent-value coverage remain.
- Evidence: py_compile, unittest=11/11, diff-check PASS; no real I/O/request/retry/child/GPU/training.
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_LAUNCHER_FREEZE_CPU_STATIC_IMPLEMENTATION` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — Table-authority close review: Stage-1 v1.7 launcher replay

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`; root=`64ffa794042ba866339446706e37c51335827d31`; child/Gitlink=`93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: approved two root files. Canonical parent now requires immutable parser/source table digests before mutation; direct negatives cover parser extra no-op and source reorder.
- Evidence: py_compile, unittest=12/12, diff-check PASS; no I/O/request/retry/child/GPU/training.
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_LAUNCHER_FREEZE_CPU_STATIC_IMPLEMENTATION` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — Parent-binding close review: Stage-1 v1.7 launcher replay

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`; root=`50b0bffeb4c94b0994d7c7bf705077fb51a9e48f`; child/Gitlink=`93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: approved two root files. Canonical base SHA now mandates frozen formal parent before table digests; direct noncanonical-parent bypass negative added.
- Evidence: py_compile, unittest=13/13, diff-check PASS; no I/O/request/retry/child/GPU/training.
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_LAUNCHER_FREEZE_CPU_STATIC_IMPLEMENTATION` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — Design review: Stage-1 v1.7 request-instance construction

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`.
- Formal root: `218f5f6254e7e926ae2d9ad8fb8206d037a9cadf`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only docs `PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_design_v0.1.md`, plus coordination records. The design is only for constructing one future docs-only exact request instance; it is not that request and cannot execute it.
- Frozen dependencies: formal parent `08d5828cdb4c12afa3b798ff01826c91ceb8755a`; verified launcher base `af19a9eb66ecaf8bd0b92a48ab1867f105026658` / `8b0fad39857fb72e3a3eb317f4acf6f2d6e94e196935f52f07d6170e79c678dd` / `18966`; closed pure replay implementation root `50b0bffeb4c94b0994d7c7bf705077fb51a9e48f` with module/test raw SHA recorded in the design.
- Review focus: require a same-round zero-mutation freshness snapshot, canonical request bytes/SHA, all replay/config/parser/environment/owner-FD closures, no fallback/stale inference, and `BLOCKED_AUTHORITY_NOT_CLOSED` before any exec. Confirm the requested design verdict authorizes only docs-only request construction followed by a new exact-pair review.
- Forbidden: request construction before this design is approved; all materialization/retry, launcher execution, source/checkpoint/manifest/data/cache I/O, collection/receipt/record/package/publication, child/runtime mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.
- Requested final verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — v0.9 request-instance remediation review

- Formal root: `de92df51`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only v0.9 docs. Closes v0.8 HIGHs with an explicit existing-object P0 allowlist and derived-only outer payload (`18875` / `658e...`); no request/materialization/runtime/GPU/training.
- Requested final verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — Remediation design review: Stage-1 request-instance v0.7

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`; root=`6361fdbcfded999e43a4efb86861f75734cef100`; child/Gitlink=`93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: docs-only v0.6 remediation. v0.7 defines non-consuming P0 formal-Git-object acquisition plus pure replay binding, non-consuming P1 injected-byte projection, then C as the uniquely consuming authority point before its first freshness observation. Any C failure is no-retry; P0/P1 failures do not consume C.
- Review focus: verify P0 supplies exact verified outer/adapter bytes without ambient worktree inference; replay input/output is bound; Phase-C consumption point is unambiguous; two-query freshness, detached request identity and all execution prohibitions remain intact.
- Evidence: formal tree only v0.7/SESSION/TODO; Gitlink unchanged; `git diff --check` PASS. No project code, request construction, real I/O, child, GPU or training.
- Requested final verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — Design review: Stage-1 v1.7 request projection preflight v0.1

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-PROJECTION-PREFLIGHT-CPU-STATIC`.
- Formal root: `c4c2d7c66b50a829dccbec811d670cc8f470c5f2`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only docs design plus records. It responds to the consumed v0.5 construction failure by defining a pure injected-bytes AST projection helper before any future construction authority: no Git/remote/filesystem/subprocess/request output, and no authority consumption on its own failure. It does not recover or retry the consumed authority.
- Review focus: strict AST-only RAW/base64/boot extraction, complete raw closure projection, fail-close taxonomy, embedded-fixture CPU/static-only tests, and the fact that a future construction still needs a distinct design/approval after this helper closes.
- Evidence: formal Gitlink unchanged; `git diff --check` PASS. No helper execution, Git/remote/filesystem I/O, request construction, materialization, launcher, source/checkpoint/manifest/data/cache access, child/runtime, GPU/CUDA/torchrun, training/evaluation/inference or LIBERO4IN1 occurred.
- Requested final verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_REQUEST_PROJECTION_PREFLIGHT_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — Implementation close review: projection preflight

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-PROJECTION-PREFLIGHT-CPU-STATIC`.
- Formal root: `b85584e18b9b4ebaf85d4a07f63a9d87908e0c98`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: only approved root pure-stdlib module/test. Evidence: `py_compile`, direct unittest `3/3`, and `git diff --check` PASS; no Git/network/filesystem in helper/test, no request construction or runtime execution.
- Requested final verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_REQUEST_PROJECTION_PREFLIGHT_CPU_STATIC_IMPLEMENTATION` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — Correction: projection remediation formal SHA

- The immediately preceding remediation request's expanded root SHA was transcribed incorrectly and is void. Its correct formal root is `5580e20ca918ec3287f77c17cdfe485dd890b440`; child/Gitlink remains `93a89ba61306d840a008813f62f26a34d54850f4`.
- This correction changes no code, scope, evidence, or requested verdict. Please review only the corrected exact pair and reply `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_REQUEST_PROJECTION_PREFLIGHT_CPU_STATIC_IMPLEMENTATION` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — Remediation design review: projection preflight v0.3

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-PROJECTION-PREFLIGHT-CPU-STATIC`.
- Formal root: `d9e4be0e990c2847f402c6e9913ea42a662ddb4c`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: docs-only v0.2 HIGH remedy. It freezes the exact bootstrap argv preimage `json.dumps(["--", *parser_argv_items], separators=(",", ":"), ensure_ascii=False).encode("utf-8")`, its 2341-byte/SHA identity, exact contract identity, schema field, and CPU/static drift assertions.
- Requested final verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_REQUEST_PROJECTION_PREFLIGHT_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — Remediation design review: Stage-1 v1.7 request projection preflight v0.2

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-PROJECTION-PREFLIGHT-CPU-STATIC`.
- Formal root: `ec12f296a321d22f52d9de652a4007a0a1f5d35b`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: docs-only v0.1 remediation. It supplies injected verified adapter source for bootstrap extraction, exact implementation paths, frozen result dataclasses, strict boot AST whitelist, and flag-aware parser validation that permits canonical duplicate values.
- Requested final verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_REQUEST_PROJECTION_PREFLIGHT_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — Remediation design review: Stage-1 v1.7 request-instance construction v0.2

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`.
- Formal root: `0831e0ba2dcb5c93e9069d2d20aca1790095dc97`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only docs v0.2 plus coordination records; v0.2 explicitly supersedes v0.1 construction-time I/O wording. It remains a design only: no request is constructed or executed.
- Exact remediation: after unanimous same-pair design approval, construction has a closed read-only allowlist: formal Git object/tree/base bytes; local `.git` identity/config bytes; frozen local ref; one `git ls-remote origin refs/heads/V2` query whose complete raw result is bound into the request; and designated path-absence checks. It fixes future Markdown/JSON output paths and required canonical JSON closures. All other network, filesystem content and runtime I/O remain prohibited.
- Forbidden: request construction before approval; materialization/retry; launcher/materializer execution; source/checkpoint/manifest/data/cache content I/O; collection/receipt/record/package/publication; directory/ref/artifact creation; child/runtime mutation; GPU/CUDA/torchrun; training/evaluation/inference/LIBERO4IN1.
- Requested final verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — Remediation design review: Stage-1 v1.7 request-instance construction v0.3

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`.
- Formal root: `0fc7965d9d1b55a99d0b1a384764f68464b02949`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only docs v0.3 plus coordination records; docs-only remediation of DS's v0.2 remote authority-ref absence finding. No request is constructed or executed.
- Exact remediation: construction may issue exactly two remote queries: `refs/heads/V2` only to bind advertised V2 identity, and `refs/heads/authority/r09-b-ttt-v035-immutable-source-v1` only to prove the fixed remote authority ref has empty output. Both complete raw outputs/lengths/SHA bind into the future request; the latter is the sole remote-absence authority. No fetch/push/other ref/network/service query is permitted.
- Forbidden: request construction before approval; materialization/retry; launcher/materializer execution; source/checkpoint/manifest/data/cache content I/O; collection/receipt/record/package/publication; directory/ref/artifact creation; child/runtime mutation; GPU/CUDA/torchrun; training/evaluation/inference/LIBERO4IN1.
- Requested final verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — Remediation design review: Stage-1 v1.7 request-instance construction v0.4

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`.
- Formal root: `2ccd42fadc325c10d072f236b9b5805c732446b3`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only docs v0.4 plus coordination records; no request construction/execution.
- Exact remediation: both permitted `git ls-remote` observations must bind returncode/stdout/stderr identities; authority-ref absence means exactly successful exit, zero stdout bytes/lines and zero stderr bytes. Timeout, nonzero exit, diagnostics, malformed/nonempty response fail-close and cannot prove absence.
- Requested final verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — Exact request review: Stage-1 v1.7 request instance v0.1

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-CONSTRUCTION-AND-REVIEW`.
- Formal root: `ad758f9589f4712ee97a169e1f4236aa59f158e6`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only exact docs request `PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.1.{md,json}` plus records. Review fresh formal/base/replay closure, successful two-query remote observations, local/remote authority-ref absence, output identity and execution boundaries.
- Evidence: JSON=`3054 bytes / 2fffb82a905f5e53d950c5cb3fc8235d6e58726a1144ca26a107a011d7c5a59d`; JSON parse and diff-check PASS.
- Requested final verdict: `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_STAGE1_V17_AUTHORITY_ROOT` or `REQUEST_CHANGES(file:line)`.
- Forbidden: before same-pair approval, all launcher/materializer/Stage-1 execution, source/checkpoint/manifest/data/cache I/O, child/runtime mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.

## 2026-09-14 — Exact request remediation review: Stage-1 v1.7 v0.2

- Formal root: `ca4df2bd9e01139b6f9e9abf507e6cf086726d63`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only v0.2 docs-only request replacement. It addresses v0.1 V2 provenance, complete closure/stream hashes and one-attempt semantics.
- Requested final verdict: `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_STAGE1_V17_AUTHORITY_ROOT` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — Design remediation review: Stage-1 v1.7 request-instance construction v0.5

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`.
- Formal root: `6af03900ab4080c6437a4aa4154ebec50b6617ef`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only docs v0.5 plus `SESSION.md`/`TODO.md`; no exact request is constructed or executed. It addresses the v0.2 same-pair final findings by replacing mathematically impossible JSON self-SHA embedding with a mandatory formal-tree Markdown-sidecar binding of the canonical JSON raw bytes, byte length, SHA-256 and blob OID. It retains all v0.3/v0.4 complete-closure and fresh same-round observation requirements.
- Evidence: formal Gitlink unchanged; `git diff --check` PASS. No remote observation, launcher/materializer, Stage-1 materialization/retry, source/checkpoint/manifest/data/cache/runtime I/O, child/runtime mutation, GPU/CUDA/torchrun, training/evaluation/inference or LIBERO4IN1 occurred.
- Review focus: confirm the detached pair binding is mechanically verifiable and does not weaken whole-request identity; confirm complete JSON closure and the two exact remote-query success contracts remain required; confirm approval authorizes only future docs-only construction of one replacement request, followed by independent exact-pair review.
- Requested final verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — Remediation close review: Stage-1 v1.7 request projection preflight

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-PROJECTION-PREFLIGHT-CPU-STATIC`.
- Formal root: `5580e20c7e406d7ceade9222353f355fe0a4a15d`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only remediation of `b85584e` in the approved projection module/direct test, plus SESSION/TODO coordination. It adds injected adapter Git-blob preimage OID verification, canonical parser/ordered pair/strict bootstrap AST checks, frozen result identities, and an entirely in-memory gzip/base64 fixture for the exact 18,875-byte outer and 91,814-byte adapter.
- Evidence: `py_compile`, direct unittest `6/6`, and `git diff --check` PASS. The helper/test perform no Git/network/path/subprocess/runtime I/O; no request construction/materialization, source/checkpoint/manifest/data/cache access, child change, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1 occurred.
- Review focus: confirm closure of the previous three HIGHs: adapter dual identity, frozen parser/bootstrap AST/identity contract, and direct canonical fixture plus fail-close evidence matrix. The formal tree retains the exact child Gitlink.
- Requested final verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_REQUEST_PROJECTION_PREFLIGHT_CPU_STATIC_IMPLEMENTATION` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — Second remediation close review: projection preflight

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-PROJECTION-PREFLIGHT-CPU-STATIC`.
- Formal root: `079167743685247d6aae62a671436e834411a3cb`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Scope: only the already-approved root pure-stdlib paths `tools/psm_wma/stage1_v17_request_projection.py` and `tools/psm_wma/test_stage1_v17_request_projection.py`, plus `SESSION.md`/`TODO.md` coordination. No child/runtime change.
- Remediation: outer `RAW[0]`/`RAW[1]` base64 arguments and `RAW[2]` parser JSON now require a single `ast.Constant(str|bytes)` via `_single_literal()`; recursive concatenation remains available only to the adapter `bootstrap_payload()` return. The frozen bootstrap argv construction is isolated as `["--", *items]` and covered by direct wrong-prefix/parser-substitution negatives. The embedded gzip/base64 fixture matrix now directly covers all three outer concatenation rejections, malformed base64 and JSON, every `ProjectedBytes` raw-length/SHA identity, and failed-call no-partial-result behavior.
- Evidence: `python3 -m py_compile tools/psm_wma/stage1_v17_request_projection.py tools/psm_wma/test_stage1_v17_request_projection.py && python3 -m unittest tools.psm_wma.test_stage1_v17_request_projection && git diff --check` PASS (`9/9`). Helper/tests remain injected-byte-only and perform no Git/network/filesystem/path/subprocess/launcher/materializer/request/runtime I/O.
- Forbidden: request construction, materialization/retry, source/checkpoint/manifest/data/cache access, child/runtime mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.
- Requested final verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_REQUEST_PROJECTION_PREFLIGHT_CPU_STATIC_IMPLEMENTATION` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — Design review: Stage-1 v1.7 request-instance construction v0.6

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`.
- Formal root: `76307bb65c08c1f9f35e3832be89c9cc617953eb`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Scope: root-only docs `PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_design_v0.6.md` plus coordination records; no runtime code or child change.
- Review focus: v0.5's one construction authority was consumed at zero-output AST failure. v0.6 makes closed projection root `079167743685247d6aae62a671436e834411a3cb` a non-consuming Phase-P precondition, isolates exactly one Phase-C construction attempt, retains the two-query fresh allowlist, detached JSON/Markdown whole identity, zero-mutation fail-close, and no-retry hard stop. Approval must authorize only construction of one future docs-only request pair, which itself needs a new exact-pair review.
- Evidence: formal tree contains only the three listed root docs/coordination paths; Gitlink unchanged; `git diff --check` PASS. No project code, request construction, Git/network/filesystem runtime I/O, materialization, child, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1 occurred.
- Requested final verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — Design remediation review: Stage-1 v1.7 request-instance construction v0.8

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`.
- Formal root: `6a2f52d6adc641edb0ac9215c72481a7dfca620a`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Scope: root-only docs `PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_design_v0.8.md` plus `SESSION.md`/`TODO.md`; no project or child code changes. The formal tree contains only these three paths.
- Exact remediation: v0.7 P0 failed before C because it asked formal parent `08d5828…` for the later helper path. v0.8 proves and freezes the actual replay base as parent path `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py`, blob `af19a9eb66ecaf8bd0b92a48ab1867f105026658`, 18966 bytes, SHA-256 `8b0fad39857fb72e3a3eb317f4acf6f2d6e94e196935f52f07d6170e79c678dd`; it separately binds the replay helper to implementation root `50b0bff…`. No P1, C, freshness observation, output, materialization, or request occurred, so v0.7 construction authority was not consumed.
- Evidence: parent-tree blob lookup, raw-byte SHA/length and formal Gitlink were independently checked; `git diff --check` PASS. The P0/P1 non-consuming versus C-before-first-observation one-attempt/no-retry semantics are unchanged.
- Forbidden: request construction before same-pair approval; materialization/retry; launcher/materializer execution; source/checkpoint/manifest/data/cache I/O; child/runtime mutation; GPU/CUDA/torchrun; training/evaluation/inference/LIBERO4IN1.
- Requested final verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or `REQUEST_CHANGES(file:line)`.

## 2026-09-14 — Canonical remediation design review: Stage-1 v1.7 request-instance v0.9

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`.
- Formal root: `de92df512e1a239e7c2fd2d8d6ea60c5fc9ca02c`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- This append-only application supersedes the earlier short-SHA v0.9 ledger line. Scope is the root-only `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_design_v0.9.md`; the formal tree contains that file only, with no child/runtime change.
- Review focus: verify P0 is a closed immutable-object allowlist (base, replay helper, adapter and projection helper), not a generic Git-source rule; verify the outer is derived solely by replay and then matches exactly `18875` bytes / SHA-256 `658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8`, never a Git object. Confirm P0/P1 remain non-consuming and C alone begins before the first freshness observation, consumes the sole authority and is no-retry.
- Evidence: formal `git diff-tree --no-commit-id --name-only -r` contains only the v0.9 design; formal Gitlink is the child above. No request construction, materialization, launcher/runtime execution, source/checkpoint/manifest/data/cache I/O, child mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1 occurred.
- Requested final verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or `REQUEST_CHANGES(file:line)`.
- Forbidden before same-pair final approval: request construction, materialization/retry, launcher/materializer execution, all real source/checkpoint/manifest/data/cache I/O, child/runtime mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.
