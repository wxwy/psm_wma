# R09-B2 P4 Launch D005 静态设计 v0.1

**状态**：draft；仅申请静态实现与 CPU 合同审核。  
**前置**：P1 stream manifest、P2 non-mutating capture、P3 GPU-only optimizer inventory 均已关闭。  
**不授权**：B2-T、`torchrun`、模型/数据/VAE/checkpoint I/O、GPU、训练、评测、推理、closed-loop、多卡、backend freeze。

## 1. 目的

P4 只生成并验收两份不可执行的 launch D005：`recurrent` 与
`ttt_fast_weight`。D005 是未来 B2-T 唯一允许执行的命令模板的冻结记录，
而不是 launcher；其中不含批准令牌，静态工具也不允许执行 `command_argv`。

它关闭 P0 的“精确 launcher/D005、world size、100 optimizer updates 与净化
环境”阻塞项，不替代 P5 的完整 resolved-config machine diff。P5 未关闭前，
P4 D005 不得升级为 B2-T 运行申请。

## 2. 输入与固定范围

静态 builder 仅接受已存在的只读输入：

- P1 的冻结 stream manifest 路径、SHA256、count 与五元组 schema；
- P3 attempt-6 的 recurrent/TTT 实际 selector、optimizer membership 与
  Gitlink `21d064f` 的 provenance；
- 同一 model-only base checkpoint 标识、四-suite cache manifests 与 SHA256；
- 两份显式 resolved-config JSON（P5 产生前仅记录其路径/SHA，不宣称 diff 已通过）；
- 用户批准的单卡资源类别、`world_size=1`、明确 microbatch、grad accumulation
  与完成 `100` 个 optimizer updates 的预算。

所有路径必须为根目录内相对路径；绝对路径、`..`、符号链接逃逸、缺失文件、
非 SHA256 值或任何未解析变量均 fail-closed。

## 3. D005 schema

两份记录写至彼此独立且未存在的路径：
`artifacts/g0/r09/b2/p4_launch_d005/recurrent.json` 与
`artifacts/g0/r09/b2/p4_launch_d005/ttt_fast_weight.json`。顶层字段固定为：

```json
{
  "schema_version": "r09_b2_p4_launch_d005_v1",
  "status": "FROZEN_NOT_EXECUTED",
  "backend": "recurrent|ttt_fast_weight",
  "source": {"root_revision": "", "submodule_revision": "", "gitlink_revision": ""},
  "command": {"argv": [], "cwd": "", "sha256": "", "executable": false},
  "environment": {"set": {}, "unset": [], "sha256": ""},
  "budget": {"world_size": 1, "optimizer_updates": 100, "microbatch": 0,
             "grad_accumulation": 0, "global_batch": 0, "samples_per_update": 0},
  "inputs": {"base_checkpoint": {}, "stream_manifest": {}, "cache_manifests": [],
             "resolved_config": {}},
  "outputs": {"run_root": "", "log": "", "checkpoint_step0": "",
              "checkpoint_step100": "", "capture_root": ""},
  "backend_contract": {"selector_keys": [], "optimizer_membership_sha256": "",
                       "fast_state_persisted": false},
  "prohibitions": ["no_execution_without_future_approval"],
  "d005_sha256": ""
}
```

`command.argv` 只能是显式 token 数组，禁止 shell string、环境插值、命令替换、
`sudo`、`bash -c`、网络 URL、`--worker-backend` 或任何执行批准令牌。`executable`
恒为 `false`。builder 只序列化 canonical JSON（排序 key、UTF-8、末尾换行），
再计算 `command.sha256` 与不含 `d005_sha256` 的记录摘要；不得自行填入运行结果。

## 4. 两侧 matched 断言

verifier 必须独立读取两份 D005、P1 manifest 与 P3 inventory，不信任 D005 自报。
除下列字段外，两份 canonical value 必须逐项相等：

1. `backend`；
2. `command.argv` 内显式 backend override；
3. `outputs.run_root/log/checkpoint_*/capture_root` 的 backend 隔离目录；
4. `backend_contract.selector_keys` 与由 P3 verifier-owned selector contract 重算的
   optimizer membership 摘要。

两侧都必须具有相同 root/submodule/Gitlink、base checkpoint、P1 manifest
SHA/count、四 suite cache manifest 集合、seed、precision、deterministic/cudnn、
worker/prefetch、noise schedule、optimizer/scheduler/EMA/clip、microbatch、grad
accumulation、world size、100 updates 及资源上限。两个输出目录不得重叠，且均
不得已存在或已由 Git 跟踪。

## 5. 静态验收和失败分流

新增 builder/verifier 后仅运行标准库/CPU 单元测试、`py_compile` 与
`git diff --check`。最小永久负例包括：

- 任一 `world_size != 1`、updates 不等于 100 或 batch 公式不成立；
- command/environment 含未解析变量、shell、网络或执行 token；
- backend 外字段差异、输出路径冲突、manifest/cache/checkpoint SHA 不一致；
- TTT selector/membership 不等于 P3 verifier-owned contract，或声明 fast state
  将持久化；
- 任何 D005 试图标记 `PASS`、`executed` 或 `executable=true`。

静态产物只能为 `FROZEN_NOT_EXECUTED` 与 verifier `PASS`，代表记录完整且不可执行。
任何缺字段或负例未拒绝均为 `FAIL`；不重试、不启动 B2-T。P5 完整 config diff
和后续 B2-T runbook 通过三方审核并获用户 GPU 授权后，才可新建一次运行申请。

## 6. 预计最小改动

- `tools/g0/write_r09_b2_p4_d005.py`：只读 builder，不导入 torch/Cosmos；
- `tools/g0/verify_r09_b2_p4_d005.py`：fail-closed schema 与 matched verifier；
- `tools/g0/test_verify_r09_b2_p4_d005.py`：CPU/标准库正负回归；
- `artifacts/g0/r09/b2/p4_launch_d005/`：只提交静态 `FROZEN_NOT_EXECUTED` JSON；
- 本设计、`TODO.md`、`SESSION.md`。

在三方批准“静态实现”前，不创建上述工具或 artifact，不修改子模块。
