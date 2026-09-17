# ChatGPT formal review — ACTIVE-ROUTE-RESUME v0.4

Status: **APPROVE**

Formal pair reviewed:
- root: `53639dcbde533f642eb9560ae4d878a911b62807`
- child/Gitlink: `525f5066393cba044f00f1104b83f5eb424a9c49`
- design blob: `920f6c33a2e95b8010329d65385f0ead79e0ec75`
- Gate: `G0-R09-B-TTT-V035-ACTIVE-ROUTE-RESUME`

## Project-level judgment

Resume is a necessary correctness prerequisite for the planned long active Local-Memory run. At the current child, model/optimizer/scheduler/trainer state can advance across a checkpoint while the active Local-Memory driver/runtime otherwise rebuilds from the catalog origin. Allowing that asymmetry would silently pair an advanced optimizer with regressed Local-Memory chronology, so the current fail-closed behavior must remain until this design is implemented and proven.

v0.4 is now sufficiently specified to enter implementation. In particular it closes the earlier load-order problem by putting the DCP `dataloader` checkpoint surface on `ActiveLocalMemoryLaunchCallback`, buffering load state before `on_train_start`, and applying it only after the driver is constructed. This matches the actual DCP order (`checkpointer.load` before callback `on_train_start`) and the existing `_DataloaderWrapper` mechanism.

The runtime-state part is also now explicit enough: scheduler rebuild, owner/scheduler rebinding, sidecar frontier reconstruction, catalog/source/plan identity checks, idle-frontier requirement and round-trip object-identity evidence are all part of the design rather than being left implicit.

The snapshot pruning argument is acceptable for this Gate: at an IDLE committed frontier, the live continuation authority needed after resume is the latest committed identity per slot plus stable/terminal state; earlier admitted/committed entries are not needed to continue the next cursor. Runtime lists must remain unpruned while running; pruning is restricted to the persisted snapshot.

## Non-blocking implementation notes

These are implementation-review checks, not blockers to this design Gate:

1. When rebuilding `runtime.committed`, verify the saved sidecar identity value agrees with the canonical scheduler identity for that slot before attaching its fast state; do not use slot number alone to silently canonicalize a mismatched record.
2. The implementation tests should include `catalog_digest` mismatch explicitly, in addition to `source_digest` / `plan_chain_id` mismatch.
3. Keep the existing resume fail-closed guard operative until all design acceptance criteria, including the GPU save/kill/auto-resume continuity witness, are produced. Design approval is not evidence approval.

## Verdict

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_ACTIVE_ROUTE_RESUME`

This verdict is bound only to root `53639dcbde533f642eb9560ae4d878a911b62807` + child/Gitlink `525f5066393cba044f00f1104b83f5eb424a9c49`. It authorizes implementation of the reviewed Resume design only. Any implementation commit or Gitlink change is a new formal pair and requires fresh review before closure. It does not authorize D8b long training or Catalog Epoch Reuse.
