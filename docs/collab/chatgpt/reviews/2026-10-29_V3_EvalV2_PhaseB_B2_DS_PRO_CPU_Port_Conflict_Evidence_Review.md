# PSM-WMA V3 EvalV2 Phase B 第二批 — DS_PRO 独立 CPU 首轮 Evidence Review

- 日期：2026-10-29
- **Formal Code Pair 未变**：Root `323f0b2a3d4aa3b40d9d8f2eb0b94c9251299728` / Child+Gitlink `774c2edb93ec5a6ba85ba1124757064d7cc779a5`。
- 前序第二批 Code Gate `APPROVE_CODE` 保持有效；本轮**只审核 DS 新的 CPU 运行报告和相关实际测试源码**，不是新的 Code Gate / 设计 Gate。
- **正式 DS Evidence Gate verdict：`REQUEST_CHANGES`（Evidence-only；未关闭）。底层执行记录为 `FAIL`，根因分类 `BLOCKED_ENVIRONMENT`，并暴露一个测试夹具端口检测口径不一致。**
- 不认定为 Phase B 生产代码 Bug、不要求任何生产源码修改。

## 1. DS_PRO 现场报告与可见证据边界

DS_PRO 报告使用独立干净 Root/Child worktree，精确 Root/Child/Gitlink 一致；原本的统一 Gate 入口、Ruff 0.12.7、CPU-only override 均保持。原始 Evidence 留在 DS 服务器 `/tmp/ds_pro_v3_evalv2_b2_20261029/evidence/`。GPT 当前未读取其服务器 JUnit 原始字节、`ss -ltnp` 输出或进程快照，以下具体运行数字来自 DS_PRO 现场执行报告；**不冒称 GPT 已独立复跑或读取 raw artifacts**。

| 组别 | DS 报告完成情况 |
| --- | --- |
| inference | 145 pass / 0 fail/error/skip |
| phase_a_regression | 255 pass / 0 fail/error/skip |
| phase_b_runtime | 20 pass / 1 fail；`-x` 在第 21 项停止，剩余 3 项未运行 |
| 总计 | **420 pass / 1 fail / 0 error / 0 skip；期望 424，但只执行 421** |

统一 Gate shell exit=1，`gate.json.status=FAIL`；不能用前 400 PASS、作者 424 PASS 或源 SHA 不变来替代独立 424 PASS。由于 Gate 在 Phase B runtime 首错退出，`gate.json` 没有最终 `source_unchanged=true`；DS 的 before 指纹与干净 Git worktree 仅为辅助佐证，不替代最终 Gate 字段。

**需纠正一项覆盖表述**：最终 Phase B runtime 的标准 24 项收集顺序中，前 17 项为 config tests、接着 3 项为 gate tests；第 21 项才是首个 `test_real_OS_multisim_native_B2_delivery_D5_task_reuse_and_resume[1-2-2]`。因此当前 20 PASS **没有完成任何正式 OS 多 Sim 集成测试**。前 145 推理用例包含 B2 事务与模拟边界测试，但不能据 Phase B runtime 已过 20 项声称独立真实 OS overlap、Server death cleanup、完整 D5 Resume 已通过。目录名 `test_real_OS_multisim_native_B0` 本身也不是 PASS 证明。

## 2. E1 — 测试夹具端口探测不一致（MEDIUM，Evidence/test-only）

- **直接实际源码**：Formal Root `tools/v3/eval_v2_batch_tests/runtime_test.py:29–45` 中 `free_ports(count)` 只在 `127.0.0.1` 上 `bind` 探测随机连续端口。
- **生产代码**：Formal Root `scripts/eval_robocasa_18task_queue.py:74–89` 中 `require_free_ports` 故意以 `0.0.0.0` 绑定并监听，严格模拟真实 Action Server 端口占用检查；`scripts/robocasa_eval_v2/runtime.py:734–742` 在启动 Server 之前调用。
- **DS 环境见证（尚未直接读取原始 `ss`）**：已有训练 PID 1202531 使用 `127.0.1.1:44783`；测试夹具在 `127.0.0.1:44783` 上认为空闲，正式 Runtime 绑定 `0.0.0.0:44783` 时得到 `[Errno 98] Address already in use`。
- **根因**：地址范围不同，`free_ports` 的“空闲”判定弱于生产 Runtime 的真实绑定约束；既有共享服务器监听使本轮触发。**生产侧拒绝冲突端口是正确行为**，不应降低生产保护或修改 Server。
- **冻结验收目标未达到**：统一 Gate shell exit0、`status=PASS`、424 测试零 fail/error/skip、精确 Pair 与 sources unchanged、真实 OS overlap/batch/cleanup/Resume 证据。

