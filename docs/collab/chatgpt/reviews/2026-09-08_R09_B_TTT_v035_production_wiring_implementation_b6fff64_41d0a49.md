# ChatGPT independent production wiring CPU/static implementation review

Formal reviewed pair:
- root implementation SHA: `b6fff64cd06ab20f9ef732ca429e1b9bc603f70c`
- child/Gitlink SHA: `41d0a49cc7275f53efbc375e04b5f7dcb5c7b701`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-WIRING-CPU-STATIC-IMPLEMENTATION`

Verdict: `REQUEST_CHANGES`

Scope/whitelist: clean. Relative to approved child `d05f14e`, the implementation changes only approved wiring/adapter/model/trainer surfaces and adjacent tests; no config/default/registry/dataset/checkpoint/real-I/O/GPU/training wiring is introduced.

Current blockers:

1. **HIGH — exact `CanonicalSegmentWiring` capability identity is not actually bound.** `cosmos_framework/model/generator/mot/production_segment_wiring.py:20-45`; `cosmos_framework/trainer/__init__.py:599-622`. The trainer validates only `wiring.adapter.pending_scan == (identity, transaction, forward.result)`. A second `CanonicalSegmentWiring` object can wrap the same adapter with a different `local_slow_parameters` tuple and still pass this guard. On a downstream failure, the delegated seam would call the substituted wiring's `clear_local_slow_grads()`, clearing the wrong Local slow-gradient owner while the adapter/result/transaction guard still succeeds. This violates the frozen v0.6 contract that the exact wiring which performed `prepare()` must be the same capability used for grad clearing and commit.

   Acceptance: bind the exact wiring capability to the forward/pending authorization and fail closed on same-adapter/different-wiring substitution before delegation/backward/commit. Add a negative fixture using the same adapter/result/transaction but a different `CanonicalSegmentWiring` with different slow parameters, asserting zero backward/commit and unchanged true Local/unrelated gradients.

2. **HIGH — the actual model→trainer marker path is not proven to execute a valid S0 consumer backward; the current frozen fixture exposes a no-grad primary.** `cosmos_framework/model/generator/mot/production_segment_wiring.py:48-59`; `cosmos_framework/model/generator/mot/production_segment_wiring_test.py:24-56`; `cosmos_framework/model/generator/omni_mot_model.py:1263-1295`; `cosmos_framework/trainer/trainer_canonical_segment_wiring_test.py:9-37`. `run_native_forward_for_test()` sums only non-None Local tokens. The current fixture is a valid S0-only consumer (`consumer_step=0`, Local absent by canonical contract), so the spy returns a constant zero scalar with no autograd path. The real `_canonical_local_memory_segment_forward()` would pass that as `primary_consumer_mean` into the existing backward seam and `loss.backward()` would terminal-fail. The successful trainer fixture bypasses this actual model helper and substitutes `forward.result.local_tokens.sum()` as the primary, so it does not establish the real marker path.

   Acceptance: make the pure test spy produce a graph-bearing consumer loss for valid S0 as well as non-S0 consumers without inventing a second production loss authority, then add an end-to-end CPU fixture that calls the real `OmniMoTModel.training_step` marker route and the real trainer canonical branch through successful backward/commit with S0 present.

3. **MEDIUM — mandatory v0.6 Evidence matrix is incomplete.** `cosmos_framework/model/generator/omni_mot_model_test.py` contains no marker reachability/disable-first parity fixture; trainer fixtures cover exact success and mismatched result only, but not missing capability, same-adapter/different-wiring, reconstructed/stale result, external-plan-key fail-closed, or the full actual model→trainer route. The implementation also ignores an external `canonical_plan` field rather than explicitly rejecting it before objective/backward/commit as frozen by v0.5/v0.6.

   Acceptance: after the two HIGH fixes, add only adjacent CPU/static fixtures for the missing negative/positive witnesses and rerun the declared CPU suites with readable PASS plus target `py_compile` and child/root `git diff --check`.

No production-wiring closure is granted. Runtime-sidecar persistence/resume, real data/cache/checkpoint I/O, config/default/registry/optimizer changes, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T and LIBERO4IN1 remain prohibited.
