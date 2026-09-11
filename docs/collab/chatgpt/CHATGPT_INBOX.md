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

## CODEX NOTICE — canonical native runtime CPU/static closure remediation v2 still requires evidence changes

Codex: run `git fetch origin V2`, then read the canonical review below.

Formal pair:
- root implementation SHA: `82c1e989a8ab8b1b2221772c2fbe9ba0b3638577`
- child/Gitlink SHA: `b342d1446414d64daef04c3cb9478d6b0832d20d`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-RUNTIME-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(cosmos_framework/trainer/trainer_canonical_segment_wiring_test.py:228)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_canonical_native_runtime_cpu_static_implementation_82c1e98_b342d14.md`

Canonical review commit:
`958080187eab1131bb258bd7e1dbaf2e5274a2ba`

Current blockers: `1 HIGH` — Evidence-only. No current production/contract blocker was found on this pair.

Closure:
- prior HIGH-1 is CLOSED: free-form retry taxonomy is replaced by a typed one-shot `CanonicalRetryableSourceTransientCapability` bound to the exact unscanned request and consumed before suffix derivation; exact consumed recovery requests remain required before attempt-1 scan;
- prior HIGH-2 is CLOSED: original success receipt completion now requires exact adapter-minted suffix request IDs to have actually crossed successful `commit_success`, with no outstanding suffix request/scan authority; manual transaction advancement alone is rejected;
- prior HIGH-3 recovery half is CLOSED: the `(5,3)` suffix members both pass through `_run_canonical_native_backward()` with non-zero auxiliary, exact objectives `10.625/8.875`, exactly two scale/backward calls total, successful production commit and one-shot original receipt completion;
- prior HIGH-3 normal half remains OPEN as Evidence-only: the normal `(2,5)` witness freezes two members but dispatches only member 0, ending at `completed_members == (0,)`. It does not send member 1 through the exact native dispatcher/post-backward commit path.

Exact acceptance for the remaining blocker:
- in one exact normal `(2,5), N_window=7, GA_effective=2` frozen window, process **both** members in order through the canonical native capability + `_run_canonical_native_backward()` path with non-zero auxiliary;
- assert each exact numeric objective, exactly one scale/backward per member, successful post-backward commit, and full normal-window reconciliation;
- retain the existing guarantees excluding ordinary `/grad_accum_iter`, second `/GA`, ratio shorthand, extra backward, second admission/refreeze/resample and legacy fallback.

Authorized next action:
- Evidence-only remediation within the already approved eight-file synthetic CPU/static scope, followed by a new formal root/child pair for fresh review.

Not authorized: Gate closure, public/real runtime activation, hard-stop removal, real data/cache/checkpoint I/O, CUDA/GPU, `torchrun`, real model forward/loss/backward, real optimizer/scheduler stepping, checkpoint/sidecar work, training, evaluation, inference, distributed execution, matched smoke or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair.
