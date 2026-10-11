# DS_PRO — V3 Batch 1 合并验收总报告（B1/B2/B3/C0/D0）

**DS report date:** 2026-10-10  
**Persisted by:** GPT on 2026-10-11, based on owner's verbatim relayed DS_PRO summary.  
**Source status:** DS_PRO independent execution report; this document preserves the reported facts, counters and caveats. It is **not** the original `/tmp` JSON, nor a claim that GPT directly inspected the training-host log bytes.  
**Formal pair:** Root `444c232b976e80ac68cde9e7370e73b9f6410f0e`; Child/Gitlink `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`.  
**Batch authority:** `docs/collab/chatgpt/reviews/2026-10-10_V3_r2_batch1_parallel_B_C0_D0_execution_authorization_444c232b_e9b8a41.md`.

## 1. DS_PRO verdict table, unchanged as reported

| Subgate | DS verdict | DS evidence summary |
|---|---|---|
| B1 | PASS | 4 configs × 4 real sample identities, 10 classes of fields bytewise SHA256-equal; compact ON/OFF proxy/storage contrast |
| B2 | PASS | Shared Episode cache MISS→HIT, Episode switch and repeat, read content/identity matches |
| B3 | PASS | 3 real episodes × first/middle/terminal = 9 segments, current/previous causal evidence independently re-read, GA2 planner layout |
| C0 | PASS (note) | latest points to iter_000000800; six checkpoint folders; iter700/800 have four main components and 8 rank sidecars; rank1–7 Scheduler shard empty |
| D0 | PASS | workers0/2/4 on 48 actual producer segments, same ordered request IDs, **first segment fingerprint** equal across configurations; resource benchmark warm-cache |

These are DS_PRO's reported verdicts. Independent GPT closure may differ where a frozen mandatory evidence field is not explicit; see review file.

## 2. Immutable real-data provenance reported by DS

- Cache: `datasets/robocasa365-target-atomic-left_wrist-exact_window`; 18 task classes / 9,126 episodes / **2,085,331 windows**.
- Manifest SHA256 prefix `8e63c73b…`; corpus digest prefix `0e0c05d0…`. Expected latent `[5,48,12,20]`; raw action `[17,15]`; source action12/state16.
- Source: `/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic`.
- Verified index: `datasets/robocasa365-target-atomic-verified-index-r1`; source binding prefix `f91b0b47…`; `exact_window_count=2,085,331`, `exact_window_v1`.
- Checkpoint root: `outputs/local_ttt_robocasa_raw15/psm_wma_v3/corrected_phase5/formal_verified_index_30k/checkpoints`.
- CPU environment: existing training venv; `CUDA_VISIBLE_DEVICES=''`, `COSMOS_DEVICE=cpu`, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `LD_LIBRARY_PATH=''`.
- No GPU, torchrun, Fresh/Resume, DCP deserialization, model training or simulator. Original Formal30k remained stopped. No production modifications or GitHub commits by DS.

## 3. B1 — real Window inputs

**DS verdict:** PASS. `/tmp/psm_wma_v3_batch1_b1b2_report.json` (382.8s).

Selected exact flat indices `0`, `7`, `1042665`, `2085330`; four configurations of (Compact Vision, Shared Episode Cache): `00`, `01`, `10`, `11`. The reporter asserts identical SHA256 across configurations for 10 field classes: `latent`, `action_raw`, `action_pad`, `tokens`, `global_row`, `plan`, `caption`, `image_size`, `key`, `start`. Example action_raw prefix `c65622fb…`, action_pad `4cfa89f8…`. Reported schema: raw video old 6,684,672 bytes; compact 1B backing; video_latent `[5,48,12,20]`, action_raw `[17,15]`, padded action `[17,64]`, image_size `[192,320,160,320]`. Cached latent required true.

**Reporter storage label needs clarification:** OFF was described as `3,129,600B dense fp32 after resize`. Given image_size/video shape `[3,17,192,320]`, contiguous uint8 occupies 3,133,440 bytes; fp32 would occupy 12,533,760 bytes. This is a presentation/measurement discrepancy, **not by itself proof of semantic data drift**. The original zero-video backing is 6,684,672B and the compact proxy stores 1B. The DS-report's precise OFF field requires clarification before being cited as a measured saving.

The summary does not enumerate which task classes correspond to the four indices, nor explicitly enumerate every ancillary `idle_frames`/fps/domain/mode/frame-index field. It may be in the real JSON; do not claim directly inspected fields absent from this summary.

## 4. B2 — real Episode Cache reuse

**DS verdict:** PASS. Same source JSON.

Shared cache: first MISS+load about 87ms, about 79.6 MB/episode; repeated HIT; cross Episode `CloseBlenderLid/0` to `PickPlaceCounterToCabinet/4498` new MISS; adjacent same-Episode Window HIT. `read_window/read_identity`, latent/action across shared OFF/ON byte-equal; isolation affirmed by DS. No eviction, failed load or oversized entry observed (these untriggered cases should not be described as tested).

## 5. B3 — Local-TTT Segment causal and layout validation

**DS verdict:** PASS. `/tmp/psm_wma_v3_batch1_b3d0_report.json` (249.5s).

Real `ExactWindowLocalCatalog`, `ExactWindowRankPlanner`, `ExactWindowSegmentProducer.prepare/materialize`; T16, B8, GA2. Fixed training config digest shown with prefix `70e9867f…` (report does not claim independent full config preflight measurement).

