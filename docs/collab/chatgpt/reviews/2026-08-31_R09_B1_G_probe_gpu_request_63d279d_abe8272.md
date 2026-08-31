# ChatGPT Review — R09-B1-G instrumentation + single-GPU smoke request

- Date: 2026-08-31
- Reviewer: ChatGPT
- Latest reviewed root HEAD: `63d279db2f44a692cfe1ee21645a11bec71271d5`
- Smoke verifier source: `012f0ac5a0fd5dfa07a9ff65dc7fc2208dea8a66`
- B1-G instrumentation submodule/Gitlink: `abe8272cc1502728baf93e76b93d160a7ac5d7e1`
- B1-S canonical closure remains: verifier root `519ba24`, artifact `fb4b423`, runtime root `0381335`
- Verdict: **REQUEST_CHANGES**

## Summary

B1-S remains CLOSED. The new B1-G probe is narrowly scoped and mostly observational, and the proposed "rebuild missing Gate-A iter2, then model-only warm-start a 5-step TTT smoke" is acceptable in principle.

However, the current B1-G request is not ready for `APPROVE_TO_RUN_B1_SMOKE`.

There are three hard blockers:

1. runtime probe / smoke verifier do **not** encode the frozen B0 five-member state schema exactly;
2. the proposed GPU commands are not environment-hermetic, so stale `PSM_*` variables can change the supposedly matched run;
3. the runbook-mandated D005 provenance is absent from the execution sequence and the new verifier does not bind the training commands/source/cache/GPU to the final artifact.

No GPU should run yet.

## Accepted

### B1-S closure remains valid

The instrumentation change does not invalidate the already closed B1-S core contract:

- default backend remains recurrent;
- TTT remains explicit opt-in;
- training-only no-grad/inference fail-fast remains unchanged;
- B1 exact optimizer allowlist remains three Local prefixes;
- no eval/inference/closed-loop support was added.

### Probe is observational in model-state semantics

`cosmos_framework/callbacks/r09_b1_runtime_probe.py`:

- adds no trainable parameter;
- stores no fast state on the model;
- does not modify optimizer groups;
- runs parameter-free TTT replay on local temporary state;
- reads actual optimizer membership/gradients before optimizer step;
- records CUDA peak after steps;
- uses deterministic `arange` evidence in its on-train-start contract probe, so it does not consume model/data RNG.

The synchronous `float(max_abs)` reads may add a small timing synchronization on the first representative step, but do not alter training numerics. This is acceptable for a bounded smoke.

### Gate-A reconstruction is acceptable in principle

The original canonical R08 Gate-A checkpoint was deleted. Rebuilding a new 2-step recurrent Local checkpoint is acceptable as a **replacement warm-start**, without reopening R08, provided:

- current source/default recurrent path is explicitly frozen and clean;
- exact environment is recorded;
- 2-step losses are finite;
- iter2 DCP is complete;
- the B1 model-only load from it succeeds;
- the rebuild is separately provenance-bound and is not silently represented as the historical canonical Gate-A checkpoint.

The request already states it is a rebuilt replacement, which is the correct framing.

## Findings

### HIGH-1 — B1-G state evidence is not B0-exact

Frozen B0 canonical schema is:

```text
W                [32,256] bfloat16 16384 B/sample
pending_evidence  [4,256] bfloat16  2048 B/sample
last_evidence     [256]   bfloat16   512 B/sample
initialized       []      bool          1 B/sample
segment_progress  []      int64         8 B/sample
total                                  18953 B/sample
```

Current probe `cosmos_framework/callbacks/r09_b1_runtime_probe.py:41-46` instead emits:

```python
names = ("W", "pending", "last", "initialized", "progress")
{"shape": list(value.shape),
 "dtype": str(value.dtype),
 "bytes": value.numel() * value.element_size()}
```

This is not the B0 schema:

- names differ: `pending` vs `pending_evidence`, `last` vs `last_evidence`, `progress` vs `segment_progress`;
- `shape` includes the batch dimension instead of `shape_per_sample`;
- `bytes` is whole-batch bytes instead of `bytes_per_sample`;
- dtype is serialized as `torch.bfloat16` rather than the frozen normalized `bfloat16`.

The new smoke verifier `tools/g0/verify_r09_b1_smoke.py` then hard-codes those abbreviated names and checks only total `bytes_per_sample == 18953`. A wrong same-byte shape/dtype could still pass.

