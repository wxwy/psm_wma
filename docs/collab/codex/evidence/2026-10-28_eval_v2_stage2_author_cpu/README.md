# Stage2 author CPU evidence — synthetic, not native acceptance

Formal Root `4769d711777c20a72dd7a3f6071a96f08ad8abb0` / Child+Gitlink `2d4a42590fead00ea16f6ae5902e2bc8382b07e2`, isolated `v3-eval-v2-stage2-20261028` candidates. Approved input design: Root `1fd3ad42075032bd0137ac9a76306169aaa45032` / Child `746c5cf2f2324104a62fb71510343aa40d3976c5`. No V3 merge, native model/Action Server, real DCP, GPU, RoboCasa environment or old431 use.

`STATUS.json` is an author report, not a GPT/DS verdict. `final_cpu02/` is the single final run: **200 passed =142 production-path +58 legacy regressions,0 failure/error/skip,86.73s pytest**; runner88.057s. `static_final/` records Ruff0.12.7 check/format,34 Python AST parses, shell syntax/help and diff whitespace. Both gates share the exact same34-file snapshot. `formal_source_bindings.json` verifies49 source/config/runbook/test/shared-helper bytes against exact Root/Child Git blobs;34 were also frozen before/after pytest. `post_commit_identity.json` records the actual production source guard passing with clean Root/Child and equal Gitlink.

`root_implementation.patch` is the exact direct-parent Root diff (`1404c34e6cb46df68368d877c296bf95a5bcc9f4`→formal Root); Child patch is `746c5cf2…`→formal Child. `root_vs_canonical.stat` also includes the previously approved design/prototype inherited on this isolated branch; it is not the incremental Stage2 production scope. Canonical V3 was `4c9990f5bfab4544fe9edc69ba7227a07ef1ed8e` at the scope lock, with unchanged Child746.

`CPU_SYNTHETIC_runtime_artifacts.tar.gz` contains the original synthetic900 Store/Scheduler records, tiny CPU FFmpeg **encoding** products,17-action/two-replan native HTTP+Local-client example and selected failure/ownership/cache fixtures. No real simulator observations, Cosmos predictions, distributed tensor checkpoint or benchmark success rate is inside. Production schema marks `prototype_only:false` because these tests exercise production code; **this does not turn synthetic Task/sample data into a real evaluation**. The test actually overwrites then rebuilds a derived summary as a recovery check; Core bytes remain immutable. `artifact_selection.json` records original selection. Some negative fixtures intentionally lack complete results.

`synthetic_900_metrics.json`:900 dispatches,50 barriers,450 synthetic successes/450 normal failures; mock lifecycle3 model loads/18 environment constructions, not actual models/environments. This test took41.070s. Current machine p95 claim~28.31ms/Core commit~4.01ms, two summary rebuilds max~2.93s;8223 JSON reads/86814 immutable-cache hits. No comparison with native throughput or claim of full-stack speedup. `task_registry_source.json` records the pinned RoboCasa source reference used only via AST literal inspection to select the18 real Task classes, without importing the simulator.

`draft_history/` preserves earlier runs, failures, commands, source hashes and JUnit. They used different pre-final source; do not add their counts to200 or present them as final-version regression passes. Initial fixture scope/default/import mistakes were corrected. `production_full01` and `final_cpu01` are pre-final green snapshots, not additional final tests. One deprecated-pynvml import warning appears in the CPU Torch RNG test. No skipped tests are hidden. `environment.json` describes this CPU-only test environment (NumPy2.2.6), **not** the separately pinned native NumPy2.2.5/RoboCasa/MuJoCo runtime.

## Independent CPU replay

Use a clean exact-pair detached worktree and the existing CPU Python environment. Do not update an active training/evaluation checkout. Set `PSM_REPO`, `CPU_PYTHON` and a **new external** `CPU_EVIDENCE_DIR` locally. Commands below contain no native evaluation launch. The `author_*_snapshot.py.txt` files retain the unmodified author runner, including author machine paths, for audit; they are not a portable installer.

```bash
cd "$PSM_REPO"
mkdir -p "$CPU_EVIDENCE_DIR"
export CUDA_VISIBLE_DEVICES="" COSMOS_DEVICE=cpu
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export PYTHONPATH="$PSM_REPO:$PSM_REPO/cosmos-framework:$PSM_REPO/scripts"
export HF_HOME="$CPU_EVIDENCE_DIR/cache/hf"
export MPLCONFIGDIR="$CPU_EVIDENCE_DIR/cache/mpl"
export XDG_CACHE_HOME="$CPU_EVIDENCE_DIR/cache/xdg"
timeout --signal=TERM --kill-after=15s 600s "$CPU_PYTHON" -m pytest \
  --noconftest -c /dev/null --rootdir="$PSM_REPO" -p no:cacheprovider -q -s -x \
  tools/v3/eval_v2_production_tests \
  cosmos-framework/cosmos_framework/simulation/robocasa/closed_loop_eval_contract_test.py \
  cosmos-framework/cosmos_framework/simulation/robocasa/closed_loop_eval_lifecycle_test.py \
  cosmos-framework/cosmos_framework/simulation/robocasa/closed_loop_eval_manual_test.py \
  cosmos-framework/cosmos_framework/simulation/robocasa/closed_loop_eval_phase6_test.py \
  cosmos-framework/cosmos_framework/simulation/robocasa/eval_utils_test.py \
  cosmos-framework/cosmos_framework/simulation/robocasa/local_memory_client_test.py \
  --junitxml="$CPU_EVIDENCE_DIR/junit.xml" \
  >"$CPU_EVIDENCE_DIR/pytest.log" 2>&1
```

PASS requires0 failure/error/skip and frozen source equality, with production D1–D5/native-codec/process/media negatives retained. Missing CPU dependencies are an environment blocker, not a reason to skip/xfail tests. This replay is a focused changed-path Gate, not full repository CPU acceptance. Required later Gates remain GPT new-pair Code Review, DS independent CPU, and separately Owner-authorized native capacity/semantics/Resume Canary before any900 rollout authorization.
