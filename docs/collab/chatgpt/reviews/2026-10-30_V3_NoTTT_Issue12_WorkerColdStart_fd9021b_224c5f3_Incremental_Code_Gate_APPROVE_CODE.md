# PSM-WMA V3 — Issue #12 Worker LeRobot 冷启动最小修复增量 Code Gate

**日期：2026-10-30**  
**Formal Root：`fd9021b0908b4b2763b3d02508b1f34df377dc97`**  
**Formal Child/Gitlink：`224c5f3c0bd6911bb49cb6bb0895ba7da53ff822`**  
**正式 Verdict：`APPROVE_CODE`（限本 Pair 的 No-TTT Worker Cold-Start 最小生产源码增量 + 合成 CPU Evidence）**

> 这份 Review 只批准当前独立隔离候选的源码 Gate。**不批准 V3/Child 生产合并、现役 No-TTT 30k Job 切换、原DCP/Checkpoint写入、真实数据、GPU、训练、正式生产部署**。Issue#12历史真实 Arm B 从DCP加载后首批120秒Timeout/0 commits、`GPU_PERFORMANCE=INCONCLUSIVE`保持不变。

## 1. Formal 身份与增量范围（GPT独立 GitHub 回读）

- 已独立从根仓 commit `fd9021b0908b4b2763b3d02508b1f34df377dc97` Git Tree 读取 Gitlink `224c5f3c0bd6911bb49cb6bb0895ba7da53ff822`，与子仓 `wxwy/cosmos-framework` 实际已发布 commit/隔离分支精确一致；该 Child 是冻结 `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7` 的直接1提交后继；根仓从同源候选 bookkeeping 基线 `2260f2a6f89368301ba50a686676994af90a2ca5` 前进2 commits。
- 子仓相对旧 Child **仅4文件**：**生产2个** `cosmos_framework/trainer/no_ttt_async_recipe.py`（增加`partial` + 在`AsyncRecipe.build`注入新Dataset factory）和新增`cosmos_framework/trainer/no_ttt_worker_source.py`（228行）；**测试2个** `no_ttt_async_recipe_test.py`、新增`no_ttt_worker_source_test.py`。原 `no_ttt_async_loader.py`、`no_ttt_cpu_loader.py`、`matched_no_ttt.py`、`RoboCasaExactWindowSourceReader`、VerifiedIndex、DCP、NoTTT Profile、父进程Transform/CFG均**未改**。根仓Formal更改为Gitlink +SESSION/TODO/窄设计文档，不属于其它技术线改码。
- 与项目固定的 `mli0603/lerobot@1a4316c6845330bc552fb982dbc44bdb4f66f2f1` 源码独立对照：真实 `LeRobotDataset.__getitem__`使用`hf_dataset[idx]`取得episode/index，经`_get_query_indices` + `_query_hf_dataset`实现Delta及padding，最后用`meta.tasks.iloc[task_idx].name`生成Caption；候选**没有覆盖**这些官方读取方法。
- Codex交接原件：`docs/collab/codex/reviews/2026-10-30_V3_NoTTT_Issue12_Worker_ColdStart_author_handoff.md`（Evidence docs commit `de20afc1d5172e8100c3852525c24c23668c2976`，**不是**Formal Root）；设计合同 `docs/build/PSM-WMA_V3_NoTTT_Issue12_Worker_ColdStart_NarrowFix_2026-10-30.md`。

## 2. 关键实现与 contract→behavior→evidence

### C12-A — 首包必须摆脱全量LeRobot eager初始化：PASS（源码与合成）

- `no_ttt_async_recipe.py` 仅在Async Worker `build()` 中通过已有`RoboCasaExactWindowSourceReader(dataset_factory=...)`注入`VerifiedWorkerLeRobotDataset`。其他线程、`nw0`、原默认 Dataset Factory 路径不改。
- `no_ttt_worker_source.py:168–226` 的子类不调用`LeRobotDataset.__init__`也不调用全量`load_hf_dataset`；只加载元数据、Accepted VerifiedIndex绝对-相对mmap及Episode spans。
- `no_ttt_worker_source.py:110–155` 按实际`read`打开**当前Episode**的Parquet，投影非视频列、RowGroup统计剪枝、4096行有界批次中筛选episode，构建单Episode HF表并按官方HF features schema进行cast + `hf_transform_to_torch`；不进行全语料加载。
- 新 `test_build_does_not_call_eager_constructor_or_read_any_source_parquet`直接对官方 eager constructor/full-loader作失败注入，在实际Worker Dataset构造后断言0 Source Parquet open，首次请求仅打开请求Episode，并检查同Episode复用；作者的合成样本`build_ms≈14.576`、`first_read_ms≈15.399`是小样本观测，**不与DS真实193秒直接计算加速比**。

### C12-B — Official LeRobot Delta/Caption/typed rows与强身份：PASS（合成范围）

