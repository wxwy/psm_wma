# iter4000 HIGH-02：实现作者交接 / 待独立增量验收

日期：2026-10-21（Asia/Shanghai）。这是作者事实记录，不是 GPT verdict，不构成 GPU/仿真执行授权。

| 版本 | 完整 SHA |
| --- | --- |
| 新 Formal Implementation Root | `ca936c8eecd593133b1e6c61ba5691331958c592` |
| Child / Gitlink（未改变） | `2d128ed5a07601cdd424974f99b67832eafeeb41` |
| 基线 / 直接父 Root（含勘误） | `c62fad0ef6c729570ee936522ea4269021164c56` |
| 原被审生产 Root | `1e00a3d978442dbbb2865b08f41535bbd26a4ce7` |
| 新 Queue Blob | `eec2702d5382358e131928db60ce75c93c0c55d5` |
| 原 Queue Blob | `6833b6ab6d17b85f7a840014ca400bc1dd6424ed` |

实现已非强推发布 V3，并保留 `v3-iter4000-server-identity-20261021`。后续证据/文档 HEAD 不代替上述 Formal Root。未覆盖任何历史提交；原审核和勘误原文保留。

## 1. 授权范围与实际变化

依据 `docs/collab/chatgpt/reviews/2026-10-21_V3_iter4000_4task_multiGPU_queue_launch_review.md` 的 ERRATUM 及 Inbox 最新勘误：**只修 HIGH-02；HIGH-01 = RETRACTED / FALSE POSITIVE。** 本轮没有修改 Lock 类型、加锁位置或锁外 publish 关系。

生产代码只有 `scripts/eval_robocasa_18task_queue.py`：

- `require_free_ports`（:70）在输出身份领取/启动模型前检查全部所需 IPv4 端口，任一占用则整个启动拒绝；每 Worker Popen 前再次检查。先检查全部，避免第二张卡端口被占时第一张卡先加载模型。
- `validate_server_info`（:83）校验 canonical absolute checkpoint/config path、raw15、state=True、Local enabled/required/action_dim15、action_chunk_size16、max_action_dim64、fps20、num_steps/guidance。采样 seed 明确仍为原 Server 默认0；Queue `--seed` 是环境主种子，二者不混同，manifest补充 policy_seed/raw/max dim记录。
- `/info` 直接走 loopback，忽略环境 HTTP proxy。`wait_server`（:144）Ready 前后检查本次进程存活；配置/协议错配立即失败，不等待/接受其它服务。
- `require_owned_listener`（:115）读取 Linux 同用户 `/proc/<Popen pid>/fd` 与 `net/tcp`，要求该进程持有所请求端口的 IPv4 LISTEN socket。这样即使旧服务在端口预检后抢占、且返回完全相同的checkpoint/config，仍不能冒充本次实例。Child现有 `ThreadingHTTPServer` 在Popen主进程中服务，无需修改Child或添加接口。
- Ready 后再次比较 Config SHA256 与本轮 frozen evaluation identity，拒绝启动期间同路径内容变化；只写验证通过的 `server_info.json` 与PID/port `server_process.json`。
- Popen/Ready异常进入原 Worker 错误路径；summary保留worker_errors，即使另一Worker已完成全部Task，仍标INCOMPLETE、完整sr=None并返回非零。只清理本次启动的Popen，外来端口服务不被终止。任务循环也检查Server异常退出。

新增定向测试 `tools/v3/eval_robocasa_queue_identity_test.py`，其余源码不变。Formal提交另外仅更新SESSION/TODO事实记录。

`scope_proof.json` 机械对照证明：discovery/atomic-write/task-result函数AST、result_lock赋值、原server/simulator command列表AST均与基线一致；修改前后均无锁内publish调用。`scripts/v3_evaluation_identity.py` 字节不变，Child洁净且Gitlink不变。未修改Child/训练/Local算法/DCP/动作解码，也未增加新的orchestrator wrapper。

## 2. 作者 CPU Evidence

目录：`docs/collab/codex/evidence/2026-10-21_V3_iter4000_HIGH02_author_cpu/`。Python3.12.14、pytest9.0.2、Ruff0.12.7。

