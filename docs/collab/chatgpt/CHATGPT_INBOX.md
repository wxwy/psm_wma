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

- immediate prior live blob SHA: `ed4834a0fa7d60effef9a11fa79caef0c044d722`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Stage-1 ContractV05 CPU/static pre-C Gate APPROVED TO CLOSE

Formal pair:
- root implementation SHA: `c99506295fed887a87670fc80fbdaf639baf5444`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-CPU-STATIC`

Verdict:
`APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_PRE_C_REHEARSAL_CONSUMER_CPU_STATIC`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-15_R09_B_TTT_v035_stage1_v17_contract_v05_pre_c_cpu_static_c995062_93a89ba.md`

Canonical review commit:
`8aaf59b50588c3190c6a888eea8d364f1ef2f32f`

Current blockers: `0`; Design/Authority: `0`; Production/implementation: `0`; Evidence/Scope: `0`; child/runtime: `0`.

Closure summary:
- the prior C08/C15 fixed authority-ref blocker is closed: `AUTHORITY_REF` is frozen to `refs/heads/authority/r09-b-ttt-v035-immutable-source-v1`; both local and remote authority-absence records require exact target/predicate before raw identity is accepted;
- both authority-absence records have direct foreign-target + foreign-raw + recomputed length/SHA negative witnesses and fail before consumer invocation;
- the C01-C15 matrix now names the controlling exact/frozen authority literals or rehearsal-sealed observation identities and points to positive/foreign-drift witnesses;
- prior P0/P1/ReplayBinding exact pins, frozen in-memory fixture, exact v0.5 paths, six-key environment, typed query/absence closure, canonical byte witnesses, capability/plan sealing, freshness-before-apply, exactly-once retirement, byte-exact post-write verification and terminal no-retry remain preserved;
- the formal root tree binds `cosmos-framework` exactly to the declared reachable child.

Scope reminder: this closes only the root CPU/static pre-C rehearsal/consumer Gate. It does not authorize v0.5 request construction/C execution, materialization, source-evidence collection/receipt closure, real consumer/Git/network/source/data/cache I/O, child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1.

This notice coordinates the canonical review and does not replace the exact formal pair.
