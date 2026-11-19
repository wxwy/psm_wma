# Issue #90 G2 Phase5 性能归因与复验

## 已测到的回退

在 `data` 上原位复读固定日志。匹配 R1 Sync 和 Raw8 的 Iter 1–10，Rank 0 的 Consumer 顺序 SHA 10/10 相同，每步平均 501.5 个有效 Consumer，实际 recipe、Global-off、B8/GA4/T16/world4、峰值显存和 forward/backward 次数相同。两次使用的代码版本、启动诊断及采样设置有差异。 [只读聚合程序](../../tools/g2/summarize_training_regression.py)

| Rank 0，秒／step | R1 Sync 1–10 | R1 Raw8 1–10 | 变化 |
| --- | ---: | ---: | ---: |
| Wall | 35.719 | 74.617 | +38.898 |
| DataPrepare | 23.792 | 25.056 | +1.264 |
| Transfer | 0.343 | 5.386 | +5.043 |
| Local Scan | 0.950 | 15.076 | +14.126 |
| Forward | 4.563 | 20.078 | +15.514 |
| Backward | 5.738 | 5.818 | +0.080 |

Transfer、Local Scan、Forward 三个 Host 时段的增量合计 34.68 秒。计时范围可能嵌套，不能解释成这个比例的 kernel 工作量。Raw8 队列等待接近 0，GA0 原始读取及全部 Transform、CAP2 和 Local-TTT 仍在父进程热路径。“队列无等待”不表示 GPU 已经取得下一批。Raw8 有 Iter10 一个 CUDA 样本，匹配的 Sync 没有。现有日志不足以确认 GIL、NUMA、内存带宽、CPU/GPU 同步或特定 kernel 的因果贡献。另有少量训练数值差异，10 步最大绝对差 outer loss 0.0004414，grad norm 0.0510，不能把历史两次运行当作严格同值验证。

稳态 R1 Sync Iter40–49 为 35.693 秒。4 卡 No-TTT 尾部 10 步为 9.529 秒。实际 loader log 确认其每 Rank 8 Spawn、prefetch1、常驻进程、后台 Source/Cache/Transform、父进程按原顺序选择 CFG，均值队列等待 139 ms、父进程 decode+CFG 230 ms。通用 launch receipt 的 loader 字段无法区分这两个实现。No-TTT 同时使用 compact cached video，且没有 Local-TTT，因而只作架构参考。8 卡 G1 Local-TTT/GA2 尾部 10.844 秒也保留为参考。

原 dense carrier 每 Consumer 分配 6,684,672 B。仅按原始占位尺寸，满载 world4 每步涉及 13.69 GB 逻辑零像素；原始分配量与实测 H2D 字节不是同一指标。两个 R1 历史运行都使用 dense，故它是独立优化变量。在 `data` 上 GPU4–7 与 NUMA1 对应，现有结果无绑定对照。主机 perf 权限拒绝 `perf_event_open`，后续 trace 要记录该限制。

## 真实 CPU 配对结果

8 个已认证 Train Episode、每集 16 个决策帧，128 个请求顺序一致。每个 Provider case 两次取中位数。同一 R1/R2 内各配置的结果内容哈希均完全相同，R2 每配置返回 384 个真实 View latent。耗时覆盖 Provider 请求，进程初始化另计，并受存储页缓存影响，不能外推为 GPU 单步。

| LRU | 线程数 | R1 ms | R2 ms |
| ---: | ---: | ---: | ---: |
| 4 | 0 | 782.86 | 8,981.06 |
| 4 | 1 | 927.81 | 10,341.92 |
| 4 | 2 | 559.00 | 5,343.74 |
| 4 | 4 | 1,257.54 | 14,567.92 |
| 4 | 8 | 1,529.30 | 15,235.50 |
| 16 | 0 | 82.05 | 1,004.94 |
| 16 | 1 | 85.71 | 1,021.11 |
| 16 | 2 | 159.43 | 2,689.37 |
| 16 | 4 | 617.33 | 6,465.51 |
| 16 | 8 | 1,136.47 | 13,139.15 |

单线程 C/B 加载次数为 128→8。固定 LRU16 的 8 线程下，R1 的自愿上下文切换中位数为 30,773 次，R2 为 198,386 次，且每个线程持有独立缓存。这个实验确认 Provider 层会遇到线程和缓存复制开销，同时不能解释 GPU Local Scan 的全部差值。

真实 Edge processor 对 128 个 CAP2 请求，以相同 CFG seed 比较 uncached 和 memo。完整条件字段、dropout 和后续 Python RNG 哈希一致，Tokenizer 调用 128→15，中位耗时 126.544→15.141 ms。每组 16 个真实空文本分支。计时不含完整 Transform 或 GPU 文本 encoder。

独立 native resize probe 的 128 个 dense / compact 占位样本具有相同的几何哈希。3 次中位耗时 4,770.709→2.452 ms，resize 后每项像素存储 3,133,440→1 B。该 CPU 实验只执行占位层和原 Resize，未测 H2D 或模型。

