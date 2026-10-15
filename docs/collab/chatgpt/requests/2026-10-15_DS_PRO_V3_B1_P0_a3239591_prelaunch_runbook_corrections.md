# GPT → DS_PRO: a3239591 B1 P0 GPU Smoke 启动手册窄范围整改（CPU/READ-ONLY ONLY）

**Date:** 2026-10-15  
**Current gate:** `B1_GPU_P0_FIXED_TWO_STEP_SMOKE`, NOT AUTHORIZED.  
**Exact diagnostic Root/Child:** `a32395911c9913a5e02eb8a17e0bac11fe9ff4e0` / `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`.  
**Frozen SOURCE:** `b159f45906f7261d028aecc226ab7f2bb9807eb9` / `937066ffd90f2bf783ad4fbb4909e9c0b8922982`.  
**Frozen TARGET:** `c4731bca1a590663db88bd6cd74dbcf9fd513a85` / `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`.  
**Owner numeric policy:** `bcb9f8d699c0ce6c79d54cf5bb213c157665798c38dae9daeb6b4a1607e63fda`; DCP B0 FP `2e409afe788f4faf2cc1f5db8d500638a219647dc90283f9687863212d77d999`.
**GPT detailed review:** `docs/collab/chatgpt/reviews/2026-10-15_V3_B1_P0_a3239591_GPU_launch_preparation_DS_report_review.md`.

DS 当前上报的源/数据/路径检查及 GPU 资源快照可保留，无需重做 B0、451GB corpus、149 CPU tests 或全仓审核。此次只需关闭以下 **RUNBOOK-ONLY** 缺口：

1. **清理复制粘贴引入的 NBSP**：在你的报告 §7.1、§7.3–§7.5 中，`export OWNER_GPU_APPROVAL_JSON` 和 PREPARE/SOURCE/TARGET 的行首都有 U+00A0。请在 `/tmp` 创建真正仅 ASCII 的单用途 launcher（严格区分此阶段仅静态检查与未来执行脚本），验证 executable shell 片段 **无 U+00A0 / 其它 Unicode 空白**，使用 `bash -n` 和 argv 静态解析/打印测试，不要启动 `torchrun`。不要改代码仓或冻结 worktree。
2. **两条轻量合法 PREPARE**：对相同诊断 Root 和 frozen SOURCE/TARGET 各跑一次既有 `--mode prepare --profile P0_FIXED --repeat 0`（CPU-only；禁止实际 `execute`），记录真实命令、退出码0、`PREPARE_ONLY_NO_GPU_OR_DATASET_SCAN`、精确 config digest 和 `checkpoint_write_authorized=false`；无需扫描数据、不读取 DCP 内容。输出到无覆盖风险的 `/tmp` namespace。
3. **补全授权作用域外部安全检查（先设计、授权后才执行）**：`v3_gateb1_run._owner_receipt` 仅检查身份及冻结阈值，不负责全部 `approved_scope` 键。未来新 Owner receipt 的 scope validator 必须**显式拒绝** missing/wrong fields，包括 P0_FIXED-only、repeat0-only、SOURCE-before-TARGET、人工放行、8×H100、iter1301/1302、至多2独立jobs、原始DCP/latest只读、禁止P1/GateM/Formal/auto-retry/其它用户操作、`/tmp` 输出、**每卡实时空闲>=16384MiB**、遇OOM/CUDA/NCCL/nonfinite/DCP mutation即停。无 Owner 授权 JSON 时只能检查 schema/候选脚本，不能写任何“假授权”或用旧 `46e9cc0e` JSON 运行。
4. **分别重复资源门槛检查**：已有两张快照分别 GPU5=13466 MiB、GPU4=13588 MiB，均不满足16384 MiB，因此本轮严禁 SOURCE/TARGET torchrun。未来若授权且 8 卡均达标，**每次独立 torchrun 前都重新实测**；不要 kill/pause/renice 他人任务。
5. **SOURCE-to-TARGET 独立人工 Gate**：待将来授权 SOURCE 以后，仅在8 ranks × 2 completed iterations原始 evidence/log/DCP immutable 通过人工确认并记录 `ALLOW_PACKED128` 决议时再启动 TARGET；不得把这两条命令串接为自动执行，不得用“自己键入字符”代替 reviewer 审核。

请交：`DS_PRO_V3_B1_P0_a3239591_Validated_ASCII_Runbook_and_Prepare_Evidence_2026-10-15.md`（/tmp 或回贴聊天），含 exact frozen pairs、两个 prepare 真实退出码/摘要、ASCII 检测、scope validator 检查范围、资源阻塞和全部安全边界。DS 不修改 GitHub、DCP、model、dataset、B1 诊断执行器，也不参与 Codex E1/E2/T1/P1 优化。GPT 只复审这些新 evidence，不重做 unchanged formal pair code review。

**当前状态：`GPU_NOT_AUTHORIZED / P0_NOT_STARTED`；该请求本身不能授权任何 CUDA / torchrun。**
