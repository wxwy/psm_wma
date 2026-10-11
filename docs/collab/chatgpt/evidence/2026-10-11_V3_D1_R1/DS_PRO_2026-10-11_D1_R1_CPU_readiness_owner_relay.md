# DS_PRO — V3 D1 Round1 Parallel CPU Readiness（Owner-relayed Evidence）

**Report date:** 2026-10-11
**Formal Root:** `444c232b976e80ac68cde9e7370e73b9f6410f0e`; **Child/Gitlink:** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`
**Official Job:** `formal_verified_index_30k` (STOPPED); **Target:** `iter_000000800` copied Shadow.
**Expected digest:** `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`
**Provenance:** This is a structured record of the DS_PRO report relayed by the owner, **not** direct GPT access to DS's `/tmp` design documents, GPU queries or raw logs. Reported A/B/C PASS are DS judgments; GPT independent adjudication is in `docs/collab/chatgpt/reviews/2026-10-11_V3_D1_R1_CPU_readiness_evidence_review_444c232b_e9b8a41.md`.

## DS scope

CPU/static only; independent evidence directories `/tmp/ds_pro_v3_d1_r1/{a,b,c}/`. No new GPU, torchrun, DCP load, forward/backward, optimizer/scheduler step, model save, code change or Formal Job resume. C1 is already CLOSED on the fixed implementation pair. Actual GPU D1 is not yet authorized.

## DS-R1-A: Numerical parity design (DS self-verdict: PASS)

- Reference `PSM_V3_COMPACT_CACHED_VIDEO=0`, `PSM_V3_SHARED_EPISODE_CACHE=0`; optimized toggles both =1; `num_workers=0`, all fixed T16/B8/GA2/K4/Hpred16/raw15/left_wrist/use_state/world8/CFG0.1.
- DS states expected model data equivalence except dense zero-video tensor versus compact zero-stride one-byte proxy; actual cached latent and image geometry continue along the same consumer path, previous Batch1 and B3 CPU parity accepted.
- Proposed per-GA single-window comparison after two members' forward/backward but **before** slow optimizer step. Fields: outer/action/vision/inner losses, generation/action/local w0 gradients, FSDP2 rank-shard fingerprints, candidate Local fast state, rank RNG, optimizer/scheduler, timings. Freeze P0 bitwise and fallback `atol=1e-3,rtol=1e-3` for bf16.
- DS claims optimizer step is deterministic when model parameters, gradients, optimizer and scheduler states are the same; thus an actual step is unnecessary to test pre-step gradient parity (does NOT itself demonstrate actual step execution parity).
- Proposes optionally an optimized-only post-comparison step to estimate step time. No actual implementation-level no-step Harness call graph or dryrun evidence was included in this summary.
- DS design file: `/tmp/ds_pro_v3_d1_r1/a/d1a_numerical_parity_design.md`.

## DS-R1-B: Memory/performance budget (DS self-verdict: PASS)

- 8×H100 80GB each, outside `robotwin_server` baseline used **45,580–47,263 MiB**, free **33,827–35,509 MiB**, GPU util≈0.
- C1 monitor's total **device-used** peak reported **52,051–53,819 MiB** inclusive of robotwin processes.
- DS's component estimate labeled `per rank`: bf16 model parameter shard `13.49GB`, master `26.98GB`, optimizer state `11.39GB`, context `2GB` ⇒ `Load-only 53.9GB`; forward/backward added `16–20GB` ⇒ full peak `68–74GiB`. DS judges fit but tight.
- DS threshold: free at least 33,500MiB, warning under 32,000MiB; process reserved cutoff 76GiB, device global used cutoff 79,000MiB. Proposed stage-timed CUDA events and per-rank allocator measurements, but **not run**.
- C1 context: the `model` DCP data shards were ~1.685GB **each** over 8 ranks (~13.48GB total) and `optim` ~1.424GB each (~11.39GB total), so values now called `per-rank` likely reflect sums across ranks, not actual live per-GPU memory. Cannot equate disk shard byte size to exact allocator residency either.
- DS budget design: `/tmp/ds_pro_v3_d1_r1/b/d1b_memory_budget.md`.

## DS-R1-C: Shadow and reproducibility scheme (DS self-verdict: PASS)

- Env flags set before dataset construction; one reference run and one optimized run, distinct `/tmp/ds_pro_v3_d1_r1/gpu_run/{reference|optimized}` log dirs; proposed new job names `d1_shadow_singlestep_ref` and `d1_shadow_singlestep_opt`.
- DS proposes setting `config.checkpoint.load_path=<existing_shadow/checkpoints/iter_000000800>` to load shared state from new Job Names, while also calling `require_dcp_grouped_resume_component`; it does **not** report copying a same-job `latest_checkpoint.txt` and iter800 into either new job's own `save_dirname`.
- DS intends checkpoint/RNG/frontier/fast-state/consumer equality, per-rank first-exception logs, static CPU preflight and fail-stop; no new actual H100 experiments were run.
- DS design: `/tmp/ds_pro_v3_d1_r1/c/d1c_harness_iso.md`.

## DS requested next authorization

One paired 8×H100 reference-versus-optimized experiment from iter800 with full 2-member GA window native forward/backward, no optimizer step, plus optional optimized-only step, numerical parity + timing + memory. DS self-reports A/B/C PASS. **This request is not executed or automatically authorized.**

Existing source/child formal SHAs unchanged by this DS report. Formal30k and original DCP remain STOPPED / unchanged as reported.
