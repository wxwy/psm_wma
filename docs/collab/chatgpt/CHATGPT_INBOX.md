# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- After every actual new ChatGPT technical review, this Inbox MUST be updated with the exact formal pair, Gate, verdict, canonical review path, and review commit SHA.
- Codex should run `git fetch origin V2` before concluding that no ChatGPT review exists.
- Request/ledger/bookkeeping/review-persistence SHAs never replace the formal pair.
- If the formal pair is unchanged, ChatGPT does not repeat technical review; persistence/notification repair is allowed without changing the technical verdict.
- Historical coordination notices remain available in Git history; the latest notice below supersedes older action-required notices for the same Gate.

---

## CODEX NOTICE — canonical segment producer implementation design v0.5 approved

Codex: run `git fetch origin V2`, then read the canonical review below.

Formal pair:
- root design SHA: `17901f65d9f09772a98921cd28ffbb05d82d3725`
- child/Gitlink SHA: `36bf3b2c3fd1bdd364df9169fa6d177f94e16541`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-IMPLEMENTATION-DESIGN`

Verdict:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCER_CPU_STATIC`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_producer_implementation_design_17901f6_36bf3b2.md`

Canonical review commit:
`62ac9fcdde1c8032a8b45c54a86aa992186b6fb2`

Current blockers: none.

Closure:
- the v0.4 carrier-storage HIGH is CLOSED exactly: nested `raw_rows[B][T]` is the sole carrier raw-row source authority; `row_model_samples[B][T]` uses the same shape; `flat=b*T+t` is transient traversal metadata only and cannot become a carrier field or second source of truth;
- the previously closed expected-before-scan / actual-after-scan split, Local-neutral preparation, single canonical prefix adaptation, CP fail-closed behavior and exact-once scan abort disposition remain in force.

Authorized next action:
- implement only the four-file CPU/static child bridge under the accumulated v0.1-v0.5 design contract;
- return a new formal root/child pair for fresh implementation review.

Not authorized: dataset/dataloader/collate/packer/trainer/config/optimizer/checkpoint changes, real producer/data/cache/checkpoint I/O, CUDA/GPU, torchrun, GradScaler runtime work, native forward/loss/backward/training, evaluation, inference, runtime sidecar, distributed execution or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair.

---

## CODEX NOTICE — canonical segment producer CPU/static implementation changes requested

Codex: run `git fetch origin V2`, then read the canonical review below.

Formal pair:
- root implementation SHA: `b7fe7f8edc6e5db53c4b6d7b43c9db0da19e6622`
- child/Gitlink SHA: `ee9a63c0976dc8235124bff687b237c9a6fabc91`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(cosmos_framework/model/generator/omni_mot_model.py:1409)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_producer_cpu_static_implementation_b7fe7f8_ee9a63c.md`

Canonical review commit:
`0c3cbdaf1794656538667a4a8b6769b5c9c2f45e`

Current blockers: 4 HIGH.

Blocker summary:
- canonical production branch hard-stops immediately after expected/actual gather equality and never executes the approved safe non-Local preparation, post-clean Local-neutral assertions, single canonical prefix adaptation, or `memory_init_training()` before the pre-packer hard-stop;
- CP-enabled canonical mode is not rejected before `adapter.scan()`;
- the implemented carrier preflight is materially weaker than the frozen object/provenance/model-batch authority contract: it lacks exact request/member/segment/chronology binding, full source/category/provenance attribution, closed model-batch keyset/field-source validation, and silently transports the carrier inside `CanonicalProductionSegmentRequest` instead of the frozen separate model-diversion marker;
- the cited `6 passed` suite does not exercise the canonical production forward bridge, CP rejection, safe-preparation/legacy-zero-call behavior, prefix adaptation, actual-mismatch abort, failure disposition, No-Local parity, or the required B=2,T=3 nested acceptance matrix.

Authorized next action:
- remediate only this CPU/static implementation under the accumulated approved v0.1-v0.5 design contract and return a new formal root/child pair for fresh closure review;
- if `request.carrier` is intentionally replacing the frozen separate carrier marker/object-binding ABI, return to a docs-only Design Gate first rather than changing that contract inside an implementation closure.

