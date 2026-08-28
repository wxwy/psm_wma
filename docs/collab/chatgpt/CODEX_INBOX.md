# ChatGPT → Codex Inbox

This file is the **single append-only handoff entrypoint** for messages that ChatGPT wants Codex/other project agents to see.

## Usage

- Before starting or continuing implementation/review work, read the **latest entry at the bottom of this file**.
- Do not rewrite or delete previous entries.
- Substantive reviews may have a detailed file under:
  `docs/collab/chatgpt/reviews/`
- The Inbox entry remains the authoritative short handoff: verdict, blockers, required next action, and link to detailed review.
- If a newer entry supersedes an older one, it must say so explicitly.
- Codex does not need to edit this file to acknowledge; record execution status in the normal `SESSION.md` / `TODO.md` workflow.

---

## 2026-08-28 — R08 Gate-0 diagnostic review @ a3d11a8

**Verdict: REQUEST_CHANGES**

**Do not run Gate-0 GPU yet.**

Target:
- root: `a3d11a8ccae47e93df61655b0b2f5d959cd87f9a`
- submodule: `10bc41085de448d60d2f71b342c03a4cfcca9ee1`

Required fixes before GPU:
1. HIGH: wrap Wan VAE encoding in `torch.inference_mode()` / no-grad and detach CPU sidecars; current code can retain autograd graphs across 64×2 VAE forwards.
2. MEDIUM: enforce deterministic VAE runtime and preferably add same-input repeat control.
3. MEDIUM: make task/episode coverage real, not only episode-first selection with a task-diversity comment.
4. MEDIUM: freeze canonical PASS threshold at <=1e-6; CLI must not be able to loosen the Gate arbitrarily.

Recommended:
- persist first-frame/suffix input fingerprints and changed-pixel counts;
- optional runtime-A-z0 vs existing cache-z0 sampled parity.

Detailed review:
`docs/collab/chatgpt/reviews/2026-08-28_R08_Gate0_a3d11a8.md`

Next:
- CPU/static-only fixes
- new commit SHA
- re-review by ChatGPT/mm/Kimi
- GPU Gate-0 only after approval


---

## 2026-08-28 — R08 Gate-0 diagnostic re-review @ 8778b7e

**Verdict: APPROVE_TO_RUN_GATE0_GPU**

Target:
- root: `8778b7e3d0504040dd12b1eddaa9fabe32b69759`
- submodule: unchanged `10bc41085de448d60d2f71b342c03a4cfcca9ee1`

Previous blockers are closed:
1. VAE encode now uses `torch.inference_mode()`; retained z0 tensors are detached CPU tensors.
2. Deterministic runtime is enforced and recorded; same-input repeat control is present.
3. Anchor selection now has explicit task/episode stratification and machine-readable coverage.
4. Canonical threshold is frozen at `1e-6`; unrestricted `--atol` is removed.
5. Input first-frame/suffix fingerprints and changed-pixel evidence are persisted.

Important runtime interpretation:
- `PASS_STRICT_BITWISE` is a strong causal PASS candidate.
- `PASS_TOLERANCE_ATOL_1E-6` does **not** close Gate-0 by status string alone; independent review must verify there is no stable/systematic suffix-dependent nonzero signal.
- `FAIL` must follow the R08 supplement fallback route; exact-window z0 must not be used as causal historical evidence.

Next:
- Codex may run the **Gate-0 GPU diagnostic only**, after the normal D005 launch disclosure.
- Preserve JSON + raw z0 sidecar through independent runtime review.
- Do not start R08 Step 2/history/model/R09 before runtime Gate-0 review closes.

Detailed review:
`docs/collab/chatgpt/reviews/2026-08-28_R08_Gate0_8778b7e.md`


---

## 2026-08-28 — R08 Gate-0 scope adjustment

**Decision: downgrade Gate-0 from a research hard gate to a one-time Wan z0 causal-contract sanity check.**

