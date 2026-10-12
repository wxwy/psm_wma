# PSM-WMA V3 — Dense默认关闭优化与训练JSON控制台过滤：CPU Gate正式闭合

**Date:** 2026-10-12
**Formal Implementation Pair:** **Root `b159f45906f7261d028aecc226ab7f2bb9807eb9` / Child+Gitlink `937066ffd90f2bf783ad4fbb4909e9c0b8922982`**。
**Gate:** `V3_DEFAULT_OFF_CACHES_AND_QUIET_TRAIN_CONSOLE`。
**Verdict:** **APPROVE — this CPU implementation/acceptance Gate only**。
**Previous Gate status:** `CODE_COMMITTED / STATIC_DIFF_SCOPED / TEST_EVIDENCE_PENDING` (review `docs/collab/chatgpt/reviews/2026-10-12_V3_console_only_progress_dense_defaults_implementation_review_b159f459_937066ff.md`)→ **`TEST_EVIDENCE_CLOSED / GATE_A_PASS / GATE_B_PASS`**。
**Evidence:** `docs/collab/chatgpt/evidence/2026-10-12_V3_console_dense_defaults/DS_PRO_2026-10-12_dense_default_quiet_console_CPU_acceptance_owner_relay.md`，DS_PRO由Owner转交的定点CPU测试报告。该报告为Owner-relayed，GPT没有从DS真实测试机独立读取pytest原始 stdout或实时Formal Job文件；GPT已重新回读远端源代码、对比SHA及覆盖的测试函数。

## 当前实现SHA身份

- GitHub远端`wxwy/psm_wma:V3` HEAD仍是同实现的docs-only后继版本；真实新的implementation Root固定`b159f45906f7261d028aecc226ab7f2bb9807eb9`（只改子仓Gitlink）。
- `wxwy/cosmos-framework:v3-local-ttt` Child`937066ffd90f2bf783ad4fbb4909e9c0b8922982`，主仓Gitlink亦为`937066ffd90f2bf783ad4fbb4909e9c0b8922982`；相对于`e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c` Child精确五个受审文件。此轮没有再修改实现Pair；原技术审核不重做，只核对新Evidence是否关闭未决测试项。

## Contract / Behavior / Evidence 闭合

**Gate A — PASS：**
- `compact_cached_video_enabled()`与`install_rank_shared_reader()`的env缺省均为`"0"`，两条默认关闭优化；显式`"1"`仍正常启用，非法值仍ValueError；无`job_name`/`resume`特判。
- DS在新Child单独CPU测试实际dataset video`uint8(3,17,256,512)`、连续、全零且完整storage；unshared源reader保持未安装；显式1/1验证compact proxy和shared reader联通。
- 正式Dense应用仍建议明确记录并设置0/0（不依赖默认值来证明历史实验身份）；只在**未指定变量时**改变新版本行为，`config_digest()`实现没有修改不自动证明跨运行所有配置语义一致。

**Gate B — PASS：**
- `TelemetryJournal.__call__()`照旧先写机器可读`monitor/train_rank0.jsonl`，并append`monitor/rank0.log`，但`TRAIN_PREFIX`不再console echo；其余`[progress]`、`[checkpoint]`、`[logging_error]`和其它告警不会被过滤。
- DS`examples/psm_wma_robocasa_formal_monitor_test.py` **10 passed**，包括history/replay/read_train_records及console异常回调、Raw保留等。正则的普通train dict仅rank0正常产生，非 rank0不应被误说成每步8份完整JSON。
- JSONL解析及schema不变；没有训练计算路径、optimizer step、checkpoint回写差异。

**环境检测 Teardown第一次失败：记录但不阻断此次Gate**
- DS首次运行数据集测试得到**11 passed +1 ERROR**，是已有`cosmos3_action_lerobot.py`设置HF_HUB_OFFLINE与`conftest.py`全局环境变化检查交互。GPT源码检查该事实成立。第一次不记为PASS。
- 预置正式训练环境变量`HF_HUB_OFFLINE=1`后**11 passed**，无error；两个测试文件总共21项在已声明的训练等价环境下全绿，5文件`py_compile`/ruff均PASS。故此一已明确隔离的既存teardown环境限制**不是此次定点生产行为的blocker**。暂不授权修改其它conftest/lerobot文件来美化测试数。
- 测试执行由DS报告，未在GPT本地完整依赖环境重跑，符合基于Owner转交Evidence的窄范围Gate判断，不代表全库regression或GPU Gate。

## Formal30k训练运行与安全边界：另行判断，不继承本APPROVE

- DS发现旧正式训练的`robo15train`在**iter839**后收到**SIGINT(2)**并已不在运行；GPT没有直接验证进程及原Job实时DCP pointer。其此前使用过Compact/Shared ON/ON，**不符合原合同 Dense OFF/OFF 的同模式运行**；迭代801–839应标注mode-deviation且不能自动当Dense正式证据。
- 训练仍绑定其启动时旧Root `444c232b976e80ac68cde9e7370e73b9f6410f0e` /旧Child `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`。本次代码虽然在新Root `b159f45906f7261d028aecc226ab7f2bb9807eb9`/Child`937066ffd90f2bf783ad4fbb4909e9c0b8922982`已APPROVE CPU门，不等于训练服务器可直接`git pull`或从iter839续训。下次恢复先只读确认`latest_checkpoint.txt`、DCP组件/8rank sidecar/新旧attempt provenance、当前运行进程及env，并由Owner选择严格OFF/OFF恢复路线（原版本显式0/0，或者另行独立批准新的FormalPair）。
- 如果最新DCP仍是原已经C1验证的iter800，则按约定回滚重放801以后；若指向其它checkpoint，必须核实真实模式、checkpoint来源和hash，ON/ON来源不可默认为Dense恢复起点。保存旧运行JSONL的history，日志只做replay-aware衍生读取。
- **本APPROVE仅解决新代码的两项CPU功能，不授权GPU、原任务DCP修改、重启、部署、D1不同模式数值等价或覆盖此前正式Root审查。** C1 CLOSED、原D1严格numerical FAIL不变。

## 结论

**`APPROVE / CPU_ACCEPTANCE_CLOSED`**。无需再让DS为这两个代码功能重复跑相同测试。后续仅当Owner需要把新Pair用于实际Formal30k恢复时，按原受限部署/资源/Preflight流程处理当前作业状态与checkpoint模式漂移，而非重开本Gate。