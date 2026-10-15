# PSM-WMA V3 — B1 GPU Readiness CPU Prepare/Config Evidence Independent Review

**Date:** 2026-10-15 (based on DS_PRO evidence dated 2026-10-14)  
**Reviewer:** GPT, independent Evidence/Gate reviewer  
**Gate scoped:** `B1_GPU_READINESS_PREPARE_AND_CONFIG_CPU_ONLY`  
**CPU Lane A/B/C evidence:** **ACCEPTED / PASS** — this is an evidence finding, **not** actual GPU readiness  
**Formal GPU-readiness verdict:** **REQUEST_CHANGES** — HIGH new runtime startup blocker `B1-GPU-IO-01`; Owner numeric freeze pending. GPU_NOT_AUTHORIZED.  
**Formal diagnostic Root code SHA:** `dfeace66bbce549bf94a447c18f3d51e5dd2e376`  
**Diagnostic Child/Gitlink:** `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`  
**Original Source/Index8:** Root `b159f45906f7261d028aecc226ab7f2bb9807eb9` / Child `937066ffd90f2bf783ad4fbb4909e9c0b8922982`  
**Original Target/Packed128:** Root `c4731bca1a590663db88bd6cd74dbcf9fd513a85` / Child `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`  
**B0 full checkpoint fingerprint, DS authoritative receipt:** `2e409afe788f4faf2cc1f5db8d500638a219647dc90283f9687863212d77d999`  
**Prior B1 CPU Code Gate:** `APPROVE_TO_CLOSE_V3_PACKED128_B1_8RANK_CPU_CODE` — already CLOSED at exact diagnostic pair; **NOT REOPENED**.  
**DS evidence:** `DS_PRO V3 — B1 GPU Readiness: CPU Prepare + Config Receipts`, 2026-10-14, pasted by Owner; no DS code changes and no real CUDA/model/DCP loading.

## 1. Frozen-pair status / scope

Live GitHub `wxwy/psm_wma:V3` and B1 diagnostic branch were freshly checked. Diagnostic B1 branch HEAD still precisely `dfeace66...`; diagnostic Gitlink `8f3672d1...`; source and target historical Root Gitlinks verified as above. The technical formal pair is **unchanged**, so this review **does not repeat** the previous full B1 CPU code audit, 138 tests, B0 CPU Gate or 451GB dataset acceptance. It adjudicates new DS CPU-only execution evidence for a DIFFERENT scoped readiness gate and the newly exposed 8-rank runtime IO path.

The DS report includes digest/hash of two underlying CPU config JSON files, but those machine JSON files were not supplied in the conversation. Therefore GPT's claim is limited to verifying its *reported* execution results, pinned source contract and related GitHub code—not independently re-hashing DS local JSON or reading private training-machine artifacts.

## 2. Lane A — actual frozen pair Prepare

**PASS as CPU-only evidence**: DS used 3 clean independent detached checkouts. Four exact-profile `--mode prepare` executions were reported exit0 (`Index8/Packed128 × P0_FIXED/P1_MATCHED_STOCHASTIC`) and returned `PREPARE_ONLY_NO_GPU_OR_DATASET_SCAN`, `checkpoint_write_authorized=false`, `gpu_authorized_by_prepare=false`, with correct frozen Root/Child, expected digest and B0 checkpoint fingerprint. This supersedes the previous invalid-Root negative probe that had not proven a legal Prepare PASS.

**Scope limit**: the diagnostic `strict_metadata()` in `tools/gates/v3_gateb1_run.py:51–91` checks paths, pins and receipt presence; it does **not** instantiate the model, execute the sampling contract, derive runtime config, prove native DCP restore, or measure GPU performance. Do not promote its exit0 to runtime readiness PASS.

## 3. Lane B — resolved config receipt

