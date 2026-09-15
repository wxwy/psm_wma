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

- immediate prior live blob SHA: `1a37afc08e6ce4b986e3af3cb812f748e29d77ff`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Stage-1 v0.5 pre-C rehearsal closure remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `bc7857492dec64a629ecb7684e6d307d146aca24`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-CPU-STATIC`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_v17_pre_c_rehearsal.py:203)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-15_R09_B_TTT_v035_stage1_v17_pre_c_rehearsal_consumer_cpu_static_bc78574_93a89ba.md`

Canonical review commit:
`361bc5904cc737ed7ffae9dbcc2d3e34b39b1ca2`

Current blockers: `1 HIGH`; Design/Authority: `0`; Production/implementation: `1 HIGH`; Evidence/identity: `0`; child/runtime: `0`.

Positive closure:
- exact-once retirement now happens before freshness comparison, so freshness failure is terminal;
- post-write verification returns typed `ReadbackV1`, and the core performs byte-exact equality plus canonical JSON/Markdown revalidation;
- patch bytes are rebuilt from sealed producer raws and compared exactly;
- exact v0.5 output tuple, exact six-key Git isolation environment, and ordinary capability/plan copy/serialization rejection are present.

HIGH 1 — live closure observation schema/semantics still do not match the frozen authority:
- `designated_absences` accepts any four unique strings instead of the exact four ordered V18 absolute-path observation records;
- `output_absences` is only a pair of pathnames, not typed absence observation records with raw predicate/result identity;
- query/authority-absence raw facts still omit explicit byte-length/SHA-256 identities required by the inherited closure, including the separately extracted remote-V2 advertised value;
- `authority_ref` is declared `authority_absent`, but `_validate_closure()` incorrectly requires non-empty stdout; the inherited absence rule requires non-empty/unqualified ref results to fail closed.

Required remediation:
- bind the exact four ordered V18 designated paths and exact absence records;
- model both v0.5 output absences as typed exact observation records;
- bind explicit raw byte length/SHA-256 identities for required query/absence results and extracted advertised V2;
- make valid remote authority-ref absence require the exact qualified empty result and reject non-empty/unqualified output;
- add direct CPU/static tests for all of these rejection cases.

No CPU/static closure is granted for this pair. v0.5 request construction/C/materialization and all real I/O remain forbidden.

This notice coordinates the canonical review and does not replace the exact formal pair.
