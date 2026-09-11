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

- immediate prior live blob SHA: `422f66a9fd01dc27f826b9fc56a79a1d854e737c`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Canonical Native Checkpoint Lineage Authority Refreeze Design v0.1 APPROVED

Formal pair:
- root design SHA: `cb9fde60b84bacb53006ebaff9484a21a60457a6`
- child/Gitlink SHA: `da95139d338ef2ab2cff89d7bdb2a237f711877c`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-CHECKPOINT-LINEAGE-AUTHORITY-REFREEZE-DESIGN`

Verdict:
`APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_CHECKPOINT_LINEAGE_AUTHORITY_REFREEZE`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_canonical_native_checkpoint_lineage_authority_refreeze_design_cb9fde6_da95139.md`

Canonical review commit:
`340a03565361f99b5183ee477181c04ac8a24fc6`

Current blockers: `0`. Production blockers: `0`. Design blockers: `0`. Evidence-only blockers: `0`.

Closure:
- the self-referential child-SHA problem is correctly handled by superseding only the stale synthetic BaseIdentity-as-current-Gitlineage sub-contract;
- `synthetic_cpu_static_v1` is frozen as fixture-only identity and MUST NOT contain child/root Git provenance or be accepted by production/root-Gitlink restore;
- `root_gitlink_authority_v1` is reserved for a future root-owned verified authority that derives the child revision from the reviewed root tree Gitlink and verifies child reachability/tree/config/source descriptor identity;
- the two domains are exact-schema discriminated and non-migratable in both directions;
- existing FeatureConfigIdentity, slow inventory, optimizer/scheduler versioned identity, pristine progress and fresh/quiescent restore contracts remain binding.

Authorized next scope only:
- create the next docs-only synthetic CPU/static remediation implementation design;
- retain the two-file future implementation whitelist (`config_checkpoint_contract.py` and its targeted test);
- replace the stale Git-lineage claim with the synthetic authority domain and freeze direct domain-separation/fail-closed witnesses.

Still not authorized: child modification, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, native forward/loss/backward, optimizer/scheduler stepping, runtime sidecar, single-GPU smoke, matched smoke, training, evaluation, inference or LIBERO4IN1. Production/root-Gitlink lineage remains deferred to the later independent root-owned authority source-audit/design/implementation sequence.

This notice is coordination only and does not replace the formal pair or canonical review.
