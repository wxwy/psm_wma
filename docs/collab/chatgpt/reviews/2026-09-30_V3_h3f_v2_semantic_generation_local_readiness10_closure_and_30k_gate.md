# PSM-WMA V3 — H3-F V2-semantic generation+Local readiness10 closure and 30k Gate

- Date: 2026-09-30
- Formal root: `e272a589ce2204f5b4324e79c0f1227d855f3e97`
- Formal child/Gitlink: `f89876a4bb013d9a48d622db776996ded295884b`
- Readiness verdict: **H3F_OWNER_LAUNCH_READINESS10_CLOSED_FOR_V2_SEMANTIC_GENERATION_LOCAL**
- Long-run Gate: **APPROVE_TO_START_H3F_FORMAL_30K_V2_SEMANTIC_GENERATION_LOCAL**
- Formal 30k started at time of this review: **false**

## Evidence accepted

CPU/static on the exact formal pair:

- pytest: 25 passed;
- Ruff check: PASS;
- Ruff format --check: PASS;
- launcher bash -n: PASS;
- git diff --check: PASS;
- root/child worktrees clean.

Owner-env exact preflight:

- catalog: 9036;
- manifest: `a8cad3f053232b348ea155f15bf79c2c9cf807dedcf39b89e246b17e43f283df`;
- selector: 7 generation/action keys + 4 V3 Local keys;
- trainable profile: `v2_semantic_generation+local_v3_raw15`;
- mesh profile: `dp_shard8_generation_and_local`;
- data profile: `official_v30_raw15`;
- local_memory_action_dim: 15;
- max_iter: 30000;
- formal SAVE_ITER owner contract: 500;
- scheduler cycle: 30000;
- warmup: 500;
- config digest: `315f1914a7f21d963515158c533cfa0b637adf4b0b15eff2cfdaff4d10adeed9`.

8×H100 readiness10:

- 8/8 ranks PASS;
- completed_iteration=10;
- progress_records=10;
- selected_generation_tensors=294;
- selected_generation_params=1,423,379,648;
- selected_local_tensors=20;
- selected_local_params=165312;
- selected_reasoner_params=0;
- complete selected_names inventory had no reasoner leak;
- generation/action/Local gradient witnesses all non-zero;
- native losses finite;
- no OOM / NaN / Inf / traceback;
- peak allocated about 9.31 GB per rank;
- reserved about 11.3 GB per rank;
- median steady iteration around 139.4 s in the observed co-resident environment;
- final iter10 DCP complete for model/optim/scheduler/trainer and all 8 dataloader rank states.

Fail-closed matrix:

- invalid SAVE_ITER rejected;
- invalid TTT_ACTIVE_GA rejected;
- wrong latent cache authority rejected;
- wrong CUDA_VISIBLE_DEVICES rejected;
- wrong expected root SHA rejected.

## Formal training contract authorized

The authorized formal H3-F training contract is:

- source: current `robocasa365_official_v30` authority;
- raw15 action contract;
- Local action dim 15;
- 9036 train catalog;
- current frozen manifest;
- generation/action + V3 Local slow trainables;
- reasoner frozen;
- FusedAdam;
- lr=5e-5;
- weight_decay=0.05;
- 5x LR multiplier on action2llm / action_modality_embed / llm2action;
- T=16;
- B_stream=8;
- active GA=2;
- K_local=4;
- inner_lr=0.1;
- dp_shard=8, replicate=1;
- max_iter=30000;
- scheduler cycle=30000;
- warmup=500;
- SAVE_ITER=500;
- primary evaluation milestones:
  1000, 2000, 4000, 8000, 12000, 16000, 20000, 24000, 30000.

## Operational constraints

This approval authorizes the formal 30k job on the exact formal pair above. It does not change the
owner's manual checkpoint-retention decision.

With SAVE_ITER=500, checkpoint cleanup must be managed manually so the output filesystem does not
fill. Never remove the checkpoint currently referenced by `latest_checkpoint.txt`, and do not
delete checkpoints while a save is in progress.

The observed readiness median was about 139.4 s/optimizer iteration in a co-resident environment.
A straight 30k extrapolation is roughly 48 days of steady compute. This is a planning estimate,
not a guaranteed runtime. Evaluation milestones and same-job resume should therefore be treated
as operational control points, not just archival checkpoints.

## Final verdict

**APPROVE_TO_START_H3F_FORMAL_30K_V2_SEMANTIC_GENERATION_LOCAL**

No additional profile/code change is required before launch unless the formal pair or training
contract changes. Any change to optimizer selector, dataset/action contract, mesh, TTT geometry,
scheduler, warmup, or formal pair reopens the Gate.
