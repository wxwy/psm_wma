# V3 Phase 1B cache-to-flat-source binding — GPT fresh source review r2

- 日期：2026-10-05
- Gate：`V3-CORRECTED-PHASE1B-CACHE-SOURCE-BINDING`
- formal root：`d7aa56730b8d04c50ed471179a0c08a038f3c07e`
- formal child/Gitlink：`21e60d6eb3a04846ffa7280aca18f6005399363e`
- design authority：`docs/build/PSM-WMA_V3_phase1b_cache_source_binding_design_v0.4_2026-10-05.md`
- parent implementation：`610737dd841dd2cd6ef3a3661d323808d41b8ef7 / db2701554ae26c50e26d1854ef3b1182de37118d`

## Verdict

`APPROVE_TO_RUN_PHASE1B_CPU_STATIC_EVIDENCE_ONLY`

这是 source-review / execution authorization，不是 Phase1B closure。
ds 只执行下面 exact-pair CPU/static Evidence；禁止修改 production code、正式测试、Gitlink。

## Fresh source review

parent pair 的唯一 blocker 已闭合：

- `RoboCasaExactWindowSourceReader.summary()` 现在显式输出：
  - `missing=0`
  - `ambiguous=0`
  - `task_mismatch=0`
  - `frame_mismatch=0`
  - `row_mismatch=0`
- formal test 精确断言上述 keys/values。
- actual mismatch 仍保持 constructor/read fail-closed，没有引入宽松继续执行路径。

formal child 相对 Phase1A parent `a40e8b782e0692e0a24e2f60893e9f4f8d858961` 仅三文件：
1. `robocasa_exact_window_cache.py` — backward-compatible identity API；
2. `robocasa_exact_window_source.py`；
3. `robocasa_exact_window_source_test.py`。

source review 未发现新的 Phase1B blocker：
- cache corpus authority 保持；
- flat-v3 only；
- official LeRobot action/state delta-query/caption；
- local-only/no-video minimal subclass；
- exact cache episode set；
- absolute→relative mapping；
- task-class annotation vs natural-language caption 分离；
- global-row / episode / frame / annotation / padding runtime exact validation；
- raw action12/state16 no-conversion；
- no model/trainer/inference/server/eval/GPU scope leak。

cx 作者自测报告：Phase1A+Phase1B combined target pytest `115 passed`，Ruff check/format、diff-check PASS。作者自测不替代 ds Evidence。

## Authorized ds Evidence

工作目录：`/disk/rl/psm_wma_v3`。

### A. exact pair / scope lock

1. `git fetch origin V3`
2. `git -C cosmos-framework fetch origin v3-local-ttt`
3. verify formal root object exists：
   `git cat-file -e d7aa56730b8d04c50ed471179a0c08a038f3c07e^{commit}`
4. verify formal root gitlink：
   `git ls-tree d7aa56730b8d04c50ed471179a0c08a038f3c07e cosmos-framework`
   must equal `21e60d6eb3a04846ffa7280aca18f6005399363e`
5. verify child HEAD / origin child = exact child or checkout exact child without editing；
6. scope：
   `git -C cosmos-framework diff --name-only a40e8b782e0692e0a24e2f60893e9f4f8d858961..21e60d6eb3a04846ffa7280aca18f6005399363e`
   must be exactly three Phase1B files.

### B. target pytest — CPU/offline only

From `/disk/rl/psm_wma_v3/cosmos-framework`:

```bash
CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 LD_LIBRARY_PATH='' PYTHONPATH=. OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /disk/rl/worktrees/cosmos-framework-v3/.venv/bin/pytest -q   cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cache_test.py   cosmos_framework/data/generator/action/datasets/robocasa_exact_window_source_test.py   -o addopts='' --tb=line
```

Expected: `115 passed`，0 failed/error。

### C. static

Changed files:
- `cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cache.py`
- `cosmos_framework/data/generator/action/datasets/robocasa_exact_window_source.py`
- `cosmos_framework/data/generator/action/datasets/robocasa_exact_window_source_test.py`

Run：
1. Ruff check；
2. Ruff format --check；
3. `git diff a40e8b782e0692e0a24e2f60893e9f4f8d858961..21e60d6eb3a04846ffa7280aca18f6005399363e --check`
4. exact scope name-only。

### D. Evidence persistence

Use fresh directory:
`/tmp/psm_wma_v3_phase1b_ds_evidence_r1/`

Save raw outputs for:
- fetch/pair/gitlink/scope
- pytest
- Ruff
- format
- diff-check
- timestamp
- summary

PASS iff all A/B/C are green.

任一失败：
- 停止；
- 保留完整输出；
- 返回 GPT；
- 不修代码；
- 不扩大测试；
- 不访问训练服务器/真实 cache/source；
- 不使用 GPU/训练/仿真。

## Boundary

即使本 Gate PASS，也只证明 synthetic/local CPU/static Phase1B contract。
仍未证明真实训练服务器 cache/source、Phase2 raw15/state15、ActionSFT/model cache-hit、Local/TTT、GPU、训练、仿真或 SR。