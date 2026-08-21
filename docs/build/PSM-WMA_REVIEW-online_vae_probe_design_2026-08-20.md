# REVIEW: Online VAE Probe Design for Latent Cache Parity

**Date:** 2026-08-20  
**Author:** Kimi  
**Reviewer:** Codex  
**Scope:** Design review only — no implementation yet.

## Background

The 4in1 LIBERO SFT (`action_policy_libero_edge_all`) currently uses **online VAE encoding** per 17-frame window. Earlier attempts to build an offline RGB→latent cache (G0-R12 / exact-window cache) failed parity with `max_abs_diff=4.625`, proving that the offline encoding contract diverged from the online path.

To build a correct latent cache, we need to treat the **online `_encode_vision_item` output as the golden baseline** and force any offline encoder to match it bit-for-bit.

## Objective

Design a probe that:
1. Captures online VAE inputs/outputs during real training.
2. Uses those captures as a baseline to validate an offline cache builder.
3. Can remain active after integration to guard against regression.
4. Can be disabled via config once stable.

## Proposed Design

### 1. Hook Point

Wrap `OmniMoTModel._encode_vision_item` in `cosmos_framework/model/generator/omni_mot_model.py`.

This method is the single online entry point that:
- Accepts a uint8 video tensor (e.g. `[3, 17, 256, 512]` for concat_view).
- Normalizes via `state.to(fp32) / 127.5 - 1.0`.
- Calls `tokenizer_vision_gen.encode(state)`.
- Returns the latent (e.g. `[5, 48, 16, 32]`).

**Implementation mechanism:** add a new callback `OnlineVAEProbeCallback` whose `on_train_start` monkey-patches `model._encode_vision_item` with a wrapper that calls the original and then saves input/output. This avoids modifying `omni_mot_model.py`.

### 2. Saved Artifacts

For each probed window:
- `raw_uint8.pt` — input uint8 tensor before normalization.
- `online_latent.pt` — output latent from online path.
- `meta.json` — metadata:
  - `iteration`
  - `num_views`, `frames_per_view`
  - raw/latent shape and dtype
  - `episode_index`, `start_frame`, `task_index`, `dataset_name` if available in `data_batch`

### 3. Sampling Strategy

Target: cover at least one episode’s worth of windows and all `start_frame % 4` remainders.

- `max_samples`: 200 initially.
- Save on every call to `_encode_vision_item` until the budget is exhausted.
- Run training long enough (tens of iterations over 4 suites) to naturally sample multiple episodes.
- Post-hoc check that saved samples include `start_frame % 4 ∈ {0,1,2,3}`; extend sampling if any remainder is missing.

### 4. Offline Encoder Verification

Standalone script: `tools/g0/verify_latent_cache_parity.py`.

For each probe sample:
1. Load `raw_uint8.pt`.
2. Run the candidate offline encoder, which must use the exact same two operations:
   - `state.to(fp32) / 127.5 - 1.0`
   - `tokenizer_vision_gen.encode(state)`
3. Compare with `online_latent.pt`:
   - `max_abs_diff`
   - `mean_abs_diff`
   - `torch.allclose(atol=1e-5, rtol=1e-5)`
4. Output per-sample PASS/FAIL and aggregate stats.

**Pass criterion:** every sample `max_abs_diff < 1e-4` and shapes/dtypes match. The old failure showed `max_abs_diff=4.625`, so this threshold cleanly distinguishes causal-vs-window encoding bugs.

### 5. Pipeline Integration Guard

After the cache is wired into training:
- Add config `verify_latent_cache=true`.
- For a small fraction of windows (e.g. 1 per 100 iterations), compute the online latent and compare with the cached latent.
- If diff exceeds threshold, fall back to online encoding and log a warning.
- Once stable over a full epoch, set `verify_latent_cache=false`.

### 6. Disabling the Probe

Final state:
- `probe_online_vae=false`
- `verify_latent_cache=false`
- Only the cache read path remains in the training loop.

## Files Expected to Change

- New: `cosmos_framework/callbacks/online_vae_probe.py`
- New: `tools/g0/verify_latent_cache_parity.py`
- Modify: `cosmos_framework/configs/base/experiment/action/posttrain_config/action_policy_libero_edge_all.py` (add probe callback behind env/config flag)
- Future: offline cache builder and `ActionLatentCacheDataset` integration.

## Acceptance Criteria for This Review

- [ ] Hook point is the correct online path (`_encode_vision_item`).
- [ ] Sampling strategy can cover one episode and all `start_frame % 4` remainders.
- [ ] Comparison metric and threshold are strict enough to catch the previous `diff=4.625` failure.
- [ ] Integration guard does not permanently slow down training.
- [ ] No core model source is modified; probe lives in callback/tooling.

## Open Questions

1. Should the probe be triggered by env var, TOML config, or both?
2. How many samples are sufficient to declare the offline encoder trustworthy for all 4 suites?
3. Should the offline cache builder live in `tools/g0/` or be promoted to a first-class dataset in `cosmos_framework/data/`?

---

**Request to reviewer:** please confirm the design before implementation starts.