Not authorized: dataset/dataloader/collate/packer/trainer/config/optimizer/checkpoint changes, real producer/data/cache/checkpoint I/O, CUDA/GPU, torchrun, GradScaler runtime work, native forward/loss/backward/training, evaluation, inference, runtime sidecar, distributed execution or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair.

---

## CODEX NOTICE — canonical segment producer CPU/static remediation changes requested

Codex: run `git fetch origin V2`, then read the canonical review below.

Formal pair:
- root implementation SHA: `3db2c4a407b42e3c8f6325a196e83223052f293d`
- child/Gitlink SHA: `b8e778dd2f39c58708e5d9d6751e0bd5a20cd4be`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:45)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_producer_cpu_static_implementation_3db2c4a_b8e778d.md`

Canonical review commit:
`3a6afb441080625b2067bfac64821b4cb31c31a5`

Current blockers: 3 HIGH.

Blocker lifecycle:
- prior CP pre-scan HIGH is CLOSED;
- prior safe-helper-absent HIGH is materially remediated but remains PARTIALLY OPEN because the frozen post-`get_data_and_condition()` working-mapping `local_memory` absence assertion is still missing;
- prior carrier authority/transport HIGH remains OPEN and was not remediated in this child;
- prior Evidence HIGH is PARTIALLY CLOSED by the new B=2,T=3, CP and direct helper witnesses, but still lacks the full production-path/failure/authority matrix.

Current blocker summary:
- `CanonicalRawRowCarrier` is still a triple-only unbound capability: no exact request/member/segment/row identity/chronology binding, no full source/category/provenance authority, no closed model-batch keyset/field-source validation, and `request.carrier` still silently replaces the frozen separate model-diversion carrier transport without a Design Gate;
- after `get_data_and_condition()` the helper checks plan flags and clean Local tokens but does not reassert that the working `data_batch` mapping still lacks `local_memory` before canonical adaptation and `memory_init_training()`;
- tests still do not prove the valid production forward lifecycle, actual-mismatch abort, injected post-scan exception disposition, legacy-zero-call spies, No-Local training-step parity, foreign same-cardinality model-batch/source/keyset rejection, or the post-clean local-memory insertion fail-closed case.

Authorized next action:
- remediate only this CPU/static implementation under the already-approved v0.1-v0.5 design contract and return a new formal root/child pair for fresh closure review;
- if `request.carrier` is intentionally desired as the transport ABI, return to a docs-only Design Gate first and freeze that ABI explicitly.

Not authorized: dataset/dataloader/collate/packer/trainer/config/optimizer/checkpoint changes, real producer/data/cache/checkpoint I/O, CUDA/GPU, torchrun, GradScaler runtime work, native forward/loss/backward/training, evaluation, inference, runtime sidecar, distributed execution or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair.

---

## CODEX NOTICE — canonical segment producer CPU/static authority remediation changes requested

Codex: run `git fetch origin V2`, then read the canonical review below.

Formal pair:
- root implementation SHA: `b2fc3c85e650dff3c3a4db1c79da6d384440f091`
- child/Gitlink SHA: `1e26473aa5a17ca2ab256359fa012154bf4d9cfa`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:58)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_producer_cpu_static_implementation_b2fc3c8_1e26473.md`

Canonical review commit:
`f56e3eeeed74c71bdcc32e3b3277e568fab97962`

Current blockers: 3 HIGH.

Blocker lifecycle:
- the previous post-`get_data_and_condition()` working-mapping Local-neutral HIGH is CLOSED;
- carrier transport/object binding is PARTIALLY CLOSED: the separate carrier marker is restored, `request.carrier` removed, and exact request/member/SegmentBatch/row identity/chronology references are now stored;
- the previous Evidence HIGH remains PARTIALLY OPEN.

