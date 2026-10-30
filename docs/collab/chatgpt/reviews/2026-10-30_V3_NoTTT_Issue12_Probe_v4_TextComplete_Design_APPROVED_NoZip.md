# Issue #12 — Probe v4 完整文本审核：APPROVE_SCRIPT_DESIGN（不再要求ZIP）

- 日期：2026-10-30；审核对象为 **DS 仓库外** `cpu_diagnostic/issue12_worker_coldstart_probe.py` v4。此结论**覆盖**本日早前因缺少原始 ZIP 而给出的 `REQUEST_CHANGES (EVIDENCE_ONLY)`；**无需重新开发 v5 或上传原始 ZIP**。
- **最终脚本/诊断设计 Verdict：`APPROVE_SCRIPT_DESIGN`**。以 Owner 已经完整粘贴的 v4 源码、Diff、启动指令、测试摘要作为充分的设计与静态审阅依据，不再强制二次传输原件。**`REAL_DATA_CPU_EXECUTION=PENDING_OWNER_AUTHORIZATION`，本次仅审代码设计，不是运行授权。**
- 冻结生产 Formal Root `e0fe911dfb9fd34957234828195cf051713f6c3d`，Child/Gitlink `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7`：完全未变。先前 Code `APPROVE_CODE` + Issue#11 DS独立CPU301 / raw6/6 PASS 仍有效；Issue#12真实 GPU：Arm A 20/20 commits，Arm B DCP load但首包 DataLoader120s Timeout / 0 commits，稳态 A/B `PERFORMANCE=INCONCLUSIVE`，均未因本条改变。
- 用户已提交 `粘贴的文本 (1)(20261030-112718).txt`，内容包括 **v4完整约528行的脚本表示、v3→v4 Diff、执行方案与SHA说明**。DS报告脚本 SHA256 `9f1996b01d76f33ad8b15d19e47c15ef46471781f35599d591b55b8e5f016c67`、Ruff/py_compile通过与不涉及真实数据的Smoke。大粘贴形式会将 `__future__` 等字符串变为 Markdown 的 `**future**`，无法从该转码文件复原精确字节并独立校验SHA；记录 `SOURCE_SHA=DS_REPORTED_NOT_INDEPENDENTLY_VERIFIED`，**该限制不再阻断设计Gate，也不推断DS原.py有语法错误**。

## v4设计验收已满足（复用前序v1–v4审阅，不重复大范围Gate）

1. `torch`模块级可用、CPU/CUDA隔离护栏；仅源/缓存/index的CPU数据通路，禁用torchrun/GPU模型/optimizer/DCP修改。
2. 真实单Worker使用公开`loader.begin()/materialize()`，每次只取一个真实Segment，partial Window不调用不合法的`finish()`；异常收尾采用`finally:loader.close()`，对自己创建的Worker额外保护。
3. `loader_construct_s / worker_startup_s / first_materialize_s / first_packet_total_s`明确区分。原PyTorch DataLoader的`timeout=120s`仅作用于取数，不包括全部初始化墙钟。
4. Parent ScopeA真实数据处理的in-process构造分阶段、ScopeB真实spawn单Worker首包，二者测量语义区别明确；高成本阶段`START/DONE` flush、`PROGRESS.current`、SIGTERM下部分证据记录；失败时可从最后一个开始阶段定位**父进程所观察的阶段**。
5. `timeout -k 120 1800`与stdout/stderr独立日志输出，避免近满`/mnt/data1`作为实验产物盘；DS现场报告`/mnt/data`可用空间约238GiB。实际安全清理和源环境依旧是执行时需遵守的约束，不会保证所有子孙进程永不残留。
6. 把`initial_frontier()`标为代表性初始rank0 request、非iter9600恢复真实Request；ScopeB明确为ScopeA之后预热条件；不能据此认定原正式4rank×8worker Timeout根因、DCP严格state parity或实机GPU性能收益。

## 证据与执行边界

- `APPROVE_SCRIPT_DESIGN`足以停止要求更多脚本审核轮次，**不需要原ZIP/原始.py再传输**；DS报告的原SHA、静态结果保留为`REPORTED`，没有伪称GPT字节/真实数据运行验证。
- 当Owner明确批准**一次**有界CPU-only真实数据实验后，DS可按已提交的v4约束在其**仓库外临时目录**执行；需要保留首包耗时、Stage START/DONE、超时及owned-worker收尾证据。执行前只需确认数据/输出路径可用、GPU不可见、实际shell命令确实包含外部timeout、不会影响运行中的正式NoTTT Job。**不再额外设立脚本 Gate，不新增v5。**
- 仍不授权：本次自动启动CPU-only实验、4GPU A/B重跑、提高正式Loader timeout、修改正式生产代码（只可Codex修改）、停止/Resume正式Job、写原DCP/Checkpoint、GPU/仿真任何实验。
