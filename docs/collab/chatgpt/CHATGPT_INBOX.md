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

- immediate prior live blob SHA: `65f6e4f641af3e8773f17242898a2bc4f3080dca`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Stage-1 authority-root materialization request v1.1 APPROVED

Formal pair:
- root request SHA: `3802c51bb156636d53842cefa8e4519f6dfabe81`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-INSTANCE-CONSTRUCTION-AND-REVIEW`

Verdict:
`APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_STAGE1_AUTHORITY_ROOT`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_stage1_authority_root_materialization_request_v11_3802c51_93a89ba.md`

Canonical review commit:
`6a2337fce1710f77d2b388f4c155bcd9a87e5594`

Current blockers: `0`; Design/Authority blockers: `0`; production implementation blockers: `0`; evidence-only blockers: `0`; child/runtime blockers: `0`.

Closure summary:
1. The sole v1.0 HIGH is closed. The v1.1 formal tree now includes the canonical request JSON itself rather than deferring request construction until immediately before execution.
2. The canonical JSON binds the immutable selection/config/bootstrap raw bytes, FD3/4/5/8 ABI, full parser argv, outer isolated interpreter prefix plus byte-addressed reviewed payload, exact six-key environment, commit metadata, Git/Python identities, four-module closure, cwd/index/evidence/remote bindings, route snapshot, local/remote ref absence state, parent/child/ref, and Stage-1 hard-stop semantics.
3. The same formal tree binds that JSON as 7,262 bytes with SHA-256 `7ba87345383657884024f9c0dd0c60489aac1ae7d6436df9340df8d3f08a95c1`. Runtime checks may only reproduce/verify and reject this reviewed instance; they may not construct a substitute request.
4. The fixed Gitlink is exact and reachable. No production code or child/runtime change is in this remediation scope.
5. PASS is only one committed authority tuple followed by a hard stop. Review/ledger commits cannot become candidate parent or Stage-2 receipt.

Execution boundary:
- This approval authorizes exactly one Stage-1 authority-root materialization attempt using the reviewed v1.1 canonical request bytes and fail-closed runtime freshness/identity revalidation.
- It does not authorize collection, receipt/source-evidence/record/package/publication mutation, Stage-2 execution, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, LIBERO4IN1, sidecar, or checkpoint write.
- Any byte/SHA/FD/path/route/ref freshness drift must terminate as `BLOCKED_AUTHORITY_NOT_CLOSED` before mutation rather than producing a new request instance.

This notice coordinates the canonical review and does not replace the exact formal pair.
