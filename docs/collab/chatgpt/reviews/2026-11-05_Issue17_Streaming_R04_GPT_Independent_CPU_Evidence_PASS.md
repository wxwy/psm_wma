# GPT 执行验收记录 — Issue #17 Streaming CPU869 与 R04 Action-Compile CPU51

**记录日期**：2026-11-05（UTC+08；服务器记录为 UTC）  
**Issue #17 独立执行 Verdict**：`CPU_GATE_PASS_WITH_EXPLICIT_TEST_ENV_COMPAT`  
**R04 Action-Compile 独立执行 Verdict**：`CPU_TARGETED_PASS`  
**边界**：真实GPU/H100/完整机器人仿真、正式评测、R04 原Run Resume、V3/G2 promotion 均**未执行、未授权**。

## 1. Formal 身份（全部来自独立干净 Git 工作树）

| Gate | Root | Child / Root Gitlink |
|---|---|---|
| Issue17 Work-conserving M32/B32 | `551b03621507dde52303f54290d4fea89d66e8da` | `82fa270e8cdb76b3e1a4e94adf0c7ce2b497884e` |
| R04 VFM Action dynamic compile | `c9fa60b7134fda8fb848c29c148f25c7a8901892` | `4e9c8104ffd15a373b576bc35ee608de1b60eea1` |

两组分开新建的Git clone，均在服务器独立目录执行，均锁定完整Root/Child SHA，测试后双仓 `git status --porcelain`为空。**没有**在生产 `psm_wma_v3` 工作树执行、改写旧R04或改任何生产代码。

## 2. Issue17 全量 CPU Gate 实际最终结果

入口：`tools/v3/run_eval_v2_streaming_cpu_gate.py`，原项目 runner；`CUDA_VISIBLE_DEVICES=''`、OSMesa、offline cache、单线程BLAS。证据目录：

`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/issue17_gpt_full_cpu_pidfd_compat3/`

| Suite | 实际通过 | FAIL/ERROR/SKIP |
|---|---:|---|
| inference | 182 | 0/0/0 |
| phase_a_regression | 278 | 0/0/0 |
| phase_b_runtime | 234 | 0/0/0 |
| media_replans | 89 | 0/0/0 |
| streaming | 86 | 0/0/0 |
| **合计** | **869** | **0/0/0** |

- 原始`gate.json` status=`PASS`、Shell exit=`0`、`source_unchanged=true`、Ruff/format/导入来源通过。
- 2026-11-04 15:35:46 UTC 完成（北京时间 23:35:46）。
- `gate.json` SHA256 `36226c83b93b7bdcdcf1abb8a9e415acee3102caf1a26fdf47f4284e67d3f919`
- `junit.xml` SHA256 `12f05160965782b6e85b31a418d9155e7ec1de3c19d88e5e7d905b7ddc3f45af`
- Root Git状态干净；Child Git状态干净；最终一致性已复核。完整五组原始日志、JUnit和源文件SHA表保留在服务器该目录。**这是GPT实际执行结果，而非引用Codex作者869项证据。**
- CPU Gate仍使用真实OS子进程/Store/Session等小规模测试，以及合成物理和模型替身。64Slot/900Core CPU证据不证明真实H100的64 Sim吞吐。

### 2.1 必须保留的环境异常与处置

服务器已有 Python3.13.11/Torch2.10.0+cu128/Ruff0.12.7环境，在禁CUDA运行时`os.pidfd_open`和`signal.pidfd_send_signal`均不存在：
- **原始未补环境的完整Gate**：inference182 PASS；PhaseA278 PASS；PhaseB `62PASS/1FAIL`；失败为`safe pidfd media cleanup is unavailable`，不是Kernel无pidfd。原始日志保留在 `issue17_gpt_full_cpu/`。
- GPT建立**仅该独立测试使用**的虚拟环境 `python313_pidfd_compat`，通过 `site-packages/*.pth`导入测试专用兼容层，把缺失的CPython接口映射至Linux x86-64原生 `pidfd_open` syscall434、`pidfd_send_signal` syscall424。先独立实际spawn/信号发送及旧失败用例1/1验证。**不改变项目生产代码或测试断言、没有弱化进程身份校验或跳过该测试。**
- 兼容层 SHA256 `9b4e5c165bc41217a9b34ef318f9e6afb913d06973482eeb6759701af1dd5991`。独立venv只读链接原Torch依赖与`ruff`二进制，并修正NVIDIA包动态库路径。两次环境调整的失败历史保留：第1次兼容环境缺`bin/ruff`导致静态阶段FAIL，第2次缺NVIDIA库定位导致import阶段ERROR，最终第3次完整869PASS。
- **严格判定**：`CPU_GATE_PASS_WITH_EXPLICIT_TEST_ENV_COMPAT`，不是“原服务器原生Python3.13环境869 PASS”。生产RoboCasa运行环境的pidfd兼容问题应在硬件Canary前单独核对，不把本测试shim当成生产修复。

## 3. R04 Action Compile CPU定向独立执行

在另一隔离工作树执行原作者51项测试：`cosmos3_vfm_network.py`/Action projector/compile等相关测试；明确排除GPU/L1共8项。无外部shim的服务器 Python3.13.11/Torch2.10.0+cu128环境，`CUDA_VISIBLE_DEVICES=''`。

- `51 passed, 8 deselected`，`0 failed/error/skipped`；Shell exit0、源码SHA一致、Root/Child干净。测试时间42.29秒。
- 独立证据目录：`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/r04_gpt_cpu_51/`
- 原始 `junit.xml` SHA256 `9ccfb65fd4da1e22efddde78813a9b6fd20a4e841723523a24a8c3019cd48b0f`
- 通过的是CPU编译边界和相关回归，**不证明**H100 BF16 grouped_mm、CUDA graphs、显存/吞吐、长期真实Action Server B1–8稳定性；R04原648有效EP不能使用新代码直接普通Resume。

## 4. 已具备/未具备的下一步条件

**已完成**：Issue17 GPT独立CPU869/869（显式测试环境兼容）以及R04 Action compile GPT独立CPU51/51；Codex原作者Gate分别已PASS，前序GPT源码审核分别`APPROVE_CODE`。两条代码线的Formal Pair仍然**互不相同**，不能各取一个Child SHA随意混用。

**仍需单独授权/执行**：
1. Issue17真正GPU+EGL/64 OS Sim/Native Batch B8/B16性能与内存/Session/Resume Canary。
2. R04编译修复匹配真实checkpoint/config的GPU编译、数值等价与B1–8交替稳定性Canary。
3. 两条代码线与G2都获相应审核后，在当时最新V3形成**新的集成Formal Root+Child/Gitlink**并验证，不能自动合并旧候选、覆盖原R04源码或跳过Manifest同一性。
4. **M/B Resume一致性仍严格保留**；旧R04受冻结源/Manifest约束，不以本CPU结果自动恢复剩余252EP。

本报告仅审计执行事实和产物引用，不改写既有source/code verdict、权重或生产运行数据。
