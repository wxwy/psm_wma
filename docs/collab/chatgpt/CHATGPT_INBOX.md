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

- immediate prior live blob SHA: `fc6c8bb27993352d7c18e9143d6d61ebc067b7ce`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Canonical Native Checkpoint Synthetic CPU/static Remediation Implementation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `8d1a667fa504f316a6f11561c639b1147ecfd16e`
- child/Gitlink SHA: `18328aeed1e6c541fadd9d9063903dee585d79a5`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-CHECKPOINT-SYNTHETIC-CPU-STATIC-REMEDIATION-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(cosmos_framework/model/generator/mot/config_checkpoint_contract.py:120)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_canonical_native_checkpoint_synthetic_cpu_static_remediation_implementation_8d1a667_18328ae.md`

Canonical review commit:
`48b4dc27bd59f0573e75b7cc183a3180ebf06713`

Current blockers: `2 HIGH`: Production `1`; Evidence-only `1`; Design/Authority `0`.

Positive findings retained:
- formal root resolves exactly to requested child;
- child delta from approved baseline is one commit and exactly the approved two-file whitelist;
- exact five-key `synthetic_cpu_static_v1` is present and contains no Git provenance;
- stale/current child-Git mappings and `root_gitlink_authority_v1` mappings fail closed;
- caller-supplied expected BaseIdentity remains removed;
- existing FeatureConfig/live ABI, optimizer/scheduler versioned identity, pristine progress, detached-shadow, and quiescent admission remain intact.

Required remediation:
1. Production HIGH: `_synthetic_fixture_authority()` currently uses placeholder 64-hex literals (`"d"*64`, `"a"*64`, `"b"*64`). The approved design requires fixture descriptor/manifest/source digests to be derived from explicit module-internal **versioned canonical fixture definitions**. Define those deterministic in-memory definitions and derive the three SHA-256 values from their canonical content; add independent recomputation/drift witnesses.
2. Evidence-only HIGH: identity/domain rejection witnesses currently do not directly prove the full frozen zero-live-mutation set. Add direct parameterized evidence with live optimizer+scheduler and snapshots asserting unchanged slow tensors, optimizer/scheduler state, iteration, Parameter/module/adapter object identities, and adapter/frontier/pending authority for synthetic digest/schema/key drift, legacy Git mapping, and production-domain rejection.

Reported `14 passed` plus Ruff/py_compile/diff-check are supporting evidence only and do not close the above source/evidence gaps.

Still not authorized: any other child file, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, native forward/loss/backward, optimizer/scheduler stepping, runtime sidecar, single-GPU smoke, matched smoke, training, evaluation, inference, LIBERO4IN1, or any `root_gitlink_authority_v1` implementation/simulation.

This notice is coordination only and does not replace the formal pair or canonical review.
