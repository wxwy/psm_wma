# ChatGPT Independent Review — R09-B / TTT v0.3.5 Canonical Segment Producer CPU/static Closure Remediation v3

**Date:** 2026-09-10  
**Role:** Independent Design / Code / Evidence / Gate Reviewer  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-CPU-STATIC-IMPLEMENTATION`  
**Formal root:** `0f321898edce5cbfbce8d790f9b9766524aa70d6`  
**Formal child/Gitlink:** `c3d5b7abb8ae9c8b6764785bd7a5b6bd4aa68ea3`  
**Previous same-Gate formal pair:** `0e88086397eb0ca709a7215fc918f5f662264fc1 / d171d7149533cb31b241b402eb738d091c927ed0`  
**Approved design authority:** `17901f65d9f09772a98921cd28ffbb05d82d3725 / 36bf3b2c3fd1bdd364df9169fa6d177f94e16541` (accumulated producer implementation design v0.1–v0.5)  
**Verdict:** `REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_production_integration_test.py:77)`

## 1. Repository-truth lock

- Latest `origin/V2` observed at review start is request/bookkeeping HEAD `299decb707c2a579bb816fcc176a79a303f62cf2`; it is not the formal implementation target.
- Latest `CODEX_INBOX.md` request declares exactly formal pair `0f321898edce5cbfbce8d790f9b9766524aa70d6 / c3d5b7abb8ae9c8b6764785bd7a5b6bd4aa68ea3` and requests only `APPROVE_TO_CLOSE_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCER_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Formal root `0f321898...` stores `cosmos-framework` exactly at Gitlink `c3d5b7abb8ae9c8b6764785bd7a5b6bd4aa68ea3`.
- Child `c3d5b7a...` is exactly one remediation commit ahead of previous reviewed child `d171d71...`.
- Child incremental diff changes only the four already-approved files: `canonical_segment_production_adapter.py`, `canonical_segment_production_adapter_test.py`, `canonical_segment_production_integration_test.py`, and `omni_mot_model.py`.
- Root incremental diff outside the Gitlink is prior review/Inbox/session bookkeeping; those commits do not replace the formal implementation pair.
- The request reports adapter pytest `4 passed`, integration pytest `7 passed in 36.81s`, py_compile and diff-check PASS. No GitHub commit status/workflow run is attached to `c3d5b7a...`, so these local execution claims are evidence clues only and must be consistent with the submitted test source.

## 2. Previous blocker lifecycle

### CLOSED — raw-row source identity / collate-truth authority

The previous HIGH at `canonical_segment_production_adapter.py:100` is materially and sufficiently closed for this CPU/static Gate.

The carrier now adds typed side metadata `raw_row_source_identities` with four-tuple `(slot, episode, source_digest, step)` and `row_model_source_rows` with exact raw-object references. `validate_model_data_batch()` computes the expected four-tuple from the frozen `member.row_identities[row].source_digest`, exact segment slot/episode/step, and rejects mismatch before adapter creation/scan. The synthetic `raw["canonical_model_sample"]` sentinel has been removed; raw collate-truth mappings are no longer mutated to carry producer bookkeeping. A direct production negative now supplies the same slot/episode/step with a foreign source digest and asserts rejection before `_canonical_production_adapter` is created.

This satisfies the previous closure condition to keep consumer gathered identity separate while preserving full source authority in typed carrier-side metadata.

### CLOSED — carrier-owned `sequence_plan` mutation on failure

The previous HIGH at `omni_mot_model.py:1440` is also closed at production semantics.

After `build_sequence_plans_from_data_batch()`, the canonical safe helper now executes `sequence_plans = [dataclasses.replace(plan) for plan in sequence_plans]` before applying `has_local_memory`. For the native `SequencePlan` dataclass this creates model-owned plan objects; the single canonical prefix adaptation therefore no longer mutates the plan objects retained by `carrier.model_data_batch["sequence_plan"]`.

The real scan-path integration fixture now intentionally supplies raw carrier plans, runs the actual canonical safe helper, reaches the mandatory pre-packer hard-stop, and checks the original carrier plans remain `has_local_memory=False` while scan bookkeeping is cleared.

### OPEN — Evidence closure

The previous Evidence HIGH is improved but not closed. The submitted integration source contains an internal incompatibility with the new production plan-cloning behavior, and several explicitly requested direct witnesses remain absent. This is the sole current blocker below.

### Previously closed items remain closed

- carrier marker activation isolation;
- CP pre-scan fail-closed;
- exact request/member/segment preflight before adapter creation;
- dynamic image/video key handling and XOR;
- list and stacked-tensor source validation;
- post-`get_data_and_condition()` Local-neutral assertion;
- safe text -> plan -> clean -> single prefix adaptation -> memory-init sequence;
- nested `[B,T]`, S0/PAD traversal, expected-before-scan / actual-after-scan ordering;
- exact scan-bookkeeping `abort_scan()` behavior.

No regression was found in these closed items.

## 3. Current blocker

### HIGH — submitted Evidence source is not runnable as claimed and still omits mandatory closure witnesses

**Direct blocking location:** `cosmos_framework/model/generator/mot/canonical_segment_production_integration_test.py:77`

