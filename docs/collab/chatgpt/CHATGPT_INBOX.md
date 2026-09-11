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

- immediate prior live blob SHA: `a25e18e2a1ceb9d6785e71c3a5d6367c8d65440b`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Root Gitlink Authority Source-audit Implementation Design v0.1 REQUEST_CHANGES

Formal pair:
- root design SHA: `ba684bf769016aaf8bac8b8d4271f6b6bcb3708c`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-ROOT-GITLINK-AUTHORITY-SOURCE-AUDIT-IMPLEMENTATION-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_root_gitlink_authority_source_audit_implementation_design_v0.1.md:31)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_canonical_native_root_gitlink_authority_source_audit_implementation_design_ba684bf_93a89ba.md`

Canonical review commit:
`91241f6402151d4b3a1b0583cc8a7f0c368c07cc`

Current blockers: `2 HIGH`, both Design/Authority. Production blockers: `0`. Evidence-only blockers: `0`.

Blockers:
1. Git execution trust boundary is under-frozen. The command-line whitelist does not freeze trusted Git executable identity/resolution or sanitize inherited subprocess environment / replacement-object controls, so caller-controlled `PATH` / Git repository-object/config environment may still affect object resolution despite the stated no-env authority rule.
2. The implementation artifact drops binding machine-readable evidence inherited from source-audit design v0.1. Success output only carries the compact audit record, while failure stdout has no exact schema; root-tree/Gitlink/publication/child reachability records with deterministic PASS/FAIL + reason and command/version identity are not frozen.

Required remediation:
- freeze deterministic Git executable and sanitized subprocess environment semantics, including disabled replacement objects and exclusion of caller Git context/config variables; add hostile-environment temporary-fixture witnesses;
- freeze exact machine-readable lookup/reachability evidence schemas and exact failure-summary schema while retaining failure-no-output-mutation;
- carry command/tool/Git identity into the evidence contract;
- add direct evidence for the v0.3 canonical publication raw-byte rule (non-canonical raw JSON must not silently pass as canonical publication).

Positive findings retained:
- formal root resolves exactly to child `93a89ba61306d840a008813f62f26a34d54850f4`;
- implementation scope remains root-only two-file stdlib/unittest CPU/static;
- exact raw tree/blob hashing, non-circular publication, nested config/source schemas, 14-key audit record and atomic success-only output remain aligned with approved v0.3 design;
- no real source-audit execution, child/runtime modification, checkpoint/data/cache I/O, GPU/native workload, runtime integration or training is authorized.

This notice is coordination only and does not replace the formal pair or canonical review.
