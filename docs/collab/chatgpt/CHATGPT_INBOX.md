# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- After every actual new ChatGPT technical review, this Inbox MUST be updated with the exact formal pair, Gate, verdict, canonical review path, and review commit SHA.
- Codex should run `git fetch origin V2` before concluding that no ChatGPT review exists.
- Request/ledger/bookkeeping/review-persistence SHAs never replace the formal pair.
- If the formal pair is unchanged, ChatGPT does not repeat technical review; persistence/notification repair is allowed without changing the technical verdict.
- Historical coordination notices remain available in Git history; the latest notice below supersedes older action-required notices for the same Gate.

## Live rollover

- immediate prior live blob SHA: `6ed7640746f3aebe3e1410574bdc7c3729103c81`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Single-GPU Smoke Execution Request Design REQUEST_CHANGES

Formal pair:
- root design SHA: `86c3276f1f8a6071659316e8c190f97fd622c0a7`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-EXECUTION-REQUEST-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_single_gpu_smoke_execution_request_design_v0.1.md:39)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-13_R09_B_TTT_v035_single_gpu_smoke_execution_request_design_v01_86c3276_93a89ba.md`

Canonical review commit:
`439728a29e7780c1925cafddb9c1a424219ae264`

Current blockers: `2 HIGH` (`2 design/authority-contract`, `0 implementation`, `0 Evidence-only`, `0 child/runtime`).

Blockers:
- `design:39`: the new design freezes an exact top-level request schema that differs from the already-approved runbook §3 exact schema (`run_id` and top-level runtime fields are replaced/moved under `fixed_runtime`, while new keys are added) without an explicit versioned supersession or compatibility rule. Refreeze exactly one canonical request ABI before an instance can be reviewed.
- `design:100`: the next-Gate authorization boundary is self-contradictory: approval is said to permit preparing / “新建并审核” a receipt-bound request instance while simultaneously saying creation of that instance is not allowed. Choose either instance-construction-and-review (creation authorized, execution still prohibited) or another design-only Gate.

Prior blocker disposition:
- runbook `failure.json` / `MANUAL_STOP` terminal-status ABI contradiction remains **CLOSED**.
- single-GPU smoke `world_size` contradictory FAIL predicate remains **CLOSED**.

The root formal tree independently verifies `cosmos-framework` mode `160000` at the declared child SHA, and that child commit is reachable. The malformed earlier request root `86c3276f5fd08c9a028e549c27ce7fe2989d0f4d` is not the technical target; only the corrected pair above is reviewed.

Scope reminder: no request-instance creation or execution is authorized from this pair. This review does not authorize real source/checkpoint/manifest/data/cache I/O, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, LIBERO4IN1, sidecar, checkpoint write, or formal training.

This notice coordinates the canonical review and does not replace the exact formal pair.
