# PSM-WMA V3 — H3-E Route-B Stage 3D H100 Stage-A warmstart closure

- Date: 2026-09-29
- Formal implementation root: `16f296cd959820c93ae36e9d8abf16546cd637ea`
- Formal child/Gitlink: `ba1996c85cc4de41df2e8bd22c0289ea4deef736`
- Verdict: **H3E_ROUTE_B_STAGE3D_CLOSED**
- Next gate: **H3-E H100 asset rebinding + preflight**

## Stage 3D result

H100-local Stage-A warmstart was regenerated under the already frozen Edge/raw15 Stage-A contract.

Frozen assets used:

- EDGE_POLICY_CHECKPOINT:
  `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Cosmos3-Edge-Policy-DROID`
- BASE_CHECKPOINT_PATH:
  `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Cosmos3-Edge-Policy-DROID-dcp`
- WAN_VAE_PATH:
  `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Wan2.2-TI2V-5B/Wan2.2_VAE.pth`
- ROBOCASA_ROOT:
  `/mnt/data1/data_v2_0617/robocasa365_official_v30`
- output root:
  `/mnt/data1/data_v2_0617/psm_wma_v3_stage_a_h100`

The existing repository Stage-A entrypoint `examples/psm_wma_robocasa_native.py` was used with
`CloseFridge`, one optimizer iteration, one H100, no resume.

CPU dryrun passed and the generated config retained:

- experiment = `action_policy_robocasa_edge`;
- `trainer.max_iter = 1`;
- `task_names = [CloseFridge]`;
- `num_workers = 1`.

## Numeric/runtime evidence

- physical GPU: H100 80GB, GPU 5;
- one-step loss: 15.6558, finite;
- gradient norm: 24.44275, finite/non-empty;
- optimizer step: completed;
- one-step time: 101.16 s;
- observed GPU memory: 42305 MiB;
- checkpoint `iter_000000001`: saved successfully.

No Local-TTT/grouped trainer path was used.

## Frozen raw15 contract

Generated `config.yaml` was re-read and verified:

- task = CloseFridge;
- fps = 20;
- chunk_length = 32;
- use_base_action = true;
- base_encoding = raw;
- raw action width = 15;
- camera_set = left_wrist;
- use_state = true;
- action_normalization = none;
- max_action_dim = 64;
- num_embodiment_domains = 32;
- encode_exact_durations = [33];
- optimizer = FusedAdam;
- lr = 5e-5;
- Local memory disabled.

## DCP authority

The generated `iter_000000001` contains model/trainer metadata plus optimizer/scheduler state.

Model metadata:

- 549 keys;
- required action2llm/llm2action/action_modality_embed keys present;
- vae2llm/llm2vae keys present;
- no `local_memory` keys.

Authority digests:

- `config.yaml` SHA256:
  `f64036c499f891979213469523a160ac08cb3d976a2add8d8fdf93750c5a5439`
- `iter_000000001/model/.metadata` SHA256:
  `53adef43a58e23f37d1132c4868ea8055be1b095cf76762b2e3e0b69ea287731`

This is a **H100-local regenerated Stage-A warmstart under the frozen Edge/raw15 Stage-A
contract**. It is not claimed bitwise-identical to the historical /disk/rl Stage-A checkpoint.

## Scope

Stage 3D did not run or modify:

- Local-TTT training;
- H3-E 8×H100 fresh/resume smoke;
- H3-E harness implementation;
- B1 cache;
- manifest authority;
- server/eval/SR.

Stage 3D is therefore closed.

## Next gate

The H3-E harness still inherits historical `/disk/rl/*` defaults through
`examples/psm_wma_robocasa_local_s1.py`. The next implementation gate must rebind H3-E to the
new H100 source/cache/Stage-A/Edge/VAE authorities with explicit fail-closed digest checks before
any 8×H100 execution is authorized.