Reasoning:
- Wan2.2 official design is a causal VAE and encodes the first frame as the key-frame prime before later temporal chunks.
- The current Cosmos Wan2.2 wrapper follows the same causal/key-frame-prime contract.
- In the existing closed-loop simulation path, inference does not have access to true future RGB suffixes, yet the model still predicts/controls effectively; this is strong engineering evidence that the useful current representation is not materially dependent on future frames.
- Therefore the main uncertainty is no longer “is Wan z0 causal?”, but only whether our specific Cosmos wrapper / exact-duration / chunking / bf16 / runtime path accidentally violates the official causal contract.

Execution guidance:
1. The already-reviewed `8778b7e` diagnostic may still be run once because the tooling is complete.
2. Treat it as an integration/regression sanity check, not as an exploratory algorithmic Gate.
3. If it PASSes, do **not** add more z0 causality experiments; immediately proceed to R08 history alignment.
4. If it unexpectedly FAILs, first investigate wrapper/chunking/runtime/config differences; do not conclude that Wan2.2 itself is non-causal.
5. Future documentation should prefer wording such as:
   `Wan z0 Causal Contract Sanity Check`
   instead of
   `Historical Visual Representation Causality hard Gate`.

The real R08 hard causality/leakage checks should focus on history construction:
- history visual indices strictly `< t`;
- history executed-action indices strictly `< t`;
- no current target action chunk leakage;
- no predicted/unexecuted action leakage;
- same-episode identity;
- state/action/visual timestamp alignment;
- episode-boundary correctness;
- padding/mask correctness;
- no DataLoader cross-sample contamination.

This scope adjustment does not revoke the prior approval to run the existing diagnostic once; it only changes its interpretation and prevents further over-investment in a property already guaranteed by the upstream architecture.


---

## 2026-08-28 — R08 Wan z0 sanity runtime review @ e7fb1ec

**Verdict: APPROVE_TO_CLOSE_SANITY_CHECK**

Result:
- `artifacts/g0/r08/gate0_z0_suffix_invariance.json`
- `PASS_STRICT_BITWISE`
- 128/128 A-vs-B z0 bitwise identical
- 128/128 A-repeat bitwise identical
- all `max_abs = 0`
- all tensors finite
- every A/B first-frame fingerprint identical
- every suffix fingerprint different
- minimum changed suffix pixels: 2,166,741
- minimum suffix max pixel delta: 218
- 4 suites × 4 remainder classes × 8 anchors, with 8 unique tasks/episodes per class

Provenance note:
- runtime root commit is `5ff9327`, not `8778b7e`;
- verified diagnostic script blob is identical at both commits:
  `6ab4487e5151e7082a50d9417a56c0b40a773ec0`;
- intermediate commits only changed ChatGPT review/inbox docs, so reviewed code == executed code.

Sidecar:
- local raw sidecar SHA256 recorded as
  `154f18cd8de9e0a065ef9c766649550b6e456723a3a72b708a3dfb22b9d96e5f`;
- keep it until mm2/Kimi runtime review also closes.

Interpretation:
- This closes the one-time **Wan z0 Causal Contract Sanity Check** on the ChatGPT side.
- Do not add more z0 causality experiments.
- The next real R08 hard checks are history alignment/leakage: strict `j<t`, executed-action boundary, no target/predicted-action leakage, same episode, timestamp alignment, episode boundary, mask/padding, and no DataLoader cross-sample contamination.

Next:
- wait for mm2/Kimi runtime review closure;
- then mark the old Gate-0 item DONE/closed as sanity check and proceed directly to R08 Step 2 causal history dataset/alignment.

Detailed review:
`docs/collab/chatgpt/reviews/2026-08-28_R08_Gate0_runtime_e7fb1ec.md`


---

## 2026-08-28 — R08 Step 2 causal-history contract review @ root 94a95c6 / submodule 31983c5

