# V3 RoboCasa Flexible Episode Resume — 设计与非破坏性迁移 r1

日期：2026-10-23（Asia/Shanghai）。**技术方案候选，提交 GPT 审核；不是生产实现或执行许可。**

Owner 契约：`docs/collab/chatgpt/requests/2026-10-23_Codex_V3_RoboCasa_flexible_episode_resume_contract.md`，提交 `cc7820bee1a73bd2bb2078cb7f00239944f66d37`。该契约替代旧的全 Manifest/整 Task Resume 等价要求。

本轮按契约建议的两步交付完成第一步：设计、legacy 迁移方案及隔离 fake-data CPU Gate。基线 Root `cc7820bee1a73bd2bb2078cb7f00239944f66d37`；生产实现仍为 `e6a970caba4bdc77f7d9b56a6a8fbcdafe57f1e0` / Child-Gitlink `813a550dab5d6b5b5e3be90d38bb97527956b4dc`，Vendor `1ac174585293ed998ffc9cf73e47439798cf6f6c`。本轮不修改生产 Resume、不更新运行中的18任务评测或 G1。

## 1. 身份、计划和引用分层

三个不同对象不能共用一个会被重新计算的 digest：

| 对象 | 内容 | 可变性 / 核验 |
| --- | --- | --- |
| `model_identity` | checkpoint、num_steps、action_horizon、guidance | 仅这四项硬相等；不同立即 old/new 报错 |
| `invocation_plan` | 当前 tasks、episodes、requested seed、媒体、GPU/端口/timeout/进度、当前 source/runtime/config | 每次 invocation 独立只增记录，不能用于额外硬相等比较 |
| `EpisodeRef` | 原始 digest、Task/Attempt/物理 ep、核心证据哈希、原 Seed/reset/runtime/source/media | 按其原身份重验；当前统计引用，不重新贴当前 digest |

`checkpoint` 是一个复合硬参数，绑定实际 canonical iteration 路径、model/.metadata SHA256 和完整有序模型 shard 内容身份；不读取 optim/、训练状态或其他 DCP。`guidance` 规范化有限浮点值；num_steps/action_horizon 严格类型并保留当前 H_pred16 / R1–16 合法范围。

Root/Child、config、任务数据来源及 runtime 变更不构成第五项旧新相等条件。记录变更/未知来源，给出 `MIXED_SOURCE_PROVENANCE`、`MIXED_CONFIG`、`MIXED_TASK_METADATA`、`MIXED_RUNTIME` 或 UNKNOWN 警告。Task metadata 在**同一 Task 内**比较，不能因为选择了不同任务就虚报元数据冲突。SHA 变化不自动证明行为变化，SHA 不变也不是物理行为等价证明；混合/未知条件不冒充单条件 benchmark。

当前执行的路径、模型可读取性、原始证据完整性、raw15/state15/required/H16 ABI、进程所有权、互斥与超时仍需有效。它们是安全前提，不能包装成大量额外旧新参数等价要求。纯复用且无新增 Episode 时不加载模型、不占 GPU、不启动 server/simulator；不为当前机器未执行的 runtime 冒写来源。

## 2. Checkpoint 身份与 legacy 证据强度

候选新模型身份为 `psm_eval_model_identity_v1`，digest 只覆盖 schema 与四个 parameters。checkpoint 子对象含 canonical path、metadata_sha256、排序的 `{name,bytes,sha256}` shards。全量模型字节流式计算哈希，不执行 pickle、不加载 Tensor；前后检查 device/inode/size/mtime/ctime 和 shard inventory 稳定。

完整哈希是新观测的强基线。结构性 pickle/ZIP 头检查仅用于拒绝明显无效输入，**不证明真实 DCP 完整或模型可加载**。实际 DCP load 仍属于后续单独授权的真实环境 Gate。完整字节 I/O 随模型体积增长；本轮只读微型假 DCP，未对真实模型测量容量、耗时或读取权重。

旧 manifest 只有 metadata SHA 和 shard `(name,size,mtime_ns,ctime_ns)`，没有历史 payload SHA：

1. 保留并校验旧 manifest 原 canonical digest；提取旧四参，不能覆盖旧文件或重算旧证据的 digest。
2. 使用当前新鲜观测核对旧 checkpoint 路径、metadata SHA、完整 shard stat inventory 和另外三参。任何不符立即拒绝，报告 old/new。不能用“目前全哈希一样”绕开发生变化的历史 stat。
3. 若吻合，记录 `LEGACY_STAT_BRIDGE_MATCH` 和 `historical_payload_sha256: null`，明确旧证明强度仍是旧 stat + metadata；当前全哈希只建立未来新基线。
4. 新控制记录保存原 manifest 引用与桥接决定；不补造历史权重哈希，不反写旧 DCP/Config/Job Identity。

