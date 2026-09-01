# R09-B2 P4 Launch D005 静态设计 v0.1

**状态**：draft；已按 ChatGPT `701d410` 的 cwd/解释器绑定意见修订，须重新审核。
**前置**：P1 stream manifest、P2 non-mutating capture、P3 GPU-only optimizer inventory 均已关闭。  
**不授权**：B2-T、任何 `torchrun` 执行、模型/数据/VAE/checkpoint I/O、GPU、训练、评测、推理、closed-loop、多卡、backend freeze。

## 1. 目的

P4 只生成并验收两份不可执行的 launch D005：`recurrent` 与
`ttt_fast_weight`。D005 是未来 B2-T 唯一允许执行的命令模板的冻结记录，
而不是 launcher；其中不含批准令牌，静态工具也不允许执行 `command_argv`。
它必须绑定 production recipe 实际读取的 argv/env 控制面，不能以平行 metadata
替代实际启动输入。

它关闭 P0 的“精确 launcher/D005、world size、100 optimizer updates 与净化
环境”阻塞项，不替代 P5 的完整 resolved-config machine diff。P5 未关闭前，
P4 D005 不得升级为 B2-T 运行申请。

## 2. 输入与固定范围

静态 builder 仅接受已存在的只读输入：

- P1 的冻结 stream manifest 路径、SHA256、count 与五元组 schema，并绑定到
  `PSM_R09_B2_STREAM_MANIFEST_ROOT`；
- P3 attempt-6 的 recurrent/TTT 实际 selector、optimizer membership 与
  Gitlink `21d064f` 的 provenance；
- 同一 model-only base checkpoint、四-suite cache manifests 与 SHA256，分别绑定到
  `BASE_CHECKPOINT_PATH`、`LIBERO_LATENT_CACHE_ROOT`，并绑定 `LIBERO_ROOT`、
  `EDGE_POLICY_CHECKPOINT`、`WAN_VAE_PATH` 与离线 HF/Transformers 控制；
- 两份显式 resolved-config JSON（P5 产生前仅记录其路径/SHA，不宣称 diff 已通过），
  且 D005 的 argv 必须包含 production-supported `trainer.max_iter=100` override；
- 单卡 launch convention：`torchrun --standalone --nnodes=1 --nproc-per-node=1`，
  `CUDA_VISIBLE_DEVICES=0`，以及明确 microbatch、grad accumulation 与完成 `100`
  个 optimizer updates 的预算；
- backend-specific `IMAGINAIRE_OUTPUT_ROOT` canonical absolute realpath，以及 recipe
  `job.project/group/name`，用于独立推导真实 `JobConfig.path_local`、checkpoint
  directory 与首次运行前的 freshness 断言。
- canonical absolute `cosmos-framework` root、其 `.venv/bin/python` interpreter 的
  文件 SHA256，以及仅相对此 cwd 解析的
  `examples/toml/sft_config/action_policy_libero_edge_all.toml`。