**Verdict: REQUEST_CHANGES**

Scope is otherwise good and remains CPU/data-contract only, but one HIGH integration bug blocks Step 2 closure.

### HIGH — `history_action` collides with existing native Action semantics

New R08 dataset output uses normalized historical evidence key:

`libero_lerobot_dataset.py:518 -> "history_action"`

But existing `ActionTransformPipeline` already treats `history_action` as a reserved native Action-conditioning field:

`transforms.py:746-760`

It pops the field, prepends all H rows to the native Action stream, changes `action_length` / `num_history_actions` / `SequencePlan`, and then sends the modified tensor through `ActionProcessor`.

Therefore H>0 R08 history currently does **not** remain Local-only and violates the frozen R08/R07 boundary.

Required:
1. do not change the existing native `history_action` feature;
2. rename R08 normalized evidence to a Local-specific key such as `local_history_action`;
3. future LocalEvidenceEncoder must consume that Local-specific key;
4. add a transform-level CPU regression proving H>0 R08 history leaves native current Action length/content and SequencePlan unchanged.

### MEDIUM — permanent Step 2 tests are missing from the commit

`31983c5` contains only dataset/factory code changes, no committed tests. Add focused CPU tests covering at least:
- H=0 disabled;
- H=16 at anchor t=0: all padding/no cross-episode;
- H=16 t=3 partial;
- H=16 t>=16 full;
- H=1 immediate history;
- action conversion/normalization parity;
- last historical action source t-1 vs first current target t;
- same-episode state/action/visual alignment;
- mask/padding correctness;
- transform-level proof that R08 history does not enter native Action/SequencePlan.

No GPU is needed.

Next:
- keep Step 2 in REVIEW;
- CPU/static-only fix;
- push new submodule SHA + root Gitlink;
- re-review by mm2/Kimi/ChatGPT;
- do not proceed to LocalEvidenceEncoder/readout/model/R09/GPU.

Detailed review:
`docs/collab/chatgpt/reviews/2026-08-28_R08_Step2_94a95c6_31983c5.md`


---

## 2026-08-28 — R08 Step 2 fix re-review @ root 90fc40e / submodule a0f26dc

**Verdict: APPROVE_TO_ADVANCE_STEP3**

The prior HIGH blocker is closed:
- R08 executed-action evidence now uses `local_history_action_raw` / `local_history_action`;
- existing native `history_action` semantics are untouched;
- committed transform regression proves Local history does not alter native current Action length/content or SequencePlan.

Permanent CPU tests now cover:
- H=16 t=0 all-padding;
- H=16 t=3 partial;
- H=16 t=16 full;
- H=1 immediate history;
- raw/normalized action parity;
- state row parity;
- transform isolation.

No new Step 2 code blocker found.

### Important scope ruling

Do **not** widen Step 2 to Edge recipe/runtime wiring.

The R08 supplement §23 explicitly separates:
- Step 2: causal history dataset contract, CPU only;
- Step 3: alignment tests;
- Step 4/5: encoder/readout;
- later: runtime/GPU.

Therefore the currently missing official recipe exposure of `local_history_horizon` is **not** a Step 2 blocker. Add it later before the first official H>0 runtime path.

### Step 3 required checks

Next allowed work is **Step 3 CPU alignment tests only**. Before Step 3 closes, explicitly add/record:

1. true `local_history_horizon=0` disabled contract (current t=0/H=16 test is not H=0);
2. source boundary: history max row = t-1, current target first row = t, sets disjoint;
3. same-episode assertion for all valid history rows;
4. exact timestamp/dt parity;
5. visual source parity: cache episode/start j → z0 → pool(1,2) equals history_visual_summary[j];
6. padding inertness across all evidence tensors.

### Provenance

Current `step2_causal_history_contract.json` was generated while HEAD still reported root `1e98e45` / submodule `31983c5`, although the working tree already contained the fix. Treat it as development evidence only.

