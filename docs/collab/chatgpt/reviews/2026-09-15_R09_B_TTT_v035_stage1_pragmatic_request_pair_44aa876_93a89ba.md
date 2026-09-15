# ChatGPT formal review — Stage-1 pragmatic request pair

- Formal root: `44aa8760630751668a5ec340ef017575c65e311d`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-PRAGMATIC-REQUEST-PAIR`
- Verdict: `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.5.json:1)`
- Blockers: 1 HIGH (Design/Authority)

## Verified

1. The formal root exists and its `cosmos-framework` Gitlink is exactly the declared child SHA; the child resolves independently.
2. The v0.5 JSON/Markdown pair is byte-bound: the Markdown names the JSON, length, SHA-256 and Git blob OID.
3. The JSON freezes the candidate materialization root `db6c4f93473e7ef58a294cff3fb8c692b100badd`, child SHA, six-key environment, exact FD input bytes/hashes, launcher/bootstrap identities, four tool paths/blob OIDs/SHA-256 values, same-round preflight facts, and the hard-stop request-pair construction semantics.
4. The candidate root exists. V25/V26/V27 host/session/IPC issues are not carried into this Gate merely because they were blockers in the earlier Gate.

## HIGH — Owner Override authority is not part of the exact formal evidence chain

The review request says this Gate is governed by `USER_OWNER_OVERRIDE_STAGE1_PRAGMATIC_EXECUTION_2026-09-15.md` and that this Owner Override supersedes V25/V26/V27 continuity and grants only one future Stage-1 materialization attempt. However, independent inspection of the formal root tree cannot resolve that named authority document, and the v0.5 JSON/Markdown request pair contains no canonical identity for the override (path + blob/SHA-256/content identity), no exact supersession clause, and no one-shot/non-retry authority identity.

Therefore the technical request is reproducible, but the authority transition is not independently reproducible from the exact formal pair: a reviewer cannot prove from `44aa876...` which immutable owner directive supersedes the inherited continuity gates, nor that the requested next authority is exactly one materialization attempt with no retry authority after failure/partial execution.

This is a Gate-level blocker, not a request-byte or tool-closure defect.

### Acceptance

Bind the Owner Override into the exact formal evidence chain, without changing the already-frozen technical request unless necessary:

- make the governing override an immutable, resolvable artifact for the formal pair (or otherwise provide a canonical immutable owner-authority object);
- bind its exact path/object identity and SHA-256/blob identity in the request authority metadata;
- state unambiguously that it supersedes only the named V25/V26/V27 host/session/IPC continuity requirements for this pragmatic Gate;
- freeze the next authority as exactly one Stage-1 materialization attempt, terminal on success/failure/partial/unknown, with no implicit retry or broader execution authority;
- keep all existing forbidden scope intact.

No materialization is approved by this review.
