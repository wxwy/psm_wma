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
