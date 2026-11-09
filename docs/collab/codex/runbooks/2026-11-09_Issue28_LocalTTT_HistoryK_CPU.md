# Issue #28 — sparse completed history on the existing EvalV2 path

Owner authority: Issue #28 final body and comments 6731421819, 6731530426,
6732473919. Base source is qualified Issue #27 Root
`9b1756f9099955d6637743f8ad2fa0ee54987b7a` / Child
`60b252d05157b2753d2caebae32b11c878504bbe`; Root metadata also preserves its
APPROVE_CODE review. This change requires a new independent code review.

## One configuration parameter

`local_ttt_history_k` accepts exact integers 1, 2, 4, 8, 16, default 16. The
Root CLI override is `--local-ttt-history-k`. Sparse values require the existing
`sim_shared_vae` / Local memory `required` path. No-TTT and server-side history
keep their original default behavior. There is no public stride/mode selector.

For the actually completed H16 Action chunk starting at T, select relative
indices `j % (16/K) == 0`. At Replan T+16, each selected observation O[T+j]
is paired with the canonical action actually executed at T+j. Index 0 reuses
the previous Policy current-frame Visual96 after its action completion; the
current O[T+16] belongs to the next chunk. Source IDs are never renumbered.

| K | Relative source indices | Extra history Encode1 | FW T1 updates |
|---|---|---:|---:|
| 1 | 0 | 0 | 1 |
| 2 | 0,8 | 1 | 2 |
| 4 | 0,4,8,12 | 3 | 4 |
| 8 | 0,2,4,6,8,10,12,14 | 7 | 8 |
| 16 | 0..15 | 15 | 16 |

First Replan has no past update. A partial final chunk is ended and drained;
it does not invent a next Replan or unexecuted actions. All original H16,
scene sampling, identity, Session and Native Batch authority remain in place.

## Producer, completion authority and consumer

The native Sim loop selects before history RGB composition/copying. Unselected
steps have no history RGB/PNG, Frame, Worker encoding or fake Visual96. Every
actual successful action still produces its raw15 digest, source frontier,
lease/chunk/Actor/epoch identity, original deadlines and Owner completion.

K<16 uses explicit `PSM28-POSTSTEP-v2` receipts with `history_k` and `selected`;
skipped receipts require `source_rgb_sha256=null`. The Feature payload is
`PSM28-FEATURES-v2` / `sim_shared_vae_sparse_b1_t1`, carries the frozen K and all
16 chronological completion rows, with `feature=null` for skipped rows. This is
an explicit skip contract, not absent data relabeled as dense valid evidence.
The Owner checks every completion against its authoritative ledger, then passes
only the selected real Visual96/raw15 rows to the original OnlineLocalMemory
T1 scan. Its committed frontier remains T+16. The wire digest covers all rows.

The existing authenticated Worker `owner_complete` accepts the optional skip
receipt. A bounded skip ledger advances only contiguous authorized gaps; skips
may arrive before an earlier selected asynchronous Frame without advancing over
that Frame. Cached boundary reuse, signatures, capabilities, byte replay fences,
ACK, End, reset and owned process cleanup retain their existing authority.
No new scheduler, sparse FW engine, model/training change or update thread exists.

K=16 uses the original dense receipt/payload fields, request fingerprint and
numerical branch. K<16 is frozen in Manifest execution, Policy Owner, Worker
bootstrap/READY, assignment and Local Session. Resume compares full execution;
M/B and source consistency checks are unchanged. One retained Sim connector B1
guard is aligned to the already approved Policy 1..8 range on this independent
branch; it does not alter the #27 PRs.

## CPU acceptance and interpretation

Use an exact clean new Root/Child pair and a new external evidence directory.
The archived author runner records exact HEAD/Gitlink, import origins, versions,
command/environment, source fingerprints before/after, Ruff/format/syntax,
raw JUnit/logs and OS behavior. It runs the new tests plus relevant default,
No-TTT, native transaction, shared Worker and topology regressions. It excludes
the old synthetic 900 test and does not rerun/relabel the historical 965 Gate.

Required: zero failed/error/skipped tests, exit 0, PASS, unchanged source,
all-five exact count table, 0→16→32, pre-capture skip, no work on unselected
frames, original deadline, replay/changed bytes/abort, real IPC/HTTP/FD Worker
lifecycles, multi-Session isolation, 32 Session sparse M16/B8 and owned cleanup.
Kernel/device/env/model boundaries used in CPU tests are explicit doubles.

The same external dense probe runs in separate old/new Child CPU processes,
seed 28, one thread. Require equal wire features/cached boundary, actual Local
FastState, Prefix and synthetic linear Action hashes over two chunks. Synthetic
actions are not Cosmos diffusion actions. Recorded counts are functional CPU
evidence, not H100 speed, RoboCasa SR or independent DS approval.

Sparse Policy status reports selected/skipped original source steps, verified
Worker feature count, adapted_steps and existing update timing; Worker histogram
counts actual encoder calls. Existing trace distinguishes background compute
from blocking work. No latency/SR benefit is asserted without later authorized
hardware measurement. Do not merge V3 or run GPU/real RoboCasa/SR/900EP here.
