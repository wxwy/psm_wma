# Local Memory A2 构建与验收运行手册

## 当前状态

代码已在隔离分支 `chatgpt/a2-delivery-20260918` 实现。代码候选 child：
`22acb13c1fdb4f146e51e3c26f1759c73e6d0d7e`。
工作区：`/disk/rl/psm_wma_worktrees/chatgpt_a2_delivery_20260918`。
原 `/disk/rl/psm_wma` 有另一执行会话同时修改代码并运行 GPU，不自动覆盖/合并其 WIP。
**当前验收状态为 BLOCKED，不是 READY_FOR_LONG_RUN。**

当前 synchronized-A2 代码定向验证：grouped/launch/driver/TTT/model 相邻 CPU 184 passed；stable-slot 核心 26 passed；CUDA vectorized-vs-scalar TTT/gradient 1 passed；verifier 负例 6 passed。真实模型 GPU 证据必须在当前 fixed child 上重新生成，旧 child 的 20-step 仅作历史性能参考，不继承为 release evidence。

## 已实现的链路

A2：`B_stream` 个 stable slot 同步取各自 next T-block → `[B_stream,T]`；T 维严格串行、slot/B 维并行 TTT scan → 合并 Local-prefix consumers → 一次 native forward → 原生加权 loss → 一次 grouped backward → 原子发布全部 row 状态。一个 group 禁止重复 slot，不再使用 scalar-selection grouping / repeated-slot dependency waves。
默认 B_stream=8、T=16、GA=16：每次 optimizer update 16 次 native forward，2048 consumers。
D025：pristine Nano 7 selectors + canonical TTT 4 selectors，合计11项，不含 legacy runtime。
恢复校验：member layout、group size、GA、T、实际 source catalog 几何与旧有 digest/frontier。
在线接口：`OnlineLocalMemorySession` + `generate_with_local_memory`，输入前一观测 visual96 与实际执行 action10。
在线状态只在真实生成成功后提交；重复请求同字节重放、失败回滚、显式 episode reset。

## 一次执行全部剩余验证

仅在唯一 GPU 空闲时执行；脚本不抢占其他训练、不安装依赖、不访问外网、不覆盖旧输出。
```bash
cd /disk/rl/psm_wma_worktrees/chatgpt_a2_delivery_20260918
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
- root/child分支均只在服务器本地创建，未推送远端，未覆盖原V2工作区。

## 独立审核处理

DS 对 `a09b6f19/ab2e3fb3` 未确认HIGH；其完整意见见 `docs/collab/chatgpt/reviews/2026-09-18_DS_independent_A2_ab2e3fb3.md`。
已补whole-T拒绝fixture、speculative rebind零突变fixture、原始异常保留fixture和全trainable参数的构造期校验。
native对照代码已准备，真实结果仍待GPU。新child不能自动继承旧pair审核结论；作者不自授APPROVE。
