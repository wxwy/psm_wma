# 2026-10-31 Owner决策：No-TTT CPU OSMesa Canary报告采信 / Gate PASS

- 角色：Owner明确推翻此前“须收集原始Evidence才能PASS”的要求；本决策覆盖上一个 `2026-10-31_V3_EvalV2_NoTTT_OSMesa_4Episode_Canary_Evidence_REQUEST_CHANGES.md` 中有关**向DS追加索取原始文件、日志、MP4、JSON及SHA256清单**的阻塞条件。保留历史记录供追溯，但不得拿已覆盖的要求继续阻塞或要求重复测试。
- **Owner原话：**「不要再收集原始证据了，我们信任ds」。
- **Effective Canary Gate: `PASS — DS_PRO_REPORTED / OWNER_ACCEPTED`**。明确表示基于DS正式测试报告由Owner授权采信，**不是**GPT独立读到DS服务器原件的验证。
- Formal implementation pair固定为 Root `d18b420c02cfc51a1b85e9f1d6ce5d26f7bd3163` / Child `2f7334c4ada6ace1d21185985aae90539052bf18`。此前Code Gate `APPROVE_CODE`继续有效；该文档不是新production修改。
- DS报告达成的指标：No-TTT `iter_000011000`、GPU7、2个Sim、CloseFridge/OpenCabinet各2Episode、4/4有效（4/4策略失败、SR0，不得误标为任务成功）、4 MP4、244 native batch，其中2次B2（Owner已批准2/244）、No OOM、clean EXIT0，OSMesa throughput可接受。
- **OSMesa CPU渲染作为本阶段方案定案**，不再为了这次Canary增加异卡EGL尝试，不要求重跑B2窗口、不再追加取证。
- 已知工程风险：`store.create()`后依赖外部脚本软链注入Numba预热缓存，可能对启动时序、环境漂移敏感。此前Finding保留为**非取证性质的运行注意事项**，在正式长跑的launch准备时请DS自行确保已可用、能稳定启动；不据此倒逼“再收集原始证据”，也不在目前要求额外实验/重构。如未来产生真实复现故障再针对性修复。
- **界限**：这次是NoTTT的4Episode机制Canary，checkpoint是iter11000，**不是iter12200评测结果**，也**不自动授权900Episode或Local-TTT正式Canary**；相关执行继续遵循Owner单独批准。训练并发能力是否成立必须基于具体运行条件，不应由本报告自动扩大。
