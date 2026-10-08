# Corrected V3 Phase3.5 — Numerical Compatibility Gate Decision v1.0

Date: 2026-10-08
Authority: GPT technical review decision for Owner consideration / execution, following DS_PRO Round-2/3 observational evidence.
Scope: **supplemental Phase3.5 only**. The 2026-10-05 Owner refreeze and historical exact-parity results are not rewritten.

## 1. Reviewed facts

- Full target-atomic cache: B3/B4 integrity passed; B5 (162/162 exact) only compares cache with its original historical VAE builder.
- P3P5 current V3 Wan encode (three task classes, nine windows): global pre-crop max_abs=0.046875, mean_abs≈0.001613, post-crop max_abs≤0.0390625, z0 max_abs≤0.015625; all finite.
- Round 3: DS independently corrected prior report's 4/9 claim to **3/9 z0 non-exact**; same three windows are non-exact for A(cache)-B(new Encode17) and A-C(new Encode1). B-C: 9/9 exact. The raw JSON remains on the training server, not in the root repository.
- In a separate 421-step Local-only sensitivity test with **untrained** parameters and **fallback** `core.step_many`, max visual96 abs difference≈0.0254, overall fast-state relative L2≈9.31e-8, prefix relative RMSE≈0.001661, stepwise inner-loss relative max≈0.01496. These diagnostics do **not** prove trained-policy or required model-owned scan behavior.

## 2. Reject internally contradictory proposed thresholds

The DS table mixed z0 and five-anchor maxima: `0.03125` cannot accept the observed *full five-anchor* pre-crop max `0.046875`.
It also proposed visual96 `max_abs<=0.001` while reporting a separate 421-step max `0.0254`; those are different windows/scopes and are not comparable as a passing bound.
It also described bf16 as fp16. Wan VAE's actual internal dtype is `torch.bfloat16`; absolute ULP spacing depends on exponent, so do **not** universally label all 0.015625 increments "one ULP".

## 3. GPT-reviewed numerical threshold for one independent supplemental probe

The frozen v1.1 P3P5 tool exposes one `--max-abs-threshold` shared by `pre_crop`, `post_crop`, and `z0`. For a strictly **held-out** final probe, accept the bounded numerical tolerance:

`P3P5_MAX_ABS_THRESHOLD = 0.0625`  (1/16 in normalized VAE latent units).

Rationale: observed worst full-latent max was 0.046875 and the next sensible BF16-scale increment is 0.0625. This is a *finite engineering tolerance* for one scoped Gate, **not** a proof of equality or of downstream success. Do not automatically increase it if new windows fail. All strict shape/source/contract, finite, crop and window identity checks remain required.

Do **not** use a separate visual96/fast-state/prefix/inner-loss numerical threshold as an alternative to P3P5 PASS; those are independent contextual diagnostics from different observation scopes and untrained Local fallback.

For final confirmation:
1. Select **three distinct, eligible target-atomic task classes not among** CloseBlenderLid, CloseFridge, CloseToasterOvenDoor. Fix their names/episode identities in the final dry-run report. First/middle/terminal exact windows per task; >=9 total.
2. Run the original V3 read-only parity tool with `--dry-run` and a separate JSON output. Ensure source/cache/VAE/camera geometry/manifest/config hashes match.
3. After dry-run PASS, execute the same selection on a single available H100 with `--max-abs-threshold 0.0625`, `--hash-vae` and a fresh JSON output; strictly no fallback/rebuild/source mutation.
4. Gate can be declared CLOSED by GPT only after reviewing the thresholded report: status PASS, 3 tasks / >=9 exact windows, pre/post/z0 all <= 0.0625, finite, exact identity and matching provenance. Any FAIL remains OPEN and is sent back for root-cause analysis, not tolerance auto-escalation.
5. Keep original P3P5 exact-threshold FAIL observation intact; this dated decision is a narrow numerical-compatibility acceptance only.

The 3-task/9-window obligation remains before **formal long training** under the Owner's 2026-10-05 refreeze.

## 4. Independently authorized GPU readiness

Based on DS_PRO's full-corpus strict preflight PASS, authorize **only**:
- CPU-only `--preflight --snapshot10` on the new exact root commit/unchanged child, using the existing 9126-episode full cache and same official DROID DCP asset paths.
- One fresh eight-H100 optimizer iteration (iter0→1) in a **new isolated job/output namespace**, after snapshot10 PASS and exact root/child/Gitlink clean checks.
- Corrected V3 entry point exclusively: `examples/psm_wma_robocasa_corrected_phase5.py`; **not** legacy `h100.py` or `h3f.py`.
- Parameters: `T=16, B_stream=8, GA=2, K_local=4, world_size=8`, required Local-TTT, raw15/state15/H_pred16, cache-hit fail closed, official `Cosmos3-Edge-Policy-DROID-dcp` fresh model initialization, never iter500.
- For an intentionally one-step bounded run, choose a coherent short schedule (`--max-iter 1 --warmup 1 --save-iter 1`) and report **its own config_digest**. Such a short-run scheduler/config digest differs from intended formal30k and does not certify formal learning-rate/resume parity.
- Report optimizer parameter inventory (generation AND Local), finite outer/action/vision/inner losses, real grads, successful optimizer step, iteration count, wall time/memory, and checkpoint if produced. If code cannot safely stop at precisely one completed iteration, **do not start**; report a blocked safe-execution plan.
- No automatic permission for 3-step+DCP, same-job resume, readiness10 or formal30k; ask for next bounded authorization after reviewer inspects step1.

Tools/documentation root commits change the exact Git SHA even if training code/child is unchanged. The new root SHA must be used in the runtime lock/preflight; never label prior `root=3dc3c90c` preflight as a fresh preflight on a later root.

## 5. Role and evidence

GPT modifies/commits code; DS_PRO performs run/verification and collects evidence only. DS_PRO may run GPU work **only** within the explicit Phase3.5 9-window probe and bounded iter0→1 scopes above; neither scope authorizes 30k training.

The dataset acceptance-receipt tooling remains offline, post-encode, and **not wired into the trainer**. Do not repeat B3/B4/B5, rebuild the 451GB cache or hash the entire corpus just to launch the readiness smoke.

Pending: actual original Round-3 JSON machine audit on the server; new held-out thresholded P3P5 PASS; fresh root snapshot10; bounded one-step evidence; formal training separate authorization.
