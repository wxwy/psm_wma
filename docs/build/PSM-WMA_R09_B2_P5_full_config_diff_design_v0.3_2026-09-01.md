# R09-B2 P5 Full Resolved-Config Diff 静态设计 v0.3

**状态**：draft。v0.3 继承 v0.2 的生产 compose、fresh-process 隔离、canonical grammar、
launch envelope 与 provenance 合同，并且**仅以本文件替换** v0.2 中 P3 binding 的 diff 规则。
它处理 ChatGPT review `2026-09-01_R09_B2_P5_full_config_diff_design_v0.2_77b313c_f004e4d.md`
的唯一 HIGH；不执行 config export、torchrun、GPU 或任何训练相关操作。

## 不变的导出边界

每个 backend 仍在独立 fresh canonical-interpreter 子进程中，以 P4 v2 D005 的净化
`environment.{set,unset,inherit_allowlist}`、cwd、PYTHONPATH 和逐字解析的 `command.argv` 启动，
从 `--sft-toml` 后的原始 trailing override 序列调用生产
`load_experiment_from_toml(frozen_toml, extra_overrides=frozen_trailing_overrides)`。禁止手写或重排
override，禁止 `launch`、`Config.validate`、`instantiate`、trainer/model/dataloader/optimizer/
checkpoint/CUDA context、torchrun、GPU、forward/backward、训练、评测和推理。完整 Config 的
canonical grammar、`effective_launch`+`resolved_config` envelope 及 production/exporter/evidence
provenance 分层，均以 v0.2 为准。

## P3 common-evidence 与 backend-contract 精确拆分

P5 envelope 必显式保存 P4 record 的 `inputs.p3_inventory` 为：

```text
{
  "path": "artifacts/g0/r09/b2/p3_gpu_inventory_attempt6/p3_gpu_inventory.json",
  "sha256": "<共同 P3 artifact SHA256>",
  "backend_contract": {
    "selector_keys": ["..."],
    "optimizer_membership_sha256": "<backend verifier-owned SHA256>"
  }
}
```

以下 JSON Pointer 必须跨 recurrent/TTT **逐值相等**，且与 P4 pair record 和 P3 PASS verifier
独立绑定：

- `/provenance/production_source` 的 root/Gitlink；
- `/provenance/inputs/p3_inventory_path`、`/provenance/inputs/p3_inventory_sha256`，以及若携带的
  P3 verifier/PASS evidence identity；
- P1 manifest、P4 record/verification 与其它 common evidence identity。

以下是唯一可不同的 P3 JSON Pointer，且不能仅靠二侧互异而通过：

- `/effective_launch/p1_p3_d005_bindings/p3_inventory/backend_contract/selector_keys`；
- `/effective_launch/p1_p3_d005_bindings/p3_inventory/backend_contract/optimizer_membership_sha256`；
- `/resolved_config/**` 中由对应 `PSM_R09_B1_TTT_ENABLED` 直接派生、并可映射回上述
  `selector_keys` 的 selector/config membership field。

verifier 必须从共同 P3 artifact 的 verifier-owned recurrent/TTT backend contract 独立重算这些
字段：recurrent 的值只可等于 recurrent contract，TTT 的值只可等于 TTT contract。path/SHA/PASS
identity 的任一差异、backend contract 缺字段/额外字段、或 selector/membership 等于非本 backend
verifier-owned 值均 FAIL。不得把整个 P3 binding 作为笼统白名单，也不得要求 backend contract
跨 backend 相等。

除上述精确 P3 backend-contract 路径外，v0.2 的 diff 白名单不变：TTT switch、其直接派生的
resolved selector/config membership、backend-specific output root/derived path；全部其它 config-tree
及 launch-envelope JSON Pointer（world=1、100-step argv、完整环境、precision、seed、data/cache、
manifest、128×16、optimizer/scheduler/EMA/clip/offline controls）均必须相等，未知 path FAIL。
实际 parameter/optimizer membership 仍由 P3 inventory 证明，P5 不将其伪造成 Config 字段。

## 永久 fixture

标准库/CPU fixture 必含 P4 的真实形状：两侧 P3 `path`/`sha256` 相同，但 recurrent/TTT
`backend_contract.selector_keys` 和 `optimizer_membership_sha256` 分别取其 verifier-owned 值时
PASS。仅改一侧 P3 path 或 SHA 必 FAIL；将一侧 backend contract 改为另一 backend 或任一
非 verifier-owned 值必 FAIL。v0.2 已列出的 D005 100-step override、环境泄漏、同进程污染、
callable identity、未解析 interpolation 与 provenance mutation 负例继续保留。

实现仍仅限 root `tools/g0/` exporter/verifier/标准库 CPU fixture tests；实现批准后，静态 export
仍须独立三方执行授权。P5 未 closure 前，B2-T 继续禁止。
