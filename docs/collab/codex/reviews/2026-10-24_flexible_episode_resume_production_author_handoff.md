# V3 Flexible Episode Resume — 作者实现交接

日期：2026-10-24（Asia/Shanghai；原始日志/JUnit 时间保留 UTC）。状态：**AUTHOR_CPU_PASS / REVIEW；代码已非 force 推送并回读。等待 GPT 增量审核和 DS_PRO 独立 CPU；不是正式 Gate PASS。**

| 身份 | 精确值 |
| --- | --- |
| 新 Implementation Root | **`252d823cf7f0e65228aa60408d50778c5a13a307`** |
| Child / Root Gitlink | `813a550dab5d6b5b5e3be90d38bb97527956b4dc`，未修改；远端 Root Gitlink 与本地 Child 已回读一致 |
| Vendor 固定身份 | `1ac174585293ed998ffc9cf73e47439798cf6f6c`，版本清单未修改；本机未验收真实安装 |
| 实现基线 | `db4ac8c690ba9f5971899d28768ac3caf7065108` |
| 已批准 Design/Prototype Root | `1bf88fa624e58e521caa2213f2b1a44bf2f2871d` / 同 Child |
| Owner 冻结契约 | `cc7820bee1a73bd2bb2078cb7f00239944f66d37` |

依据：Owner 请求 `docs/collab/chatgpt/requests/2026-10-23_Codex_V3_RoboCasa_flexible_episode_resume_contract.md`；已批准 r2 设计 `docs/collab/codex/designs/2026-10-23_V3_RoboCasa_flexible_episode_resume_design_r2.md`；GPT r2 审核 `docs/collab/chatgpt/reviews/2026-10-23_V3_flexible_episode_resume_design_r2_1bf88fa_813a550d_review.md`。设计批准允许本次最小生产接线，不能继承为新实现 Pair 的验收通过。

## 实现行为

默认手动入口 `scripts/run_robocasa_eval.sh` / `scripts/eval_robocasa_18task_queue.py` 接入生产 `robocasa_resume_cli`、`robocasa_resume_store`、`robocasa_resume_execution` 和 `scripts/robocasa_episode_resume/`。默认 CLI 走同一受保护 admission 路径；原整 Task `execute` 和严格整 Run namespace helper 已移除，没有隐式回退。没有修改 Child、模型、Local-TTT 算法、Action Path、训练代码或 Vendor。

- 只有 Checkpoint（实际路径、模型内容/文件清单身份）、num_steps、action_horizon、guidance 四项参与旧新模型硬相等。新全量 SHA 基线与历史 metadata/stat 桥接区分保存；差异在写 migration/invocation/attempt 或启动模型前拒绝。Config/Root/Child/数据元信息属于来源和可比较性记录，不形成第五项模型相等限制；当前执行仍检验模型、Config和Task元数据在冻结观测后未改变。
- 同名历史目录必须显式 `--resume`，使用原 `.run.lock` 非阻塞独占租约；锁内重读模型/身份和来源。输出目录不得位于或包含 Checkpoint、Config、dataset。原 root manifest、原摘要、原 Attempt、JSONL、媒体和历史 Evidence不改写、覆盖、改名或删除。
- 每次复用重新验证原 SourceManifest/digest、Typed outcome、原 horizon、闭合进度、actions/predictions/frontier、Local cleanup及原媒体策略；catalog 的 `verified` 字段不能代替证据。矛盾 COMPLETE按原整 Task和全部 Episode核心先验，整个来源隔离并保留诊断；合法 RUNNING/FAILED闭合前缀仍可复用。
- Fresh / 新增 Task无有效完成历史时，保持 literal requested Seed、一个 Task环境和连续 N次 reset；已有完成历史需要补缺时才采用稳定派生 Seed、独立环境、physical0→logical slot映射。不伪称恢复旧 RNG流。持久 reservation/progress与已验证 catalog缺口重建待执行槽，重启不依赖内存 pending；缩小不删除来源，扩大仍优先补原缺口。
- 本次 tasks、episodes、seed、媒体与执行参数决定当前计划。只选择当前任务的前N个有效完成来源；额外来源原位保留且不进入本次 SR。正常 behavioral failure计完成，runtime_error/缺证据不计完成。报告同时包含 reused/executed/failed/excluded/remaining、原 source与当前视图 producer、实际 Seed及混合/未知标识。全复用明确 `runtime_probed=false`，不会冒充在新 seed或当前 runtime下重新执行；全复用不启动模型、占端口或执行新 runtime probe。
- Worker/进程清理错误与完成覆盖分别保全；最终重扫失败或复用来源变化会持久 PARTIAL、保留错误/清理证据、剔除未重新证明的来源，并返回非零。生成/环境视频仍分开；旧 none/first→当前 all只报告历史缺口，不补造录像或迫使已验证 Episode重跑。浏览副本不改变权威评测状态。

## 持久布局和 I/O

