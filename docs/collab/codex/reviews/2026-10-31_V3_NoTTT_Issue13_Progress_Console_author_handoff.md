# Issue #13 — No-TTT 默认 Progress-only Console：作者交付与增量审核申请

2026-10-31（Asia/Shanghai）。本次仅 Root 日志输出层；**新代码待 GPT 审核，
未合并 V3，不授权训练、GPU 或修改 C12200 A/B。**

| 对象 | 精确身份 |
| --- | --- |
| Formal Implementation Root | `24dbb677f7a60eeab6934c44352c7e00fa6d9b36` |
| Child / Gitlink（未改） | `0ae313e329d290fc6b8a50fda1112820fb7ac485` |
| 源码基线 / Owner任务书 | V3 `3332d1825de8778e3d6dbb7e9ba98cbffff487c6` |
| 隔离候选分支 | `v3-nottt-progress-console-20261031` |
| 后续已读 canonical 文档 HEAD | `2bcc27e94576837167cacd190af7dc837e6129cd` |

实际读取 Issue13、最新 canonical Inbox、正式实施单、标准4/8GPU入口和 Child
Observer/Journal。Owner明确默认生效，覆盖先前外部可选过滤建议。后续2bcc27e9
仅新增另一Pair的性能Review/Inbox；已完整保留到本候选（f9d6d246文档merge），
与Formal24dbb677相比仅两文档不同，**不改变本次Implementation Pair**。
本任务不继承 Issue12 GPU性能批准，也不推进那条线的移植或正式Resume。

生产改动只有三份 Root 文件：

- `scripts/train_v3_matched_no_ttt.sh:27` 与 `_4gpu.sh:68`：默认经共享输出包装器
  执行**原来整条**torchrun命令。原训练Python、argv、Admission、环境export、cwd、
  Profile/Worker选项全部保留；没有新增启用开关。
- `scripts/no_ttt_console.py`：仅标准库的前台包装器，无Torch/CUDA/model导入。
  合并训练stdout/stderr，以未过滤的原始字节先写唯一文件，再只回显完整的
  `[CorrectedV3][progress] `行。既有Phase5 `human_progress=rank==0`、Observer
  非rank0早退提供Rank0来源；不改进度内容或Journal。

每次运行使用 `OUTPUT_ROOT/_launch_logs/JOB_NAME/launch_<ns>_<random>.log`，
O_EXCL独占创建、权限0600，Resume新文件不覆盖旧文件。该目录不提前占用正式
Trainer Job Namespace。开始时仅打印一次完整日志位置；正常训练只回显进度。
训练`monitor/train_rank0.jsonl`、`monitor/rank0.log`及其保存时机完全未改。

包装器明确等待真实训练退出，exit7仍返回7；SIGINT/TERM返回130/143。失败终端
显示 `[NoTTT][failed]`、wrapper/child退出码、日志路径和最后8KiB上下文。原始
日志保存所有已输出字节，不在写入前过滤。写入处理短写；关闭时fsync，任何
日志setup/write/sync/close错误均非零并停止本次owned训练。没有每步fsync。
巨大或未完成诊断行的显示缓冲有16KiB界限，完整raw不截断；正常进度远小于
该界限。无进度、只有warning且子进程exit0也正确返回0，不受grep空匹配影响。

torchrun的Rank可独立Session，故单杀外层PGID不充分。包装器只在shutdown阶段
使用Linux子reaper和自身后代树，核对PID start token，允许5秒退出，再有界
freeze/kill/reap/drain；不信号其它Job，不在正常训练步扫描`/proc`。系统前提为
Linux `/proc`、subreaper及系统`python3`；训练本身仍用原`$PYTHON`。该前提缺失
或日志初始化失败时，不启动训练。Child、模型、Loss、Optimizer、Loader、
120秒Timeout、Config、Frontier、DCP/RNG和Local-TTT/EvalV2全部未修改。

## 作者 CPU / 静态证据

证据目录：
`docs/collab/codex/evidence/2026-10-31_nottt_issue13_progress_console_author_cpu/`

