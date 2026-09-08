# ChatGPT independent review — R09-B TTT v0.3.6 canonical training/runtime contract @ bc25211

Date: 2026-09-08

## Verdict

**REQUEST_CHANGES**

Formal Gate:
`G0-R09-B-TTT-V035-CANONICAL-SEMANTICS-DESIGN`

Formal design pair:
- root design SHA: `bc252114b6799559a172a3061677562c8df565a2`
- child/Gitlink baseline: `80aec090688e3c710c41e1dfd86b6500773db2c7`
- superseded prior design target: `6828b55400d49ef82f1eed895fd609bf8179c3a8`
- review-start remote `V2` bookkeeping HEAD: `d2421342e333a55df31a33928f180b2d603a204b`

The user-supplied string `6bc252114...` was not a valid root commit. Current canonical `SESSION.md` and `CODEX_INBOX.md` both identify the actual current formal target as `bc252114.../80aec090...`; GitHub commit lookup confirms `bc252114...` is `design: remediate local memory training contract v0.3.6`. This review binds only that verified pair.

Scope check:
- `bc25211... -> d242134...` contains only SESSION/TODO and canonical Inbox rollover/bookkeeping; no new design/implementation target supersedes `bc25211...`;
- child remains exactly `80aec090...`; v0.3.6 itself is docs-only;
- no child/runtime/packer/trainer modification, GPU/CUDA/torchrun, real data/cache/checkpoint I/O, training, evaluation or inference is authorized by this review.

## Closed relative to 6828b55

v0.3.6 materially closes the known prior migration-design blockers:
- freezes shifted previous-evidence ABI `S_t <- e_(t-1)` and explicit S0 Local absence;
- defines `training_stream_end`, terminal/tail/rebind and sparse `None` Memory Prefix semantics;
- separates rank-local episode-stream scheduler ownership from slow LR scheduler behavior under GradScaler skip;
- makes the unscaled native model loss the sole native-loss finiteness authority;
- partitions primary consumer loss from auxiliary/load-balancing loss and gives the Local path unique scaling ownership, preventing a second unconditional trainer `/GA`;
- requires state/dt/age branches to be physically absent and requires optimizer/checkpoint inventory refreeze;
- inserts a mandatory runtime-sidecar Gate before formal training.

These are real design closures and should not be re-opened absent a new contradiction.

## Finding

### HIGH — GA-window partial failure semantics are not atomic, so the frozen loss denominator and slow-gradient state can become inconsistent

**Location:**
- `docs/build/PSM-WMA_Local_Memory_canonical_training_runtime_contract_v0.3.6.md:78-88`
- `docs/build/PSM-WMA_Local_Memory_canonical_training_runtime_contract_v0.3.6.md:92-121`

**Root cause:** §4 commits each successful segment's fast state, cursor, queue and exposure immediately after that segment's outer backward. §6, however, freezes `N_window = sum_mu N_valid_mu` before the first backward in the GA window and uses that fixed denominator for every primary-loss contribution. The design does not define what happens when a later microbatch in that same GA window hits load/decode/cache identity failure, inner non-finite, forward exception or backward exception after earlier microbatches have already:
1. accumulated slow gradients weighted by the original planned `N_window`, and
2. committed their fast chronology/cursor/exposure.

At that point the implementation cannot simply remove the failed microbatch from the denominator because earlier gradients are already scaled, and it cannot transparently replay the whole window because earlier chronology has already committed and §4 forbids random replay/rebind. The document also does not state whether the entire slow-gradient GA window is discarded, whether accumulation continues with the original denominator, or whether a new denominator/window begins. Those choices are observably different training algorithms.

A related binding is also missing: the planned `N_valid_mu` used to form `N_window` is not explicitly required to equal the actual `consumer_valid` count that reaches the gather/loss seam before that microbatch backward. A scheduler/packer mismatch would therefore silently corrupt the same weighting contract.

**Contract violation:** the document claims to be the unique implementation contract for valid-consumer weighting, scheduler chronology and abort semantics. Without a single GA-window failure/denominator rule, the CPU/static implementation design cannot be deterministic or prove the stated full-valid/tail gradient equivalence.

**Acceptance condition:** freeze one explicit GA-window transaction rule before implementation. At minimum it must state:
1. `planned_N_valid_mu == actual_gathered_N_valid_mu` is checked before each Local-path backward; mismatch fails closed before that microbatch contributes slow gradients or fast commit;
2. if any microbatch fails after one or more earlier backwards in the same GA window, exactly what happens to already accumulated slow grads, the pending optimizer/LR-scheduler step, and the remaining microbatches;
3. whether successful earlier fast chronology/cursor/exposure commits are retained (recommended if chronology is consumption-authoritative) or rolled back, and how this remains consistent with the no-replay rule;
4. if earlier fast commits are retained, the safest deterministic rule is to discard/zero the entire partial slow-gradient GA window, perform no slow optimizer/LR-scheduler step for that window, and start the next GA window with a newly planned denominator; if a different policy is intended, its equivalent mathematics and rollback mechanism must be frozen explicitly;
5. add required CPU fixtures for failure at microbatch 0 and after at least one successful backward, verifying byte-identical/expected fast chronology state, slow `.grad`, optimizer iteration, episode scheduler, slow LR scheduler and next-window denominator planning.

## Evidence / scope note

This is a docs-only design review. No runtime tests are required for the design verdict itself. The current v0.3.6 text is substantially improved and the finding above is the only blocking design ambiguity found in this review.

## Required next submission

A docs-only v0.3.7 (or equivalent new design SHA) that closes the GA-window transaction/denominator rule may be resubmitted against the same child baseline if no child changes occur. It requires fresh same-SHA review.

Until approval, still prohibited:
- child/runtime/packer/trainer implementation;
- GPU/CUDA/torchrun;
- real data/cache/checkpoint I/O;
- training/evaluation/inference;
- formal Local-Memory training or later smoke Gates.
