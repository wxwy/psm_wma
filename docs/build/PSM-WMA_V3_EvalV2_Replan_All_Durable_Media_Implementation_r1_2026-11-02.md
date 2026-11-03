# EvalV2 all-Replan durable media — isolated implementation r1

Owner contract: `docs/collab/chatgpt/requests/2026-11-02_V3_EvalV2_Replan_Video_All_Lossless_Media_Fix_Codex.md`
at Root `f49d52e5646e54a1eb45c31f3179901650694c20`.
Base approved implementation: `4b581493db805c92964cb27e740c736db87c0329` /
Child `9a8cd6183424bfce245fbca393ca25ed59919ea6`.
Candidate: `v3-eval-v2-replan-all-20261102`. This document describes implementation,
not a GPT verdict or hardware/run authorization. The post-commit author handoff
and `gate.json` bind the new exact Formal Pair.

## Effective options

```yaml
# User opts in for a small manual diagnostic Run; no default media switch change.
save_generated_video: all
media_spool_max_jobs: 4
media_spool_max_bytes: 536870912
media_drain_timeout_s: 300.0
```

Matching CLI overrides are `--media-spool-max-jobs`, `--media-spool-max-bytes`,
`--media-drain-timeout-s`. Jobs1..64 and bytes1..2147483648 are positive integers;
drain is finite and0<seconds<=3600. Limits are per Action Server, not per Sim.
Root config/argv, server preflight, actor `/info`, initial server identity proof,
resolved invocation, Sim settings and periodic batch telemetry record the values.
Strict all-mode rejects a Server which did not receive the requested settings.

300s is a configurable diagnostic completion budget for decode, transfer,
encoding, full-frame CPU verification and ACK, distinct from the existing2s
termination grace. Normal completion does not kill a healthy writer after2s.
Timeout/OOM/disk/codec/transport failure is explicit; no infinite waits.

## Sequence and lock boundaries

1. Only all-mode sends an authenticated nonblocking `/v2/media/reserve` before
   its native prediction. It binds the exact lease, request digest, payload hash,
   frontier and Replan index. Capacity is retained through durable media ACK.
   Repeated reservations are idempotent; replay after ACK consumes no new slot.
2. Full spool returns429. The client waits/retries with a finite media deadline,
   outside the actor/model lock and executor. It never resubmits a prediction to
   manufacture missing video. Unavailable/oversized media becomes explicit
   incomplete; native actions still execute once, and further diagnostic requests
   stop after a media fault. No silent concurrency remapping/restriction.
3. Each strict job reserves `min(32MiB, configured byte budget)`, conservatively
   covering its retained candidate or encoded response, using the existing32MiB
   wire cap. The byte limit bounds retained spool content, not total process RSS,
   diffusion activations or the decoder's transient scratch. Oversized candidates
   are rejected before CPU copy. Encoded replies must fit both caps.
4. Strict decode gets priority over newly queued inference on the SAME executor.
   There is no capacity wait inside that executor/model lock. The original native
   action Generation, Local prefix/Fast transaction and prediction deadline are
   unchanged. Reservation is a media preflight; the client still clamps the
   subsequent prediction's original budget to the remaining Episode deadline.
5. For low-load diagnostic all-mode, the Sim synchronously fetches/saves/ACKs
   each Replan. This deliberately trades throughput for a simple completion
   guarantee. None/first keep their existing fast/best-effort paths; rollout frame
   selection/encoding and media-independent Core/SR authority remain unchanged.
6. Encoder Queue submission waits within the media budget. A separate bounded
   local datagram reports `VIDEO_SAVED` or `VIDEO_FAILED`. Saved receipts bind
   Episode/Attempt/generation, index, assignment/request/payload and video hash.
7. Encoder writes a temporary MP4, closes the writer, decodes EVERY frame on CPU
   and checks dimensions/count, fsyncs and atomically renames the completed file,
   atomically publishes its receipt, THEN sends VIDEO_SAVED. Failed pre-publication
   writes leave no misleading final MP4. A failure between video publication and
   receipt publication remains incomplete; an existing file is never overwritten.
8. Parent checks the durable receipt/file hash before `/v2/media/ack`. Lost ACK
   retries use the same receipt without another encode. Permanently lost ACK
   retains the MP4/receipt but marks the diagnostic incomplete. No Session revival.
9. Normal Episode end drains active deliveries before Session End/Reset; sentinel
   follows the successful per-index receipts. A concurrent End waits without the
   model lock; unrelated Session End can progress while the client encodes.
   Existing owned process/feeder cleanup and unknown-FD fail-closed behavior stay.
   All-mode coordinator RPC allows ONE extra media drain budget for response/
   cleanup; `episode_deadline` sent to prediction remains the original value.

## Outputs and failure authority

- Existing `media/generated/replan_XXXX.mp4`, plus atomic
  `replan_XXXX.receipt.json`. No videos_view or duplicate production video copy.
- Episode `generated_media_completion.json` reconciles expected/saved/ACKed/
  missing indexes, independently of `result.json`, Local ACK and environment SR.
- `media_diagnostics.json` retains per-request failures and saved paths on ACK
  failure. No fetched-to-queue status is treated as saved in all-mode.
- Root `media_summary.json` checks valid Core Episodes' matching completion,
  file inventory, receipt identities and unchanged file hashes. It does not
  run FFmpeg again, change SR, rerun completed Episodes, or generate lost videos.
  Missing/legacy/invalid receipts are incomplete, never backfilled or forged.
- CLI prints the separate media status and returns nonzero on MEDIA_INCOMPLETE,
  even when scientific Core/SR is qualified. Scientific `summary.json` is not
  relabelled as a robot failure. Pending/invalid Episode accounting stays in the
  original Core summary; media expected counts refer to valid committed Cores.

## CPU evidence and boundaries

New tests exercise actual dispatcher/actor/client and native Episode paths, with
synthetic model output/fake physics, real CPU Local modules in a separate group,
real owned subprocesses, and actual small FFmpeg encode/full decode. Controls
cover4-job/full/byte spool, decode priority, queue backpressure, slow/failed
encoder, disk/rename/decode failure, last Replan/End, other Session End,
reservation/ACK/replay identity, timeout/cancel, Local Fast/prefix/End preservation,
none/first, configuration propagation and Core/SR/media separation.

Clock CPU tests substitute explicit kernel file contents while running the real
parser. This cloud lacks `/proc/self/timens_offsets`; it does not prove the target
host Client/Server clock domain. Original clock checks are not changed.

No model/checkpoint, GPU/EGL, real RoboCasa, old H3/H2/out2/NoTTT result/log/media,
training/DCP, shared worktree or official V3/Child ref is accessed or changed.
Historical HW-MEDIA-03 full decode and Batch hardware gates remain separate;
new synthetic MP4 evidence cannot close them. Submit new Pair and author CPU,
request GPT incremental review, then STOP. No automatic V3 promotion or Canary.
