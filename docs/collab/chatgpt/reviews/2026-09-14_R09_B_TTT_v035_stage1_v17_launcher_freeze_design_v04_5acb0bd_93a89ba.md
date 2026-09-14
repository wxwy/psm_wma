# ChatGPT Review — Stage-1 v1.7 launcher freeze design v0.4

- Formal root: `5acb0bdadcc5ecbc22b720e5eeac6a3c95780bdc`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`
- Verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_LAUNCHER_FREEZE_CPU_STATIC`

## Findings

Blockers: 0. Design/Authority: 0. Production implementation: 0. Evidence-only: 0. child/runtime: 0.

The sole v0.3 HIGH is closed. v0.4 appends the four missing outer-source self-check replacements and binds each to its exact surrounding runtime guard rather than permitting global numeric/hash replacement:

- bootstrap raw length `7538 -> 9406`;
- bootstrap raw SHA `7e1c0ecc2161984a88ea0d0eae82f9f7ced709ca919f0302f74a3a068e08c9b8 -> ccd8ee2772d666707c919e6a20376c997771b9ff068fe0432fdaa96c686ab097`;
- `RAW[2]` parser length `2427 -> 2336`;
- `RAW[2]` parser SHA `72777bd7305c760c48c069eafd068f1a538383a6fdb8d40258acf3d8fc3b7ae2 -> 1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333`.

Together with the inherited v0.3 flag/adjacent-value-aware parser table and original four source replacements, the design now freezes a complete canonical replay input sufficient to require direct reproduction of outer payload `18875` bytes / `658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8`. The direct CPU/static witness must consume the complete parser table plus all eight source replacements and include a drift negative for each newly added self-check literal.

Formal scope remains docs-only in this pair. Root Gitlink resolves exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`; no child/runtime production bytes changed.

## Authorized next action

This approval authorizes implementation only after required same-pair reviewer approvals, and only at the two frozen root paths inherited from v0.3:

- `tools/psm_wma/stage1_v17_launcher_replay.py`
- `tools/psm_wma/test_stage1_v17_launcher_replay.py`

The implementation remains pure stdlib / CPU-static: no `main()`, Git/path/FD/network/`os.execve` I/O, project clean-root/index/ref/evidence creation, source/checkpoint/data/cache access, child/runtime mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.

This design approval does **not** authorize v1.7 request construction, Stage-1 retry/materialization, or revival of the consumed v1.6 authority. A future v1.7 exact request may be constructed only after separate implementation review and close approval, with fresh observations and independent request approval.
