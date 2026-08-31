# REVIEW G0-R09-B-SOURCE-AUDIT / B0 TTT CPU backend(Kimi)

- 日期:2026-08-30
- 对象:子模块 `9114afc`(`local_evidence.py` 新增 `TTTLocalMemoryBackend`、`local_evidence_test.py` 新增 contract 测试);根仓 `c0d6936`(`tools/g0/verify_r09_b0_ttt_contract.py`、`artifacts/g0/r09/b0_ttt_contract.json`)
- 依据:`docs/build/PSM-WMA_R09_B_TTT_preflight_runbook_v0.2_2026-08-30.md` §3 PASS/FAIL 合同、`docs/build/PSM-WMA_R09_B_TTT_source_audit_v0.1_2026-08-30.md` 获批候选值

## 结论:REQUEST_CHANGES(仅测试/证据覆盖,实现行为经独立探针验证正确)

## 独立复验(已执行)

- `pytest local_evidence_test.py -k ttt`:1 passed。
- 复跑 `verify_r09_b0_ttt_contract.py`,产物与 `b0_ttt_contract.json` 逐字段一致(除 tool SHA),status=PASS。
- 数值/合同核对:state 五元组 shape/dtype/bytes 与 audit :52-60 一致(18,953 B);SGD lr=0.1、segment_steps=4、MSE(W@e, stopgrad(e[:32])) 与 audit :18-24 一致;two-segment 逐位等价 max_abs=0;detach、无 named_parameters、all-mask absent 均符合。
- Kimi 额外 ad-hoc 探针(未入仓):batch permutation 不变性 PASS;cross-sample isolation PASS;all-mask continuation 保持 present/token PASS(修正对照后 `torch.equal` 成立)。

## 问题(按严重级)

1. MEDIUM — 合同要求的三个行为没有入库测试/artifact 证据。runbook v0.2 :27 把 batch permutation、cross-sample isolation 列入 PASS 必备,audit :27 要求 all-mask continuation 保持 present 与 token;`local_evidence_test.py:117-132` 仅覆盖单有效样本 + 全 mask 样本,三者均缺少定向断言。实现行为已被 Kimi 探针证明正确,只需把探针固化为测试,不需改实现。建议位置:`local_evidence_test.py` 新增 permutation/isolation/all-mask-continuation 三个 case,或在 verify 工具 checks 中补充对应字段。
2. MEDIUM — partial reset 语义未定义也未测试。runbook v0.0.2 :27 要求 partial/full reset 分别通过;`TTTLocalMemoryBackend` 只有整批 `state=None` 全量重置路径(`local_evidence.py:210-211`),无按 sample 部分重置 API。请明确 B0 范围:若 partial reset 属 runtime wrapper 职责(如 R08 的 presence-reset 语义),在 audit/runbook 注明豁免;若属 B0,补 API 与测试。
3. LOW — `verify_r09_b0_ttt_contract.py:30` 的 `bytes_limit_pass` 是与获批常量 18,953 的等值断言,正确但与 audit 耦合为魔法数;建议注释引用 audit :24 来源行,防未来 dtype/shape 变更时双处漂移。

## 不误报说明

- 首轮探针曾显示 all-mask continuation token 变化,系 Kimi 对照组写错(对照 replay 含 2 个有效步);修正后 `torch.equal` 成立,不计为问题。
- `verify` 工具中 `split`/`split_present` 变量复用覆盖(行内第二次赋值)无害,不计。

## 关闭条件

- 问题 1/2 的测试或豁免注明入库并通过;问题 3 注释补充。之后 Kimi 转 APPROVE。
