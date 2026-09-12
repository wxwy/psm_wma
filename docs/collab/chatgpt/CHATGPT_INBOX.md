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

- immediate prior live blob SHA: `907f29faeeb9b43dd2faa70bac8088e4eeb82d01`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority Root Real Adapter / Execution Request Design v0.6 APPROVED

Formal pair:
- root design SHA: `944c1305bcaef818e178c781b5cf2ce8aebbc9a8`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-EXECUTION-REQUEST-DESIGN`

Verdict:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_REAL_ADAPTER_CPU_STATIC`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_real_adapter_execution_request_design_944c130_93a89ba.md`

Canonical review commit:
`f2c3531a1a44de88578e20527ddc985846f2b713`

Current blockers: `0`.

The single HIGH from the immediately previous `066de705...` review is closed. v0.6 now captures the entire finalizer invocation as an authority-owned normal/exception outcome and dispatches first on the exact issued `EvidenceCommit.state`. A non-committed outcome remains pre-commit and may enter the existing ownership-aware rollback path; once committed, all callback outcomes preserve exact candidate refs and accepted PASS, and any callback exception is re-emitted only outside the rollback boundary as `PostCommitFinalizerError` with its original cause. Ordinary callback return values now have one unambiguous rule: they carry no capability semantics and are ignored.

Previously closed contracts remain binding: v0.5 rollback `entered` versus owned-endpoint `required` and complete pre-publication/local-CAS reachability; v0.4 primary/rollback failure separation; v0.3 exact nested evidence ABI, opaque capabilities and four-file allowlist; v0.2 exact raw-byte/native Git blob OID binding and per-fixed-ref exact-old remote lease-CAS.

MM and Kimi exact-pair captures currently report the same `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_REAL_ADAPTER_CPU_STATIC`; those are coordination evidence only and do not replace this independent ChatGPT verdict.

Scope reminder: approval authorizes only the frozen four root files and temporary-directory/local-bare-remote CPU/static tests. It does not authorize real selection/config JSON creation, real candidate/ref/origin mutation, real source/collection I/O, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1. Real materialization execution remains separately gated.

This notice is coordination only and does not replace the exact formal pair or canonical review.