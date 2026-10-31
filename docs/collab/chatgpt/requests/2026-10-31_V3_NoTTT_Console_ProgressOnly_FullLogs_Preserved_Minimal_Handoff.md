# No-TTT 控制台只显示 Progress；完整日志不丢失（最小实施指令）

2026-10-31。Owner需求：**No-TTT training开始后，工作界面正常运行时只显示 `[CorrectedV3][progress]`，但所有详细训练、Loader、Rank、warning/error日志仍完整存盘，类似Local-TTT的直观进度显示。** 此为**日志呈现**调整，不是新模型/Loader/数据处理/Performance Gate。

## 源码核对

- Frozen NoTTT candidate Formal Root `fd9021b0908b4b2763b3d02508b1f34df377dc97` / Child `224c5f3c0bd6911bb49cb6bb0895ba7da53ff822`。`examples/psm_wma_robocasa_corrected_phase5.py:1368-1390` 的rank0 `TelemetryJournal`绑定Observer且 `human_progress=True`。
- `examples/psm_wma_robocasa_formal_monitor.py:72-127`：`TelemetryJournal.__call__`优先将 `[CorrectedV3][train]`写入 `monitor/train_rank0.jsonl`，所有传入的observer行追加 `monitor/rank0.log`，而训练JSON不会重复回显到console；`[CorrectedV3][progress]`自然仍回显。
- `cosmos_framework/trainer/matched_no_ttt.py:349-355`：NoTTT异步Loader的 `[NoTTT][cpu_loader]`每个step直接 `print()`；其它各rank/Cosmos框架日志也会进入torchrun stdout/stderr。仅调整TelemetryJournal无法做到终端完全只有progress，应该**在最外层训练启动命令的stdout/stderr作终端分流**，而不是删除训练器日志。

## 最小实现：现有/下一次DS仓库外 launcher 直接使用（无需改生产源码）

在实际launch脚本外层替换原来的单纯 `> launch.log 2>&1` 或 `tee`。**注意不能叠两个tee导致重复写盘**。真实命令与env按当前Owner批准的runbook保持，以下 `$RUN_SCRIPT`/`$STOP_ITER`/`$LOG_DIR` 均从S0实际路径取得，示例供DS在**下一次尚未启动的** NoTTT job使用，绝不对当前GPU A/B过程中进程插管：

```bash
set -uo pipefail
mkdir -p "$LOG_DIR"
FULL_LOG="$LOG_DIR/launch.full.log"  # 本次启动的唯一、非正式job覆盖日志
printf 'Full log: %s\n' "$FULL_LOG"
set +e
PYTHONUNBUFFERED=1 bash "$RUN_SCRIPT" resume "$STOP_ITER" 2>&1 \
  | tee -a "$FULL_LOG" \
  | awk 'index($0, "[CorrectedV3][progress]") { print; fflush() }'
rc=("${PIPESTATUS[@]}")
set -e
# exit status不得被awk/tee成功掩盖。
if (( rc[0] != 0 || rc[1] != 0 || rc[2] != 0 )); then
  printf 'FAILED: train=%s tee=%s filter=%s; complete log=%s\n' "${rc[0]}" "${rc[1]}" "${rc[2]}" "$FULL_LOG" >&2
  tail -n 80 "$FULL_LOG" >&2
  exit 1
fi
```

正常运行时Console**只显示Rank0 progress**。Launch full log保存**所有torchrun stdout/stderr**（包括warnings/loader/ranks/traceback，不能提前grep后再写盘）；Machine metrics依然在 `monitor/train_rank0.jsonl`、observer raw在 `monitor/rank0.log`。必须保持 stderr 错误完整落盘，异常退出可在Console显示末尾错误，但正常时不刷屏。

**已用最小模拟命令静态验证管线**：输入`initializing`、`[NoTTT][cpu_loader]...`、`[CorrectedV3][progress]...`、stderr与退出码5；屏幕仅显示progress，full log包含四类行，`PIPESTATUS[0]=5`未被吞掉。尚未在真实training时切换/运行该wrapper。

## 若希望以后成为仓库标准入口（Codex负责，仅后续单独小Patch）

- **Codex是仓库内shell/Python实现唯一作者**，可在本轮GPU matched A/B和其源码证据冻结后，为4GPU NoTTT外部启动入口添加一个**显式可选**的progress-only_console分流，不改其核心`exec torchrun`配置或消除Exception；不建议修改`TelemetryJournal`本体或复写所有Python print。
- 最小改动优先只限已有external DS launcher；如果纳入仓库则只改一个启动脚本/新增一个极短的外部output wrapper，提供 `PIPESTATUS`、全量log完整性、只console progress、正常/失败/无progress/管线中断、SIGINT退出这些**shell-level合成验证**即可。不得重跑旧301CPU/58或GPU来验收终端过滤。
- **本任务不授权修改正在运行的正式30k NoTTT、刚安排的C12200 A20+B20独占matched实验配置、其正式checkpoint、训练源码或现有Formal Pair**；不能因为用户要console简洁而影响精确GPU性能A/B公平性。

## 已启动进程立即观察（不会改变其工作终端）

如已经有完整`launch.log`正在持续写入，用户可另开一个控制台：
```bash
tail -n 0 -F "$FULL_LOG" | awk 'index($0, "[CorrectedV3][progress]") { print; fflush() }'
```

以上命令只读，不影响任务，也不改变原启动终端输出。

**Gate：只评估人机可读console与full log分流，不扩大训练技术工作。**