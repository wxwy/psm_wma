# ChatGPT review — Stage-1 v1.7 request-instance recovery design v1.6

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V16`
- Formal root: `0a229ce3dfe5f6fbfb799b5813f09616d32088a4`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Verdict: `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_recovery_design_v1.6.md:17)`
- Blockers: `1 HIGH`; Design/Authority: `1 HIGH`; Production: `0`; Evidence/identity: `0`; child/runtime: `0`.

## Formal target / scope

This is a fresh formal pair relative to the previously reviewed request pair `696773a127e2dbb8c052f208cb9ee3a4ec9ce9cd / 93a89ba61306d840a008813f62f26a34d54850f4`.

The formal root resolves and its tree binds `cosmos-framework` as mode `160000` exactly equal to `93a89ba61306d840a008813f62f26a34d54850f4`. The root is docs/status-only for this Gate: the design file plus coordination records; there is no child/runtime implementation change.

The current design correctly treats the rejected v0.3 request and its consumed construction authority as non-reusable, freezes a new non-overlapping v0.4 JSON/Markdown pair, keeps P0/P1 non-consuming, makes C one-shot/no-retry, preserves the single strict UTF-8 `patch_raw -> patch_text -> apply_patch(patch_text)` consumer seam inherited from V15, and restores the exact six-key Git isolation environment plus detached canonicalization/five-field sidecar identity requirements.

Those positive changes close the three findings that were visible directly in the rejected v0.3 request, but they do not yet preserve the entire inherited construction closure.

## Authority chain used for this review

The controlling earlier request-instance design v0.5 explicitly froze that a future replacement request must carry a complete same-round zero-mutation snapshot, including:

- formal/base/replay identities;
- `.git` identity and `.git/config` raw bytes;
- local `V2`;
- two exact remote queries including command, timeout, return code, stdout/stderr raw bytes, lengths and SHA identities, plus the remote `V2` advertised raw value;
- local/remote fixed authority-ref absence;
- designated path absences;
- selection/config/bootstrap/contract raw bytes, canonical parser argv, six-key environment, owner-FD insertion, replay output, and cwd/index/evidence targets.

Later V1.0 froze the closed P0 object/literal authority and V15 froze the exact bytes-to-patch consumer seam. V1.6 may supersede only what it explicitly rewrites; it cannot silently drop v0.5 closure elements that were never superseded.

## HIGH 1 — V1.6 still shrinks the inherited C freshness/provenance closure

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_recovery_design_v1.6.md:17-26` (`## C 的不可缩减闭包`)

V1.6 says the C closure is “不可缩减”, but its enumerated mandatory JSON facts do not actually include several still-frozen v0.5 authority fields:

1. the `.git` object/directory identity itself;
2. the local `V2` value observed in the same zero-mutation round;
3. the remote `V2` advertised raw value as a separately bound provenance value, not merely the raw stdout of a query;
4. local fixed authority-ref absence;
5. remote fixed authority-ref absence.

The design does require `.git/config`, two remote query raw records, designated candidate/record/receipt/publication absences, P0/P1 identities, targets, six-key environment and canonical detached identity, but those are not equivalent to the missing facts above. In particular, “two remote query stdout raw bytes” does not itself freeze which extracted advertised `V2` value must be bound, and designated output/record absences do not replace the separately frozen authority-ref absence checks.

Because V1.6 expressly claims to restore an **unreduced** C closure, leaving these inherited facts implicit creates a second shrinkage path: a future v0.4 request could satisfy the literal V1.6 list while still omitting same-round Git repository/provenance/ref authority that v0.5 required. That would again make the later request unable to prove exact construction provenance and runtime freshness fail-close.

### Why existing evidence does not close this

- The current target is a design Gate, so `git diff --check` or docs-only scope cannot prove omitted authority semantics.
- V1.0's P0 literal authority closes immutable source acquisition, not the missing same-round `.git` / V2 / fixed-ref freshness facts.
- V15 closes only the byte-exact patch consumer seam; it does not supersede or remove v0.5 freshness/provenance fields.
- The rejected v0.3 request already demonstrated why a summarized/reduced closure is insufficient; this recovery design must freeze the full inherited set before another one-shot construction authority is granted.

### Acceptance

Revise the recovery design so the future canonical v0.4 JSON must, in the same zero-mutation C observation round, explicitly serialize and bind at minimum:

- `.git` identity;
- local `V2` raw/value identity;
- both exact remote query records **and** the extracted remote `V2` advertised raw value;
- local fixed authority-ref absence;
- remote fixed authority-ref absence;

in addition to every V1.6-listed field. State that these are inherited mandatory authority fields from v0.5 and cannot be inferred from query blobs, ambient state, history, or later reconstruction. Any mismatch or omission must fail closed before producer output.

No production or child/runtime blocker exists in this docs-only target.

## Verdict / boundary

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_recovery_design_v1.6.md:17)`

No v0.4 request construction authority is granted for `0a229ce3dfe5f6fbfb799b5813f09616d32088a4 / 93a89ba61306d840a008813f62f26a34d54850f4`.

Still prohibited: v0.4 construction under this pair; Stage-1 materialization/execution/retry; launcher/materializer execution; real source/checkpoint/manifest/data/cache I/O; collection/receipt/record/package/publication; child/runtime/config mutation; GPU/CUDA/torchrun; training; evaluation; inference; LIBERO4IN1.