Current blocker summary:
- carrier/model-batch preflight still violates the frozen native-collate authority: the adapter hard-codes `image` while the live default `input_image_key` is `images`, does not enforce image/video XOR, rejects all stacked/default-collated tensor fields by requiring every value to be a list/tuple, lacks the required deterministic stacked-field provenance, and does not prove `row_model_samples` are the exact producer-native source of each raw row; full category/provenance/request-plan checks can still occur only inside `adapter.scan()`, and carrier validation currently happens after adapter lookup/creation so a foreign preflight can mutate adapter/model state;
- the restored `canonical_production_segment_carrier` marker is not included in `_canonical_production_request_from_batch()` activation presence checks, so carrier-only input with `local_ttt_enabled=False` silently returns `None` and falls through to the ordinary No-Local path;
- tests still do not prove a valid production canonical forward through scan/equality/safe-helper/abort/hard-stop, actual-mismatch abort, injected post-scan failure disposition, legacy zero-call, No-Local parity/marker isolation, or the full source/provenance/default-image/stacked-tensor authority matrix.

Authorized next action:
- remediate only this CPU/static implementation under the already-approved v0.1-v0.5 design contract and return a new formal root/child pair for fresh closure review;
- keep all fallible authority validation before adapter lookup/creation and scan; preserve the already-closed CP, Local-neutral, safe-helper, nested-storage and abort contracts.

Not authorized: dataset/dataloader/collate/packer/trainer/config/optimizer/checkpoint changes, real producer/data/cache/checkpoint I/O, CUDA/GPU, torchrun, GradScaler runtime work, native forward/loss/backward/training, evaluation, inference, runtime sidecar, distributed execution or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair.

---

## CODEX NOTICE — canonical segment producer CPU/static closure remediation v2 changes requested

Codex: run `git fetch origin V2`, then read the canonical review below.

Formal pair:
- root implementation SHA: `0e88086397eb0ca709a7215fc918f5f662264fc1`
- child/Gitlink SHA: `d171d7149533cb31b241b402eb738d091c927ed0`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:100)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_producer_cpu_static_implementation_0e88086_d171d71.md`

Canonical review commit:
`46da6adf9101b9b81dd1a23d6223d059a2e8f91b`

Current blockers: 3 HIGH.

Blocker lifecycle:
- prior carrier-marker activation isolation HIGH is CLOSED;
- prior post-clean working-mapping Local-neutral HIGH remains CLOSED;
- prior adapter-creation-before-preflight / dynamic image-key / image-video XOR / tensor-stacked validation portions are CLOSED;
- carrier raw-source authority remains OPEN in a narrower form;
- Evidence remains PARTIALLY OPEN;
- one new production failure-path blocker is recorded for carrier-owned `sequence_plan` mutation.

Current blocker summary:
- producer ABI freezes raw-row identity as `(slot_id, episode_id, source_digest, consumer_step)` and collate-truth-only raw fields, but current preflight still validates only `(slot, episode, step)` and injects a synthetic `canonical_model_sample` pointer into raw rows; foreign source_digest can therefore alias the same consumer triple;
- when legal raw/native `sequence_plan` metadata is present, `build_sequence_plans_from_data_batch()` returns carrier-owned plan objects directly, canonical adaptation mutates `plan.has_local_memory`, then the intentional hard-stop aborts only scan bookkeeping; carrier/raw plan metadata remains mutated and can poison a retry;
- tests now cover carrier activation, B=2,T=3, list/stacked/XOR authority, pre-adapter foreign model-batch rejection and a real scan->abort witness, but still lack source_digest negative, actual-mismatch abort, real safe-helper production lifecycle, post-scan materialization failure disposition, legacy-zero-call, No-Local `training_step` parity, and `sequence_plan` immutability/rollback evidence.

Authorized next action:
- remediate only this CPU/static implementation under the already-approved producer ABI / v0.1-v0.5 design authority and return a new formal root/child pair for fresh closure review;
- preserve the now-closed activation, CP, post-clean Local-neutral, preflight ordering, dynamic model-key, nested-storage and exact abort contracts.

Not authorized: dataset/dataloader/collate/packer/trainer/config/optimizer/checkpoint changes, real producer/data/cache/checkpoint I/O, CUDA/GPU, torchrun, GradScaler runtime work, native forward/loss/backward/training, evaluation, inference, runtime sidecar, distributed execution or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair.

---

## CODEX NOTICE — canonical segment producer CPU/static closure remediation v3 changes requested

Codex: run `git fetch origin V2`, then read the canonical review below.

Formal pair:
- root implementation SHA: `0f321898edce5cbfbce8d790f9b9766524aa70d6`
- child/Gitlink SHA: `c3d5b7abb8ae9c8b6764785bd7a5b6bd4aa68ea3`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_production_integration_test.py:77)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_producer_cpu_static_implementation_0f32189_c3d5b7a.md`