Three episodes, 9 segments:
- `CoffeeSetupMug/episode_001744`, 209 windows, 14 segments, cursors {0, 7, 13}; tail `valid_count=1` at step208.
- `CloseBlenderLid/episode_000000`, 345 windows, 22 segments, cursors {0, 11, 21}; tail valid=9 at 336–344.
- `CloseBlenderLid/episode_000457`, 697 windows, 44 segments, cursors {0, 22, 43}; tail valid=9 at 688–696.

DS reports `causality_ok`, `visual_recheck`, `action_evidence_recheck`, `raw_item_steps_present`, `pad_valid_beyond_count`, `pad_step_is_minus1` all true; valid previous-step evidence matches re-read latent→visual96 and previous action[1], terminal only `training_stream_end`.

First GA plan: `member_counts=[128,128]`, `n_window=256`; 8 distinct slots per member. Each slot carries same Episode from GA member0 cursor0 to member1 cursor1 (first step0 then16); candidate frontier cursor2/next_segment_id2. `slots_distinct_across_members=false`, `episodes_distinct=false`, `slots_ordered=false` in DS probe reflect **repeated member ownership**, not automatically a bug in the plan; compare against actual frozen planner semantics, not global slot-uniqueness across members.

**Evidence reporting gap:** this summary validates actual causal re-read and one GA plan but does not explicitly show the **same 9 segment outputs under both (OFF/OFF) and (ON/ON)**, nor output of native `gather_exact_window_same_index` comparison. Thus the frozen cross-toggle parity and same-index order contract need a narrow witness/addendum; this note does not assert the code is defective.

## 6. C0 — Formal30k DCP structure inventory

**DS verdict:** PASS with caveat. `/tmp/psm_wma_v3_batch1_c0_inventory.json`.

Directory pointer `latest_checkpoint.txt` targets `iter_000000800`. Available iterations: 200, 400, 500, 600, 700, 800. For 200–600 no `optim` component; do not treat those as strict same-job resume candidates. At 700 and 800 `model`, `optim`, `scheduler`, `trainer` exist, model shards total around 13.49 GB, trainer around 183KB, optim no zero-byte shard; all 8 `dataloader/rank_*.pkl` present and nonempty. Scheduler: rank0 shard 14,506B, rank1–7 shard sizes 0; `structurally_complete=false` in a conservative original probe.

**Independent code interpretation:** pinned Child `cosmos_framework/checkpoint/dcp.py:1186-1195` constructs `CustomSavePlanner(dedup_save_to_lowest_rank=True)` for *every* saved component, including Scheduler. Therefore one rank owning the replicated tiny scheduler data is **consistent with the writer contract**, not evidence of missing 7 unique states. Presence of the four required metadata, at least one Scheduler payload, nonempty model/optim/trainer and eight rank dataloader files makes iter800 *structurally plausible*, pending actual DCP strict-load validation in C1. C0 structural PASS does **not** certify DCP payload integrity or optimizer/RNG/fast-state recovery.

## 7. D0 — Raw Segment Producer CPU workers 0/2/4

**DS verdict:** PASS. `/tmp/psm_wma_v3_batch1_b3d0_report.json`.

Three GA windows × two GA members × eight slots = **48 segments per worker configuration**. DS reports per-configuration `order_ok=true`, `unique_fingerprints=true` and `cross_config_first_segment_fp_identical=true` with shared first fingerprint `477d81a4bbc7b1ab`. Full per-segment cross-config fingerprint/tensor equality was **not explicitly reported**.

| num_workers | wall_s | segments/s | iteration_wait_ms | cache hits/loads/misses delta | RSS delta |
|---|---:|---:|---:|---|---:|
| 0 | 8.11 | 5.92 | — | 2406 / 0 / 0 | 0 KB |
| 2 | 12.40 | 3.87 | 2079 | 2406 / 0 / 0 | 0 KB |
| 4 | 35.34 | 1.36 | 6117 | 2406 / 0 / 0 | 0 KB |

Reported resident RSS around 6.0 GB and stable. All worker configurations reused the same Episode cache; **each measured 0 loads, 0 misses**, so this is a warm-cache materialization-focused benchmark and must not be interpreted as cold read, general I/O speedup evidence, or GPU training throughput. On this particular measured warm workload workers0 was faster. No failure, leakage or worker exception reported.

**Evidence reporting gap:** all 48 outputs per configuration were not shown to match across worker counts, only their order and first fingerprint. Separate cold/warm throughput requested by frozen contract was not demonstrated. A compact all-fingerprints comparison and limited cold-cache probe is sufficient to complete this part; a full training run is unnecessary.

## 8. Scope summary and evidence provenance

- DS source files reported but **not** uploaded: `/tmp/psm_wma_v3_batch1_b1b2_report.json`, `/tmp/psm_wma_v3_batch1_b3d0_report.json`, `/tmp/psm_wma_v3_batch1_c0_inventory.json`.
- Reporter says the pinned formal pair matched and all work was read-only. The exact returned local Git hashes were not enumerated in the relayed summary.
- An earlier external probe attempt failed because its `segment_fingerprint` test script applied `int()` to an Episode-ID string; DS corrected this external probe and reran successfully. This is not evidence of a production defect, but should be represented in the probe audit trail.
- DS could not fetch the full frozen review document on-host but states direct owner instructions authorized execution; reviewer has independently reread the frozen GitHub contract and considers it unmodified.
- On this current review, the project's original Formal30k job remains STOPPED; neither DCP loader state consistency nor required real-model numeric parity is certified by any result.
