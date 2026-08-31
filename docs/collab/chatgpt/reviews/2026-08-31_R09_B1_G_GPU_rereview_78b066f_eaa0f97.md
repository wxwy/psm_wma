# ChatGPT Review — R09-B1-G GPU smoke rereview

- Date: 2026-08-31
- Review request root: `78b066f1758831c92ff06c6a1acaee852fd99997`
- Implementation root: `15225c50dcb1ed07b0b4099ed5854cfe2afd429d`
- Submodule/Gitlink: `eaa0f979974579939bc680ff683cf016bafdbce8`
- Verdict: **REQUEST_CHANGES**

## Summary

The B0-exact state-schema blocker is closed: the runtime probe now emits exact per-member names, per-sample shapes, normalized dtypes, and bytes, and the smoke verifier exact-compares those members. The additional present/detach facts are also hard-gated.

However, the GPU run is still not approved. The provenance/environment fixes currently describe intended launch conditions but do not yet prove or enforce the actual two-phase execution. Three hard blockers remain.

## HIGH-1 — D005 records sanitization but does not execute or prove it

`tools/g0/write_r09_b1_d005.py` writes an `environment` dict and an `unset_environment` list, but it does not launch the command under that environment and does not verify the current shell was sanitized. `--command` is an arbitrary caller-provided string.

Therefore a sidecar can claim `PSM_R09_A1_ENABLED=0`, `PSM_R08_HISTORY_MODE=normal`, or an unset stale probe while the subsequently executed shell command inherits different ambient values.

Required fix: freeze an executable hermetic launcher contract. Either:

- make a wrapper execute the exact command with the recorded env/unsets (`env -u ... KEY=value ...`), writing D005 from the same resolved command; or
- commit exact two-phase shell commands that explicitly contain every required `env -u`/assignment, and make the verifier validate the recorded command string/hash against that approved command contract.

Merely recording intended env/unsets is insufficient.

## HIGH-2 — smoke verifier does not bind the actual two-phase D005 provenance

Current `verify_r09_b1_smoke.py` consumes only one `--training-sidecar` and hard-gates a small subset of B1 fields. It does not hard-gate:

- sidecar `source.root_revision` / `submodule_revision` / `gitlink_revision`;
- Gitlink == submodule;
- source equals the reviewed training source;
- `command_sha256` or exact command;
- GPU identity/cap;
- `expected_steps`;
- LIBERO root/output/log/run-root;
- the separate Gate-A rebuild D005 sidecar;
- Gate-A expected steps=2 / B1 expected steps=5;
- B1 input checkpoint equals the exact rebuilt Gate-A output.

This leaves the previous HIGH-3 provenance requirement open.

Required fix: consume **both** Gate-A-rebuild and B1-smoke sidecars and hard-gate the complete chain. At minimum require reviewed source/Gitlink equality, exact command hash(es), exact checkpoint handoff, data/cache, GPU/world-size/network, output/log/probe paths, and expected step counts. Emit both sidecar SHA256 values in the final artifact.

## HIGH-3 — Gate-A replacement and no-online-VAE criteria are not machine-closed

The current verifier checks B1 finite losses and cache env fields, but it does not machine-verify the rebuilt warm-start preconditions required by the prior review:

- Gate-A rebuild 2/2 finite steps;
- complete `iter_000000002` DCP;
- exact rebuild output path;
- no online VAE fallback during rebuild;
- B1 model-only load from that exact rebuilt checkpoint.

Likewise `LIBERO_LATENT_CACHE_VERIFY_RATIO=0` + non-empty cache root does not itself prove that no online VAE fallback occurred. Add an explicit machine-readable cache-only/no-fallback criterion from config/log/runtime evidence for both phases.

Keep the terminology `Gate-A-compatible rebuilt warm-start`; do not label it the historical canonical Gate-A.

## Accepted

- runtime state members now exactly match frozen B0 names/shape_per_sample/dtype/bytes_per_sample;
- total logical state payload remains 18,953 B/sample;
- `segment_present_equal`, `fresh_present_equal`, `token_detached`, and `reset_all_mask_members_detached` are now in the smoke verifier hard gates;
- B1-S remains CLOSED;
- no GPU/eval/inference/multi-GPU/long-train/shared-MoT/Global/Agent/RL scope creep was found in this patch.

## Verdict

**REQUEST_CHANGES**

B1-G GPU remains **NOT APPROVED**. No GPU run should start yet.

Required next submission is evidence/launch hardening only; no model/algorithm redesign is requested.