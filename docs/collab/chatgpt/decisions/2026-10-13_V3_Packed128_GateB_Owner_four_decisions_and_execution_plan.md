# V3 Packed128 Gate B — Owner 四项最终决议及实施次序

**Date:** 2026-10-13
**Authority:** Owner explicit decisions D1=A, D2=A, D3=A, D4=A (four sequential replies in ChatGPT)
**Status:** `OWNER_DECISIONS_FROZEN / B0_IMPLEMENTATION_AND_CPU_VALIDATION_AUTHORIZED / B0_ACCEPTANCE_PENDING / B1_GPU_NOT_AUTHORIZED / MIGRATION_NOT_AUTHORIZED / FORMAL30K_HOLD`.
**Technical design:** `docs/collab/chatgpt/designs/2026-10-13_GPT_V3_Packed128_GateB_Round2_comparator_and_iter1300_migration_design.md`.
This is an **Owner decision/plan** record, **not** an implementation verdict, CPU Gate closure, GPU authorization or numerical-threshold freeze. Documentation HEAD must never be confused with the frozen implementation SHA.

## 1. Owner decisions: four items all explicitly confirmed

| Decision | Final choice | Frozen meaning |
|---|---|---|
| D1 | A — split Gate B from Gate M | Gate B validates numerical equivalence using **transient in-memory source-state adaptation only**; Gate M separately produces a valid new-layout checkpoint after Gate B succeeds |
| D2 | A — authorize Comparator Harness + isolated CPU Gate B0 | GPT builds an independent diagnostic harness and CPU negative tests; DS_PRO performs CPU-only acceptance. **No B1 GPU, production training/inference, checkpoint write or migration is authorized** |
| D3 | A — both P0 and P1 REQUIRED | P0 FIXED sigma/noise/CFG and P1 MATCHED_STOCHASTIC with matched per-consumer sigma/noise/CFG must each meet full GPU numerical parity before Gate B1 may close |
| D4 | A — Terminal Partial P0 and P1 REQUIRED | A terminal/shortened-row case must pass **real GPU** parity under both P0 and P1. CPU-only terminal tests and full-window-only GPU results are not sufficient |

Decisions D1–D4 are closed. Numeric *values* proposed in design §6 are **not** implicitly ratified by D3; Owner must freeze the specific FP32/BF16/near-zero/FQN loss and gradient criteria **before any new GPU comparison**.

## 2. Frozen paired source identities

- Original production Index8 SOURCE: Root `b159f45906f7261d028aecc226ab7f2bb9807eb9`, Child/Gitlink `937066ffd90f2bf783ad4fbb4909e9c0b8922982`.
- Standalone Packed128 TARGET: Root `c4731bca1a590663db88bd6cd74dbcf9fd513a85`, Child/Gitlink `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`.
- Full Segment Prefetch Pair Root `d45712a37318357ba2f57bde3d0f1f448aabbbd9`, Child/Gitlink `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1` is OUTSIDE B1 and remains independently CPU C0 CLOSED.
- **Only** original Index8 `iter_000001300` DCP can seed migration. Iter1400 failed save, excluded. Original DCP / latest pointer / pinned Formal30k tree immutable.

## 3. Frozen acceptance dependencies

### B0 — CPU Harness readiness (current authorized scope)

1. Commit **complete** diagnostic candidate to an isolated non-production root branch; keep production `origin/V3` Gitlink, old source and Packed128 implementation pairs unchanged. Identity must bind exact diagnostic commit, source/target SHA and module import paths.
2. CPU: `py_compile`, Ruff under repository config and scoped unit/negative tests; real 8-rank sidecar/17-field profile/schema/dual-window planner/terminal validity/collective rhythm preflight; two actual pinned source/target CPU transformed Native payload hashes if source data is accessible; immutable source DCP checksum before/after.
3. Consumer-keyed CFG scope and P0/P1 witness schema, randomness isolation and fail-closed **P1 sigma distribution unimplemented** marker explicitly covered. Proof that unauthorized `paired-run` fails closed.
4. CPU gate verdict binds **exact diagnostic SHA**, executor logs and direct contract-to-evidence. Local tests alone do not close B0; DS_PRO independent runtime acceptance and GPT review are needed.
5. No GPU, CUDA, torchrun, Nsight, real 4B/FSDP8 DCP model load, new DCP/Checkpoint writes, Formal30k mutation, migration or training.

