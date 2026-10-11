# PSM-WMA V3 — C1 FINAL Strict Shadow Same-job Restore Evidence Closure

**Date:** 2026-10-11
**Formal verdict:** `C1_RESTORE_PASS / C1_CLOSED`（Owner-relayed DS_PRO evidence + independent pinned code cross-check; no GPT rerun）
**Formal Root Implementation:** `444c232b976e80ac68cde9e7370e73b9f6410f0e`
**Child/Gitlink:** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`
**Current post-Gate:** `D1_OPEN_FOR_CPU_READINESS_ONLY / D1_GPU_HOLD / E_F_HOLD / FORMAL30K_STOPPED`

## Evidence authority and previous conditions

- Frozen C1 authorization: `docs/collab/chatgpt/reviews/2026-10-11_V3_C1_round3_8xH100_strict_shadow_load_only_authorization_444c232b_e9b8a41.md`.
- Round2 CPU/Shadow readiness closure: `docs/collab/chatgpt/reviews/2026-10-11_V3_C1_round2_P1_P2_P3ISO_evidence_closure_444c232b_e9b8a41.md`.
- R3 first review: `docs/collab/chatgpt/reviews/2026-10-11_V3_C1_R3_P4_evidence_review_444c232b_e9b8a41.md`, which held final PASS for RNG-origin and multiattempt provenance.
- Owner-relayed R3 successful GPU load report: `docs/collab/chatgpt/evidence/2026-10-11_V3_C1_R3/DS_PRO_2026-10-11_C1_round3_P4_owner_relay_summary.md`.
- New E1/E2 source record: `docs/collab/chatgpt/evidence/2026-10-11_V3_C1_R3/DS_PRO_2026-10-11_C1_E1_RNG_E2_attempts_owner_relay.md`. Raw DS GPU/CPU log/JSON files remain on the training host, not inspected directly by GPT. No new code/implementation pair was proposed; **no repeated general code/design review**.

## Final E1 — RNG source / metadata: PASS

DS used the actual production `FileSystemReader.read_metadata()` against Shadow iter800 `trainer/.metadata` and enumerated **49 keys**, `iteration` + `rng_state_{0..7}` × six (48/48). Keys are exactly the six expected `torch,torch_cuda,numpy_packed_len,numpy_packed_bytes,random_packed_len,random_packed_bytes` for every rank; metadata dtype is reported, while shapes are explicitly code-defined rather than falsely described as actual metadata shape.

GPT independently checked fixed Child `cosmos_framework/checkpoint/dcp.py:930-955` and `cosmos_framework/utils/generator/rand_state.py:11-47`. `dcp.py` constructs the `rng_state_{dist.get_rank()}` key, checks metadata for that prefix, and if present inserts RNG state into strict DCP load and calls `set_rand_state_dict` on the loaded state. On the reported trusted same-job Shadow target, **eight matching metadata groups + successful strict 8-rank DCP load + postload RNG change/replay evidence** close the previously missing causal source witness. It is not the weaker inference from self-replay alone.

**E1 verdict `PASS`.** No need for a fifth 8×H100 test; no original Formal30k DCP read/write needed.

## Final E2 — Attempt provenance: RECONCILED with permanent protocol deviation

DS identifies **four** launched torchrun harness attempts, with timestamps, failure stage, exit status and causal attribution:
- A1 wrong CWD / relative model JSON FileNotFoundError **before load**.
- A2 real strict DCP load succeeded but external test assertion misread FSDP2 flattened optimizer state.
- A3 real strict DCP load succeeded but external test assertion incorrectly required nonempty disabled GradScaler state.
- A4 load and all registered verification checks passed 8/8.

The success monitor's `first_load_exception=None`, output files and complete GPU samples belong to A4 only. A1–A3 original full logs were overwritten or only exist as partial session notes: don't invent full attribution or continuous source invariant monitoring for every attempt. DS's account is compatible with the actual pinned production optimizer/scaler interfaces; there is no evidenced production bug or strict DCP load error.

**Important violation not waived:** A1–A4 departed from the owner's one-load invocation authorization. Archive under **`C1-R3-PROTOCOL-DEVIATION: FOUR_GPU_ATTEMPTS_INSTEAD_OF_ONE; EARLIER_LOGS_NOT_PERSISTED`**. Do not rewrite history as a single pristine run. This deviation remains an execution discipline item for DS_PRO; require fail-stop and new explicit owner authorization after future GPU/test-harness errors. The deviation does not falsify the independently identified successful A4 loading from Shadow, and is therefore **nonblocking to technical C1 closure**, but is not treated as compliant execution.

**E2 verdict `RECONCILED_WITH_DEVIATION`.**

## C1 accepted technical evidence (exactly bounded)

P4 final report + E1/E2 addendum support:
- Root/Child/Gitlink frozen pair, production complete config digest `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`, real iter800 file identity.
- **Eight-rank, actual 8×H100 FSDP2 DCP load** via the separate immutable-copied Shadow job, Checkpointer reports `warm_start=False`, all five components `model,optim,scheduler,trainer,dataloader`, iteration800, no missing/unexpected model keys reported.
- Real FSDP2 flattened Optimizer state keys 2826/2826 against DCP metadata, finite; Scheduler `last_epoch=800`, disabled GradScaler has correct empty state.
- Rank-specific RNG state loading branch now established for all eight ranks.
- 8 Sidecar pending states converted into actual GPU `GroupedLocalMemoryWindow.live` via pinned `restore_grouped_local_state`; fast state four tensor fingerprints, source/corpus/config identities, scheduler, frontier, first future GA window **all match P2 CPU witness across eight ranks** (`n_diffs=0`).
- Original Formal30k source job remained STOPPED, reported manifest before/after 232 entries identical in recorded check scope; separate Shadow path permitted Trainer constructor config writes without overwriting the source.

**Limitations retained:** Evidence is DS executed/owner-relayed rather than GPT direct replay of 8-rank raw JSON; large model/optimizer tensors not individually compared to raw DCP bytes, though production strict DCP loading succeeded. This was **Load-only**: no model loss, gradients, optimizer update, continuation benchmark, robot policy/Simulator results. Global GPU used-peak includes external robotwin_server and is not per-rank allocated/reserved measurement. Do not claim iter801 numerical continuity or training readiness solely from C1.

## Formal disposition and next authority

**Close `C1_RESTORE_PASS / C1_CLOSED` for frozen Formal Pair and iter800 Shadow same-job Load-only.** Supersede the prior **Evidence-only** `REQUEST_CHANGES` from R3; do not repeat C0/Batch1/C1 or add GPU as a paperwork exercise.

**D1 Round1 CPU readiness only** authorized in `docs/collab/chatgpt/reviews/2026-10-11_V3_D1_round1_parallel_CPU_readiness_authorization_444c232b_e9b8a41.md`. D1 actual GPU forward/backward/optimizer microstep **not yet authorized**, because full comparative control and resource coexistence contract must be frozen first. E/F, original Formal30k Fresh/Resume, DCP mutation and production code editing all remain HOLD. If D1 requires a different implementation pair, formal technical re-review must occur before execution; a newer docs-only V3 HEAD does not change this verdict.