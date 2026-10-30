# Issue #12 — Worker LeRobot 冷启动最小修复，申请增量 Code Gate

2026-10-30（Asia/Shanghai）。**作者 CPU 自测交付，待 GPT 审核；不是独立 DS
验收，不是 GPU 性能 PASS，不是正式训练切换授权。**

| 身份 | 精确 SHA |
| --- | --- |
| 新 Formal Root | `fd9021b0908b4b2763b3d02508b1f34df377dc97` |
| 新 Child / Gitlink | `224c5f3c0bd6911bb49cb6bb0895ba7da53ff822` |
| 隔离分支（Root/Child） | `v3-nottt-lerobot-coldstart-20261030` |
| 已审旧 Formal Root / Child | `e0fe911dfb9fd34957234828195cf051713f6c3d` / `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7` |
| 旧源等价的候选 bookkeeping 起点 | `2260f2a6f89368301ba50a686676994af90a2ca5` |
| 最新任务书 / 诊断审核来源 | V3 `9344198a5abf4964a4997bf7e9268b8e5ccc73e8` |

本轮已重新 fetch、核对 V3 advertised/tracking 9344198a，并实际阅读 Issue12
详细 Review、最小交接和旧 Pair Code APPROVE、Issue11 DS301/6raw PASS。
旧 Gate 保留，不重新审核、不重跑旧301；新的通过数字只绑定本表新 Pair。
Root 的后续 Evidence/Inbox 提交不替代 Formal Implementation SHA。

## 问题与最小实现

旧 Worker 在第一次 `__getitem__` 内执行 `AsyncRecipe.build()`，SourceReader
随即构造完整 LeRobotDataset、加载筛选后的全源 Arrow 表并从 `index` 列重建
全量 Python 行映射。DS 报告约193秒构建、单 Worker120秒无首包，足以定位
这项改动；本轮没有重复现场诊断，亦不把 DS 数字写成作者测量。

仅两处生产修改：

- `cosmos-framework/cosmos_framework/trainer/no_ttt_async_recipe.py:230`：在既有
  SourceReader 的 `dataset_factory` 接口注入 Worker 专用读取类；Recipe字段、
  身份、RNG策略、Source/Transform调度、120秒Timeout及清理协议均不变。
- `cosmos-framework/cosmos_framework/trainer/no_ttt_worker_source.py:181`：
  `VerifiedWorkerLeRobotDataset` 绕过全源 eager 构建，只打开已有 VerifiedIndex
  mmap和元数据，按已受验的 relative spans 路由实际读取。请求时才加载当前
  Episode 的投影非视觉列，按 row-group 筛选及4096行有界批次过滤，有限 LRU
  复用。仍使用官方 HF feature cast、Torch transform，且不覆盖官方
  `__getitem__ / _get_query_indices / _query_hf_dataset / _get_query_timestamps`。
  Caption 仍由 LeRobot `task_index -> meta.tasks.iloc[].name` 产生。

默认 SourceReader完全未改，nw0保持原路径。每次读取的17行身份、Padding、
raw12/state16到raw15/state15、缓存Latent及最终SourceBinding校验全部保留。
Source/Cache/Transform仍在spawn Worker，CFG仍由父进程在原Consumer位置抽样。
没有预热超时豁免、增大120秒Timeout、fork、完整Dataset pickle、Parent搬运或
串行回退。没有模型、Loss、Optimizer、FSDP、Frontier、DCP/RNG实现或配置改动。

额外 Source Arrow LRU 的独立上界为每Worker `max(1,8/workers)` Episodes及既有
`max_cache_bytes`（默认2GiB）；nw8最多16GiB/rank、world4最多64GiB**保留源表**。
这是上界，不是实测RSS。Cast/读批次/框架/Latent mmap/IPC还占额外内存；数据
超限明确失败，不截断或改样本。真实RAM、IO容量留给后续现场资格验证。

## 作者定向 CPU Evidence

根路径：
`docs/collab/codex/evidence/2026-10-30_nottt_issue12_worker_coldstart_author_cpu/`

