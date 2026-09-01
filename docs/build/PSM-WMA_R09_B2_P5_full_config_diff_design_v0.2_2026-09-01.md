# R09-B2 P5 Full Resolved-Config Diff 静态设计 v0.2

**状态**：draft。v0.2 取代 v0.1，逐项处理 ChatGPT review
`2026-09-01_R09_B2_P5_full_config_diff_design_04082e4_142f69b.md` 的四个 HIGH。
本阶段只申请后续 root-side exporter/verifier/tests 实现；不执行 config export。

## 目标与边界

P5 将在 **两个彼此独立的新解释器进程** 中，复放 P4 v2 D005 已冻结的实际 compose
输入，分别导出 recurrent 与 `ttt_fast_weight` 的完整 canonical resolved config，并输出
machine-readable JSON Pointer diff。它证明除实际 backend 控制面之外两侧配置相同；不替代训练，
不读取 checkpoint、数据或 VAE。

exporter 只能调用生产 compose 入口
`cosmos_framework.configs.toml_config.sft_config.load_experiment_from_toml`；不得调用
`launch`、`Config.validate`、`instantiate`，也不得创建 trainer、model、dataloader、optimizer、
checkpoint、分布式/CUDA context。禁止 torchrun、GPU、forward/backward、训练、评测与推理。

## 冻结输入与精确 compose

- 每个 backend 的唯一输入是其通过 P4 pair verifier 的 D005 record。父进程逐字解析并验证其
  `command.argv`：固定 interpreter/cwd、`--sft-toml <relative recipe>`，及其后原始顺序的
  trailing Hydra override token。它从 argv 导出 TOML 路径和 `extra_overrides`，禁止手写、并集、
  排序或平行 override 列表。
- 子进程必须在 D005 `command.cwd` 启动，使用 D005 canonical interpreter 和 D005 绑定的
  `PYTHONPATH`。它调用
  `load_experiment_from_toml(frozen_toml, extra_overrides=frozen_trailing_overrides)`，因此
  `trainer.max_iter=100` 与 `trainer.save_zero_checkpoint=true` 必经与生产相同的 TOML→schema→
  Hydra→experiment import→OmegaConf compose 路径，且 trailing override 最后生效。
- parent 先按 D005 `environment.{set,unset,inherit_allowlist}` 构造空白语义环境：只保留
  allowlist，删除 `unset` 及所有非 allowlist 父变量，再应用 `set`；不能以
  `os.environ.update()` 叠加。子进程的实际环境、cwd、interpreter、argv 派生结果写入 envelope；
  任一与 D005 不符立即 FAIL。
- recurrent 与 TTT 绝不在同一长驻 Python 进程 compose。每侧各由一条 fresh-process 请求生成
  一个 JSON 临时文件，父进程只读取/验证结果，避免 experiment module import、Hydra
  `ConfigStore` 或 `GlobalHydra` 的跨 backend 污染。子进程启动后不得预导入 experiment；若检测到
  已导入目标 experiment 或已初始化 Hydra，立即 FAIL。

## Canonical resolved-config grammar

`Config.to_dict()` 的完整树不得删除字段。exporter 以如下递归、确定性的 grammar 编码；所有
dict key 必须为字符串且按 Unicode codepoint 排序，输出 canonical JSON（UTF-8、无空白、
`sort_keys=true`）：

1. `null`、bool、int、有限 float、str 保持 JSON primitive；NaN/Infinity 拒绝。
2. list/tuple 统一为 JSON list，保留顺序；dict 递归编码并排序。
3. attrs/dataclass/config container 递归读取声明字段；OmegaConf container 必须先 resolve，任一
   `${...}` 或 `OmegaConf.is_missing()` 残留立即拒绝。
4. class、function、method 与 Lazy target 规范为
   `{"__psm_type__":"callable","fqn":"<module>.<qualname>"}`；禁止 `repr()`、内存地址、
   仅 `__name__` 或省略 target identity。
5. Enum 规范为 `{"__psm_type__":"enum","fqn":"<module>.<qualname>","name":"<name>"}`；
   path-like value 为 `{"__psm_type__":"path","value":"<as_posix>"}`。
6. 其它任意对象、非字符串 key、循环引用或不可判定 FQN 的 callable 均 fail-closed，绝不 stringify
   或静默丢弃。

verifier 比较该完整树，包含所有 type/target identity。永久 fixture 必覆盖 callable identity 改变
即 FAIL，以及未解析 interpolation/不支持对象即 FAIL。

## Artifact envelope 与 diff 合同

每侧 artifact 为一个完整 envelope，而不是只保存 `resolved_config`：

```text
{
  "schema_version": "r09_b2_p5_full_config_diff_v2",
  "backend": "recurrent|ttt_fast_weight",
  "provenance": {
    "production_source": {"p4_recorded_root_revision": "...", "gitlink_revision": "..."},
    "exporter_source": {"root_revision": "...", "tool_sha256": "..."},
    "inputs": {"p4_record_sha256": "...", "p4_verification_sha256": "...",
               "p1_manifest_sha256": "...", "p3_inventory_sha256": "..."}
  },
  "effective_launch": {
    "command": {"argv": [...], "cwd": "...", "interpreter": {"realpath": "...", "sha256": "..."},
                "toml": "...", "trailing_overrides": [...]},
    "environment": {"set": {}, "unset": [], "inherit_allowlist": [], "effective": {}},
    "world_size": 1, "budget": {...}, "p1_p3_d005_bindings": {...},
    "derived_job_path_local": "..."
  },
  "resolved_config": {...}
}
```

`production_source` 始终来自 P4 record（当前为 recorded clean source），绝不可被后续
root-only exporter commit 覆盖；`exporter_source` 单独记录实现工具来源。closure 时的 evidence
commit 另记在 verification，不能回填为 production source。

diff 按 JSON Pointer 分为 `effective_launch` 与 `resolved_config` 两个 namespace。允许差异仅为：

1. `effective_launch.environment.set/ effective` 中的
   `PSM_R09_B1_TTT_ENABLED`，及其同源 D005 backend 标识；
2. `effective_launch` 的 backend-specific `IMAGINAIRE_OUTPUT_ROOT`、由 JobConfig 推导的
   `derived_job_path_local`，以及该输出根在 resolved config 中的等值字段；
3. resolved config 的实际 `local_history_backend`/TTT enable selector；
4. 上述 switch 所实际派生的 selector/config membership。

world size、budget、D005 argv（包括两个 100-step trailing overrides）、完整语义环境、P1/P3
binding、precision、seed、data/cache root、window manifest、microbatch=128、accum=16、optimizer、
scheduler、EMA、clip 与 offline controls 均须逐值相等。实际 optimizer parameter membership 继续
以 P3 verifier-owned inventory 绑定；P5 不把它伪造为 Config 树字段。任何未白名单 JSON Pointer
差异均 FAIL。

## 实现与验收

实现仅新增 root `tools/g0/` exporter、verifier 与标准库/CPU fixture tests。实现审核通过后，
仍需单独三方授权才可在 clean worktree 执行一次静态 export；届时无论成功或失败均不启动
torchrun/GPU/模型构造/训练。

永久负例至少包括：遗漏、改值或重排 D005 的
`trainer.max_iter=100`/`trainer.save_zero_checkpoint=true`；父环境泄漏；错误 interpreter/cwd；
同进程 sequential compose 或错误 backend 预 import；未解析 interpolation；callable target 变更；
P4/P1/P3 provenance mutation；以及任一未白名单 config/launch path mutation。P5 未 closure 前，
B2-T 继续禁止。
