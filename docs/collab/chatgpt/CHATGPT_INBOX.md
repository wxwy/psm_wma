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

- immediate prior live blob SHA: `32c4040b1fe1dbc5594c45a825e132773a162ddd`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Stage-1 v1.7 request-instance design REQUEST_CHANGES

Formal pair:
- root design SHA: `218f5f6254e7e926ae2d9ad8fb8206d037a9cadf`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_design_v0.1.md:5)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_stage1_v17_request_instance_design_218f5f6_93a89ba.md`

Canonical review commit:
`fc62403c51c9c96e2b484a4974ab3a62c00d87c6`

Current blockers: `1 HIGH`; Design/Authority: `1 HIGH`; Production/Authority: `0`; Evidence/Scope: `0`; child/runtime: `0`.

Positive disposition:
1. Formal root resolves Gitlink exactly to reachable child `93a89ba...`; child/runtime production bytes are unchanged.
2. v1.6 authority is explicitly consumed/non-reusable.
3. The design correctly separates design approval from a future docs-only exact request instance and from any Stage-1 execution authority.
4. Frozen dependencies are explicit: formal parent `08d5828...`, launcher base `18966 / 8b0fad...`, closed replay root `50b0bff...`, and canonical parser/outer identities.
5. The future request is required to bind a same-round zero-mutation freshness snapshot, canonical request bytes/SHA, exact parser/environment/owner-FD/replay identities, and to fail-close stale/fallback/mixed-parent/reordered/duplicate/request-byte drift.

Remaining HIGH — construction I/O authority is self-contradictory:
- line 5 states this design does not authorize materialization **or any real I/O**;
- the Construction contract later requires the approved constructor to read the formal Git object/tree, local `.git` identity/config bytes, fixed local/remote refs, and designated path absences for the same-round freshness snapshot;
- those are real read-only Git/filesystem provenance/freshness I/O (and a remote-ref observation may involve network I/O).

Exact remediation:
1. Replace the blanket `任何真实 I/O` prohibition with an explicit construction-time read-only allowlist.
2. Allow only the enumerated provenance/freshness observations needed for the one docs-only request instance: formal Git object/tree identity/bytes, local `.git` identity/config bytes, frozen local/remote ref observations, and designated path-absence checks.
3. State explicitly whether the remote-ref observation may contact the configured Git remote; if yes, limit it to that exact read-only query and bind its raw result; if no, define the exact non-network authority source.
4. Preserve zero mutation and continue to prohibit source/checkpoint/manifest/data/cache content I/O, runtime/service I/O, directory/ref/artifact creation, launcher/materializer execution, child/runtime mutation, GPU/CUDA/torchrun, training/evaluation/inference and LIBERO4IN1.
5. Preserve one-request-only + fresh exact-pair request review before any single Stage-1 attempt can be authorized.

Scope reminder: this verdict authorizes only docs-only design remediation. It does not authorize request construction, Stage-1 retry/materialization, launcher execution, downstream collection/receipt/record/package/publication, child/runtime mutation, GPU or training. v1.6 authority remains consumed.

This notice coordinates the canonical review and does not replace the exact formal pair.
