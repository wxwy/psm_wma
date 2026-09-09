# PSM-WMA Local Memory v0.3.5 Production Active Wiring 实现设计 v0.6

**日期**：2026-09-09

**状态**：docs-only remediation；须三方对本文件 formal pair 同 SHA 批准后才可实现

**任务/Gate**：`G0-R09-B-TTT-V035-PRODUCTION-ACTIVE-WIRING-DESIGN`

## 1. Authority 与增量

本文件 supersede v0.1--v0.5 active-wiring 设计。v0.5 的 active/native GA 精确对齐、counter-zero 起始、open-token 连续性、active/no-marker fail-closed、sealed resolution、唯一 scaled backward 与全部白名单/禁止范围继续生效。

v0.5 的 §3 把当前 `CallBackGroup` 不存在的 callback collection 误称为公开 collection，因而不可实现。本 v0.6 仅冻结该缺口的最小修正：不新增 callback API，不修改 `utils/callback.py`，只在 active trainer branch 中受限地只读其现存 registration list。该访问是本 Gate 对私有字段规则的唯一、显式豁免。

本 Gate 仍只授权未来 CPU/static 白名单实现；禁止 producer、packer、dataset、manifest、config、optimizer-selector、checkpoint、真实 I/O、CUDA/GPU、torchrun、训练、评测、推理与 LIBERO4IN1。

## 2. 冻结的 trainer-local callback filter

`trainer/__init__.py` 可新增局部 helper：

```text
_dispatch_active_callbacks_excluding_ttt(callback_group, hook_name, **kwargs)
```

helper 必须显式导入：

```python
from cosmos_framework.model.generator.mot.ttt_lifecycle import TTTLifecycleCallback
```

它仅允许在 active Local-Memory branch 的 `on_before_backward` 和 `on_after_backward` 调用，且其唯一私有访问为一次只读 `callback_group._callbacks`。实现必须满足：

1. 不写入、替换、排序、切片赋值、缓存或向 callback group 注册任何对象；不得改变 `_callbacks` list 身份、长度或元素身份。
2. 按该 list 当时的原始 registration order 遍历；对每个非 TTT callback，以原样 `kwargs` 调用同名 hook，调用次数恰为一次。
3. 只跳过 `type(current_callback) is TTTLifecycleCallback` 的对象；不得以名称、duck typing、任意 predicate 或 `isinstance` 扩大排除集合。TTT 子类不是本 Gate 的隐式排除对象，若以后需要该语义必须新建设计 Gate。
4. 每个被调用对象仍必须通过现有 `hasattr`/callable fail-closed 检查；不得吞掉 hook 异常。
5. helper 不得用在 no-marker/legacy branch。该分支必须继续逐字节语义等价地调用原始 `self.callbacks.<hook>(...)` dispatcher，并保留既有 legacy lifecycle/optimizer 路径。

active optimizer branch 同时必须绕过 `_ttt_lifecycle` 的 legacy observe、commit、abort、found-inf 与 resolve 调用。该 helper 不是一般 callback API，不能接受任意排除类型或 predicate。

## 3. 白名单与 CPU/static 证据

白名单延续 v0.5：`production_active_wiring.py`、`canonical_segment_runtime.py`、`omni_mot_model.py`、`trainer/__init__.py`、`production_segment_bridge.py` 及相邻 tests。`utils/callback.py` 仍明确禁止修改。

相邻 CPU/static fixture 必须用一个 pre-existing lifecycle spy、一个真实 `TTTLifecycleCallback`、至少两个 ordered non-TTT callback spies，以及一个 `TTTLifecycleCallback` 子类 spy，证明：

1. active 两个 hook 中，仅 exact-class `TTTLifecycleCallback` 是零调用；非 TTT 与子类 spy 保持 registration order、原参数和一次调用。
2. 调用前后 `id(callback_group._callbacks)`、长度以及逐元素 `id` 序列完全不变。
3. active step 的 legacy lifecycle observe/commit/abort/resolve 均为零调用。
4. 紧邻 no-marker control 仍经原 `self.callbacks.<hook>` dispatcher，真实 `TTTLifecycleCallback` 仍被调用；其顺序、参数、次数和既有 legacy 路径不变。
5. 既有 v0.5 GA exact-mode、interleaving rejection、one native boundary、sealed preflight、success/skip resolution、one weighted scaled backward 证据保持通过。

仅允许 CPU pytest、目标 `py_compile`、子模块及根仓 `git diff --check`。实现后必须以新 root/child formal pair 再次三方 closure review；本文件本身不授予任何运行或训练权限。
