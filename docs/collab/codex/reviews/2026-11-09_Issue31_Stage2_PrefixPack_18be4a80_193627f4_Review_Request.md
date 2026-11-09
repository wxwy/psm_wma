# Issue31 Stage2 — Prefix-safe request-local pack reuse

Codex author review request, 2026-11-09T22:00:25+08:00. Status **REVIEW**; independent verdict not claimed.

Draft [Root PR33](https://github.com/wxwy/psm_wma/pull/33) /
[Child PR11](https://github.com/wxwy/cosmos-framework/pull/11), both unmerged.
Evidence commit28b19890; publication receipt is metadata only. Performance NOT_MET.

Formal Root **`18be4a80a5ae4d97bc7d287034d24efab847c496`** / Child-Gitlink **`193627f42f4cd1ba6d563aefb8fa8f9428ecb56d`**.
Approved Stage1 baseline Root5b89f3eddbfe27ee72c173696a386e0b756d7866 /
Child4446be0f6dad9b6dc887ef90af52d0af754d4682; latest baseline documentation
590071c599c0531cd9feca9ae748eb0be1af1c89 preserved. Independent branch
`v3-local-ttt-prefix-pack-issue31-20261109` stacked on the Stage1 candidate.
Later evidence/Inbox commits do not replace this implementation Pair.

Stage1 APPROVE_CODE was read directly from its exact-pair formal GPT report after
fetch, advertised-ref check and ff-only fromcab44ba2 to590071c5. It approves
text-KV correctness/model-only P50, not Stage2, P99 or V3 merge. Owner's latest
instruction plus Issue31's separately attributable second-stage scope authorize
this new candidate and model-only author verification. No merge is performed.

## What changed

The **only production function changed is `generate_samples_from_batch()`** in
Child `omni_mot_model.py`. Compute the already approved Prefix text-KV eligibility
before allocating templates, then enable existing pack reuse only for that same
B1/single-sample/two_way/guidance1, no postprocess/DP/CFG/CP path. Add
`use_prefix_pack_templates=False` to preserve the approved text-KV-only reference.
Disabling Prefix text KV also preserves the original full Prefix-on path.
NoPrefix/NoTTT ignores this new Prefix-specific option and retains native behavior.

Templates are allocated inside each generation call after attaching its current
Prefix. The existing native updater refreshes noise and timestep each denoise
step while retaining Prefix, masks, positions, action-domain/raw-width validity.
No template is saved on a model or Session. On success/failure, local references
expire; text cache cleanup and dispatch restoration retain Stage1 semantics.

No changes to attention/backend, precision, compile limit8, text-KV implementation,
Fast Weight algorithm, training, VAE, Sim/Worker, scheduler, required model-mode/DCP
inventory or strict K/H/M/B Resume. AST proof retains `_get_velocity`, native
template updater/timestep copier and both original eligibility helpers unchanged.
Root code changes only its existing benchmark; Gitlink and bookkeeping are separate.
`cpu/scope.json` and full Root/Child diffs bind this exact scope.

## CPU and controlled negative

Exact clean Pair, `author02`: **201/201 PASS**, zero failures/errors/skips,
Shell0/gatePASS, **1487/1487 source fingerprints unchanged**, nine scoped
format/AST/Ruff files pass. One inherited W0 continuation assertion remains
explicitly deselected; it was independently reproduced by GPT on both old4cd5
and approved4446. It is not fixed, rerun or counted PASS here. Three inherited
I001 exceptions remain narrow; no full-repository green claim.

Four native packer/get_velocity cases (FP32/BF16, noisy/non-noisy Action) compare
all finalized dataclass fields and synthetic velocities for30 distinct noise/time
steps. Only device transfer and model prediction are substituted in these tests.
Generation orchestration tests use real small MoT layers with CPU SDPA as before:
one template/30steps, unchanged actions, Prefix/instruction sensitivity, per-request
freshness, weakref release after error/retry/reset/cold-start, unsupported guards,
NoTTT option parity. CP test checks eligibility only, not a fabricated distributed run.
Original Stage1 tests now explicitly set packOFF to preserve their existing
assertions; new tests exercise the default packON separately.

Same new test file on exact old4446 production gives expected RED at
`assert obj.templates == 1` (actual0). New same case passes in final201. Old
production is clean; only that new test is untracked. Hash/status proof is in
`cpu/controlled_red_green.json`. Raw RED log/JUnit retained. Red pytest rootdir
was inferred as /dev from `-c /dev/null`; explicit source path/hash and actual
assertion identify the execution, not the unusual display node label.

Initial dev01 import-sort failure, dev02 187PASS/14 new-fixture failures, corrected
new14PASSdev03, author01 201PASS on prior Root1568888c, and final author02 are all
retained. Fixture corrections supplied CPU Attention, Tensor domain IDs and valid
CP/CFG boundaries; they did not cause production changes. Historical runs are
not summed as a larger current Gate.

Executed CPU command (use a new output directory for independent replay):

```bash
cd /workspace/work/psm-wma-prefix-pack-issue31
env CUDA_VISIBLE_DEVICES='' LD_LIBRARY_PATH='' OMP_NUM_THREADS=1 \
  OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  /workspace/.venvs/psm-wma-cpu/bin/python \
  /workspace/work/issue31-prefix-pack-evidence/cpu_gate.py \
  --root /workspace/work/psm-wma-prefix-pack-issue31 --run author02 \
  --expected-root 18be4a80a5ae4d97bc7d287034d24efab847c496 \
  --expected-child 193627f42f4cd1ba6d563aefb8fa8f9428ecb56d
```

`cpu/index.json` binds all local raw logs, JUnit, commands, environment and source
inventories, plus source diffs/controlled proof. No private server file is present.

## Incremental H100 model-only comparison

Both modes use **text KV ON** and identical Local iter15000 DCP/weights, input,
history/FastState/4×32 Prefix/seed. The only mode difference is packOFF vs packON.
Native required-mode/DCP inventory checks pass. B1/raw15/H16/guidance1/30-step
UniPC; synthetic fixed RGB composite/history, no real executed env.step evidence.
FW construction is outside generation timing; current VAE is included once and
separately timed. No Sim/Worker/HTTP/SR/900EP or training launched.

Only authorized GPU6 was used, GPU0–3 untouched; `gpu_load_sim.py` left unchanged.
Three AB/BA warmup pairs, audit, all layer and pack-audit hooks restored/removed,
three new clean warmup pairs, **30 balanced AB/BA pairs**, then separate profiler.
The complete executed command is `gpu/executed_command.sh` and includes
`--optimization prefix_pack`. Do not overwrite existing server output on replay.

| GPU-event native generation ms | textKV ON / packOFF | textKV ON / packON |
|---|---:|---:|
| P50 | 837.0812 | 798.8678 |
| P95 | 844.7195 | 803.0262 |
| Mean, all samples | 836.9260 | 798.0850 |
| P99, interpolation | 846.2682 | 805.8524 |
| Max | 846.7140 | 806.9632 |

P50 incremental speedup **1.0478×**, latency reduction **4.565%**;
30/30 paired runs faster. All samples, maxima and tails
are retained; none trimmed. This run's P99 is a30-sample interpolation, not an SLA.
**Performance gate NOT_MET**: predeclared speedup threshold1.05× was missed;
benchmark status `CORRECTNESS_PASS_PERFORMANCE_NOT_MET`, **Shell exit2**.
No threshold change, cherry-picking or additional model rerun was performed.
The confirmed scope saves packing work but keeps30 model forwards on both
sides; profiler event counts remain close. The remaining generation cost must
be profiled separately before choosing another optimization. This candidate
does not add a dense Attention path or claim to explain that residual cost.
**The prior Stage1 pair-2 P99 anomaly remains unexplained and open**, regardless
of whether a similar outlier appears here. No NoTTT608ms causal comparison or
Episode throughput/SR benefit is claimed across different experiments.

- All60 measured Vision/raw15 Action outputs exactly match the reference,
  max abs=0, with unchanged assertion tolerances. Instrumented/uninstrumented
  audit and repeated-original also exact; changing Prefix changes actual Action.
- All28 layers, both modes:30forwards,29gen-only,30Prefix contexts/projections.
  Each new request refills its own text cache and builds a fresh template.
- Native **total** pack calls31→2: one common `_prepare_inference_data` pack
  per request plus denoising pack30→1. Count assertion covers total calls.
- Source identity, frozen Prefix/FW and checkpoint metadata hash unchanged,
  recompile limit8 retained; process exits2 for performance NOT_MET, no owned
  model process remains. Numerical correctness PASS is a separate result.
- Single post-timing profiler CUDA events, including copies:
  39667→38654.
  This is a single profiler sample, not a30-run kernel statistic. Full memory,
  VAE, mean and tail statistics are in `gpu/gpu_statistics.json`.

GPU01 on prior Root1568888c/same Child passed numerical audit but stopped on the
benchmark's incorrect assumption of30/1 total calls. Actual31/2 includes the native
preparation pack. New Root18be4a80 corrects only that assertion; the original
failure remains hashed/server-only. GPU02 is the new complete numerical PASS /
performance NOT_MET run, not a relabeling or complete Gate PASS.

Only derived metrics/hashes and author-created reducer source are published.
The 31 raw model inputs/outputs, logs/JSON/profile
artifacts remain on the server with SHA256/size bindings. Source directory:
`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_codex_issue31_prefix_pack_20261109/root2`;
raw output `.../gpu02`. Existing Stage1 private files were not modified/exported.

## Requested Gate

Please independently review exact **Root18be4a80 / Child193627f4** against approved
Stage1, focusing on template eligibility, current Prefix/noise/time retention,
request/error lifetime, unchanged NoTTT/strict Resume and isolated numerical/perf
evidence. Keep this candidate and upstream PRs Draft/unmerged. Author CPU/GPU
correctness evidence does not close the performance/independent Gate or authorize V3 promotion, a dense
Attention redesign, training, real Sim/SR or900EP.
