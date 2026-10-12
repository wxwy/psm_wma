# PSM-WMA V3 — Formal30k torchrun 日志魔数重构设计裁决（不阻塞正式恢复）

**日期:** 2026-10-12
**任务:** `FORMAL30K_NAMED_RANK_LOGGING_DESIGN_ONLY`
**Formal production Root:** `444c232b976e80ac68cde9e7370e73b9f6410f0e`; **Child/Gitlink:** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`.
**技术结论:** **选择方案 A 的最小专用实现**，由 **cx 提交实现**，GPT 待新 implementation SHA 做增量审核；不修改当前已冻结训练代码、不改变正式恢复授权、不以这份设计记录给出新训练许可。
**来源:** Owner 转交 DS 报告 `docs/collab/chatgpt/evidence/2026-10-12_V3_formal30k/DS_PRO_2026-10-12_torchrun_tee_magic_number_owner_relay.md`；官方 PyTorch 文档 https://docs.pytorch.org/docs/main/elastic/run.html 及 https://docs.pytorch.org/docs/stable/elastic/multiprocessing.html。
**交接:** `docs/collab/chatgpt/requests/2026-10-12_V3_formal30k_named_rank_logging_cx_implementation_request.md`。

## 1. 审核事实与根因

- PyTorch `torchrun` 日志参数 `--tee/--redirects` 的单值表示 **stdout/stderr stream bitmask**，**不是**要收集的 Rank 序列。`--tee 0,1,2,3,4,5,6,7` 因语法不符合单一 `0..3` 或 `rank:std` 而失败。与模型 Forward、分布式梯度或 C1/D1 无关。
- `--tee 3` 等价 `Std.ALL`，适用于所有 local Rank，将 stdout+stderr 写盘并回显终端；`--tee 3` 自带重定向，不需要再冗余 `--redirects 3`。作为当前 Owner 手动 Resume 的即时 workaround **正确且不阻塞训练**。
- 这里是 **操作界面/可维护性问题**，不是现有生产训练脚本Bug。无需重复 C1、Index、D1数值或正式 Root/Child 原冻结审核。

## 2. 设计决策及其它候选判断

采用 **A 的专用小型启动封装**，未来实现候选位置：
- 根仓 V3：`tools/v3/formal30k_ranklog_launcher.py`
- CPU测试：`tools/v3/test_formal30k_ranklog_launcher.py`
- 可选独立只读入口清单/提交 SHA记录，不改 `cosmos_framework/trainer`、`examples/psm_wma_robocasa_corrected_phase5.py`、DCP、Dataset或recipe。

不采用 B：劫持训练脚本各 Rank 的标准输出/错误输出会触及生产Runtime、异常生命周期及已有 `TelemetryJournal`，超出只修日志表达的必要范围。C 虽然最少行数，但将 `3` 隐藏到 shell 中，欠缺显式类型定义/CLI验证，后续扩展容易重复错误；可作为当前 `--tee 3` workaround，但不是长期规范实现。

## 3. 冻结的可读 CLI contract

Owner 未来只看命名选项，不输入整数：
```bash
--rank-log-mode tee --rank-log-streams all
```
`rank-log-mode` 有 `tee`（写文件+回显）与 `files`（仅写文件）两种；`rank-log-streams` 可抽象 `all/stdout/stderr`。**Formal30k 默认且强制 `all`**，不能通过 `none/stdout/stderr` 取消异常日志证据；其它选项若留作复用，需在另一个 job Scope 单独审核。该专用正式任务默认 `tee + all`。

cx 在使用与当前 CUDA torchrun相同的 venv Python 的外部小脚本中导入：
```python
from torch.distributed.elastic.multiprocessing.api import Std

