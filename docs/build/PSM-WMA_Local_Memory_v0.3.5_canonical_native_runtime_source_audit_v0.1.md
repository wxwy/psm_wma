# PSM-WMA Local Memory v0.3.5 Canonical Native Runtime Source/ABI 审计 v0.1

**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-RUNTIME-SOURCE-AUDIT`
**状态**：只读审计完成；待独立三方审核；不授权实现或执行
**设计基线**：root `59bd39f61b3498e56d9824b99059c1566b05b87c` / child `c0e6e55cbab00b7d40eccacc0de1c4c91b66f9d9`

## 1. 结论

结论为 `APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_RUNTIME_IMPLEMENTATION`，但仅表示八项
source/ABI owner 已能被唯一定位并可据此创建下一份 docs-only implementation design；现有
production route 仍在 `omni_mot_model.py:1434` 和 `trainer/__init__.py:520-523` fail-closed，
不能运行真实 native forward、backward、optimizer、GPU 或训练。

## 2. 八项 source/ABI 地图

| 项 | 唯一 source owner | 已证明合同 | 实现设计的 fail-closed 要求 |
| --- | --- | --- | --- |
| 1 model/Local seam | `omni_mot_model.py:136-175,1399-1438` | canonical request 排斥 legacy marker；adapter 只绑定注册 encoder/core；scan 后 native-safe preparation 保持 model batch Local-neutral。 | canonical mode、request、carrier 或 registered canonical module 任一缺失即拒绝；不得走 legacy `_ttt_local_memory_tokens()`（`1133-1192`）。 |
| 2 packer/cardinality/prefix | `canonical_segment_production_adapter.py:79-238,583-609,634-668`；`sequence_packing/sequence.py:163-171,919-922`；`packers.py:246-254`；`cosmos3_vfm_network.py:942-966` | carrier 按 stream-major valid traversal 排除 PAD；owner maps 保存多 vision/action/sound ownership；prefix 是每 consumer `[K_local,D_local]` 或 `None`，projector 输出 hidden prefix。 | 任一 source identity、cardinality、S0 `None`、PAD absence、`K_local` 或 feature dim 不一致即拒绝；禁止 legacy Local GEN span。 |
| 3 planned/actual/N_window | `local_memory_segment.py:109-136`；`canonical_segment_production_adapter.py:706-718` | immutable plan owns positive planned counts 和 `N_window`；objective 前强制 actual=planned；prepare commit 再次校验 gathered count。 | runtime plan 必须在首个 backward 前冻结；不允许 caller 重新计数、`N_window=0` 或 count mismatch。 |
| 4 primary/auxiliary 缩放 | `local_memory_segment.py:133-136`；`canonical_segment_production_adapter.py:304-341`；`trainer/__init__.py:963-972` | primary 仅 `planned_n_valid/N_window`；auxiliary 仅 `1/ga_effective`；native split 将 weighted modality population 归约到 consumer axis。 | implementation 必须保留两个独立系数；普通 full-valid 还原 `(L_consumer+L_aux)/GA`，禁止 shorthand、总 loss 重乘或第二次 GA 缩放。 |
| 5 scaler/optimizer/DDP 边界 | `trainer/__init__.py:524-595,729-780,935-999` | ordinary DDP/no-sync、callback、backward、optimizer、scheduler 和 zero-grad 的唯一顺序已存在；canonical native route仅允许一处无 ordinary `/grad_accum_iter` backward，且当前 hard-stop 禁止 scaler/optimizer。 | 新路线必须在 objective 形成后才接入 scale/unscale/step；未取得 scaler disposition、错误 plan boundary、二次 `/grad_accum_iter` 都 fail closed。 |
| 6 producer/cache identity | `canonical_segment_production_adapter.py:54-205,548-613`；`local_memory_segment.py:18-39,154-162` | carrier 保留 nested raw row、slot/episode/source/cursor identity 和 model-batch object identity；preflight 验证每个 valid row 的 source identity。 | manifest/config/source digest、episode/cursor/terminal 或 raw visual/action evidence 缺失、foreign、重排即拒绝；不得由 model 猜测。 |
| 7 feature/config/optimizer/checkpoint | `config_checkpoint_contract.py:12-108`；`cosmos3_vfm_network.py:227-229,284-291`；`action_policy_libero_edge_all.py:70-102,230-245` | feature config、四组历史 selector、projector/modality注册及 strict payload 检查均有 source owner。 | v0.3.5 的 K/V-only TTT inventory 必须重新冻结；旧 checkpoint/config 不匹配必须 fail closed，不能复用旧 recurrent selector 结论。 |
| 8 persistence/rank/sidecar | `canonical_segment_production_adapter.py:706-768`；`canonical_segment_adapter_scheduler.py:532-603`；`trainer/__init__.py:520-523` | fast commit mutation和rank-local scheduler contract有 owner；当前无 canonical runtime sidecar/save-load integration。 | 首轮 smoke 必须显式声明 mid-episode resume unsupported；无单独 sidecar schema、rank/world/config/manifest/source identity restore owner 时不得声称 resume 或 distributed supported。 |

## 3. 实现设计必须封闭的现状边界

1. `omni_mot_model.py:1434` 在 attach native preparation 后固定抛出
   `canonical-production native forward seam is unavailable`；这是正确的当前硬停止，implementation
   design 必须指定如何接入原生 pack/MoT/loss，不能删除后直接运行。
2. `trainer/__init__.py:520-523` 在 canonical production mode 下拒绝 enabled scaler 或真实
   optimizer；implementation design 必须定义已形成 objective 后的等价时序和失败处置，不能解除
   guard 即进入普通 `loss / grad_accum_iter` 分支。
3. `omni_mot_model.py:1133-1192` 是旧 lifecycle 的 row-wise 路线；canonical production mode
   在 `136-157` 已与其 marker 隔离。新实现必须维持此隔离。
4. `config_checkpoint_contract.py:12-17,45-60` 仍列出旧 recurrent backend selector；按 v0.3.5
   K/V-only continual TTT 语义，feature/config/optimizer/checkpoint refreeze 必须在 CPU/static
   implementation 后、GPU smoke 前独立完成。

## 4. 审计证据与后续顺序

本审计仅读取 source/documentation；没有执行 Python、真实 data/cache/checkpoint I/O、CUDA/GPU、
torchrun、native forward/loss/backward、optimizer/scheduler、训练、评测、推理或 LIBERO4IN1。

后续严格为：runtime implementation design → CPU/static implementation → feature/config/optimizer/
checkpoint refreeze → single-GPU smoke design/approval → single-GPU smoke → runtime-sidecar design →
CPU/static verification → resume smoke → LIBERO4IN1 matched-smoke design/approval → matched smoke →
formal-training design/command approval → formal training。
