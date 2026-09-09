# ChatGPT 独立 runtime-owner / sidecar design v0.8.4 review

Formal reviewed pair:
- root design SHA: `9e3e8714005d5758e06f031274753e5529f6c793`
- child/Gitlink SHA: `5d16b84fe17a42f128065bf36361f6b1bb93a436`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-WIRING-RUNTIME-SIDECAR-DESIGN`
- request/bookkeeping HEAD observed at review start: `9a70060aeb12383d0bbaf80e87827ebc42fefccc`

Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh incremental review relative to prior formal design pair `f2face62e51c4aef89dff6085fd87bb5441a612b` / `5d16b84fe17a42f128065bf36361f6b1bb93a436`. Child is unchanged. v0.8.4 is a docs-only remediation for the prior ChatGPT SCALER_SKIP lifecycle HIGH and abort-preflight MEDIUM. Review is based only on the Codex canonical request, v0.8.4 plus inherited v0.8-v0.8.3 contracts, the prior ChatGPT review, and the formal child source.

## Prior blocker status

1. **CLOSED — abort preflight now protects negative cases from partial mutation.** v0.8.4 requires exact owner phase/current transaction/current forward/adapter pending tuple validation before any transaction, owner, scheduler, sidecar or pending mutation. Substitute/stale/cleared pending cases are explicitly required to preserve owner/transaction/scheduler/pending/committed snapshots byte-for-byte/value-for-value. This closes the prior MEDIUM for the specified negative cases.

2. **PARTIALLY CLOSED — SCALER_SKIP is no longer a permanent owner terminal.** v0.8.4 correctly separates scaler skip from true terminal `ABORTED` and intends to return the owner to a reusable state. However, the retained scheduler admission frontier is not reconciled with the committed sidecar frontier, leaving the skip path unrealizable; see current blocker.

## Current blocker

1. **HIGH — `SCALER_SKIP -> IDLE -> fresh scheduler.admit()` advances scheduler chronology past the uncommitted skipped identity, while sidecar chronology remains at the previous committed identity.** `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.8.4.md:16-29,52-56`; `cosmos_framework/model/generator/mot/local_memory_segment.py:293-318`; `cosmos_framework/model/generator/mot/local_memory_segment_adapter.py:24-41,55-68`.

   In the formal child, `RankLocalSegmentScheduler.admit()` is not a read-only reservation: it immediately appends the chosen identity to `admission_order` and assigns `stable_slots[slot] = chosen`. Its next admission for that slot must therefore be the same episode/source/category with `cursor == previous.cursor + 1`.

   The sidecar advances on a different authority: it writes only after successful trainer transaction + adapter commit. `LocalMemorySegmentSidecar.read(identity)` accepts continuation only when the requested identity has `cursor == previous_committed.cursor + 1` relative to the stored sidecar record.

   v0.8.4 freezes scaler skip as: exact-discard pending, call `transaction.grad_scaler_skip()`, clear owner transaction/forward/admitted/retry handles, return to `IDLE`, do **not** call `scheduler.commit()` or alter scheduler, then start the next window via a **new** `scheduler.admit()`. Suppose sidecar is committed at cursor `k` and cursor `k+1` is admitted/prepared then scaler-skipped. Scheduler `stable_slots` remains at uncommitted `k+1`, while sidecar remains at committed `k`. A fresh scheduler admission must choose `k+2`, but sidecar read for `k+2` rejects because it requires `k+1`. Thus the required CPU/static acceptance “skip -> fresh admit/begin/prepare and read prior committed frontier” cannot be satisfied with the frozen child APIs and whitelist.

   The same split makes the claimed immediate post-skip snapshot impossible under the inherited committed-frontier guard: sidecar’s latest slot record is identity `k`, while scheduler `stable_slots[slot]` is the uncommitted skipped identity `k+1`, so the required sidecar/scheduler frontier equality fails.

   **Acceptance:** freeze one coherent authority for the admitted-but-uncommitted skipped identity without modifying scheduler source. The simplest compatible design is to retain the exact skipped `SegmentIdentity` after clearing the old transaction/forward/pending, and let the next fresh transaction/window **reuse that already-admitted identity without calling `scheduler.admit()` again**, analogous to the retry first-member authority but without converting it to attempt-1 recovery. Only after that identity successfully commits may later identities use normal `admit(next)`. Alternatively, explicitly authorize and design a scheduler rollback helper, but that would expand the current whitelist/scheduler contract and needs its own precise semantics. In either case, define whether immediate post-skip snapshot is legal; if scheduler and sidecar frontiers intentionally differ until the skipped identity is resolved, snapshot must remain fail-closed until they reconverge. Add CPU/static Evidence for committed cursor `k` -> admit `k+1` -> scaler skip -> no duplicate admission -> reuse/resolve exact `k+1` -> sidecar read from committed `k` -> commit -> normal `k+2`, plus snapshot negative/positive boundaries matching the chosen contract.

## Scope boundary

No runtime-owner CPU/static implementation authority is granted for this pair. This remains docs-only. No production model/trainer/packer wiring, persistent sidecar/checkpoint I/O, config/default/registry changes, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T, or LIBERO4IN1 is authorized.