STREAMS = {"all": Std.ALL, "stdout": Std.OUT, "stderr": Std.ERR}
```
只有此处转换为CLI值。实现采用**列表 argv** 启动（不得拼接 `shell=True` 命令）：
- `mode=tee` → `["--tee", str(int(STREAMS["all"]))]`；
- `mode=files` → `["--redirects", str(int(STREAMS["all"]))]`；
- 禁止同时传多个互相冗余的 `--tee/--redirects`，禁止裸 `0,1,...,7`、`--max-restarts>0`、额外位置参数 `venv/bin/python` 假充训练脚本。
- 配合 `--log-dir <唯一目录>`，torchrun依其日志标准在内部建立 `<rdzv_run_id>/attempt_0/<rank>/stdout.log|stderr.log`；不可写死 `log_dir/rankN.log` 的错误期望。
- wrapper 必须支持 **默认只展示/校验 argv 的 dry-run**，只有明确 `--launch` 才能运行一次由 Owner 手动触发的生产命令；无自动调度/循环重试。
- 捕获实际当前 Formal30k 已批准完整 argv/environment；禁止通过通用任意透传改变 `--phase resume`、原Job路径、`--expected-root/child`、`--num-workers0`、warmup/save/batch/GA/seed 或CUDA配置。尽量只封装日志flags，少做功能性业务重构。

## 4. 冻结 Formal Pair / 发布边界

- 当前训练机 **仍需保持** Root `444c232b976e80ac68cde9e7370e73b9f6410f0e`、Child/Gitlink `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`；它的 Owner 手动命令使用正确 `--tee 3` 即可，不必等待 cx。
- cx 代码将写入**远端主仓 V3 新 implementation commit**，该 HEAD改变不能被当作冻结原训练服务器Root。即使只有工具与测试变更，也应形成**新实现target**，按本独立 Logger Gate 做源 Diff/Tests fresh Review，而不是悄悄替换旧正式执行身份。
- 当前服务器 `git pull` V3 会破坏 `verify_root_child_lock`；不得通过拉最新代码取新 Launcher。若之后确需启用，必须将经SHA审核的单文件侧载到**冻结工作树外**的独立只读目录，冻结文件 SHA、启动实参和Runtime证据，经后续窄Gate批准后才替换正式手动启动命令。
- wrapper 不能触发模型训练，除非 Owner 明确执行带 `--launch` 的版本；cx/DS 单独只运行 CPU parser/mock/dry-run tests，GPU/SIM/DCP均不在本次授权范围。

## 5. 实现 Gate 的可验收证据

cx 提交新的 implementation SHA 后，独立验证：
1. CPU parser / enum 映射：`tee/all` ↔ `Std.ALL`，`files/all` ↔ `Std.ALL`，非法 `0,1,2,3,4,5,6,7` 必 fail-closed；`--tee` 与 `--redirects`不冗余共存。
2. 8-rank dry-run mock 的 torchrun argv、`--log-dir`、日志分rank路径、`--max-restarts=0`、入口点为真实 `phase5.py`，且实际 `VENV/torchrun`、`PYTHONPATH` 指向冻结Child。
3. argv/环境冻结对照：`--phase resume`、`job.name=formal_verified_index_30k`、两个OFF env、raw prefetch0、全部训练超参以及 `config_digest` 符合既有Formal合同，不允许改变模型/data/optimizer/ckpt/telemetry。
4. Log输出目录唯一，不覆盖前次失败/成功，8 rank两条流均记录；进程首异常和返回码保留，不吞异常，不自动重试。CPU模拟写日志与无GPU dry-run即可，不因这项重做训练。
5. `--help`、dry-run 不启动Trainer/Torchrun或修改原Job文件；真正 `--launch` 需Owner明确操作。
6. 回传 cx 完整 commit SHA、相关文件diff/测试输出及零生产代码修改证明；DS只读验证，GPT之后审核实现Gate。

## 状态

`LOGGER_DESIGN_ACCEPTED_FOR_CX_IMPLEMENTATION`（仅指设计方案、非已实施代码PASS）。
`FORMAL30K_RESUME_OWNER_MANUAL_AUTHORITY_UNCHANGED`；无训练启动、无生产源码更改、无现有正式Pair变化。当前GPU资源政策按先前Owner 20GiB Guard生效。