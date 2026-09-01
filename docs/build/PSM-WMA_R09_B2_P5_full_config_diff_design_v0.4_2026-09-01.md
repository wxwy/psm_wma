# R09-B2 P5 Full Resolved-Config Diff 静态设计 v0.4

**状态**：draft。v0.4 继承 v0.2/v0.3 的 compose、canonicalization 与 P3 合同，仅修正
P4 recorded-source、evidence 与 exporter 不可共存于同一 root 的执行模型。

## 三根职责

- `production_root`：只读、tracked-clean checkout，HEAD 必为两份 P4 record 的
  `source.root_revision`（当前 `ddb4e0e`），子模块 HEAD/Gitlink 必为 `21d064f`。D005 child
  只在该 root 的 `cosmos-framework` cwd/PYTHONPATH 中 compose。
- `evidence_root`：只读、tracked-clean checkout，保存 committed P4 recurrent/TTT/verification、
  P1 header 与 P3 artifact/PASS verifier。exporter 对这些文件逐字 SHA256 绑定，不能把它作为
  production source。
- `exporter_root`：只读、tracked-clean checkout，保存获批 P5 工具。它独立记录 HEAD、clean、
  exporter/verifier/child source SHA256；不得被写入 child `PYTHONPATH` 或作为 production cwd。

parent 接受这三条 canonical absolute root，拒绝重叠/符号链接混淆。它先独立验证 production
revision+Gitlink、evidence P4 record digest/verification/P1/P3 SHA、exporter source hashes；绝不调用
要求单根同时存在 source 与后提交 evidence 的 P4 live verifier。

## 自包含 child 与父编排

child entrypoint 不在模块导入时依赖 `tools.g0`；parent-only P4/P3/git helpers 均延迟到 parent
分支。child 以 production D005 interpreter/cwd/精确净化 environment 运行，唯一输入为已签名
request JSON；先检查 cwd/interpreter/env/backend precondition，再仅导入 production
`load_experiment_from_toml`，canonicalize 后写 staging tree。CPU subprocess fixture 必证明它在精确
D005 cwd/env 下能到达 pre-compose guard，且不调用 compose。

parent 为每次运行创建唯一 immutable `attempt-<uuid>` staging root；两个 child 都 PASS、完整 envelope
pair verifier PASS 后，才原子 `rename` 到此前不存在的 canonical result root。失败 attempt 保留在
独立 staging 路径并标记 FAIL，canonical result root 不创建。

## Envelope 与 verifier

每侧 envelope 的 `provenance`、`provenance.inputs`、`effective_launch`、`command`、`environment`、
`p1_p3_d005_bindings` 必有精确字段集。verifier 不信任 peer equality：独立绑定 production root
source/Gitlink、evidence P4 record/verification/P1/P3 SHA、P3 PASS SHA、exporter root revision/clean 与
三工具 SHA。P3 common path/SHA/PASS 必等于 evidence；backend contract 由 evidence P3 规则重算。
resolved backend 与完整 selector list 均逐侧精确校验，之后才允许 JSON Pointer backend diff。

实现批准后仍须独立三方授权才可做一次静态 compose；不授权 torchrun/GPU/训练。
