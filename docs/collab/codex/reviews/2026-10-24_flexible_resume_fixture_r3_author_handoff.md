# DS Retry1 fixture-only r3 作者交接

Formal test-only Root `dfb8a12140be7bf34584504c47df9042229f5bfb`；Child/Gitlink `813a550dab5d6b5b5e3be90d38bb97527956b4dc`未变；基线 `22b0abcbf08316d576ef2d56c55af6151a6060e5`。`scripts`、`configs`、`third_party`、Child树与已批准生产Root `6151e0712f28ace5d92258a8feb31fa8f1ee81c1`逐树相同。既有GPT Code APPROVE保持其原Pair含义；新fixture仍需fresh incremental review，DS Evidence RED不自闭合。

## 范围和预算

只修改Queue测试，新增stdlib专用watchdog helper。真实FFmpeg解码、C01/Local清理、SR/COMPLETE、复用数、不启动新Server等原断言保持。普通/双阶段总硬限600s，task_timeout900s，独立无媒体CPU/核心文件推进180s；健康Task墙钟120s，late prerequisite300s。根据作者原场景最高约158s、DS报告整体约1.93倍的时间范围留有限余量，不声称严格证明DS全是环境问题，也不保证任意拥塞下绿色。

监测使用有来源的PID/PPID/PGID/start ticks；核心JSON/JSONL/MP4/PNG变化与媒体Python/FFmpeg CPU ticks可刷新idle。排除UI/server/eval心跳及父线程CPU；仅Runnable不能刷新idle。CPU活动本身不证明逐帧解码，忙循环仍在独立硬限失败。4项控制覆盖持续推进超过旧等待预算、无推进停滞、CPU忙循环硬限、心跳不算媒体进展，并验证无关进程存活。

终止前保存console、进程样本、最终阶段相关文件、实际小媒体、source/invocation索引，之后仅杀观察归属且start ticks仍相符的PID。独立目录由PSM_WMA_FIXTURE_EVIDENCE_DIR指定，缺省/tmp/psm-wma-queue-fixture-evidence。单文件32MiB、总128MiB保留上界；在观察大小截取，后续并发追加不在snapshot范围，跳过/缩短显式记录。文件原件不改。正常和非零场景同样保存。归档focused/controls/full_scenarios含实际快照，不只作者摘要。

任务超时将全局fixtureTask budget从5改120，挂死模拟器及忽略SIGTERM的子进程持续3600s；仍使用原生supervise/真实时钟/OwnedProcess，不篡改deadline算法。定向记录120.336s触发task wall timeout，SIGTERM后SIGKILL，恰1失败Task、3健康Task、15闭合Episode、PARTIAL/sr=null。断言另增加真实超时原因、elapsed>=119.5、completed_tasks=3。

## 证据和统计

最终冻结五组：**168 passed, 72 subtests passed in 1399.81s (0:23:19)**，failure/error/skip=0。JUnit声明240，实际168个testcase，成功subtests不单列元素。16Python Ruff0.12.7check/format/compile及冻结哈希通过，源码hash绑定exact commit。迭代期定向（最终心跳排除策略冻结前）7PASS+15subtests，最后policy控制4PASS；不相加为另一套全量通过。

受控RED1FAIL演示固定0.1秒wait拒绝确实推进的0.6秒producer；GREEN控制同producer完成且原wait确实TimeoutExpired。它不是DS90秒媒体失败的本机复现。真实媒体及业务场景由定向和最终五组执行证明。DS服务器原日志未挂载，6失败/9失败仅引用已有GPT/DS报告。早期作者控制夹具2FAIL/1PASS是缺少异常类import的编写错误，已修复，原日志独立保留，不能冒充DS红测。

Evidence `docs/collab/codex/evidence/2026-10-24_flexible_resume_fixture_r3_author_cpu/` 包括完整命令、红/绿/最终日志JUnit、实际场景tar快照、scenario_index、Diff、source及artifact SHA、远端回验。旧Evidence未改。请求GPT仅复审fixture-only新Pair，再DS clean detached工作树独立完整五组；使用已有CPU环境、外部缓存/evidence，失败保留原件不改源码。无GPU/真实模型/Kitchen/DCP/训练，不更新G1/当前评测或iter12000历史20集。Codex提交后STOP。