原型支持旧 `psm_v3_eval_identity_v1` / `psm_v3_eval_identity_vendor_v1` 的模型桥接；Episode 重用还需要后者提供的 runtime、required ABI、Local cleanup 等证据。缺少这些不能仅凭模型桥接判为可复用。序列化保存的旧“当前观测”不能代替本次新鲜读取。

完整哈希是时点观测，不是持续存储租约。生产接线须在锁内形成稳定观测，并在实际 Action Server 加载前后重核输入/来源；若外部正在替换模型则 fail closed。Checkpoint 不能在完成检查后被悄悄替换而继续推理。

## 3. 控制目录与迁移顺序

候选布局（本轮尚未创建生产控制目录）：

```text
<run>/evaluation_manifest.json                 # 原 v1，永不覆盖
<run>/.run.lock                               # 继续共用，不能另起不互斥的新锁
<run>/<Task>/attempt_NNNN/                     # 旧证据原位；新 attempt 独占分配
<run>/_resume_v2/model_identity.json            # 新模型基线，只创建一次
<run>/_resume_v2/migrations/<id>.json           # 旧 manifest / 桥接 / 选择诊断
<run>/_resume_v2/catalog/<ref_id>.json          # 已验 EpisodeRef，追加而非覆盖
<run>/_invocations/<id>/
  invocation_manifest.json                    # 当前计划与 source/runtime/config
  resume_plan.json                            # 启动计划
  source_manifests/<Task>/<logical_id>.json    # 每个新增物理执行的原始身份
  logical_slots.json                          # logical id -> source attempt / physical ep
  episode_events.jsonl                        # reused/executed/failed，逐集来源
  resume_report.json, screening_summary.json   # 当前视图
```

新 summary 是 versioned view；不覆盖旧 v1 summary/manifest 来伪造同 digest。Task 外的新控制目录避免污染旧 `_attempts()`；自定义媒体浏览目录也不得占用任何未来 Task 根。

生产 admission 顺序：

1. 只读解析当前计划；同名已有 run 无显式 `--resume` 时拒绝。只读核对四参/legacy 桥接前提，错误不得创建 invocation/attempt、加载模型或认领新实验。
2. 取得同一个 `.run.lock` 的独占非阻塞锁；被占用时不写迁移或计划。现有 v1 手动运行目录已含该锁；无有效租约或不支持的旧格式明确 BLOCKED，不盲目导入。
3. 锁内重新读取并核对四参/原 manifest，形成稳定模型观测，重验所有要用的 Episode 核心与原媒体；此时才只增写 migration/catalog/invocation。
4. 终端和 resume_plan.json 同步公布当前任务、requested seed/episodes、每任务 old/reused/new/excluded、实际历史 Seed、覆盖缺口与资源映射。
5. 仅给 new Episode 调度模型和仿真。结束或异常均保留引用/事件/报告；当前 Worker 或清理错误不因结果覆盖已满而消失。

prototype 的 `locked_snapshot()` 已实测先比较、拿现有锁、锁内再比较、只读扫描及异常释放锁；**尚不是实际 Launcher 的完整受保护 admission 管线**。legacy_ingest、实际 Episode 扫描、计划与锁已有分组件/部分组合 CPU 证据；生产集成后仍必须测试完整链条与无 `--resume` 行为。

## 4. Episode 核心验证与确定性去重

从整 Task validator 中分离单 Episode 验证，不删掉旧整 Task 校验来求通过。RUNNING/FAILED Task 中较早完成的 Episode 可重用，Task 最后关闭失败与早先 Episode 核心完成分别记账。

每条来源需要：原 manifest/Attempt identity/runtime 合法；本集 typed success 或正常 horizon behavioral_failure；正数 steps 与原官方 horizon 相容；单集 JSON 与存在的聚合行一致；对应有序闭合 C01 start/end；有效 Local cleanup/reset；原 run/attempt/episode 的 actions/predictions、raw15/env12 向量、计数与 frontier 一致。required Local 的预测 session/episode/consumer frontier 必须和实际 cleanup/已完成动作相符，不能拿任意 UUID 清理记录充数。

第三集只有 start 或末尾未完成 JSONL 写入时，前两集闭合证据仍有效；未闭合集不复用。重复/foreign/错序等完整损坏记录明确诊断，不冒称普通中断。原策略要求的媒体还需实际解码；缺失/腐败为 `CORRUPT_ORIGINAL_MEDIA`，不同于本次策略升级而历史未录制。

