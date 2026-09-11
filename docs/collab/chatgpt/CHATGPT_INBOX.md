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

- immediate prior live blob SHA: `0f57cd8b2799d9d01bedaca9c15c271625c09120`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Canonical Native Feature / Config / Optimizer / Checkpoint CPU/static Implementation trusted-lineage closure REQUEST_CHANGES

Formal pair:
- root implementation SHA: `2d2a32a9ced1f7fd2767e783c9b1dd133164669a`
- child/Gitlink SHA: `da95139d338ef2ab2cff89d7bdb2a237f711877c`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FEATURE-CONFIG-OPTIMIZER-CHECKPOINT-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(cosmos_framework/model/generator/mot/config_checkpoint_contract.py:178)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_canonical_native_feature_config_optimizer_checkpoint_cpu_static_implementation_2d2a32a_da95139.md`

Canonical review commit:
`73c650f54473b66b92e1ccf2e247a9485b54e5a7`

Current blockers: `1 HIGH`, Production. Authority/Design blockers: `0`. Evidence-only blockers: `0`.

Remediation status:
- caller-provided `base_identity` entry points: CLOSED; save/restore now derive expected BaseIdentity internally;
- optimizer/scheduler versioned canonical JSON/SHA-256 identity contract: CLOSED;
- live evidence feature-version ABI binding: CLOSED;
- detached pristine scheduler and distinct implementation Gate remain CLOSED;
- remaining HIGH: `_CPU_STATIC_TRUSTED_LINEAGE_OWNER.child_git_revision` is hard-coded to prior child `d0d73338ca1b0e8ae350d447181a804308241390`, while the exact formal/current Gitlink is `da95139d338ef2ab2cff89d7bdb2a237f711877c`. Current canonical payloads therefore encode stale source lineage.

Required remediation:
- bind BaseIdentity to the actual trusted formal/current child revision rather than a stale prior child;
- do not solve this by chasing a self-referential child SHA literal inside the child commit; use an independently owned trusted lineage authority capable of binding the exact formal Gitlink, or first refreeze/supersede the contract if the two-file/no-I/O scope cannot represent it;
- add a direct witness that the canonical expected BaseIdentity for the submitted formal pair contains the submitted Gitlink and rejects the immediately prior child revision.

Positive findings retained:
- formal root resolves exactly to requested child;
- child remediation remains within the approved two-file synthetic CPU/static scope;
- reported `14 passed` plus Ruff/py_compile/diff-check remain supporting evidence only.

Still not authorized: real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, native real forward/loss/backward, optimizer/scheduler step, sidecar/resume, single-GPU smoke, matched smoke, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
