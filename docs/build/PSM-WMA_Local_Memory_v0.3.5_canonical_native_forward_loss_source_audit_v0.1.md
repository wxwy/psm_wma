# PSM-WMA Local Memory v0.3.5 Canonical Native Forward/Loss Source Audit v0.1

**日期**：2026-09-10  
**状态**：docs-only source audit；须三方同 SHA 批准后才可创建 implementation design  
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-FORWARD-LOSS-SOURCE-AUDIT`

## 1. Authority、范围与结论

本审计以 `PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md` §18、§20，及已批准的 canonical production ABI implementation design v0.3 为 authority。它只读取当前 child `5d0e037ced559c07081fd4880c633dc03f325efe`；不改 child、配置、packer、trainer、真实 I/O、GPU、训练或推理。

结论：已关闭的 producer CPU/static bridge 正确在 native packer 前 hard-stop；它不能直接扩展为真实 forward。下一实现前必须独立冻结三项 ABI：

1. immutable gathered producer rows 如何形成 native `SequencePlan`、text、`GenerationDataClean` 的同序 view；
2. native flow consumer term 与 load-balancing auxiliary term 的精确分解；
3. 新 canonical capability 如何在 trainer DDP/GA boundary 只执行一次已 window-normalized backward，并在任何 P2 未授权 GradScaler/optimizer boundary前 fail closed。

旧 row-wise `canonical_segment_forward` capability 不可复用为新 canonical authority。

## 2. 当前 source map

|对象|实际 source|事实|canonical disposition|
|---|---|---|---|
|producer bridge|`omni_mot_model.py:1399-1419`|preflight、registered adapter scan、expected/actual gather 对比后调用 safe prepare，再无条件 hard-stop并 `abort_scan()`|保留 pre-scan、scan、abort authority；禁止删除 hard-stop或直接落 ordinary path。|
|safe gathered preparation|`omni_mot_model.py:1421-1448`|从 `carrier.model_data_batch` copy 创建 text/plan/clean；plan clone后唯一写 gathered Local prefix；返回 native preparation tuple|可复用为 gathered input creator，但必须在新 design中冻结所有 gathered data fields、flat identity和S0/PAD对应关系。|
|ordinary native chain|`omni_mot_model.py:1489-1689`|ordinary path取得 inputs、采样 schedule、在`:1581-1588` pack，随后 noise、CUDA、denoise、`:1661-1669` loss|只能作为 source map；不可调用 `_get_training_inputs()`、不可把 canonical path回退成 ordinary row-wise history injection。|
|packer Local ABI|`packers.py:76-100,244-255`|packer按 caller `sequence_plans`顺序消费；`has_local_memory=True` 时从 dense Local list消费，否则写 `None` prefix|新 producer 必须只生成 gathered valid row；S0 plan存在且 prefix=`None`；PAD不得形成 plan或Local list entry。|
|flow per-instance evidence|`flow_matching.py:55-90`|返回 scalar weighted mean与 `[B]` per-instance mean；当前 canonical `consumer_valid` 不在此函数中表达|implementation design须在 producer gathered axis与该 per-instance axis之间证明 exact cardinality/order；禁止在 total scalar之后补权重。|
|loss aggregation|`omni_mot_model.py:1830-`及 normal call `:1661-1669`|`_compute_losses()`当前返回总 scalar和日志 dict；normal path未公开 canonical `consumer_loss`/`auxiliary_loss` capability|新 design必须最小新增 typed loss split，保留既有 modality/sample scale，且 auxiliary 不得乘 valid-consumer比例。|
|trainer ordinary backward|`trainer/__init__.py:520-555`|ordinary分支执行 `grad_scaler.scale(loss / grad_accum_iter).backward()`|canonical不可走此 scalar division；No-Local必须保持不变。|
|历史 canonical branch|`trainer/__init__.py:896-927`|接受旧 `CanonicalSegmentForward/CanonicalSegmentWiring`，并调用旧 row-wise transaction seam|明确 superseded；新 canonical capability不得伪装成该 output schema。|

## 3. 下一 implementation-design 必须冻结

### 3.1 新的 typed capability

新 capability 必至少绑定同一对象的 request、adapter scan result、gathered native-row view、plan tuple、clean payload、`actual_n_valid`、consumer/auxiliary scalar、prepared scheduler reconcile 与 transaction。它不得携带任意 caller supplied count、旧 `CanonicalSegmentWiring`、旧 active capability 或可替换 callback。

### 3.2 Gather/packer 边界

producer按 `flat(b,t)=b*T+t` 只保留 valid consumer；每个 gathered native row必须同时有同一 source 的 text/plan/clean modality fields。S0是 valid native row但 Local prefix absent；PAD无 plan、无 text/clean item、无 prefix。新 design必须先决定 native clean payload能否以原 field-wise list语义安全 gather；若任一 field不可同序 gather，必须 fail closed并另起 adapter design，禁止制造零样本或插入 fake Local token。

### 3.3 Loss/GA 与 trainer boundary

新 model seam须在 native modality/sample scaling后显式产出：

```text
consumer_loss
auxiliary_loss
actual_n_valid
L_member = plan.objective(member_index, consumer_loss, auxiliary_loss, actual_n_valid)
```

仅新的 canonical trainer dispatcher可在 exact typed capability下调用一次 `grad_scaler.scale(L_member).backward()`；它不得再除 `grad_accum_iter`。P2阶段 enabled GradScaler、optimizer step、skip disposition均必须在不可逆边界前 terminalize、clear/suppress、abort typed scan，且零 fast-state/scheduler/transaction commit。No-Local继续 ordinary branch。

## 4. Required next Gate 与验收

下一 Gate 只能是 docs-only `CANONICAL-NATIVE-FORWARD-LOSS-IMPLEMENTATION-DESIGN`，其白名单、输入/输出 dataclass、native loss split和canonical trainer dispatcher必须先由三方审核。随后才可有独立 CPU/static implementation Gate。

该 design 必含以下 CPU/static witness：stream-major gathered field/order/S0/PAD；per-instance consumer alignment；consumer/auxiliary GA algebra（full valid无 `1/GA²`）；canonical一次 backward无 ordinary `/GA`；enabled scaler/optimizer boundary terminal零提交；No-Local零 canonical construction；旧 canonical/active output schema fail closed。

本 audit 不授权任何代码或真实执行。请求唯一 verdict：

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_FORWARD_LOSS
```
