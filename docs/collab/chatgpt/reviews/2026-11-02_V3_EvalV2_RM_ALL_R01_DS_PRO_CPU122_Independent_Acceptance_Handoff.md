# GPT → DS_PRO 执行交接 — RM-ALL-R01 独立 CPU122 Gate

**状态：待 DS_PRO 独立执行；此文件是可执行验收指令，不是测试已完成报告。**  
**本次执行范围：仅独立 CPU Gate；不得自行启动 GPU/正式900EP/合并 V3。**

## A. 审核对象与边界

- 审核通过的严格 Formal Pair（不是候选 HEAD）：
  - Root：`e7ce99d7a0bbb7a81ea7afcee7253548687dc223`
  - Child/Gitlink：`c93f2abf4fb27d36176ff8db094379a853cec796`
  - 两仓候选分支：`v3-eval-v2-replan-ack-r01-20261102`
- GPT 代码审核：`APPROVE_CODE`、`RM-ALL-R01 CLOSED`，详见 `docs/collab/chatgpt/reviews/2026-11-02_V3_EvalV2_RM_ALL_R01_e7ce99d7_c93f2abf_Incremental_Code_Gate_APPROVE_CODE.md`。
- 本轮只验证 Media ACK History 修复及其相关回归。Codex 已有 **122 author PASS** 不能算 DS 独立 PASS，也不能把历史379再次计数。
- **只用新建的独立、干净 detached Root/Child checkout 和新的证据目录**。不 checkout、reset、merge、修改正在运行的训练/评测工作树，不改 Root V3/官方 Child，不碰任何旧 `out2`、No-TTT、历史 H2/H3、checkpoint/DCP、既有媒体/日志，也不查询/管理别人的 GPU 任务。GPU0–3 不触碰；**本 CPU 测试不得启动 GPU**。
- 仅可创建、使用、清理本次 DS 测试自己的临时目录/进程；禁止宽泛 `pkill/killall` 或覆盖任何现存 Run/evidence。
- 本交接不要求 DS 对已批准的 `d2041e38/0dd13d3d` 整套媒体设计重新做源码审计、也不要求再跑旧379或旧版RED2。若有新症状，提交证据即可。

## B. CPU 独立验收：明确的两组测试、两个解释器

作者的可复现工具和冻结 test 已在**候选文档 HEAD**的以下路径，**正式 Root commit 并不包含这些随后提交的 Evidence 文档**。从候选文档 checkout（可只读）复制到本次独立证据目录，再在精确 Formal checkout 上运行：

- `docs/collab/codex/evidence/2026-11-02_eval_v2_rm_all_r01_author_cpu/run_cpu.py`
- `docs/collab/codex/evidence/2026-11-02_eval_v2_rm_all_r01_author_cpu/red_validated/frozen_test.py`
- 原作者四项参照证据：同目录 `final/green/invocation.json`、`final/regression/invocation.json`、各自 JUnit/gate，以及 `final/static/commands.json`。
- 冻结新测试 SHA256：`2114ca1435316be8ec2f4e13383badc0ebedcfee2da7a44966139fdf7ad53354`；不要编辑 test/source 以适配环境。

**输入变量由 DS 按服务器实际情况填入，下面路径均为占位符，不能原样运行。**

```bash
set -euo pipefail
# 必须是全新的隔离路径，禁止放在out2/历史结果、运行中训练工作树内。
export ROOT=/ABS/INDEPENDENT_CLEAN_ROOT_AT_e7ce99d7
export DOCROOT=/ABS/READONLY_CANDIDATE_DOCS_WITH_AUTHOR_EVIDENCE
export EVID=/ABS/NEW_DS_ONLY_CPU122_EVIDENCE_ROOT
export PY313=/ABS/VERIFIED_PYTHON_3_13/bin/python
export PY312=/ABS/VERIFIED_PYTHON_3_12_CPU_TORCH/bin/python
export FORMAL_ROOT=e7ce99d7a0bbb7a81ea7afcee7253548687dc223
export FORMAL_CHILD=c93f2abf4fb27d36176ff8db094379a853cec796

test ! -e "$EVID" && mkdir -p "$EVID/tools"
test "$(git -C "$ROOT" rev-parse HEAD)" = "$FORMAL_ROOT"
test "$(git -C "$ROOT/cosmos-framework" rev-parse HEAD)" = "$FORMAL_CHILD"
test "$(git -C "$ROOT" rev-parse HEAD:cosmos-framework)" = "$FORMAL_CHILD"
test -z "$(git -C "$ROOT" status --porcelain)"
test -z "$(git -C "$ROOT/cosmos-framework" status --porcelain)"

AUTHOR="$DOCROOT/docs/collab/codex/evidence/2026-11-02_eval_v2_rm_all_r01_author_cpu"
cp "$AUTHOR/run_cpu.py" "$EVID/tools/run_cpu.py"
cp "$AUTHOR/red_validated/frozen_test.py" "$EVID/tools/frozen_test.py"
sha256sum "$EVID/tools/frozen_test.py"
"$PY313" --version
"$PY312" --version

# Group 1：74 media/API tests (含新增16），使用可运行pytest/FFmpeg的 Python3.13
"$PY313" "$EVID/tools/run_cpu.py" \
  --root-worktree "$ROOT" --phase green --output "$EVID/green" \
  --frozen-test "$EVID/tools/frozen_test.py" \
  --expected-root "$FORMAL_ROOT" --expected-child "$FORMAL_CHILD"

# Group 2：48 native Batch/Local/Fast CPU回归，
# 使用本机真正具备CPU Torch和所需依赖的Python3.12
"$PY312" "$EVID/tools/run_cpu.py" \
  --root-worktree "$ROOT" --phase regression --output "$EVID/regression" \
  --frozen-test "$EVID/tools/frozen_test.py" \
  --expected-root "$FORMAL_ROOT" --expected-child "$FORMAL_CHILD"
```

