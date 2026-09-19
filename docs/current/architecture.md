# Current Architecture

## Scope

This document summarizes the current implemented Local Memory stage. It does not claim the later Persistent Spatial State or Action-conditioned World Model stages are complete.

```text
LIBERO RGB / robot interaction stream
              │
              ├── current observation → Cosmos3 vision/action path
              │
              └── previous causal evidence
                      │
                      ▼
               Local evidence encoder
                      │
                      ▼
                TTT fast-weight core
                      │
                      ▼
                Local Memory prefix
                      │
                      ▼
               Cosmos3-Edge MoT
                      │
                      ▼
          native Flow-Matching action objective
```

The Local branch changes the input context and learns its own slow parameters, but the outer optimization target remains the native Cosmos action-policy objective.
## Canonical training geometry

| Quantity | Current value |
|---|---:|
| `B_stream` | 8 |
| `T = ttt_tbptt_steps` | 16 |
| `K_local` | 1 |
| Local dimension | 32 |
| TTT inner LR | 0.1 |
| Fast-state dtype | fp32 |
| Consumers / native forward | 128 |
| Native forwards / optimizer update | 16 |
| Consumers / optimizer update | 2048 |

`[B_stream,T] = [8,16]` is a chronology factorization of the native consumer microbatch. `B_stream=8` is not itself the consumer batch size.

## Execution order

1. Each stable slot provides its next chronological `T=16` segment.
2. TTT scans serially along `T`; different slots are independent and execute in parallel.
3. Valid Local prefixes and consumers are flattened/gathered in the same stream-major order.
4. All 128 consumers enter one native Cosmos forward.
5. The valid-consumer weighted outer objective is backpropagated.
6. Only after successful backward are detached fast states committed for the next segment.
7. Slow gradients accumulate across 16 native microbatches before `optimizer.step()`.
## Parameter/state split

**Slow trainable state** includes the selected Cosmos generation/action heads plus the Local Memory slow groups such as the evidence encoder, TTT core parameters, Local projection and Local modality embedding.

**Runtime fast state** is slot-local `W_fast`. It is persistent across segments of the same episode, detached after each completed microbatch, not synchronized by the slow optimizer, and reset for a fresh episode.

Fresh episodes initialize from the current learned `W_bar_0`; continued segments reuse only their own previously committed detached fast state.

## Causality

The implemented route is past-only. For consumer `S_t`, the memory input is derived from earlier executed evidence; fresh `S0` is a valid consumer but has no fabricated `e_-1` Local evidence. The read happens after the corresponding fast update (`update-then-read`).

## Main implementation area

The PSM-WMA implementation is inside `cosmos-framework/cosmos_framework/model/generator/mot/` with integration in `omni_mot_model.py`, trainer callbacks, action-policy config, inference server and LIBERO client.

For the exact mathematical/runtime contract, see `../build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md` and `../build/PSM-WMA_Local_Memory_v0.3.5_active_route_member_shape_refreeze_design_v0.3.md`.