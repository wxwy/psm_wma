# PSM-WMA V3 EvalV2 — Issue #14 per-Task First-N Rollout MP4 独立增量 Code Gate

- **日期**：2026-11-01
- **审核者**：ChatGPT（独立代码 / Evidence 审核）
- **技术 verdict**：`APPROVE_CODE`
- **Formal Root implementation/design**：`fd183f9e8fddfaef93b6ec9484184f071062ae41`
- **Formal Child / Gitlink**：`8664267704da3206e719f3c7eef2b5ed86e2a417`
- **基线**：Root `9ba1dd110a4e3e99e717937c2f8d044fa077cdbf` / Child `6c83596d6a259e89c4cd3e79424024983426ac3d`
- **隔离候选分支**：`v3-eval-v2-rollout-first-n-20261101`
- **冻结合同**：Owner [Issue #14](https://github.com/wxwy/psm_wma/issues/14) + `docs/build/PSM-WMA_V3_EvalV2_Rollout_First_N_Issue14_2026-11-01.md`
- **范围**：仅上述 Formal Pair 的增量 Code Gate + 作者合成 CPU Evidence；非 V3 promotion、非真实模型 / 仿真 / MP4 / GPU / 900EP 执行许可。

## 1. 独立核对的实际代码

1. Root `scripts/robocasa_eval_v2/config.py:23,174-180`：新字段默认 `None`；非 null 必须是 exact int、`0 <= N <= episodes_per_task`，拒绝 bool、浮点、字符串、负值、超界与 `save_rollout_mp4=false` + 任意非 null N（含 0）。校验发生在 CLI episodes override 后；缺省继续使用原布尔策略。
2. Root `scripts/robocasa_eval_v2/runtime.py:54-75,325-330`：所有物理 Actor 获得原样 cap；在 Registry / 进程设置前，从已有不可变 invocation 记录选择 mode=fresh 的初始 resolved 配置；拒绝 Resume cap drift 和无 Fresh 锚点的新非 null cap，旧记录缺键按 null 处理。查看了实际 CLI `save()` 封装写入与 Child Store `records()` 行为，并非只相信交接文本。
3. Child `cosmos_framework/simulation/robocasa/eval_v2_adapter.py:109-111,125-130,259-264`：每次 `NativeEpisode.execute` 根据当前 `attempt['episode'] < N` 选择 rollout，不在可复用 Actor 初始化阶段缓存结果；`generated` 参数独立传给原 `MediaSink`；记录 `rollout_requested` 和 cap 诊断。
4. 已核查原 `MediaSink.frame()` 只在 rollout=true 时入队、`prediction()` 依 none/first/all 单独筛选；`contract.py` 保持 `media_participates_in_SR=False`。Store / Scheduler / MediaSink / Local-TTT / Model / Server / Training 未修改。Root 相对基线 7 个变更路径（其中 2 个生产文件），Child 1 个生产文件；和 frozen scope 一致。

## 2. Contract → behavior → Evidence

- `rollout_policy_test.py`：legacy null/true/false，N=0/3/50，非法值、CLI override；真实 CLI CPU dry-run；已有 Fresh invocation 与旧缺键记录的 Resume 拒漂移；实际 Runtime Actor setting 生成。
- 同一个 `NativeEpisode` 和原 native loop / loopback Local Client，覆盖两 Task、ep0/1/2/3/49、成功/行为失败、重复 index；MediaSink 的 frame/prediction 筛选为原实现，仅将编码提交替身化。逐 episode 检查 `rollout_requested`、generated 选择和 Local reset。
- 注入媒体构造 / callback 错误，核对 Core commit 与 Local reset 不受 optional media 失败改变。
- 已直接读取作者原始 `final/junit.xml`：69 testcase、0 failures、0 errors、0 skips（50 新 + 17 既有配置回归 + 2 既有 Core/media 回归）。`final/gate.json`：scoped Ruff check/format、AST4 均 PASS，Root/Child/Gitlink 确切绑定，执行前后源码未改。11 份 source binding、42 份产物 hash 的清单及发布回执可查。
- 初始作者 Gate 20 pass/1 fail、第二轮 27 pass/1 fail 的原始 Gate 仍保留；失败来自夹具未使用生产 invocation `save()` 封装、未持有生产 Store.locked lease。后续仅修改测试夹具及 SESSION，未改生产代码或放宽断言。上述失败不合并计入最终 69。

证据：`docs/collab/codex/evidence/2026-11-01_eval_v2_issue14_rollout_first_n_author_cpu/`；交接：`docs/collab/codex/reviews/2026-11-01_V3_EvalV2_Issue14_Rollout_First_N_author_handoff.md`。本次采用远端源码 + 原始 Evidence 独立审核，**未独立重新执行 pytest**。

## 3. Findings / Gate closure

- **Current blockers：无**。未发现与 Issue #14 冻结合约相冲突的代码或定向 CPU Evidence。
- **旧夹具阻塞：CLOSED**（原失败过程已留痕）。
- **Verdict：`APPROVE_CODE`，仅关闭本次独立候选的增量合成 CPU Code Gate。** 作者 Gate PASS 不自动扩大本 verdict 的适用范围。
- **明确不授权**：自动合并/提升正式 V3 或官方 Child、拉取/改动在跑 `out2` 的共享 worktree/YAML/媒体/DCP/结果/日志、干扰 NoTTT 正式训练、DS 派发、真实 RoboCasa、真实 FFmpeg/MP4、GPU、模型/Server、Canary、正式评测或实际性能结论。生成视频仍可每 Episode 输出首段预测媒体；减小 rollout 数量不等于消除 OSMesa 渲染开销。
- 正式 V3 源码 / 当前在跑 job 的实际部署身份 **未从运行服务器验证**；GitHub 的 V3 分支在本轮审核起点未替换候选。后续真实验证、promotion 与 run 应分别授权。

本 review 是针对精确 Formal Pair 的结论；后续仅追加 review/Inbox/receipt 属 bookkeeping，不形成新的 implementation verdict。
