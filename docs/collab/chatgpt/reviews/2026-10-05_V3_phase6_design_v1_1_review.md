# V3 Corrected Phase6 online inference / simulator / evaluation design v1.1 — GPT formal review

- 日期：2026-10-05
- Gate：V3-CORRECTED-PHASE6-DESIGN
- formal design root：`5c2435eaffc8565e54fe7fc780c75a00ff9675d9`
- production child/Gitlink：`b673ceda5a9ff058abb31224b7006f2d87771ad2`
- Phase6 design：`docs/build/PSM-WMA_V3_phase6_online_inference_eval_design_v1.1_2026-10-05.md`
- superseded candidate：Phase6 v1.0 root `a05ac63073fda096687443ede0b778454fd78a70`
- scratch implementation parent authority：`afb9ca8d9f8ec080518a838f56a681073eb4b495`（Phase4/5 debug scratch closed tree）

## Verdict

`APPROVE_PHASE6_DESIGN_V1_1_FOR_SCRATCH_IMPLEMENTATION`

`PHASE6_REAL_PARITY_GPU_SIM_NOT_AUTHORIZED`

`PRODUCTION_PROMOTION_STILL_BLOCKED_BY_PHASE3P5_THRESHOLDED_REAL_PARITY`

本 verdict 只允许 Phase6A CPU/static/debug implementation 在独立 scratch descendant of `afb9ca8...` 中进行；不允许修改 production child/Gitlink，不允许 ds 启动 Phase6 real Wan parity、server GPU smoke、RoboCasa simulator 或 SR screening。

## Review findings

1. **Corrected visual authority 已与 v3.0 / Phase0 mapping 对齐。**
   - active Local 不再使用 B1 separate-camera causal endpoint / mean+RMS；
   - wire 只携带 completed pre-action `left|wrist` composite；
   - server-side independent `T_pixel=1` Encode1 是 correctness 默认；
   - policy current-z callback 明确降为 optional optimization，不是实现前置 seam。

2. **Phase6 v1.0 的 preprocessing-identity 缺口已在 v1.1 关闭。**
   - `image_size` 与 `preprocess_profile` 进入 Local request / replay identity；
   - session 内 silent geometry/profile drift 必须 fail-closed；
   - Policy/Local 共享同一 spatial preprocessing helper；
   - repeat-before-pad 与 pad-before-repeat 必须做 byte-equivalence 证明，避免 refactor 改变 Policy 输入。

3. **Encode1 parity 被正确拆成独立 Phase6 Gate。**
   - 现有 Phase3.5 observational `max_abs=0` 只证明 cache Encode17 vs online Encode17，不被误写成 Encode1 已通过；
   - v1.1 要求三方 witness：
     A=cache actual-window `Z_t[0]`；
     B=independent Encode1(current composite)；
     C=server repeated-current Policy visual tokenizer encode 的 first latent；
   - A/B/C + visual96 都需数值比较；
   - threshold 必须在 observational run 后冻结，不以因果性直接假定 exact equality；
   - 该 debug Gate 不替代 Phase3.5 production thresholded parity。

4. **Completed-evidence chronology 修正正确。**
   - 当前 evaluator 的 pre-`env.step` `record_executed` 被明确列为 blocker；
   - corrected contract 只允许 `env.step` 成功返回后推进 consumer frontier；
   - decoder/env.step failure 均为零 evidence 发布；
   - done/success 在成功 step 后出现时，该动作仍是 completed evidence；
   - predicted-but-unexecuted chunk tail 永不进入 Local。

5. **executed raw15 authority 正确落在 post-decoder canonical command。**
   - 保留官方 `decode_15d_to_env12` 为唯一 env action authority；
   - new wrapper 同时返回 exact submitted env12 与 canonical executed raw15；
   - canonical raw15 必须重新 decode 回相同 env12；
   - 明确覆盖 rot6d orthogonalization、mode threshold、base zero/clip、gripper clip；
   - 禁止通过机器人 post-step 物理 pose 反推 action。

6. **Online Local fast-state transaction 可复用但 required route 已禁止 direct-core fallback。**
   - 保留 `OnlineLocalMemory` session/prepare/commit/abort/reset/replay；
   - required Corrected RoboCasa 必须注入 model-owned `scan_local_memory`；
   - scan 不可用时 fail-closed；
   - FSDP model-owned boundary 继承 Phase4，不允许在 adapter 外调用 `core.initial_state`。

7. **H_pred / R / T 独立性被落实到 online implementation contract。**
   - runtime 只约束 `1 <= R <= H_pred`；
   - 不添加 `R<=T`；
   - evidence N>T 时按 T 顺序分块、carry detached W、禁止 reset；
   - final prefix/state/telemetry 与 per-step scalar reference parity 是 formal CPU acceptance。

8. **Replay/reset/memory-bounded semantics清晰。**
   - lost-response replay 必须 exact same frontier/composite/action/profile；
   - replay 不重复 Encode1 / fast update，`encoded_steps=0`；
   - changed bytes same frontier fail-closed；
   - client 只持有 unacknowledged evidence；
   - server 不保留 episode causal VAE history；
   - reset 清除 fast/token/replay witness，跨 episode泄漏被禁止。

9. **Server seam保持最小。**
   - 保留已有 `prepare -> generate(prefix) -> commit / exception abort`；
   - Local required 仍先保持 serial `/predict`；
   - `/predict_batch` required-mode batching延期，不在 first Gate 扩大并发 transaction scope；
   - off-mode 必须证明零行为回归。

10. **Phase6 implementation scope合理且边界清楚。**
    - scratch 必须从 clean `afb9ca8...` descendant 开始；
    - allowed files限定于 online Local adapter/contract/helper、server minimal preprocessing seam、sim client/eval decoder/evaluator/tests；
    - Phase1A/B/2/3、checkpoint/DCP、trainer/resume、optimizer、FSDP、attention、memory_prefix 应保持零 diff；
    - historical B1 files保留历史但 corrected active modules不得 import。

## Phase6A implementation authorization

cx 现在可在独立 scratch worktree中实现 design §21–22，仅限 CPU/static/debug contracts。

必须至少完成：

- corrected wire / old-B1 reject；
- shared spatial preprocessing；
- T=1 Encode1 helper（可 mock/fake tokenizer 做 CPU contract；不得启动 real GPU parity）；
- client post-step completed ledger；
- canonical raw15/env12 wrapper与 round-trip tests；
- OnlineLocalMemory N>T chunking；
- replay/reset/transaction；
- server required/off mode regression；
- no-B1-import / forbidden-file diff；
- Ruff/format/py_compile/diff-check。

实现完成后形成新的 scratch SHA，由 GPT fresh source review。

## Still blocked

以下均未授权：

- Phase6 Encode1 real Wan parity；
- server GPU smoke；
- simulator 48/128-step；
- 18-task screening / SR；
- Phase5/6 scratch promotion；
- root Gitlink change；
- formal training/GPU readiness。

Phase3.5 production thresholded Gate仍单独 OPEN；本 review 不构成 waiver。

