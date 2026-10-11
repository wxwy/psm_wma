# PSM-WMA V3 C1 Round3 — 8×H100 Strict Shadow DCP Load-only Evidence Review

**Date:** 2026-10-11
**Formal verdict:** `REQUEST_CHANGES` (**Evidence-only**; targeted CPU addendum; NO repeat GPU Run).
**Exact Implementation Root:** `444c232b976e80ac68cde9e7370e73b9f6410f0e`
**Child/Gitlink:** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`
**Status:** `C1_SHADOW_LOAD_TECHNICAL_PASS_REPORTED / C1_RNG_METADATA_EVIDENCE_OPEN / C1_ATTEMPT_LEDGER_OPEN / C1_FORMAL_NOT_CLOSED / D1_E_F_HOLD / FORMAL30K_STOPPED`

## Frozen authority and source boundary

- Execution authority: `docs/collab/chatgpt/reviews/2026-10-11_V3_C1_round3_8xH100_strict_shadow_load_only_authorization_444c232b_e9b8a41.md` (only one 8-rank load-only job; fail-closed and preserve first exception).
- Prior C1 P1/P2/P3-ISO closure: `docs/collab/chatgpt/reviews/2026-10-11_V3_C1_round2_P1_P2_P3ISO_evidence_closure_444c232b_e9b8a41.md`.
- DS_PRO user-relayed report: `docs/collab/chatgpt/evidence/2026-10-11_V3_C1_R3/DS_PRO_2026-10-11_C1_round3_P4_owner_relay_summary.md`. The raw `/tmp` harness, logs and JSON on the training host remain inaccessible to GPT. DS reports a successful fourth load attempt, not the first.
- Formal Pair unchanged; no repeated full technical review. GitHub V3 documentation HEAD is not the implementation Root.

## Established, limited behavioral disposition

The DS report strongly supports successful **8/8 strict distributed DCP load from the separate Shadow**: `source.warm_start=False`, all five components loaded, iteration 800, FSDP2 Optimizer flattened state inventory 2826/2826, disabled GradScaler empty state, Scheduler epoch800, complete rank Sidecars and actual `restore_grouped_local_state`. Per-rank GPU Local Live State/next GA member plan matched independent CPU P2 `n_diffs=0`. Source Formal30k manifest reported unchanged. Thus **no evidenced Model/Optimizer/Local checkpoint bug**, and no reason to rerun this expensive successful Load-only.

This is **not yet** a formal `C1_RESTORE_PASS` for the two reasons below.

## Finding C1-R3-F1 — RNG checkpoint-source witness missing

- **Severity:** HIGH (Evidence-only; may become production/asset blocker only if metadata missing).
- **Evidence:** `docs/collab/chatgpt/evidence/2026-10-11_V3_C1_R3/DS_PRO_2026-10-11_C1_round3_P4_owner_relay_summary.md`, section "Explicit limits" #1; pinned Child `cosmos_framework/checkpoint/dcp.py:930-956`; `cosmos_framework/checkpoint/dcp.py:1224-1244` writer, and `cosmos_framework/utils/generator/rand_state.py:10-38` state layout.
- **Root cause:** Production Checkpointer reads `trainer/.metadata`, checks presence of `rng_state_{rank}`, and **silently does not call `set_rand_state_dict` when it is absent**. The reported `changed=True` between before/after and `replay_deterministic=True` from a newly captured postload state cannot by themselves establish that iter800 checkpoint RNG bytes were loaded. Even an arbitrary postload RNG state is replayable.
- **Frozen contract:** Requires each rank's RNG restored, not merely deterministic self-replay; actual GPU C1 Gate's authorization expressly disallows treating silent RNG absence as strict PASS.
- **Minimal acceptance:** Read only existing trusted **Shadow** (or original read-only) `trainer/.metadata` using `FileSystemReader.read_metadata()` on CPU, verify for **each rank 0..7** `rng_state_{rank}` has exactly the six expected fields: `torch`, `torch_cuda`, `numpy_packed_len`, `numpy_packed_bytes`, `random_packed_len`, `random_packed_bytes`. Record keys/count/dtype/shape as available and corresponding preexisting P4 `rank_{rank}.json` restored fingerprints/logs. Confirm actual production loader on fixed Child takes the `rng_key_exists=True` branch when these keys are present; since successful 8-rank strict load was already observed, this supplies the missing load-source witness. **Do not rerun GPU Load, RNG replay or full model.** Missing keys => true `FAIL`, not report PASS.

## Finding C1-R3-F2 — execution attempt scope and monitor attribution

- **Severity:** MEDIUM (execution/Evidence provenance; no production implementation bug alleged).
- **Evidence:** `docs/collab/chatgpt/evidence/2026-10-11_V3_C1_R3/DS_PRO_2026-10-11_C1_round3_P4_owner_relay_summary.md`, "P4 Harness execution chronology"; round3 authority states "single job/one round", preserve first failure and stop, not retry on DCP errors.
- **Root cause:** Report has four separate 8-rank harness invocations (attempt1 CWD FileNotFoundError, attempt2 optimizer schema false-negative, attempt3 GradScaler disabled schema false-negative, attempt4 success). The monitor's `first_load_exception=None` and its ~260.6s sampling window cannot unqualifiedly describe all attempts. This departed from the one-invocation protocol even though attempts2/3 are reported to have genuinely restored DCP and there was no actual strict-load failure.
- **Minimal acceptance:** Extract **existing** attempt-by-attempt start/end, exit stage, first exception, whether `checkpointer.load()` returned iteration800, which path was used (Shadow vs original), and whether original Formal30k was read-only throughout; explicitly attribute monitor/unchanged-manifest evidence to the run(s) it observed. Document exception to single-attempt authorization; no reset/clean, no new GPU run, no retrospective rewrite of earlier logs. An honest evidence addendum resolves the ambiguity; this procedural deviation must remain in the ledger rather than being called a single pristine first attempt.

## Nonblocking disclosures

- Optimizer 2826/2826 flattened keys + successful real strict `dcp.load` is stronger than a helper-only count test, but the summary does not show individual tensor-to-DCP value fingerprints. Do not invent per-tensor bitwise compare.
- `Model` test only explicitly probes 6 finite changed tensors; native `ModelWrapper.load_state_dict` raises on missing/unexpected keys, and DS reports no exception. Exact per-parameter equality not separately measured.
- P4-MONITOR's global device-used peak (52–54GiB) includes external robotwin_server baseline (~46GiB), not per-rank `torch.cuda.max_memory_allocated/reserved`. If existing rank JSON has local statistics, add them; absent telemetry is not by itself a reason for a new GPU load.
- Source Formal30k was reportedly unchanged; successful Shadow load does NOT authorize Original Formal30k Resume, D1 GPU numeric parity, forward, backward or any optimizer step.

## Next independent authorized work

**Two minimal CPU-only tasks may run in parallel**, no intermediate GPT review:
- `C1-R3-E1` Checkpoint `trainer/.metadata` RNG-key witness on all ranks.
- `C1-R3-E2` Four-attempt log/monitor chronology and original file identity reconciliation, including 8-rank successes and first exceptions.

See `docs/collab/chatgpt/reviews/2026-10-11_V3_C1_R3_minimal_CPU_evidence_addendum_authorization_444c232b_e9b8a41.md`. No GPU/torchrun, original DCP mutation, actual model reload, D1/E/F/Fresh/Resume, or production code modification. If E1/E2 support the DS report, GPT can close `C1_RESTORE_PASS` **without another GPU test**. If a real key/state mismatch emerges, fail closed.

This Evidence review is submitted to `docs/collab/chatgpt/reviews/`; the canonical Inbox append makes it the formal current verdict for the same implementation pair.