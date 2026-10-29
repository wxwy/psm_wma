# DS_PRO — Issue #9 No-TTT Async Overlap 独立合成 CPU Gate（一次性精确 Pair）

- 日期：2026-10-29；**状态：GPT Code Gate `APPROVE_CODE` 后授权的 CPU-only Evidence replay 指令；不是GPU/真实数据/训练授权。**
- **Formal Root `e0fe911dfb9fd34957234828195cf051713f6c3d` / Child+Gitlink `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7`**。任何SHA不一致直接 `BLOCKED_WRONG_PAIR`，禁止自行 checkout修复当前活动工作树。
- Code Review：`docs/collab/chatgpt/reviews/2026-10-29_V3_NoTTT_AsyncOverlap_e0fe911d_f6a92d47_Incremental_Code_Gate_APPROVE_CODE.md`；Code任务 [Issue #9](https://github.com/wxwy/psm_wma/issues/9)。另一只读现况任务 [Issue #10](https://github.com/wxwy/psm_wma/issues/10) 是分开的，请勿与本 Gate混用产物。
- **永不触碰运行中的正式 No-TTT** `no_ttt_packed128_droid_fresh_30k_world4_ga4` 或它的活跃源码/identity/checkpoint/进程/清理策略，G1和GPU0–7都不允许启动测试/抢占。此任务只允许运行隔离、无真实数据、CUDA隐藏的合成 CPU tests（与作者相同合同），不允许生产CUDA、真实DCP或模型数据读取。

## 一次执行的现场/输入条件

在 DS 允许的全新、**独立于活动训练工作树**的临时 Git clean detached Root worktree（包含精确Child repo工作树/Gitlink）中运行。只从已发布Git SHAs复制源码，不能 reset、pull、merge、git checkout 或强推活动训练工作树。无干净隔离目录或必要 Python依赖时，仅返回 `BLOCKED_ENVIRONMENT`，不要碰旧 Job。

- CPU环境已安装 torch、pytest、Ruff **0.12.7**，本地离线；执行脚本自动设置 `CUDA_VISIBLE_DEVICES=""`、offline和cache到新 evidence-dir。该CPU脚本在测试内确实创建可控本地小型 synthetic source/cache和真实spawn CPU worker；**不会读取真实 RoboCasa 数据、HF外部模型、GPU或DCP**。
- 新外部证据目录必须不存在，且不在Root/Child source内。由DS自主选择唯一命名，例如 `/tmp/dspro_nott_async_e0fe911d_f6a92d47_<unique>`；不能覆盖作者历史 `locked03`。
- **启动前核对** Root HEAD/Child HEAD/Gitlink、`git status --porcelain`均干净；禁止动训练服务器中的正式工作树/本地4个未推送Evidence提交。
- **唯一项目测试命令**，在隔离 Root 根目录使用符合依赖的 Python，按实际选择的唯一Evidence路径替换：

```bash
cd /PATH/TO/ISOLATED_CLEAN_ROOT
python tools/v3/run_no_ttt_async_cpu_gate.py \
  --root-worktree "$PWD" \
  --expected-root e0fe911dfb9fd34957234828195cf051713f6c3d \
  --expected-child f6a92d47b6dac7998ddc58b3da26ef93f8068dc7 \
  --evidence-dir /tmp/dspro_nott_async_e0fe911d_f6a92d47_UNIQUE
```

该CPU-only Gate会在Runner内一次执行准确的三套新async测试＋8套旧Regression清单、Ruff、format、AST、精确Source哈希和raw JUnit生成；**禁止附加第二轮实机模型、GPU、DCP、RoboCasa、性能实验**。若首轮FAIL，保留 Evidence，STOP 报告，无自动重跑/更换断言或补丁。

## PASS/FAIL和回传

- PASS：`gate.json: status=PASS, source_unchanged=true`，精确 Root/Child/Gitlink；`async.xml`的72项和`regression.xml`的229项组成301项全部0fail/error/skip；显式被排除的1个真实数据节点保持 NOT_RUN（不计PASS），Ruff/format/AST13均exit0。
- 直接验证 `timelines/overlap_trace.json` 含3 Window且真实CPU spawned Source+Transform与fake compute的 **later Member 和 next Window** 均有正交集；不能只看 worker PID 或测试标题。参照作者基线说明该测试不等于GPU加速。审计四逻辑Rank、B8/T16/GA4/partial、nw0/1/2/4/8、CFG三流RNG、old→new same-job Frontier、worker crash/timeout PID/外部进程隔离。
- `source_sha256.json`/日记、`gate.json`、`junit.xml`、`async.xml`、`regression.xml`、`async.log`、`regression.log`、`ruff*.log`、timeline/worker清理原件均保留在独立 Evidence 目录，报告具体路径与按合同算出的数字；无需复制 30k DCP、作者81份归档、真实视频或重新跑原 Compact CPU Parity。
- 如 native source/digest/timing失配或GPU访问，明确 FAIL 并保留证据；严禁以“作者301PASS”代替DS自己的独立结果。没有GPU设备/训练环境不是此CPU Gate BLOCKER。
- 报告最后单列：`DS_CPU = PASS/FAIL/BLOCKED`；`REAL_GPU_PERFORMANCE=NOT_RUN`；`REAL_DCP_RESUME=NOT_RUN`；`FORMAL_JOB_UNTOUCHED` 若可真实见证，否则 `NOT_VERIFIED`。STOP 等GPT独立增量Evidence Review，不自行merge或启动下一阶段。

如 DS 设备离线只能交 `BLOCKED_CONNECTIVITY`；发出本指令不表示已执行。
