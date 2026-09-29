# PSM-WMA V3 — H3-E Stage 3E H100 asset-rebinding preflight closure

- Date: 2026-09-29
- Formal implementation root: `db08117786a2483ca5cc7f4b58a0c3518e78bccc`
- Formal child/Gitlink: `b43097c74982f13e67c071ece729c7b6929cad52`
- Verdict: **H3E_ROUTE_B_STAGE3E_PREFLIGHT_CLOSED**
- Next authorization: **APPROVE_TO_RUN_H3E_8XH100_FRESH_ITER0_TO_ITER1**
- Bookkeeping commits after the formal pair do **not** replace the formal implementation pair.

## Exact-pair/static closure

ds independently validated the exact pair above:

- root/child/Gitlink exact match;
- root and child worktrees clean;
- pytest: 11 passed;
- ruff check: PASS;
- ruff format --check: PASS;
- git diff --check: PASS.

The owner-requested H3-F future long-run budget is frozen in the child as:

- `H3F_FORMAL_MAX_ITER = 30000`;
- checkpoints/eval at `1k,2k,4k,8k,12k,16k,20k,24k,30k`.

H3-E smoke semantics remain unchanged:

- fresh run ends at optimizer iteration 1;
- same-job resume, if later authorized, ends at optimizer iteration 2.

## Real H100-authority preflight

The formal preflight ran without CUDA training / torchrun / optimizer step and returned:

- catalog episodes = 9036;
- manifest digest =
  `a8cad3f053232b348ea155f15bf79c2c9cf807dedcf39b89e246b17e43f283df`;
- config digest =
  `912f70d8191c17c5f491845237b81389877c9ecace7bc07d1f09d0f767315664`;
- Stage-A DCP keys = 549;
- native grouped batch = 8;
- geometry = `[8,8,2,16,4]`.

H100 Stage-A asset authority digests matched exactly:

- config SHA256:
  `f64036c499f891979213469523a160ac08cb3d976a2add8d8fdf93750c5a5439`;
- iter1 model metadata SHA256:
  `53adef43a58e23f37d1132c4868ea8055be1b095cf76762b2e3e0b69ea287731`.

The eight preflight episodes were unique, all in the production 9036 catalog, and all in the
rank-0 partition. Independent re-materialization reproduced the same eight identities through:

`RoboCasaEpisodeCatalog -> RankLocalGroupedPlanner -> StageARoboCasaEpisodeBinder ->
materialize_member -> 8 slot index0 -> collate_grouped_native_batch`.

Native batch contract:

- sequence-plan count = 8;
- action sample shape = `[33,64]`;
- raw action sample shape = `[33,15]`.

## Fail-closed probes

Both negative probes passed:

1. wrong expected child is rejected by the formal pair lock before output creation;
2. an in-memory corrupted expected Stage-A config digest is rejected by
   `validate_h100_asset_authority`, while the formal asset remains unchanged.

Therefore Stage 3E preflight is closed.

## Fresh 8×H100 authorization

Authorize only the fresh H3-E integration smoke:

- exactly 8 H100 ranks on one node;
- `phase=fresh`;
- one optimizer iteration only;
- fresh output/job path;
- exact formal pair above;
- existing H100 source/cache/Stage-A/Edge/VAE authorities;
- no code/config mutation.

The fresh smoke must prove:

1. all 8 ranks start and bind distinct rank-local catalog partitions;
2. 32 native forwards + 32 native backwards / rank for the two GA members × T16 path;
3. finite native losses;
4. selected host + all Local parameters participate in the optimizer inventory as frozen;
5. finite/non-empty selected gradients and non-zero Local gradient witnesses;
6. exactly one optimizer step succeeds;
7. fast-state transaction commits exactly once;
8. completed grouped iteration = 1;
9. DCP `iter_000000001` contains model/optim/scheduler/trainer metadata plus rank-local
   dataloader state for every rank;
10. all rank result JSON files report PASS;
11. CUDA evidence records per-rank peak memory and no OOM/non-finite path;
12. the output is preserved untouched for the later same-job resume Gate.

Same-job resume is **not** authorized by this closure. It requires fresh-smoke PASS and a new
explicit authorization.

## Still forbidden

- no H3-E resume-to-2 before fresh closure;
- no H3-F 30000-step training;
- no B1 cache/manifest/Stage-A mutation;
- no fallback geometry change if fresh fails;
- no reduction of slots/T/GA/ranks to make the smoke pass.
