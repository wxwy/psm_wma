# ChatGPT Review — Stage-1 v1.7 request-instance design v0.2

- Formal root: `0831e0ba2dcb5c93e9069d2d20aca1790095dc97`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`
- Requested verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`

## Verdict

`APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`

Blockers: **0**
- Design/Authority: 0
- Production/Authority: 0
- Evidence/Scope: 0
- child/runtime: 0

## Pair / scope verification

- Formal root resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Relative to v0.1 formal root `218f5f6254e7e926ae2d9ad8fb8206d037a9cadf`, the technical remediation is docs-only: new v0.2 request-instance design plus `SESSION.md` / `TODO.md`; other differences are coordination/review bookkeeping.
- No child/runtime production bytes are changed.
- v1.6 authority remains consumed and cannot be reused.

## Prior blocker disposition

### CLOSED — construction-time read-only I/O authority ambiguity

v0.1 simultaneously said that no real I/O was authorized and required construction to take a same-round freshness/provenance snapshot from Git/filesystem/remote-ref state. v0.2 supersedes that wording with one explicit, closed construction-time I/O allowlist that becomes usable only after unanimous same-pair design approval.

The allowed observation surface is now exact and read-only:

1. frozen formal-parent commit/tree/blob identity plus launcher base raw bytes;
2. current `.git` identity and `.git/config` raw bytes;
3. the frozen local ref plus exactly one network query, `git ls-remote origin refs/heads/V2`, with command and complete raw result/length/SHA bound into the request;
4. absence-only checks for designated clean-root/index/ref/evidence/pending targets.

The design expressly forbids every other network/service access, source/checkpoint/manifest/data/cache content I/O, collection/receipt/record/package/publication, launcher/materializer execution, runtime/child mutation, GPU/CUDA/torchrun, training, evaluation, inference, and LIBERO4IN1.

## Frozen dependencies and construction closure

The design preserves the exact frozen dependencies:

- formal parent `08d5828cdb4c12afa3b798ff01826c91ceb8755a`;
- launcher base blob `af19a9eb66ecaf8bd0b92a48ab1867f105026658`, raw SHA-256 `8b0fad39857fb72e3a3eb317f4acf6f2d6e94e196935f52f07d6170e79c678dd`, bytes `18966`;
- closed replay implementation root `50b0bffeb4c94b0994d7c7bf705077fb51a9e48f` with frozen module/test identities;
- canonical parser `2336 / 1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333`;
- canonical outer payload `18875 / 658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8`.

Construction is limited to exactly one future root docs-only Markdown/JSON request pair at the frozen paths. The future request must use the frozen pure replay helper with injected verified formal-parent bytes, then take one same-round allowlisted zero-mutation snapshot and bind all enumerated provenance/freshness, parser/environment/owner-FD/replay/target and canonical whole-request JSON identities.

Fallback base, mixed parent, stale observation, inferred defaults, reordered argv/environment, duplicate owner-FD, request-byte mismatch, missing/extra allowlisted observations, and non-allowlisted I/O all remain fail-closed as `BLOCKED_AUTHORITY_NOT_CLOSED` before `os.execve`.

## Authority boundary

This approval authorizes only construction of **one** fresh docs-only exact Stage-1 v1.7 request instance under the v0.2 allowlist and fixed output paths.

It does **not** authorize:
- materialization or Stage-1 execution/retry;
- launcher/materializer execution;
- reuse/revival of v1.6 authority;
- source/checkpoint/manifest/data/cache/runtime I/O outside the explicit read-only allowlist;
- collection/receipt/record/package/publication;
- child/runtime mutation;
- GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1.

The constructed exact request must receive an independent same-pair three-party request review before it can grant a single Stage-1 attempt.
