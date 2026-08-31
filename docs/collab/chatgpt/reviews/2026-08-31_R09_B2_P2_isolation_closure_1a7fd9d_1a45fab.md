# R09-B2 P2 Non-mutating Capture Closure Review

- Request: `b89b37b7b76f2f5c3ef09ec5b2efc1e1f41ab82c`
- Evidence/root: `1a7fd9dff06bca7333be8c3ef392df6af27ff24a`
- Recorded clean implementation root: `d8455a61d293bb3d84a60877c73044637e07ddb7`
- Submodule/Gitlink: `1a45fab50bf22ca454eceb77d70cd94fb4c66f44`

## Verdict

`APPROVE_TO_CLOSE_B2_P2`

P2 is approved only as the CPU-only non-mutating capture/isolation contract. This does not authorize B2-T, GPU/runtime capture, model/VAE/optimizer loading, training, evaluation/inference/closed-loop, or P3-P5.

## Review findings

The three blockers from the previous review are closed:

1. **Isolation is wired into the actual callback entrypoint.** `R09B2NonMutatingCaptureCallback` now calls the single `capture_with_isolation()` path. That path snapshots protected state before capture and executes `require_unchanged()` in `finally`, so a protected mutation causes fail-closed rejection even on exceptional paths.
2. **TTT state schema is the frozen B1 schema.** The helper requires exactly `W`, `pending_evidence`, `last_evidence`, `initialized`, and `segment_progress`, rejecting missing or extra members.
3. **RNG and stream metadata are covered.** Isolation snapshots include CPU RNG and all CUDA RNG states when CUDA exists. The callback requires immutable `b2_stream_ordinal`, `b2_stream_epoch`, and `b2_stream_microbatch`; the P1 manifest wrapper now propagates microbatch metadata.

The tracked v3 CPU artifact records seven protected-state mutation cases (`parameters`, `buffers`, `optimizer`, `scheduler`, `batch_metadata`, `recurrent_state`, `ttt_state`), and each is rejected through the callback entrypoint. The artifact binds the recorded clean implementation root, submodule/Gitlink and collector/verifier/capture-source hashes.

## Scope note

This closure proves the isolation helper/callback interface and negative mutation contract on CPU. It does **not** prove that a future production `snapshot_provider` is wired to complete live model/optimizer/runtime objects, nor does it prove GPU capture safety or training behavior. Those remain future gated integration/runtime work and must not be inferred from P2 closure.
