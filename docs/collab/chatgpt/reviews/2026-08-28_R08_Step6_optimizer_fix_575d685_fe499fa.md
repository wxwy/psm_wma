# ChatGPT Review — R08 Step 6 optimizer-fix re-review @ root 575d685 / submodule fe499fa

- Date: 2026-08-28
- Reviewer: ChatGPT
- Target root evidence: `575d6851fb8fb7798d4a4a06dcf9e749b1b543b1`
- Target implementation root: `84a4f32abaa35841725a33c4b40f588bde410167`
- Target submodule: `fe499fa1308f2151dd67a7f943cf6386229ea38c`
- Inbox request: `0cf00e01bcb00d3158ec831fc1b9abd20e019046`
- Verdict: **REQUEST_CHANGES**
- GPU Gate A/B: **DO NOT START YET**

## Executive summary

The previous optimizer-visibility HIGH is now genuinely closed.

`fe499fa` moves the trainable R08 runtime from the outer `OmniMoTModel` into `net.local_history_runtime` inside `build_net()`, before parallelization. `_inject_local_history()` now reads the production runtime from `self.net`.

The new unit test also uses the actual production selector `_build_params_with_metadata()` and checks real parameter object identities under the same `model.net.named_parameters()` hierarchy used by the optimizer. This is materially stronger than the previous synthetic substring test.

The production packer trace remains valid and now also records `condition_frame_indexes_action_unchanged=true`.

However, moving the runtime into `net` exposes a new GPU-before-launch initialization bug: the runtime is created while the entire network is on the `meta` device, but the existing `Cosmos3VFMNetwork.init_weights()` never initializes the new runtime after `to_empty()` materializes real storage.

That must be fixed before Gate A.

## Previous HIGH — optimizer visibility: CLOSED

Production hierarchy is now:

```text
OmniMoTModel
└── net
    ├── local_history_runtime
    │   ├── encoder
    │   └── readout
    ├── local_memory2llm
    └── local_memory_modality_embed
```

The production optimizer scans exactly `model.net.named_parameters()` and selects by substring.

The committed test now calls `_build_params_with_metadata()` against a real `model.net` hierarchy and proves the actual parameter objects for:
- `local_history_runtime.*`;
- `local_memory2llm.*`;
- `local_memory_modality_embed`;

are selected, while the unrelated outer module is not selected and no state adapter is present.

This closes the previous optimizer visibility issue.

## HIGH — meta -> to_empty leaves R08 runtime uninitialized

`OmniMoTModel.build_net()` runs under:

```python
with torch.device("meta"):
    ...
    net = Cosmos3VFMNetwork(...)
    if self.config.local_history_enabled:
        net.local_history_runtime = LocalHistoryRuntime(...)
```

So all R08 runtime parameters are meta tensors. Their normal PyTorch constructor `reset_parameters()` calls execute only against meta tensors and do not create persistent numerical values that survive later materialization.

After parallelization, the production path does:

```python
net = net.to(dtype=dtype)
net.to_empty(device=DEVICE)
net.init_weights(buffer_device=DEVICE)
```

`to_empty()` allocates real parameter storage **without copying/initializing values**.

The current `Cosmos3VFMNetwork.init_weights()` explicitly initializes:
- time embedder;
- Vision heads;
- Action heads;
- Sound heads;
- R07 `local_memory2llm` and `local_memory_modality_embed`;
- language model;

but it does **not** initialize `net.local_history_runtime`.

Therefore on real GPU construction, the new R08 encoder/readout can contain uninitialized device memory before checkpoint load. Since these are new parameters absent from the base checkpoint, checkpoint loading cannot be relied on to populate them.

### Impact

Gate A could observe:
- non-deterministic/garbage Local evidence;
- NaN/Inf depending on allocator contents;
- unstable gradients;
- run-to-run behavior unrelated to the intended PyTorch default initialization.

This is a deterministic construction bug, not something worth discovering with a GPU run.

### Required fix

Add an explicit post-materialization initialization contract for the R08 runtime.

Preferred narrow approach:
1. give `LocalEvidenceEncoder` / `StatelessLocalReplayReadout` (or `LocalHistoryRuntime`) an explicit `reset_parameters()` / `init_weights()` method that initializes exactly its own Linear/Embedding/LayerNorm parameters using the intended defaults;
2. call it from `Cosmos3VFMNetwork.init_weights()` when `local_history_runtime` exists;
3. do not reinitialize R07 Local projection or unrelated network weights.

Then add a CPU/meta lifecycle regression that reproduces the real construction semantics:

```text
create runtime under torch.device('meta')
-> materialize with to_empty(device='cpu')
-> call the new explicit R08 init
-> every R08 parameter finite
-> deterministic under fixed seed
-> expected LayerNorm/Embedding/Linear initialization contract
```

At minimum the test must prove that initialization is actually executed after materialization, not merely that a normally-created CPU runtime is finite.

## Runtime/packer trace: PASS

The latest artifact records:
- runtime root `84a4f32`;
- submodule `fe499fa`;
- matching tool SHA;
- mixed valid/all-mask gating;
- exactly one packed Local token for the valid sample;
- all-mask Local absent;
- valid payload shape `[1,5]`;
- Vision mRoPE unchanged;
- Action mRoPE unchanged;
- Vision condition-frame indexes unchanged;
- Action condition-frame indexes unchanged.

At runtime root `84a4f32`, the Gitlink already points to `fe499fa`. The only later root change to `575d685` is artifact/status material, so provenance is accepted.

## Non-blocking multi-GPU FSDP note

The current Edge-all recipe is explicitly single-GPU, so this does not block the immediate Gate A once initialization is fixed.

However, for any future `world_size > 1` run, note that `net.local_history_runtime` becomes part of the root `fully_shard(net, ...)` parameter set, while `_inject_local_history()` calls `self.net.local_history_runtime(...)` outside the normal `net.forward()` entry point.

Root FSDP2 unshard/reshard hooks may therefore not fire for this direct child call. Before enabling multi-GPU R08 training, add a dedicated multi-rank smoke or route Local-history encoding through an FSDP-registered root method / deliberately excluded replicated module.

Do not widen the current single-GPU Gate A solely for this future concern.

## Required next action

Keep Step 6 in `REVIEW`, CPU/static only.

1. Add explicit R08 runtime post-`to_empty` initialization.
2. Add a meta -> materialize -> init regression test.
3. Run CPU/static tests and regenerate evidence only if the production trace/tool changes.
4. Push new submodule/root SHAs and request independent re-review.

After this one initialization issue closes, ChatGPT expects Step 6 to be eligible for **APPROVE_TO_RUN_GPU_GATE_A** for the current single-GPU recipe.

**No GPU and no R09 before that fix.**
