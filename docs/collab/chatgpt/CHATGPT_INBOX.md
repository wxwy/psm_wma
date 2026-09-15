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

- immediate prior live blob SHA: `1fd97062bc4c66c78a7ad05203c7935ad4ce7698`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Stage-1 v0.5 authority-binding remediation has one CPU/static evidence-scope blocker

Formal pair:
- root implementation SHA: `6c4e395f38591c4b27a5627c184fc739af968669`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-CPU-STATIC`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/test_stage1_v17_pre_c_rehearsal.py:54)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-15_R09_B_TTT_v035_stage1_v17_pre_c_rehearsal_consumer_cpu_static_6c4e395_93a89ba.md`

Canonical review commit:
`05d562823e934231046c8df71a95adeb46041ad8`

Current blockers: `1 HIGH`; Design/Authority: `0`; Production/implementation: `0`; Evidence/Scope: `1 HIGH`; child/runtime: `0`.

Positive closure:
- the previous authority-binding HIGH is closed: P0 raw bytes are pinned by exact length/SHA and computed Git blob OID, P1 eight injected objects are exact ordered identities, ReplayBinding exact base/owner/parser/source values are pinned, and foreign-but-self-consistent drifts fail before the consumer;
- formal root resolves and binds `cosmos-framework` exactly to the declared child;
- no new production-helper blocker was found.

HIGH 1 — the CPU/static unittest itself performs real source filesystem I/O:
- `tools/psm_wma/test_stage1_v17_pre_c_rehearsal.py:54` executes `Path("tools/psm_wma/stage1_v17_launcher_replay.py").read_bytes()`;
- the controlling v3.1 design requires pure in-memory CPU/static validation and explicitly forbids real `source` I/O; the live request repeats the same hard scope;
- therefore the reported 9/9 suite is not admissible closure evidence for this Gate even though the implementation logic is now correct.

Required remediation:
- replace that runtime source read with an already frozen in-memory zero-I/O fixture/literal whose exact raw/blob identities are checked through the same public production closure path;
- preserve all current P0/P1/ReplayBinding exact pins and negative drift tests;
- rerun the CPU/static suite with no real source/Git/network/data/cache I/O.

No CPU/static closure is granted for this pair. v0.5 request construction/C/materialization, all real I/O, child mutation, GPU and training remain forbidden.

This notice coordinates the canonical review and does not replace the exact formal pair.