This reintroduces the exact class of schema weakness B0 previously fixed.

#### Required fix

Make the probe reuse the B0 exact member representation:

```json
{
  "W": {"shape_per_sample":[32,256],"dtype":"bfloat16","bytes_per_sample":16384},
  "pending_evidence": {"shape_per_sample":[4,256],"dtype":"bfloat16","bytes_per_sample":2048},
  "last_evidence": {"shape_per_sample":[256],"dtype":"bfloat16","bytes_per_sample":512},
  "initialized": {"shape_per_sample":[],"dtype":"bool","bytes_per_sample":1},
  "segment_progress": {"shape_per_sample":[],"dtype":"int64","bytes_per_sample":8}
}
```

The smoke verifier must exact-compare actual runtime members against this frozen expected schema and hard-gate the equality.

Also hard-gate the already-recorded exact state facts that are currently omitted from PASS:

- `segment_present_equal`
- `fresh_present_equal`
- `token_detached`
- `reset_all_mask_members_detached`

Do not only serialize them.

### HIGH-2 — proposed GPU commands are not environment-hermetic

The request calls the two runs matched and says B1's only variable is TTT opt-in, but the commands leave multiple recipe-driving environment variables inherited from the shell.

This repository has repeatedly used the same shell for R08/R09 Normal/Zero/Shuffle/A1/B1 work. Stale values can materially change the run.

Examples:

- `PSM_R09_A1_ENABLED=1` changes the recurrent Gate-A rebuild optimizer allowlist;
- stale `PSM_R09_A1_PROBE_OUTPUT` causes B1 TTT fail-fast;
- `PSM_R08_HISTORY_MODE=zero|shuffle` changes history intervention;
- `PSM_R08_LOCAL_HISTORY_HORIZON` changes the history horizon;
- `PSM_LOCAL_DUMMY_DIM` changes Local dimension used by history runtime;
- `PSM_LOCAL_DUMMY_ENABLED=1` conflicts with Local history;
- `PSM_LOCAL_DUMMY_MODE=shuffle` affects Local/history data handling;
- `PSM_R08_GATE_B_CAPTURE_ONLY=1` can remove the normal checkpoint callback;
- stale probe/capture envs can add unrelated callbacks;
- `LIBERO_MAX_EPISODES` can silently shrink the data source.

`DISABLE_AUTO_RESUME=1` only solves resume selection; it does not sanitize these variables.

#### Required fix

The approved command must explicitly neutralize/freeze all run-affecting env, either via `env -u ...` or explicit values.

At minimum, both runs should freeze:

```text
NPROC_PER_NODE=1
PSM_R08_LOCAL_HISTORY_ENABLED=1
PSM_R08_LOCAL_HISTORY_HORIZON=16
PSM_LOCAL_DUMMY_ENABLED=0
PSM_LOCAL_DUMMY_DIM=32
PSM_LOCAL_DUMMY_MODE=normal
PSM_R08_HISTORY_MODE=normal
PSM_R09_A1_ENABLED=0
PSM_R09_A1_PROBE_OUTPUT=<unset>
PSM_R08_GATE_B_CAPTURE_ONLY=0
LIBERO_MAX_EPISODES=<unset>
LIBERO_LATENT_CACHE_VERIFY_RATIO=0
LIBERO_NUM_WORKERS=0
```

Gate-A rebuild must additionally ensure B1 probe output is unset and `PSM_R09_B1_TTT_ENABLED=0`.

B1 smoke must set:

```text
PSM_R09_B1_TTT_ENABLED=1
PSM_R09_B1_PROBE_OUTPUT=<exact path>
```

Unrelated R07/R08 probe/capture/online-VAE envs should be explicitly unset for both runs unless they are intentionally part of the evidence plan.

### HIGH-3 — D005 and training provenance are not bound to the smoke artifact

The frozen B1 runbook line 49 requires **before launch**:

> D005 sidecar must record full command, root/submodule/Gitlink, checkpoint, cache, GPU, output path and resource cap.

The proposed sequence contains only the two training commands. No D005 sidecar creation/validation is included.

The newly added `tools/g0/verify_r09_b1_smoke.py` also does not close this gap. Its output records:

- verifier argv/tool SHA;
- checkpoint paths;
- runtime probe.