另保存一次冷进程 R1 Provider `cProfile`，供核对 Python 调用树。CPU 文件是 `provider-r1.prof`，可用 `python -m pstats` 查看。冷进程 profile 混有框架导入开销，方法分解采用上表的预热后 Provider 请求时间。训练 CUDA kernel trace 和全链路火焰图仍为 NOT_RUN。

## 候选代码与语义

- 分别暴露 LRU4/16、Raw1/2/4/8、compact carrier、CAP2 memo 和 Spawn1/2/4/8。实验默认值仍为 sync、4、dense、memo-off。
- CAP2 memo 复用有界的 episode-static 内容与 dropout 两分支，输出保留完整 token、mask、position、任务/recipe identity。父进程按原 Consumer 顺序抽取 CFG。缓存命中后每个 Consumer 得到独立 tensor。
- Spawn 复用 No-TTT 的真实本地 G1 Source/Cache/Transform、每进程独立 G2 Provider、一次 active 与一次 speculative Window 调度。R1 通过 global-off 路径，R2 走现有合法 View 读取及 Tensor/Mask 来源。启用的 Root Provider 在准备时记录已使用的 DATA_C/B/语言/选图文件身份，在父进程消费前复核。源文件按已认证快照的只读发布合同使用。
- 父进程控制 Consumer 顺序、CFG 随机数、Local-TTT scan/update、collate、优化器、提交和 DCP。失败中止从未提交的 Window，收回预取并恢复父 RNG。终止步不提交下一 Window。DCP 只保存已提交的 Frontier；恢复后再创建队列。当前训练 recipe、Stage A 1000／B 29000 和每 100 步保存由现有代码负责。
- opt-in GPU trace 最多一个完整 optimizer step，每 Rank 记录 CPU/CUDA Chrome trace。使用单独 namespace 测 trace；普通计时与 trace 的数据分开。Profiler 事件用于判断 dispatch、同步、传输、Local scan 与 CUDA kernel，调度和 NUMA 需要相应系统测量。

## 可复现命令

原始训练记录和私有输入在 `data` 原位读取。使用仓库 checkout 和现有 PSM Python，模型与数据路径由 `configs/g2/robocasa365_target_atomic.assets.env` 和已有 formal recipe 提供。

```bash
python -m tools.g2.summarize_training_regression "$PRODUCTION_ROOT/outputs"
CUDA_VISIBLE_DEVICES='' "$G2_PYTHON" -m tools.g2.benchmark_training_cpu provider \
  --recipe "$R1_RECIPE" --workers 0,1,2,4,8 --caches 4,16 --episodes 8 --frames 16 --repeats 2
CUDA_VISIBLE_DEVICES='' "$G2_PYTHON" -m tools.g2.benchmark_training_cpu provider \
  --recipe "$R2_RECIPE" --workers 0,1,2,4,8 --caches 4,16 --episodes 8 --frames 16 --repeats 2
CUDA_VISIBLE_DEVICES='' "$G2_PYTHON" -m tools.g2.benchmark_training_cpu compact --repeats 3
CUDA_VISIBLE_DEVICES='' "$G2_PYTHON" -m tools.g2.benchmark_training_cpu cap2 \
  --recipe "$R1_RECIPE" --edge "$G2_EDGE_MODEL" --repeats 3
```

### Owner 手动 GPU 复验

从固定候选 Root 和 Gitlinked Child 启动。每次换独立 tag，使用 GPU4–7 且同一批已认证数据和 G1 Iter27700 模型。先分别跑 R1/R2，确认无其它进程争用这四卡并记录 CPU/GPU 条件。诊断 2 或 10 步，用 2 步验证实际模型输入，用 10 步比吞吐。下列是手动命令。

```bash
export G2_GPUS=4,5,6,7
export G2_OUTPUT_ROOT=/path/to/issue90-diagnostics
G2_DATA_LOADER=sync PSM_G2_EPISODE_CACHE_SIZE=4 bash scripts/g2/train_formal.sh r1 benchmark sync_lru4
G2_DATA_LOADER=sync PSM_G2_EPISODE_CACHE_SIZE=16 bash scripts/g2/train_formal.sh r1 benchmark sync_lru16
G2_DATA_LOADER=sync PSM_G2_EPISODE_CACHE_SIZE=16 PSM_V3_COMPACT_CACHED_VIDEO=1 \
  bash scripts/g2/train_formal.sh r1 benchmark sync_compact
G2_DATA_LOADER=sync PSM_G2_EPISODE_CACHE_SIZE=16 PSM_V3_COMPACT_CACHED_VIDEO=1 \
  PSM_G2_CAP2_TOKEN_CACHE=1 bash scripts/g2/train_formal.sh r1 benchmark sync_compact_memo
for loader in raw1 raw2 raw4 raw8 spawn1 spawn2 spawn4 spawn8; do
  G2_DATA_LOADER="$loader" PSM_G2_EPISODE_CACHE_SIZE=16 PSM_V3_COMPACT_CACHED_VIDEO=1 \
    bash scripts/g2/train_formal.sh r1 benchmark "compact_${loader}"
done
G2_BENCHMARK_STEPS=2 G2_PROFILE_TRACE=1 G2_DATA_LOADER=spawn2 \
  PSM_G2_EPISODE_CACHE_SIZE=16 PSM_V3_COMPACT_CACHED_VIDEO=1 \
  bash scripts/g2/train_formal.sh r2 benchmark spawn2_trace
```