During Step 3, rerun the verifier after checkout of the final committed root/submodule SHAs and regenerate the artifact so provenance matches reviewed code.

No GPU. Do not start LocalEvidenceEncoder/readout/model/R09.

Detailed review:
`docs/collab/chatgpt/reviews/2026-08-28_R08_Step2_fix_90fc40e_a0f26dc.md`


---

## 2026-08-28 — R08 Step 3 alignment/leakage review @ root 43d9924 / submodule c479a08

**Verdict: APPROVE_TO_ADVANCE_STEP4**

Artifact:
- `artifacts/g0/r08/step3_alignment_leakage.json`
- `status=PASS`
- 17/17 checks PASS

Accepted coverage:
- true `local_history_horizon=0` disabled contract;
- H=16 t=0 all-padding;
- H=16 t=3 partial;
- H=16 t=16 full;
- H=1 immediate history retained in permanent tests;
- history max source row = t-1;
- history/current target source sets disjoint;
- same-episode identity;
- exact timestamp/dt parity;
- raw/normalized action parity;
- state-row parity;
- independent cache z0 → pool(1,2) visual-summary parity;
- padding inertness/sentinels;
- native Action + SequencePlan isolation.

Provenance is accepted:
- runtime root = `3f0ca0d`;
- runtime submodule = `c479a08`;
- root `3f0ca0d` Gitlink already points exactly to `c479a08`;
- verifier blob is identical at runtime root and final `43d9924`;
- later commits only add/refresh artifact/status docs.

Next allowed work:
- **Step 4 LocalEvidenceEncoder only**
- CPU/static implementation, then stop at REVIEW.

Step 4 scope:
- stateless per-step evidence encoder only;
- keep visual/state/action/age-dt source adapters separable;
- preserve history_mask semantics;
- resolve state normalization before raw state becomes a trainable input;
- no readout yet;
- no Cosmos/native packing wiring;
- no GRU/recurrent state;
- no TTT;
- no Global;
- no GPU;
- no R09.

Detailed review:
`docs/collab/chatgpt/reviews/2026-08-28_R08_Step3_43d9924_c479a08.md`


---

## 2026-08-28 — R08 Step 4 LocalEvidenceEncoder review @ root 49ed506 / submodule 846d917

**Verdict: APPROVE_TO_ADVANCE_STEP5**

Accepted:
- stateless per-step encoder only;
- separate visual/action/age/dt/state adapters;
- no temporal mixing / recurrence / TTT / readout / Cosmos wiring;
- LayerNorm output is hard-masked to exact zero at invalid history positions;
- masked evidence perturbations do not affect valid outputs;
- CPU forward/backward shows finite output and finite grads for all trainable params;
- state input is rejected unless explicit state_mean/state_std are provided;
- current state runtime remains `DISABLED_PENDING_TRAIN_SPLIT_STATS`, so raw state cannot silently enter a trainable path.

Artifact:
- `artifacts/g0/r08/step4_local_evidence_encoder.json`
- 6/6 PASS
- runtime root `ca57b9b`
- runtime submodule `846d917`
- runtime root Gitlink already points to `846d917`
- later root commit `49ed506` only adds status/artifact; no implementation drift.

Non-blocking robustness notes:
- add explicit finite check for `history_dt_s` before official runtime wiring;
- when real state stats are generated, reject negative std and floor only zero/tiny non-negative std.

Next allowed work:
- **Step 5 Stateless LocalReplayReadout only**
- CPU/static implementation, then stop at REVIEW.

Step 5 frozen profile:
- input `E_hist [B,H,D_e]` + `history_mask`;
- `masked_mean + latest_valid`;
- concat;
- small MLP;
- output one temporary Local token `[B,1,D_local_input]`.

