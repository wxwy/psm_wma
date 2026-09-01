# R09-B2 P1 production manifest build review

- Request: `4227c6a32d83361f7d498b079a592c95a53c888f`
- Implementation: `4177e83088e6c2e0a2b620bfdf8593e325fc375b`
- Reviewed Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **APPROVE_TO_BUILD_P1_PRODUCTION_MANIFEST**

## Review

The implementation change is narrow: `cache_exists()` now caches the window-key set per `(suite, episode_index)`, while stream order, `identity()`, reverse-index bijection, suite round-robin, ordinal arithmetic, and record serialization remain unchanged. This reduces repeated `torch.load` of the same episode cache from per-record to at most once per episode during the builder.

The cached representation keeps key-presence semantics in the builder. The downstream existing P1 verifier still independently reloads cache entries and requires `isinstance(item["windows"][start_frame], dict)`, plus source hashes, suite-record partition, ordinal/packer arithmetic, cache-window coverage, and dataset-index bijection. Therefore the production artifact is valid only if that verifier returns PASS; builder completion alone is not closure evidence.

The requested production budget is consistent with the frozen production recipe: `optimizer_updates=100`, `grad_accum=16`, `max_samples_per_batch=128`, giving exactly `204800` records on `world_size=1`.

## Authorized scope

One CPU-only build followed immediately by the existing P1 verifier is approved.

Required runtime bounds:

- cwd: `/disk/rl/psm_wma`
- GPU disabled: `CUDA_VISIBLE_DEVICES=`
- LIBERO root: `/disk/rl/data/LIBERO_LeRobot_v3`
- latent-cache root: `/disk/rl/data/LIBERO_LeRobot_v3_cosmos_exact_window_shared_vae_v1`
- output: `artifacts/g0/r09/b2/p1_production_manifest_100x16x128/`
- budget: `100 x 16 x 128 = 204800` records
- shuffle seed: `42`
- after build, run `verify_r09_b2_stream_manifest.py` against the generated `header.json`, `records.jsonl`, suite files, the same LIBERO/cache roots, and current repo root.

Before execution, the output directory must be absent and Git-untracked. This approval is one-shot: if the build or verifier fails after creating any output, do not overwrite/retry that path without a new review.

## Non-blocking note

The builder now caches only window keys rather than the original dict-valued entry check. This is acceptable for this bounded build because the immediately-required P1 verifier independently restores the stronger dict-valued cache-window validation. A builder PASS without verifier PASS must not be treated as valid P1 production evidence.

## Not authorized

This approval does **not** close P1/P4 by itself and does not authorize P4 D005 closure, P5, B2-T, `torchrun`, GPU, model/VAE/weight loading, training, evaluation, inference, or closed-loop execution.
