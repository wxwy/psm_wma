# ChatGPT review — Stage-1 v1.7 request-instance recovery design v1.4

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V14`
- Formal root: `cb80b88c86b2af19c6d677e630a0615c5b451626`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`
- Blockers: `0`; Design/Authority: `0`; Production: `0`; Evidence: `0`; child/runtime: `0`.

## Formal target / Gitlink

This is a fresh formal pair relative to the previous recovery-design target `1db75ffad55a5ab7f29a9bf3a8701842ca4c3807 / 93a89ba61306d840a008813f62f26a34d54850f4`.

The only authoritative v1.4 formal root is `cb80b88c86b2af19c6d677e630a0615c5b451626`; the earlier ledger transcription `cb80b88c69e9f477d8ec08fa6c6f8a4bb57a4a0a` is explicitly superseded and is not a review target.

The formal root tree independently resolves `cosmos-framework` as mode `160000` exactly equal to `93a89ba61306d840a008813f62f26a34d54850f4`, and that child commit is reachable in `wxwy/cosmos-framework`.

The formal-root delta is docs-only and limited to `SESSION.md`, `TODO.md`, and `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_recovery_design_v1.4.md`. No project production code or child code changes in this target.

## CLOSED — prior HIGH 1: Gate identity mismatch

v1.3 declared the unversioned recovery Gate while its review ledger used a `...V13` Gate. v1.4 closes that ambiguity by freezing exactly one Gate literal:

`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V14`

The formal design uses that exact literal, the formal coordination state uses the same V14 identity, and the corrected live review request uses the same Gate. No old `...RECOVERY-DESIGN` or `...V13` token may substitute for it.

## CLOSED — prior HIGH 2: producer→consumer handoff was not mechanically closed

v1.4 now freezes the exact future write seam rather than only naming `apply_patch` abstractly.

The producer constructs `json_raw` and `markdown_raw` in memory and deterministically derives one `patch_raw` using an explicit two-file `*** Add File` encoder. Before the consumer invocation it binds the complete patch input as `(len(patch_raw), sha256(patch_raw), patch_raw)` together with the JSON/Markdown raw identities and JSON Git-blob preimage OID.

The consumer authority is singular: exactly one `apply_patch(patch_raw)` invocation for the two already-frozen paths. The design forbids manual/context reconstruction, alternate encodings, stdout reconstruction, shell redirection, Python file writes, temporary files and alternate patch grammar.

After the consumer returns, C may read only the two designated paths and must prove byte-for-byte equality with the original producer `json_raw` and `markdown_raw`, then re-check canonical JSON, detached Markdown identity, JSON length/SHA and Git-blob preimage OID. No second write is allowed.

The non-atomic case is also fail-closed: zero-file, one-file, consumer failure, or any equality/identity failure becomes terminal `BLOCKED_AUTHORITY_NOT_CLOSED:request-patch-handoff`; any residue is preserved as failure evidence and cannot be deleted, overwritten, completed, repaired or retried under the consumed authority.

This directly satisfies the prior exact acceptance: deterministic encoder, bound consumer-input identity, one consumer invocation, post-write byte equality, and explicit terminal partial-residue semantics.

## Lifecycle / scope consistency

The earlier consumed v1.2 construction authority remains permanently exhausted and is not reused. P0/P1 remain non-consuming; a future C may begin only after fresh same-pair three-party approval and still consumes before its first freshness observation. PASS can create only the frozen docs-only `...request_instance_v0.3.{json,md}` pair and must then hard-stop for independent exact-pair request review.

No current Production, Evidence, child/runtime, or scope blocker is introduced by v1.4.

## Verdict

`APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`

This verdict closes only the V14 docs-only recovery-design Gate. It does not authorize materialization, launcher/materializer execution, source/checkpoint/manifest/data/cache I/O, collection/receipt/record/publication, child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.
