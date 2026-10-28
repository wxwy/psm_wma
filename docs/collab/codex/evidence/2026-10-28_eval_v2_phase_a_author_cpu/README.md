# Evaluation V2 Phase A — author CPU evidence, not native acceptance

Formal Root **`fd7e43f6630a436ab3d83edcd3ce9d1516b342d1`**, Child/Gitlink **`d2c1bda62880dbeee196f70945e5bc430b73f4b6`**. Isolated candidate branch in both repositories: `v3-eval-v2-slots-a-20261028`. Owner Issue8 was ACKed before implementation in Root `4292905afcf6dfd0ce4f00e336c35a7c09e319b0`. Approved source baseline remains Root4769d711777c20a72dd7a3f6071a96f08ad8abb0 / Child2d4a42590fead00ea16f6ae5902e2bc8382b07e2; that approval does not transfer to this new architecture.

**Review the FULL Phase A range `4292905a..fd7e43f6`**, including initial implementation1ac82af4 plus final late-exit qualification closure. `root_implementation.patch` covers that complete range. `root_last_commit_only.patch` is only the final small delta and cannot replace the full review. Child patch is2d4a4259..d2c1bda6. `root_vs_canonical.stat` additionally includes previously approved Stage2 code inherited only in this candidate; it is not the incremental Phase A scope.

`final03/` is the sole final author run: **255 passed =197 production-path +58 legacy regressions,0 failure/error/skip,178.04s pytest**; runner179.811s. `static_final03/` records Ruff0.12.7 check/format,37 AST parses, shell syntax/help and source whitespace checks. Test/static37-file hashes agree before/after and with the exact Formal Pair. `formal_source_bindings.json` binds52 source/config/test/shared-helper/runbook files to exact Git blobs;37 were additionally frozen in the test runner. `post_commit_identity.json` is the actual production source guard passing on clean committed Root/Child with equal Gitlink.

The25 G/N combinations execute the real production Runtime/Scheduler/SimSlot/native policy+HTTP/Local-client APIs; model/OS/GPU/physics boundaries are doubles. Default Root `_actor` creation and real Worker socket `serve` also run through a transport bridge, with only OS process/model/physics replaced. Other existing process tests use real owned CPU processes to verify cancellation, group cleanup, PID reuse refusal and parent death. Toy server state verifies fresh session W0 semantics and completed-evidence updates; this is **not GPU Local-TTT numerical validation**.

`synthetic_900_metrics.json`:900 actual dispatches,50 barriers,3 physical SimSlot objects/3 mock model loads,900 fake Task environment creations,450 synthetic successes+450 normal failures. The complete native-codec synthetic900 test took87.985s. It is deliberately deeper than the earlier scheduler-only test, so no speedup/regression claim against its timing is made. Current p95 claim76.89ms/Core commit27.14ms/lock wait65.54ms; two summary rebuilds max3.00s;10023 JSON reads/118688 cache hits. Whole-test `resource.getrusage(RUSAGE_CHILDREN)` reports maxRSS351012KiB (~342.79MiB), user CPU126.14s/system51.71s. This is a CPU process high-water measurement, not aggregate native Sim/GPU capacity.

`CPU_SYNTHETIC_runtime_artifacts.tar.gz` contains original synthetic900 Core/ledger output, Task-switch/session/seed/grant fixtures, default Worker transport, D4/Resume/quarantine/late-exit examples and tiny CPU FFmpeg **encoding** products. No real simulator, Cosmos weights, DCP tensors or benchmark SR is included. Production schemas appear because these tests execute production writers; synthetic Task/data do not become a real benchmark. Media remains outside SR and is never fully MP4-decoded by this Gate.

`counterfactual_late_exit_red/` and its runner snapshot retain a targeted RED proof: restore ONLY the in-memory `Runtime.run` AST from pre-final1ac82af4, without editing working files; the late-zero-exit assertion fails because the original scope could omit a completed current Slot. `draft_history/late_exit01/` and final03 pass the corrected case: Core stays immutable; clean qualification blocks; explicit execution-only Resume resolves the fault without a prediction or retest. **This is a new Phase A delivery edge, not the withdrawn Stage2 F1.** Commit/cancel locking was preserved and both lock orderings are tested.

`draft_history/` preserves all prior CPU runs/source hashes/commands, including fixture failures: wrong scheduler ledger level, fake metadata digest correctly rejected by the real Worker, port55004 collision in the OS ephemeral range, and transport template setup without an acquired Store lease. Corrections use real production contracts; no assertion, timeout or admission safety was relaxed. Previous252/254 green snapshots are different pre-final source, not additional final passes. One deprecated-pynvml warning remains in the CPU Torch RNG test. Static output-directory retry was external tooling only. Raw patches/logs retain original whitespace; do not normalize evidence to make artifact-level whitespace checks green.

## Independent replay after GPT Code Gate

Use a clean exact-pair worktree and existing CPU environment. Set `PSM_REPO`, `CPU_PYTHON`, and a **new external** `CPU_EVIDENCE_DIR`. Do not change a training/evaluation worktree. The frozen `author_*_snapshot.py.txt` files preserve author commands/machine paths; they are audit snapshots, not installers.

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

PASS requires0 fail/error/skip and frozen-source equality. Missing dependencies are an environment blocker, not permission to skip tests. This is a focused author CPU Gate, not full repository or DS acceptance. No native/GPU/real Action Server/DCP/RoboCasa/900, training/old431 operation, canonical merge or Phase B follows this package. Next is GPT new-pair Code Gate, then DS independent CPU; native capacity/semantics/Canary needs separate Owner authorization.