The remediation changed production `_prepare_canonical_production_inputs()` to clone every plan with standard-library `dataclasses.replace(plan)` before Local adaptation (`omni_mot_model.py:1432`). That production change is correct for native `SequencePlan`, which is a dataclass.

However the submitted integration fixture still creates carrier plans as:

`raw_plans = [SimpleNamespace(has_local_memory=False), SimpleNamespace(has_local_memory=False)]`

at line 77. The production-path test later returns those exact `raw_plans` from its monkeypatched `build_sequence_plans_from_data_batch()`, and the direct helper test independently monkeypatches the builder to return another list of `SimpleNamespace` plans. `dataclasses.replace()` rejects `SimpleNamespace` because it is not a dataclass instance. Therefore the current submitted source cannot both be the reviewed child and produce the request's claimed `canonical_segment_production_integration_test.py = 7 passed`: at least the direct-helper path and the real production helper path encounter the new `dataclasses.replace()` boundary before the assertions they claim to witness.

This is not a production regression in native `SequencePlan`; it is an Evidence-integrity failure in the exact closure suite.

Even after replacing those fake plans with real `SequencePlan` dataclass fixtures, the previous review's exact Evidence closure condition is still only partially implemented. The current two-file suite now directly covers foreign `source_digest` before adapter creation and a real scan -> real safe-helper -> intentional hard-stop -> abort path with carrier-plan immutability. It still does not directly witness:

1. injected post-scan `result.gathered` identity/count mismatch through `_canonical_production_segment_forward()`, followed by exact abort and unchanged frontier/scheduler/transaction/commit authority;
2. an injected exception *inside* the real safe-preparation/materialization or `memory_init_training()` sequence, followed by exact abort and no partial committed mutation;
3. explicit production-path zero-call spies for `_prepare_training_data()`, `_get_training_inputs()`, `_inject_local_history()` and `_ttt_local_memory_tokens()`;
4. `training_step()` No-Local parity/fall-through proving canonical carrier/helper/adapter are not constructed/invoked when Local is disabled and no markers are present;
5. post-`get_data_and_condition()` insertion of ordinary `local_memory`, proving fail-closed before canonical adaptation / `memory_init_training()`.

Those items were explicit closure conditions of the immediately preceding formal review, not new blocker inflation. Source inspection of production code is favorable, but this Gate's frozen acceptance requires `contract -> production behavior -> direct CPU/static evidence`; passing unrelated or incomplete tests is insufficient.

**Violated frozen contract**

- implementation design v0.1/v0.3/v0.4 CPU/static acceptance requiring direct legacy-zero-call, No-Local parity and failure-disposition witnesses;
- previous same-Gate formal review exact Evidence closure condition;
- standing Evidence rule that a claimed test result must correspond to the submitted source and establish `contract -> behavior -> evidence`.

**Exact closure condition**

Within the same four-file CPU/static whitelist:

1. make all integration plan fixtures passed through the real helper actual `SequencePlan` dataclass instances (or an equivalent native builder result compatible with `dataclasses.replace()`), then rerun the exact two requested pytest files and report results from the final child SHA;
2. add a production-path actual-gather identity/count mismatch witness with exact abort and unchanged frontier/scheduler/transaction/commit authority;
3. add a real-helper/materialization or `memory_init_training()` exception witness with the same failure disposition;
4. add explicit production-path zero-call spies for ordinary/legacy preparation (`_prepare_training_data`, `_get_training_inputs`, `_inject_local_history`, `_ttt_local_memory_tokens`);
5. add a No-Local `training_step()` parity/fall-through witness showing no canonical carrier/helper/adapter construction;
6. add a post-clean ordinary-`local_memory` injection negative proving rejection before canonical adaptation/memory-init;
7. keep all tests before packer/noise/native forward/loss/backward and do not broaden into real I/O/GPU/training.

Return a new root/child formal pair after those Evidence fixes. No further production redesign is requested by this review unless the new evidence exposes a real behavior defect.

## 4. Scope / non-blocking findings

- Current production blockers from the prior review are CLOSED.
- The current remaining blocker is tests/Evidence-only.
- Child diff remains entirely inside the approved four-file whitelist.
- No dataset/dataloader/collate/packer/trainer/config/optimizer/checkpoint mutation is introduced.
- No real data/cache/checkpoint I/O, CUDA/GPU, torchrun, native packer/noise/forward/loss/backward/training, evaluation, inference, runtime sidecar, distributed execution or LIBERO4IN1 work is authorized or introduced.
- `data_resolutions=None` remains a later forward-enabled Gate watchpoint only and is not a blocker for this pre-packer CPU/static Gate.

## 5. Blocker lifecycle / authorized next action

Current blocker count: **1 HIGH (Evidence only)**.

Authorized next action: repair only the CPU/static Evidence suite under the existing production contract and return a new formal root/child pair for fresh closure review. Production source need not be changed unless required to make an existing frozen behavior directly testable or a new direct witness exposes a real defect.

Not authorized: dataset/dataloader/collate/packer/trainer/config/optimizer/checkpoint changes, real producer/data/cache/checkpoint I/O, CUDA/GPU, torchrun, GradScaler runtime work, native forward/loss/backward/training, evaluation, inference, runtime sidecar, distributed execution or LIBERO4IN1.

## 6. Exact verdict

`REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_production_integration_test.py:77)`
