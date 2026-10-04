# V3 Phase 1A cache-first exact-window catalog — GPT fresh source review

- 日期：2026-10-05
- Gate：`V3-CORRECTED-PHASE1A-CACHE-CATALOG`
- formal root：`459ff4bd30959cba916813c30c85faf51fad1db0`
- formal child/Gitlink：`a40e8b782e0692e0a24e2f60893e9f4f8d858961`
- parent implementation pair：`7c214251f3535116e7b19f964ee907e8653fd388 / e98f293f396df74bb7030d525c40faa21e7d226d`
- design authority：`docs/build/PSM-WMA_V3_Local_TTT_on_latest_Cosmos_RoboCasa_detailed_design_v3.0_2026-10-04.md`
- Phase0 mapping authority：`861849491488258214e96e778cff7d1bd0309089 / c00a014444083c7c554fff7626f48cceaf5c5c31`

## Verdict

`APPROVE_TO_RUN_PHASE1A_CPU_STATIC_EVIDENCE_ONLY`

这是 source-review / execution authorization，不是 Phase1A closure。
ds 只执行下面 exact-pair CPU/static Evidence；禁止修改 production code、正式测试、Gitlink。

## Fresh source review

formal child 从 `e98f293f...` 到 `a40e8b7...` 仍只修改：

- `cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cache.py`
- `cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cache_test.py`

r2 唯一 blocker 已闭合：

1. `_audit_files()` 现在扫描 recognized `tasks/*/episodes/*.pt` namespace 的全部 `.pt` payload；
2. 未声明 canonical episode、`episode_bad.pt`、短位数 `episode_7.pt`、其它 `foo.pt` 均进入 discovered/extra；
3. strict mode fail-closed；non-strict audit 中 discovered/rejected/extra 可见；
4. 新增三类定向 tests，未通过“放宽 regex 使 malformed 文件合法化”规避问题。

其余 Phase1A source contract 保持：
- cache manifest 决定 membership；
- declared missing 必停；
- portable locator 不信任 absolute episode_path；
- manifest SHA 与 machine-path-independent semantic corpus digest 分离；
- VAE contract 保留完整，只要求 exact durations 含17；
- lazy exact-key read，无 nearest/floor fallback；
- finite fp32 exact `[5,48,H,W]`、17 frame indexes / 5 anchor indexes；
- no raw dataset enumeration、no VAE/tokenizer fallback、no B1 endpoint/visual96。

cx 报告作者自测：60 passed，Ruff check/format、diff-check PASS；仅作自测，待 ds 独立 Evidence。

## Authorized ds commands

工作目录：`/disk/rl/psm_wma_v3`。
必须先核 exact pair：
- formal root tree 的 `cosmos-framework` gitlink = `a40e8b782e0692e0a24e2f60893e9f4f8d858961`
- child HEAD / origin/v3-local-ttt = 同一 SHA
- child formal diff 相对 `c00a014444083c7c554fff7626f48cceaf5c5c31` 只含上述两个文件

运行：
1. target pytest（CPU/offline）：
   `CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 LD_LIBRARY_PATH='' PYTHONPATH=. OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /disk/rl/worktrees/cosmos-framework-v3/.venv/bin/pytest -q cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cache_test.py -o addopts=''`
2. Ruff：
   `/disk/rl/worktrees/cosmos-framework-v3/.venv/bin/ruff check <两个 changed files>`
3. format：
   `/disk/rl/worktrees/cosmos-framework-v3/.venv/bin/ruff format --check <两个 changed files>`
4. `git diff c00a014444083c7c554fff7626f48cceaf5c5c31..a40e8b782e0692e0a24e2f60893e9f4f8d858961 --check`
5. scope：
   `git diff --name-only c00a014444083c7c554fff7626f48cceaf5c5c31..a40e8b782e0692e0a24e2f60893e9f4f8d858961`

PASS：
- pytest 全绿（expected 60 tests）；
- Ruff/format/diff-check exit 0；
- scope 仅两个 Phase1A files；
- exact pair 一致。

任一失败：保留完整输出，返回 GPT；ds 不修代码，不扩大测试，不访问训练服务器/真实 cache，不运行 GPU/训练/仿真。
