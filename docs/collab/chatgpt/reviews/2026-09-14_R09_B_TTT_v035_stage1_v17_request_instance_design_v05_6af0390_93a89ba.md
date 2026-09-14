# ChatGPT Review — Stage-1 v1.7 request-instance design v0.5

## Formal pair

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`
- Root: `6af03900ab4080c6437a4aa4154ebec50b6617ef`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`

## Scope / ancestry

- Formal root immediate parent is `4ae4824e8b3315a31c11c9edcacebd1c96caad0e`.
- Exact formal delta is only `SESSION.md`, `TODO.md`, and `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_design_v0.5.md`.
- The earlier `AGENTS.md` change seen when comparing from an older review-notification HEAD is not part of this formal root commit.
- Formal root Gitlink resolves exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`; child/runtime bytes are unchanged.

## Findings

### 1. Detached whole-JSON identity binding is mechanically closed

v0.5 correctly replaces the impossible self-embedded whole-file SHA requirement with a non-circular request-pair binding:

- future JSON has one canonical raw-byte representation: UTF-8, recursively sorted keys, compact separators, no extra whitespace, exactly one trailing newline;
- JSON must declare the canonicalization literal and must not contain its own whole-file length/SHA;
- sibling Markdown must bind the JSON relative filename, canonical byte length, SHA-256, canonicalization literal, and the JSON blob OID from the exact request formal tree;
- verifier first reserializes the JSON object and requires byte-for-byte equality with the committed raw JSON, then validates all five Markdown sidecar fields including the formal-tree blob identity;
- missing/extra/mismatched/self-identity/path/blob conditions fail before freshness/preflight/exec as `BLOCKED_AUTHORITY_NOT_CLOSED:request-identity`.

This is non-circular and mechanically verifiable because the JSON blob OID is computable before the Markdown blob is created, while the exact formal root subsequently fixes both blobs in one immutable tree.

### 2. Complete closure is preserved, not weakened

v0.5 explicitly retains the full v0.3/v0.4 request closure. A replacement request must still bind, from a new same-round zero-mutation observation:

- formal/base/replay identities;
- `.git` identity and `.git/config` raw bytes;
- local `V2`;
- both exact remote-query commands, timeout, return code, stdout/stderr raw bytes, lengths, hashes, and advertised V2 raw value;
- local/remote fixed authority-ref absence;
- designated path absences;
- selection/config/bootstrap/contract raw bytes, lengths, and hashes;
- canonical parser argv plus length/hash;
- exact six environment key/value pairs;
- owner-FD insertion, replay output, and cwd/index/evidence targets.

The previous v0.2 request's incomplete closure therefore cannot be reused as satisfying v0.5.

### 3. Freshness semantics are now compatible with a moving collaboration branch

v0.5 preserves the corrected rule that remote `V2` is construction provenance only. The observed advertised commit must be an ancestor of the future exact request formal root, but runtime does not require equality with a naturally moving collaboration branch.

Fixed authority-ref absence and designated path absences remain runtime freshness facts and must fail closed on drift. Historical v0.2 observations are explicitly forbidden from being reused under a new timestamp; the replacement request requires a new same-round observation.

### 4. Authority boundary remains design-only

This approval authorizes only construction of one new docs-only replacement request pair under the frozen two-query allowlist. The resulting request must undergo a new independent exact-pair three-party review.

This design does not authorize launcher/materializer execution, Stage-1 materialization/retry, source/checkpoint/manifest/data/cache/runtime I/O, downstream collection/receipt/record/package/publication, child/runtime mutation, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1.

The future request may grant at most one exact Stage-1 attempt after its own approval, with zero-mutation preflight fail-close, authority-tuple hard stop, and permanent no-retry after failure/consumption.

## Blockers

- Design/Authority: 0
- Request/Authority: 0 at this design stage
- Production/Authority: 0
- Evidence/Scope: 0
- child/runtime: 0

## Final verdict

`APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`
