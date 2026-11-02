# Replan all-media — author handoff, REQUEST_GPT_INCREMENTAL_CODE_REVIEW

| Identity | Exact value |
| --- | --- |
| Formal Root implementation | `d2041e388eda084e42a2d6b0d115db8beedfab44` |
| Formal Child / Root Gitlink | `0dd13d3d952aa7cbab39f966dfab04b23551f0c9` |
| Candidate Root + Child branch | `v3-eval-v2-replan-all-20261102` |
| Owner request / Root base | `f49d52e5646e54a1eb45c31f3179901650694c20` |
| Child base | `9a8cd6183424bfce245fbca393ca25ed59919ea6` |
| Prior approved implementation | `4b581493db805c92964cb27e740c736db87c0329` / `9a8cd6183424bfce245fbca393ca25ed59919ea6` |
| Author scoped CPU | **379 passed, 0 failure/error/skip**, clean exact Pair |
| Independent GPT / DS / hardware | **Pending**; not implied by author PASS |

The later evidence/request/publication commits are bookkeeping only; they never
replace the Formal Root above. Previous source approvals stay with their own
exact pairs. This is a new media-only implementation and needs fresh incremental
Code Gate. No official V3 promotion is authorized or performed.

## Implemented behavior

Only user-selected `save_generated_video: all` is strict. Per Server spool defaults
to4 jobs/512MiB, configurable via YAML/CLI/server argv, validated and checked
against actual `/info`. Independent `media_drain_timeout_s` defaults300s,
0<value<=3600; it is distinct from Encoder termination grace.

Authenticated media reservation precedes native inference. Full capacity returns
429 and the client retries with a bounded media budget OUTSIDE actor/model locks
and the shared executor. Strict decode is prioritized on that executor; no
capacity wait can starve the decoder needed to release a job. Each retained job
reserves up to the existing32MiB wire item cap, bounded by configured bytes;
oversized candidate/decoded response yields explicit MEDIA_INCOMPLETE. Defaults
are per Server, not per Sim or a total-process-RSS guarantee.

For this low-load manual diagnostic mode, fetch/save/ACK is synchronous per
Replan. The Encoder waits for bounded Queue acceptance, writes a temporary MP4,
closes it, fully decodes/checks every frame and dimensions, fsyncs/atomically
publishes it and its identity-bound receipt, THEN reports VIDEO_SAVED over a
separate bounded datagram channel. Parent rechecks receipt/file SHA before media
ACK. Action inference is never rerun to repair video. Lost ACK reuses the same
receipt; saved MP4 survives permanent ACK failure. Replay after completed ACK
does not allocate another reservation or encode. Foreign replay is a media error.

Normal End drains active media, then sends Session End/Reset and finally closes
the Encoder. Sentinel follows confirmed writes; healthy encoding is not killed
by the old2s grace. All-mode RPC permits one additional drain allowance for
response/cleanup, but the prediction `episode_deadline` and base transaction
deadline protocol are unchanged. Timeouts/failures remain finite, preserve saved
files, mark MEDIA_INCOMPLETE and run safe cleanup. Unknown FD/Queue failures and
actual surviving owned processes retain fail-closed behavior.

Episode completion records reconcile expected/saved/ACKed/missing indexes. Root
`media_summary.json` checks receipts/inventory/hashes separately from scientific
Core/SR. No final automatic FFmpeg pass occurs there. All-mode media incomplete
prints a diagnostic and exits nonzero while scientific result/summary authority
remains unchanged. Completed valid Episodes are never rerun or retrofitted with
fabricated receipts. None/first and rollout policy keep their existing semantics;
no default900EP media-switch/config/concurrency remapping is introduced.

Implementation details/options/limitations:
`docs/build/PSM-WMA_V3_EvalV2_Replan_All_Durable_Media_Implementation_r1_2026-11-02.md`.
Production review anchors: Root config:34, runtime:243/292/449/669, CLI:213,
generated_media.py:7; Child batch transactions:133/240/336/488/559,
PolicyTransport:190/230/388, MediaSink:247/307,
generated_video.py:80/132. Consult exact source bindings for authoritative blobs.

## Evidence

Base directory: `docs/collab/codex/evidence/2026-11-02_eval_v2_replan_all_author_cpu/`.

