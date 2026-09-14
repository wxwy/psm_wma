# ChatGPT review — Stage-1 v1.7 request-instance recovery design v1.3

- Formal request ledger Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V13`
- Formal design declared Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN`
- Formal root: `1db75ffad55a5ab7f29a9bf3a8701842ca4c3807`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Verdict: `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_recovery_design_v1.3.md:3)`
- Blockers: `2 HIGH`; Design/Authority: `2 HIGH`; Production: `0`; Evidence: `0`; child/runtime: `0`.

## Formal target / Gitlink

This is a fresh formal pair relative to the previously reviewed recovery design `19181644aa7d8f08abfdc9c206f24d2dfc9acb1e / 93a89ba61306d840a008813f62f26a34d54850f4`.

The formal root tree independently resolves `cosmos-framework` as mode `160000` exactly equal to `93a89ba61306d840a008813f62f26a34d54850f4`, and that child commit is reachable in `wxwy/cosmos-framework`.

The immediate formal-root delta is one docs-only commit limited to `SESSION.md`, `TODO.md`, and `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_recovery_design_v1.3.md`. No project production code or child code changes in this formal target.

The reported v1.2 construction failure is consistent with the frozen one-shot lifecycle: C had begun, completed the allowlisted freshness snapshot and produced candidate bytes, but did not write the frozen pair. Treating that authority as consumed with no retry is the fail-closed interpretation. v1.3 correctly does not reuse it.

## Positive findings

1. The future request tuple remains the previously frozen authority tuple: formal parent `08d5828cdb4c12afa3b798ff01826c91ceb8755a`, child `93a89ba61306d840a008813f62f26a34d54850f4`, and sole output pair `...request_instance_v0.3.{json,md}`.
2. P0/P1 remain non-consuming and C remains one-shot/no-retry beginning before the first freshness observation.
3. The intended recovery direction is correct: candidate production, file creation and detached identity verification must all occur within the same consumed C rather than leaving stdout-only bytes for later reconstruction.
4. The design continues to prohibit materialization, launcher/runtime execution, source/checkpoint/manifest/data/cache I/O, downstream collection/receipt/publication, child/runtime mutation, GPU/CUDA/torchrun, training/evaluation/inference and LIBERO4IN1.

## HIGH 1 — exact Gate identity is contradictory between the formal design and the review ledger

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_recovery_design_v1.3.md:3`

The formal design declares:

`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN`

but the live `CODEX_INBOX` review request for this exact pair declares:

`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V13`.

The collaboration protocol treats the exact formal pair **and Gate** as the review authority. These two literals cannot both identify the same approval token. An approval under the ledger Gate would not be byte-identical to the Gate embedded in the reviewed design, while an approval under the design Gate would not match the delivered request record.

### Required remediation

Choose exactly one Gate literal and make it identical in:
- the formal v1.3 design;
- the live review request / `CODEX_INBOX`;
- `SESSION.md` / `TODO.md` coordination state;
- the requested final verdict record and future canonical review.

A version suffix may be used or omitted, but there must be one exact Gate identity for the exact formal pair.

## HIGH 2 — the producer→`apply_patch` handoff is not mechanically closed

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_recovery_design_v1.3.md:32`

v1.3 correctly says the producer must hold canonical JSON/Markdown raw bytes in memory and forbids a stdout-only candidate. However, it then names `apply_patch` as the only consumer without freezing the transformation from those raw bytes into the patch request that `apply_patch` actually consumes.

That leaves an authority gap between the producer bytes and the consumer input:
- `apply_patch` consumes patch text/operations, not the producer's opaque `(json_raw, markdown_raw)` byte tuple directly;
- the design does not define a deterministic patch encoder, escaping/newline rule, single-invocation grammar, patch raw length/SHA, or an equivalent structured API that consumes the producer value without re-materializing it in agent context;
- therefore a future executor can still manually copy/reconstruct/escape the producer bytes to form a patch, which is precisely a second handoff step capable of truncation or transcription drift;
- post-write verification would fail closed, but only **after** the sole C authority has been consumed and possibly after one half of the pair exists. That is safe but does not close the handoff design this Gate is specifically meant to repair.

### Required remediation

Freeze a mechanically exact consumer seam. For example:
1. define a deterministic in-memory encoder from `json_raw` and `markdown_raw` to one exact `apply_patch` input covering both files in a single consumer invocation;
2. bind that patch/input representation by exact byte length and SHA-256 before invocation;
3. require the consumer to accept only that bound representation and the two frozen paths, with no manual/context reconstruction or alternate encoding;
4. after the consumer returns, reopen both files and require byte-for-byte equality with the original producer raw bytes before canonical/sidecar checks;
5. define the failure residue policy explicitly if the single consumer invocation is not all-or-nothing. Any partial pair must remain terminal/no-retry and must not be accepted as a request.

An equivalent structured write API is acceptable if it directly consumes the producer bytes and is frozen with the same exactness. The key requirement is that the producer value itself, not a manually reconstructed patch, is the sole consumer authority.

## Boundary

No request construction is approved for `1db75ffad55a5ab7f29a9bf3a8701842ca4c3807 / 93a89ba61306d840a008813f62f26a34d54850f4`.

Still prohibited: materialization; launcher/materializer execution; source/checkpoint/manifest/data/cache I/O; collection/receipt/record/publication; child/runtime/config mutation; GPU/CUDA/torchrun; training; evaluation; inference; LIBERO4IN1.
