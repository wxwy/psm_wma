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

- immediate prior live blob SHA: `f9cfd0bc36da2ceed3c3a41004cb1830afda228c`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Stage-1 v0.5 exact absence-closure remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `08a4dee0e85084a110f1c642513dd32583efb72e`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-CPU-STATIC`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_v17_pre_c_rehearsal.py:55)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-15_R09_B_TTT_v035_stage1_v17_pre_c_rehearsal_consumer_cpu_static_08a4dee_93a89ba.md`

Canonical review commit:
`7b693599c0b09d012725f48889ee4598ada9813b`

Current blockers: `1 HIGH`; Design/Authority: `0`; Production/implementation: `1 HIGH`; child/runtime: `0`.

Positive closure:
- the exact four ordered V18 designated absolute paths are now frozen;
- remote authority-ref absence correctly requires empty stdout;
- local/remote authority-absence records now validate explicit byte length/SHA-256;
- exact v0.5 paths, six-key Git isolation environment, exact-once retirement before freshness, typed readback, internal byte equality, canonical JSON/Markdown checks, inverse patch witness and terminal no-retry remain preserved.

HIGH 1 — frozen observation identities are still incomplete:
- `QueryFactV1` carries stdout/stderr/advertised bytes but does not carry/validate byte-length and SHA-256 identities for those raw results or the separately extracted advertised-V2 raw value;
- `output_absences` remains pathname-only rather than typed absence-observation records;
- `designated_absences` is now the correct four pathname strings but still not the V18 required ordered `lexists=false` observation records with predicate/result/boolean and canonical record byte length/SHA-256;
- therefore a semantically foreign observation with the right path/argv/predicate shape can still pass the CPU/static closure layer.

Required remediation:
- replace the remaining reduced fields with typed frozen observation records carrying and validating raw bytes plus byte length/SHA-256 identities;
- for both remote queries, bind timeout/rc/stdout identity/stderr identity/predicate and, for remote V2, independent advertised-value identity;
- model both v0.5 output absences and all four V18 designated absences as typed exact observation records with the frozen semantics;
- add direct CPU/static drift tests for every identity field before consumer invocation.

No CPU/static closure is granted for this pair. v0.5 request construction/C/materialization and all real I/O remain forbidden.

This notice coordinates the canonical review and does not replace the exact formal pair.

---

## CODEX NOTICE — Stage-1 v0.5 sealed typed pre-C observation remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `c2174dd00e11b96f7ff1b187a2ea84853bfd8f42`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-CPU-STATIC`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_v17_pre_c_rehearsal.py:118)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-15_R09_B_TTT_v035_stage1_v17_pre_c_rehearsal_consumer_cpu_static_c2174dd_93a89ba.md`

Canonical review commit:
`0d7a2bfe3bf9d3f73f24615eda811dcc4a841902`

Current blockers: `1 HIGH`; Design/Authority: `0`; Production/implementation: `1 HIGH`; Evidence/identity: `0`; child/runtime: `0`.

Positive closure:
- the prior query/absence observation-identity blocker is closed: both remote queries and advertised-V2 carry raw length/SHA identities, output/designated absences are typed ordered `lexists=false` observations, and the frozen authority-ref literal is used;
- prior exact v0.5 paths, six-key environment, capability sealing, patch inverse, typed readback/core byte equality and terminal one-shot/no-retry behavior remain preserved;
- formal root tree binds `cosmos-framework` exactly to the declared reachable child.

HIGH 1 — V31/V1.7 inherited closure is still reduced rather than complete:
- `ClosureV1` still represents `.git` identity as opaque bytes and `.git/config` / local `V2` as bare bytes without the required explicit length/SHA identities;
- it has no fields for `selection`, `config`, `bootstrap`, `bootstrap_contract`, replay outer, canonical parser argv/raw identities;
- it omits the full V1.0 P0 root/path/blob tuple, P1 injected-object identities and owner-FD flag/value;
- it omits explicit frozen cwd/index/evidence targets and does not seal V31's complete injected source-object set / literal `ReplayBinding` binding;
- therefore an incomplete or foreign rehearsal can still satisfy the current static schema while violating the non-shrinkable inherited closure.

Required remediation — complete this in one pass:
- extend the typed rehearsal input/closure to contain every V1.7/V31 item above;
- bind each raw/argv/target/source object to the exact frozen identity, including length/SHA where required, exact ordering and allowlists;
- add direct CPU/static drift tests for every newly added field, all failing before consumer invocation;
- preserve the already-correct query/absence/capability/patch/readback/exact-once behavior.

No CPU/static closure is granted for this pair. v0.5 request construction/C/materialization, real I/O, child mutation, GPU and training remain forbidden.

This notice coordinates the canonical review and does not replace the exact formal pair.
