# V3 Phase 1B cache-to-flat-source binding — GPT fresh source review

- 日期：2026-10-05
- Gate：`V3-CORRECTED-PHASE1B-CACHE-SOURCE-BINDING`
- formal root：`610737dd841dd2cd6ef3a3661d323808d41b8ef7`
- formal child/Gitlink：`db2701554ae26c50e26d1854ef3b1182de37118d`
- design authority：`docs/build/PSM-WMA_V3_phase1b_cache_source_binding_design_v0.4_2026-10-05.md`
- parent Phase1A child：`a40e8b782e0692e0a24e2f60893e9f4f8d858961`

## Verdict

`REQUEST_CHANGES`

Phase1B 不授权 ds 执行。当前 production binding/source semantics 未发现新的核心 blocker，但 formal child 仍漏掉 adoption review 的一项 summary contract。

## PASS findings

1. formal child diff 仅 Phase1B 允许的 3 个文件：Phase1A cache identity API + source module + source tests。
2. corpus membership 仍由 Phase1A cache catalog 决定，source extra episode 不进入 index。
3. flat LeRobot v3 source-only 约束明确；不 silent remap latest multi-shard layout。
4. official `LeRobotDataset` 仍拥有 action/state delta-query 与 caption semantics；Phase1B 不实现 raw15/rot6d/state15。
5. local/no-video seam 成立：
   - offline guard 在 factory 前；
   - metadata/data preflight；
   - minimal subclass 只 override `_check_cached_episodes_sufficient` + `download`；
   - runtime instance video feature view 被移除，dynamic `video_keys=[]`；
   - direct defense test 真正命中 overridden download，Hub pull 0。
6. filtered `episodes=exact cache set` + absolute→relative index mapping 有 fail-closed tests。
7. cache global-row witness、episode/frame/annotation/padding 都在 runtime exact-window read 校验。
8. annotation task class 与 natural-language caption 分离正确；valid test 明确 `task_class="Pick Mug"` 与 `ai_caption="Please pick the mug"`。
9. raw action12/state16 有 exact shape/dtype/finite guards，并对 synthetic source 逐值验证 16/17 帧。
10. adoption review A/B/D clarification 已有实质测试：preflight factory injection、direct download fallback、cross-task duplicate episode index、missing source episode、length/bounds、annotation 0/>1/mismatch/multi-class/non-scalar、abs→relative duplicate/unmappable。

## Remaining blocker

### LOW/MEDIUM — summary mismatch counters 未按 frozen design 显式化

- file:line：child `cosmos_framework/data/generator/action/datasets/robocasa_exact_window_source.py:390-405`
- current：`"mismatch_counters": {}`
- frozen design/adoption requirement：valid constructed reader 的 summary 至少明确：
  - `missing: 0`
  - `ambiguous: 0`
  - `task_mismatch: 0`
  - `frame_mismatch: 0`
  - `row_mismatch: 0`
- root cause：实现保留了早期 placeholder empty dict，未随 design v0.4/adoption clarification 收口。
- why it matters：训练启动日志后续要机器可读地区分“没有 mismatch”与“该类别根本没统计”；空 mapping 会造成 audit ambiguity。
- acceptance：
  1. valid summary 返回上述固定 keys 全为 0；
  2. 增 formal CPU test 精确断言 keys/values；
  3. 不引入“遇到 mismatch 后继续统计”的宽松行为；任何 actual mismatch 仍 fail-closed；
  4. 不扩大 Phase1B scope。

## Next

cx 只修上述 summary + test，跑 Phase1A+Phase1B targeted pytest、Ruff check/format、diff-check，形成 fresh child/root pair。
ds 暂停，不修代码、不跑旧 pair。