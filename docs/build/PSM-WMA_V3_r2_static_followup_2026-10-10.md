# V3 r2 source integration: static follow-up and CPU validation

Date: 2026-10-10. Owner authorized direct Child-first / Root-Gitlink-second publication. This is author validation, not independent approval or Resume authorization.

## Source authority

The supplied prepublication handoff was stale. Fresh Git reads found r2 already implemented at Root `cf0c92731197bfdd0de073a4c07ca93194f58968` / Child `d41be4f5485dcd9321318840c8c278c1f7487924`; Root `5e7f2d2c2db39b7fc676d6a6f846af16e610eaf1` added publication bookkeeping. The original candidate ZIP was unavailable in this machine; validation used the actual published source, not a reconstructed bundle.

The published Trainer observer already accepts and forwards `payloads` and `optimizer`. All four internal calls were checked for keyword compatibility; the actual grouped Trainer/Resume tests were then exercised through the repository conftest.

## Follow-up scope

- Fix the 81 observed Ruff violations: import ordering, two unused imports and one-line test statements. Normalize formatting across r2 files and six earlier MC-01 files required by the migration Gate. Ruff rules/versions remain unchanged.
- All 19 Child files retain identical non-import Python AST. No Local-TTT math, policy loss, optimizer/scheduler algorithm, FSDP logic or DCP serializer is changed by this follow-up.
- Fix the evaluation identity test fixture to use `tmp_path/evaluation`: repository conftest writes logs into `tmp_path`, so the original fixture violated the production empty-output requirement. Keep every existing rejection assertion and the separate legacy-output test; do not weaken evaluation identity.
- Preserve all prior branches, notes, artifacts and original Formal30k source/checkpoints. SESSION/TODO only receive append-only records for this task.

## Current-instance evidence

Evidence: `docs/collab/chatgpt/evidence/2026-10-10_V3_r2_static_followup.json` and its referenced raw JUnit files. Tested source SHA256 values bind the code bytes; the successor publication handoff records the exact commit pair.

- Python 3.13.15, Torch 2.10.0+cpu, Ruff 0.12.7; installed dependencies compatible.
- 28 migration-Gate Python source files: compile, Ruff check and format check PASS; three Root launchers pass `bash -n`.
- The migration runner's complete `TEST_FILES` list with the real repository conftest: **328 passed, 3 skipped, 0 failures/errors**.
- Standalone component/monitor/prefetch/runner regression: **120 passed, 0 skipped/failures/errors**. This overlaps the migration list and must not be added to 328 as a distinct-test count.
- The three skips require real cache/source/Edge/base/VAE assets. They are unrun real-data checks, not passing gates.

Initial integrated execution exposed missing packages, read-only HOME cache locations and the nonempty fixture directory. Dependencies were installed at repository-pinned versions without changing manifests/lockfiles. Hugging Face, Matplotlib and font caches were redirected into writable workspace paths; no TLS/signature verification was disabled. The final run retained conftest, assertions and the complete requested test list.

## Repeat the read-only CPU Gate

On the existing checked-out exact pair, use its verified training Python environment, not a new worktree. Provide a new external evidence directory; preserve prior evidence. Set writable `HF_HOME`, `HF_DATASETS_CACHE`, `MPLCONFIGDIR` and `XDG_CACHE_HOME` before invocation if HOME is read-only. Add the existing venv bin directory to PATH so the runner finds Ruff 0.12.7.

```bash
python tools/v3/run_migration_cpu_gate.py \
  --root-worktree "$PWD" \
  --expected-root <exact-execution-root-from-publication-handoff> \
  --expected-child e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c \
  --evidence-dir <new-directory-outside-checkout>
```

## Remaining independent acceptance

Fresh Review is required for the changed pair. DS_PRO independently executes the CPU/static Gate, then Gates B-F for real RoboCasa source/action/state/latent/token/SequencePlan, latest complete DCP and all Resume state, workers0/2/4 numeric/throughput comparison, full-policy online Local/simulator intervention and strict 18-task screening. DS_PRO must not edit production code.

`formal_verified_index_30k` remains stopped. Latest complete DCP iteration is unknown; never assume iter800. Frozen config digest remains expected-only, not newly measured. Do not Fresh, Resume or modify DCP until all necessary independent gates pass.

## Owner/GPT decision and resumed publication

Owner pasted GPT authorization to complete the new Pair and stop additional acceptance of the old Pair. Root publication is based on `32cc72bf49385904c2e720314ea47f47f492906c`, preserving all its reviews and scoped operational history. Its H3-F quarantine permission explicitly targeted the old Pair; this follow-up does not broaden runner allowlists or automatically transfer that permission to a new Pair. A new independent Gate invocation must satisfy its own workspace prerequisites or report BLOCKED for disposition.

New author recheck logs use `/workspace/onboarding/v3-new-pair-author-check` (a fresh external directory), with tracked copies under `docs/collab/chatgpt/evidence/2026-10-10_V3_new_pair_author_check/`. Current runtime is Python 3.13.15. Earlier uncommitted local artifacts are retained as historical observations, not the new Pair acceptance record. Exact implementation SHA will be recorded by a separate docs-only Fresh Review request commit, avoiding self-referential commit hashes. The source commit and subsequent ledger HEAD must be distinguished.

Resumed author recheck completed: Ruff check/format for all 28 runner lint files PASS; measured Python syntax PASS; migration TEST_FILES 328 passed, 3 real-asset skips (113.81 seconds); runner regression 8 passed; three launcher shell syntax checks PASS. Full raw commands, source hashes, logs and JUnit are in the new tracked evidence directory. Neither the raw pytest counts nor author-check.json is independent Gate A acceptance. The runner itself is only formatted and retains its production workspace checks and fail-on-first-stage semantics.
