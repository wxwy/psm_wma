# PSM-WMA v0.3.5 Canonical Native Feature / Config / Optimizer / Checkpoint CPU/static Implementation 设计 v0.1

**日期**：2026-09-11
**状态**：docs-only implementation design；待同 SHA 三方审核。
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-FEATURE-CONFIG-OPTIMIZER-CHECKPOINT-CPU-STATIC-IMPLEMENTATION-DESIGN`

## 1. 前置、目标与禁止范围

唯一前置 authority 为 composite refreeze design v0.1+v0.2+v0.3，其 closure formal root=`5ede9ac264518ccdbca1cdbc24f4e0694b6cf85a`、child/Gitlink=`f49f568923555fe15efe546925cbe6cc9140170e` 已获 ChatGPT/MM/Kimi 同 SHA `APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_FEATURE_CONFIG_OPTIMIZER_CHECKPOINT_REFREEZE`。本设计只授权下一提交实现小型 in-memory CPU/static contract，不能重新解释任何已冻结 identity 或 progress semantics。

禁止真实 checkpoint/data/cache I/O、DCP、CUDA/GPU、torchrun、native `OmniMoTModel` forward/loss/backward、optimizer/scheduler step、sidecar、trainer、packer/producer、训练、评测、推理或 LIBERO4IN1。fixture 只能构造内存 `nn.Module`、tensor、detached optimizer/scheduler；不得将 public path monkeypatch 成已实现。

## 2. 精确 child 白名单

后续 implementation commit 只能修改以下两个 child 文件：

1. `cosmos_framework/model/generator/mot/config_checkpoint_contract.py`；
2. `cosmos_framework/model/generator/mot/config_checkpoint_contract_test.py`。

不得修改 model config、`omni_mot_model.py`、Local evidence/core、runtime authority/adapter/scheduler、trainer、checkpoint backend、recipe、数据或测试基础设施。当前 `OmniMoTModelConfig` 和 active owner 的源码只作为 identity 读取依据；若实施中发现其没有必要字段或要求改动白名单外文件，立即停止并新建设计 Gate。

## 3. 必须实现的 exact in-memory contract

`config_checkpoint_contract.py` 必须提供一个 versioned exact `FeatureConfigIdentity`，键集严格等于 v0.2 §2 的 15 个 active fields 加 `schema`；构造/反序列化均拒绝缺失、未知、bool masquerading、值漂移或任何 noncanonical active-TTT组合。当前 child CPU/static compatibility 只接受 resolved `k_local=1`；不得在本 Gate 实现 multi-slot 放宽。

payload 的 `BaseIdentity` 必须严格等于 v0.2 §3 的六键 schema：`schema`、`child_git_revision`、`canonical_model_config_sha256`、`checkpoint_source_fingerprint`、`manifest_sha256`、`source_sha256`。identity builder 必须从 explicit immutable inputs 生成 canonical JSON SHA-256；禁止 generic default、caller-selected label、空值、路径或时间戳。CPU/static fixture 可用可复算 synthetic descriptors，但不得冒充生产资产。

payload schema 必须显式承载 config/base identities、ordered slow tensors、optimizer identity/state、scheduler identity/state 和 `iteration`。原有隐式 `base_identity=None`、通用 schema default 与只比较 caller expected mapping 的入口必须删除或 fail closed。config、base、tensor、identity、runtime key 和 admission 的全部 preflight 都在首个 live mutation 前完成。

optimizer identity 必须精确比较 fully-qualified class、ordered group names/ordered member names（与 exact registered object identity 对齐）、每组完整 typed hyperparameter mapping、每个 member allowed state schema。scheduler identity 必须精确比较 fully-qualified class、constructor/config、完整 state schema。实现不得把 `state_dict` 可 load 误当 identity 正确。

v0.3 的 progress predicate 必须作为单一 validator 原样实现：`iteration == 0`；所有 canonical optimizer member 均没有 saved state entry，`optimizer.state == {}`；scheduler state exact equals 已 exact-validated detached optimizer/scheduler identity 在构造完成、任何 user-visible step 前的完整 pristine `state_dict()`；optimizer/scheduler 都缺席时二者 identity/state 必须 explicit `null` 且 iteration 仍为零。任一 nonzero iteration、state/step entry、scheduler pristine field drift、单边存在或 identity drift 全部 pre-mutation reject。

`strict_restore_into()` 仅可按以下顺序执行：

```text
decode/clone payload
  -> validate FeatureConfigIdentity + BaseIdentity + inventory/tensors
  -> build detached pristine shadows and validate optimizer/scheduler/progress predicate
  -> validate fresh/quiescent runtime admission
  -> copy existing registered slow tensors once, then load already-validated pristine state
```

禁止创建/替换 module 或 `Parameter`，禁止 post-mutation rollback。仍继承 exact slow inventory、four `w0_fast_*` slow seeds、runtime-fast-state exclusion，以及 empty frontier/pending/transaction/frozen scheduler admission；reject 后所有 live slow bytes、optimizer groups/state、scheduler state、iteration、registered object/adapter identity 与 runtime authorities必须 byte/object-for-object 不变。

## 4. 直接 CPU/static witness

`config_checkpoint_contract_test.py` 必须以小型内存 fixture 覆盖：

1. 15-field FeatureConfigIdentity 的 valid canonical mapping，以及每类 missing/unknown/type/value/bias/backend/dimension drift 零 mutation reject；
2. BaseIdentity 六键及其 digest derivation：child revision/model-config/source fingerprint/manifest/source drift，generic default/caller mapping 均 reject；
3. exact owner/inventory/selectors、four `w0_fast_*` slow seeds 与 runtime-fast-state absence；
4. valid pristine payload 的 round trip：live registered objects 不替换，slow tensors恢复，optimizer state 仍空，scheduler exact pristine，iteration 为零；
5. late tensor/owner/optimizer class/group/member/hyperparameter/schema、scheduler class/config/schema defect 都在首 mutation 前 reject；
6. v0.3 每项 progress witness：nonzero iteration、任意 member state/step、nonempty optimizer state、任意 scheduler pristine field drift、单边 optimizer/scheduler presence，逐项证明 zero live mutation；
7. fresh/quiescent admission 的 committed frontier、每种 pending authority、open transaction/recovery receipt/frozen scheduler transition 均 pre-mutation reject；fresh success 后 frontier empty、adapter exact bound；
8. runtime/sidecar key、mid-episode state及任何真实 filesystem/DCP path 一律 reject/不触达。

不得调用 `optimizer.step()`、`scheduler.step()`、native model forward/loss/backward 或真实 I/O 来构造 witness。

## 5. 验证、提交与 verdict

实施前必须先取得本设计针对同一 root/child pair 的三方唯一 verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_NATIVE_FEATURE_CONFIG_OPTIMIZER_CHECKPOINT_CPU_STATIC
```

实现后只运行该定向 CPU/static test 文件、改动文件 Ruff、目标 `py_compile`、child/root `git diff --check`；结果仅是 synthetic CPU/static evidence。任何 `REQUEST_CHANGES`、SHA 不同或缺一方都保持 REVIEW，不得改 child。

即使 implementation closure 获批，也只关闭 synthetic refreeze contract；真实 checkpoint I/O、optimizer/scheduler activation、single-GPU smoke、sidecar/resume、matched smoke 与 LIBERO4IN1 training 都仍需独立后续 Gate。
