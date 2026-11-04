# Issue17 — EvalV2 streaming M32/B32 candidate: author CPU846 PASS

原先 `physical_slots()` 受 Task 数封顶，RoundScheduler 又限制同 Task 每轮只派一个 Episode，因此18 Task无法兑现每卡32 Sim。候选新增显式 streaming 协议，在同一 No-TTT／Local-TTT EvalV2 中分配64 Slot、持续派发不同 Episode、并发初始化，并将 M 与 Native Batch 上限独立支持到32。旧调度协议保留，当前不是 V3 promotion 或硬件运行授权。

## 精确审核对象

| 项目 | SHA |
| --- | --- |
| Formal Root | `00e119cc20cabe082974bd3495474b589c4b46b6` |
| Child / Gitlink | `82fa270e8cdb76b3e1a4e94adf0c7ce2b497884e` |
| Root 官方基线 | `ea0828c7d45a443cc74ae2582419f14e7782a17e` |
| Root Owner 需求分支起点 | `9eae18b319f7ba5a4990dc2073cf1b19668e14cf` |
| Child 官方基线 | `1069fe78841228cadbbfbe6afbd767eaed6225da` |

两仓独立分支：`v3-evalv2-streaming-m32-b32-20261104`。后续 evidence/Inbox/docs 提交是 bookkeeping，不能替代上表 Formal Root；DS 应精确 checkout 上表。Root implementation9869046d；CPU环境/旧fixture补全a9f9c2d1；旧Registry兼容/剩余CPU夹具纠正00e119cc。Child implementation82fa270e。完整要求为 Owner [Issue #17](https://github.com/wxwy/psm_wma/issues/17) 及原需求文档；[最小设计](../designs/2026-11-04_EvalV2_Streaming_M32_Minimal_Design.md)、[实现与复跑说明](../designs/2026-11-04_EvalV2_Streaming_M32_Implementation.md)。

## 作者统一 CPU Evidence

干净精确 Pair，Shell **exit0**，`gate.status=PASS`，`source_unchanged=true`，89个 watched 源码文件 SHA256 前后一致；Ruff0.12.7、format、AST65文件和 import origin 均通过。

| 组 | PASS | FAIL / ERROR / SKIP |
| --- | ---: | --- |
| inference | 182 | 0 / 0 / 0 |
| Phase A regression | 278 | 0 / 0 / 0 |
| Phase B runtime | 234 | 0 / 0 / 0 |
| media replans | 89 | 0 / 0 / 0 |
| new streaming | 63 | 0 / 0 / 0 |
| 合计 | **846** | **0 / 0 / 0** |

证据目录：[artifacts/eval_v2_streaming_m32/2026-11-04_author_cpu](../../../../artifacts/eval_v2_streaming_m32/2026-11-04_author_cpu)。可直接读取 `gate.json`、`junit.xml`、五组原始JUnit、环境、源码SHA表、`final_summary.json` 和双仓 full patch；`cpu_evidence.tar.gz` 保留完整原始日志／临时行为证据／失败历史／外置诊断插件，归档SHA见同目录 manifest。原始外部工作目录 `/workspace/work/eval-streaming-m32-evidence/author-formal-03` 保留，不覆盖失败01/02。

- M32/B8、M32/B16 各一次18个真实 underlying Task名称×50 EP，2个独立 Policy owner、64个不同物理 Slot UUID 和真实 SimSlot FSM、900唯一Core及900唯一Session；全部关闭并 Resume 保持已有 Core。物理进程、设备、扩散模型与仿真 physics 在此64-Slot CPU场景中是明确替身。它不是64真实OS Sim／GPU性能证据。
- 32 Session公开Client→真实dispatcher→Native H16输入输出载体在 No-TTT／Local-TTT 下验证 B8/B16/B32；B32出现真实32成员native调用，按 Session/state 正确返还。Local 使用真实微型CPU fast state、prefix与commit，No-TTT不建Local状态；replay/ACK/End/timeout/隔离旧回归均保留。
- 独立真实OS四Sim测试在两种模式下用受控慢 READY、make_env证明启动重叠／每GPU一个Server；同Task双Slot Server exit23故障、owned进程清理、外部进程隔离、停止时无晚到spawn均验收。
- 无 Round Barrier的新策略、同Task多EP、Task公平性、种子grant序号及attempt→physicalSlot→sampling→Core防错、Owner-pending、故障恢复、公开CLI Fresh→Resume均覆盖。旧900同时保留并通过900派发、50个RoundBarrier、450success／450failure和3个Slot／model替身的原断言。
- `none`不做no-op逐step rollout compose或启动Encoder；Policy与Local证据所需合成保留。严格all媒体落盘→receipt→ACK→End／失败不改SR回归，双严格decode之间Ready推理可继续，媒体也不饥饿。

CPU模拟的步骤极短且元数据I/O占比大，两组900主要得到B1／B2，这是合法partial batch，**不是硬件Batch8／16吞吐证明**。较大有效Batch在独立32Session的Native shape/routing场景验证。不据此宣称H100性能、B32显存安全或R03/R04可直接比较。

## 生产增量边界

Root：config/execution身份、真实Slot容量、runtime/startup小模块、dry-run计划及telemetry。Child：显式新schedule/sampling版本、StreamingScheduler复用原lease/ticket/Core权限，短Store metadata锁、physical attempt绑定及并发恢复，独立 `streaming32` 容量贯穿Server／Client／ACK，媒体与Ready推理有界交替、禁用no-op rollout callback，Worker分阶段timing。没有第二套模型／仿真／事务框架。

旧v1仍Task数封顶及RoundBarrier，默认legacy8；新协议 `streaming_task_affinity_v2` 明确允许M/B各1..32。每个新Run显式提供RSS／owned GPU预算和启动reservation/concurrency；只统计本次owned compute/graphics PIDs，foreign occupancy不作为拒绝门，未知计量fail-closed。所有durable spawn在新模式从返回前就计入，未READY或INFO失败的Server不漏计。每GPU锁保护完整握手及发布，失败停止且不自动重复spawn；每Slot锁及关闭门保护生命周期。清理前等待全部作业退出，故障归属不再用同Task覆盖的latest attempt。完整vendor逐资产SHA／runtime digest／source／render上下文核查未移除或缓存伪造。

**Owner最终明确保留 M/B Resume一致性限制。** `identity.py`相对基线无diff，Runtime/CLI完整execution比较、Manifest／模型／任务／资源／源码身份与已提交Core不可重跑均继续严格。新采样版本标明场景顺序与旧Run的比较边界，不承诺逐EP场景复现。

`tools/g2/**`、Child model/trainer/data及render_devices.py与基线无diff；训练加载/GPU计算并行线、Local算法、旧结果及运行中的R04均未操作。没有连接远程桌面、读取／复制／外传远程服务器文件；没有真实GPU／模型／数据集／训练／Canary执行。

## 失败历史与纠正（不得合并计数）

1. 开发capacity80PASS；新concurrency最初11PASS/3FAIL源于错误注入空资源探针，修正后新streaming54PASS。补边界focused60PASS/2明确排除已完成900；最后cleanup/recovery2PASS。初始Ruff E731及修正均保留。这些是重叠开发运行。
2. Formal01（9869046d/82fa270e）inference182PASS，PhaseA100PASS/1FAIL。原fault为CPU夹具误走EGL但无实机证明，随后rendezvous超时。固定并记录OSMesa环境；定向又暴露旧fixture缺 `save_generated_video`，基线生产代码已要求此字段。仅为CPU helper合并DEFAULTS／显式OSMesa和no-media，所有旧断言／生产渲染校验保留。定向原快照用例1PASS。
3. Formal02（a9f9c2d1/同Child）inference182PASS，PhaseA167PASS/1FAIL；旧900完成。旧socket registry double无id；新owned-map只在streaming消费，所以最小生产兼容修复将新增登记限定streaming，新模式仍从durable spawn立即计量。剩余排查659PASS/2FAIL/3排除900。
4. AST抽取测试补真实 `transaction_capacity` 依赖。永久ACK-loss原失败内部行仍 **INCONCLUSIVE**；透明单次诊断2PASS不是覆盖该失败。2秒fixture总预算包含真实1.147秒Encoder启动；受控2.1秒启动延迟使原fixture在ACK前RED，新fixture仅把Server/Client总预算改10秒（sink原已10秒），增加真实ACK尝试及此前durable文件/receipt断言，保留全部原文件／hash／decode／INCOMPLETE／cleanup断言。相同受控延迟GREEN1PASS10.34秒。生产媒体／超时实现无修改。最后相关8PASS后冻结本Formal并完整846PASS，含全部900，没有skip/deselect。

独立实现侧只读agent检查发现五项并发风险，修复后均回读关闭；cleanup锁边界、legacy兼容及最后CPU夹具也独立回读。该agent未执行测试、不代表DS；本文件不自授APPROVE_CODE。审查记录在artifact `peer_source_audit.md`。

## 同一 Pair 复跑与请求

在干净隔离worktree精确检出上述Root及Child，使用作者已记录的CPU环境：

```bash
cd /workspace/work/psm-wma-streaming-m32
CUDA_VISIBLE_DEVICES='' LD_LIBRARY_PATH='' /workspace/.venvs/psm-wma-cpu/bin/python \
  tools/v3/run_eval_v2_streaming_cpu_gate.py \
  --root-worktree /workspace/work/psm-wma-streaming-m32 \
  --expected-root 00e119cc20cabe082974bd3495474b589c4b46b6 \
  --expected-child 82fa270e8cdb76b3e1a4e94adf0c7ce2b497884e \
  --evidence-dir NEW_DIRECTORY_OUTSIDE_WORKTREE
```

Gate记录OSMesa、禁GPU／离线、缓存外置、精确命令、完整环境与89源文件哈希。原作者该命令 shell0，五组846PASS。换机器可替换路径，但精确Pair、依赖/import origin及原始证据判据不能省略。

**请求GPT对本完整增量做fresh independent Code Gate：`APPROVE_CODE` 或 `REQUEST_CHANGES`。** 新调度／采样版本、同Task多在飞Store原子性、startup／close ownership、资源meter/reservation、双模式Batch与媒体公平性是重点。作者CPU PASS不代替DS独立验收；通过源码Gate后再由DS在独立干净工作树复跑同Pair，实际H100/64OS Sim/性能与真实评测须相应Owner授权。未自动promote V3/v3-local-ttt；G2两线各自批准后，按合并时最新V3无损整合。
