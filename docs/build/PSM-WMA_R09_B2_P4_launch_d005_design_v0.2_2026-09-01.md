# R09-B2 P4 Launch D005 静态设计 v0.2

**状态**：draft，等待三方审核。v0.2 不执行任何训练命令；它仅规范化 v0.1 中已实现的
root-only 静态记录结构，禁止将 v1 名称用于不同字段形状。

## 变更

- `schema_version` 改为 `r09_b2_p4_launch_d005_v2`。
- P4 verifier 固定读取并 SHA256 绑定 committed P1 production header、`records.jsonl`、
  四个 suite JSONL，以及 P3 attempt-6 inventory/PASS verifier；live submodule HEAD 与
  root Gitlink 必须均为 P1/P3 provenance `21d064f`。
- `environment.set` 是唯一允许的显式运行变量，`inherit_allowlist=[]`；`unset` 覆盖 rank、
  所有已知 `PSM_*`/`LIBERO_*` probe、dummy-dimension、cache、online-VAE 与代理语义变量。
- 当前 record 的字段结构固定为：`source`、`command`、`environment`、production `budget`、
  `inputs.{p1_manifest,p3_inventory,external_assets}`、派生 `outputs`、`d005_sha256`。
  verifier 拒绝缺少、额外或不匹配的字段；后续真实 D005 必须在该结构下生成。

## 不变约束

两 backend 只允许 TTT switch、P3 contract 与独立 output root 不同；命令始终为不可执行的
`FROZEN_NOT_EXECUTED`。本设计不授权 torchrun、GPU、模型/数据/权重读取、训练、评测、推理、
P5 或 B2-T。