**PASS as CPU-only config evidence**, based on the actual frozen `examples/psm_wma_robocasa_corrected_phase5.py` authorities for both legs: DS built two configs via `_load_config` + `overlay_config` and a minimal trusted receipt/manifest-backed catalog surrogate; no full preflight, LeRobot, cache payload walk, GPU or model instantiation. DS reports exact independently recomputed config digest equality with frozen B0 receipts:
- Source `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`
- Target `1ab2bbe4df9954467bb0acf0d371dce40dff8bd04cfa3c81ca0ec6fe76a94b4a`

Resolved agreement: `FusedAdam`, LR `5e-5`, weight decay `0.05`, betas `(0.9,0.99)`, eps `1e-8`, generation/action/local selected patterns, bf16 precision with FSDP8 fp32 master config, Local-TTT `T16/B8/GA2/K4`, loss scale/action weight `10/10`, vision waver/action logitnormal, independent-action-schedule=false, shift dictionary `{'256':3,'480':5,'720':10}` (DS prints numeric-looking keys), vision bucket `256`, 30k/warmup500, GradScaler disabled, Sound generation/scheduling disabled. Attention dropout=0 was **SOURCE-DERIVED default + no resolved override**, not tested in instantiated CUDA model. Source has no layout term; Target has member-packed slot-major term, explaining the intentionally different config digests.

**Scope limit:** full FSDP runtime optimizer state, parameter.grad storage dtype, actual BF16 master path, per-Consumer vision bucket and GPU stochastic equivalence remain **GPU_UNVERIFIED**, not unresolved CPU receipt fields.

## 4. Lane C — safe unauthorized Execute and guard geometry

**PASS as CPU-only safety evidence**: with each real pinned frozen Root, `--mode execute` without `--owner-authorization-json` was reported to fail at `tools/gates/v3_gateb1_run.py:94–114,230–236` before CUDA or Cosmos/model imports. Static review corroborates `v3_gateb1_same_job.py:29–93` scopes checkpoint save-denial through both GA2 steps and returns a transient same-job read source; result evidence is confined to isolated `/tmp` path. Actual model and DCP **not** executed or loaded.

## 5. New GPU-runtime finding independent of the CPU receipt

### `B1-GPU-IO-01` — **HIGH / GPU Readiness blocking**

**File/line:** `tools/gates/v3_gateb1_dcp_transient.py:63–67,86,111–118` and `tools/gates/v3_packed128_gateb_compare.py:185–212`; caller `tools/gates/v3_gateb1_native_driver.py:302–306` / `tools/gates/v3_gateb1_run.py:306–318`.

**Observed source behavior:** `strict_transient_load(..., hash_shards=True)` is the default. At lines 86 and 111 the function calls `snapshot_checkpoint(checkpoint_path, hash_shards=True)` **before and after** official DCP load. `snapshot_checkpoint` iterates all 32 DCP `*.distcp` shards and SHA256-reads **every shard** (B0 code at lines 185–205). Called independently on each of 8 ranks, this is **16 complete 32-shard hash sweeps per two-step leg job**. With 2 legs × 2 stochastic profiles × 2 independent repeats, this can reach 128 redundant all-shard hash sweeps. The result is read-only and does not itself mutate a checkpoint, but unnecessarily repeats expensive B0-type full-shard verification and can dominate GPU validation wall clock / shared storage bandwidth. DS's CPU-only Prepare deliberately never reaches this code path, and reported using the original B0 full-shard fingerprint without re-hashing.

**Violated requirement:** previously accepted, immutable iter1300 DCP is the authoritative source; B0 is CLOSED; B1 should consume B0's existing full-shard fingerprint and prove no writes with an isolated read-only path, not implicitly trigger 32-shard re-hashing in every GPU process. This risks the Owner's bounded, low-cost validation budget and conflicts with no re-running costly closed verification work. Note: this is **checkpoint I/O**, not a claim the 451GB RoboCasa dataset was rescanned.

