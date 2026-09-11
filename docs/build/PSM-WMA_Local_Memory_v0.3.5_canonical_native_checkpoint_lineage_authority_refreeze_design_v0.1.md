# PSM-WMA v0.3.5 Canonical Native Checkpoint Lineage Authority Refreeze 设计 v0.1

**日期**：2026-09-12
**状态**：docs-only；待同 SHA 三方审核。
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-CHECKPOINT-LINEAGE-AUTHORITY-REFREEZE-DESIGN`

## 1. 触发原因与目标

本设计只处理 ChatGPT 对 formal root `2d2a32a9ced1f7fd2767e783c9b1dd133164669a` / child `da95139d338ef2ab2cff89d7bdb2a237f711877c` 的 HIGH：两文件、无真实 I/O 的 child 源码不能把其**自身 resulting Git SHA**稳定写入源码常量。把前一 child SHA 写成 `_CPU_STATIC_TRUSTED_LINEAGE_OWNER` 虽移除了 caller 自授权，却错误声称 payload 绑定当前 formal Gitlink。

目标不是再追写一个前序 SHA，而是把两种语义严格分离：

1. synthetic CPU/static contract 只证明内存 identity、zero-mutation preflight 与 fixture 完整性；
2. production Git lineage 只由 future 的 root-owned authority 在可核验 root Gitlink 上派生；
3. 两类 authority 的 schema、API、payload 和验收 witness 不可互相替代。

本 Gate 仅冻结该边界与后续实施路线；不修改 child、不执行真实 checkpoint/data/cache I/O、DCP、CUDA/GPU、torchrun、forward/loss/backward、optimizer/scheduler step、sidecar、训练、评测、推理或 LIBERO4IN1。

## 2. 冻结的 authority 域

### 2.1 `synthetic_cpu_static_v1`

当前已批准的 CPU/static 实现必须改为只接受该域的 fixture authority。它的 canonical mapping 必须含：

```text
schema = "synthetic_cpu_static_v1"
fixture_descriptor_sha256
fixture_manifest_sha256
fixture_source_sha256
```

它不得含 `child_git_revision`、root SHA、路径、时间戳或声称 production asset 的字段。三个 digest 必须来自 fixture 的 versioned canonical descriptor；缺失、未知 key、类型/摘要漂移均在第一个 live mutation 前 reject。该域不能代表 checked-out child，不能作为 production save/restore 或 release provenance。

`FeatureConfigIdentity`、slow inventory、optimizer/scheduler versioned identity、pristine progress 和 fresh/quiescent restore 的既有 CPU/static 合同保持不变；只有把 synthetic fixture 错称 current Git lineage 的 `BaseIdentity` 子合同被本文件 supersede。

### 2.2 `root_gitlink_authority_v1`

真实 checkpoint lineage 必须由一个 future、独立批准的 root-owned authority 生成，而非 child caller、payload 或 child-source hard-coded SHA。其 canonical signed/verified input 至少精确绑定：

```text
root_git_revision
root_tree_sha256
submodule_path = "cosmos-framework"
child_git_revision
child_tree_sha256
canonical_model_config_sha256
checkpoint_source_descriptor_sha256
```

该 authority 的 `child_git_revision` 必须从已验证 root tree 的 `cosmos-framework` Gitlink 读取，并同时验证 child commit/tree 可达；payload 只携带派生结果，不能选择 expected mapping。任何 root SHA/tree、Gitlink、child tree、config 或 source descriptor drift 必须在 live mutation 前 reject。

真实 Git inspection、authority manifest load/verification、签名或等价的 root-owned immutable publication，以及将 authority 注入 runtime 的方式，均属于 future 独立 source-audit/design/implementation Gate。本设计不假装这些能力已存在，也不以 child 相对路径、`git rev-parse`、环境变量或调用者参数替代它。

## 3. 不可混用与迁移规则

1. `synthetic_cpu_static_v1` payload 永远不得被 production/root-Gitlink restore API 接受；`root_gitlink_authority_v1` payload 也不得退回 synthetic API。
2. schema domain 是 exact-match discriminator；不得用缺省、兼容分支、版本降级或 generic mapping 跨域加载。
3. 已有 `d0d733...` / `da951...` synthetic payload 不得迁移为 production lineage；它们只能由 superseded CPU/static fixture test 使用或显式 reject。
4. future production authority 首次落地前，CPU/static Gate 的成功只能表述为“synthetic contract PASS”，不能表述为当前 child checkpoint provenance PASS。
5. future real-I/O Gate 必须提交含 Gitlink authority 的新 formal root/child pair，并重新完成三方审核；不得把本 docs-only 批准视作真实 I/O、checkpoint、GPU 或训练授权。

## 4. 后续最小实施序列

1. 本 design 三方 `APPROVE_TO_DESIGN` 后，单独创建 synthetic CPU/static remediation implementation design；其白名单仍仅 `config_checkpoint_contract.py` 与对应 test，删除/替换 stale child-SHA claim，新增 domain-separation witnesses。
2. 该 implementation closure 后，独立进行 root Gitlink authority source audit：只读验证 root tree、Gitlink、child reachability 和 immutable authority publication 的可信根。
3. 审核通过后才可设计 root-owned authority runtime integration；它必须有独立的真实-I/O 许可与 preflight-first zero-mutation tests。
4. 只有 root-owned authority implementation、真实 checkpoint contract、对应 execution runbook 和后续 GPU Gate 都分别获得三方批准后，才可讨论训练路径；本文件不授权其中任一步。

## 5. 本 Gate 的直接验收 witness

审核者必须能够从设计文本确认：

1. synthetic domain 中不存在任何 current/previous child SHA claim；
2. synthetic domain 的 digest/unknown-key/domain drift 会 fail closed，且 reject 前无 live mutation；
3. synthetic payload 不能被 future production authority 接受，反向也成立；
4. future production child revision 明确取自 root-owned verified Gitlink，绝非 child-source 常量、payload、环境变量或 caller 参数；
5. 本 Gate 没有 child diff、真实 I/O、GPU 或训练授权。

## 6. Verdict

请求唯一 verdict：

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_CHECKPOINT_LINEAGE_AUTHORITY_REFREEZE
```

或 `REQUEST_CHANGES(file:line)`。批准只允许下一份 docs-only synthetic CPU/static remediation implementation design；不授权 child 修改、真实 I/O、DCP、CUDA/GPU、torchrun、forward/loss/backward、step、sidecar、训练、评测、推理或 LIBERO4IN1。
