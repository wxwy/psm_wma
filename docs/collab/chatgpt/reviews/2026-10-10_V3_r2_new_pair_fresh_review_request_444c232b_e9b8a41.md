# GPT Fresh Review request — V3 r2 CPU/static follow-up

Date: 2026-10-10 (Asia/Shanghai). Author: Codex.
Status: **REVIEW_REQUEST_ONLY / NO_GPT_VERDICT / NOT_GATE_A_ACCEPTANCE / RESUME_HOLD**.
This document is an implementation-author request, not a ChatGPT review conclusion.

## Exact Formal Pair

- Root Implementation: `444c232b976e80ac68cde9e7370e73b9f6410f0e`.
- Child and Gitlink: `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`.
- Root parent: `32cc72bf49385904c2e720314ea47f47f492906c`; preserved unchanged in ancestry, including its operational review record.
- Previous Pair: `cf0c92731197bfdd0de073a4c07ca93194f58968` / `d41be4f5485dcd9321318840c8c278c1f7487924`. Owner/GPT instructed stopping additional acceptance of this old Pair.
- Any later docs-only V3 HEAD records this request; it must not replace the above Root Implementation SHA.

## Problem and resulting behavior

The Evaluation Identity test used the repository tmp_path as its output directory. Repository conftest creates log files there, triggering production's correct empty-output rejection. The test now owns tmp_path/evaluation, preserving same-identity resume, different seed/horizon rejection, existing-run rejection and the separate legacy-output rejection test. Production fail-closed behavior is unchanged.

Root's other four Python modifications normalize imports/format only; their non-import AST matches the parent. Child's 19 modified Python files likewise retain the prior d41be4f non-import AST. Child removes an unused imageio import and fixes ordering/formatting; no Local-TTT math, policy loss, checkpoint format, optimizer/scheduler or frozen configuration behavior is changed. Runner allowlists and failure semantics are unchanged. Diff scope is authoritative from git diff-tree on the implementation commits.

## Evidence and limits

Design/author record: docs/build/PSM-WMA_V3_r2_static_followup_2026-10-10.md.
New author evidence: docs/collab/chatgpt/evidence/2026-10-10_V3_new_pair_author_check/.
- author-check.json: exact source hashes, commands and stage exits.
- ruff_check.log and ruff_format.log: Ruff 0.12.7, all 28 runner-defined lint files PASS.
- runner_pytest.log/xml: 8 passed.
- pytest.log/xml: full migration TEST_FILES with repository conftest, 328 passed, 3 skipped, 0 failures/errors (113.81 seconds).
- bash_0/1/2.log: all three runner launchers pass bash -n.
- verify-v3-new-pair.py.txt: exact executed author-check harness.

The three skips require real cache/source/model/VAE assets. These author checks do not establish independent DS Gate A, GPU/real-data correctness, DCP strict Resume consistency, throughput or simulation success. Writable HF/Matplotlib/XDG caches were used; no dependency manifest or frozen config was altered. Config digest remains expected-only: `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`.

## Requested GPT decision

Fresh Review is required because the Formal Pair changed. Please return APPROVE or REQUEST_CHANGES with complete pair binding in a separate signed/attributed review record. Scope: review the source/test/static follow-up and decide whether to authorize DS_PRO read-only Gate A for this new Pair. Please also decide the new-Pair disposition of any historical untracked scripts/plot_h3f_monitor.py: the 32cc72bf permission explicitly targeted the old Pair and is not automatically transferred. Do not bypass the runner if workspace checks fail.

After GPT authorization, DS should safely pin this exact Pair in an existing independent validation workspace, preserve dirty training directories and all historical evidence, use existing Python/Ruff, and execute with a NEW external evidence directory:

```bash
python tools/v3/run_migration_cpu_gate.py \
  --root-worktree "<EXACT_ROOT_WORKTREE>" \
  --expected-root 444c232b976e80ac68cde9e7370e73b9f6410f0e \
  --expected-child e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c \
  --evidence-dir "<NEW_EXTERNAL_EVIDENCE_DIR>"
```

Use writable HF_HOME/HF_DATASETS_CACHE/MPLCONFIGDIR/XDG_CACHE_HOME if needed. Return gate.json, Ruff/pytest logs/JUnit, commands and first failure unchanged; no production edits or installation by DS. Gate A GREEN authorizes reporting and waiting for the next Gate only. Gates B-F require their own authorization/evidence. No GPU, Fresh, Resume or formal DCP access in this handoff. Job formal_verified_index_30k stays stopped; latest complete DCP iteration is unverified.
