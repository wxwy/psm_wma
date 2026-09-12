# ChatGPT Review — Authority Root PASS Linearization Design v0.9

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-PASS-LINEARIZATION-DESIGN`

## Exact formal pair

- root design SHA: `a98e82714940d7bed1969cafb2ef32100c287d59`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_pass_linearization_design_v0.9.md`

The formal root is reachable (`docs: refine authority pass terminal state`). Its exact tree was independently checked: `cosmos-framework` is mode `160000`, type `commit`, exact child `93a89ba61306d840a008813f62f26a34d54850f4`. The child commit is independently reachable in `wxwy/cosmos-framework`.

## Review basis

Fresh incremental review against:

- approved authority-root design chain v0.3-v0.6;
- v0.7/v0.8 PASS-linearization design chain;
- prior ChatGPT v0.8 review `0ad5fb3379456f485fd861595e3db4ab62c3555f / 93a89ba...`, which reported three HIGH findings: terminal-state indivisibility, guard/crash-window semantics, and ref-witness semantics;
- exact v0.9 text.

## Prior blocker closure status

### v0.8 HIGH-1 — multiple semantic state writes: CLOSED

v0.9 collapses acceptance/rollback/preserve/witness-return semantics onto one authority-owned terminal-state cell and makes all public properties derived from that single state. The design explicitly removes independent mutable `committed/issued/consumed` fields and defines one semantic pointer transition from PENDING to ACCEPTED. This closes the previous split-brain design class, provided implementation preserves one shared holder/cell as specified.

### v0.8 HIGH-2 — guard/crash B window missing: CLOSED

v0.9 explicitly supersedes the previous guard ordering, makes guard transition the final fallible pre-state action, and freezes A/B/C crash windows. In particular, the previously missing durable state `guard absent + final evidence present + terminal still PENDING` is now window B and is permanent fail-stop after restart. B/C are intentionally indistinguishable from pathname evidence and both require a future manual recovery design. That is a valid fail-closed choice.

### v0.8 HIGH-3 — ref witness semantics: PARTIALLY CLOSED

v0.9 correctly chooses the weaker, honest **observation-only witness** semantics rather than pretending exact-old CAS is a global namespace lock. However §3 then adds an incompatible CPU/static requirement; see the single remaining HIGH.

## Current blocker

### HIGH-1 — observation-only ref semantics contradict the required pre-swap drift behavior

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_pass_linearization_design_v0.9.md:38-40`

v0.9 explicitly chooses this contract:

- `AcceptedPass` binds the last exact local/remote `== candidate` observation before pointer swap;
- it **does not claim** that refs remain exact after that observation;
- any drift after that observation is external corruption;
- once terminal state is ACCEPTED, such drift does not rollback acceptance and later detection must fail-stop/recover.

That is a coherent choice and is exactly one of the two acceptable directions from the v0.8 review.

But the next paragraph requires CPU/static tests to inject local/remote drift **between the last observation and the pointer swap** and assert:

- while PENDING, the transaction does not accept and rolls back;
- only drift after ACCEPTED preserves terminal state and fail-stops later.

Those requirements cannot both be true under the chosen observation-only model. After the declared **last** ref observation there is, by design, no further ref I/O/namespace lock before the in-memory terminal-state pointer swap. Therefore a drift that occurs in that interval is not observable by authority before the swap. The authority must either:

1. still perform the pointer swap based on the historical exact observation, with any later-discovered mismatch classified as external corruption/fail-stop; or
2. perform another ref validation / acquire a stronger coordination primitive before acceptance, which means the previous observation was not actually the last one and merely moves/redefines the race boundary.

The current text asks implementation to do both: adopt observation-only authority while also detecting an otherwise unobservable post-observation/pre-swap mutation. The next implementation Gate would have to invent an extra read/lock/hook or weaken one of the stated invariants.

### Exact acceptance

Choose one exact semantics and make §3 plus the test matrix match it:

**Option A — keep observation-only witness (recommended because it matches v0.9's stated choice):**
- define the last exact local/remote observation as the only ref fact bound into the terminal transition;
- explicitly state that external ref drift after that observation, including drift occurring before the pointer swap, does **not** invalidate the already-prepared acceptance transition because it is outside the observed authority fact;
- if/when such drift is detected later, classify it as external corruption and enter fail-stop/recovery without rolling back an ACCEPTED terminal state;
- update the CPU/static matrix so post-observation/pre-swap drift may result in ACCEPTED based on the historical witness, but any later ref check reports corruption and cannot silently claim current exact refs.

**Option B — require no acceptance when drift occurs before swap:**
- abandon pure observation-only semantics for that boundary;
- freeze the exact extra coordination/read mechanism that detects drift before the terminal swap;
- define its own race/atomicity contract rather than leaving implementation to add another ad hoc observation.

Do not retain the current impossible combination.

## Non-blocking observations

- The v0.9 single-terminal-cell direction should be retained.
- The B/C permanent fail-stop restart policy is conservative but internally valid.
- For crash window A, implementation/restart tests should prove that pre-accept process loss with candidate refs cannot infer ownership from equality alone; existing exact-old lease/preflight must fail closed rather than delete or adopt a same-candidate foreign ref. This is important evidence but does not require reopening the design if the existing lease rules already enforce that behavior.
- v0.9 supersedes v0.8 terminal-transition semantics; implementation should therefore avoid reintroducing a separate mutable one-shot `consumed` bit. Internal `AcceptedPass.consume()` may only reflect/check the shared terminal state unless a new independently justified state is explicitly designed.

## Blocker summary

- design/contract blockers: `1 HIGH`
- total blockers: `1 HIGH`

## Final verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_pass_linearization_design_v0.9.md:38)`

This verdict binds only the exact formal pair `a98e82714940d7bed1969cafb2ef32100c287d59 / 93a89ba61306d840a008813f62f26a34d54850f4`.

No implementation token is granted. Real source/candidate/ref/evidence operations, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, and LIBERO4IN1 remain prohibited.
