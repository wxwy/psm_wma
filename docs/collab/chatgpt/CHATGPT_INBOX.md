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

- immediate prior live blob SHA: `c5fde84661779125d86db81f23f87850e760d6b8`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Canonical Native Feature / Config / Optimizer / Checkpoint CPU/static Implementation lineage remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `eeec46d5c5667d7c3a30d9637025cc0819aeb468`
- child/Gitlink SHA: `d0d73338ca1b0e8ae350d447181a804308241390`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FEATURE-CONFIG-OPTIMIZER-CHECKPOINT-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(cosmos_framework/model/generator/mot/config_checkpoint_contract.py:132)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_canonical_native_feature_config_optimizer_checkpoint_cpu_static_implementation_eeec46d_d0d7333.md`

Canonical review commit:
`39f83828dd64ceb4bda68451c6072aec39ac014b`

Current blockers: `1 HIGH`, Production. Authority/Design blockers: `0`. Evidence-only blockers: `0`.

Remediation status:
- optimizer/scheduler versioned exact identity + canonical JSON SHA-256 discipline: CLOSED;
- live evidence feature-version ABI binding (`visual96`, `action10`, state/dt/age disabled, evidence/core/projector ABI): CLOSED;
- detached pristine scheduler and distinct implementation Gate remain CLOSED;
- owner-derived BaseIdentity remains incomplete: `LineageOwnerIdentity` is directly caller-constructible, and `strict_restore()` / `strict_restore_into()` still accept caller-provided `base_identity` as expected authority. The direct valid test uses `child_git_revision="f" * 40` rather than formal child `d0d73338ca1b0e8ae350d447181a804308241390`, so matching foreign payload + matching foreign expected mapping can self-authorize.

Required remediation:
- derive expected BaseIdentity inside the trusted checkpoint/manifest lineage-owner path from the exact reviewed/current child revision and frozen manifest/source descriptor authority;
- do not let restore accept an arbitrary caller-selected expected BaseIdentity mapping that can be chosen to match a forged payload;
- add a direct witness where payload and caller-supplied foreign lineage agree syntactically but restore still rejects because the trusted owner/current child is the reviewed child (or exact independently owned CPU/static lineage authority).

Positive findings retained:
- formal root resolves exactly to requested child;
- child delta remains exactly the approved two-file whitelist;
- reported `14 passed` plus Ruff/py_compile/diff-check are supporting evidence only.

Still not authorized: real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, native real forward/loss/backward, optimizer/scheduler step, sidecar/resume, single-GPU smoke, matched smoke, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
