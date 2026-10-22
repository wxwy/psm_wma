# G1 iter8900 Owner-authorized cross-pair Resume — author handoff

日期：2026-10-22。基于Owner明确Override设计批准，只交付代码/CPU候选；**不启动训练，不是独立验收通过**。

| 项目 | 精确版本 |
| --- | --- |
| Candidate Implementation Root | `b910304dbf493eb5babe26cf1b055edc8477b386` |
| Candidate Child/Gitlink | `61bfa94766d33d95a7fa9771857d0f2fb3f0b405` |
| Root/Child分支 | `v3-g1-cross-pair-resume-20261022` |
| Root基线 | `1fc28effe9e33a2e6522f6ffe60c55c68f8b367c` |
| Child修改基线 | `35b0ea1ccee9ee26653ed6589c484f0997d1c586` |

Child先提交/推送，Root再固定Gitlink；两者仅发布隔离refs，未自动部署或主线合并。后续文档HEAD不是Implementation。旧e012 Root对象、目标机8610ad88完整SHA及真实G1摘要均未由作者取得，不冒称验证。

## 1. 已实现的最小合同

- Child `examples/psm_wma_robocasa_corrected_phase5.py:142–346`：显式 `--owner-authorized-g1-cross-pair-resume`，仅精确Job `packed128_droid_fresh_g1_20261019`、resume、T16/B8/GA2/K4/world8、30k/warm500/save100，拒绝Fresh/其它Job/默认路径隐式迁移。旧Root `e0121d34592d10323ede480eb3409468a07371ba` / Child `2d128ed5a07601cdd424974f99b67832eafeeb41` 必须精确匹配，旧canonical YAML SHA钉死 `f87e2e49c6931ce7dc32b467aa3f8026269f5ad255216e1cdd8fafb1d7e7374e`。identity schema/namespace/layout/diagnostic/semantic自哈希及原canonical YAML/PKL hash、symlink保护保留。
- 仅最高层root/child两个source字段可归一化。其余semantic递归比较类型/键/值（包括模型、Tokenizer、Optimizer/Scheduler/Trainer、数据/Cache/Source/Index、RNG、H/T/B/GA/K/world等）；错误报告完整字段路径，不能跳过整个semantic。
- 历史摘要重建：`hash({phase5_digest: current_raw_digest, training_identity: frozen_record.semantic})`，只用于旧Source身份绑定。必须逐值等于具有原canonical Config副本的原始fresh launch记录，并匹配8个rank sidecar的config_digest/iteration/cache/corpus/source/profile rank-world及每个SegmentProvenance digest。不能用猜测前缀或单纯新Pair重算摘要冒充旧摘要。sidecar实际SHA/size及原launch SHA保存为见证；读取中变化或trailing数据拒绝。
- `preflight()`将验证后的旧digest交入report；`main()`未修改，原Producer和trainer.bind_grouped_stream继续从report取同一digest。preflight可选snapshot Producer在Override下也使用已验证旧digest；正常路径仍用原摘要规则。8-rank只读agreement额外绑定runtime audit，避免旧digest相同掩盖各Rank运行了不同新Source。
- `_resume_checkpoint()`保留原四组件metadata和8份sidecar/symlink检查，Override还要求latest精确`iter_000008900`且原执行预算大于8900。**这是仅本次8900起点授权，不能自动用于今后别的迭代**；也不能把推理“optim不需要”误用于完整训练恢复。
- `JobLifecycle.write_config()`在原独占lease下重验当前Source与冻结authority；与preflight见证不同则在创建新launch前拒绝。以后合法执行时，只在新launch.json写Owner flag、frozen/runtime Source、旧/新semantic digest、旧config_digest、canonical Config SHA、8900路径、8rank witness和验证状态。真实Optimizer/Scheduler/RNG/Fast完整加载标为`PENDING_UNCHANGED_STRICT_RUNTIME_LOAD`，不把metadata存在或digest一致声称完整恢复已通过。RAM/新launch Config16允许，旧canonical Config32/PKL/Identity/已有DCP/latest文件不重写。
- Root `scripts/train_v3_packed128_staged.sh`：只增加可选第三个显式flag，必须resume且JOB_NAME精确G1；未知参数、Fresh或其他Job提前拒绝。正常两参数入口原行为保留。测试用假Python捕获argv，不执行torchrun。

## 2. 关于设计中“新Child=35b0”的自引用问题

35b0是修改前基线，新增代码必然产生61bfa947这个新SHA，不可能同时要求执行新增代码和HEAD仍等于35b0。实现保留原`--expected-root/--expected-child`与实际HEAD/Gitlink/clean的完整相等检查；Override还要求运行Child是35b0的后继（包括该基线），不接受无关谱系。**未来只按新审核Pair精确钉死实际61bfa947/new Root**，不把任意“新Child”都视为审核通过。

这不是放宽旧frozen authority，也不猜测目标机8610ad88前缀。若浅克隆缺少35b0 ancestor对象，先只读fetch所需历史并重验；不忽略祖先检查或reset训练目录。新Root可为经Owner指定的完整实际运行SHA，必须与`--expected-root`精确相等，不能用8位前缀。

## 3. 没有修改的安全边界