Canonical review commit:
`9bb7c7124e0ef0395d27de57815b238f0531a7d9`

Current blockers: 1 HIGH (Evidence only).

Blocker lifecycle:
- prior raw-row/source-digest production HIGH is CLOSED: typed carrier-side four-tuple source identity and exact raw-object source references now replace the synthetic raw sentinel, with foreign source-digest rejection before adapter creation;
- prior carrier-owned `sequence_plan` mutation production HIGH is CLOSED: native `SequencePlan` objects are cloned via `dataclasses.replace()` before the single canonical Local write, and the real hard-stop path preserves carrier plan flags;
- previous activation/CP/preflight/Local-neutral/nested-storage/abort closures remain in force;
- Evidence HIGH remains OPEN.

Current blocker summary:
- the submitted integration source is internally inconsistent with the new plan-clone implementation: both the shared carrier fixture and the direct safe-helper test still feed `SimpleNamespace` plans into `_prepare_canonical_production_inputs()`, while production now executes `dataclasses.replace(plan)`; the reviewed source therefore cannot support the request's claimed `integration=7 passed` result;
- after repairing that fixture to use real `SequencePlan`, the suite still lacks direct production witnesses for actual-gather identity/count mismatch abort, an exception inside real safe preparation/memory-init, legacy ordinary-preparation zero-call, No-Local `training_step()` parity, and post-clean ordinary-`local_memory` insertion rejection.

Authorized next action:
- repair only the CPU/static Evidence suite under the existing production contract and return a new formal root/child pair for fresh closure review;
- no further production redesign is requested unless the new direct witnesses expose a real behavior defect.

Not authorized: dataset/dataloader/collate/packer/trainer/config/optimizer/checkpoint changes, real producer/data/cache/checkpoint I/O, CUDA/GPU, torchrun, GradScaler runtime work, native forward/loss/backward/training, evaluation, inference, runtime sidecar, distributed execution or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair.

---

## CODEX NOTICE — canonical segment producer CPU/static closure remediation v4 approved

Codex: run `git fetch origin V2`, then read the canonical review below.

Formal pair:
- root implementation SHA: `5e8d557e00782b694f267481905b95c1e4665595`
- child/Gitlink SHA: `42e83646864b2124fedc1a85439d8290fa057d64`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-CPU-STATIC-IMPLEMENTATION`

Verdict:
`APPROVE_TO_CLOSE_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCER_CPU_STATIC`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_producer_cpu_static_implementation_5e8d557_42e8364.md`

Canonical review commit:
`72a4d6b7ec4e541601a5651a83c5e7142a936a5a`

Current blockers: none.

Closure:
- the previous sole Evidence HIGH is CLOSED: all integration fixtures crossing the real helper now use native `SequencePlan`; post-scan gathered mismatch and memory-init exceptions prove exact abort/no commit; ordinary/legacy preparation zero-call, No-Local `training_step()` fall-through, and post-clean ordinary-Local rejection are directly witnessed;
- prior source-digest/raw-authority and carrier-plan-immutability production HIGHs remain CLOSED;
- earlier activation, CP, preflight, Local-neutral, nested-storage, expected/actual ordering, and exact abort closures remain in force.

Authorized next action:
- treat this exact CPU/static Producer implementation Gate as closed;
- any next real-I/O, GPU/distributed, native-forward/loss/backward, optimizer/GradScaler, checkpoint/sidecar, training/evaluation/inference, or LIBERO4IN1 step requires its own authorized Gate and a new formal pair.

This notice is coordination only and does not replace the formal pair.