此项是测试夹具的可达 false-negative 环境问题，不是 Native Batch、Local-TTT 事务或科学 SR 错误。它在多进程 OS 试验开始前阻断了本次验收；不得据此推断其它 3 项 OS 测试逻辑失败。

## 3. 最小处置：同 Formal Pair 单次重试，先不改代码

本轮**不要求 Codex 额外生产改动、第三批架构、时钟域专题、模型/训练变更或等待生产 Job 退出**。现有 `free_ports` 使用随机 `port=0`，下一次运行并不绑定旧的固定 44783；可在 Owner **明确授权后**使用同一干净精确 Pair，在全新的外部 Evidence 目录**完整重跑统一 Gate 一次**。旧失败原件原样保留。不要杀进程、改监听、清理旧 Evidence、`reset --hard` 或绕过端口保护。

示意命令（使用 DS 同一已核验 CPU Python 环境，且新 Evidence 路径必须不存在）：

```bash
ROOT_SHA=323f0b2a3d4aa3b40d9d8f2eb0b94c9251299728
CHILD_SHA=774c2edb93ec5a6ba85ba1124757064d7cc779a5
WT=/tmp/ds_pro_v3_evalv2_b2_20261029/root
EVID=/tmp/ds_pro_v3_evalv2_b2_20261029/evidence_retry1
PY=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin/python
test ! -e "$EVID" || { echo "Evidence directory already exists"; exit 1; }
cd "$WT" && set -o pipefail
"$PY" tools/v3/run_eval_v2_batch_b2_cpu_gate.py \
  --root-worktree "$WT" \
  --expected-root "$ROOT_SHA" \
  --expected-child "$CHILD_SHA" \
  --evidence-dir "$EVID" \
  2>&1 | tee "$EVID.console.log"
```

接受标准**不变**：单次完整 424 PASS、0 failures/errors/skips、shell exit0、`gate.json.status=PASS`、`source_unchanged=true`、精确身份一致，且 OS 多 Sim 重叠/B2、成员对应/Session clean、Server death 与 Resume 均有原始见证。报告只需原始文件路径、关键值与 SHA；DS 不得将 retry1 结果覆盖之前的 FAIL。若 retry1 仍 FAIL，原样报告并停止，不自行多次重试。

若该误判在独立重跑中再次出现，才授权 Codex 在隔离候选进行**仅测试夹具**的最小 `free_ports` bind 地址 `127.0.0.1`→`0.0.0.0` 对齐，辅以针对不同回环监听地址的确定性 CPU 负例；不修改任何生产端口保护。该 test-only 变更形成新 Formal Pair 后仅做极窄的新 Pair 增量审核，并由 DS 继续统一 CPU Gate。**现在不先行扩大整改。**

## 4. Gate / 权限

- **Phase B 第二批 `APPROVE_CODE`：维持，不重审、不撤销。**
- **DS_PRO 独立 CPU Evidence Gate：`REQUEST_CHANGES`（Evidence-only／未关闭；环境端口冲突造成本次 FAIL）。**
- **仍未批准** V3/Child 正式生产源码合并、真实 GPU/Cosmos/RoboCasa Canary、DCP/训练/900集、现有训练工作树或 Checkpoint 修改。
- 后续仅：Owner 授权 DS 单次 exact-pair retry → GPT 核对最终 DS Evidence → Owner 决定受控合并／1GPU M2 B2 真实 Canary → 900集。
- 本 Review 为报告级校验、源码定位与下一步最小处置；本轮写入 V3 仅为 docs bookkeeping，**不构成新的 Formal Implementation Root**。

## 5. 源码与前序 Gate

- [实际测试随机端口选择](https://github.com/wxwy/psm_wma/blob/323f0b2a3d4aa3b40d9d8f2eb0b94c9251299728/tools/v3/eval_v2_batch_tests/runtime_test.py#L29)
- [生产正确拒绝端口占用](https://github.com/wxwy/psm_wma/blob/323f0b2a3d4aa3b40d9d8f2eb0b94c9251299728/scripts/eval_robocasa_18task_queue.py#L74)
- [Runner 生产预检调用点](https://github.com/wxwy/psm_wma/blob/323f0b2a3d4aa3b40d9d8f2eb0b94c9251299728/scripts/robocasa_eval_v2/runtime.py#L734)
- [已批准正式第二批 Code Gate](https://github.com/wxwy/psm_wma/blob/0f655489cd04062d72ecdd3cf6bb6baee5888796/docs/collab/chatgpt/reviews/2026-10-29_V3_EvalV2_PhaseB_Native_Batch_B2_323f0b2a_774c2edb_Incremental_Code_Gate_APPROVE_CODE.md)
