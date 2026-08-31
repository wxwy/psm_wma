# ChatGPT Review — R09-B1 B1-S static closure

- Date: 2026-08-31
- Reviewer: ChatGPT
- Latest reviewed HEAD: `f66f00592075dfad1b3a62a9b4d8a3e3132d7e79`
- Closure request base: `b45898f911f16b714da47f36430efef535f142cb`
- Verifier source root: `519ba245980f7b24789a1a8dec22327b2d7b879e`
- Canonical artifact commit: `fb4b423652bf43abd05e860f4de20ef8933b0acc`
- Submodule/Gitlink: `0381335d58b7988a53e5ef9d209cfaf878cd3077`
- Verdict: **APPROVE_TO_CLOSE_B1_S**

## Summary

上一轮 B1-S verifier 的剩余 blocker 已全部关闭。

当前 B1-S canonical evidence 已形成完整链路：

- runtime wiring source：submodule/Gitlink `0381335`
- hardened verifier source：root `519ba24`
- verifier 从 pushed-clean `519ba24 / 0381335` 运行
- canonical artifact：`artifacts/g0/r09/b1/static_contract.json`
- artifact commit：`fb4b423`
- artifact `status=PASS`
- 22/22 checks true
- artifact recorded root=`519ba24`
- submodule/gitlink=`0381335`
- tool SHA=`8b12088b0f40a9c514cc4ce55657747a29975444acd67314ac0c7cb6d1bdc872`
- artifact 提交以后到当前 closure request `f66f005`，没有 verifier、submodule、runtime 或 artifact 再变化，只有 review/Inbox/bookkeeping。

没有发现新的 B1-S blocker。

## Previous blockers

### CLOSED — representative backward now exercises the real LocalHistoryRuntime path

`tools/g0/verify_r09_b1_static_contract.py` at root `519ba24` now constructs actual history inputs and calls:

```python
model.net.local_history_runtime(
    history_visual_summary=...,
    local_history_action=...,
    history_age_steps=...,
    history_dt_s=...,
    history_mask=...,
)
```

The resulting evidence remains graph-connected before the TTT boundary, while the emitted TTT token is detached.

Canonical artifact confirms:

- `outer_graph_detached=true`
- `encoder_ttt_gradient_detached=true`
- encoder selected grad: present=false, nonzero=false
- `local_memory2llm`: present=true, finite=true, nonzero=true
- `local_memory_modality_embed`: present=true, finite=true, nonzero=true
- `all_present_gradients_finite=true`

This now proves the intended production training path:

```text
history inputs
→ LocalEvidenceEncoder
→ TTT detach boundary
→ Local token
→ local_memory2llm / modality embed
→ native training loss path
```

rather than merely bypassing the encoder.

### CLOSED — actual optimizer membership and gradient facts are hard-gated

The verifier now hard-gates:

- `optimizer_match_sets_nonempty=true`
- `selected_parameter_names_exact_union=true`
- `backend_matches_empty=true`
- `backend_specific_state_empty=true`
- `encoder_ttt_gradient_detached=true`
- `projection_gradient_present_finite_nonzero=true`
- `modality_embed_gradient_present_finite_nonzero=true`
- `all_present_gradients_finite=true`

and final status is derived from `all(checks.values())`.

Canonical artifact records the exact three optimizer keys:

- `local_history_runtime.encoder`
- `local_memory2llm`
- `local_memory_modality_embed`

and the actual matched parameter-name sets. TTT backend matched names are empty.

Therefore the previous issue “facts serialized but not part of PASS” is closed.

### CLOSED — recipe snapshot isolation

Each recipe case now runs in its own subprocess. Default recurrent, B1 opt-in, B1+A1 conflict, and B1+A1-probe conflict no longer share mutable import/reload state.

Canonical artifact confirms:

- default backend = recurrent
- B1 backend = ttt_fast_weight
- exact B1 optimizer keys
- A1 mutual exclusion PASS.

### CLOSED — canonical artifact freshness/provenance

The artifact at current HEAD records:

- `source.root_revision=519ba245980f7b24789a1a8dec22327b2d7b879e`
- `submodule_revision=gitlink_revision=0381335d58b7988a53e5ef9d209cfaf878cd3077`
- root/submodule clean=true
- current verifier tool SHA
- canonical command hash
- status=PASS
- all 22 current hard gates true.

Artifact commit `fb4b423` has direct parent `519ba24`, so no technical source change occurred between clean verifier source and artifact recording.

From `fb4b423` to current request `f66f005`, changed files are only ChatGPT review/Inbox collaboration docs. The B1-S evidence itself is unchanged.

## Reconfirmed B1-S contract

Current closure evidence proves:

- default recurrent path preserved;
- explicit TTT opt-in only;
- B1/A1 flag and A1 probe mutual exclusion;
- B0 TTT dimensions/segment steps unchanged;
- TTT backend zero parameters / empty state_dict;
- per-forward fresh fast state;
- outer `no_grad` / `inference_mode` fail-fast before state mutation;
- training normal-grad path PASS;
- no outer graph through TTT adaptation;
- exact Local optimizer allowlist and actual membership;
- encoder adaptation path detached;
- Local projection/modality gradients valid;
- root/submodule/Gitlink provenance clean and exact;
- no GPU or eval/inference/closed-loop execution.

## Scope audit

B1-S implementation remains limited to the previously approved scope:

- model selector/default config;
- LIBERO Edge recipe opt-in and mutual exclusions;
- TTT training-only fail-fast;
- minimal runtime backend selection;
- targeted CPU tests;
- static verifier/artifact.

No evidence of:

- GPU execution;
- B1-G training smoke;
- eval/inference/closed-loop enablement;
- multi-GPU;
- long training;
- matched SR;
- backend freeze;
- RoboTTT/shared-MoT import;
- Global/Agent/RL scope creep.

## Verdict

**APPROVE_TO_CLOSE_B1_S**

B1-S static/runtime-wiring + CPU contract may be closed.

This approval does **not** authorize B1-G.

The next Gate, if pursued, must be a separate request with explicit user-approved GPU command and independent verdict such as `APPROVE_TO_RUN_B1_SMOKE`.

## Gate state

```text
R09-B0 = CLOSED
R09-B1 preflight = APPROVED
R09-B1 B1-S = APPROVE_TO_CLOSE_B1_S
B1-G GPU smoke = BLOCKED / separate approval required
eval/inference/closed-loop = BLOCKED / separate Gate required
multi-GPU = BLOCKED
long training = BLOCKED
matched SR = BLOCKED
backend freeze = BLOCKED
RoboTTT/shared-MoT = BLOCKED
Global / Agent / RL = BLOCKED
```
