# V3 EvalV2 Phase B B2 — 受控生产提升（Promotion）源码一致性审核

**日期：**2026-10-30

**Scope verdict：`APPROVE_CODE` — controlled Git content promotion/source-tree equivalence ONLY.** 已在 GitHub 更新 V3，源提升提交SHA：`978337deef0173f60336977367e21f513772a465`；Child/Gitlink：`0ae313e329d290fc6b8a50fda1112820fb7ac485`。此 verdict 不把旧Root测试结果冒称为新Root的独立435完整测试，不授权真实 GPU/Canary/正式900/训练或触碰NoTTT本机工作树。

## 1. SHA身份与历史

- 被测试 Formal Root：`a139b5a35877a79e0a56c2208f3002f731972b11` / Child+Gitlink `0ae313e329d290fc6b8a50fda1112820fb7ac485`。
- V3生产提升 Root：`978337deef0173f60336977367e21f513772a465` / Child+Gitlink `0ae313e329d290fc6b8a50fda1112820fb7ac485`。
- 当前V3在文档归档前代码HEAD：`978337deef0173f60336977367e21f513772a465`（与`978337deef0173f60336977367e21f513772a465`如相同则无需额外实现比对）。
- `978337deef0173f60336977367e21f513772a465` 单Parent `d2f5bcc879aa8acb4341f8a12c56544e7814954b`，使用受控Git树叠加已验证的Git Blob，不是直接merge候选长期分支；其Code Root SHA因V3已有文档历史不同而与被测试Formal Root不同。

## 2. 生产合并的精确内容和防误覆盖

GitHub比较源树：候选被测试Root有13,283条递归tree entry；V3原有12,513条。双方有不同的文档/审计历史，全面分支merge会把大量无关docs引入或覆盖。

此次Promotion以前一V3 tree `49ae0d91ea8a9f5be101059fa7b511b3e9081455` 为base，创建新tree `23140e7865a58c1acff6b35f6dd6963fb8ee5ad2`，导入**只含以下53项**：
- `configs/eval/` 两个EvalV2 YAML；
- `scripts/` 十个EvalV2执行/CLI/Runtime/Process脚本；
- `tools/v3/` 四十个EvalV2 prototype/design/production test/PhaseB batch/gate文件；
- `cosmos-framework` Gitlink：旧 `746c5cf2f2324104a62fb71510343aa40d3976c5` → 精确 `0ae313e329d290fc6b8a50fda1112820fb7ac485`。Child新SHA是旧Gitlink的直接后继链（GitHub compare: ahead7, behind0）。

该提升是GitHub源对象直拷，非重新手写生产代码，含51普通文件 `100644`、1可执行脚本`100755`、1Gitlink`160000`。Remote compare基线→`978337deef0173f60336977367e21f513772a465`仅53个文件，0个docs/SESSION/TODO变动，未触碰其它已有NoTTT根仓路径。提升前做了同名production path mismatch检测：除Gitlink外已有生产路径不被覆盖。

**重要的源码等价证明：** independent full recursive Git-tree comparison，冻结新tree `23140e7865a58c1acff6b35f6dd6963fb8ee5ad2` 与被测试Root tree `4414e4986210c1f7bee5b31e2c215ba6671f3e0e`，在排除 `docs/`、`SESSION.md`、`TODO.md`后，**9,844/9,844 非文档路径的 Git SHA、mode、object type 完全一致（0 mismatch）**。合并前V3所有docs和SESSION/TODO的Git SHA也完全保留（0 mismatch）。本证明同时包括整个Root的非文档Python/shell/config文件与Child Gitlink，而不仅是53个被添加的文件。

由此，V3源码内容已与已通过CPU Gate的正式Root在相关路径上同字节一致；但**root commit SHA/实验身份发生改变**，生产升级以本次Promotion SHA单独追溯，不能原封不动转用旧Root作为新实验身份。

## 3. CPU Evidence 的精确边界

- 被测试正式源Root `a139b5a35877a79e0a56c2208f3002f731972b11` / Child `0ae313e329d290fc6b8a50fda1112820fb7ac485` 的作者完整合成CPU435/435，原始JUnit/Gate/源/OS证据已由GPT独立核查，Review：`docs/collab/chatgpt/reviews/2026-10-30_V3_EvalV2_PhaseB_Author435_a139b5a3_0ae313e3_Evidence_Gate_PASS.md`。
- DS_PRO在隔离独立Clone对**同一被测试正式源Pair**报告完整435/435 PASS、source_unchanged true、B2/F3/Store等行为PASS。用户明确选择依据DS已提交报告继续流程而不再逐条复制长XML；因此**DS_PASS_REPORTED / OWNER_ACCEPTED_FOR_PROMOTION**。GPT未获取DS服务器自身原始JUnit/OS原件，不能写作`GPT_INDEPENDENT_RAW_VERIFIED_DS_PASS`。
- 新Promotion Root `978337deef0173f60336977367e21f513772a465` 只有源码/子模块**Git-tree完全等价**的窄fresh Code审核；未在新Root `978337deef0173f60336977367e21f513772a465` 独立重跑435CPU。禁止把源等价与形式化新 SHA 运行身份混成一项。

## 4. 非授权事项/本地训练隔离

此处只执行GitHub远端V3受控源提升；未操作`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/`；未对该目录fetch/checkout/reset/rebase/merge、未终止NoTTT任务，也未启任何GPU/Cosmos/EGL/RoboCasa/Canary/real900或训练。Github V3 HEAD可能在此审查记录再次增加docs-only提交，但其Formally promoted implementation SHA仍是`978337deef0173f60336977367e21f513772a465`，Gitlink仍需保持`0ae313e329d290fc6b8a50fda1112820fb7ac485`。

真实下一步**单独的Owner授权Gate**是1 GPU / M=2 / B=2真实Canary：须在保证NoTTT训练GPU与CPU不被占用的独立目录/资源下执行，验证真正Cosmos模型及RoboCasa Session/动作/前缀、真实仿真replan与cleanup；不能因为CPU synthetic435通过自动宣称GPU Gate完成。正式18×50真实900同样不得提前执行。

**此报告是生产提升后的新Root最小源码等价审核，非重新审整个PhaseB代码。**
