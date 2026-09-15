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

- immediate prior live blob SHA: `7caed54b0a7a6a364f543e970812458b50a86422`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — ContractV05 consolidated closure still has one fixed-ref authority-binding blocker

Formal pair:
- root implementation SHA: `8bc6e93547a5a3f7db541f3843a6d36a32d23181`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-CPU-STATIC`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_v17_pre_c_rehearsal.py:379)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-15_R09_B_TTT_v035_stage1_v17_contract_v05_pre_c_cpu_static_8bc6e93_93a89ba.md`

Canonical review commit:
`ca3fcec60fae170fbf87301b4f14907489541283`

Current blockers: `1 HIGH`; Design/Authority: `0`; Implementation/authority binding: `1 HIGH`; Evidence/Scope: `0`; child/runtime: `0`.

Positive closure:
- the prior real-source-I/O blocker is closed with frozen in-memory replay-helper bytes;
- P0/P1 exact identities, literal ReplayBinding, exact v0.5 tuple, six-key environment, canonical byte witnesses, typed query/absence records, exactly-once retirement and terminal no-retry remain preserved;
- `ContractV05` and the C01-C15 matrix are present;
- formal root resolves and binds `cosmos-framework` exactly to the declared child.

HIGH 1 — local/remote fixed authority-ref absence is still only self-consistent, not bound to frozen truth:
- `_validate_closure()` checks only that both authority-absence predicates equal `authority_absent`, both targets are non-empty, and each raw record is self-consistent by length/SHA;
- a foreign non-empty target plus arbitrary foreign raw with recomputed length/SHA can therefore pass rehearsal;
- the current fixture uses generic `refs/local-authority` / `refs/remote-authority` targets, and there is no foreign-but-self-consistent negative witness for this class;
- this directly violates the convergence directive's exact-frozen-truth rule and contradicts matrix C08/C15 being marked PASS.

Required remediation — one class-wide pass:
- bind local and remote fixed authority-ref targets to the exact inherited frozen literals; non-empty is insufficient;
- keep live observation bytes as rehearsal-time truth, but only after their fixed ref/path/query identity is exact, then require C freshness equality to the sealed observation;
- add foreign-but-self-consistent negative tests for both authority-absence records, changing target and raw together with recomputed length/SHA, and prove pre-consumer fail-close;
- sweep all C01-C15 fixed identity fields for the same self-consistency-only pattern;
- update the matrix so every row includes the directive-required exact frozen expected literal/value/identity plus direct positive and foreign-self-consistent negative witnesses.

No CPU/static closure is granted for this exact pair. v0.5 request construction/C/materialization/source-evidence, all real I/O, child mutation, GPU and training remain forbidden.

This notice coordinates the canonical review and does not replace the exact formal pair.
