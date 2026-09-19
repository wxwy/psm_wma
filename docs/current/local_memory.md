# Temporal Local Memory — Current Semantics

## What the memory consumes

The first canonical Local Memory evidence uses only causal information from the past interaction stream. The frozen feature identity is `causal_visual96_executed_action10_v1`: visual summary + actually executed action. Predicted-but-not-executed action suffixes do not enter the evidence path.

Current feature identity:

- Local Memory enabled
- Local history backend: `ttt_fast_weight`
- `local_history_state_enabled = false`
- `ttt_tbptt_steps = 16`
- `ttt_inner_lr = 0.1`
- `k_local = 1`
- Local dimension = 32
- runtime fast-state dtype = fp32

## Canonical time indexing

Fresh episode:

```text
W_fast[-1] = clone(current W_bar_0)
S0          = valid Cosmos consumer, Local absent
e0 -> update W_fast[0] -> M1
e1 -> update W_fast[1] -> M2
...
e14 -> update W_fast[14] -> M15
```

Therefore the first 16-position segment has 16 valid consumers but only 15 effective TTT inner updates.
## Inner vs outer optimization

`L_inner` belongs only to the fast-state transition. It is computed independently per stream and is **not** added to the Cosmos outer loss.

The slow model is optimized through the native weighted Cosmos objective. In the current action-policy recipe the native total contains the configured vision/action Flow-Matching terms and any native auxiliary term; Local Memory changes the conditioning path rather than replacing this objective.

For a GA window, outer normalization is by valid consumers:

```text
L_window = sum(valid consumer losses) / total valid consumers in window
```

When every microbatch is full, this reduces exactly to `1 / GA` weighting per native microbatch.

## Fast-state lifecycle

- fresh episode → clone the current learned `W_bar_0`
- same episode, next segment → reuse previous committed detached `W_fast`
- no fast-state graph crosses a microbatch boundary
- slow `.grad` may accumulate across GA microbatches
- `optimizer.step()` updates slow parameters only
- episode terminal → discard old episode fast carry before the next fresh episode
- failed forward/inner/backward → candidate fast state is not published
## Stable-slot A2 packing

Each native microbatch contains one next chronological segment from every stable slot:

```text
slot 0 : t0 ... t15
slot 1 : t0 ... t15
...
slot 7 : t0 ... t15
        ↓
  [8,16] logical layout
        ↓
128 consumers in one Cosmos forward
```

Within a slot, chronology is strict. Across slots, episodes and cursor values do not need to match; synchronization means only that each native microbatch contains one next segment per stable slot.

Catalog reuse is slot-local. A slot may enter a new catalog epoch only after its current episode is terminal. The long-run readiness probe has exercised this production path through 5000 optimizer windows with no chronology or queue-replay mismatch.

## Inference

Online inference maintains fast state per session. The client sends session/episode/consumer-step identity together with causal evidence. A generated action is committed only after successful generation; reset clears the session. The server supports `local_memory_mode = auto | off | required`, making memory-off evaluation an explicit ablation.

## Authority

Detailed semantics: `../build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md`.

Stable-slot A2 override: `../build/PSM-WMA_Local_Memory_v0.3.5_active_route_member_shape_refreeze_design_v0.3.md`.