# PSM-WMA Local Memory v0.3.5 Production Segment Integration 设计 v0.1

**日期**：2026-09-09
**状态**：docs-only；须三方同 SHA 审核后才可实现
**Gate**：`G0-R09-B-TTT-V035-PRODUCTION-SEGMENT-INTEGRATION-DESIGN`

## 1. 目的与前置 authority

本设计把已关闭的 synthetic `CanonicalSegmentRuntimeOwner` 接到一个**仍为 CPU/static 的 production-shaped bridge**。它不接 dataset、dataloader、真实 cache、checkpoint 或 GPU。唯一上游语义为 detailed addendum v0.3.5、migration integration v0.2，以及已关闭的 runtime-owner pair `e74184e` / `556e278`。

目标是冻结一次 native consumer forward 的调用边界：segment 先 scan/gather，valid consumer payload 与对应 Local token 一一传入 native consumer seam；outer loss backward 成功后才通过 owner commit sidecar state。PAD 永不进入 native forward。

## 2. 下一 implementation 白名单

仅可修改/新增以下 child 文件，且仅 CPU/static synthetic fixture：

- `cosmos_framework/model/generator/mot/production_segment_bridge.py`（新增）；
- `cosmos_framework/model/generator/mot/production_segment_bridge_test.py`（新增）；
- `cosmos_framework/trainer/__init__.py`（仅新增最小、显式 bridge 调用 seam）；
- `cosmos_framework/trainer/trainer_local_memory_integration_test.py`（相邻测试）。

不得改 `production_segment_wiring.py`、scheduler/source、dataset/packer/config/registry/checkpoint/callback、模型结构或已有 Local core。

## 3. 精确事务与 ABI

bridge 输入是已经构造并验证的 `SegmentBatch`、exact `CanonicalSegmentRuntimeOwner`、exact `GAWindowPlan` 和候选 `SegmentIdentity`。它不得从 loader 推断或重建这些 authority。

```text
owner.admit -> owner.begin -> owner.prepare
  -> forward.payloads / forward.locals  (only gathered valid consumers)
  -> native consumer seam exactly once
  -> trainer _run_local_memory_segment_backward(... exact plan/index/identity)
  -> owner.commit(exact transaction, exact forward)
  -> owner.admit_next or owner.finish_window
```

native seam 接受 parallel `payloads: tuple[Any,...]` 与 `locals: tuple[Tensor|None,...]`；长度必须相等，gather identity 必须与 forward identity 完全一致。S0 的 Local 必为 `None`，non-S0 必为可见 Local；bridge 不得自行生成 zero token。`consumer_valid=False` 的 PAD 已由 `gather_consumers()` 排除，不能调用 native seam 或贡献 outer loss。

`_run_local_memory_segment_backward` 是唯一 slow-loss scaling/transaction commit authority；bridge 不得第二次 backward、缩放、optimizer step 或 LR step。只有该调用成功后可 `owner.commit`；任何 seam/backward exception 均调用 exact `owner.abort_terminal` 或既有 transient taxonomy，绝不 sidecar commit。

## 4. 状态、禁用与图边界

- owner、adapter pending capability、forward 和 transaction 必须 object-identical；substitute/stale capability fail closed、零 mutation。
- feature-disabled Local 的 bridge 必须完全绕过 scan/native Local injection，保留 native no-Local consumer path 的 payload、loss、grad 与调用次数；不得向 Local parameter 喂假常数。
- bridge 不保存 graph-bearing token/forward 到下一 packed microbatch；只允许 adapter 既有 detached numeric sidecar state 在成功 commit 后 carry。
- 本 Gate 不实现 restore/persistence；snapshot 仅用于 CPU assertion，不写盘。

## 5. CPU/static 验收

新增 fixtures 必须覆盖：

1. 两 valid consumers（S0 + non-S0）各一次 native seam，Local 仅 non-S0 可见，PAD 零调用；
2. successful backward 后精确一次 owner/sidecar commit，finish 后 snapshot frontier 一致；
3. native seam 或 backward failure 无 sidecar commit、pending 被 exact abort 清理、无额外 slow step；
4. substitute/stale forward/transaction/identity fail closed且 scheduler/sidecar零 mutation；
5. disabled parity：native payload/loss/grad/call-count 与 no-Local fixture相同；
6. 定向 pytest、目标 `py_compile`、child/root `git diff --check` PASS。

## 6. 明确禁止与后续

本 Gate 不授权真实 `SegmentBatch` producer/episode queue、manifest/cache 读取、模型真实 forward、config/default/registry、persistent sidecar/checkpoint、CUDA/GPU/torchrun、训练/评测/推理或 LIBERO4IN1。生产 packer/source 与真实 model/trainer integration 必须在本 CPU/static bridge 关闭后另建设计 Gate。
