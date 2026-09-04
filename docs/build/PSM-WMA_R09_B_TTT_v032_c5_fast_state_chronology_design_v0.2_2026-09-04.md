# PSM-WMA R09-B TTT v0.3.2 C5 fast-state transition 设计 v0.2

**日期**：2026-09-04  
**状态**：替代 v0.1；design-only，需三方同 SHA 审核  
**上游**：`PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.2.md`

## 1. 重新限定的 Gate

C5 是**单个已准入 causal transition 的 persistent fast-state CPU contract**，不是 episode/rollout chronology authority。它只证明：一次有效调用对给定的、已由上游 R08 admission 证明为 completed causal evidence 的 `evidence_t:[B,256]`，恰做一次 K/V write，随后从更新后的 state 读取 `K_local` 个 token。

本 Gate 不能从裸 tensor 判断 future/GT provenance、重复、重排或跨 owner state substitution；不得声称能够拒绝这些调用。它不接受 `[B,H,256]`，以防实现层自行重放 history；上游 caller 仍须保证每个 admitted transition 只调用一次。

在 C6 前新增强制的 `C5A-CHRONOLOGY-OWNER-SEGMENT-DESIGN`：冻结 episode/rollout owner identity、transition/segment offset、retry/replay、state owner、training segment materialization 与 trainer `backward()` 原子边界。未关闭 C5A 不得进入 config/checkpoint、GPU 或训练。

## 2. C5 输入、输出与闭合计数状态机

```text
state_in: ContinualTTTFastState | None
evidence_t: [B,256]
valid_t, done_before_t: [B] bool
counter_in: [B] int64
N = ttt_tbptt_steps > 0, default 16, configurable

tokens_t: [B,K_local,32], state_out, present_t:[B] bool, counter_out:[B] int64
```

所有行输入先满足 `0 <= counter_in < N`；`state_in is None` 时所有 `counter_in==0`。shape/dtype/device/nonfinite、负计数、`counter_in>=N` 或初始化非零计数必须在投影和 update 前拒绝。

逐行顺序为：

1. `done_before_t` 行先 whole-pytree reset 到 learned W0，计数置零；其他行不变。
2. `valid_t=false`：无 write/read，输出精确零、`present=false`，计数不变（但保留本行已发生的 reset）。
3. 有效行：一次 `theta_K/theta_V` KVB write，随后仅从更新后的 state 用 `theta_Q+r_k` 做 `K_local` reads；`present=true`。
4. `c1=c+1`。若 `c1==N`，token 保留本步 pre-detach outer gradient，state 只对该行 row-selective detach，`counter_out=0`；否则 state 为更新值，`counter_out=c1`。

故 `N=1` 时每次有效调用都返回更新后 readout、数值相同的 detached carry state 与零计数。`N` 是梯度截断长度，不是 state horizon 或 reset 周期。

## 3. 实现与验收边界

获 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_C5_FAST_STATE_TRANSITION_CPU` 后，仅允许改 `local_evidence.py`、`local_evidence_test.py`，合成 CPU tensor。验收必须覆盖：连续 transition carry、一次 write/更新后 read、K=1、逐行 reset/invalid isolation、`N=1/16/非默认`、row-selective detach 数值与图边界、counter 全部 fail-before-projection 路径、slow parameter gradient reachability 和 fast state 非 `named_parameters()`。

禁止 Cosmos forward/packer/attention、config/optimizer/checkpoint/trainer/inference/parallelization、`MemoryState` 混用、GPU/真实 I/O/训练。C5A、C6、C7、C8、C9 仍各须独立设计与三方审核。
