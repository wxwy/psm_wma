# Issue35 K16 首次慢段与长尾：外部诊断探针

2026-11-10，Asia/Shanghai。此包只增加诊断工具，不修改生产源码、训练、编译参数、Memory 或 Attention。真实运行对象仍为已限域批准的 Formal Root `1b184204e301a51a7a20ed4dde1a11689589cf2d` / Child-Gitlink `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`。新文档分支不是新生产配对。

本轮 **34/34 CPU 探针测试 PASS**，未启动 H100、模型或仿真。首次约890ms慢段和1295.667ms长尾的实际根因仍为 **UNKNOWN**；`COLD_START_AND_LONG_TAIL_LATENCY_STABILITY=OPEN`。本工具不关闭性能Gate，不授权V3合并。

## 为什么这些观测仍然必要

正式独立报告已证明真实K16严格数值相同，并测得热态ON/OFF配对节省P50=33.853ms、29/30次ON更快；同时保留首次慢段和偶发长尾。Dynamo `unique_graphs=8`稳定只表示没有观测到新增Dynamo图，不能证明CUDA图录制/回放、库内初始化、主机调度、内存分配或GPU时钟均不变。生产 `velocity_fn` 仍有原生 `cudagraph_mark_step_begin()`；这里只把CUDA图状态作为待核查项，不据此宣称它是根因。

不重新执行K1/No-TTT或此前314项CPU，不增加Attention优化。下一次收集仍只用原Local iter15000、K16/source64、B1/H16/raw15、guidance1、30-step UniPC及服务器既有冻结输入和严格Action/Vision检查。

## 工具行为与限制

`probes/latency_probe.py` 用 `runpy` 执行服务器原有K16 runner，仅在 `OmniMoTModel.generate_samples_from_batch` **编译边界外层**包一层。所有参数按原样转发，返回原对象，原异常继续抛出；不读取输入/输出Tensor，不重新编码、构造Prefix、恢复/抽取RNG或额外执行模型。

- 前后检查精确clean Formal Root/Child/Gitlink，runner文件SHA256不变；探针与输出须在工作树之外。既有 `verify_source()` 和模型/设备证明保留，不关闭或规避它们。
- CLI强制只接受一次显式 `--k 16 --step 64`（支持等号形式），缺失、重复、K1等拒绝。它验证原runner参数，不代替原runner对完整请求和状态的严格检查。
- 每次调用记录Host wall边界、process/thread CPU、线程schedstat、进程page faults/context switches、GC时间、已有Dynamo计数器、CUDA allocator计数和缓存开关参数。开关参数不等于实际绑定证明，不能据此代替此前31次真实binding证据。
- 可在原当前stream前后记录CUDA events，**不额外同步**、不设置device/stream、不reset内存统计、不修改GC、编译或allocator配置。事件未就绪时标注缺失，不能把缺失计成0ms。`--no-cuda-events`提供无事件控制；其他Host/allocator观测仍存在。
- 不开启逐层或逐step hooks；不触发编译计数器模块的额外导入。所有缺失/失败显式记录；无调用、collector失败、source/runner变化时CLI不会给出`RECORDED`成功。原runner的非零退出/异常优先保留。
- 本探针只支持既有串行回放。重入/并发调用不加锁排队，继续原调用并把诊断标记不完整；不声称具备多Server观测能力。

**时延口径必须区分**：`host_wall_ms`是原生成方法调用到返回，不含既有runner随后执行的同步；`cuda_event_ms`是当前stream的事件跨度，含设备idle/排队空隙，不是Kernel执行总和。原runner的GPU/wall计时可能包含探针前后CPU/写日志开销，故本次计时是**有观测扰动的诊断数据**，不能替换未插桩性能结果。预/后观测时间另记，但不覆盖全部JSON写入；不能直接相减得到“零开销”。

GC回调和metadata对象本身可能改变GC发生时刻；若发现GC关联，仍须用独立轨迹/控制确认。CPU时间差与wall时间范围也有少量边界偏差，不能把CPU、GC和GPU inclusive时间相加或精确相减作根因证明。