**As-of-authoring candidate status**: An isolated ZIP `V3_GateB_B0_Comparator_CPU_Candidate_20261013.zip` exists in conversation files; local authoring container retest had `21 passed` and Python `py_compile exit0`, but Ruff was **not available** (`exit127`), and actual DS_PRO environment/full B0 has **not** run. Isolated GitHub branch `v3-gateb-comparator-b0` at `853cf9a850d62e01596cd175683e89b5cbab97ff` contains **only numeric helper**, not the full ZIP. **Do not tell DS_PRO remote B0 is ready** until exact complete candidate is pushed or otherwise reproducibly materialized with SHA.

### B1 — real 8×H100 parity (future separate Owner authorization)

Required four combinations:
- Full-window × P0 FIXED
- Full-window × P1 MATCHED_STOCHASTIC
- Terminal Partial × P0 FIXED
- Terminal Partial × P1 MATCHED_STOCHASTIC

Both legs must use identical consumer identities/valid masks, transformed payloads, Local prefix and initial fast states; site-complete matched sigma/noise/CFG witnesses. It is **not valid** to claim identical post-step global RNG streams across layouts. For each successful full GA2, Packed target must execute exactly **2 Native Forwards + 2 Backwards per rank**, once optimizer/scheduler, with **actual** terminal n<=256/rank rather than padded 256. Source Index8 rankwise native-call count must be collective-safe, or test fails closed until a reviewed rank-safe fixture exists (no silent omission of terminal rows). Compare real loss components/aux, complete optimizer-selected generation/action/local FQNs (including missing/nonfinite/near-zero), gradients, higher-order Local-TTT, four fast-state tensors, frontier/commit, optimizer deltas/moments, latency and peak memory; 2-step bounded trials with pre-registered tolerance and isolation.

P0-only, P1-only, Full-only or CPU-only outcomes **must not close B1**. OOM/NCCL/not reproducible => FAIL/BLOCKED, not automatic batch downshift or threshold relaxation. Old V2 ~2.4% gradient figure is historical only, not B1 tolerance authority.

### Gate M — explicit source→target checkpoint migration (only after B1 PASS and new Owner authorization)

- Source sidecar and model/optim/scheduler/trainer verified under old authority; 8 ranks.
- Target config_digest recomputed **honestly** from Packed128 native layout; old digest retained as source lineage. Strict sidecar top-level exact 10 keys unchanged; deep-clone, update only its top-level config_digest **and each active `SegmentProvenance.config_digest`**. External `MIGRATION_MANIFEST.json` records immutable old/new SHA and digest identities. Other identity/frontier/scheduler/fp32 fast-state bytes/values preserved.
- Create a valid target DCP through verified official APIs in **new isolated temp namespace**, validate all components and actual 8-rank strict load, atomic rename only on PASS. Old DCP/latest/worktree remain byte-for-byte intact.
- Verify new namespace ordinary Strict Resume from iter1300, first **iteration1301**, then valid checkpoint and another strict resume. **Do not** claim changed layout yields bitwise same RNG consumption as historical Index8.

### Formal30k — final, separately authorized

- Only after B1 and M passed, Owner manually starts from iter1301 in the target namespace. Default initial formal route: Packed128 base + legacy global RNG + `nw=0`; do not concurrently enable Consumer-keyed RNG or Full Segment Prefetch.
- Inspect first checkpoint, data/frontier/RNG state, tensor/gradient/loss norms, wall time, peak VRAM and correctness signals.
- Full prefetch GPU throughput/causal Nsight stall trace remain **separately approved, non-critical-path** optimizations.

## 4. Owners, artifacts and stop rules

- **Owner**: four decisions confirmed; later specific GPU, migration and formal training authorizations retained.
- **GPT**: design, isolated B0 candidate/handoff and fresh evidence review; any B0 fix must be reviewed under new exact SHA, no inherited verdict.
- **DS_PRO**: validation-only, CPU Gate B0 execution on isolated pinned code, evidence report and no production code changes. Later B1 runs only after Owner authorization.
- Next deliverables, in order: (i) complete B0 branch package and lint/test; (ii) DS_PRO CPU acceptance report and GPT closure; (iii) Owner freeze numeric thresholds + B1 harness review; (iv) Owner-authorized 8×H100 four-combination GPU; (v) Owner-authorized migration, then formal resume.
- If any required proof is unavailable, report `BLOCKED`, retain first failing command/stack/source SHA, do not automatically skip, enlarge scope, edit source DCP or silently claim Gate success.

**Current authorization remains CPU-only B0.** This Owner record is docs-only and must not change formal implementation SHA/Gitlink.