```text
<run>/evaluation_manifest.json                 # 已有原件保留；fresh首次建立
<run>/.run.lock
<run>/_resume_v2/model_identity.json            # 稳定新模型基线
<run>/_resume_v2/legacy_migration.json          # 非破坏旧身份桥接记录
<run>/_resume_v2/catalog/<locator>_<hash>.json  # 只增观察，复用仍重验原件
<run>/_invocations/<id>/
  invocation_manifest.json, resolved_config.json, resume_plan.json
  runtime_probe.json                          # 仅有新执行/实际probe时保存原始证据
  reservations/<batch>.json                   # 持久logical/physical分配
  sources/<Task>/<batch>/evaluation_manifest.json
  sources/<Task>/<batch>/<Task>/attempt_0001/  # 原始物理证据和cleanup
  snapshots/<sequence>.json                   # 不可变报告快照
  current_summary.json                        # 本invocation当前视图
<run>/latest_invocation.json                  # 便捷指针，指向当前摘要/快照
<run>/videos_view/                            # 独立浏览副本
```

旧 root `screening_summary.json` 不冒充本次结果；终端和 latest指针给出当前报告位置。模型入口全量读约两遍（锁前/锁内），预算为 `2 × (.metadata + 所有模型shard字节)`；日志/计划记录实际 bytes/files/elapsed。每批加载前后、提交和结束使用当前强身份的文件清单/stat观察，不每集再次扫全权重；这不是新的 payload证明。Episode/媒体重验另外产生只读 I/O与CPU解码成本。没有读取真实大模型来测量实际吞吐、缓存或最坏等待时间；禁止把合成 fixture耗时当真实存储预算。计划/恢复文档有明确资源上界。

## CPU Evidence与复验

**最终作者五组组合：`154` passed，`72` subtests；failure/error/skip=`0 / 0 / 0`。最终日志/命令/JUnit：`docs/collab/codex/evidence/2026-10-24_flexible_episode_resume_production_author_cpu`。第二次最终冻结组合用时 1063.26s；JUnit 声明 tests=226，实际 154 个 testcase 元素；成功 subtests 不单列 XML 元素，不等同于226项顶层测试。**

五组为 production components、store、execution、新CLI integration以及既有 Queue identity/lifecycle回归：

1. `tools/v3/robocasa_resume_components_test.py`
2. `tools/v3/robocasa_resume_store_test.py`
3. `tools/v3/robocasa_resume_execution_test.py`
4. `tools/v3/robocasa_episode_resume_integration_test.py`
5. `tools/v3/eval_robocasa_queue_identity_test.py`

第4组当前16项执行真实默认 CLI/resolve→四参/legacy bridge→flock→Store/持久分配→executor→**未修改的 Child main/run_policy/LocalMemoryClient**→HTTP ack/reset→核心证据/当前报告。模型、Kitchen环境、state观测与runtime attestation是CPU替身；进程/PID、Local session/ack/frontier/reset、JSONL和原媒体验证实际执行。覆盖 fresh5、新Task与旧补集并存、legacy2+new3、四参无写拒绝、全复用/占用端口、busy lease、第三集异常与真实失败计数、媒体升级、reset HTTP500及新Server恢复、最终重扫失败和输入目录重叠拒绝。

Ruff0.12.7 check、format --check、语法/受保护路径/依赖边界共15个Python文件：**`PASS；docs/collab/codex/evidence/2026-10-24_flexible_episode_resume_production_author_cpu/static_checks.json、frozen_source_sha256.json 和 artifact_sha256.json`**。记录精确冻结源码hash；Evidence/docs提交不能代替 Implementation Root。

失败迭代与最终结果分开：`integration/run02` 暴露并修复 authoritative start事件误用UI事件的 executed/failed少计；`final_run01` 第一次五组组合暴露 task_failures把未执行缺集任务误算为失败（期望1、实际4），修复后才执行第二次完整组合。这两项真实生产失败的原日志/JUnit、最终源码差异和最终日志同时交付。最早一次缺 lease的合成夹具原日志曾被覆盖，仅保留事实说明，不补造日志；详见归档的 integration iteration_notes。设计 r1/r2旧161/185项及此前聚焦PASS不得叠加成当前版本一次全量PASS。

## 请求与边界

请求 GPT对**新精确 Implementation Root/Child Pair**增量审核代码与Evidence，再交 DS_PRO在新的 clean detached工作树、已有完整CPU环境独立执行同一五组组合及静态检查，返回原始日志/JUnit/命令。详见 `docs/collab/codex/evidence/2026-10-24_flexible_episode_resume_production_author_cpu/independent_cpu_handoff_notes.md`；精确 Root 和最终统计已绑定 STATUS。

本轮没有读取/保存/恢复真实 DCP、加载真实 Action Server模型、启动GPU、执行真实 RoboCasa构建/reset/step、重跑已完成20集、更新活动18-task或G1工作树。Checkpoint字节哈希/非执行header检查不证明DCP tensors可加载；旧stat桥不能追溯不存在的历史全权重hash；fake环境不能证明真实RNG/物理等价或SR。派生 gap方案明确是便利性混合，不是旧连续场景协议benchmark。新实现仍待 GPT与DS独立Gate，实际模型/GPU/仿真/训练继续由Owner另行授权。