对 R2 分别重跑 sync 和选中的 Spawn 配置，用 R2 的实际 native input witness 核对 View。比较每 Rank 顺序、每步 loss/gradient、CPU 阶段与关键 Rank CUDA 时间，分别标注首次初始化、末步采样与 checkpoint。诊断 namespace 的 checkpoint 拒绝 Resume。正式 strict-resume 和 Iter1000 转阶段验收需要独立受控执行及每 Rank sidecar，对比未中断分支；2/10 步诊断不会跨该边界。

运行 Gate 通过后，Owner 的正式新任务入口示例：

```bash
G2_DATA_LOADER=spawn2 PSM_G2_EPISODE_CACHE_SIZE=16 PSM_V3_COMPACT_CACHED_VIDEO=1 \
  bash scripts/g2/train_formal.sh r1 fresh reviewed_spawn2
G2_DATA_LOADER=spawn2 PSM_G2_EPISODE_CACHE_SIZE=16 PSM_V3_COMPACT_CACHED_VIDEO=1 \
  bash scripts/g2/train_formal.sh r2 fresh reviewed_spawn2
```

正式 Resume 使用同一 job tag、源码和已确认的运行配置。正式选择的 worker 需要用上述 A/B 实测确定。只有两组独立 Gate 通过后才执行共享四 GPU 的容量与总完工时间实验。

## 固定源码与验收边界

- 正式基线为 Root `77fe8fe475350bbbbfce8e18cced0e7339558544`、Child/Gitlink `3d2eba6996fef459dbc8f4b48eca97aedad43608`。候选在合入诊断 PR #23/#24 后的 Child `952aa13ed04d1e3dde173dc8542ba0781db3def9` 上实现。
- 固定候选 Root `3ac7cb3fbb33545c7ca755b8e866542a147990cc`、Child `4cca4e977f3b5609dd3892825404faf83aeed8f9`。两个 PR 都采用 Draft。 [Root #91](https://github.com/wxwy/psm_wma/pull/91) · [Child #25](https://github.com/wxwy/cosmos-framework/pull/25)
- 真实 CPU native rank0 对照跑在 Root `b252a09b173cc54396eee84d3fff567619c5ecea`、Child `0e9b25ad2f740f9e84674895c24df3b2c19f9e7c`。两 profile 各一 Window、512 Consumer、51 dropout、2 Spawn workers。R1 零 View、R2 1,856 条 View 引用。逐 Consumer 完整 payload、原始 action/state、CAP2 条件、View tensor/mask 和来源、交错的父进程 RNG 与最终 Planner frontier 指纹完全一致。最终源码补父路径软链接检查、修正计时汇总和更新回归夹具。
- 文件凭据适用认证数据的不可变和原子发布约定。父进程复核文件身份和规范路径。相同 inode、大小和时间戳粒度内的直接覆盖不应作为有效生产发布。已有内容哈希验证仍留在实际数据读取路径。
- Child 首次运行被上游 pytest hook 改写设备可见性，随后中断该 pytest。复跑显式隐藏设备并关闭自动插件和 conftest。未运行实际模型训练。真实 Native CPU 子进程退出有资源跟踪器清理 loky 信号量的提示。
- 原始日志与 profiler 保留在 `data` 的隔离目录 `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_issue90_cpu_20261119.Lp0Al9/`。仓库保存派生测量、受版本控制的入口和复现命令。 [原始命令](../collab/codex/evidence/2026-11-19_issue90/commands.json)
- 最终候选 Root CPU 247/247，Child 聚焦 CPU 107/107，17 个较长 legacy loader 用例另行筛出。上一份同产品源码的 GPU-hidden 宽套件 248 通过、1 跳过、1 失败。失败为同尺寸原位覆盖落在文件系统时间戳粒度内，最终回归使用实际支持的同尺寸原子替换，并验证软链接替换。 [机器结果](../collab/codex/evidence/2026-11-19_issue90/results.json)
- **NOT_RUN**。GPU 2／10 步候选耗时、真实 R2 GPU Forward、GPU 跟踪与火焰图、四 Rank strict DCP Resume、Iter1000/1001 阶段边界、一机双任务吞吐。现有 CPU 数据不能证明候选低于 35.7 s/step。仓库 V3 执行分工由 Owner／执行端启动 GPU，文档提供隔离命令。