| 项目 | 结果 |
| --- | --- |
| 精确clean Formal Pair 合成CPU | **49 passed：21新增 +28既有launcher用例，0fail/error/skip** |
| 测试时间 | JUnit/pytest20.79s；外层命令21.28s |
| Bash语法 | 两份脚本分别 `bash -n`，均exit0 |
| ShellCheck | 0.10.0，两份脚本PASS |
| Ruff / format / AST | 0.12.7，4个变更Python文件全部PASS |
| 版本 / 源码 | Root/Child/Gitlink精确；前后clean，6份源码SHA256不变 |
| 原断言 | 两个旧fixture文件全部46条原assert AST保留；仅输出读取/helper复制及格式改变 |
| 原训练调用 | 两脚本整个训练命令文本、前置Admission/export/cwd逐字相同；另4/8GPU×Fresh/Resume完整fake argv/关键env相等 |
| 原始封装 | 38项artifact SHA256、6项Formal Git Blob/SHA绑定；原始JUnit/log/命令/env/Diff/审计/两个console+raw示例 |

覆盖正常进度与stdout/stderr逐字保留、Rank1/Loader/train/checkpoint/traceback
过滤位置、exit7、warning无progress、连续Resume不覆盖、不占Fresh namespace、
超长/碎片化/无效编码raw、进度实时刷新且log先写、日志open/write/fsync和管道
初始化失败、exec失败、SIGINT/TERM、忽略TERM的独立Session Rank、终止期间
新建子进程、父进程先失败但子进程持管道、foreign存活。真实local PID均回收。

`examples/exit0/console.stdout` / `examples/exit7/console.stderr` 和各自
`full_launch.log` 为**额外两次真实捕获的假训练输出示例**，不加进49项统计，
不冒称真实训练日志。`history`中先前17/49 PASS与最终49不累加。无测试失败。
内部审计是作者证据，不等价于GPT或DS独立运行。

为跟上新默认输出，旧Fake Python测试从原始full log读取其JSON；训练命令/
profile/拒绝条件/Resume断言未放松。旧两文件同时按Ruff格式整理，无生产语义
变化。没有运行其无关推理/Job生命周期测试，也**未重跑旧NoTTT CPU58/301**。
没有真实模型、数据、torchrun、DCP或GPU执行，没有GPU加速或性能等价声明。
新增工作仅为必要输出I/O与前台监督，不加训练步统计或设备同步。

重放：从Evidence HEAD导出 `run_gate.py` 到工作树外，在干净Formal Root上运行：

```bash
python '<EXPORTED_EVIDENCE_HELPER>/run_gate.py' \
  --root '<EXACT_FORMAL_WORKTREE>' \
  --expected-root 24dbb677f7a60eeab6934c44352c7e00fa6d9b36 \
  --expected-child 0ae313e329d290fc6b8a50fda1112820fb7ac485 \
  --shellcheck '<SHELLCHECK_BINARY>' \
  --evidence '<NEW_EXTERNAL_EVIDENCE_DIR>'
```

该helper/证据在后续文档提交中，不在Formal代码提交里；不得将Evidence HEAD
替代Formal Root。脚本仅执行fake shell场景，HF/Matplotlib/XDG/Ruff缓存全部
写独立目录，原始命令与安全环境覆盖记录完整；不输出继承的秘密环境。

## 提交与停止

请GPT对**新24dbb677 / unchanged0ae313e3**进行Issue13最小增量Code Gate，
给出 `APPROVE_CODE / REQUEST_CHANGES`。未自动关闭Code Gate，未要求DS/GPU
复跑。Root后续Evidence/Inbox/回验记录不是新的Implementation SHA。

发布隔离分支并回验后STOP。没有合并/推送Canonical V3或修改其Child；没有
操作正式NoTTT/G1、C12200 A/B冻结工作树/命令、任何训练Checkpoint、Config、
Job Identity或历史Evidence。未来Owner批准提升时，仅移植这三份Root生产文件
和必要测试，不整树覆盖其它NoTTT/EvalV2候选，也不因本日志任务重跑GPU对照。