But it does **not** record/hard-gate:

- training root revision;
- training submodule revision;
- training Gitlink revision;
- Gitlink == submodule;
- exact Gate-A rebuild command hash;
- exact B1 training command hash;
- D005 sidecar SHA;
- cache path/provenance;
- base/rebuilt checkpoint provenance;
- GPU identity/resource cap;
- no-network declaration.

It only checks current verifier-time tracked-clean state, which is not sufficient provenance for a completed GPU run.

#### Required fix

Before GPU approval, freeze two D005 sidecars (or one sidecar with two ordered phases):

**Gate-A rebuild phase**
- exact hermetic command;
- cwd;
- source root/submodule/Gitlink;
- base checkpoint;
- LIBERO root/cache;
- GPU/world size/resource cap;
- output/log/checkpoint path;
- network=off;
- expected max_iter=2.

**B1 smoke phase**
- exact hermetic command;
- same source root/submodule/Gitlink;
- rebuilt iter2 checkpoint as explicit model-only input;
- cache/data;
- probe output;
- final checkpoint/log path;
- GPU/world size/resource cap;
- network=off;
- expected max_iter=5.

Then make `verify_r09_b1_smoke.py` consume the sidecar(s) and hard-gate at least:

- recorded root/submodule/Gitlink match the approved source;
- Gitlink == submodule;
- exact command hash(es);
- initial/final checkpoint paths;
- data/cache paths;
- probe/log paths;
- GPU device present;
- expected step counts.

### MEDIUM-1 — no-online-VAE-fallback is a stated PASS criterion but the verifier does not check it

The GPU request explicitly requires “无 online VAE fallback”.

Current `verify_r09_b1_smoke.py` only parses finite total/action loss from the training log. It does not inspect config/log/sidecar for:

- `LIBERO_LATENT_CACHE_ROOT`;
- `LIBERO_LATENT_CACHE_VERIFY_RATIO=0`;
- absence of online fallback;
- cache/data provenance matching the rebuilt Gate-A phase.

Add a machine-readable hard gate. The cleanest route is to bind the exact cache env in D005 and additionally fail if the log/config reports online VAE fallback.

### MEDIUM-2 — replacement Gate-A should have explicit precondition evidence

The reconstruction concept is approved, but before B1 step 1 starts from its output, require:

- 2/2 finite rebuild steps;
- complete `iter_000000002` DCP structure;
- exact rebuilt path;
- source/env provenance;
- no online VAE fallback.

It is useful to enable the existing R08 Gate-A probe for the rebuild, but a full historical R08 re-closure is not required. The subsequent B1 model-only load is itself sufficient fresh-load evidence for the model weights if it succeeds.

Do not label the rebuilt checkpoint as the old canonical Gate-A; label it `Gate-A-compatible rebuilt warm-start`.

## Smoke verifier accepted parts

The newly added verifier is useful and should be retained:

- reads initial/final DCP model state;
- expects removal of exactly the four recurrent GRU tensors;
- bitwise-checks frozen common tensors;
- checks finite total/action losses;
- consumes actual optimizer/gradient probe facts;
- checks CUDA peak.

Those are appropriate B1-G smoke gates. The requested changes are provenance/schema hardening, not a redesign.

## Verdict

**REQUEST_CHANGES**

### Current gate state

```text
R09-B0 = CLOSED
R09-B1 preflight = CLOSED
R09-B1 B1-S = CLOSED

B1-G instrumentation = REVIEW / REQUEST_CHANGES
B1-G single-GPU smoke = BLOCKED / NOT APPROVED
Gate-A-compatible rebuild = concept accepted, execution not yet approved

eval/inference/closed-loop = BLOCKED
multi-GPU = BLOCKED
long training = BLOCKED
matched SR = BLOCKED
backend freeze = BLOCKED
RoboTTT/shared-MoT = BLOCKED
Global / Agent / RL = BLOCKED
```

## Required next submission

Only the following is needed:

1. fix runtime probe + smoke verifier to exact B0 member schema and full present/detach hard gates;
2. provide hermetic Gate-A rebuild and B1 smoke commands;
3. add D005 provenance sidecar(s) and bind them in the verifier;
4. hard-gate cache/no-online-fallback;
5. resubmit the exact run request.

No GPU should run before the next approval.
