# PSM-WMA Local Memory v0.3.5 Production Active Wiring 实现设计 v0.5

**日期**：2026-09-09

**状态**：docs-only remediation；须三方对本文件 formal pair 同 SHA 批准后才可实现

**任务/Gate**：`G0-R09-B-TTT-V035-PRODUCTION-ACTIVE-WIRING-DESIGN`

## 1. Authority 与范围

本文件 supersede v0.1--v0.4 active-wiring 设计，以 v0.3.5 addendum 与 closed pair `1c6c9ec`/`78b8c9c` 为 authority。仅授权未来 CPU/static 白名单实现；禁止 producer/packer/dataset/manifest/config/optimizer-selector/checkpoint、真实 I/O、GPU、torchrun、训练、评测、推理和 LIBERO4IN1。

v0.4 已冻结的 trainer/model exact runtime registry、main-process prepared injection、owner sealed preflight/resolve、first-member-only retry、one batched internal native seam、marker ABI 和 legacy isolation均继续有效。

## 2. 固定 active optimizer-window mode

active mode 绝不替换 trainer 的 native accumulation trigger。`GAWindowPlan.ga_effective` 必须精确等于 `self.config.trainer.grad_accum_iter`，且 active window 只能在 trainer `grad_accum_iter == 0` 时由 exact initial authority 开始。初始 plan/registry token 在任何 model forward 前验证：

```text
initial_plan.ga_effective == config.trainer.grad_accum_iter
and trainer_grad_accum_iter == 0
```

一旦 registry 创建 active `ga_window_token`，直到该 token 的 final `CompletedWindowCapability` 经 sealed resolution 关闭前，每个 accumulation microbatch 必须：

```text
be active
and carry the same exact registry object
and carry the same exact ga_window_token
and appear at the exact next member index.
```

在 open active window 中 no-marker/legacy batch、不同 token/registry、漏 member、或 active start 于 nonzero normal counter 都必须在 model forward/backward 前 fail closed，零 owner/optimizer/scheduler mutation。反之，normal/no-marker batch 仅在没有 open active token 时可走逐行不变的既有路径。final active member 必须同时满足 `grad_accum_iter + 1 == ga_effective == config.trainer.grad_accum_iter`，因此现有 trainer optimizer boundary 与 owner completed capability 一一对齐。

CPU/static tests 必须覆盖 mismatch `ga_effective`、mid-normal-window start、active/no-marker interleaving、other-token interleaving，并断言 zero forward/backward/owner/optimizer mutation；另覆盖完整 active window 仍用原 trainer counter 触发一次 optimizer boundary。

## 3. trainer-local exact filtered callback dispatch

不改 `utils/callback.py`，不读取/写入未冻结的 callback 私有机制。仅在 `trainer/__init__.py` 新增一个局部 helper：

```text
_dispatch_callbacks(callback_group, hook_name, *, exclude_ttt_lifecycle: bool, **kwargs)
```

它只在 `exclude_ttt_lifecycle=True` 时按 callback group 已有 registration order 迭代其公开 callback collection，跳过 `isinstance(callback, TTTLifecycleCallback)` 的 exact instances；所有其他 callback 以未改参数调用同名 hook。`exclude_ttt_lifecycle=False` 时 trainer 必须继续调用原有 `self.callbacks.<hook>(...)`，不能把 no-marker 也迁移到 helper。

active step 将该 helper 用于 `on_before_backward` 与 `on_after_backward`，并在 active optimizer branch 绕过 `_ttt_lifecycle` abort/found-inf/resolve；no-marker 分支保持既有 callback dispatcher、legacy abort 与 optimizer route 完全不变。该 helper 不是新 callback API，不修改 callback group，不接受 arbitrary type/predicate，不改变 non-TTT callback 的顺序、次数或 args。

CPU/static fixture 必须以一个 pre-existing lifecycle spy、一个真实 `TTTLifecycleCallback` 和至少两个 ordered non-TTT callback spies 证明：active step non-TTT hooks 顺序/参数与 normal 相同、TTT hooks zero call、legacy lifecycle observe/commit/abort/resolve zero call；紧邻 no-marker control 保持原 dispatcher 行为。

## 4. 保留的 active runtime contract

trainer main process 绑定唯一 registry 到 trainer 与 model；它在 `model_ddp.training_step` 前 shallow-copy envelope 注入 `psm_local_memory_active=True` 与 exact prepared capability。prepared/active/sealed capability 都携带 exact registry，reconstructed/other-registry/stale/double object 在 forward 前失败。模型在 `_get_training_inputs` 前从该 registry consume prepared，通过内部 `_run_active_local_memory_native_forward` 对完整 non-callable Mapping payload tuple 一次 batched native seam，并唯一返回 `psm_local_memory_active_forward`。

completion 仅同 registry 消费该 output，按 v0.3.5 weighted objective 做唯一 scaled backward 与 post-backward owner commit。owner `canonical_segment_runtime.py` 的 preflight 在任何 callback/optimizer mutation 前生成 owner seal；post-step resolve 只消费 seal，不重做可失败 identity/boundary checks。skip 保留已提交 fast frontier且不 scheduler step。旧 `TTTLifecycle` 对 active path 全程零调用。

## 5. 白名单与验收

允许：`production_active_wiring.py`、`canonical_segment_runtime.py`、`omni_mot_model.py`、`trainer/__init__.py`、`production_segment_bridge.py` 及相邻 tests。禁止其他所有路径，包括 `utils/callback.py`。

CPU/static 证据至少覆盖：one batched seam/S0/PAD；registry/marker/callback rejection；first-only retry/later terminal；GA exact mode 与 interleaving negative；single weighted scaled backward；owner sealed preflight zero-mutation negatives；success/skip resolve；trainer-local callback filter 的 ordered non-TTT parity/TTT zero-call；pre-existing lifecycle isolation/no-marker parity。仅运行 CPU pytest、py_compile、双仓 diff-check；实现后仍须新 SHA 三方 closure review。
