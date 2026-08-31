# ChatGPT Review — R09-B1 B1-S verifier rereview

- Date: 2026-08-31
- Reviewer: ChatGPT
- Latest reviewed root HEAD: `d0ddc5181ececeba7db452739d19ae7de53ef235`
- B1 runtime submodule/Gitlink remains: `0381335d58b7988a53e5ef9d209cfaf878cd3077`
- Previous verdict: `REQUEST_CHANGES` on root `fdd5a7a`
- Verdict: **REQUEST_CHANGES**

## Summary

上一轮 HIGH-1（live module / `importlib.reload()` 污染）已正确关闭：

- verifier 改为每个 recipe case 独立 subprocess；
- default / B1 / A1-conflict / probe-conflict 不再共享 live module state；
- selector 与 optimizer-key snapshot 现在具有隔离性。

上一轮 HIGH-2 也已有明显进展：

- 使用训练同源 `_build_params_with_metadata`；
- 派生 selected parameter names / prefix matches；
- 创建实际 optimizer；
- 输出 gradient facts。

但当前 gradient proof 仍绕过 production Local dataflow，且关键 optimizer/gradient facts 只是写入 JSON、没有进入 `status=PASS` hard gate。因此当前 verifier 仍不能作为 B1-S canonical closure verifier。

Runtime wiring `0381335` 不要求回退或重做。

## Findings

### HIGH-1 — gradient test bypasses `LocalEvidenceEncoder`; cannot prove the frozen production detach contract

Relevant lines:

- `tools/g0/verify_r09_b1_static_contract.py:99-105` — 构造 `LocalHistoryRuntime(encoder, readout, TTT backend)`
- `:111` — 实际 backward 前却直接调用：
  ```python
  token_for_grad, _, _ = model.net.local_history_runtime.recurrent_backend.replay(evidence, mask)
  ```
- `:112` — 再对 projection / modality embed backward。

这条测试路径是：

```text
prebuilt evidence
→ TTT backend
→ local_memory2llm
→ loss
```

而不是 production path：

```text
history visual/action/age/dt
→ LocalEvidenceEncoder
→ TTT backend (detach)
→ local_memory2llm / modality embed
→ loss
```

因此当前 encoder 没梯度只是因为 encoder **根本没参与 forward**，并不能证明 B0 冻结语义“encoder 输出进入 TTT 后被 detach，native loss 不经 adaptation 回传”。

上一轮批准中特别要求的“encoder 无 TTT 回传证明”尚未成立。

#### Required fix

CPU representative backward 必须走真实 `LocalHistoryRuntime.forward(...)`：

1. 构造 finite history inputs：
   - `history_visual_summary`
   - `local_history_action`
   - `history_age_steps`
   - `history_dt_s`
   - `history_mask`
2. 调用：
   ```python
   token, present, evidence = model.net.local_history_runtime(...)
   ```
3. 用返回 token 进入 `local_memory2llm`，并加入 modality embed，构造 representative scalar loss；
4. backward 后机器可读 hard-gate：
   - encoder selected params：grad 应为 `None` 或 exact zero（按实现事实冻结一种口径）；
   - `local_memory2llm`：grad present + finite + nonzero；
   - `local_memory_modality_embed`：grad present + finite + nonzero；
   - TTT backend：zero parameters / zero matched names；
   - token/state outer graph 仍 detached。

这样才能证明“encoder **参与了** production forward，但被 TTT detach boundary 截断”，而不是简单绕过 encoder。

### MEDIUM-1 — matched names and gradient facts are serialized but not hard-gated by `status`

Current code:

- `:114+` builds `gradient_facts`
- `:144` only checks `selected_parameter_names_present = bool(selected_names)`
- `:147` sets:
  ```python
  status = all(checks.values()) ...
  ```
- `:154` serializes detailed `matched_parameter_names` / `gradient_facts`.

Problem:

The runbook explicitly freezes `status=PASS` to hard-gate:

- “三条 exact optimizer key **及匹配名**”
- actual optimizer membership / gradient contract.

But current PASS can still succeed if, for example:

- one exact key has zero matched parameters, as long as some other selected parameter exists;
- projection/embed gradient is missing, non-finite, or zero;
- encoder gradient unexpectedly becomes nonzero through a future wiring regression.

Those facts would appear in JSON but would not fail `status`.

#### Required fix

Add explicit hard gates, at minimum:

- every exact key has a non-empty expected match set;
- selected parameter names equal the union of those three exact-key match sets;
- backend matched names = [];
- encoder detach expectation satisfied;
- projection grad present / finite / nonzero;
- modality-embed grad present / finite / nonzero;
- every present gradient finite.

Do **not** require encoder nonzero; the expected B1 behavior is the opposite.

### MEDIUM-2 — canonical B1-S artifact is still absent

At root `d0ddc51`, remote path:

`artifacts/g0/r09/b1/static_contract.json`

still does not exist.

That is acceptable while fixing the verifier, but means:

- B1-S is not closed;
- no `APPROVE_TO_RUN_B1_SMOKE`;
- no GPU/B1-G.

After HIGH-1 / MEDIUM-1 are fixed:

1. push exact verifier source;
2. run from exact pushed-clean root/submodule with `--require-clean`;
3. generate canonical `static_contract.json`;
4. commit/push artifact;
5. request B1-S closure review.

## Accepted fixes

### CLOSED — prior module-reload contamination

`_recipe_snapshot()` now runs each config case in a separate subprocess, eliminating the shared `importlib.reload()` module-state problem.

### CLOSED/PARTIAL — actual optimizer evidence

Using `_build_params_with_metadata` is the correct direction and should be retained. `matched_parameter_names`, selected names and backend matched names are now derived rather than declared.

### Runtime implementation remains accepted

Submodule `0381335` remains within approved B1-S scope:

- default recurrent;
- opt-in TTT;
- A1 flag/probe mutual exclusion;
- training-only no-grad/inference fail-fast before state mutation;
- no GPU / eval / inference / closed-loop support added.

No runtime rollback is requested.

## Verdict

**REQUEST_CHANGES**

Scope of requested changes: verifier / targeted CPU evidence only.

```text
R09-B0 = CLOSED
R09-B1 preflight = APPROVED
B1-S runtime wiring = ACCEPTED
B1-S verifier/closure = REVIEW / REQUEST_CHANGES
B1-G GPU = BLOCKED
eval/inference/closed-loop = BLOCKED
multi-GPU = BLOCKED
long training = BLOCKED
matched SR = BLOCKED
backend freeze = BLOCKED
RoboTTT/shared-MoT = BLOCKED
Global / Agent / RL = BLOCKED
```