## 已有服务器入口（仅查看目录及CLI声明，未执行）

`G=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/issue35_prefix_projection_independent_20261110`

- clean生产工作树：`$G/root`。
- 连续ON和Dynamo计数复验：`$G/benchmark_new_on_dynamo.py`。
- 同进程ON/OFF交错：`$G/benchmark_projection_paired_K16.py`。
- 原始记录和私有Tensor仍在服务器原位置。没有复制这些文件到本包。

执行者沿用其上一轮已审核的Python解释器、checkpoint/config、frozen request和原始reference路径。下列 `ISSUE35_*` 是**执行侧必须从上一轮原命令恢复的输入**，不是可猜测的新路径；任何变量缺失先停，不启动模型。Codex本轮没有读取checkpoint或Tensor以填写这些值。

## 第一次诊断：一轮受控连续ON，不随机反复重跑

先由GPT核对原始命令/输入/设备、选定新输出目录，向Owner显示实值命令。将本包自有probe复制到工作树之外；不要把diagnostic文档HEAD检出覆盖Formal工作树。

```bash
G=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/issue35_prefix_projection_independent_20261110
: "${ISSUE35_PYTHON:?reuse the original interpreter}"
: "${ISSUE35_PROBE:?external path to latency_probe.py}"
: "${ISSUE35_FROZEN:?reuse the exact K16 request_0064.pt}"
: "${ISSUE35_REFERENCE:?reuse the exact approved original Local reference}"
: "${ISSUE35_CHECKPOINT:?reuse Local iter15000}"
: "${ISSUE35_CONFIG:?reuse its matching config}"
EVID="$G/latency_diagnostic01"
test ! -e "$EVID" || exit 1
mkdir "$EVID"
cd "$G/root"
```

先启动下一节的独立遥测会话，确认已有CSV记录，再在上述同一主会话执行原生回放：

```bash
env CUDA_VISIBLE_DEVICES=6 LD_LIBRARY_PATH='' \
  "$ISSUE35_PYTHON" "$ISSUE35_PROBE" \
  --root "$G/root" --runner "$G/benchmark_new_on_dynamo.py" \
  --out "$EVID/observer" --cuda-device 0 -- \
  --root "$G/root" \
  --formal-root 1b184204e301a51a7a20ed4dde1a11689589cf2d \
  --formal-child d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2 \
  --frozen "$ISSUE35_FROZEN" --reference "$ISSUE35_REFERENCE" \
  --ckpt "$ISSUE35_CHECKPOINT" --config "$ISSUE35_CONFIG" \
  --k 16 --step 64 --gpu 6 --warmup 4 --n 50 \
  --out "$EVID/native" >"$EVID/run.log" 2>&1
```

资源仅原GPU6，一次加载、一轮4暖机+50测量。没有新No-TTT、K1、仿真、SR或900EP。若原环境还需已有PYTHONPATH/offline变量，逐项保留；不改变编译上限8或原有编译mode。GPU可用性由实际执行侧核对，文件列表检查不证明GPU空闲。

### 同时间轴设备遥测

使用执行侧已有工具，仅记录所选GPU的聚合状态，不枚举/停止其他任务，不设定时钟/功率。可在同一诊断的独立会话使用以下命令；只在检查当前驱动支持全部字段后启动，错误原样保存，不把不支持字段伪填0：

```bash
EVID=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/issue35_prefix_projection_independent_20261110/latency_diagnostic01
test -d "$EVID" || exit 1
nvidia-smi -i 6 \
  --query-gpu=timestamp,uuid,pstate,clocks.current.sm,clocks.current.memory,power.draw,power.limit,temperature.gpu,utilization.gpu,utilization.memory,memory.used,clocks_throttle_reasons.active \
  --format=csv --loop-ms=200 >"$EVID/gpu.csv" 2>"$EVID/gpu_telemetry.log"
```

采样进程也有开销，不能把其结果直接当成未观测生产P99。`host_before/after`同时保存Unix/monotonic ns，用于关联原生result、generation.jsonl和设备CSV。执行结束只关闭本次自建采样进程，保存自己的PID/退出码；不动已有任务。

