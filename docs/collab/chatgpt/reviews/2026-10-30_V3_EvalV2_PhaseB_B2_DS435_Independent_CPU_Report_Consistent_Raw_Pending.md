# PSM-WMA V3 EvalV2 Phase B2 — DS_PRO 独立 CPU435 报告口径核查（Raw Evidence Pending）

**审核日期：**2026-10-30。**审核角色：**GPT独立 Evidence reviewer。**Formal source Pair 未变**，不重复 F1/F2/F3/F4/Store/READY Code Gate 审核。

| Identity | SHA |
| --- | --- |
| Formal Root | `a139b5a35877a79e0a56c2208f3002f731972b11` |
| Formal Child/Gitlink | `0ae313e329d290fc6b8a50fda1112820fb7ac485` |
| 本轮 V3 当前远端基线 | `e7543ff63bfc1f492349fb05e61aa0c8317588b1`（文档归档，不是Formal技术SHA） |
| DS独立运行目录（报告） | `/tmp/ds_pro_evalv2_435_20261030/` |
| 报告给定 Gate SHA256 | `919f3ca9c12e9c06f9f4f5e1320ebbf3a7c2a399ab5c91f75073c0c8062ea379`（**未独立校验原始字节**） |

## 1. Formal verdict / truthfulness boundary

**DS执行报告自述：`PASS` (435/435, exit0, `gate.status=PASS`, `source_unchanged=true`)。报告内结果、算术与已冻结CPU条件相容；无新Code blocker线索。**

**GPT独立 Evidence Gate 当前处理状态：`REQUEST_CHANGES` — Evidence-only，唯一 open item `DS-RAW-1`：DS此次原始 Gate/JUnit/OS 文件尚未通过本审核者可访问渠道交付。**

严格区分：

