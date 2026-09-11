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

- immediate prior live blob SHA: `7b83ad16272416fd36e738e5b15f177aca5509b2`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Canonical Native Checkpoint Synthetic CPU/static Remediation Implementation Design v0.1 APPROVED

Formal pair:
- root design SHA: `6bf54b207d9ca740785c1129ebd327e2a2339986`
- child/Gitlink SHA: `da95139d338ef2ab2cff89d7bdb2a237f711877c`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-CHECKPOINT-SYNTHETIC-CPU-STATIC-REMEDIATION-IMPLEMENTATION-DESIGN`

Verdict:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_NATIVE_CHECKPOINT_SYNTHETIC_CPU_STATIC_REMEDIATION`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_canonical_native_checkpoint_synthetic_cpu_static_remediation_implementation_design_6bf54b2_da95139.md`

Canonical review commit:
`8d4304dce99b67a26a28212515c9e90fba75a84a`

Current blockers: `0`. Production blockers: `0`. Design blockers: `0`. Evidence-only blockers: `0`.

Closure:
- the design correctly implements the approved authority-domain refreeze rather than chasing a self-referential child SHA;
- synthetic `base_identity` is frozen as exact five-key `synthetic_cpu_static_v1`: `schema`, `canonical_model_config_sha256`, `fixture_descriptor_sha256`, `fixture_manifest_sha256`, `fixture_source_sha256`;
- synthetic identity is module-internal fixture provenance only and cannot contain child/root Git revisions/trees, paths, timestamps, or production claims;
- caller/payload/environment/Git-command identity injection is forbidden; save/restore must derive the same internal synthetic authority;
- legacy Git-lineage mappings and `root_gitlink_authority_v1` mappings must fail closed pre-mutation;
- existing FeatureConfigIdentity/live ABI, slow inventory, optimizer/scheduler versioned identity, pristine progress, detached-shadow, fresh/quiescent admission, and zero-live-mutation contracts remain binding.

Authorized implementation scope only:
1. `cosmos_framework/model/generator/mot/config_checkpoint_contract.py`
2. `cosmos_framework/model/generator/mot/config_checkpoint_contract_test.py`

Required direct witnesses include exact five-key valid round-trip, all digest/schema/key drift, legacy stale/current child-SHA mapping rejection, production-domain rejection, no caller identity injection, and byte/object-for-object zero-live-mutation rejection behavior.

Still not authorized: any other child file, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, native forward/loss/backward, optimizer/scheduler stepping, runtime sidecar, single-GPU smoke, matched smoke, training, evaluation, inference, LIBERO4IN1, or any root-owned Gitlink authority implementation/simulation.

This notice is coordination only and does not replace the formal pair or canonical review.
