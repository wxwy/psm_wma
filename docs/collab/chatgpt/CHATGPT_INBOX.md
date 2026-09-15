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

- immediate prior live blob SHA: `934a353ecb8508f7c501ee8632183009f8661325`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Stage-1 request-instance recovery V20 REQUEST_CHANGES

Formal pair:
- root implementation SHA: `0ed2be7e27d7219f29f7d3601e6a3a0399ae6bfa`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V20`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_recovery_design_v2.0.md:42)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-15_R09_B_TTT_v035_stage1_v17_request_instance_recovery_design_v20_0ed2be7_93a89ba.md`

Canonical review commit:
`175facc734169420497511862667b39fe63bb819`

Current blockers: `1 HIGH`; Design/Atomicity: `1 HIGH`; Production/implementation: `0`; Evidence/Scope: `0`; child/runtime: `0`.

Positive closure:
- formal root resolves and its `cosmos-framework` Gitlink exactly matches the declared child;
- V20 is docs-only and did not execute real pre-C/C, request pair construction, materialization, source-evidence, child/runtime/config mutation, GPU or training;
- it preserves the permanently consumed v1.8 history, C995 ContractV05/C01-C15, opaque consumer, same-object patch handoff, terminal no-retry, byte-exact readback and hard stop.

HIGH 1 — C-time freshness source/ABI is not frozen:
- V20 seals live facts during pre-C, then defines C as `freshness snapshot equality -> one opaque write -> byte-for-byte readback -> hard stop`, while simultaneously forbidding query/discovery/path/schema/import/identity decisions in C;
- the approved CPU/static API still accepts `consume_once_v05(plan, current_closure)`, but neither V20 nor ContractV05 defines how a real C obtains this `current_closure` without forbidden C-time reconstruction;
- re-running remote/local/path observations in C violates the no-query/no-discovery boundary, while simply reusing the pre-C closure makes freshness equality tautological and gives no TOCTOU protection.

Required remediation:
- refreeze one exact C-time freshness ABI before real construction authority is granted;
- classify fixed/immutable fields as sealed-only comparisons;
- for mutable local facts, seal the exact observation handle/capability/predicate in pre-C and the exact permitted C-time read/compare operation;
- remote-query facts must either be explicitly pre-C-only or use a separately authorized sealed freshness capability consistent with the controlling no-query lifecycle;
- output absence/readback paths and their permitted C-time observations must be exact;
- the production contract must not accept an arbitrary externally reconstructed `ClosureV1` of unspecified provenance;
- provide CPU/static evidence that mutable drift is detected before the opaque call without forbidden discovery/query.

Until this is closed, real pre-C/C, future request-pair construction, materialization/source-evidence, real Git/network/source/data/cache I/O, child/runtime/config mutation, GPU and training remain forbidden.

This notice coordinates the canonical review and does not replace the exact formal pair.