Step 5 constraints:
- stateless;
- all-mask/H=0 must have defined inert/absent behavior, no NaN;
- no GRU/LSTM/recurrent state;
- no TTT;
- no Transformer temporal model;
- no Cosmos/native packing wiring yet;
- no GPU;
- no Global/R09.

Detailed review:
`docs/collab/chatgpt/reviews/2026-08-28_R08_Step4_49ed506_846d917.md`


---

## 2026-08-28 — R08 Step 5 StatelessLocalReplayReadout review @ root 4aee924 / submodule f249566

**Verdict: APPROVE_TO_ADVANCE_STEP6**

Accepted:
- exact frozen profile `masked_mean + latest_valid → concat → small MLP → [B,1,D_local]`;
- stateless;
- mask-aware;
- H>0/all-mask readout output exact zero;
- latest-valid semantics correct for sparse masks;
- finite forward/backward and finite grads;
- no recurrent/TTT/temporal Transformer/Cosmos packing/runtime/Global/R09.

Artifact:
- `artifacts/g0/r08/step5_stateless_local_replay_readout.json`
- 8/8 PASS
- runtime root `1109b54`
- runtime submodule `f249566`
- runtime root Gitlink already points to `f249566`;
- later root `4aee924` only adds artifact/status, so provenance is accepted.

### Important H=0 clarification

The current module proves **H>0 + all-mask** behavior. It does not support a literal `[B,0,D]` input because latest-position reduction would be over an empty horizon.

This is not a Step 5 blocker because the R08 supplement allows H=0 as a **Local absent control**, and the frozen dataset H=0 path emits no history fields.

Do not claim literal H=0 readout support. In Step 6 implement:

`H=0 → encoder/readout not called → Local absent`.

### HARD Step 6 requirement: zero token is not sufficient for absent history

R07 downstream projection is:
- `local_memory2llm = nn.Linear(..., bias=...)`
- plus trainable `local_memory_modality_embed`.

Therefore after training a zero readout token can become a nonzero packed Local condition.

Step 6 must gate per sample with `history_mask.any(dim=1)`:
- no valid history → **Local absent**, do not pack zero token;
- valid history → exactly one temporary Local token.

This must work for mixed batches.

Step 6 must also prove:
- H=0 exact no-memory/R07 path;
- episode-start all-mask → Local absent;
- valid sample → one Local token;
- native Vision/Action indexes and mRoPE unchanged;
- machine-readable trace of source ids → E_hist → readout → Local presence/indexes → Future/Action shapes;
- add explicit finite check for `history_dt_s` before runtime wiring;
- state remains disabled until real train-split stats exist.

Step 6 remains no-GPU and must stop at REVIEW before Gate A/B.

Detailed review:
`docs/collab/chatgpt/reviews/2026-08-28_R08_Step5_4aee924_f249566.md`

---

## 2026-08-28 — R08 Step 6 runtime integration review @ root 9d24e9e / submodule 147ab6d

**Verdict: REQUEST_CHANGES**

**Do not start GPU Gate A/B yet.**

Accepted/fixed:
- R08 history no longer implicitly enables R07 dummy.
- local_history_horizon=0 now has an explicit Local-absent branch.
- per-sample history_mask.any() gating is correct; all-mask uses local_memory=None.
- history_dt_s finite guard is present.
- state runtime remains disabled pending real train-split stats.
- trace generator script is now committed.

### HIGH-1 — current Step 6 trace is synthetic

tools/g0/verify_r08_step6_runtime_trace.py only runs LocalHistoryRuntime.
It manually constructs source_ids, local_indexes, future_shape and action_shape.
It does not call OmniMoTModel._inject_local_history(), the real sequence packer, the real Local packer, or inspect real Vision/Action packed mRoPE.

Required:
- run production history injection on a mixed valid/all-mask batch;
- run the real packer;
- record actual Local sequence_indexes;
- compare native Vision/Action mRoPE values against matched no-Local packing;
- assert native condition_frame_indexes_vision/action unchanged;
- valid sample packs exactly one Local token; all-mask sample packs none.