- `DS_CPU_PASS_REPORTED / REPORT_CONSISTENT`：可记录已经执行、报告全绿，不要求重跑。
- `RAW_EVIDENCE_PENDING`：没有独立读取DS自身机器上`/tmp/...`文件的实际内容、核验报告的 SHA256、正式JUnit testcase唯一性、OS witness原件。因此 **暂不称“GPT独立核验证实DS CPU435 Gate PASS / Gate正式关闭”**。
- 先前作者CPU435 Gate `PASS` 已在 [正式 Review](https://github.com/wxwy/psm_wma/blob/832bd90fffc8096419293caa1470886f361630bd/docs/collab/chatgpt/reviews/2026-10-30_V3_EvalV2_PhaseB_Author435_a139b5a3_0ae313e3_Evidence_Gate_PASS.md) 直接逐个检验过 GitHub 原件，**不能拿作者raw代替DS raw**。
- GPT已尝试原始服务器路径：当前本会话沙箱不包含DS `/tmp/ds_pro_evalv2_435_20261030/evidence/gate.json`；已连接的Desktop Commander设备当前离线，无法访问该服务器。GitHub V3证据目录亦未找到这次DS原件归档。此为可访问性限制，不是DS运行失败。

## 2. DS所报告结果（标记为 reported，未独立原始核验）

| Gate Step | DS报告 |
| --- | --- |
| import_origin | exit 0，Child 从隔离克隆导入 |
| Ruff check / format | exit0 / exit0 |
| inference | 145 PASS，0 fail/error/skip |
| Phase A | 256 PASS，0 fail/error/skip |
| Phase B | 34 PASS，0 fail/error/skip |
| **合计** | **435/435 PASS，0 fail/error/skip；shell0；gate PASS** |
| 源码状态 | 原报告称原始54项SHA全部一致、Root/Child洁净、无残留测试进程 |

报告还称：
- G1/N2/E2（1模型/2Sim/2episodes）native histogram `{1:4,2:2}`，有**2次真实B2**、4个valid，physics_overlap=true；
- G2/N3/E1 和 G1/N3/E1 histogram `{1:6,2:0}`，允许动态部分Batch；这两个场景不应强制出现B2，**不是反例**；
- F1通配地址拒绝其它loopback，F2三拓扑，F3有两个活跃Ticket时Server死、只清理owned组，Store并发mkdir安全回归、F4进度快照、D5/Resume均PASS（按DS报告）；
- `git clone --no-checkout` 独立克隆，`git checkout --detach`冻结Root，Submodule URL override仅写此Clone的local Git config；CPU-only环境、缓存与tmp放置于独立BASE、无pip更改。当前NoTTT训练所在 `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/` 未操作，GPU未占用，算力余量按DS报告充足。GPT未直接获取当前机器PID/资源快照，不将“无干扰”宣传为独立观测事实。

**以上都属于DS报告证据，不可改称经GPT逐条原始验证。** 报告中所列SHA256是待匹配的字节锚点。独立CPU gate结果的判断必须仍按同一 Formal Pair + DS 自身原件完成。

## 3. 唯一未关闭事项 DS-RAW-1 — MEDIUM evidence-only

**位置：** DS报告 `/tmp/ds_pro_evalv2_435_20261030/evidence/`，当前无法直接访问；已知目标 `gate.json`、`junit.xml`、`inference.xml`、`phase_a_regression.xml`、`phase_b_runtime.xml`、`phase_b_runtime.log`、`source_sha256.json`、`evidence_files.sha256`、可公开的相关OS原始记录。

**根因：**本次申请只包含DS生成的摘要与文件名、SHA256值，未包含那些可被GPT读取并哈希核验的原始DS文件；Desktop Commander唯一设备离线；本会话沙箱文件系统与DS服务器不共享`/tmp`。

**违反的验收证据条件：**独立Evidence审核须在精确正式版本下建立 CPU Gate contract → 实际多进程行为 → **可访问原始证据** 的链，不允许只因DS或作者声明 PASS就发最终Gate closure。此为**证据可访问性**问题，不指向任何生产/夹具/测试缺陷。

**最小验收条件：**DS不再跑测试、不改源码，只将**此次已经生成**的文件以不可变形式交付，例如交给Codex在**独立仅文档/证据分支**归档或直接作为当前聊天附件。至少交付DS自己的 Gate JSON、combined与三组JUnit、PhaseA/PhaseB原始log、源前/后SHA及import/static日志、`evidence_files.sha256`；并保留/提供能支持原有B2/F3/owned进程清理与Session隔离的原始OS证据或真实测试输出。对外发布须避开敏感环境变量、个人凭据；如果为保密进行了删改，需保留原文件的hash和删改范围，不得声称上传文件与原始完全同字节。无需拷贝整个`phase_b_runtime_tmp`，仅选有关OS片段及原始raw即可。

提供后，GPT只进行 **DS-RAW-1 极窄证据复审**（原SHA256 → JUnit唯一case/zero fail → Gate身份/exit/source unchanged → OS witness），不重做Code Review、不重跑435，不复验已通过的作者完整CPU。

## 4. Remote V3/Owner gate boundary

独立核对最新远端 V3 参考：`e7543ff63bfc1f492349fb05e61aa0c8317588b1`；V3 Gitlink仍为 `746c5cf2f2324104a62fb71510343aa40d3976c5`，**不是**已批准的正式Child `0ae313e329d290fc6b8a50fda1112820fb7ac485`。DS报告中的本地HEAD `5b540cce`与最新远端分叉状态不能作为可直接Merge的事实依据。勿在NoTTT目录执行checkout/fetch/reset/merge/rebase。

**在 DS RAW证据复审正式关闭且Owner另行授权之前：不作 V3/Child生产合并、不启真实1GPU/M2/B2 Canary、正式18×50、不占NoTTT训练资源。** 即便DS raw审核通过，真实Canary仍是**独立的Owner授权 Gate**。技术上无必要新增其他架构Gate或重新调Batch参数。
