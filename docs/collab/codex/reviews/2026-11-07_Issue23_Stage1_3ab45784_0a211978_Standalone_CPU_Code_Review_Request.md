# Issue23 Stage1 — standalone shared VAE Worker: code review request

Date: 2026-11-07 Asia/Shanghai. Request independent GPT `APPROVE_CODE` or
`REQUEST_CHANGES` **for standalone Stage1 only**. No independent verdict claimed.

## Exact implementation target

| Object | Full SHA |
| --- | --- |
| Formal standalone CPU Root | `3ab4578475d8df5ce93b7bde6c4f2073a46f777e` |
| Child / candidate Gitlink | `0a2119782fb5078fee3359f9ef7383d788744458` |
| Approved Stage0 Child / incremental review base | `8a170d56014af937b146b35e2b89753313614785` |
| Official Child baseline | `1ca308055fc41fb69efaeb9efaa23808f164a18e` |

Independent Root/Child branch: `v3-sim-shared-vae-issue23-stage1-20261107`.
Stage0 approval is in Root formal review `5c66ea37` and canonical ledger77f130bb,
plus direct Owner Stage1 authorization. Child has two implementation commits:
f64a0396 (standalone implementation), 0a211978 (one test-fixture correction).
Root supporting evidence/Inbox successors are bookkeeping, not new test targets.

