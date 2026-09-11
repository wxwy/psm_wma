# PSM-WMA v0.3.5 Canonical Native Checkpoint Synthetic CPU/static Remediation Implementation 设计 v0.1

**日期**：2026-09-12
**状态**：docs-only；待同 SHA 三方审核。
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-CHECKPOINT-SYNTHETIC-CPU-STATIC-REMEDIATION-IMPLEMENTATION-DESIGN`

## 1. 前置与严格范围

唯一前置是 lineage-authority refreeze design formal root `cb9fde60b84bacb53006ebaff9484a21a60457a6` / child `da95139d338ef2ab2cff89d7bdb2a237f711877c` 的 ChatGPT、MM、Kimi 同 SHA `APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_CHECKPOINT_LINEAGE_AUTHORITY_REFREEZE`。

本设计仅授权后续一个 synthetic CPU/static remediation implementation，白名单精确为：

```text
cosmos_framework/model/generator/mot/config_checkpoint_contract.py
cosmos_framework/model/generator/mot/config_checkpoint_contract_test.py
```

禁止任何其他 child 文件、真实 checkpoint/data/cache I/O、DCP、CUDA/GPU、torchrun、native forward/loss/backward、optimizer/scheduler step、sidecar、训练、评测、推理或 LIBERO4IN1。

## 2. Superseded 子合同与保留合同

本文件 supersede 先前 CPU/static implementation 中把 `BaseIdentity.child_git_revision`、`LineageOwnerIdentity` 或 `_CPU_STATIC_TRUSTED_LINEAGE_OWNER` 当作当前 child/root Git provenance 的所有表述和实现。它们在 synthetic 路径中必须删除，不得保留 legacy fallback。

下列合同保持逐字 binding：exact 15-key `FeatureConfigIdentity` 及 live ABI binding、canonical slow inventory、optimizer/scheduler versioned/digested identity、pristine-before-first-step relation、detached shadow validation、fresh/quiescent admission、preflight-first single mutation 与 reject zero-live-mutation。

## 3. Exact synthetic `base_identity` mapping

payload key `base_identity` 保持原位以避免本 synthetic contract 的无关接口重排，但其 value 必须是 **exactly five-key** mapping：

```text
schema = "synthetic_cpu_static_v1"
canonical_model_config_sha256
fixture_descriptor_sha256
fixture_manifest_sha256
fixture_source_sha256
```

所有 digest 均为 64 位小写 hex，`canonical_model_config_sha256` 必须 exact 等于 full `FeatureConfigIdentity` canonical JSON SHA-256。后三个 fixture digest 必须分别来自 module-internal、versioned synthetic fixture descriptor/manifest/source 定义；该定义只服务 deterministic in-memory CPU/static test，不能由 caller、payload、环境变量、路径、时钟或 Git 命令选择。

实现必须同时强制：

1. `set(mapping)` 与上述五键 exact 相等，schema exact 相等；
2. `build_base_identity(feature_config=...)` 只从该 module-internal synthetic fixture authority 派生 expected mapping，public save/restore API 不接收 caller-supplied expected identity；
3. `slow_checkpoint_payload()` 和 restore staged preflight 使用相同内部派生值；
4. `child_git_revision`、`root_git_revision`、`root_tree_sha256`、`child_tree_sha256`、路径、时间戳、production/source-kind 伪装字段，及任何 unknown/missing/type/digest drift 都在首次 live mutation 前 reject；
5. 不存在 legacy `LineageOwnerIdentity`、previous/current child SHA、generic identity 或 compatibility branch。

这个 mapping 是 fixture provenance，不是 Git provenance。成功只能报告 synthetic CPU/static checkpoint contract PASS；不得报告 current child Gitlink、production checkpoint provenance 或 production restore PASS。

## 4. Future production domain 的明确排除

`root_gitlink_authority_v1` 不在本 implementation 中实现、导入、模拟或接受。任何声称该 schema 的 mapping 都因 exact synthetic schema/key set 不匹配而 fail closed。未来 production authority 必须单独通过 root-owned Gitlink source audit、design 和 implementation Gate，且只有它可以从 verified root tree 读取 `cosmos-framework` Gitlink。

因此本实现既不以 child-source 常量取代 root Gitlink，也不以测试传参、环境变量或 Git CLI 偷渡 production authority。

## 5. 定向 CPU/static witness

定向 test 必须覆盖且只覆盖内存对象：

1. valid synthetic save/strict restore round-trip，`base_identity` exact 五键且无任何 Git revision/tree/path/time 字段；
2. each synthetic digest、schema、feature-config digest 的 value/type/format drift 和 missing/unknown key，均 pre-mutation reject；
3. legacy mapping containing `child_git_revision`（包括 stale `d0d733...` 与 current `da951...`）reject；production-shaped `root_gitlink_authority_v1` mapping reject；
4. caller 无法向 save/restore/build API 注入 synthetic 或 production expected identity；
5. 所有上述 reject 后，registered slow tensors、optimizer/scheduler groups/state、iteration、Parameter/module/adapter identity 和 runtime authority 均 byte/object-for-object unchanged；
6. 既有 optimizer/scheduler/ABI/pristine/quiescent witnesses 不回归。

不得通过真实文件、Git CLI、environment lookup、forward/backward、optimizer/scheduler step 或 CUDA 来产生上述证据。

## 6. 验证与 verdict

后续 implementation 必须至少执行定向 pytest、目标 Ruff、`py_compile`、child/root `git diff --check`；这些只验证两文件 synthetic scope，不能当作 production provenance 证据。

请求唯一 verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_NATIVE_CHECKPOINT_SYNTHETIC_CPU_STATIC_REMEDIATION
```

或 `REQUEST_CHANGES(file:line)`。批准仅授权本文件 §1 的两 child 文件 synthetic CPU/static implementation；不授权真实 I/O、GPU、训练或 future root-Gitlink authority。
