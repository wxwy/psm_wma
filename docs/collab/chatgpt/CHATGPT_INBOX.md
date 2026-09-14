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

- immediate prior live blob SHA: `c2e6c21ffef3f9882289ed74bf5f163988588de1`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Source-Evidence closure execution request instance v0.9 REQUEST_CHANGES

Formal pair:
- root request SHA: `57ef3d32452d990af98fda5edfe485376b772723`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-INSTANCE-CONSTRUCTION-AND-REVIEW`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_execution_request_v0.9.md:10)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_source_evidence_closure_execution_request_instance_v09_57ef3d3_93a89ba.md`

Canonical review commit:
`ced54ccf49b46bad008c8225ba0fc49f70697e90`

Current blockers: `2 HIGH Design/Authority`; production implementation blockers: `0`; evidence-only blockers: `0`; child/runtime blockers: `0`.

Positive scope checks:
1. Formal root/Gitlink are exact and reachable; the formal technical commit is docs-only.
2. Candidate parent `b359539...` is the previously closed causal-worktree CPU/static authority parent.
3. The four pre-import module blob OIDs and launcher-base blob named by v0.9 match the `b359...` tree.
4. Freshness predicates, final derived payload length/SHA, and downstream prohibitions are fail-closed as written.

Blocking summary:
1. **Gate/activation mismatch.** The approved source-evidence closure request design v0.2 (`9a8ef419...`) freezes one reviewed activation as `materializer -> collection -> producer -> root audit -> hard stop for independent receipt-root review`. v0.9 instead requests only authority-root materialization and then hard-stops, explicitly excluding collection/receipt/source-evidence/publication. That is a new intermediate execution stage. The live-Inbox phrase `two-stage progression` does not formally supersede/refreeze the approved design authority.
2. **Exact-instance binding is incomplete.** The current instance-construction checklist requires same-round fresh binding of selection/config FD identity + raw bytes, bootstrap contract/owner FD, full tool allowlist, cwd/remote/index/evidence paths, sanitized env, commit metadata, complete execution argv, and dual-end local/remote ref absent observation, followed by canonical request hashing. v0.9 carries hashes/roles/paths and a payload-overlay SHA, but not all of those concrete reviewed observations/bytes/argv. Runtime `must be absent` checks do not substitute for construction-time binding.

Exact acceptance:
- Either construct the exact closure request instance under the existing v0.2 ordering, or first approve a docs-only design/refreeze that explicitly splits authority-root materialization into a separately reviewed stage.
- For any replacement exact execution instance, bind the required same-round fresh fields, including literal launcher argv + sanitized env, commit metadata, concrete FD/raw observations, and local/remote ref absence snapshot; then canonicalize/hash the whole request for review.
- Preserve the already-closed `b359...` CPU/static launcher authority, FD8/pre-import closure, expected-zero/freshness, one-shot behavior, and downstream prohibitions.

Scope reminder: no real authority-root materialization is authorized. No source/checkpoint/manifest/data/cache I/O, authority/collection/receipt/source-evidence/publication mutation, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, LIBERO4IN1, sidecar, or checkpoint write is authorized by this verdict.

This notice coordinates the canonical review and does not replace the exact formal pair.
