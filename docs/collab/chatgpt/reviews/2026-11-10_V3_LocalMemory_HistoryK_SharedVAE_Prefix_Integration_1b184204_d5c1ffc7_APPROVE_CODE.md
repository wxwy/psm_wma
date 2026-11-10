# V3 Local-TTT History-K + Shared VAE + Prefix — 最终集成审核与发布回执

- 审核日期：2026-11-10
- 独立审核对象（formal implementation pair）：
  - Root: `1b184204e301a51a7a20ed4dde1a11689589cf2d`
  - Child / Gitlink: `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`
- 发布前 V3 baseline: `e58cef1f53d2382d39c871ce5a50e4acdd5ce268`
- 发布回执：Child `v3-local-ttt` fast-forward 到上述 Child；Root PR #40 标准 Merge Commit `e23fe240c167f9ccc97b4e112ca76c178c5c1416`
- **独立技术结论：`APPROVE_CODE`，仅适用于本次既定 V3 Local Memory 推理集成范围。** Owner 于 2026-11-10 明确要求执行合并。
- 注意：本结论由 GPT 独立技术复核支持，不冒称 Kimi/MM 的额外批准，不代表所有后续 Gate 已关闭。

## 一、审核范围与差异

Root PR #40 是从上述 V3 baseline 到 formal Root 的 72 个提交，1084 个变动文件：其中非证据/会话文档的代码变动集中在 `cosmos-framework` Gitlink、4 个 `scripts/robocasa_eval_v2/` 源文件和 11 个 `tools/v3/` benchmark/test 文件。Child 从 `b0dbd115d03e801ec4d0788c30ee0b0e9655d4db` 到目标 `d5c1ffc7` 为 12 提交无分叉快进，包含 History-K、Shared-VAE 路由和 Prefix 推理的既定小步修复/优化。

不改动 Local Memory 的作用路径、FastWeight/训练语义、原始 Action 块长度、checkpoint；稀疏 K 按 H=16 校验，保持 Sim/Policy 与 Native 事务链路。

审核改动的 1084 个文件均未检测到二进制模型/权重资产；对约 15.2 MB 文本内容做常见 GitHub PAT、AWS key、API key、私钥、Bearer JWT 模式扫描，未命中。这是窄模式扫描，不等于全面秘密审计。

## 二、直接行为证据

1. **此前本 Pair 的独立 CPU scoped Gate**：314/314 PASS，0 failures/errors/skips，1487 source fingerprints unchanged（保留明确列出的历史 W0 deselection，不冒充全仓全绿）。来源：服务器 `_gpt_independent_gates_20261104/issue35_prefix_projection_independent_20261110/independent_final_audit.json`。
2. **集成 CPU Gate**：在同一 Root/Child pair 上跨模块 115/115 PASS、0 fail，记录于服务器 `_gpt_independent_gates_20261104/v3_integration_gate_20261110/independent_four_task_gate.json`。
3. **K16 真实 H100 严格数值**：同真实 source_step=64，四模式 raw15 Action/Vision 精确相同，30 UniPC denoising steps Velocity 精确相同；保留性能波动记录。来源：上述 `issue35_prefix_projection_independent_20261110/independent_final_audit.json`。
4. **真实 10-episode SR 复核**：Local-TTT checkpoint `iter_000027700`，任务 `PickPlaceToasterToCounter`，seed=0，K=16，GPU6/7 Policy、GPU4/5 EGL Sim，sims_per_gpu=2；10/10 valid，10 success，0 failure/invalid/interrupted；`clean_execution=true`、`results_qualified=true`、`unresolved_process_errors=0`、exit=0；每个 episode 均有 `environment_success=true`、`success_latch`、`cleanup_ok=true`，10 份 MP4 保存成功。
   - 服务器输出根：`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/iter27700_pickplace_toaster_newcode_10ep_20261110/`
   - 核心原始证据：`run/summary.json`、`run/tasks/PickPlaceToasterToCounter/episodes/*/result.json`、`logs/fresh.log` 和 `configs/iter27700_pickplace_toaster_10ep_k16.yaml`。
   - 历史 R07 同任务 49/50 (98%)，但评测样本/资源配置不同，不能据此断言性能提升。
5. 新集成此前 CloseFridge/NavigateKitchen/PickPlaceSinkToCounter/TurnOnSinkFaucet 单 seed 各 1 次失败（0/4），均为有效任务失败而不是执行崩溃；10/10 成功排除了“新代码 SR 必然归零”，不代表其他 task 的泛化结论。

## 三、合并操作与回验

- 在 GitHub 上将 `wxwy/cosmos-framework` 的 `v3-local-ttt` 从 `b0dbd115...` **无强制快进**至目标 `d5c1ffc7...`，并读回 `v3-local-ttt...d5c1` identical（ahead=behind=0）。
- 将 Root PR #40 从 Draft 转 Ready，按期望 head SHA `1b184204...` 使用 **merge** 方法进入 `V3`；GitHub 返回 `merged=true`，Merge SHA `e23fe240...`。
- 回验 PR #40 状态 `closed/merged=true`；`1b184204...V3` 比较 `ahead_by=1`、`files=[]`，表示 Merge Commit 相对被审候选无代码树差异；合并后的 Gitlink 仍为 `d5c1ffc7...`。

## 四、边界与遗留项

- 本结论不意味着 18 tasks 的总体 SR、No-TTT 因果比较、生产 P99、启动稳定性、负载峰值、线上部署已经验收。
- Issue35 的初次加载延迟非平稳、偶发长尾仍开放，后续应独立测量；不以这些未冻结的性能期待为理由否定已经通过的本次正确性与真实任务闭环。
- 旧阶段单独的 `APPROVE_CODE` 只在各自 frozen scope 内有效；本次对新集成 formal pair 的独立核验及 Owner 发布命令是额外证据，不扩大旧 verdict。
- 本次审核/回执文档提交只属于 review/bookkeeping；**正式实现 pair 不因文档 HEAD 更新而变化**。