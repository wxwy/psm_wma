# DS_PRO — V3 C1 Round3: CPU-only Minimal Evidence Addendum (Parallel)

**Date:** 2026-10-11
**Implementation:** Root `444c232b976e80ac68cde9e7370e73b9f6410f0e` / Child+Gitlink `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`.
**Formal verdict pending:** `REQUEST_CHANGES` (Evidence-only only).
**Review and rationale:** `docs/collab/chatgpt/reviews/2026-10-11_V3_C1_R3_P4_evidence_review_444c232b_e9b8a41.md`.
**Goal:** Complete C1 final evidence from **existing** DCP metadata/rank JSON/logs, not by running a fifth 8×H100 load.

## Run concurrently in separate external /tmp workspaces

### E1 — RNG metadata load-source witness (CPU-only, no tensor load)

- Use the pinned trusted `iter_000000800/trainer/.metadata` in the **Shadow**; read via production DCP `FileSystemReader(...).read_metadata()` (do not deserialize tensors, read model shards, `torchrun` or initialize CUDA).
- For each rank 0..7, enumerate exact metadata keys rooted at `rng_state_{rank}`, requiring six entries: `torch`, `torch_cuda`, `numpy_packed_len`, `numpy_packed_bytes`, `random_packed_len`, `random_packed_bytes`. If metadata key structure uses nested naming, provide the literal keys and a simple documented normalization. Check tensor shape/dtype if provided, and verify no missing rank entry.
- Reuse existing successful P4 JSON/logs to report `rng_restored` and postload fingerprints and to confirm loader used `strict_resume=True`, `warm_start=False`, `trainer` key, iteration800. Explain from fixed Child `dcp.py:938-956` why all six per-rank keys plus strict successful load means `set_rand_state_dict` ran. Do not claim checkpoint-to-runtime equality by simply replaying self-generated random numbers.
- If rank-specific keys are absent, `E1_FAIL`; if unavailable due to environment, `E1_BLOCKED`. Preserve first failure. No GPU repeat.

### E2 — Four-attempt provenance / monitor scope (CPU-only)

- From original untouched `/tmp/ds_pro_v3_c1_round3/load_run.log`, `rank_{0-7}.json`, `monitor_summary.json`, source job manifests, and file timestamps, make a table for attempts 1–4 with: start/end, CWD, exception, checkpoint source realpath, load call reached? return iteration800?, first failure stage, exit status, type of harness-only change, and no production code/dataset/DCP mutation witness.
- Clearly mark that the monitor's `first_load_exception=None` refers to **attempt4 only** if that is the measured coverage; do not erase exceptions from 1–3. State which attempts are covered by the source job invariance manifests; use older P3 pre-attempt and last P4 post-attempt file identity witnesses if available, but do not invent monitoring not performed.
- The original Round3 authorization was a *single* load-only job; repeat attempts occurred. Record this **protocol deviation** openly, while separately distinguishing harmless harness startup/inspection assertion faults from real DCP/production restore failure. Do not infer that a successful attempt erases previous failures.
- If material provenance cannot be reconstructed, `E2_BLOCKED`; no request to reproduce attempts.

## Common constraints

- **No GPU use**, no new `torchrun` or `checkpointer.load()`, model/optimizer/scheduler load, forward/backward/training, original Formal30k Resume/Fresh, or source DCP writes.
- No production/test code changes. External ephemeral CPU probe solely for metadata or log parsing is permitted; DS does not push GitHub or delete any prior Evidence.
- P1/P2/P3-ISO and successful P4 Live Fast State Parity are accepted as reported; **do not rerun them**.
- Keep original Formal30k STOPPED and unchanged.

## Single handoff

Report `DS_PRO_V3_C1_R3_EVIDENCE_ADDENDUM_2026-10-11.md`:
1. `E1_PASS / FAIL / BLOCKED` with all-rank literal metadata keys and loader branch witness.
2. `E2_PASS / FAIL / BLOCKED` attempt provenance and monitor scope.
3. Formal Pair, Shadow target, exact config digest, evidence paths, original job unchanged witness.
4. Distinguish proved assertions from inferred/untested ones. Do not label overall `C1_RESTORE_PASS` until GPT evaluates this addendum.

**STOP after E1+E2**. GPT will issue the final C1 verdict and next D1 authorization as appropriate.