# PSM-WMA V3 — EvalV2 Owner GPU Resource Policy 独立增量 Code Gate

- 日期：2026-11-01
- **正式技术 verdict：`APPROVE_CODE`**（仅限这次 Owner 改动的隔离候选源码及作者定向 CPU Code Gate）
- Formal Root：`4b581493db805c92964cb27e740c736db87c0329`
- Formal Child/Gitlink：`9a8cd6183424bfce245fbca393ca25ed59919ea6`（未变）
- 上次已审 Formal Pair：Root `6484dd83efc512e6801470790eb84ac7349c127a` / Child `9a8cd6183424bfce245fbca393ca25ed59919ea6`，上一轮 `APPROVE_CODE` / RM-M01 CLOSED 不重审
- 独立候选：`v3-eval-v2-render-media-20261101`。Request/evidence/Inbox/Review bookkeeping HEAD **不是** implementation SHA。
- 用户冻结的新口径：GPU4–5 供 Action Server，GPU6–7 供 EGL；GPU0–3 属他人，不能用。GPU 占用与训练共存由 Owner 判断，EvalV2 **不得查询/管理外部 CUDA 作业**，不得因 `memory.used + reserve` 等 GPU 内存预估拒绝准入；保留选定 GPU 身份、PCI→EGL 及实际 Context、进程自身 RSS、owned-process 安全清理。M8/B2 和所有 Rollout/Generated MP4 不变。

## 1. Fresh identity / diff 审核

已通过 GitHub 直接锁定 Formal Root `4b581493db805c92964cb27e740c736db87c0329`、Child/Gitlink `9a8cd6183424bfce245fbca393ca25ed59919ea6`、候选发布 HEAD（审核时 `c49634f0268be3205e4971d060a048c5aae2de07`），正式 V3 Root `7e2be5ca40891915a1e86eea935ed054ec1984dd` 未合入本候选。

独立读取新 Root commit 与实际 production/test 内容，唯一 Production 变动：
`scripts/robocasa_eval_v2/resources.py`。
测试改动：
`tools/v3/eval_v2_batch_tests/owner_gpu_resource_policy_test.py`（新增）、
`render_mapping_test.py`（Owner 新策略）、
`tools/v3/eval_v2_production_tests/entry_test.py`（更新两个入口用例）。
其余 Root production、所有 Child production 及 Gitlink 不变。作者 scope/保护文件 Git blob 收据与实际 commit 变动一致。

## 2. Contract → production 逐项核实

- `resources.check():18–25` 查询 `nvidia-smi -i <selected IDs> --query-gpu=index,uuid`，仅对 `gpu_ids ∪ render_gpu_ids` 的**选定编号**进行只读身份查询；完全移除 `--query-compute-apps`、`memory.total,memory.used` 和已用/预留显存门禁。
- `resources.check():27–37` 仍拒绝未选中 ID、重复 GPU 索引、缺失设备和前缀不合法 UUID；`resources.gpu_identity():74–99` 的 UUID+PCI 查询未改。Child `render_devices.py` 的实际 EGL context/PCI 验证不变。
- `resources.check():33–52` 仍只读取传入 owned process groups 的 RSS，`max_rss_bytes` 自身进程限额仍有效；不读取、列举或停止其他进程。
- 函数 `check(cfg, processes=(), *, before_models=False, run=...)` 保持兼容；`before_models` 仍接收但无 GPU 预算逻辑，返回 `gpus=index→uuid`、`owned_pids`、`rss_bytes`。核查相关 Runtime 调用只依赖成功/抛错的准入结果，无已发现的 `reserves`/显存元组消费者。
- `max_gpu_fraction`、`server_reserve_bytes`、`render_reserve_bytes_per_sim` 保留配置字段但不再作为此资源准入 Gate 的行为依据，符合用户要求。无新的 GPU 操作或其他任务管理逻辑。

## 3. Evidence 核查

直接读取作者原始 `final/junit.xml`：**70 tests, 0 failures, 0 errors, 0 skipped**。测试构成：15 Owner policy + 33 Render mapping + 20 EGL identity/Context doubles + 2 Entry resource cases。检查 `final/gate.json` 精确 Root/Child/Gitlink、before/after clean 和源码未变；`final/commands.json` pytest 以及 Ruff0.12.7 check、format check exit code 为零；语法记录通过。作者交接的 6 source bindings / 27 artifacts 与正式证据目录一致。没有将 development70 重复累计，也没有声称历史192/206重跑。本轮是**静态 GitHub 源码审核+作者原始 CPU Evidence 核查**，GPT 未独立运行测试。

原始单测以严格 double 禁止预算字段读取和任何 `memory`/`compute-apps` 查询，覆盖 before/after-model、EGL/OSMesa、缺失/错误 ID、复用选卡、owned RSS、安全报错传播；没有真实 NVML、GPU、Simulator、FFmpeg 或模型运行。因此真实驱动兼容、共卡 CUDA/EGL 稳定性、GPU 显存/OOM、M8/B2 及视频编码仍属 **Hardware Gate**。

## 4. Finding 与决定

**本轮未发现需要阻止当前 GPU 准入策略增量的 Production blocker。**

复核中留意：`resources.check` 对不同索引共享同一 UUID 的非正常查询输出没有单独拒绝。回读上一 Formal Pair 的同文件，发现此特性在改动前也不存在；本轮没有放宽 GPU 配置身份映射/Child EGL Context 检查，也没有证据证明目标机器实际发生 UUID 别名。因此将其记作**非阻断的历史边界观察**，不以此延迟本次 Owner 明确授权的“小范围去占用门禁”改动。后续硬件 Gate 应按已有代码验证实际物理 PCI/EGL Context 身份，不能仅凭数字索引假定异卡。若后续发现真正的 UUID/PCI 别名，再单独报告并处理。

**Final verdict：`APPROVE_CODE`**，只对 `4b581493db805c92964cb27e740c736db87c0329` / `9a8cd6183424bfce245fbca393ca25ed59919ea6` 的 Owner GPU Policy incremental Code Gate 生效，历史 RM-M01/GPU EGL 审核结果原样保持。下一步 DS_PRO **独立定向 CPU 验收**；真实 Canary / V3 提升须获得 Owner 单独授权。本批准不授权修改/中断训练和 `out2`，不授权启动 GPU/EGL/FFmpeg、900EP/Resume 或查询/使用 GPU0–3，不暗示 CUDA 与 EGL 与训练共卡已被实测证明安全。

参考：
- 作者交接：`docs/collab/codex/reviews/2026-11-01_V3_EvalV2_Owner_GPU_Resource_Policy_Author_Handoff.md`
- 作者原始 Evidence：`docs/collab/codex/evidence/2026-11-01_eval_v2_owner_gpu_policy_author_cpu/`
- 前一正式 Review：`docs/collab/chatgpt/reviews/2026-11-01_V3_EvalV2_RM_M01_6484dd83_9a8cd618_Incremental_Code_Gate_APPROVE_CODE.md`
