# ChatGPT review — Stage-1 v1.7 request-instance recovery design v1.5

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V15`
- Formal root: `b9a460330a2dc4ff1b9d034ae4986fa490e74ad7`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`
- Blockers: `0`; Design/Authority: `0`; Production: `0`; Evidence: `0`; child/runtime: `0`.

## Formal target / Gitlink

This is a fresh formal pair relative to the previously reviewed V14 target `cb80b88c86b2af19c6d677e630a0615c5b451626 / 93a89ba61306d840a008813f62f26a34d54850f4`.

The exact formal commit `b9a460330a2dc4ff1b9d034ae4986fa490e74ad7` adds only `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_recovery_design_v1.5.md`; later `SESSION`/`TODO` and review-request commits are bookkeeping and are not part of the formal technical target.

The formal-root tree independently resolves `cosmos-framework` as mode `160000` exactly equal to `93a89ba61306d840a008813f62f26a34d54850f4`; that child commit is reachable in `wxwy/cosmos-framework`.

## Inherited V14 authority remains intact

V15 explicitly preserves the V14 future tuple, P0/P1/C lifecycle, single-consumer contract and terminal partial-residue policy. Therefore the already-reviewed V14 constraints remain authoritative unless V15 narrows them further:

- the consumed prior construction authorities remain exhausted and are not reused;
- P0/P1 remain non-consuming;
- C begins before its first freshness observation and is one-shot/no-retry;
- only the frozen docs-only v0.3 JSON/Markdown pair may be created;
- the single consumer remains the only write path;
- post-write equality and detached/canonical identity checks remain mandatory;
- any consumer/partial-residue/equality failure remains terminal and non-retryable.

V15 does not broaden construction into materialization or runtime execution.

## CLOSED — bytes → text consumer type seam

V14 froze a byte-exact `patch_raw` authority but expressed the consumer abstractly as `apply_patch(patch_raw)`. V15 closes the remaining type ambiguity by defining exactly one strict conversion:

`patch_text = patch_raw.decode("utf-8", "strict")`

and exactly one consumer call:

`apply_patch(patch_text)`.

Before the call, V15 requires `patch_text.encode("utf-8") == patch_raw` and binds both byte-domain and re-encoded text-domain length/SHA identities. No alternate bytes/string conversion, manual/context reconstruction, escaping, formatting, stdout reconstruction, shell redirection, Python file write or temporary-file path is permitted.

Thus the consumer string is not an independently reconstructed authority: it is a single strict UTF-8 view of the already-bound producer bytes, with exact round-trip equality required before consumption.

## CLOSED — exact LF / empty-line round trip

V15 replaces the V14 `raw.splitlines()` encoder with the exact line rule:

`lines(raw) = raw[:-1].split(b"\n")`

under the frozen preconditions that each producer raw value is UTF-8, CR-free and LF-terminated. Each encoded payload line receives exactly one leading `+` and one trailing LF.

The specified inverse removes exactly one leading `+`, joins payload lines with `\n`, and appends exactly one final LF. This is byte-invertible for the required cases, including:

- an ordinary final content line;
- an empty content line;
- consecutive empty lines.

The design also requires the actual `json_raw` and `markdown_raw` to pass the same inverse witness before `patch_raw` is derived, so the fixture proof is not detached from the real producer values.

After the sole `apply_patch(patch_text)` call, C still requires both designated files to equal the original producer raw bytes byte-for-byte. Any conversion, witness, consumer, residue or equality failure is terminal/no-retry.

## Gate / coordination consistency

The current formal design and live review request use the same exact Gate literal:

`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V15`.

The current coordination state also records V15 as REVIEW and describes exactly the same strict UTF-8 conversion and line-encoder witness acceptance scope. No stale V14 token is being used as the authority for this formal pair.

## Verdict

`APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`

No current blocker remains for this exact V15 recovery-design pair.

## Scope reminder

This approval is narrow: after the required same-pair multi-review approval condition is satisfied, it permits exactly one future docs-only request-pair construction under the inherited V14 contract plus the V15 type/round-trip seam, followed by independent exact-pair request review.

It does **not** authorize materialization, Stage-1 runtime execution or retry, launcher/materializer execution, source/checkpoint/manifest/data/cache I/O outside the separately approved construction allowlist, collection/receipt/record/publication, child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.
