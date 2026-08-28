# ChatGPT Review — R08 Wan z0 causal-contract sanity runtime @ e7fb1ec

- Date: 2026-08-28
- Reviewer: ChatGPT
- Result commit: `e7fb1ec3f612bb829c5970029fdee701d3b82b57`
- Reviewed diagnostic implementation: `8778b7e3d0504040dd12b1eddaa9fabe32b69759`
- Runtime root commit recorded in artifact: `5ff9327468aa7c507b528c5fc8095c33df3dde02`
- Runtime submodule: `10bc41085de448d60d2f71b342c03a4cfcca9ee1`
- Artifact: `artifacts/g0/r08/gate0_z0_suffix_invariance.json`
- Verdict: **APPROVE_TO_CLOSE_SANITY_CHECK**

## Summary

The one-time Wan z0 causal-contract sanity check passes with the strongest possible outcome.

The committed artifact reports:

- `status = PASS_STRICT_BITWISE`
- 128 anchors total
- 4 LIBERO suites
- all four `start_frame % 4` classes
- 8 anchors per suite/remainder
- 8 unique episodes and 8 unique tasks per suite/remainder
- 128/128 A-vs-B z0 comparisons bitwise identical
- 128/128 A-repeat comparisons bitwise identical
- maximum A-vs-B `max_abs = 0`
- maximum repeat-control `max_abs = 0`
- all compared tensors finite
- first-frame fingerprints match for every A/B pair
- suffix fingerprints differ for every A/B pair
- minimum changed suffix pixel count = 2,166,741
- minimum suffix max pixel difference = 218

This directly confirms that, under the current PSM-WMA Cosmos/Wan exact-window runtime contract, changing the 16-frame suffix does not change latent temporal index 0.

Per the later scope decision, this is interpreted as an implementation/runtime contract sanity check, not as a new discovery about Wan2.2 causality.

## Provenance consistency

The runtime artifact records root commit `5ff9327`, while the diagnostic implementation was reviewed at `8778b7e`.

This is acceptable and verified:

- `tools/g0/verify_r08_z0_suffix_invariance.py@8778b7e`
- `tools/g0/verify_r08_z0_suffix_invariance.py@5ff9327`

have the identical Git blob SHA:

`6ab4487e5151e7082a50d9417a56c0b40a773ec0`

The commits between `8778b7e` and `5ff9327` only add ChatGPT review/inbox documentation; the executed diagnostic code did not drift from the reviewed implementation.

The artifact also records the required deterministic runtime:

- `CUBLAS_WORKSPACE_CONFIG=:4096:8`
- `cudnn_benchmark=false`
- `cudnn_deterministic=true`
- deterministic algorithms enabled
- `torch.bfloat16` Wan compute
- `cuda:0`
- explicit dataset and VAE paths
- exact argv and seed

## Sidecar

The JSON records raw sidecar:

`artifacts/g0/r08/gate0_z0_suffix_invariance.pt`

with SHA256:

`154f18cd8de9e0a065ef9c766649550b6e456723a3a72b708a3dfb22b9d96e5f`

The sidecar is intentionally not committed because it is ~85 MiB. I cannot independently open the local-only file through GitHub, so this review relies on the committed machine-readable JSON plus the recorded sidecar digest.

This is not a blocker because:
- the result is strict bitwise zero across all 128 pairs;
- all per-record z0 SHA/metrics and input fingerprints are present in the committed JSON;
- Codex states the sidecar remains retained locally for mm2/Kimi review.

Keep the sidecar until the remaining independent runtime reviews close.

## First failed launch

The first attempt failed before the diagnostic because clearing `LD_LIBRARY_PATH` hid the venv CUDA 13 `libnppicc.so.13` required by torchcodec.

The successful second attempt used the venv CUDA library path and completed the intended diagnostic. This is an environment-launch failure, not a Gate result, and does not affect the successful artifact.

## Interpretation

Because every tested A-vs-B pair is bitwise identical, there is no tolerance-only ambiguity and no systematic nonzero suffix-dependent signal to inspect.

Therefore the current exact-window `latent[0]` route is accepted for R08 historical visual evidence from the standpoint of the Wan causal runtime contract.

This does **not** prove R08 history construction itself is causal. The next hard checks are the actual history alignment/leakage contracts:
- history visual index strictly `< t`;
- history executed-action index strictly `< t`;
- no current target action leakage;
- no predicted/unexecuted action leakage;
- same-episode identity;
- state/action/visual timestamp alignment;
- episode-boundary handling;
- padding/mask correctness;
- no DataLoader cross-sample contamination.

## Approved next action

ChatGPT side: this sanity check may be closed.

After mm2/Kimi runtime review also closes:
1. mark the old Gate-0 item DONE/closed as a one-time sanity check;
2. do not run further z0 causality experiments;
3. proceed directly to R08 Step 2 causal history dataset/alignment work;
4. keep the project narrative as “upstream Wan causality contract verified in our runtime,” not “we discovered Wan z0 causality.”