`training_identity()`、原始`config_digest()`、`overlay_config()`、`main()`及原执行预算/namespace路径函数AST不变。通用Trainer、DCP/RNG/Optimizer、Local算法、Producer/Planner、Config-truth helper及原有回归文件字节不变；评测Queue/Guardrails改动完整保留。完整状态真正恢复仍由原SafeLocal checkpointer/callback/restore_grouped_local_state做，不能绕过Cursor/frontier/Fast shape/finite或rank RNG校验。

Scope仅Child Phase5+新测试、Root launcher+Gitlink/notes/Evidence。原审查记录和Inbox archive保留；Owner设计Override取代“必须退回旧Pair”的历史决定，但不自动批准这个新Implementation。

## 4. CPU Red/Green与可证明范围

目录：`docs/collab/codex/evidence/2026-10-22_G1_iter8900_cross_pair_resume_author_cpu/`。

- **115 passed =68新增case+28原F0方法+19原Config-truth case，32 subtests PASS，0fail/error/skip，6.275s**。JUnit147包含subtests，不是147个独立方法。20 warnings为既有Cache测试fixture level marker。Python3.12.14/Torch2.10+cpu/OmegaConf2.3.0/attrs25.4.0，Ruff0.12.7 check/format、syntax、bash-n、root/child diff PASS。
- Red：原35b0 Phase5在同一合成旧G1/newPair fixture拒绝Source相等检查。baseline仅补Owner固定常量供新fixture使用，未复制兼容逻辑；原始错误日志/旧源码hash保留。
- Green：严格通过唯一G1+flag、旧摘要跨旧launch/8rank sidecar/provenance一致性；新Source重算摘要由原restore实际拒绝。对每Rank运行**未修改原函数/类体**的snapshot、restore、core validator、frontier/planner/callback，真实CPU Tensor Fast值/游标与下一窗口计划一致，损坏游标/NaN/形状/provenance继续拒绝且live引用不变。只有重依赖import wiring隔离、callback基类替身；模型core维度缩小，B8/GA2/world8/T16/K4保留。不是GPU/FSDP或完整DCP Restore。
- 负例覆盖无flag/Fresh/其他job/非源模型与优化器/调度/Tokenizer/数据/RNG/几何漂移、错误oldPair/semantic/hash/canonical、错误runtime Root/Child/Gitlink/dirty源码/祖先、缺component/rank、错误iteration/digest/历史launch、launch前sidecar/report漂移；旧原始合成文件SHA+mtime不变。新launch测试仅新子目录追加。
- 实际preflight函数通过重模型/数据加载边界替身和显式semantic fixture执行，验证report及snapshot Producer使用历史digest；8-rank collective是mock不是Gloo/NCCL，实际运行Source git命令通过定向受控替身做正反例。完整机器环境/Config.validate/真实G1摘要与Checkpoint内容没有在作者云端实测。
- 测试只在临时YAML/PKL/metadata占位文件上运行，production YAML固定SHA只在fixture内替换成合成文件SHA；不把这个fixture说成目标f87文件已读取。作者没有访问真实G1资产、停止进程、同步服务器或启动GPU/真实模型/Action Server/Simulator/训练。
- gate.json记录完整命令/cwd/env/RC/Source SHA；manifest、日志/JUnit、witness、原始diff及scope proof齐全。

## 5. 下一步：GPT新Pair审核 → DS只读CPU → Owner单独实际启动

请对b910304d/61bfa947完整新Pair做增量审核，不再要求checkout旧Pair；重点审source-only normalization、历史digest连续性、runtimeSource审计、未改变真实恢复验证。新代码未自动合入V3，canonical V3 Inbox将有隔离Pair交接指针。

DS在clean detached独立新Pair工作区可执行（Child cwd，外置pycache/log/空pytest.ini）：

```bash
CUDA_VISIBLE_DEVICES='' python -m pytest --noconftest -c <EXTERNAL_PYTEST_INI> -q -s -p no:cacheprovider \
  examples/psm_wma_robocasa_g1_cross_pair_resume_test.py \
  examples/psm_wma_robocasa_phase5_f0_test.py \
  examples/psm_wma_robocasa_effective_config_test.py
```

完整依赖可直接导入；最小CPU环境参考证据里的pytest_cpu.py，只隔离无关Dataset eager registry，修正云端硬路径。执行两改动Child文件Ruff0.12.7 check/format、Root launcher bash-n。实际G1只读preflight/digest核验须在新Pair技术审核后由DS按真实路径提供完整args，精确expectedRoot/Child与Owner flag，**只用`--preflight`而非训练入口/torchrun**，不得调用JobLifecycle writer写真实Job。

应读取并报告真实frozen YAML/PKL/Identity、原fresh launch、8900所有rank sidecar和full-training组件的完整见证；旧digest由这些文件验证，不是作者常量。任何非源语义或digest/component问题BLOCKED，保留实际失败字段，不另开广泛绕过。此后完整真实CUDA/FSDP/Optimizer/Scheduler/RNG/Fast Restore仍需单独执行授权，不能以CPU PASS直接继续30k。

**STOP：仅隔离代码/CPU交付。等待新Pair GPT独立审核及DS验收；不自动部署、GPU/训练或写Checkpoint。**
