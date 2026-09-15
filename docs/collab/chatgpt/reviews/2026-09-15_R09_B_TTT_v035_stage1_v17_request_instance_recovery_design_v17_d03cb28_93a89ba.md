# ChatGPT review — Stage-1 v1.7 request-instance recovery design v1.7

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V17`
- Formal root: `d03cb28ca138090f50adc09d4e810713457353af`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`
- Blockers: `0`; Design/Authority: `0`; Production: `0`; Evidence/identity: `0`; child/runtime: `0`.

## Formal target / scope

This is a fresh formal pair relative to the previously reviewed V16 recovery-design pair `0a229ce3dfe5f6fbfb799b5813f09616d32088a4 / 93a89ba61306d840a008813f62f26a34d54850f4`.

The formal root resolves and changes exactly three root paths for this Gate: `SESSION.md`, `TODO.md`, and `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_recovery_design_v1.7.md`. Its formal tree binds `cosmos-framework` as mode `160000` exactly equal to `93a89ba61306d840a008813f62f26a34d54850f4`; that child commit resolves in `wxwy/cosmos-framework`. No child/runtime implementation change is part of this target.

## Authority chain / delta reviewed

The controlling request-instance design v0.5 froze the full fresh same-round zero-mutation construction closure. V1.0 froze the closed P0 immutable-object/literal authority. V15 froze the strict byte-exact `patch_raw -> patch_text -> exactly one apply_patch(patch_text)` consumer seam. V16 preserved those rules and repaired the six-key environment, raw closure class, detached canonical JSON/Markdown identity, new non-overlapping v0.4 output pair, and one-shot/no-retry lifecycle, but V16 still omitted five inherited v0.5 provenance/freshness fields.

The prior ChatGPT V16 review therefore required the future canonical v0.4 JSON to explicitly bind, in the same zero-mutation C observation round, at minimum:

1. `.git` identity;
2. local `V2` raw/value identity;
3. both exact remote-query records plus separately extracted remote `V2` advertised raw value;
4. local fixed authority-ref absence;
5. remote fixed authority-ref absence;

and required these fields to be non-inferable from query blobs, ambient state, history, or later reconstruction, with omission/drift failing closed before producer output.

## Closure finding

V17 closes that exact HIGH without weakening prior authority:

- `.git` object/directory identity is now mandatory in the same zero-mutation round together with `.git/config` raw bytes and local `V2` raw value/length/SHA identity;
- the two and only two permitted remote queries remain fully bound by argv, timeout, return code, stdout/stderr raw bytes, lengths and SHA identities, and the V2 query additionally requires a separately extracted advertised `V2` raw value with its own length/SHA identity;
- local and remote fixed authority-ref absence are now explicit mandatory authority facts, each binding the observed path/ref, complete raw result, length/SHA and explicit success/absence predicate; they may not be inferred from designated-path absence, the remote-V2 query, a prior round or the environment;
- V17 explicitly states that the v0.5 same-round zero-mutation provenance closure remains fully effective and cannot be reduced to query blobs, ambient state, historical records or later reconstruction;
- mismatch/omission in fields, query order/count, timeout, raw bytes, identities, authority absences, environment or designated absences fail-closes before producer output;
- remote `V2` remains construction provenance only; it is not converted into a moving-branch runtime-equality condition.

The rest of the inherited closure remains intact: selection/config/bootstrap/bootstrap_contract/replay/parser raw authority, full P0 root/path/blob tuples, P1 injected-object identities, owner-FD flag/value, cwd/index/evidence and designated output/record/receipt/publication absences, exact six-key Git isolation environment, canonicalization literal, five-field Markdown sidecar identity, strict single patch consumer, byte-for-byte post-write verification, non-overlapping v0.4 pair, P0/P1 non-consuming lifecycle, one-shot C, terminal residue semantics and permanent no-retry.

No new contradiction was introduced in the reviewed delta. The design Gate remains docs-only and grants no materialization or runtime execution authority.

## Verdict / boundary

`APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`

This approval is bound only to exact formal pair `d03cb28ca138090f50adc09d4e810713457353af / 93a89ba61306d840a008813f62f26a34d54850f4` and Gate `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V17`.

Authorization remains narrow: after the required same-pair multi-review approval condition is satisfied, exactly one future docs-only v0.4 request-pair construction is permitted under the frozen authority, followed by an independent exact-pair request review.

Still NOT authorized: Stage-1 materialization/execution/retry; launcher/materializer execution; real source/checkpoint/manifest/data/cache I/O outside the separately frozen construction observation allowlist; collection/receipt/record/package/publication; child/runtime/config mutation; GPU/CUDA/torchrun; training; evaluation; inference; LIBERO4IN1.
