# ChatGPT re-review — R09-B TTT v0.3.2 C5A replay-evidence remediation @ eb2a583

Date: 2026-09-04

## Verdict

**REQUEST_CHANGES**

Formal Gate:
`G0-R09-B-TTT-V032-C5A-CHRONOLOGY-OWNER-SEGMENT-IMPLEMENTATION`

Formal implementation pair:
- root remediation SHA: `eb2a5839d41e1e611b5d4ea4ec5f6924c7e8425f`
- child/Gitlink: `ca4b88a7d6ed3091acc0ab5f5f97f7e6f5e5cfd2`
- request/bookkeeping SHA: `eac6c0f37da80f5d20e6867b11257d6b39a0b32c` (not the implementation target)
- frozen C5A design authority: `bbe0444eaa8c08f05ca5a5eea0e331253d263592`
- immediately preceding implementation pair: root `bfae469715566a0c82ad80a5e58f3227ab2be50a` / child `958bb20b96578acc92a6375899855a5b49274e41`

Review-start remote `V2` was `eac6c0f...`; its parent is exact implementation root `eb2a583...`. The bookkeeping SHA therefore does not replace the formal implementation target.

Scope check:
- child `958bb20... -> ca4b88a...` is exactly one tests-only commit;
- only `cosmos_framework/model/generator/mot/c5a_owner_segment_test.py` changed;
- production `c5a_owner_segment.py` is unchanged from the previously accepted validity-prefix implementation;
- root only advances SESSION/TODO and Gitlink, while the later `eac6c0f...` commit appends the review request;
- no production/runtime Cosmos wiring, config/optimizer/checkpoint/trainer/inference/parallelization, GPU/CUDA/torchrun, real model/data/cache/checkpoint I/O, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 scope drift was found.

## Closed relative to bfae469 / 958bb20

Three of the four final acceptance-tail requirements are now directly closed:
- **pending replay numerical equality**: the invalid pending replay now checks value equality against the materialized row, in addition to presence=False, shape, graph-free value and zero extra C5 write;
- **backward-failure exact rollback**: the fixture now establishes a committed owner first, snapshots fast state, `_last_timestep`, committed ReplayRecord value/shape/presence, reverse identity index and epoch, then proves failed outer backward leaves all committed state exactly unchanged and commit remains closed;
- **abort committed ReplayRecord equality**: abort now compares committed ReplayRecord value/shape/presence contents, not only key sets, alongside state/chronology/index/epoch equality;
- the previously closed validity contiguous-prefix production rule remains intact and production code is unchanged in this remediation.

No new production algorithm defect was found.

## Finding

### HIGH — the changed-byte fresh-epoch fixture still does not exercise the required same owner/source identity/timestep reuse boundary

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment_test.py` in `test_epoch_allows_same_identity_fresh_capability_and_rejects_stale()` (around lines 285-300)
- prior same-Gate review: `docs/collab/chatgpt/reviews/2026-09-04_R09_B_TTT_v032_C5A_validity_prefix_remediation_bfae469.md`

**Root cause:** the prior acceptance condition required proving that after an owner reset/epoch increment, the old epoch's `(owner, source_identity, source_timestep)` digest/replay authority does not leak into the new epoch. The same owner + same source identity + same source timestep must be reusable in the new epoch both with the same source bytes and with changed source bytes, while the stale old-epoch capability rejects before Encoder/C5.

The current test correctly proves stale epoch-0 rejection and fresh epoch-1 admission for `owner='a', source_identity='s', source_timestep=0` with the same bytes. But the changed-byte case is issued at `source_timestep=1`, not the same `source_timestep=0`. That only proves an ordinary new contiguous source in epoch 1; it does not prove that the old epoch's digest/replay entry for the exact same logical identity/timestep cannot cause stale replay/conflict when bytes differ.

**Acceptance condition:** tests-only remediation is sufficient. Add a direct fresh-runtime/reset fixture (or an equivalent separate owner transaction) where:
1. epoch 0 commits `owner='a', source_identity='s', source_timestep=0` with source bytes A;
2. reset advances owner to epoch 1 and stale epoch-0 capability rejects before Encoder/C5;
3. a fresh epoch-1 capability for the **same owner, same source_identity, same source_timestep=0** but source bytes B is admitted as a new epoch-local row, not replay/conflict;
4. zero stale committed replay/reverse-index authority from epoch 0 is observed after reset.

Retain the already-added same-byte fresh-epoch case and all current replay/rollback/validity fixtures. Re-run the isolated C5A CPU selector and report exact pass count plus py_compile and child/root diff-check.

If this exact negative/positive epoch-boundary fixture passes without exposing a production defect, no further production-code change is expected before closure review.

## Evidence note

Root status records isolated CPU pytest=`33 passed`, plus py_compile and diff-check PASS. These commands were not independently rerun in this connector environment and are treated as submitted evidence.

Still prohibited until fresh same-SHA closure:
- production/runtime Cosmos wiring;
- config/optimizer/checkpoint/trainer/inference/parallelization;
- GPU/CUDA/torchrun and real model/data/cache/checkpoint I/O;
- training/evaluation/inference;
- P4/P5, B2-T and LIBERO4IN1.
