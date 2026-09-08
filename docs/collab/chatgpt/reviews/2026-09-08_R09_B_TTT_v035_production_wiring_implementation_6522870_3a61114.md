# ChatGPT 独立 production wiring CPU/static remediation review

Formal reviewed pair:
- root implementation SHA: `6522870454f30ed38cbd76c028042188f62aee96`
- child/Gitlink SHA: `3a61114939e7724e93f1b0860ffe662c19ce3c88`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-WIRING-CPU-STATIC-IMPLEMENTATION`
- frozen design authority: root `e68fd83023c6c9877f18f7c34cff13f97b9b93b7`, `PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.6.md`, inheriting v0.5/v0.4 whitelist, selector, plan, Local-only grad owner, spy and existing-backward-seam contracts.

Verdict: `REQUEST_CHANGES`

## Incremental scope

本轮仅审核上一正式实现 `b6fff64cd06ab20f9ef732ca429e1b9bc603f70c` / `41d0a49cc7275f53efbc375e04b5f7dcb5c7b701` 到当前 formal pair 的增量，并重新核对前序三个 blocker 与冻结 v0.6 contract。child remediation 仅修改六个已授权路径：production wiring/fixture、model marker/fixture、trainer canonical branch/fixture；未发现越出 v0.5 八路径 child whitelist 的改动。root implementation 仅更新 `SESSION.md`、`TODO.md` 与 Gitlink。

## 前序 blocker closure

1. **CLOSED — exact `CanonicalSegmentWiring` capability identity.** `cosmos_framework/model/generator/mot/production_segment_wiring.py:13-46`; `cosmos_framework/trainer/__init__.py:607-633`; `cosmos_framework/trainer/trainer_canonical_segment_wiring_test.py:50-74`. `CanonicalSegmentForward` 现在冻结 `wiring`，trainer 在 delegation/backward/commit 前要求 `forward.wiring is wiring`，same-adapter/different-wiring substitution 因而 fail closed。

2. **CLOSED — S0 actual marker→trainer autograd path.** `cosmos_framework/model/generator/mot/production_segment_wiring.py:53-69`; `cosmos_framework/model/generator/omni_mot_model.py:1263-1303`; `cosmos_framework/trainer/trainer_canonical_segment_wiring_test.py:12-33`. S0 无 visible Local payload 时，spy 通过 exact Local slow-owner 的零系数 graph anchor 保持 scalar graph-bearing；positive fixture 由真实 `OmniMoTModel.training_step` marker route 产生 output，再进入真实 `_run_canonical_segment_backward` 并完成 transaction/commit，不再用手工 primary 绕过 model helper。

3. **CLOSED — prior mandatory negative/selector matrix omissions.** 当前相邻 fixtures 已覆盖 enabled marker precedence + legacy-uninvoked、disabled native-path precedence、missing capability、same-adapter substitute wiring、external plan、stale result 以及 exact success。静态 identity guards 对 mismatched/stale result 均在 delegated seam 前拒绝。

## Current blocker

1. **HIGH — remediation changes the inherited non-S0 consumer-loss semantics by counting every visible Local token twice.** `cosmos_framework/model/generator/mot/production_segment_wiring.py:64-68`.

   Current code is logically:

   ```text
   present_tokens = non-None forward.locals
   local_sum = sum(present_tokens, start=all_local_tokens.sum())
   ```

   For any non-S0 valid consumer, `forward.locals` already contains the corresponding slice(s) of `forward.result.local_tokens`. Therefore `all_local_tokens.sum()` contributes those Local tokens once, and the subsequent `present_tokens` sum contributes the same visible tokens again. With an all-valid non-S0 segment, the spy changes the primary from the pre-remediation `Σ visible_local` to `2 * Σ visible_local` (PAD/absent rows do not repair this).

   This is not authorized by v0.6. The frozen v0.6 states that it only supplements the model→trainer capability/data ABI while preserving v0.5; v0.5 preserves the v0.4 in-memory spy and existing weighted-loss/backward authority. v0.4 freezes the outer formula as `L_i=(N_valid_i/N_valid_window)*primary_consumer_mean_i + auxiliary_loss_i/GA_effective` with no second loss authority. Doubling the primary before that seam changes the CPU/static contract rather than merely making S0 graph-bearing.

   The current S0 fixture does not expose this regression because S0 has no Local payload and its masked `all_local_tokens` value is zero; `test_s0_test_spy_remains_graph_bearing` therefore only exercises the new graph-anchor case. No current fixture asserts that a non-S0 primary equals the visible consumer Local contribution exactly once.

   **Acceptance:** preserve the pre-remediation visible-consumer scalar for non-S0 consumers exactly once, while keeping S0 numerically zero-valued but graph-bearing through an allowed zero-coefficient anchor. Add an adjacent CPU/static witness with at least one non-zero non-S0 visible Local token that asserts the exact primary scalar (and the actual marker→trainer path), so a duplicate contribution cannot pass. Re-run the declared target suites/regressions plus target `py_compile` and child/root `git diff --check`. Any resulting new child/root implementation SHA requires fresh same-pair review.

## Scope boundary

No production-wiring closure is granted for this formal pair. This review remains limited to the frozen CPU/static synthetic wiring Gate. It does **not** authorize persistent runtime-sidecar/resume, real data/cache/checkpoint I/O, config/default/registry/optimizer/dataset/manifest changes, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T, or LIBERO4IN1.
