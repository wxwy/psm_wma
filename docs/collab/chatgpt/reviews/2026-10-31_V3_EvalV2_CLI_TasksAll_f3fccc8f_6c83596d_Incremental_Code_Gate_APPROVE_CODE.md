# PSM-WMA V3 EvalV2 — `--tasks all` CLI wildcard parity：窄增量独立 Code Gate

**审核日期：2026-10-31。正式 Verdict：`APPROVE_CODE`（仅本精确Formal Pair的CLI任务选择增量及作者合成CPU Evidence）。**

| 身份 | 精确 SHA |
| --- | --- |
| Formal Root Implementation | `f3fccc8f9ba99cbaf8ce5e3597edfce8b6fc4ce1` |
| Formal Child / Gitlink（未变） | `6c83596d6a259e89c4cd3e79424024983426ac3d` |
| 当前审查前 canonical V3 | `0ab13951d640d50ea2c9c8812817bf3009eae7b5` |
| 作者Evidence/Bookkeeping HEAD（非Formal） | `5bd1c354ec011fd2379862c378cb6989dbe6f662` |

## 一、冻结的真实 Bug / Scope

- Owner报告 `--tasks all` 被Root `scripts/robocasa_eval_v2/config.py:94` 旧实现的 `a.tasks.split(",")` 变为 `['all']`；`identity.py:67-77` 仅当`cfg['tasks']=='all'`时解释完整18 Task通配符，对列表`['all']`按非法Task拒绝。这是精确的CLI→Discovery语义不一致，而不是Dataset目录/评测Server/PhaseB Batch的问题。
- Root `0ab13951d640d50ea2c9c8812817bf3009eae7b5 → f3fccc8f9ba99cbaf8ce5e3597edfce8b6fc4ce1` GitHub compare验证 **ahead1/behind0，只改1个production路径`config.py`的一行（+1/-1）**，另新增`tools/v3/eval_v2_batch_tests/tasks_cli_test.py`、一份Build说明及SESSION/TODO记录。整个Child/Gitlink保持`6c83596d6a259e89c4cd3e79424024983426ac3d`；Scheduler、identity/discover、EvalV2 CLI、Store、model/DCP/训练、各Launcher/EvalV2 Runtime与Sim没有生产差异。
- 正式源码精确实现 `config.py:93–94`：`cfg["tasks"] = "all" if a.tasks == "all" else a.tasks.split(",")`；只特殊处理大小写精确的CLI字符串`all`，其他命令保持历史逗号列表拆分，故CSV顺序/非法名单拒绝均不改变；YAML `tasks: all`与CLI override now have identical normalized `cfg["tasks"]`。没有引入额外Task名标准化、隐式fallback或新的研究语义。

## 二、Contract → Behavior → Evidence

| 合同/风险 | 真实实现 + 测试 | 判断 |
| --- | --- | --- |
| CLI `--tasks all` 等价YAML `tasks: all`，选完整18个atomic任务 | 新`tasks_cli_test.py:test_cli_all_overrides_subset_and_matches_yaml_all_in_every_run_mode`覆盖`dry-run/fresh/resume`的 config resolve+discover parity；`test_default_all_yaml_all_and_cli_all_are_the_same_selection`验证未填YAML的default all | PASS（Fresh/Resume仅解析，不是真实Run） |
| 不能破坏CSV Task选择或顺序 | `test_csv_still_preserves_requested_order_and_overrides_yaml_all`验证`OpenCabinet,CloseFridge`顺序及YAML覆盖；本次生产 else 恰为旧`split(',')` | PASS |
| 混杂通配符、未知、空、大小写错误，不能静默变相all | 参数化`all,CloseFridge`、`all,all`、`NoSuchTask`、空串、`ALL`测试维持`ValueError`；不完整18任务目录仍由现有Discovery拒绝 | PASS |
| 真公开CPU dry-run计划而不加载GPU/模型/环境 | 真实`robocasa_eval_v2.cli.main`与实际`discover`，Synthetic18 Task metadata；CLI all vs YAML all JSON完全相同，18 Tasks × 2 Epis = 36 Episode-major slots；fake不可达Checkpoint/Config；`prepare_inputs`及Runtime被显式forbidden，`models_loaded=0 / environments_created=0 / runtime_attested=false` | PASS（仅合成CPU边界） |
| 旧Bug确实复现、不是伪RED | 作者将**精确旧版`config.py` Blob `714a76156c5542c846681c6bc31c91935e01c69e`**以`importlib.spec_from_file_location/sys.modules`注入，执行同一个冻结新公开dry-run测试；真实`red.xml` 1/1失败，错误在`identity.py:71` `only RoboCasa365 Target Atomic-Seen tasks...`，与本次Bug完全相符；新源码`green`通过 | RED/GREEN真实可追溯 |

## 三、作者原始Evidence独立检查

- Evidence：`docs/collab/codex/evidence/2026-10-31_eval_v2_cli_tasks_all_author_cpu/` at HEAD `5bd1c354ec011fd2379862c378cb6989dbe6f662`；正式源码检查Root与Child确切Git Tree及Production Blob `config.py = 2881df219c254f485e601b9e1a540c4ca15c1b46`，新测试Blob `21616a29c53cbde3b9174c5829ac4d85bcfb3178`，与作者原件`formal_source_bindings.json`一致。
- GPT直接读原始`junit.xml`：**29个不同`classname+name`测试、0 failure/0 error/0 skip**；其中新增CLI12、旧Config/Profile17。作者`green.log`为`29 passed in 0.37s`。GPT直接读`red.xml/red.log`确认仅有**1个预期失败**，不把故意RED混计为新版本的失败。
- `gate.json`表明冻结Formal Pair与前后Source不变、Ruff 0.12.7 scoped check/format与syntax2文件 exit0，作者未执行GPU。GPT自实现并自测SHA256校验，再按GitHub获取字节内容，逐一核对`artifact_manifest.json`中**12份关键原始Evidence，12/12 SHA256一致**（green/red JUnit与log、门控/Scope、旧config与bootstrap、Ruff日志、README等）。这不是GPT在训练服务器上运行pytest。

## 四、Findings、权限和下一步

- **旧CLI通配符Bug：`CLOSED`**。本Formal Pair未发现新的HIGH/MEDIUM blocker，代码Diff精确、回归边界清楚、已有正式EvalV2其它Gate保持，不重复84/324/301或真实GPU测试。
- **Verdict：`APPROVE_CODE`** 仅限 `f3fccc8f9ba99cbaf8ce5e3597edfce8b6fc4ce1` / `6c83596d6a259e89c4cd3e79424024983426ac3d` 的EvalV2 CLI `--tasks all`语义修复及作者合成CPU Evidence；不授权另行修改PhaseA/PhaseB、改变LocalTTT required、任何训练/仿真/GPU/900任务、使用原DCP或动已有Run。
- **合并建议**：Codex在与正在运行的训练/仿真**完全隔离**的代码目录安全提升已批Root单行修复和必要测试到最新canonical V3（Child Gitlink仍6c），非强推/远端源Blob readback后提交回执；**绝不热更新共享在训目录、重启Job或重复历史测试**。提升后方可在新的、已同步的安全CLI环境直接使用`--tasks all`；当前未提升的现场仍可在YAML写`tasks: all`并不传CLI该参数作为无需代码变更的有效workaround。

正式Review与Canonical`docs/collab/chatgpt/CODEX_INBOX.md`均写入后才算正式Verdict；后续Docs-only SHA不得代替已审核Formal Pair。