- `VerifiedWorkerLeRobotDataset` 没有override官方`__getitem__`、`_get_query_indices`、`_query_hf_dataset`、`_get_query_timestamps`；`_VerifiedRows`只提供原官方查询所需的`hf_dataset[index/list]`及`hf_dataset[key][indices]`接口。
- 子仓测试`test_official_delta_caption_padding_and_source_windows_match`直接比较合法源的**每个Window**、shared/split/reverse/subset布局、尾Padding、caption/task_index、Tensor shape/dtype和绝对/相对Row identity；结合原 `RoboCasaExactWindowSourceReader.read_window` 的17帧Frame/Row/Task/Action/State强校验。
- 真实源文件名、Episode metadata、VerifiedIndex接受范围/relative spans、文件路径`_local_path`均有拒绝机制。测试覆盖bad metadata/mapping、丢失/越界Parquet、行数/frame/episode/annotation/NaN/caption腐坏等负例。
- 未新增Checkpoint/Frontier游标、CFG抽样或时序权威。真实生产值尚需Owner批准后由DS验证。

### C12-C — LRU存储与错误清理：PASS（合成范围），容量风险留运行验收

- `no_ttt_worker_source.py` 对原始Arrow retained table双重限额：`max_episodes=max(1,8/workers)`与`max_cache_bytes`，超限抛`MemoryError`而不截断，不修改原始Cache/Index文件；tests验证按Episode驱逐和重新读取一致。
- 该限额只覆盖**retained source Arrow cache**；构造中的临时Parquet batch、cast buffers、HF对象/Tokenizer、既有Latent mmap和IPC依旧会占用RAM。按默认2GiB×8workers×4rank，单新增source缓存理论 retained上界64GiB（不等于实测或总内存）；真实Host RAM/IO与每Worker首包时间仍属下一步DS验收。
- 旧的`NoTTTAsyncLoader` 120秒Timeout / parent CFG随机数消费/Worker CUDA隔离/请求Token与FileVersion witness、Bounded cleanup不改。新test `test_spawned_real_recipe_source_transform_cfg_and_cross_window_cleanup`使用真实临时Parquet/PT与2个spawn Worker在 B8/GA4 三Window通过实际Loader读取/变换/CFG，并检查与旧同步producer相同及Worker PID回收；仅文本Processor为测试替身。
- 选定旧回归涵盖T16/B8/GA4、nw1/nw8、相同Job CPU checkpoint frontier Resume 0→8/8→0/8→8、真实Worker Source+Transform跨Member/Window overlap、文件变化拒绝、异常/忽略SIGTERM Owned cleanup；**非真实四Rank DCP/FSDP**。

## 3. 独立原件 Evidence Gate

- GPT通过GitHub connector**直接读取**作者发布的 `docs/collab/codex/evidence/2026-10-30_nottt_issue12_worker_coldstart_author_cpu/` 中原始`final/junit.xml`、`final/async.xml`、`final/regression.xml`、`gate.json`、环境、Source SHA、Protected Audit和Witnesses，而非只采纳作者汇报。
- **独立解析JUnit：47个新Source+Recipe测试、11个选定旧回归，共58个唯一testcase；0 failure、0 error、0 skip**。`gate.json`五步运行exit0（import origin、ruff check/format、async、regression），`final/ruff_check.log`=“All checks passed!”、`ruff_format.log`=“4 files already formatted”；报告syntax4/clean checkout来自作者Evidence，本地当前没有安装pyarrow/datasets/lerobot所以**GPT没有亲自重跑**这些测试。
- 依据GitHub发布的 `artifact_sha256.json` 冻结manifest，GPT使用独立SHA256实现计算了**11份重要原始证据**（Gate/JUnit/Async/Regression XML、Env、Source SHA、Protected Audit、两个Source Witness、Formal Pair、Formal Bindings）；**11/11字节SHA精确匹配**，不声称43/43全部核验。
- 直接比较GitHub child Baseline→Formal仅上述4文件，且Protected Audit中12个权威Source Blob未变、原10个Recipe测试/Fixture函数声明未删除；与实际Diff交叉一致。合成timeline虽然记录Source+Transform与fake compute交叠，**不等于真实GPU overlap**。
- 保留警告：pynvml deprecation、nw8超过当前容器CPU affinity建议、resource_tracker 退出时回收2个Semaphore。现有测试证明owned worker PID回收而不是现实机器无任何资源后遗留。

## 4. 独立增量裁决

- **当前Pair无可确认的生产 blocker / tests-evidence blocker，正式`APPROVE_CODE`。** 通过范围仅是**Worker按需初始化 + 官方LeRobot delta/source语义 + synthetic CPU consistency/RNG/cleanup**，不是“现实RoboCasa Loader已经能够在120秒内首包”、不是GPU训练收益验证。
- **后续要做的唯一最小性能链路**（须Owner再授权）：DS在原相同冻结真实数据/Index/Compact1上用新Pair做**一次真实1Worker首包及Host RAM/IO/Worker清理验证**，必要时限定4rank×8workers CPU资源；仅当首包健康、来源/值一致，再在**独占GPU4–7**、相同合法完整DCP C的隔离输出A/B进行少量真实optimizer commits并量化稳态P50/P90/数据stream gap。不能用旧共享GPU下A壁钟与新独占B直接比较，也不允许切正在运行的正式30k Job。
- 不重跑旧CPU301、不重做DS已运行的失败冷启动probe、不添加新数据缓存体系，不修改V3当前EvalV2 Gitlink或生产任务。Root docs-only评审落盘不改变这组Formal Implementation Pair，新的GitHub commit不代替这对SHA。