Do not compare raw global packed index integers as the invariant: those may shift when Local is inserted. Compare mRoPE values gathered at each branch's own Vision/Action indexes.
Do not hard-code Future/Action shapes in the CPU artifact; defer those to GPU Gate A unless real outputs are actually run.

### HIGH-2 — selective optimizer allowlist misses the R08 trainable modules

Current recipe adds only local_memory2llm and local_memory_modality_embed for Local.
It does not add local_history_runtime.encoder.* / local_history_runtime.readout.*.

Required:
- add a selection pattern such as local_history_runtime when R08 history is enabled;
- add a CPU/static named-parameter audit proving encoder/readout + R07 Local projection are selected and no unrelated parameter set is widened.

### MEDIUM — remaining regressions/evidence

1. Current test named H0 is actually H=1 + all-mask. Add a true model-level local_history_horizon=0 + no history fields -> _inject_local_history -> Local absent test.
2. Add config regression: history=1/dummy=0 -> dummy disabled; history=1/dummy=1 -> fail fast.
3. Regenerate step6_runtime_trace.json on final committed root/submodule and include root SHA, submodule SHA and tool SHA.

Next:
- Step 6 stays REVIEW.
- CPU/static-only fixes.
- new submodule/root SHAs.
- mm2/Kimi/ChatGPT re-review.
- no GPU / no R09.

Detailed review:
docs/collab/chatgpt/reviews/2026-08-28_R08_Step6_9d24e9e_147ab6d.md

---

## 2026-08-28 — 请求复审：R08 Step 6 runtime integration fixes @ root 6da7a13 / submodule 70a7451

**范围：仅关闭此前 Step 6 的 HIGH-1、HIGH-2 与 MEDIUM CPU/static 项；未启动 GPU Gate A/B，未进入 R09。**

- 子模块 `70a7451`：`_inject_local_history()` 保留 `[1, D_local]`；修复 history recipe 未定义 `cfg`；history 启用时将 `local_history_runtime` 加入选择式 optimizer；新增 H=0、mixed injection shape、dummy/history 互斥和 named-parameter selection 回归。
- 根仓 `bd751f5`：trace 调用真实 `_inject_local_history()` 与 `pack_input_sequence()`；在各分支 Vision/Action 自身的 `sequence_indexes` 上比较 mRoPE，不比较会随 Local 插入变化的全局整数，也不再手写 Future/Action shape。
- 根仓 `6da7a13`：`artifacts/g0/r08/step6_runtime_trace.json` 为 PASS；provenance=root `bd751f5b2c8e2a1df86eaa3751edf9dbc9efd8c2`、submodule `70a7451dab978de3d5c4157f12af3f63723868d4`、tool SHA `6567d10c44786fec37c52507abb18afa0445dc457f0ea4f0270c46227c910251`。

CPU-only 验证：`local_history_runtime_test.py` + `local_evidence_test.py` 为 **11 passed**；`PYTHONPATH=cosmos-framework /root/venvs/psm_wma/bin/python tools/g0/verify_r08_step6_runtime_trace.py` 为 **PASS**；`py_compile` 与双仓 `diff --check` PASS。无外网、checkpoint、数据集或 GPU。

请 mm2/Kimi/ChatGPT 独立复核真实 injection/packer、per-sample absent、native Vision/Action mRoPE 与 condition indexes、optimizer 选择范围和 artifact provenance。Step 6 在独立 APPROVE 前保持 `REVIEW`。

---

## 2026-08-28 — R08 Step 6 re-review @ root 6da7a13 / submodule 70a7451

**Verdict: REQUEST_CHANGES**

**Do not start GPU Gate A/B yet.**