| 执行 | 结果与边界 |
| --- | --- |
| Source + Recipe | **47 passed**，25.50s；原19项Recipe、28项新增参数化场景 |
| 选定旧回归 | **11 passed**，113.97s；无整套301重跑 |
| 总计 | **58 passed / 0 failures / 0 errors / 0 skipped** |
| Ruff0.12.7 / format / AST | 4个变更Python文件全部通过；import origin正确 |
| 版本 / 清洁性 | 精确Root/Child/Gitlink，前后clean，`source_unchanged=true` |
| 内部只读保护审计 | 12项关键Git Blob不变，10个旧测试/Fixture/Helper定义AST逐项不变；Recipe只有 `build()` 成员变更 |
| Raw封装 | 43项artifact SHA256及18项Formal source Git Blob/SHA256绑定；完整Diff、JUnit、命令、环境、trace、初期失败均保留 |

新增场景包括共享/分开Parquet、反转Episode物理顺序、筛选子集、首/中/终窗、
官方尾端Padding、真实语言Caption、全部字段逐值/类型对照，冷构建零数据文件
打开及禁止eager构造正例、LRU淘汰/内存限额、错误metadata/映射/路径/缺文件/
行数/frame/episode/task/NaN/caption拒绝、CPU RNG中立和真实spawn回收。

新增完整接线测试使用临时16个Episode（真实Parquet/PT格式）、实际生产
NoTTTAsyncLoader、实际Source/Transform、B8/GA4、两个spawn Worker连续3个
Window；仅文本词表为CPU替身。强制Worker不能调用eager LeRobot构造，并保留
真实文件witness。父进程CFG、模型夹杂抽样、consumer、frontier与同步路径一致；
所有Owned PID已回收。此测试T=2用于局部首包/缓存接线；选定旧回归另覆盖
T16/B8/GA4 full/terminal与nw1/nw8、旧CPU模型0→8、8→0、8→8全状态Resume、
预取、源/缓存变动、忽略SIGTERM和非自身进程存活，**不是实际四Rank DCP/FSDP**。

小合成source witness：构建14.576ms（零Source Parquet打开），首次读取15.399ms；
单spawn内部构建34.492ms、首次读取19.996ms。真实LeRobot读取行为在测试中执行，
但这些输入很小、词表是替身，**绝不能与DS真实193秒做加速比，不能证明真实
首包小于120秒，不能宣布GPU吞吐改善**。已有合成overlap trace保留，仅验证
此前调度功能没有退化。

原始警告保留：pynvml deprecation、nw8高于本容器CPU affinity建议、Python
resource_tracker在退出时清理两个注册Semaphore。正式测试明确检查Owned PID
回收和foreign survival，不据此声称已完成真实机器资源容量验收。

## 重放

在干净的精确Formal工作树，使用现有CPU环境及**全新外部**Evidence目录：

```bash
python '<EXPORTED_EVIDENCE_HELPER>/run_gate.py' \
  --root-worktree '<EXACT_FORMAL_WORKTREE>' \
  --expected-root fd9021b0908b4b2763b3d02508b1f34df377dc97 \
  --expected-child 224c5f3c0bd6911bb49cb6bb0895ba7da53ff822 \
  --evidence-dir '<NEW_EXTERNAL_EVIDENCE_DIR>'
```

该Evidence helper在后续文档提交中，请从Evidence HEAD取到工作树外运行；
**不要将Evidence HEAD当作Formal Root**。脚本强制CPU/离线、独立HF/Matplotlib/
XDG/Ruff缓存、禁用依赖完整分布式插件的原conftest；原完整301 Gate同样如此。
精确命令与环境见 `commands.json` / `final/environment.json`。

## 申请与停止边界

请 GPT 只审核本次两文件生产增量与针对性作者Evidence，给出新Pair独立
`APPROVE_CODE / REQUEST_CHANGES`。既有193秒归因、旧301和已关闭设计不重开。

本候选从冻结NoTTT分支起步；V3当前Gitlink属于独立EvalV2技术线，**本次没有
把旧NoTTT Gitlink写回V3，也没有合并或回滚那条线**。后续若Owner授权提升，
应只移植这两个生产文件/测试的窄增量，保留canonical双方实现和协作记录，
不能以整个本候选树覆盖V3。

提交后STOP：新Pair尚无GPT Code verdict、DS新CPU/真实首包/合法DCP/GPU成绩。
后续只有Owner另行授权后才由DS做一个真实Worker首包检查；再在相同完整合法
DCP及匹配独占GPU条件下验证C+1真实commit、Step Wall和current-stream gap。
不拿旧共享GPU A与新独占B相减，不重复冷启动探针，不提高Timeout掩盖失败。

正在运行的正式NoTTT/G1、其工作树、Config、Job Identity、Checkpoint和历史
Evidence均未访问或修改。Issue12旧B超时/0commit及GPU性能INCONCLUSIVE维持。
