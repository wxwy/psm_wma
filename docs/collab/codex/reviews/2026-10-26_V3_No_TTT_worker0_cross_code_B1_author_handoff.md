# B1 author CPU supplement — old workers0 to candidate workers0

2026-10-26. **Author Evidence only; no Gate closure or real Resume authorization.** Responds solely to HIGH Evidence-only B1 in GPT review at V3 `05230424baa79f24a6385e19d553170f40ca30c5`.

| Authority | Exact SHA |
| --- | --- |
| Original production implementation | `76d1cc70622d3b456a3c388ad98917b7d532890b` |
| New test-only Root target | `35d85f81ba6925e718a87d721b80686745791c60` |
| Child / Root Gitlink (unchanged) | `3e5bf90b4eb5fa5cbad9fa7ab62e86bf44c6b07b` |
| Old pre-worker baseline Root | `e6ae2084305a8c24d763d82b517984660cc73c30` |
| Old pre-worker baseline Child | `923d9c3fd392e6bafbdb1771a292c7b313e6b3dc` |
| Root candidate branch | `v3-nottt-process-workers-20261026` |

This new Root adds **one test file plus SESSION/TODO**, no production source or Child change. `scripts/`, `configs/`, `third_party/`, Gitlink and entire Child equal the reviewed original implementation. Later evidence/docs HEAD is not a new production implementation. Do not repeat the closed findings or whole source audit; review this scoped test/Evidence supplement. Original GPT production Gate remains REQUEST_CHANGES pending reviewer disposition of B1.

## What actually ran

`tools/v3/no_ttt_legacy_worker0_resume_test.py` exports the pinned baseline Git source with `git archive`. Inactive historical asset symlinks are omitted **without following them**; paths are recorded, no Python source symlink accepted. All baseline Python source comes from the original923d9c3 Child. A separate old interpreter imports the actual old Phase5 and Trainer; echoed import origin/hash is compared to Git blobs. A separate candidate interpreter imports actual3e5bf90b source. This is not old code dynamically executed inside new module globals, and not a newly fabricated worker>0 sidecar.

Old production `training_identity`, `config_digest`, `JobLifecycle.write_config` and `NoTTTFrontierCallback.state_dict` create the original **synthetic** Job with the literal formal No-TTT world4 job name, canonical YAML/pickle/identity and four Rank CPU states. Model/optimizer/scheduler/data are deliberately synthetic: the test does not instantiate the actual official Cosmos/FusedAdam or load a real DROID checkpoint. Identity fields model the frozen world4 profile; real Job/config/DCP were never read.

Two geometries each execute rank0..3 sequentially: **T16/B8/GA4/world4**, full member counts128/128/128/128 and terminal128/8/128/8. Old worker0 saves after optimizer update2, then uninterrupted old worker0 computes reference updates3 and4. Candidate worker0 restores those exact files in the same synthetic namespace, without adding worker CLI options, changing config digest/identity or frontier schema. It replays updates3 and4 against the old uninterrupted reference.

Exact equality covers all transformed payload/action/state/latent/masks/augmentation metadata, real native collation, Consumer/slot/member order, weighted per-member toy loss, pre-optimizer and pre-zero gradients, model tensor, SGD momentum, scheduler/scaler state, trainer iteration, full committed per-rank Frontier and Python/NumPy/Torch CPU RNG after each update. Candidate deliberately perturbs process RNG before restoring old state. The native model boundary is a differentiable scalar Generation toy with no prefix kwarg; **not a claim of Cosmos outer-loss/GPU gradient validation**.

Old checkpoint format remains `psm_v3_matched_no_ttt_frontier_v1`, with no loader-profile field; candidate loader remains absent. Old canonical Job/config/identity/state files are chmod0444 and their SHA256, mtime and mode are compared after every replay/negative. Production `check_job_namespace` accepts the original semantic identity unchanged. World4 source admission waiver is preserved; no new Root/Child Git pin or override.

Six negative cases: changed config or seed semantics rejected by actual namespace identity validation; wrong rank/profile, Frontier counter, config digest and iteration rejected by actual frontier restore before any native Forward or optimizer update. Each checks that original files remain unchanged. No validation is disabled and no old state rewritten.

## Author result and preserved evidence

**8 passed,0 failure/error/skip,68.54 seconds**. Ruff0.12.7 check/format and syntax/frozen test hash PASS. Existing601+42subtests/5old skips were **not rerun or aggregated**; their earlier Evidence remains unchanged and scoped to the earlier pair.

`docs/collab/codex/evidence/2026-10-26_nottt_worker0_cross_code_B1_author_cpu/` contains:

- `junit.xml`, `pytest.log`, `command.json`, `exit.json`, `STATUS.json`, environment/static logs and exact test patch;
- `B1_WITNESS.json`: old writer/new reader distinct PIDs, full/terminal counts, four-rank final Frontier witnesses and same semantic/config identity;
- `frozen_old_and_new_cpu_witness.tar.gz`: **65 original files**, including8 original old Rank checkpoints, canonical Job identity/YAML/pickle, old uninterrupted references, per-subprocess commands/import origin SHA/log/results and immutable-file witnesses; original bytes preserved;
- `frozen_witness_files.json` and `SHA256SUMS.json` bind archive contents and evidence artifacts; `shared_authorities_sha256.json` proves11 relevant shared training/planner/data/checkpoint files unchanged between baseline and candidate;
- `iterations/` retains two earlier failed attempts (safe archive rejection of inactive asset link, then JSON tuple/list fixture representation). Both are **not PASS**; fixed fixture only, no production relaxation. JSON-normalized comparison preserves exact tensor bytes and all ordered values.

Replay on a separate CPU checkout with pinned Git objects available:

```bash
CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  PYTHONDONTWRITEBYTECODE=1 NOTTT_B1_EVIDENCE_ROOT=<NEW_EXTERNAL_DIRECTORY> \
  HF_HOME=<WRITABLE_CACHE>/hf MPLCONFIGDIR=<WRITABLE_CACHE>/mpl XDG_CACHE_HOME=<WRITABLE_CACHE> \
  <CPU_PYTHON> -m pytest --noconftest -c /dev/null --rootdir=<ROOT> -p no:cacheprovider \
  -q -s tools/v3/no_ttt_legacy_worker0_resume_test.py --junitxml=<NEW_EXTERNAL_DIRECTORY>/junit.xml
```

Run from the detached Root target above; corresponding Child3e5bf90b must match Gitlink. Existing externally provisioned CPU environment must include project dependencies; author Python3.12.14/Torch2.10.0+cpu in environment.json. Full exact author command/env/subprocess source paths are retained. No GPU or production assets needed.

## Required disposition / stop

Request GPT scoped B1 Evidence review for test-only Root35d85f81ba6925e718a87d721b80686745791c60/Child3e5bf90b4eb5fa5cbad9fa7ab62e86bf44c6b07b, anchored to unchanged production76d1cc70/3e5bf90b. No reopening of Worker implementation design. If accepted, DS_PRO independent CPU and **separately Owner-authorized real4-rank DCP/CUDA-RNG same-job Resume** remain required. No physical concurrent Gloo/NCCL/FSDP or real save/load was executed. The synthetic2→3/4 witness does not establish that any active real checkpoint can safely Resume.

**workers0→workers1/2/4 and positive-worker count changes remain rejected.** No migration design or guard relaxation is included. Do not stop running No-TTT/G1, alter live files, merge candidate into V3, run GPU/real DCP/model/source/cache, or begin migration on this author result. Codex STOP after candidate publication/readback.
