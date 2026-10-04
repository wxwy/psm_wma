# V3 Phase 1A cache-first exact-window catalog — GPT source review r2

- 日期：2026-10-05
- Gate：`V3-CORRECTED-PHASE1A-CACHE-CATALOG`
- formal root：`7c214251f3535116e7b19f964ee907e8653fd388`
- formal child/Gitlink：`e98f293f396df74bb7030d525c40faa21e7d226d`
- design authority：`docs/build/PSM-WMA_V3_Local_TTT_on_latest_Cosmos_RoboCasa_detailed_design_v3.0_2026-10-04.md`
- supersedes：`docs/collab/chatgpt/reviews/2026-10-05_V3_phase1a_cache_catalog_source_review_7c214251_e98f293f.md`

## Verdict

`REQUEST_CHANGES`

此前同 pair 的 `APPROVE_TO_RUN_PHASE1A_CPU_STATIC_EVIDENCE_ONLY` **撤销且不得执行**。ds 暂停；先由 cx 修复下面唯一 source blocker，形成 fresh child/root pair，再做 fresh review。

## Blocker

### MEDIUM — recognized episode payload namespace 中的 malformed/unexpected .pt 会被静默忽略

- file:line：child `cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cache.py:291-303`
- current behavior：
  - `_audit_files()` 只 glob `tasks/*/episodes/episode_*.pt`；
  - 对 glob 命中但不符合 `episode_[0-9]{6,}\.pt` 的文件直接 `continue`。
- directly reproducible examples：
  - `tasks/Foo/episodes/episode_bad.pt`
  - `tasks/Foo/episodes/episode_7.pt`
  - 当前均位于 recognized `tasks/<slug>/episodes/` payload namespace，却不会进入 `discovered/extra`，strict catalog 也不会 fail。
- root cause：文件审计把“expected canonical filename”误当成了“是否属于需要审计的 payload namespace”的过滤条件。
- violated contract：Phase1A task 明确要求 **unexpected episode payload files under the recognized tasks/.../episodes namespace must be reported and, in strict training mode, fail closed**。cache 是训练 corpus authority，不能静默容忍额外 payload。
- acceptance：
  1. 审计 recognized `tasks/*/episodes/` 下所有 episode payload `.pt` 文件，而不是仅 canonical regex；
  2. canonical expected file 正常计入 discovered；
  3. 未声明 canonical episode、malformed `episode_*.pt`、以及其它 `.pt` payload（如 `foo.pt`，若位于该 namespace）均至少计为 extra/invalid 并在 strict mode fail-closed；
  4. non-strict audit 若保留，统计必须显式可见；
  5. 添加定向 tests 覆盖 `episode_bad.pt`、短位数 `episode_7.pt`、其它 unexpected `.pt`；不得只改 regex 让它们变成“合法 episode id”。

## Other source findings

除上述 blocker 外，当前 Phase1A scope 的 manifest authority、portable locator、semantic digest、lazy exact-key read、fp32 [5,48,H,W]、17-frame/5-anchor validation、no raw/VAE fallback 等未发现新的 source blocker。

本 review 不授权 ds、GPU、训练、仿真或 Phase1B。