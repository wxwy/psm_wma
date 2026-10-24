# Fixture-only MEDIUM-F01 作者整改交接

Formal Root `fe9d537b4a5f82c8ea72a4f8ce182fdcefac6790` / Child-Gitlink `813a550dab5d6b5b5e3be90d38bb97527956b4dc`。基线 `976f77e7529a11dffef48ea0388ed6454a0b1209`；GPT dfb8a121/813a550d REQUEST_CHANGES 的 MEDIUM-F01。生产scripts/configs/third_party/Child树与原已批准 `6151e0712f28ace5d92258a8feb31fa8f1ee81c1` 逐树完全相同；未改生产算法/预算/媒体审计、G1、历史结果或真实模型/DCP。

## 最小整改

仍只改watchdog和其控制测试。超时时先以PID+start ticks核对归属，SIGSTOP root及其递归后代（包括独立session），阻止正常取证复制期间继续fork。`_retain`处于try/finally中，成功/失败都进入bounded cleanup；取证后重新发现并冻结，不能仅用旧rows。仅向仍匹配start ticks的owned PID发送SIGKILL，根Popen.wait回收；不使用全系统kill或waitpid(-1)。

清理阶段临时启用Linux CHILD_SUBREAPER，把被杀root的后代接管回来，并仅waitpid已确认的owned PID，避免留下活进程或zombie。原subreaper标志在finally恢复；foreign control不在known owner集合，不被杀/回收。Linux/proc/prctl是本控制测试运行前提，不能把权限错误跳过为PASS。清理总预算10秒，冻结有界；无法清理会留remaining/errors并保持非成功。

快照异常保留原hard_limit/no_cpu_or_file_progress和EVIDENCE_SNAPSHOT_FAILED，不转PASS。主watchdog.json写失败则尝试cleanup.json；整个证据卷不可写时通过stderr和异常state继续报告，不能保证在已满卷写出文件。证据目录分配/观察I/O也有同一异常清理保护；KeyboardInterrupt/SystemExit在清理后继续传播，不伪装成普通测试成功或吞掉用户中断。600/900秒总预算、180秒stall、120秒真实Task超时及所有FFmpeg/C01/Local/Resume断言不变。

## 确定性负例与结果

- 原watchdog跑两项新负例：2failed。其一强制watchdog.json写OSError，旧清理未运行；另一项在retain期间触发root创建新的不同session/PGID child，旧rows漏杀。测试finally仅回收自己的受控进程。
- 新负例会故意SIGCONT取证前已冻结root，握手确认新child出生，再断言新PID/PGID消失、root回收、foreign仍活、reason/错误可读。即使测试hook重新打开fork窗口，取证后rediscovery仍有效。
- 最终8项控制PASS（原4+上述2+目录分配失败+中断传播），0skip；新children不只是Z状态，最终拥有PID列表为空。原始snapshot失败fallback cleanup.json、PID/PPID/PGID/start证据和foreign存活见证已保存。
- 最终冻结五组：**172 passed, 72 subtests passed in 1661.25s (0:27:41)**，failure/error/skip=0。JUnit声明244，实际172个testcase，成功subtests不单列XML。16Python Ruff0.12.7check/format/compile/源码哈希绑定通过。此前中止的组合及一次重复路径启动命令单独归档，均不计PASS；final command.json/run_final.py保证只有5个唯一测试文件。

Evidence `docs/collab/codex/evidence/2026-10-24_fixture_MEDIUM_F01_author_cpu/`：完整原始red/green/final日志JUnit、实际场景tar快照及scenario_index、命令/哈希/Diff/远端回验。中间green首次发现child已杀但Z未reap，随后加强子进程回收和PID/PGID不存在断言；迭代记录不改写为最终结果。

请求GPT只对新Pair的MEDIUM-F01做fresh incremental review，再DS clean detached精确Pair独立五组CPU；DS Gate仍RED，作者自测不自关闭。旧生产Code APPROVE不重审，不启动真实GPU/ActionServer/Kitchen/DCP或训练，不更新G1和当前评测，不重跑/改写iter12000既有20集。Codex提交后STOP。