**Minimum accepted repair (GPT/Codex only, narrow code):**
1. Preserve the original supplied B0 full-shard fingerprint as immutable authority, verified against the preexisting trusted B0 receipt. **Do not** naively switch `hash_shards=False` and compare its *different* lightweight fingerprint to the original full-hash B0 value; that would fail a valid source.
2. Use a **lightweight, no-shard-content-read** before/after source immutability witness: read-only local source/mount or equivalently protected path, unchanged source path, component and shard file name/size/mtime set, four small DCP metadata file hashes and eight local sidecar hashes. Independently block any `save` or latest-pointer mutation (already in native SameJob adapter). Write no source DCP bytes.
3. Report two separate identity fields: `authoritative_b0_checkpoint_fingerprint` (original B0 receipt) and `runtime_lightweight_immutability_witness` (explicitly NOT a full-content digest). Ensure comparing Source/Target still uses the identical authoritative B0 fingerprint in `ConsumerKey` and report, while also requiring before/after lightweight invariants equal; fail CLOSED on missing/mismatched receipt or any changed metadata/stat.
4. Add CPU negative tests proving that no full `sha256_file` is called on DCP shards; B0 authoritative fingerprint preserved, metadata/sidecar/stat mutation rejected, and original strict same-job 5-component read + no-save guarantees survive. Only change isolated B1 diagnostic implementation/tests, no frozen Child/source data or B0 re-run.
5. Commit NEW exact formal diagnostic implementation SHA and obtain independent focused DS CPU verification and fresh GPT incremental review for the changed pair. Until then GPU Readiness remains BLOCKED.

**Do not solve this by disabling checkpoint protections**, rewriting the source `latest_checkpoint.txt`, replacing the frozen source Checkpoint, or rehashing all shards as an ad hoc B0 replay.

## 6. Remaining independent Owner decisions / GPU-scope boundaries

**Numeric policy not yet frozen:** B1 r2 threshold candidates are currently implemented in `tools/gates/v3_gateb1_metrics.py` but Owner has not approved the loss/gradient/FP32 Fast State/DeltaP/Adam DeltaM1/DeltaM2/missing FQN/near-zero/runto-run acceptance rules. Candidate values must be approved **before** 8×H100; no after-the-fact widening. The actual optimizer and loss scalar storage dtypes cannot be inferred just from configured bf16 model precision. Owner signoff must identify valid dtype branches or fail-closed for unexpected dtypes, and exact gradient/optimizer/GA2/Local Fast State evidence required.

**Sound/attention config:** accept DS's current config evidence for `sound_gen=false`, `independent_sound_schedule=false`, `attention_dropout=0` (default/no override), but require fail-closed confirmation at launch if a real instantiated model differs. `arch_invariant_rand` inferred inference-only; remain GPU-time probe. Actual valid Native Consumer binding of vision bucket `256` and P1 cross-leg RNG parity are GPU-time conditions.

**GPU authorization:** this report is **not** an Owner authorization and must not be used to construct or sign `V3_PACKED128_B1_GPU_OWNER_APPROVED` JSON; no `torchrun`, CUDA, DCP native GPU load or Formal30k may start.

## 7. Final disposition

- **CPU-only Lane A/B/C:** execution evidence **ACCEPTED/PASS**; do not rerun the four legitimate `prepare` tests or resolved-config receipt merely due to code-doc bookkeeping.
- **Current B1 GPU Readiness:** **REQUEST_CHANGES** based on the new HIGH `B1-GPU-IO-01` runtime blocker and pending Owner numeric threshold freeze. This is not a reversal of the already APPROVED B1 CPU Code Gate at `dfeace66`.
- **Gate B1 real 8×H100:** `GPU_NOT_AUTHORIZED`; no GPU parity has been run.
- **Gate M/30k formal resume:** HOLD. B0, offline dataset verification and full repo audit remain closed/deferred per Owner.