稳定 locator 为 `(original_digest,Task,Attempt,physical_episode)`，文件哈希是快照证明，不是另一个 Episode ID。attempt.json、results.json、全 progress 流等共享可变观测不能因状态/追加变化使一集被计为两集；核心文件同 locator 不同 hash 则 `SOURCE_EVIDENCE_CHANGED`，不能作为新结果收进来。每次重用仍要以原 identity 重新验证，不能信任外部 JSON 中的 `verified: true`。

legacy 同一 manifest 中不同 attempt 从0重跑的重复索引，按 numeric attempt 最早有效来源选择；后者无论成功与否都排除并保存 chosen/excluded/冲突原因，不能按 success 择优。来源本身歧义、同 attempt 聚合/单集矛盾或非法重复目录明确拒绝该候选。只增 catalog 中同一 logical slot 也只能选一个来源；旧物理 ep0 与新 logical3/physical0不能按 physical0全局去重。

legacy 初次摄入将物理 reset ordinal 映射到逻辑槽位，并保留原编号。以后新执行用独立 source attempt 的 physical ep0，引用映射到 logical slot3等；原 C01/Local 的本地0..N协议不改。未完成 reservation 可在新 attempt 重试，不复用半集；同 requested seed/slot 得到相同派生 Seed。任务数量/顺序/GPU变化不改变已分配槽位；视图 dense ordinal 与不可重分配的 catalog slot 分开记录。

## 5. 当前计划选择与统计

每个当前 Task：`reused=min(requested, verified_completed)`，`new=requested-reused`，`excluded=verified_completed-reused`。当前未选 Task 不进入统计。按照确定的 catalog/逻辑顺序选前N个，旧多余文件与引用原位保留；后续扩大计划可再次使用。存在待重跑槽位时优先重试该 reservation，再追加新编号，避免因新进程都 physical0 而重复计数。

| 情况 | 当前视图 / 调度 |
| --- | --- |
| old3 / request5 | 重用3，仅执行逻辑3、4；source physical均0但映射明确 |
| old8 / request5 | 重用前5、执行0、excluded3；分子分母只取前5 |
| Task4扩到18 | 旧Task逐集重用，仅补新增任务和缺集 |
| 缩小 Task集合 | 只统计本次选择，其他历史不改 |
| 两集完成、第三集 runtime_error | 只重用两集，未完成槽位在新 attempt执行 |

启动/结束/逐集事件均包含 requested/reused/executed/excluded/failed/remaining、原路径/原 digest/Task/Attempt/source ep、当前 logical slot 与 effective seed。`executed` 另分 executed_completed；runtime_error不计行为失败或成功。缺集时 `sr=null`，另报 `partial_sr` 和剩余数。当前 invocation 的 Worker/清理错误即使覆盖已满也保持非零退出与非 COMPLETE；历史失败不永久污染以后已补齐、无当前错误的 invocation。

Seed/runtime/config/task-source 混合与 UNKNOWN 警告出现在启动、结束和 JSON，而不只留作者日志。Scanner 的所有排除/冲突诊断必须进入 plan/report，不能只传 records 丢掉 diagnostics。

## 6. Seed 与场景采样选择

现有 Child 为每 Task 创建一次环境，再逐集 reset，未保存可恢复的环境 RNG；重启后跳过几个编号或只 burn resets 都不能证明恢复了原 action-dependent RNG 流。

本候选明确选择 **独立逐 Episode 采样**：

```text
effective_seed = uint32(SHA256(canonical{
  sampler_version: psm_robocasa_independent_episode_seed_v1,
  requested_seed, Task, logical_episode_index
})[0:4])
```

Attempt nonce、GPU、任务调度和 invocation 次序不进入 Seed material；重试保持可重放。新物理 Episode 用这个实际 Seed 创建 fresh environment，再执行一次 public reset，记录 constructor Seed、public reset ordinal0、logical->physical映射、版本与 Seed material SHA。策略 action/Local-TTT 仍走原路径。可以用一集一个 simulator 子进程实现，避免改 Local 算法：Task 的 Action Server仍单 slot，成功 episode 的 Local end/reset 后运行下一集；失败时中止该Task、回收Server，按当前基础设施策略停止或切换下一Task，禁止带泄漏 session继续。

该策略不承诺原 RNG 连续性、数学零碰撞或物理场景绝不重复；有限场景本来可能重复。明确写 `NOT_HISTORICAL_RNG_STREAM_CONTINUATION`。同 requested family 下混用旧顺序reset与新逐集协议标 `MIXED_SAMPLING_PROTOCOL`，不能称同一不间断流的第N集。