[Exact incremental Child diff](https://github.com/wxwy/cosmos-framework/compare/8a170d56014af937b146b35e2b89753313614785...0a2119782fb5078fee3359f9ef7383d788744458):
four new modules, four test files and one Stage1 README, +4497 lines. All nine
paths are additions. No existing Policy/LocalMemory/model/training/test/config
files or approved Stage0 documents changed. Root production source is unchanged;
only isolated candidate Gitlink and docs/ledgers changed. This is a standalone
CPU Pair, **not integrated EvalV2 deployment**. Official V3 is not updated.
Latest official V3 observed at publication30380d74806aa02173ab2dc52f17eef7cc2f1fdb
still binds Child1ca30805; interim commits are G2 docs owned by the other line.
PR4 and design PR5 branches are unchanged.

## Implementation

New files under `cosmos_framework/inference/`:

- `robocasa_vae_protocol.py`: copied immutable Frame, strict bounded JSON and
  full public Lease, canonical RGB/action/feature digest, finite f32 and HMAC.
  Receipt verification is explicitly stateless; it cannot prove env.step or
  replace enrollment/causal/revocation checks. Typed uncertain-drain failure.
- `robocasa_vae_worker.py`: one serialized encoder owner, independently configured
  B1/4/8 and wait0/2/5 (B1=0); READY-origin window, full/early-deadline dispatch,
  across-batch Session fairness; original budgets; bounded queued/active/retained
  items, bytes, chunks, tombstones, Slots, retired Sessions and trace ring.
  Exact retries/changed bytes, mock-issued/completed ranges, ordered consume,
  concurrent End, retained errors, sticky quarantine and late-result rejection.
- `robocasa_vae_client.py`: independent bounded Unix data/control lanes, separate
  local Owner capability, original absolute RPC deadlines, no pickle. Session
  credentials cannot enroll/advance completion. Tracks live handlers through
  real exit; owned-inode cleanup, startup rollback and first-error retention.
- `robocasa_vae_encoder.py`: lazy numeric imports; already-loaded frozen BF16
  tokenizer injection; pure preprocessing and full pre-crop Visual96 helper;
  B-axis-only T1 batching; explicit eager/B1-AOT identity. No loading or compiling.
  CUDA error is conservatively unproven drain; CPU tests use a fake device label.

Worker traces include READY/dispatch/encode/result/ACK/End ns and batch histogram;
these are CPU control traces, not complete P0 or GPU profiling evidence.
The runbook is `docs/designs/issue23_sim_shared_vae_stage1/README.md` in Child.

## Exact-Pair author CPU evidence

Evidence root: `docs/collab/codex/evidence/2026-11-07_issue23_stage1/`.
Raw JUnit, logs, environment/versions, before/after source hashes, source identity
and safe actual subprocess lifecycle record are retained. Runner is archived as
`run_cpu_gate.py.txt`, SHA256
`bdf0651e70aec1d063a7b08a3ce63d8342cfb9112036d254d49a3257d84d097b`.

Command, cwd `/workspace/work/psm-wma-sim-shared-vae-issue23`:

```bash
/workspace/.venvs/psm-wma-cpu/bin/python \
  /workspace/work/issue23-stage1-evidence/run_cpu_gate.py \
  --root /workspace/work/psm-wma-sim-shared-vae-issue23 \
  --expected-root 3ab4578475d8df5ce93b7bde6c4f2073a46f777e \
  --expected-child 0a2119782fb5078fee3359f9ef7383d788744458 \
  --evidence-dir /workspace/work/issue23-stage1-evidence/author-02
```

Python3.12.14 / Torch2.10.0+cpu / Pytest9.0.2 / Ruff0.12.7. GPU hidden, model
network disabled, plugin autoload disabled and numeric threads1; exact overrides
are archived. No real checkpoint/data/model/GPU/Sim was accessed. Both worktrees
were clean and Root Gitlink matched Child when execution began.

**PASS: Shell exit0; gate.status=PASS; source_unchanged=true.** Ruff check and
format pass. New standalone pytest: **173 tests +185 passing subtests**; selected
legacy protection: **74 tests**. JUnit counts subtests as testcases:358 new +74
legacy =432 rows; do not call these432 independent top-level tests. There are
247 top-level tests,185 subtests, zero failure/error/skip. This is a focused CPU
Gate, not the historical complete EvalV2/Streaming/DS Gate.

Legacy74 cover existing Session transactions, No-TTT/Local-TTT dual mode, online
memory and composite preprocessing. Actual subprocess tests cover signed round
trip/retry/ACK/End, blocked encoder with responsive control, encoder error,
null credential rejection, crash/restart epoch rejection, external dummy process
survival during owned cleanup, and zero exit/full IPC quiescence. The independent
dummy process is then reaped by its own test fixture. No server or running-job
inspection was performed.

First attempt is preserved in `author-01/`: Root4495399d/Childf64a0396,
172 pass/1 fail (+185 subtests), legacy NOT_RUN, source unchanged. Its only failure
was the public-directory permission fixture: inherited umask0077 turned requested
mkdir0755 into actual0700. The fix explicitly chmods/asserts0755, preserving the
production rejection logic. Final Pair reruns all173 new cases and legacy74;
earlier FAIL is not overwritten or reclassified.

## Open boundaries and next decision

All real Wan BF16 parity, GPU/EGL, RoboCasa, latency/throughput/SR are NOT_RUN.
Stage1's CPU golden math and fake encoder are not real-model evidence. Signing
key/actual-loaded VAE attestation, trusted Sim execution and OS isolation require
their later Gates; HMAC alone does not establish causality.

Policy-owned boundary capture/reuse remains NOT_IMPLEMENTED, independently from
PR4. Current standalone Worker expects contiguous encoder source ranges; Stage3
must separately authorize15-frame subranges while preserving actual source steps
1..15/17..31 and Policy-owned0/16 boundaries. No extra boundary Encode1, implicit
skip or source renumbering is allowed. This limitation is explicit, not claimed
as completed15+1 integration. Policy B1 actual peer-wait proof and READY Policy
scheduling, FastState transaction integration and complete P0 traces are also
Stage3 work. M/B Resume strictness and existing off/required validation unchanged.

Please review the new exact code increment and raw CPU evidence. An approval
closes standalone Stage1 code only; it does not authorize GPU, production Action
Path, a real checkpoint, training, PR/V3 merge, official Gitlink changes, existing
run operations or a larger SR study. Stage2 real Wan/EGL needs a separate Owner
Gate; P0 A/B/C latency/SR and multi throughput remain separate future conclusions.