说明：
- `run_cpu.py` 会设置 `CUDA_VISIBLE_DEVICES=""`、`COSMOS_DEVICE=cpu`、offline/cache/OSMesa、独立测试输出和 300s owned-process watchdog；在开始和结束均核对 Root/Child/Gitlink SHA、工作树 clean、源码 SHA、冻结测试是否被修改。
- 作者 Group 1 Python3.13.5（58继承+16新增）；Group 2 Python3.12.14 + CPU Torch2.10.0（48回归）。DS可用服务器兼容解释器，但必须明确报告差异，不得以“Python3.12能启动”替代 Torch/import 真实可用。
- **任何不满足/缺依赖：`BLOCKED_ENV`，保存原始错误，停止；不得擅自在共享训练环境安装/改包、重新生成测试或放宽断言。** 可在经准许的独立 DS 环境准备后复测。

### CPU Gate PASS 定义

必须满足全部：
1. `$EVID/green/junit.xml` 真实 **74 collected / 74 passed / 0 failed/error/skipped**；
2. `$EVID/regression/junit.xml` 真实 **48 collected / 48 passed / 0 failed/error/skipped**；
3. 两份 `gate.json` 均标 `AUTHOR_CLEAN_PAIR_CPU_PASS`（该字段来自冻结复现脚本的标签，**DS 报告仍要写 `DS_INDEPENDENT_PASS`**），带精确 Formal Pair、测试前后零 dirty、冻结 test SHA 原值；
4. Root/Child/Gitlink 一致；无源码/历史结果改写、无 GPU 请求或 GPU 进程。独立静态核查新 Child 生产文件与 Root 新测试的 Ruff check / format --check / 语法（参照作者 `final/static/commands.json`，只读执行），结果 PASS。
5. `MEDIA_INCOMPLETE` 的显式错误/异常用例按预期通过，跨 Replan old Reserve/ACK 与 End202 不回退。**作者旧 RED2 不要求 DS 重跑**，已由 GPT 读取原始证据。

如任何条件不满足，按实际原因返回 `FAIL` 或 `BLOCKED_ENV`，不要写“基本通过”或以作者 JUnit 充数。

## C. DS_PRO 交付模板与停止点

按如下结构提交简明结论并给出新文件的**实际绝对路径**：

- 形式：`DS_PRO — EvalV2 RM-ALL-R01 independent CPU acceptance`；
- Formal Root/Child SHA、gitlink、候选文档 HEAD、独立 checkout 路径、DS 两解释器绝对路径/版本、Ruff版本、执行命令/退出码；
- `CPU74: PASS/FAIL/BLOCKED_ENV`，`CPU48: ...`，`TOTAL 122/122`（只有确实通过才写），静态 PASS/FAIL；
- 附原始 `green/{gate,invocation,junit,pytest}.json/xml/log` 与 `regression/` 对应文件、静态日志、冻结 test SHA/source hashes、测试前后 git clean；发现失败给首个真实栈、file:line、root cause 候选而非臆测。
- 无需再交 old379 整套 Evidence；可引用作者原有证据文件路径但不可当 DS 自己运行结果。
- **CPU 完成就 STOP 并回报 GPT/Owner，不自动启动 GPU 或正式18×50、不合并 V3**。GPU 实体 Canary 必须另行收到 Owner 许可。

## D. 随后真实媒体 Canary（仅建议方案，**未授权执行**）

CPU Gate PASS 后建议 Owner 单独授权 DS 进行**小规模**新的 Fresh Run（例如1个有效RoboCasa Task × 1 EP，必要时2 EP），指定 `save_generated_video: all`、有效的实际 checkpoint、只读数据、独立新输出命名空间，采用已经硬件验证的 **Action Server GPU6 → EGL Simulator GPU4**，Phase B M1/B1；禁止 GPU7 做 EGL Render（历史发生原生SIGABRT）。不探测、查询、影响 GPU4–7 上其他训练；GPU0–3不参与。

该未来 Canary 应明确记录：每次实际 Replan 的 `replan_count == generated_mp4_count == encoder_VIDEO_SAVED_receipts == server_acknowledged_count`；每文件真实完整解码（不仅ffprobe容器）与文件/receipt哈希、全量状态 `COMPLETE`、`media_summary.json`、Core SR 和 `MEDIA_INCOMPLETE` 的独立性、Session/Encoder/feeder清理；另量化每次媒体 decode/encode/inspect/fsync/ACK 耗时及总 EP 墙钟吞吐。若媒体失败，只停止本次新 Run 并保留证据，不更改模型/策略、历史H3、训练或其它进程。

**本节仅计划，不是 GPU 授权。**