## 按观测结果决定下一步

| 同一慢/快样本的证据 | 能支持的排查方向 | 仍不能直接下的结论 |
| --- | --- | --- |
| Host跨度增加、runqueue/context-switch变化，CUDA时间线出现host送核空洞 | CPU抢占/主线程停顿/GC候选 | CPU或GC已被证明是旧运行的根因 |
| allocator重试/同步/设备分配计数随慢样本增加 | allocator/显存压力候选 | 单看reserved增长就等于OOM或内存缺陷 |
| 同一Kernel工作量下SM时钟、Pstate/功率限制与慢段对应 | 设备频率/功率/争用候选 | 没有同步时间线也能归因于外部负载 |
| Dynamo计数不变，CUDA图/库调用轨迹仍发生变化 | CUDA Graph或库内运行时行为候选 | unique_graphs稳定证明所有编译/录制都不变 |
| 所有上述信号未关联、慢段未复现 | 证据不足 | 问题已修复或Gate已通过 |

若首次记录仍不清楚，仅再安排必要的同进程ON/OFF交错或一个有trace的受控复验，不盲目重复整套性能测试。原paired runner保持 `--k 16 --step 64 --physical-gpu 6 --triplets 30 --warmup 4`，其余输入完全同前；probe只替换runner路径/透传相应原参数，不改runner。无事件控制或未插桩控制必须独立标记，不能混入同一性能分布。

需要CUDA因果轨迹时，优先用执行环境已有Nsight Systems采集CUDA API、CUDA Graph、cuBLAS、GPU kernel及OS runtime时间线；不存在则报告工具缺口，不自动安装或换后端。可单独启用当前PyTorch实际支持的`TORCH_LOGS=cudagraphs,recompiles`记录，但必须把日志/Profiler扰动与无trace计时分开，不改任何compile选项。所有trace/私有路径/原始数据只留服务器。本包没有假定驱动/工具版本或先验根因。

## 输出与停止条件

- `metadata.json`：source/runner/probe身份、调用数、诊断错误；`RECORDED`仅表示记录完成，不是性能PASS。
- `generation.jsonl`：generation、cuda_span/unavailable和observer_summary，通过call编号关联。保留暖机、全部慢段/离群、缺失值和所有失败。
- 原native `result.json/run.log`、遥测CSV、可选系统trace，以及前后source guards保持。
- 任意原严格数值断言、source/设备校验或原runner失败立即停止该诊断，保留首错，不自动重跑。collector失败则标记`DIAGNOSTIC_INCOMPLETE`，不能以缺失字段解释根因。
- 只有慢/快样本的同时间轴机制证据支持首因，才提出对应最小代码修复。未复现或无对应关系则`INCONCLUSIVE`，稳定性Gate保持OPEN。不得删除慢样本、扩大warmup隐藏慢段，或用50次有限样本宣称生产P99已通过。

## 本地CPU证据

`raw_cpu/dev01`为最初26项PASS与当时两个源文件；`dev02`保留两项样式错误及当时源文件，pytest未执行；`dev03`为最终34项PASS、0失败/错误/跳过、Shell0和两文件静态通过。34项包含前26项，不相加。使用模拟CUDA和CPU Tensor测试透明性，无checkpoint、GPU context或真实回放。

在本包`probes/`目录、已有CPU Python环境中复跑（新建输出目录）：

```bash
env CUDA_VISIBLE_DEVICES='' LD_LIBRARY_PATH='' \
  OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  PYTHONPATH="$PWD" /workspace/.venvs/psm-wma-cpu/bin/python -m pytest \
  --noconftest -c /dev/null --rootdir="$PWD" -p no:cacheprovider \
  -q probe_test.py --junitxml=/path/to/new_cpu_evidence/junit.xml
```

CPU PASS不证明观测开销为零、CUDA API在目标驱动上的兼容性、诊断一定能复现慢段或其根因。当前生产批准仍只按正式独立报告；没有新GPU结果，没有V3合并。
