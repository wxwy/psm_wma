# RM-ALL-R01 — bounded Episode ACK history, author incremental handoff

**Request GPT fresh incremental Code Gate; author CPU PASS is not approval.**

| Identity | Exact value |
| --- | --- |
| New Formal Root | `e7ce99d7a0bbb7a81ea7afcee7253548687dc223` |
| New Formal Child / Gitlink | `c93f2abf4fb27d36176ff8db094379a853cec796` |
| Isolated Root + Child branch | `v3-eval-v2-replan-ack-r01-20261102` |
| Reviewed old implementation | `d2041e388eda084e42a2d6b0d115db8beedfab44` / `0dd13d3d952aa7cbab39f966dfab04b23551f0c9` |
| Root base after consuming review | `ec8a8bf31d6e4cd2cc1a387b77d8510aef57e06f` |
| Author scoped final CPU | **122 distinct passed, 0 failure/error/skip** |
| New targeted tests | **16**, same frozen bytes before old RED and new GREEN |

The detailed review was read from the freshly fetched candidate, then fast-forwarded
with both review commits preserved. Sole production blocker was RM-ALL-R01.
Previous full379 evidence and review remain immutable at their original pair.
No inherited full/hardware gate is relabelled. Evidence/bookkeeping HEADs do not
replace this Formal Pair.

## Minimal implementation

Only Child `cosmos_framework/inference/robocasa_batch_transactions.py` changes:
**26 additions /8 deletions**. Root production code, other Child files, config,
spool defaults4/512MiB, media deadline300s, Encoder/file verification, Local-TTT,
SR, Scheduler/Store, model/training/checkpoint, GPU policy and Vendor are unchanged.
Root implementation adds the new focused test, Gitlink and SESSION/TODO only.

`_acked_media[session_id]` now maps every saved request key to its immutable
`(payload_sha256, receipt_digest, replan_index)`, rather than overwriting the last
key. After Replans0/1/… are saved, correct older reservation returns
`already_saved=true` without allocating a job, and its identical ACK returns
idempotent success. Changed key/payload/index/receipt or foreign/stale lease is
rejected; no new native prediction/decode/Encoder work is done for replay.

Bound is **100001 records per active Episode**, matching the EXISTING public
reservation frontier range0..100000. Only key/digests/index are retained, not
video, frames, paths or full receipt. Pending strict reservations count toward
the same bound before admission, so multiple pending ACKs cannot overshoot it.
Exhaustion explicitly returns `reserved=false / MEDIA_INCOMPLETE`, never evicts
older authority or loops forever. Existing-record replay bypasses new-capacity
admission. This is a fixed metadata bound, not a new user/config/ABI option.
Session count remains the existing maximum8 physical Slots.

History survives End202 while the executor is still in flight. It is released
only when the existing base Session End reports `acknowledged=true`. Subsequent
Slot generation has a distinct lease and old identities cannot resurrect state.
No base Session/transaction/client lifecycle or native model lock is modified.

## Frozen RED/GREEN and public-path controls

Evidence: `docs/collab/codex/evidence/2026-11-02_eval_v2_rm_all_r01_author_cpu/`.

- Old0dd production source was checked byte-for-byte against the Git object
  BEFORE running the new tests. The new test was copied/hash-frozen before RED.
  Two actual saved/ACKed Replans have different frame sequences and video hashes.
- Old targeted **RED2**: first reservation replay wrongly allocated1 job instead
  of `already_saved`; correct first ACK replay raised the original unknown/changed
  ACK error. Exact public `transaction_dispatch` and actual actor/CPU Encoder run;
  no helper-only fabricated completion.
- New clean Formal Pair: **74 media tests =16 new +58 inherited**, Python3.13.5;
  **48 batch Actor/native/real CPU Local tests**, Python3.12.14 CPU Torch. All122
  distinct pass with no skips. This is scoped, NOT a rerun of379 and NOT DS/GPU.
- New cases cover two- and six-Replan old reserve/ACK replay, repeated pressure
  beyond four spool slots, following new Replan, no extra native/decode/encode,
  unchanged files/receipts, changed key/hash/index/frontier/receipt/assignment
  refusal, foreign valid Session isolation, exact capacity including pending jobs,
  old-proof replay at capacity, End202 retention, acknowledged End release and
  stale generation refusal. Existing none/first, actual Local prefixes/Fast state,
  Native action, Encoder failure and Core/SR separation regressions are retained.

Raw RED and final JUnit, stdout, commands/env/Python/source hashes, frozen test,
aggregate122 XML, two fresh distinct MP4/receipts/full-decode proof, minimal diffs,
Ruff0.12.7/format/AST/py_compile2, two source bindings and protected-tree/old379
immutability proof are archived with checksums. Tests were not edited for GREEN.
The first draft external driver had a redundant message-validation assertion
after pytest had correctly produced RED2; its raw output is retained. Corrected
the driver check only, revalidated same old production/same frozen test as RED2;
this is not four unique RED cases or a hidden production/test fixture change.

Clock tests keep the unchanged real parser with explicit kernel-file doubles;
no target-host native clock proof is claimed. The packaged two MP4s are NEW
32x32 RGB3-frame CPU test clips, not Cosmos model/RoboCasa/historical footage.

## Boundaries and reviewer request

No V3 merge/promotion, GPU/device/task query, real Cosmos/Action Server/RoboCasa,
training/DCP/Job/shared worktree or old H3/H2/out2/NoTTT media/log/result access.
No old379 artifact/test mutation. Root+Child candidate commit/publish only.

Nonblocking performance note is accepted: full decode/fsync/SHA confirmation has
real cost. This fix does not optimize that path or claim negligible overhead.
Per-Replan completion latency/overall throughput remain separately authorized
target-host Canary measurements. Historical HW-MEDIA-03/Batch evidence is not
closed by synthetic clips.

Request **APPROVE_CODE / REQUEST_CHANGES / BLOCKED** for RM-ALL-R01 on this new
exact Pair. Incremental single-file code/identity-lifetime review only; no need
to reopen approved design or unrelated media/GPU/training paths. Publish Child
first, then Root and fresh-readback refs/Gitlink/source/artifacts; STOP for GPT.
Independent DS CPU and any hardware execution remain separately gated.
