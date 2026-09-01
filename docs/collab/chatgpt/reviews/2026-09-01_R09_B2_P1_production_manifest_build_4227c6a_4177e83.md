# R09-B2 P1 production manifest build review

- Request: `4227c6a32d83361f7d498b079a592c95a53c888f`
- Implementation: `4177e83088e6c2e0a2b620bfdf8593e325fc375b`
- Reviewed Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **APPROVE_TO_BUILD_P1_PRODUCTION_MANIFEST**

## Scope

This approval is only for the requested CPU-only construction of the full P1 production stream manifest and the mandatory existing P1 verifier pass. It does not close P1/P4 by itself and does not authorize P4 closure, P5, B2-T, `torchrun`, GPU, training, evaluation, inference, model/VAE/weight loading, or broader scope.

## Review

The implementation changes only the cache-window membership lookup in `tools/g0/build_r09_b2_stream_manifest.py`: it memoizes window keys per `(suite, episode_index)` so a cache episode is deserialized at most once by the builder. Stream ordering, `identity()`/`reverse_index()` checks, suite round-robin, record arithmetic, and output schema remain unchanged. The added regression verifies repeated window lookups within an episode issue one `torch.load` and that an absent window still returns false.

The requested production budget is consistent with the frozen matched-run contract: `optimizer_updates=100`, `grad_accum=16`, `max_samples_per_batch=128`, hence exactly `204800` records. The builder computes the count from these arguments and fails if the final record count differs.

### Non-blocking observation

The cached builder now stores only `windows` keys, whereas the old per-record check required `windows[start_frame]` to be a `dict`. A malformed cache entry whose key exists but value is not a dict can therefore pass the builder's precheck. This does **not** authorize a false P1 PASS because the mandatory existing P1 verifier independently reopens cache entries and requires `isinstance(item["windows"][start_frame], dict)`. Therefore the verifier MUST be run immediately after the production build and any verifier failure remains terminal for this attempt. A later cleanup may preserve the exact old builder semantics by caching only keys whose values are dicts.

## Execution conditions

Before the single CPU build:

1. root and `cosmos-framework` worktrees must be clean and Gitlink must equal the checked-out submodule revision;
2. target `artifacts/g0/r09/b2/p1_production_manifest_100x16x128/` must be fresh/nonexistent and untracked;
3. use the frozen values `100`, `16`, `128`, shuffle seed `42`, `world_size=1`, `num_workers=0`;
4. `CUDA_VISIBLE_DEVICES` must be empty; no GPU use;
5. input is limited to existing LIBERO metadata/parquet indices and the existing latent-cache episode files/manifests; no MP4, VAE, model, checkpoint or weight I/O;
6. after build, run `verify_r09_b2_stream_manifest.py` on the generated `header.json`, `records.jsonl`, suite records, canonical LIBERO root and cache root;
7. acceptance requires exactly `204800` records and verifier `status=PASS`; otherwise keep the gate blocked/review and do not advance to P4 closure.

Authorization token for this bounded step: `APPROVE_TO_BUILD_P1_PRODUCTION_MANIFEST`.