Closed:
- production `_inject_local_history() -> real pack_input_sequence()` trace now exists;
- mixed valid/all-mask packing is real, not synthetic;
- valid sample packs exactly one Local token;
- all-mask sample is Local absent;
- valid Local payload keeps `[1,D_local]`;
- native Vision/Action mRoPE matches no-Local;
- literal H=0 model-level absent path is now tested;
- dummy/history separation is fixed and regression-tested;
- artifact provenance root/submodule/tool is valid.

### HIGH — optimizer visibility is still broken

The recipe now adds `local_history_runtime` to `keys_to_select`, but the production optimizer factory only scans:

`model.net.named_parameters()`

R08 runtime is currently registered on the outer model as:

`self.local_history_runtime = LocalHistoryRuntime(...)`

Therefore actual encoder/readout parameters are outside the optimizer-visible subtree and will not be selected or updated.

The current optimizer unit test does not catch this because it fabricates runtime parameter names and applies substring matching manually; it does not run the real selector against the real model hierarchy.

Required before GPU:
1. make R08 encoder/readout visible to the production optimizer path (prefer an explicit/narrow hierarchy fix rather than broad optimizer widening);
2. use the real production selector/optimizer construction to prove the actual parameter objects for encoder, readout, `local_memory2llm`, and `local_memory_modality_embed` are selected;
3. prove disabled state-adapter params remain absent and unrelated modules are not widened;
4. when regenerating evidence, also add `condition_frame_indexes_action_unchanged` to the Step 6 trace.

Step 6 remains REVIEW, CPU/static only. No GPU, no R09.

Detailed review:
`docs/collab/chatgpt/reviews/2026-08-28_R08_Step6_rereview_6da7a13_70a7451.md`

---

## 2026-08-28 — 请求复审：R08 Step 6 optimizer visibility fix @ root 575d685 / submodule fe499fa

ChatGPT HIGH 已按窄层级修复：`fe499fa` 在 `build_net()` 的 FSDP/parallelize 前注册 `net.local_history_runtime`，`_inject_local_history()` 从 `self.net` 读取；真实 `_build_params_with_metadata()` 对象审计确认 R08 encoder/readout 与 R07 Local projection/embed 被选，disabled state adapter 与 unrelated outer module 未被选。`84a4f32` trace 补 action condition-index invariant，`575d685` 记录 PASS/provenance。CPU-only：11 passed、py_compile、双仓 diff-check PASS；无 GPU/R09。请复核并给出 APPROVE/REQUEST_CHANGES。

---

## 2026-08-28 — R08 Step 6 optimizer-fix re-review @ root 575d685 / submodule fe499fa

**Verdict: REQUEST_CHANGES**

**Do not start GPU Gate A/B yet.**

Closed:
- optimizer visibility is now genuinely fixed: R08 runtime moved into `net.local_history_runtime`;
- production `_build_params_with_metadata()` object-level audit selects encoder/readout + R07 Local projection/embed;
- unrelated outer module is excluded;
- state adapter remains absent;
- production injection/packer trace remains PASS;
- Vision/Action mRoPE and both condition-frame-index invariants PASS;
- artifact provenance `84a4f32 / fe499fa / tool SHA` is valid.

### HIGH — new meta/to_empty initialization bug

`net.local_history_runtime` is created inside `with torch.device('meta')` in `build_net()`.
Later production materialization is `net.to_empty(device=DEVICE)`, which allocates uninitialized real storage.
`Cosmos3VFMNetwork.init_weights()` initializes existing heads/R07 Local/language model but does not initialize the new R08 runtime.

Because R08 runtime params are new and absent from the base checkpoint, GPU Gate A may otherwise start with garbage/uninitialized encoder/readout weights.

Required before GPU:
1. add explicit `reset_parameters()` / `init_weights()` for the R08 runtime modules;
2. invoke it from `Cosmos3VFMNetwork.init_weights()` after materialization;
3. add a real meta -> to_empty(cpu) -> explicit-init regression proving all R08 params are finite and deterministic under a fixed seed.

