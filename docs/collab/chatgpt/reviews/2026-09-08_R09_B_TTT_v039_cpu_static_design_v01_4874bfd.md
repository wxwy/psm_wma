# ChatGPT 独立审核 — canonical CPU/static implementation design v0.1

日期：2026-09-08

## Verdict / formal target

**REQUEST_CHANGES**

- Gate：`G0-R09-B-TTT-V035-CANONICAL-CPU-IMPLEMENTATION-DESIGN`
- Formal root design SHA：`4874bfd223606e4d3b9335c4bc2490a088011c78`
- 实际 root tree 的 child/Gitlink：`80aec090688e3c710c41e1dfd86b6500773db2c7`
- 起始远端 V2 HEAD：`afa5af926ea902ab083af6437ad2a1327cc4eb61`，仅 request/bookkeeping。
- 前置 semantics formal root：`e4b2d2f980ce0f038ae1a44ed379d16bbf05b9d9`。
- 前置 review：`docs/collab/chatgpt/reviews/2026-09-08_R09_B_TTT_v035_canonical_semantics_v039_e4b2d2f.md`。

这是新 Gate 的首轮实现设计审核，不是上一 semantics Gate 的重复审核。上一 retry MEDIUM 已 CLOSED，不作为当前 blocker。

## 核查范围

核对最新 canonical Inbox、formal commit 全部实际 diff、前置 formal target 至当前 compare、实际 root tree Gitlink、88 行设计全文，以及本会话已读取且 diff 证明未变的 v0.3.6–v0.3.9 合同、前序 review、root AGENTS/执行治理技能。进一步读取 child AGENTS、直接相关 local_evidence.py、trainer/__init__.py 和 action_sft_dataset.py 的实际实现。

root technical delta 仅新设计，SESSION/TODO 和 review/Inbox 为流程记录；child 未变。没有运行项目代码/测试、GPU 或真实数据/模型/checkpoint。以下是设计与既有接口的接缝问题，不是对本 Gate 尚未实现代码的测试失败报告。

设计文件简称 D：
`docs/build/PSM-WMA_Local_Memory_v0.3.9_cpu_static_implementation_design_v0.1.md`。
child 文件行号均绑定上述 child SHA。

## 当前 blockers

### NEW B1 — HIGH — 声称复用的 scan 在 valid 分支前投影 PAD/S0

- **file:line**：D:56、D:57；关联 D:47。
- **实际代码证据**：`cosmos_framework/model/generator/mot/local_evidence.py:592`–599 对每个 timestep 调用 step_many；:549 在传入 valid 判断前对整个 evidence_t 调用 project_evidence；:373–384 对全 batch 读取、检查有限性并进行 K/Q/V projection；直到 :483–488 才跳过 invalid row。
- **根因**：设计只承诺 encoder 按 evidence_valid 选行，却指定按 [B,T] 调用现有 scan_segment_many；encoder 之后的 dense invalid 行仍会被 core 投影。填零仍会执行带 bias 的 projection；保留不可读取填充值则可能在 mask 生效前被有限性检查拒绝。present=False 或未 write 不能证明未读取/未投影。白名单里的“batched scan seam”没有明确覆盖这个实际复用行为。
- **违反 frozen contract**：v0.3.6 §2 明确要求按 evidence_valid 先分支，invalid dense storage 不得编码或投影；§9 C 要求 PAD 不 encoded/updated/emitted/gathered/counted。D:47 同样承诺 PAD 不进入 evidence/read/loss。
- **可验收修复条件**：冻结 canonical seam 在任何 evidence-dependent finite check/K/Q/V projection/read/write 前排除 invalid 行的确切接口和修改范围，明确与旧 scan 回归路径的关系。CPU acceptance 必须覆盖混合 valid/PAD/S0 batch、全 invalid timestep，直接观察 encoder/core projection/read/write 的实际参与行，验证 invalid payload 未访问且 committed fast state 不变；不能只断言 present=False。本意见只要求设计明确合同，不授权现在修改代码。

### NEW B2 — MEDIUM — SegmentBatch 声称完全继承但删去 consumer_payload

- **file:line**：D:31、D:34–42；关联 D:58–59。
- **根因**：v0.3.6 §2 的冻结 ABI 包含 `consumer_payload`，本设计却以 `consumer_action[B,T,10]` 取代而未定义等价映射或外部 payload authority。96 维 summary 与单个 10 维 action 不能定义 native consumer condition/target payload。设计因此没有冻结 valid gather 如何保持 payload、Local token 和 slot/episode/source identity 的一一对应。synthetic doubles 也需服从同一 schema，不能默默抹去该字段。
- **违反 frozen contract**：v0.3.6 §2 SegmentBatch 字段、§3 stream-major flatten/gather、§6 native consumer loss、§9 D identity-preserving gather；D:31 自称“完全一致”，没有授权 ABI supersession。
- **可验收修复条件**：恢复或明确等价的 consumer_payload ABI/所有权，说明 consumer_action 是否额外字段及用途，冻结 consumer payload 与 Local None/token 共用的 valid gather 顺序和 identity 绑定。增加 synthetic 非平凡 payload 的 flatten/gather round-trip 断言，验证 S0 consumer 保留、PAD 排除、payload/Local/identity 不错配。无需真实 model I/O 或实现 model forward。

### NEW B3 — MEDIUM — 两个批准 literal 对应不同授权阶段

- **file:line**：D:86–87；对照当前 canonical Inbox 的 CPU/static implementation design request。
- **根因**：申请请求 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_CPU_STATIC`，D:86 却用前置 semantics Gate 的 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_CPU_DESIGN` 授权白名单代码实现。该旧 literal 原只授权“新建 implementation design”，两者不可互换；即使要求同 SHA，当前 Gate 的批准信号仍不唯一。
- **违反 frozen contract**：v0.3.9 §4 的前置批准边界、当前 Gate 申请的 literal、精确 Gate/scope authority 原则。
- **可验收修复条件**：在新版本中统一 Gate ID、exact literal 与其唯一授权范围，并同步申请；前置 semantics literal 仅作为 prerequisite。不得由旧 Gate verdict 推导当前代码实现授权。

## 其他已核对与边界

- v0.3.9 plan-chain retry invariant 被继续继承；历史 MEDIUM 保持 CLOSED。
- 实际 B2ManifestAwareIterableDataset:125–143 是 num_workers=0 的有序 sample iterator，先加载 dataset item 再验证 identity；它不是现成 metadata-only scheduler。后续实现仍须遵守 frozen metadata planning/no real I/O，不能把整个真实 iterator 的行为视为 CPU double 已证明。
- 实际 trainer:494 为统一 /grad_accum_iter，:495–506 仍关联旧 lifecycle，:509–521 为固定 GA step。当前设计声明 helper 不接入 loop；本审核不授权借 loss seam 改造这些 production lifecycle/step 行为。
- 本轮未发现 child scope 实际越界，因为尚无 child 改动；批准前不得开始白名单实现。

当前合计：**1 HIGH + 2 MEDIUM，均为 design blockers**。不是 tests-only remediation，不得将 production 已无 blocker 作为结论。

详细 review 与 canonical Inbox 同时持久化后才形成正式 REQUEST_CHANGES。当前 Gate 不关闭；不授权白名单代码、production wiring/config/optimizer/checkpoint、真实 preflight/staging/record/refreeze/export/compose、GPU/CUDA/torchrun、真实 model/data/cache/checkpoint I/O、训练/评测/推理、P4/P5、B2-T、LIBERO4IN1 或其他后续 Gate。Review/bookkeeping SHA 不改变 formal target。
