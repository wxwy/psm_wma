# Local Memory A2 构建与验收运行手册

## 当前状态

A2 已完成工程交付并收敛回主仓 `/disk/rl/psm_wma` 的 `V2`。canonical implementation/evidence pair 保持：
- root `2a9df880713da179aee141dd97c6b20a2b1d8c2e`
- child `22acb13c1fdb4f146e51e3c26f1759c73e6d0d7e`

V2 当前直接 pin 到 canonical child `22acb13c...`；此前 V2 child merge commit `ae2e9f7...` 与 `22acb13c...` 的 Git tree SHA 完全相同，因此该 pin 只统一 evidence identity，不改变任何模型代码字节。原隔离 worktree 已 merge 后退役，不再作为项目入口。

**当前工程验收状态：PASS；long-run readiness：PASS / READY_FOR_LONG_RUN；5000-step 长训授权：TRUE；实际长训：尚未启动。**
本 PASS 表示当前 A2 训练/恢复/数据生命周期/证据链已经满足启动长训的工程条件，不代表 LIBERO SR 提升、真实机器人结论或长训结果。

最终工程证据：CPU 244 passed / 0 failed；B=1 matched control 2-step PASS；A2 3-step GPU control PASS；exact resume PASS；native grouped-vs-scalar loss/gradient parity PASS；RGB→visual96 parity PASS；online action-path PASS；full-catalog 20-step budget PASS；delivery verifier `artifacts/g0/sync_a2_final_verification_2a9df880_v3.json` 为 10/10 PASS。

D028 长训 readiness 追加证据：production `GroupedActiveLocalMemoryWindowDriver + GroupedSegmentRuntimeOwner` 在真实 full LIBERO4IN1 catalog 上 metadata-only 连续规划 5000 optimizer windows，`5000/5000` PASS；共 80,000 native groups、640,000 logical segments、10,240,000 consumers；每个 stable slot 恰好消费 80,000 segments；4 个 suite consumer exposure 均为 2,560,000；chronology/group-shape/queue-replay error 均为 0。最终 slot epoch 为 `{0:27,1:63,2:45,3:60,4:28,5:60,6:46,7:60}`。readiness verifier `artifacts/g0/a2_long_run_readiness_2a9df880/a2_long_run_readiness_v1.json` = `PASS / READY_FOR_LONG_RUN`，`long_run_authorization=true`。

A2 full-catalog 20-step 实测平均 `176.059 s/step`、CUDA peak allocated `45.045 GiB`；5000-step 基础墙钟外推约 `10.19 days`，不含 eval/checkpoint 等额外开销。旧 B=1/scalar `14.6 days` 估计不再用于 A2；`1.369×` speedup 仅属于 10-episode/suite matched control，不外推到 full catalog。

## 已实现的链路

A2：`B_stream` 个 stable slot 同步取各自 next T-block → `[B_stream,T]`；T 维严格串行、slot/B 维并行 TTT scan → 合并 Local-prefix consumers → 一次 native forward → 原生加权 loss → 一次 grouped backward → 原子发布全部 row 状态。一个 group 禁止重复 slot，不再使用 scalar-selection grouping / repeated-slot dependency waves。
默认 B_stream=8、T=16、GA=16：每次 optimizer update 16 次 native forward，2048 consumers。
D025：pristine Nano 7 selectors + canonical TTT 4 selectors，合计11项，不含 legacy runtime。
恢复校验：member layout、group size、GA、T、实际 source catalog 几何与旧有 digest/frontier。
在线接口：`OnlineLocalMemorySession` + `generate_with_local_memory`，输入前一观测 visual96 与实际执行 action10。
在线状态只在真实生成成功后提交；重复请求同字节重放、失败回滚、显式 episode reset。

## 复现全部验收

仅在唯一 GPU 空闲时执行；脚本不抢占其他训练、不安装依赖、不访问外网、不覆盖旧输出。
```bash
cd /disk/rl/psm_wma
bash tools/g0/run_a2_delivery_validation.sh artifacts/g0/a2_acceptance_NEW
```

执行顺序：绑定源码的完整 CPU 回归 → 3-step synchronized-A2 真实控制跑 → 验证每 group 为 8×16 stable-slot stream-major identities → 真实模型 regrouping loss/梯度对照 → 两个连续观测的真实动作生成 → 从iter2新进程恢复至iter3并比较 frontier/fast-state → 全catalog 20-step预算 → 统一验收JSON。
新进程恢复不冒充 abrupt-kill witness；本脚本不故意杀其他进程。
固定sigma/epsilon的native对照验证数学/批处理路径，不声明随机数流或GPU训练逐位等价。
若任一步失败，保留原始日志/输出并返回非零；使用新的输出目录再次验证，禁止覆盖证据。

## 证据与授权边界

- 代码、参数、source/catalog几何必须与receipt一致；readonly/bookkeeping提交不冒充implementation SHA。
- `verify_active_local_memory_pretrain_gate.py` 现委托新校验器；无A2真实证据默认BLOCKED，不再依据旧B=1六项摘要给PASS。
- CPU只是行为回归；真实GPU单组、恢复、native梯度、在线生成和20-step分别验收，不能互相替代。
- `delivery_status.json` 即使为PASS，也不是独立review批准、长训启动授权或成功率提升证明。
- 5000-step训练、真实机器人运行、LIBERO成功率/消融结果没有在本次短测中完成。
- 当前在线API要求调用方提供前一观测visual96和**实际执行**的标准化action10；HTTP客户端的RGB/action适配并未被偷偷假定已完成。
- A2 已合并回本地 V2，并将 V2 gitlink 固定到 canonical child；本轮尚未执行远端 push。训练/测试过程记录可入 Git，checkpoint/模型权重与 config.pkl 二进制快照保持本地。

## 独立审核处理

最终 exact implementation pair `2a9df880/22acb13c` 已由独立 DS 给出 `APPROVE`：工程代码、真实 GPU 证据与 exact-pair binding 无 concrete blocker。DS_PRO 首轮指出两项 root-only blocker：D026 决策编号歧义，以及 zero-init 梯度 verifier 判据过宽；二者已在 `dd6c30dc` 关闭，DS_PRO 复核确认 B1/B2 已关闭。MM 最终复核因外部 429/token quota 未完成，不作为本次 closure 的必要条件。

最终 verifier `sync_a2_final_verification_2a9df880_v3.json` 保持 `independent_review_approval=false`，因为该字段由纯证据校验器保守固定，不把 reviewer 结果写回原始 verifier JSON；当前交付状态文件另行记录独立 review 已通过。

仍有一个非阻塞 residue：child 源码中两处旧 scalar-order docstring 与 D026/D027 当前语义不一致。它不改变 formal child tree、训练实现或 evidence binding，本轮为避免制造新 implementation SHA 不再修改。