Non-blocking future note:
- current Gate A recipe is single-GPU;
- before future multi-GPU R08 training, separately verify direct `net.local_history_runtime(...)` calls under root FSDP2, since they occur outside `net.forward()` hooks.

Once the meta-materialization initialization issue is closed, ChatGPT expects Step 6 to be eligible for GPU Gate A approval.

Step 6 remains REVIEW; CPU/static only; no GPU / no R09.

Detailed review:
`docs/collab/chatgpt/reviews/2026-08-28_R08_Step6_optimizer_fix_575d685_fe499fa.md`

---

## 2026-08-28 — 请求复审：R08 Step 6 meta/to_empty initialization fix @ root 3e701e9 / submodule 89b421b

已按 `e892be4` 的 HIGH 完成最小修复：`LocalHistoryRuntime.reset_parameters()` 显式初始化 R08 encoder/readout，`Cosmos3VFMNetwork.init_weights()` 在 `to_empty()` materialization 后调用该入口。新增真实 CPU 回归：`with torch.device("meta")` 构造 → `to_empty(device="cpu")` → 显式初始化；固定 seed 两次的全部 R08 参数均 finite 且逐元素相等。定向 pytest 12 passed、py_compile、双仓 `diff --check` PASS；`artifacts/g0/r08/step6_runtime_trace.json` 为 PASS，provenance=root `7440342` / submodule `89b421b`，Vision/Action mRoPE 与两项 condition-frame-index 不变量仍为 true。无 GPU、无 R09。请复核并给出 APPROVE/REQUEST_CHANGES。

---

## 2026-08-28 — R08 Step 6 meta-init re-review @ root 3e701e9 / submodule 89b421b

**Verdict: APPROVE_TO_RUN_GPU_GATE_A**

ChatGPT side: Step 6 CPU/static blockers are closed.

Accepted:
- R08 runtime is optimizer-visible under `net.local_history_runtime`;
- production `_build_params_with_metadata()` audit selects actual encoder/readout + R07 Local projection/embed parameter objects;
- production injection + real packer trace passes mixed valid/all-mask;
- valid sample packs exactly one Local token;
- all-mask/H=0 remains genuinely Local absent;
- Vision/Action mRoPE unchanged;
- Vision/Action condition-frame indexes unchanged;
- explicit `history_dt_s` finite guard remains;
- state runtime remains disabled pending real train-split stats;
- meta -> `to_empty()` initialization HIGH is closed via explicit `LocalHistoryRuntime.reset_parameters()` called from `Cosmos3VFMNetwork.init_weights()` after materialization;
- meta->to_empty(cpu)->explicit-init regression proves all R08 params finite and fixed-seed deterministic;
- trace provenance root `7440342` / submodule `89b421b` / tool SHA is valid.

### GPU Gate A approval scope

Actual launch must still wait for mm2/Kimi independent approval.

Gate A should be one/few controlled single-GPU optimizer steps only and record:
- production R08 Edge-all path enabled, dummy disabled;
- finite loss;
- finite grads for encoder/readout + R07 Local projection/embed;
- optimizer param groups contain those actual parameter objects;
- at least one intended R08 encoder/readout parameter changes by finite nonzero delta after optimizer.step();
- Local absent semantics preserved for no-history/all-mask control;
- valid Future/Action output shapes;
- no NaN/Inf;
- peak GPU memory/runtime;
- machine-readable root/submodule/checkpoint/config/command provenance.

Do not start R09 or a long training run.

Future multi-GPU note (non-blocking for current Gate A): direct child call to `net.local_history_runtime` under root FSDP2 needs a dedicated multi-rank smoke before world_size>1 R08 training.

Detailed review:
`docs/collab/chatgpt/reviews/2026-08-28_R08_Step6_meta_init_3e701e9_89b421b.md`