| 检查 | 实测 |
| --- | --- |
| 新定向测试 + 既有Identity/Screening回归 | **28 passed**：13个新测试方法 +15个既有回归case；**41 subtests**，55个无关项deselected；0 fail/error/skip，24.006s |
| JUnit | 69 bookkeeping cases =28+41，不是69个独立方法 |
| 新/改两文件 Ruff check、format --check | PASS，使用Child `.ruff.toml`、Ruff0.12.7 |
| 语法、diff、范围对比 | PASS |

完整命令/cwd/env/RC/source SHA在 `gate.json`；原始输出和XML在 `pytest.log` / `pytest.xml`；`witnesses.json`提取12个Queue集成场景，`implementation.patch`是精确生产+测试diff，`manifest.json`绑定此Pair及产物哈希。

覆盖：真实stdlib HTTP子进程与Linux PID/socket检查、真实临时Git Root/Child身份；1/2/4 Worker分别完成相同四Task×5=20条合成结果；非首端口冲突在输出目录领取前停止；错checkpoint/config/mode零模拟器调用；Config内容中途变化拒绝；同身份旧Server抢占端口拒绝且外来Server仍活着；全部20条结果完成后另Worker启动失败或Server死亡仍非零退出；模拟器边界失败保留错误、无完整SR。没有残留Worker线程，本次拥有的HTTP/占位进程均被回收。

首轮直接unittest为12方法通过；新增Config变化负例后进行上述最终13方法+回归联合运行，不跨运行累加计数。扩展pytest第一次因未设置Child PYTHONPATH而收集失败（RC2），只调整外部测试环境后通过，原始失败保留在 `environment_setup_attempt/`。没有删除/跳过测试来取得GREEN。

**真实边界：**没有导入或加载实际Action Server模型、没有GPU/CUDA/torchrun、没有真实Simulator/DCP/数据读取。HTTP服务、模型metadata/shard、Git仓库、Episode结果、所谓MP4均是临时CPU合成fixture；视频只是非空清单占位，不代表可解码MP4或真实SR。现有模型身份保证仍是metadata hash+shard stats，不宣称模型body全哈希。

## 3. 真实运行前仍须确认

- 本修复需Linux、同用户可读取本次Server的 `/proc/<pid>/fd` 和 `net/tcp`；无法读取时fail-closed，不回退为仅凭 `/info`。这在作者CPU环境已实测，训练服务器权限尚需DS独立确认。
- `/info` 必须报告action_chunk_size16、max_action_dim64及本文精确协议。**没有修改Server命令以强行覆盖模型推断的chunk**；若真实Config被旧recipe解析为32，此次会正确拒绝，不应临时放宽或加未审核override让它通过。具体真实iter4000配置本机不可读，DS先做只读登记；CPU通过不等于真实模型可运行。
- M03：Queue仍是通用按数量发现Task的入口，没有硬编码四Task。实际持久目录必须由DS只读断言集合精确为 `{CloseFridge,TurnOnSinkFaucet,PickPlaceSinkToCounter,NavigateKitchen}`，metadata唯一；本机只验证了合成目录，不能冒称读过服务器四个目录。
- M04：`--resume`只复用同Root/Child/Checkpoint/Config/protocol/tasks身份的完整Task五条结果；任何1–4条partial结果会拒绝，不能Episode级续接或跨namespace拼接。新Root改变evaluation digest，不能复用旧Root结果。本轮不开发Partial Resume，不删除/覆盖旧证据。
- HIGH-02修复不是全部E1 process-timeout/cancellation验收：原simulator整体deadline、线程join和清理上界没有在本批重写；新测试的外部20秒超时保护只保护CPU fixture，不是生产watchdog。不得因此宣称任意native仿真卡死已解决。真实screening仍需独立执行方案和异常停止授权。

## 4. 独立交接 / 停止

CPU-only DS准备及未来**未执行**命令模板：`docs/collab/chatgpt/requests/2026-10-21_DS_PRO_V3_iter4000_HIGH02_CPU_readonly_preparation_ca936c8e.md`。模板显式指定server-python、GPU列表、steps30/guidance1.0、20个Episode和新输出namespace，包含真实四Task只读核对。

请求GPT对新Pair做HIGH-02及相关错误传播的增量审核，不再要求整改已撤销的锁Finding，也不重开F0/F1/G0/G1/旧B1。本次作者CPU不是独立PASS；**GPU release仍未获得授权**，需新Pair验收、实际空闲GPU/显存/端口及Owner单独许可后再谈执行。未操作训练服务器上的任何正在运行作业。
