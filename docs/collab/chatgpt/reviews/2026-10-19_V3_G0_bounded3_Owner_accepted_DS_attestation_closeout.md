# V3 G0 bounded_3step — Owner 接受 DS_PRO 现场证据后的 Gate 关闭裁决

**日期**：2026-10-19  
**决定来源**：Owner 在本会话中明确表示：「相信ds，gpt和codex不能读取训练服务器的文件」。  
**Gate**：G0 bounded_3step, 8×H100, fresh, `--stop-after-iter 3 --audit-missing-grads`。  
**正式范围内裁决**：`APPROVE_TO_CLOSE` — **仅 G0，采用 Owner 授权的 DS_PRO on-host evidence attestation 作为足够证据**。  
**独立核验限定**：GPT 没有直接读取训练服务器原始 JSON/log、24条审计、DCP metadata，也未在GitHub回读到本地G0 Root `0d770dd0...`。因此 **不得宣传为 GPT 独立 raw-evidence verified**。此为 Owner 明确选择的证据保证等级，而非无条件独立验证。  
**G1 Fresh100**：`GPU_EXECUTION_RELEASE=BLOCKED`，待下一 Gate 的明确 Owner GPU 授权与新运行身份/容量检查。

## 1. 精确 G0 作业身份（DS_PRO 现场核验、Owner 接受）

- G0 as-executed Root：`0d770dd03ef701d85e58751aa7f6df58dd1a8861`（训练机本地，未发布至 GitHub V3）。
- Child/Gitlink：`2d128ed5a07601cdd424974f99b67832eafeeb41`，此 Child 代码在远端可直接查看。
- 已独立核验过的生产合并 Root：`dd6e040ea8229fc3ce81259952444f82dd9897b2`。DS_PRO 现场 `merge-base`、`git diff --name-status` 报告 `0d770dd0` 为该 Root 后代，增量仅 `docs/` 10文件（M1 + A9），无 production 变更；Owner 明确认可 DS_PRO 此项现场证明。本裁决不谎称 GPT 能直接验证本地0d Git对象。
- G0 config_digest：`61c69bbc265fed40bae2a8c41bd09c77cc8027a024f29611321b5cd8433ee326`；semantic_digest：`9ceaaf306d2c0b5edf0a348029741230864343dd68a433cef7bb77ddc49cd495`，报告称 identity 与 launch一致。
- 训练 DROID Fresh、Packed128、raw15/state15、left_wrist、T16/B8/GA2/K4、world8、30000/500/100、workers0、F1 synchronous DCP，G0 独立命名空间 `bounded_g0_20261017`。

## 2. G0 冻结合同 / DS 行为证明 / Owner 裁决

| G0 合同 | DS_PRO 现场报告 | 本裁决 |
|---|---|---|
| 8×H100 NCCL + `Config.validate()` + DROID Fresh | 真实torchrun RC0，3次 optimizer update 完成，`Done with training` | DS现场认证，Owner接受；G0内CLOSED |
| 8rank×3step Missing-Gradient Audit | 24/24唯一 `(rank,iter)`，均 `AUDIT_OK`，`audit_errors=[]`，`missing=0`，每rank 314 selected/present（Generation289 + Action5 + Local20） | DS现场认证，Owner接受；G0内CLOSED |
| 稳定性和训练遥测 | rank0 3步 outer/action/vision 有限，`telemetry_errors=[]`，`nonfinite=0`，无CUDA/OOM、3步按设定退出 | DS现场认证，Owner接受；G0内CLOSED |
| F1 DCP 发布与身份 | `iter_000000003/complete.v1.json` `complete=true`，world_size=8，model/optim/scheduler/trainer完整分片、8 rank sidecars、latest指向iter3，侧边哈希一致 | DS现场认证，Owner接受；G0内CLOSED |
| 存储 | G0独立输出24GiB，2026-10-19现场 `/mnt/data1` 报告剩余314.05GiB，目标FS prelaunch T1~T5通过 | G0已完成；G1必须再实时评估 |
| 数据/执行隔离 | G0 `diagnostic_only_do_not_resume=true`，独立namespace；未触碰旧Index8 DCP | 必须保留，G0 iter3 **永不作正式Resume源** |

上表属于 **trusted on-host executor attestation**，并非外部审核者亲自读取所有原始证据。

## 3. 对历史 blocker 的精确处理

- `G0-EVID-01`：关于 `0d770dd0` 本地Root，DS已给本地Git证据，Owner明确接受。**CLOSED_BY_OWNER_ACCEPTED_DS_ATTESTATION**，不再要求Git bundle/evidence branch。
- `G0-EVID-02`：24条raw审计由 DS 现场复算（报告称 tmux 历史中成功run事件24/24、排除早期失败历史），Owner明确接受。**CLOSED_BY_OWNER_ACCEPTED_DS_ATTESTATION**，不再要求将server JSON/log交给GPT。
- `G0-EVID-03`：complete/latest、8rank component/sidecar、SHA256和目标卷由 DS 现场检查，Owner明确接受。**CLOSED_BY_OWNER_ACCEPTED_DS_ATTESTATION**，不再要求将DCP metadata上传给GPT。
- 两份历史 `REQUEST_CHANGES` 审核保留为可追溯记录；本文件是之后的**Owner明确授权的证据接受方式变更与G0 Gate closure**，不是悄悄改写此前GPT独立核验结论。
- **审计能力上限**：源码中的 `AUDIT_OK/missing=0` 主要反映梯度对象存在性；全Slow数值非零/Optimizer moment、Local→Action因果、长程收敛、RoboCasa真实SR及E1可靠性 **不在G0 scope**，不能因G0通过而宣称解决。
- F0/F1/S0历史 CLOSED 保持；旧B1 strict numeric parity FAIL 保持，不能借G0重标成PASS。

## 4. 后续门及协作规则

1. **G0 bounded3：CLOSED。停止针对G0重复索要Git objects、24raw JSON、DCP shard或训练服务器访问权限；不重做已完成GPU/CPU测试。**
2. **G1 Fresh100：仍需单独Owner GPU授权**，新不存在的Job namespace、清晰的Root/Child与`config_digest`冻结、实时8GPU和目标FS/容量检查。G1必须官方DROID Fresh，严禁从G0 iter3恢复；完成后由DS负责现场训练/Evidence真实性核验、GPT审核设计/报告/后续 Gate，而不是人为阻断其无法访问的文件。
3. **协作原则（本项目此类现场证据）**：在 GPT/Codex 均不能访问训练服务器时，Owner 明确授权信任 DS_PRO 作为现场执行/证据见证者。后续审核可以基于其完整、可追溯的现场报告作 Gate 判断；不得把该接受方式伪称为 GPT 自行raw验证。若后续出现实质性矛盾或新的生产 bug 线索，再提明确、有限的专项核查要求。
4. **本 Gate 的 `APPROVE_TO_CLOSE` 不授权** G1、G2、正式30000步训练、仿真/E1、诊断DCP Resume或任何checkpoint清理。
