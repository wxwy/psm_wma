# Issue27 — Root 9b1756f9 / Child 60b252d0：streaming M16×2（32 Sessions）Evidence 整改复审

- 日期：2026-11-09（CST）
- Formal root implementation/tests SHA: `9b1756f9099955d6637743f8ad2fa0ee54987b7a`
- Formal Child/Gitlink SHA: `60b252d05157b2753d2caebae32b11c878504bbe`
- 上一轮形式 Pair：Root `15dbc97bf13437905ec38247382834067e5341ae` / Child `60b252d05157b2753d2caebae32b11c878504bbe`
- Base V3 `e58cef1f53d2382d39c871ce5a50e4acdd5ce268`；Child base `b0dbd115d03e801ec4d0788c30ee0b0e9655d4db`。
- PR：Root [#29](https://github.com/wxwy/psm_wma/pull/29)、Child [#8](https://github.com/wxwy/cosmos-framework/pull/8)，本 Gate 不操作合并。
- **正式 verdict literal：`APPROVE_CODE`，仅关闭 Issue27 通用 Shared VAE 拓扑的 CPU/静态 Code+Evidence Gate。**

## 与前一轮相比实际变化

GitHub 精确 Root compare `15dbc97b...9b1756f9`：新 formal Root 只改 Root 的 `tools/v3/eval_v2_batch_tests/shared_vae_routing_test.py`、`shared_vae_daemon_fixture.py`，新增 `shared_vae_streaming_m16_test.py`，另有 review/ledger/runbook 文档；Child SHA 不变、Root `scripts` 生产 tree SHA 均为 `5753a1a7c448c94e05e337380f5addccc7b71468`，实际零生产代码变更。因此不重复生产语义审核/旧完整965+207 tests。

## 历史唯一 blocker —— CLOSED

原报告 `2026-11-09_Issue27_15dbc97b_60b252d0_GenericTopology_Evidence_REQUEST_CHANGES.md` 指出：旧 `(2,8)` 只有16 total Sim，而 Owner 要求的代表性 `2×16` 指每个 Policy Server 对应16个 Sim，共32，缺正式 streaming M16 的多 Session/Worker/Owner真实 CPU 进程合同证据。

独立检查新提交 **实际代码** `tools/v3/eval_v2_batch_tests/shared_vae_streaming_m16_test.py`、`shared_vae_routing_test.py`：使用原 `Store` + frozen18Tasks Manifest + `Runtime` + `streaming_task_affinity_v2` + `streaming32`。真实 CPU Worker subprocess、Registry、private FD、Unix IPC、Owner HTTP 及 Native transactions 贯通；实际 Wan/DCP/Current Boundary/EGL/Sim和物理时钟为明确合成/替身，不把 CPU 试验冒充真实仿真。

两种实际场景均覆盖：
- 2 Policy ×16 Sim/Policy = 32 real Session/Slot identities，按 Policy 正确分配每16个；
- 2 render GPU →2 Worker、各16 Session/1 Policy epoch；同 render GPU →1 Worker、32 Session/2 Policy epochs；
- 真实两个 Native Actor 分别记录 `B8+B8`，每 Session action/response 映射一致；
- 32 条 Worker source1 signed feature 均验证 lease/epoch/source/原始身份；source0 为 Policy-owned 缓存 boundary（CPU 模拟），无重复 VAE；
- 各 32 Policy response ACK、Worker result ACK、scoped End、native End；真实被保护 Session 未被错误 capability / stale generation / cross-server lease 污染；
- Worker exit0、IPC 被回收，外部独立进程存活，真实 owned CPU RSS 测量为正，资源 reservation 清除。

已核对 Repo 原始机读产物：`docs/collab/codex/evidence/2026-11-09_issue27_streaming_m16_32_sessions/author-01/m16_os_behavior_0.json` 与 `m16_os_behavior_1.json`，分别 Worker数2/1、unique Session32、B8+B8 per server、32 ACK/End；`author-01/focused.xml` 18 testcase /0 fail/0 error/0 skip；`author-01/pytest.log` “18 passed”，5项 pytest 标记/依赖警告不是失败；`author-01/gate.json` Ruff/check/pytest exit0、source_unchanged；`production_identity.json` Root scripts tree 前后完全相同，Child 未改。

原始开发过程曾因 synthetic action 6D rotation 无效出现2失败，文档将其与最终18PASS严格区分，修正仅在测试夹具中，未发现需升级的生产 blocker。

### 结论

- 上一轮 MEDIUM Evidence-only blocker **CLOSED**，无新增已确认 blocker。
- **`APPROVE_CODE`：Issue27 CPU/static/Evidence gate closure**；此版本通用 Server/Sim 拓扑扩展有足够 CPU 合同证据，可结束本轮代码整改。旧1×1 H100、旧 server_vae 2×16评测并未因为本 Code Gate 变成新多实例 shared VAE 的真实 H100 通过。
- 尚未授权且尚未完成：新 shared VAE 真实多 Sim GPU/EGL/Action path/throughput 性能、SR、900EP、训练或自动合并 V3。需要真实验收时只运行既定最小 GPU smoke，不重复旧900EP。
- #28 独立任务：以**审核通过的 Issue27 精确 code pair**（或后续经过单独验证的合入版本）为基础，仍是一套 EvalV2，新增 `local_ttt_history_k=1/2/4/8/16` 默认16，按已执行 H16 Chunk 相对索引 `i%(16/K)==0` 选择，i=0 是上一轮 Cosmos/current Policy frame的缓存，未选帧不做历史 VAE/FW，但源 step 完成和事务身份仍完整。#28 不包含在本次 `APPROVE_CODE` 范围内。

## 审核方法和证据边界

本轮审核独立读取 GitHub 正式 SHA 增量与直接测试源码，核对作者 JUnit/原始 scenario receipt/进程签名与源码结论是否匹配，未单独发起第二次 pytest 或连接 H100。这是**独立代码/证据判断**，而不是声称“Reviewer 亲自重跑了18项”。