仓库拥有的 recipe、P1 manifest 与 D005 artifact 必须为根目录内相对路径，拒绝绝对
路径、`..`、符号链接逃逸。外部 runtime asset（checkpoint、VAE、Edge processor、
LIBERO/cache root、Python executable、`IMAGINAIRE_OUTPUT_ROOT`）必须是 canonical
absolute realpath，且位于 verifier-owned allowlisted root 内；每项记录 kind、realpath、
文件 SHA256 或递归文件清单 SHA256。由 production job path 推导的 run/log/checkpoint/
capture 输出同属 external output root，但其 D005 声明必须等于该推导值。缺失、非
SHA256、未解析变量、仓内路径逃逸或外部路径不在 allowlist 均 fail-closed。

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
  "command": {"argv": [], "cwd": "", "interpreter": {}, "sha256": "", "executable": false,
              "launcher": {"kind": "torchrun", "nnodes": 1, "nproc_per_node": 1,
                           "standalone": true},
              "effective_overrides": {"trainer.max_iter": 100, "trainer.save_zero_checkpoint": true}},
  "environment": {"set": {}, "unset": [], "inherit_allowlist": [], "sha256": ""},
  "budget": {"world_size": 1, "optimizer_updates": 100, "microbatch": 0,
             "grad_accumulation": 0, "global_batch": 0, "samples_per_update": 0},
  "inputs": {"base_checkpoint": {}, "stream_manifest": {}, "cache_manifests": [],
             "resolved_config": {}, "external_assets": {}},
  "outputs": {"job_identity": {"project": "", "group": "", "name": ""},
              "run_root": "", "log": "", "checkpoint_step0": "",
              "checkpoint_step100": "", "capture_root": "", "fresh_before_launch": true},
  "backend_contract": {"ttt_enabled_env": "0|1", "selector_keys": [], "optimizer_membership_sha256": "",
                       "fast_state_persisted": false},
  "prohibitions": ["no_execution_without_future_approval"],
  "d005_sha256": ""
}
```

`command.cwd` 固定为 canonical absolute `<repo>/cosmos-framework` realpath，且 verifier
必须逐字要求该值；根仓 cwd、任意其它 cwd、符号链接 alias 或缺失 cwd 均拒绝。
`command.argv` 只能是显式 token 数组，第一项固定为 `command.interpreter.realpath`
（该 executable 的 SHA256 必与 D005 外部资产记录一致），随后固定为 `-m
torch.distributed.run --standalone --nnodes=1 --nproc-per-node=1 -m
cosmos_framework.scripts.train`。禁止 bare `torchrun`、PATH-dependent launcher 或任意
其它 Python executable。`--sft-toml` 只能为上述 cwd 下的唯一 framework-relative
`examples/toml/sft_config/action_policy_libero_edge_all.toml`；禁止绝对/不同 cwd 语义的
TOML 表示。argv 还须明确包含 `trainer.max_iter=100` 与
`trainer.save_zero_checkpoint=true`；禁止 shell string、环境插值、命令替换、`sudo`、
`bash -c`、网络 URL、`--worker-backend` 或任何执行批准令牌。`executable` 恒为 `false`。
builder 只序列化 canonical JSON（排序 key、UTF-8、末尾换行），再计算
`command.sha256` 与不含 `d005_sha256` 的记录摘要；不得自行填入运行结果。

`environment.set` 必须包含 production 实际消费的：
`PSM_R08_LOCAL_HISTORY_ENABLED=1`、`PSM_R09_B1_TTT_ENABLED=0|1`、
`PSM_R09_B2_STREAM_MANIFEST_ROOT`、`LIBERO_NUM_WORKERS=0`、
`LIBERO_LATENT_CACHE_ROOT`、`LIBERO_LATENT_CACHE_VERIFY_RATIO=0`、`LIBERO_ROOT`、
`BASE_CHECKPOINT_PATH`、`EDGE_POLICY_CHECKPOINT`、`WAN_VAE_PATH`、
`HF_HUB_OFFLINE=1`、`TRANSFORMERS_OFFLINE=1`、`CUDA_VISIBLE_DEVICES=0`、
`PYTHONPATH=<canonical cosmos-framework>` 与 backend-specific
`IMAGINAIRE_OUTPUT_ROOT`。`torchrun --standalone` 是唯一允许的 env:// rank source；
因此 D005 不得自行设置 `RANK`、`WORLD_SIZE`、`LOCAL_RANK`、`MASTER_ADDR` 或
`MASTER_PORT`，verifier 从 launcher 精确推导 `world_size=1` 并拒绝冲突 rank/world
变量。recurrent 必为
`PSM_R09_B1_TTT_ENABLED=0`，TTT 必为 `=1`；verifier 从该值独立推导 production
selector，并与 P3 artifact 的排序 `selected_by_optimizer` 名称集合 canonical-JSON
SHA256 比较。`environment.unset` 必须列出所有已知会改变 backend、probe、online VAE、
checkpoint/tokenizer/cache 或网络语义的变量；`inherit_allowlist` 是唯一可继承的键集，
任何未列入但命中 `PSM_*`、`LIBERO_*`、`*_CHECKPOINT*`、`*_CACHE*`、`HF_*`、
`TRANSFORMERS_*`、`WAN_VAE_*` 或代理变量的父环境键均 fail-closed。

verifier 必须从 `IMAGINAIRE_OUTPUT_ROOT` 与 effective `job.project/group/name` 复现
`JobConfig.path_local`，并强制 `outputs.run_root`、`outputs.log`、`outputs.capture_root`
及 `outputs.checkpoint_step0/100` 为该目录的确定性子路径。两个 backend 的实际
`path_local`/`checkpoints` 必须不同，运行前均不存在、未 Git 跟踪，且不存在
`checkpoints/latest_checkpoint.txt`、任何 `checkpoints/iter_*` 或其它 same-job 文件；
否则可能优先完整 resume，必须 fail-closed。`checkpoint_step0` 只因 argv 实际设置
`trainer.save_zero_checkpoint=true` 才允许作为 required output。

## 4. 两侧 matched 断言

verifier 必须独立读取两份 D005、P1 manifest 与 P3 inventory，不信任 D005 自报。
除下列字段外，两份 canonical value 必须逐项相等：

1. `backend`；
2. `environment.set.PSM_R09_B1_TTT_ENABLED`（recurrent=`0`、TTT=`1`）及由其实际
   派生的 selector/membership；
3. backend-specific `IMAGINAIRE_OUTPUT_ROOT` 及由实际 job identity 推导的
   `outputs.run_root/log/checkpoint_*/capture_root` 隔离目录；
4. `backend_contract.selector_keys` 与由 P3 verifier-owned selector contract 重算的
   optimizer membership 摘要。

两侧都必须具有相同 root/submodule/Gitlink、base checkpoint、P1 manifest
SHA/count、四 suite cache manifest 集合、seed、precision、deterministic/cudnn、
`PSM_R09_B2_STREAM_MANIFEST_ROOT`、`LIBERO_NUM_WORKERS=0`、cache root/verify ratio、
noise schedule、optimizer/scheduler/EMA/clip、microbatch、grad accumulation、world
size、`torchrun` 单进程 argv、`CUDA_VISIBLE_DEVICES=0`、argv 中实际
`trainer.max_iter=100`/`trainer.save_zero_checkpoint=true` 及资源上限。两个实际
job/checkpoint 目录不得重叠，且均不得已存在或已由 Git 跟踪。

## 5. 静态验收和失败分流

新增 builder/verifier 后仅运行标准库/CPU 单元测试、`py_compile` 与
`git diff --check`。最小永久负例包括：

- 任一 `world_size != 1`、updates 不等于 100 或 batch 公式不成立；
- metadata 为 100 但 argv 有效 `trainer.max_iter` 仍为 5000，或无显式 100 override；
- metadata `world_size=1` 但 argv 不是冻结的 one-process `torchrun`，或存在冲突的
  rank/world-size env；缺少或非单值 `CUDA_VISIBLE_DEVICES`；
- `command.cwd` 为根仓/任意非 framework realpath/符号链接 alias，或 `--sft-toml`
  不是 framework cwd 下的唯一相对 recipe；
- `command.interpreter` SHA/realpath 正确但 argv 使用 bare `torchrun`、PATH-dependent
  launcher 或不同 Python executable；
- TTT metadata 正确但 `PSM_R09_B1_TTT_ENABLED=0`，或该 env 与实际 selector/P3
  membership 摘要不符；
- P1 manifest SHA 正确但 `PSM_R09_B2_STREAM_MANIFEST_ROOT` 缺失，或其存在但
  `LIBERO_NUM_WORKERS != 0`；cache metadata 正确但 cache root/verify-ratio env 缺失；
- command/environment 含未解析变量、shell、网络、执行 token 或未 allowlist 的继承变量；
- 仓内路径绝对/逃逸，或外部 asset 不是 allowlisted canonical absolute realpath；
- D005 自报隔离输出但 `IMAGINAIRE_OUTPUT_ROOT + job.project/group/name` 推导到相同
  path，或任一 real job/checkpoint directory 已存在、被跟踪、含 `latest_checkpoint.txt`
  或 `iter_*`；
- `checkpoint_step0` 被声明但 argv 未设置 `trainer.save_zero_checkpoint=true`；
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
