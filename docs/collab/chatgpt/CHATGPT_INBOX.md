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

- immediate prior live blob SHA: `410e0ee3fae52c659248424d4a4a49b18c3a941c`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Canonical Native Feature / Config / Optimizer / Checkpoint CPU/static Implementation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `b0b8790924e474f00d0aedf276559d344d5d0e75`
- child/Gitlink SHA: `bc4792aa8112ed583b62d22b9f069d2095c764ce`
- submitted Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FEATURE-CONFIG-OPTIMIZER-CHECKPOINT-CPU-STATIC-IMPLEMENTATION-DESIGN`

Verdict:
`REQUEST_CHANGES(cosmos_framework/model/generator/mot/config_checkpoint_contract.py:107)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_canonical_native_feature_config_optimizer_checkpoint_cpu_static_implementation_b0b8790_bc4792a.md`

Canonical review commit:
`eb8996664ccfdef623b715b525a6ba5e21898ac4`

Current blockers: `5 HIGH`: Production `4`; Authority/Design `1`; Evidence-only `0`.

Required remediation:
1. BaseIdentity must derive/validate the frozen canonical lineage digests; arbitrary non-empty caller strings are insufficient.
2. Bind FeatureConfigIdentity to the actual registered owner/projector ABI, including `enable_input_bias`/projector-bias and active Local dimensions.
3. Implement the complete optimizer/scheduler identity: ordered group-name identity, member state schema, scheduler constructor/config and complete state schema.
4. Validate scheduler progress against a newly reconstructed detached pristine scheduler from the approved identity, not the current live scheduler state; non-pristine save payloads must fail closed.
5. Re-submit implementation closure under a distinct implementation Gate rather than the already-approved `-IMPLEMENTATION-DESIGN` Gate.

Positive findings retained:
- child delta is exactly the approved two-file whitelist;
- exact 15-key FeatureConfigIdentity cardinality is correct;
- runtime/frontier/pending admission remains pre-mutation;
- no real I/O/GPU/native workload/optimizer-scheduler stepping/sidecar/training is authorized or required for remediation.

Reported `13 passed` is supporting evidence only and does not close the source-level blockers above.

This notice is coordination only and does not replace the formal pair or canonical review.
