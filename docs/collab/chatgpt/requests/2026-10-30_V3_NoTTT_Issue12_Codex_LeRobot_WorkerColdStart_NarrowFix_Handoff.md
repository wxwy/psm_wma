# Codex Design Handoff — Issue #12 No-TTT Async 首次Worker构建瓶颈

2026-10-30。负责仓库内源码及正式测试的唯一作者：Codex。DS_PRO只做外部诊断/Owner授权后的执行；GPT审核；Owner控制最终授权。**本工单允许进行只读设计和候选准备，不是正式源码合并/训练/新GPU或真实数据运行授权。**

原冻结 Root e0fe911dfb9fd34957234828195cf051713f6c3d / Child f6a92d47b6dac7998ddc58b3da26ef93f8068dc7；APPROVE_CODE与Issue#11 CPU301 PASS保留。DS真实CPU-only：ScopeA SourceReader构建192.97秒，其中LeRobotDataset init188.78秒；真实单spawn Worker ScopeB第一次materialize在120秒超时，没有首包。无须再让DS重复Probe。

**目标：** 消除或安全地前移每个Async Worker首个__getitem__时昂贵的LeRobotDataset eager build，保证正常首包能够在原120秒数据请求Timeout内到达，且稳态Worker Source/Transform仍在后台真正并行。不要仅加大Timeout掩盖成本。

关注冻结 Child：
1. cosmos_framework/trainer/no_ttt_async_loader.py:124-135，PreparedDataset首次self.recipe.build；:245-295 begin/first-materialize，保持request token/ordering/bounded cleanup。
2. cosmos_framework/trainer/no_ttt_async_recipe.py:195-254，worker重建Index、SourceReader、Tokenizer、Producer。
3. cosmos_framework/data/generator/action/datasets/robocasa_exact_window_source.py:247-258及459-505，官方LeRobotDataset eager构造和17帧Delta、caption、action/state/row identity严格语义。

**先交付最小实现方案与候选Patch范围：**
- 优先考虑轻量worker-source路径（复用既有VerifiedIndex和离线受验数据，维持官方LeRobot Delta输出与强校验），或显式 bounded one-time worker readiness/prewarm、将初次构建的失败定位与正式每包120秒Timeout分离；若后者仅把190秒初始化移动到启动阶段，必须报告真实初始化壁钟和资源成本，不能伪装为获得吞吐优化。
- 不允许fork携带CUDA训练状态，不能把完整LeRobotDataset大对象直接pickle给32个spawn Worker而造成不受控内存；不能偷偷把Source所有工作退回Parent使其不再异步。
- 保留world4/B8/T16/GA4、generation-only、Compact1、raw15/state15、cached latent、正式frontier/episode/slot游标、CFG Parent RNG顺序、FSDP/DCP train state、官方caption/tokenizer与每Read的身份校验、rank清理、nw0旧同步回归。

**最小验证：** Codex只对候选新改动跑局部synthetic CPU数据/顺序/RNG/cleanup回归，不重跑旧301/6raw；准备新Root/Child Gitlink正式增量Code Gate，GPT独立Review；仅在Owner另行批准后，DS做一个真实数据Worker首包检查，随后以相同完整合法DCP独占GPU条件做最小matched A/B并实际验证C+1提交、端到端Step Wall与GPU current-stream gap。不得用旧共享GPU A的Wall与新独占B直接相减。

禁止：在运行中正式Job工作树修改/停训，覆盖其源DCP、切正式30k、改EvalV2、调整正式120s Timeout掩盖问题、未授权新真实CPU/GPU执行或生产合并。
