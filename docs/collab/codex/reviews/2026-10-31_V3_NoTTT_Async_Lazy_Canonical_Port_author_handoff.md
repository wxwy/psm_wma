# No-TTT async/lazy pipeline — current-V3 integration Code Gate request

Status: **REVIEW / author CPU PASS**. Request GPT fresh incremental review of
the new integration Pair. This is not a self-issued Code Gate approval.

| Identity | Full SHA |
| --- | --- |
| Formal implementation Root | `c66ade95b044d3664cd782d43d7917a604425db3` |
| Formal Child / Root Gitlink | `baf1b5bf46853e9849a91518803b9738fc216235` |
| Current-V3 Root baseline | `2bcc27e94576837167cacd190af7dc837e6129cd` |
| Current-V3 Child baseline | `0ae313e329d290fc6b8a50fda1112820fb7ac485` |
| Accepted performance donor Root | `fd9021b0908b4b2763b3d02508b1f34df377dc97` |
| Accepted performance donor Child | `224c5f3c0bd6911bb49cb6bb0895ba7da53ff822` |
| Isolated Root and Child branch | `v3-nottt-async-lazy-port-20261031` |

Evidence/Inbox/remote-receipt successor commits do not replace the formal Pair.
No canonical branch promotion is requested by this handoff.

## Why the port includes prerequisites

Actual current-V3 inspection found `MatchedNoTTTTrainer.bind_grouped_stream()`
still using `NoTTTCpuLoader` and RAW recipe; the accepted Issue9 AsyncLoader and
AsyncRecipe are absent. Copying only the two Lazy Source files would not put
them on the active training path. The explicit executable dependency closure is
six production files, each **byte-identical to accepted donor224c**:

- New `trainer/no_ttt_async_loader.py`, `no_ttt_async_recipe.py`,
  `no_ttt_worker_source.py`.
- `trainer/matched_no_ttt.py`: positive-worker binding and checkpoint-boundary
  handling from the tested donor; workers0 remains synchronous.
- `utils/no_ttt_loader_profile.py`: runtime-only async provenance/limits.
- `data/generator/action/datasets/robocasa_exact_window_cached_sft.py`:
  reconstruction metadata for the existing transform.

Seven donor test/support files accompany them. Two are already-reviewed fixture
corrections: the reduced RAW fixture explicitly selects its original backend;
the example fixture uses supported structured config and a temporary receipt.
No production serializer rule or previous numerical assertion is loosened.
The new Root test adds7 receiver sentries for actual binding and identity.

No whole donor commit/child merge was used. Exact object audit confirms:

- All13 selected Child paths (6 production +7 tests/support) equal donor blobs.
- All other **1,255 Child objects equal current canonical0ae**. Current EvalV2
  evaluation/inference/simulation trees, model, checkpoint, configs and packages
  remain byte-for-byte unchanged.
- Entire trainer/data/model/checkpoint/utils/configs/examples/uv.lock trees now
  equal the performance-tested donor224c. Both Root training launchers equal
  canonical2bcc and donorfd9021. This preserves the tested training path without
  bringing the older donor's evaluation files across.
- Root production launchers/configs remain untouched; Issue13 console helper
  is absent. Its separate candidate and review are not part of this request.

Full scope/inventory:
`docs/build/PSM-WMA_V3_NoTTT_Async_Lazy_Canonical_Port_2026-10-31.md` and
`docs/build/PSM-WMA_V3_NoTTT_Async_Lazy_Port_inventory_2026-10-31.json`.

## Author evidence on this exact Pair

Raw bundle:
`docs/collab/codex/evidence/2026-10-31_nottt_async_lazy_canonical_port_author_cpu/`.

| Check | Result |
| --- | --- |
| Receiver binding / lazy source / recipe selection | 33 passed |
| Async overlap / full-partial / RNG / Resume / failure regressions | 10 passed |
| Final unique testcase total | **43 passed, 0 failures/errors/skips** |
| Ruff0.12.7 check and format | PASS,14 scoped Python files |
| Syntax / exact source before-after | PASS14 / unchanged |
| Formal source binding | 14/14 checked Python Git blobs + SHA256 |
| Git scope / donor equality / canonical preservation | PASS, explicit audit JSON |

The earlier7-case binding run is repeated in final43, not43+7 unique cases.
Prefinal Root784 had import-bootstrap Ruff annotation placement corrected in
c66 before final verification; four comment-only lines, no production changes.
Final raw commands/logs/JUnit/environment, overlap timeline, lazy-build witness,
full Root/Child diffs and artifact checksums are included. No full301 or full58
historical suite was rerun.

Tests exercise real CPU multiprocessing/Trainer lifecycle and official source
read/transform helpers with synthetic local parquet/latents, fake text vocabulary
and tiny CPU models. State-continuity checks cover model, optimizer, scheduler,
iteration, RNG, committed Frontier and next Consumers for0→8/rank0 and8→8/rank3.
These are CPU full-state fixtures, **not real DCP** or an independent DS execution.

Logs retain pynvml deprecation,8-worker/affinity5 advisory and an async-exit
resource_tracker warning about2 semaphore objects. Selected owned-worker exit
assertions passed; we do not claim blanket zero leaked OS resources. CPU overlap
is measured against synthetic compute, not CUDA throughput.

## Performance evidence and next review boundary

The accepted matched GPU A/B remains historical **DS_REPORTED**, reviewed by GPT
in `2026-10-31_V3_NoTTT_Issue12_C12200_Exclusive_Matched_NW0_NW8_20x2_Performance_APPROVE_PERFORMANCE.md`.
It is not rerun or newly independently verified here. Step Wall15.489s→9.611s
supports approximately1.61x throughput in that experiment. Progress `data`
means ready `gpu_data_stall_ms` current-stream gap; no whole-GPU idle49x claim.
Pending read-only DS metric correction does not require another GPU experiment.

Request only the **incremental integration Code Gate**: active receiver binding,
donor object equivalence, current EvalV2 preservation and targeted CPU evidence.
Do not repeat previously closed donor design/performance reviews. Any resulting
approval remains separate from canonical merge or formal training authorization.

No GPU, real dataset/model/DCP, Action Server, RoboCasa or formal Job was accessed.
No original checkpoint/config/Job identity/history was modified. No A/B-generated
checkpoint promotion. If Owner later authorizes formal Resume, the proposed source
remains the original complete iter12200 with nw8/prefetch1/persistent1/timeout120;
this handoff does not run it or change launcher defaults. Stop for GPT review
after isolated Child→Root publication and remote readback.