| Group | Original JUnit count | Author interpreter |
| --- | --- | --- |
| New strict API/media/config/native/SR tests | 58 | Python3.13.5 |
| Related media/RM-M01/config/render/worker/native regression | 174 | Python3.13.5 |
| Existing transactions + real CPU Local/Fast/native-prefix regression | 129 | Python3.12.14, Torch2.10.0+cpu |
| Existing owned OS multi-Sim/HTTP/native-batch/cleanup/Resume | 18 | Python3.12.14, Torch2.10.0+cpu |
| Aggregate DISTINCT pytest cases | **379** | Two interpreters, no single-env claim |

Each original clean-Pair invocation records command/cwd/env, Root/Child/Gitlink,
source hashes, Python and unchanged source/status assertions. Static check is
Ruff0.12.7 check/format --check plus AST/py_compile,22 source Git Blob/SHA-256
bindings. No skipped cases or test threshold relaxation. The old spool-byte
negative was updated to exceed the configured new512MiB cap and now additionally
asserts no CPU copy; original action/Local/B=1 safety assertions remain.

Tests cover full4-job spool/backpressure; byte/candidate/decoder failures; decode
priority under queued inference; slow decode/fetch/Encoder; full Encoder Queue;
disk-full/rename/frame errors; immediately final Replan/End; Encoder death/
bounded kill/feeder cleanup; early/late/foreign ACK; ACK loss/replay; cancelled
Session; concurrent End and unrelated Session cleanup; none/first fast paths;
YAML->CLI->server options->actor info; false media-complete refusal; Core/SR and
real CPU Local Fast updates/prefixes/End ACK preserved even on media failure.

`synthetic_10_replans` preserves10 newly created genuinely decodable3-frame32x32
MP4s,10 Encoder receipts and full-decode SHA/count manifest. The loopback real
HTTP test checks the files and receipts BEFORE each actual media ACK and proves
10 single predictions/10 ACKs/10 saved files, missing0, immediate End, no owned
Encoder/feeder left. This is fresh CPU synthetic footage, NOT Cosmos output or
RoboCasa/historical hardware evidence. New native all-mode tests also execute
the actual145-action/10-Replan loop with fake physics, and real CPU Local tests
exercise two Replans with cold/hot prefix and confirmed Session reset.

Development failures are retained separately with disposition; they are neither
hidden nor described as a frozen old-code RED Gate. The final379 PASS is separate.
Artifacts, diffs, portable author CPU helper and exact commands/environment are
hash-bound in SHA256SUMS.json. No source/fixture writes occurred during final tests.

Clock-domain parser is unchanged and tested with explicit proc-file doubles;
actual cloud `/proc/self/timens_offsets` is absent. No target native clock proof.

## Scope, history and stopping point

Static `scope.json` verifies the precise file allowlist and unchanged Git trees/
blobs for model/Local algorithm, base Session/client deadline protocol, Scheduler,
Store, native action/SR loop, render mapping, Root GPU resource policy, Vendor,
training/data/checkpoint/config code. No historical results/config/Job/checkpoint,
old H3/H2/out2/NoTTT media/logs, shared live worktrees/processes or GPU0–3 accessed.
No real Action Server/model/GPU/EGL/RoboCasa launch. Actual FFmpeg here is
limited to fresh synthetic CPU media, not target-host/historical-file validation.

Inbox in request base was140743bytes, already above131072. Rollover preserved all
bytes at `docs/collab/chatgpt/archive/CODEX_INBOX_20261102_REPLAN_ALL_f49d52e.md`,
same original/archive Blob `dd00d0981b57c55fb7ea21aa978ccd92f1603817`; continuity
index then resumes append-only. This routine bookkeeping is not an implementation
Gate. History is intact and official V3/Child refs remain separate.

Request GPT **APPROVE_CODE / REQUEST_CHANGES / BLOCKED** for this exact new Pair,
incremental media path only. After Child->Root candidate publication and remote
readback, STOP. No promotion, DS dispatch or GPU execution. Independent DS CPU
and separately authorized small real-media Canary remain pending. Historical
HW-MEDIA-03 and real Batch hardware findings are not closed by these synthetic
tests; no claim of decoding417/121 old videos or repairing80 missing H3 videos.
