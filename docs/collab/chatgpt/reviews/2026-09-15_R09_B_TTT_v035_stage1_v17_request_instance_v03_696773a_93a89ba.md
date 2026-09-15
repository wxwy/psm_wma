# ChatGPT review — Stage-1 v1.7 request instance v0.3

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-CONSTRUCTION-AND-REVIEW`
- Formal root: `696773a127e2dbb8c052f208cb9ee3a4ec9ce9cd`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Verdict: `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.3.json:1)`
- Blockers: `3 HIGH`; Design/Authority: `2 HIGH`; Production: `0`; Evidence/identity: `1 HIGH`; child/runtime: `0`.

## Formal target / scope

This is a fresh formal pair relative to the approved V15 recovery-design target `b9a460330a2dc4ff1b9d034ae4986fa490e74ad7 / 93a89ba61306d840a008813f62f26a34d54850f4`.

The formal request root is exactly one commit after the observed construction parent `21a1d5afb16e8e04cc052bc5993cabc4a52a2905` and changes exactly two files:

- `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.3.json`
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.3.md`

The formal root tree resolves `cosmos-framework` as mode `160000` exactly equal to `93a89ba61306d840a008813f62f26a34d54850f4`; that child commit is reachable in `wxwy/cosmos-framework`. No production or child code changes are part of this target.

Positive findings:

- the request preserves the frozen authority parent `08d5828cdb4c12afa3b798ff01826c91ceb8755a` and child Gitlink;
- the constructed request commit parent is exactly the local/remote V2 value recorded by the request snapshot;
- the two frozen v0.3 sibling paths are the only formal-root delta;
- the Markdown-declared JSON formal-tree blob `4eb4b8bdfa51ac2e9db846ad4ec2c3262ab4b1ac` matches the actual JSON blob in the formal root;
- the pair remains docs-only and states a hard stop for independent exact-pair review.

These positive facts do not close the frozen request-authority contract below.

## HIGH 1 — the canonical JSON does not contain the complete frozen C snapshot / closure authority

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.3.json:1`

The frozen v0.5/v0.6/v0.7 contract, explicitly inherited by the later recovery designs without weakening, requires the request JSON to carry the complete same-round zero-mutation authority facts, including raw values needed to prove the exact construction state. The current v0.3 JSON keeps only a reduced summary and therefore cannot serve as the exact request authority for materialization.

Concrete omissions / reductions include:

- `.git/config` is reduced to byte length + SHA-256; the required raw config bytes are absent;
- the two remote-query records omit the frozen timeout and stdout/stderr byte lengths; the contract requires command, timeout, return code, raw streams, lengths and SHA identities;
- `selection`, `config`, `bootstrap`, `bootstrap_contract` and canonical parser argv are reduced to length/SHA summaries; the frozen closure requires their raw bytes / exact argv authority, not only digests;
- the P0 source identities do not bind the full authorized root/path/blob tuples for base/replay/projection/adapter acquisition;
- the explicit owner-FD insertion is absent;
- the frozen `cwd` / `index` / `evidence` targets are absent;
- inherited designated candidate/record/receipt/publication absence authority is not represented;
- the replay/closure authority is therefore not complete enough for a later verifier to distinguish the approved construction state from a digest-equivalent or incompletely observed request.

This violates the frozen rule that the future request must not shrink the v0.5–v1.0 closure and must bind every allowlisted observation required for the later Stage-1 pre-mutation fail-close.

### Acceptance

Do not patch or overwrite this v0.3 pair under the consumed construction authority. A replacement requires a new docs-only recovery/construction authority with newly frozen output paths, then one fresh construction that serializes the complete inherited C snapshot/closure, including the exact raw facts and all required timeout/length/FD/target/absence identities, followed by a new exact-pair request review.

## HIGH 2 — `freshness.environment` substitutes ambient shell metadata for the frozen six-key execution environment

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.3.json:1`

The request currently binds:

- `LANG=en_US.UTF-8`
- `LC_ALL=en_US.UTF-8`
- `PWD=/disk/rl/psm_wma`
- `SHELL=/bin/zsh`
- `TZ=Asia/Shanghai`
- `USER=root`

That is not the frozen six-key environment used by the authority launcher and retained by the request contract. The frozen launcher authority is exactly:

- `GIT_CONFIG_GLOBAL=/dev/null`
- `GIT_CONFIG_NOSYSTEM=1`
- `GIT_CONFIG_SYSTEM=/dev/null`
- `GIT_NO_REPLACE_OBJECTS=1`
- `LANG=C`
- `LC_ALL=C`

Those values are execution-isolation authority, not incidental host metadata. Replacing them with ambient shell/process values severs the request from the reviewed Git/config/replacement-object isolation semantics and would make a later materialization approval non-exact.

### Acceptance

A freshly authorized replacement request must bind the exact frozen six key/value pairs above, with no substitution by ambient `PWD`/`SHELL`/`TZ`/`USER` values. Any mismatch must fail closed before request emission/materialization.

## HIGH 3 — detached canonical JSON identity is incomplete

**Locations:**

- `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.3.json:1`
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.3.md:6`

The frozen v0.5/v0.6 identity contract requires:

1. JSON to contain an exact `canonicalization` field declaring UTF-8, recursive sorted keys, compact separators and exactly one terminal LF; and
2. Markdown to bind five sibling-JSON identity fields: relative filename, whole raw byte length, SHA-256, the same canonicalization literal, and formal-tree Git blob OID.

The formal JSON has no `canonicalization` field. The Markdown binds the JSON path, byte length/SHA and blob OID, but omits the canonicalization literal. Therefore the detached sidecar does not satisfy the five-field identity contract and a later verifier cannot establish from the request itself that the reviewed raw bytes are the unique frozen canonical representation.

The actual JSON blob OID does match the Markdown's blob value, so this finding is specifically about the missing canonicalization authority, not a blob mismatch.

### Acceptance

The freshly authorized replacement JSON must carry the exact canonicalization literal and the sibling Markdown must bind all five required identity fields. Mechanical verification must reserialize the JSON and require byte-for-byte equality before any later freshness/preflight/materialization step.

## Verdict / boundary

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.3.json:1)`

No materialization authority is granted for `696773a127e2dbb8c052f208cb9ee3a4ec9ce9cd / 93a89ba61306d840a008813f62f26a34d54850f4`.

Production implementation and child/runtime code have no blocker in this docs-only target because they are not changed by the formal root. The current blockers are request Design/Authority and detached request identity only.

Still prohibited: Stage-1 materialization/execution/retry; launcher/materializer execution; real source/checkpoint/manifest/data/cache I/O; collection/receipt/record/package/publication; child/runtime/config mutation; GPU/CUDA/torchrun; training; evaluation; inference; LIBERO4IN1.