Seed字段语义：`requested_seed`/`seed_family` 是请求的基 Seed；`effective_seed` 是真正传给环境的数值。`MIXED_SEED` 表示请求 family混合（例如旧0、新1）；`MULTIPLE_EFFECTIVE_ENV_SEEDS` 列出逐集实际不同 Seed。一个新 derived-family 的多集不会被误报为用户改过 `--seed`，但也不将派生值冒充 literal base seed。旧未知 Seed保持 UNKNOWN；policy seed仍固定0。

old seed0已有8集，本次 request seed1/5集：执行0，实际历史 family/Seed均0；醒目 `NO_NEW_EPISODES_AT_REQUESTED_SEED`，不宣称完成seed1新评测。old0已有5集、本次seed1/8集：引用旧5与新3，逐集 Seed可见，MIXED_SEED/采样混合统计仅为便利汇总。真实场景指纹若可采集则记录实际 env metadata；无法追溯的旧场景不能补造。

## 7. 媒体覆盖与浏览

先按每个来源**原保存策略**验证应该存在的媒体，再以当前策略计算覆盖视图。none/first→all不迫使旧集重跑或补造录像；all→none不应沿用上次 missing列表。覆盖必须从本次 requested policy + 已验证 availability + 实际 prediction_count重新计算。

逐集保留 available_rollout、available_init_png、available_generated、prediction_count、expected_generated_per_original_policy、original_policy、requested_policy、missing_requested_media；汇总缺失项与覆盖率，不虚报全覆盖。未知预测总数明确 unknown，不当all已覆盖。

`videos_view` 的旧 Root digest单值限制需在生产第二步适配为 SourceRef resolver，按每集原 manifest/digest验证后只导出存在的媒体；原始名称、JSONL、清单与哈希不改。展示副本与 current-plan统计分开，不能因浏览文件存在就认定可复用，也不能改旧 digest迎合浏览器。

## 8. 第二步最小生产接线与验收边界

审核本设计/原型后再实施，不直接把 prototype 复制到入口当作已验收实现：

1. 增加 model identity / invocation / catalog模块与新 admission；保留原 validator 及 legacy只读解析。
2. Queue 改为逐集 refs/remaining调度；新 SourceManifest与 logical/physical映射，不覆盖原 run manifest。任务结束/错误传播及 owned process回收保持独立硬门。
3. 单 Episode核心 validator与 SourceRef重新核验；媒体按原策略；统计按当前选集。明确错误级别，模型/manifest损坏或来源歧义不能靠自动新实验掩盖。
4. 新 Episode采样最小接线；优先复用原单集 simulator和required Local生命周期，必要Child只增 Seed/场景 provenance，不改策略/动作。
5. 进度显示 logical slot/reused/executed；浏览模块按来源解析不同digest；发布 plan/report/事件只增记录。

生产第二步必须在精确新 Pair 做实际 CLI/Queue fake-server全链 CPU Gate：四参各变更在任何写/加载前失败，显式 --resume、3→5/8→5、tasks增减、partial前缀与重复来源、Seed变化与全复用告警、媒体策略与坏原媒体、GPU/端口/timeout变化、并发锁、当前Worker错误不被覆盖数吞掉、迁移无历史改写和逻辑/物理进度不串线。随后 GPT fresh review / DS clean detached独立CPU。GPU、真实RoboCasa/模型与现有评测更新由 Owner 另行授权。

## 9. 本轮 CPU Gate 与限制

新文件只在 `tools/v3/episode_resume_prototype/`；生产 Launcher不导入。最终 **161 passed，0 failure/error/skip**：identity45、legacy Episode45、scene34、plan/report/admission原型37。实际使用了未改的 legacy identity helper、Local/审计/media validators及 owned-process回收器；输入是 tiny Git/DCP/JSONL/MP4/PNG与 fake env。Ruff0.12.7、格式、语法及生产文件未改检查另有完整 Evidence。

已覆盖：四参错误、payload替换、legacy stat桥/原digest保留，2/5闭合前缀与Local/媒体负例、旧attempt去重、当前计划扩缩/多余排除、逐集Seed/reset可控轨迹、媒体当前视图重算、稳定locator/核心冲突/同logical去重、Seed family与实际Seed区分、当前Worker错误、锁前/锁内复查及外部进程不被清理。扫描2个真实schema假Episode→计划补3→假完成汇总已组合验证，但新增3个是**validated-record替身**，不是生产 Queue执行；模型桥/锁/当前计划尚未接成正式入口，不把组件通过说成实际 Resume实现通过。

未执行真实 DCP读取/保存/恢复、Action Server模型加载、GPU、RoboCasa构建/reset/step、生产工作树同步或训练。作者 Gate只支持本设计候选审核，不是独立CPU、真实场景分布或生产执行通过。
