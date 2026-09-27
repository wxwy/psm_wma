# PSM-WMA V3 Stage B2 Resource Profiles v0.2 — 4090 Smoke vs 8xH100 Formal

- Date: 2026-09-27
- Supersedes v0.1 only where this document changes the Local-Memory trainable inventory.
- Current smoke host: RTX 4090 24GB.
- Formal host: 8xH100.
- Stage B1 closure pair: root `93db96df841a14c4c3ef73bf6b4488142adcf567` / child `1ecebf1ab2fa64bc1d5906959c4cb1fe1d1edc5a`.

## Correction to v0.1

B2 needs a new Local-Memory injection bridge from Local32 into the Cosmos hidden space. If that bridge is frozen at zero, or otherwise blocks input gradients, an outer policy loss cannot train the upstream TTT parameters.

Therefore "TTT-only" means **Local-Memory subsystem only**, not only the pre-B2 B0 modules.

For Edge hidden_size=2048, the 4090 trainable Local-Memory inventory is:

- LocalEvidenceEncoder: 29,440 parameters.
- ContinualTTTLocalMemoryCore: 66,240 parameters.
- `local_memory2llm: Linear(32,2048,bias=True)`: 67,584 parameters.
- `local_memory_modality_embed: [2048]`: 2,048 parameters.
- Total: **165,312 trainable parameters**.

All four groups must live under stable parameter names containing `local_memory`, and the 4090 smoke optimizer remains:

```text
keys_to_select = ["local_memory"]
```

This keeps all host generation/action/reasoner parameters frozen while allowing the native outer loss to update the complete Local-Memory path.

## Bridge initialization

`local_memory2llm.weight` must be non-zero at the first outer backward. Use the same fan-in rule as other input projectors:

```text
std = 1 / sqrt(local_memory_dim)
trunc_normal_(weight, std=std, a=-3*std, b=3*std)
bias = 0
```

`local_memory_modality_embed` uses the normal hidden embedding scale:

```text
std = 1 / sqrt(hidden_size)
trunc_normal_(embed, std=std, a=-3*std, b=3*std)
```

Do not zero-initialize the projector.

## 4090 profile

Trainable only: the 165,312-parameter Local-Memory inventory above.

Frozen:
- moe_gen
- time_embedder
- vae2llm / llm2vae
- action2llm / llm2action / action_modality_embed
- all reasoner/host parameters.

Freezing must not use no_grad/inference/detach across the Local prefix → native loss path.

Smoke geometry remains:
- S1: one slot, T=16 segment with only 1–2 valid terminal consumers, one optimizer step.
- S2 if memory permits: one slot, full T=16, one optimizer step.
- K=4, local_dim=32, raw15, policy chunk32/33-frame remain frozen.

## 8xH100 formal profile

Formal trainable set:
- current Edge generation/action-policy allowlist
- plus the complete Local-Memory inventory.

The 4090 profile must be an explicit smoke-only config/override and must never overwrite the formal recipe default.

## Required gradient witness

For the 4090 smoke:
- every required Local-Memory parameter group receives finite gradient;
- at least one TTT-core slow parameter has non-zero gradient on the **first** outer backward;
- local_memory2llm receives finite non-zero gradient;
- no frozen host parameter receives a gradient;
- one optimizer step changes Local-Memory parameters;
- sampled frozen host parameters remain bitwise unchanged.
