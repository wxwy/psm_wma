# V3 Phase 2 raw15/state15 + H_pred16 — GPT fresh source review r3

- 日期：2026-10-05
- Gate：V3-CORRECTED-PHASE2-IMPLEMENTATION
- formal root：471b7fec4f50296efb3a328735dc2611b900995f
- formal child/Gitlink：ce07cb6f4a3f7792d85b7583ff6c8bda0bfa0cb0
- design authority：docs/build/PSM-WMA_V3_phase2_raw15_state15_hpred16_design_v1.1_2026-10-05.md
- parent Phase1B child：21e60d6eb3a04846ffa7280aca18f6005399363e
- supersedes implementation reviews for 8b21e7b1/826c7ca0, 6d033018/9819cec5

## Verdict

APPROVE_TO_RUN_PHASE2_CPU_STATIC_EVIDENCE_ONLY

这是 source-review / execution authorization，不是 Phase2 closure。
ds 只执行下面 exact-pair CPU/static Evidence；禁止修改 production code、正式测试、Gitlink。

## Fresh source closure

r2 唯一 blocker 已闭合：

1. CorrectedRoboCasaPolicyContract 构造时把真正参与 runtime authority 的三项保存成 immutable private snapshot：
   - _vae_compute_dtype: str
   - _vae_exact_durations: tuple
   - _vae_chunk_frames: tuple-of-tuples
2. resolve_tokenizer_config / validate_tokenizer_config 不再读取可被 caller 原地修改的 public vae_encode_contract nested objects。
3. public manifest copy仍保持原始 dict/list 形态，便于日志/serialization，但对其 mutation不再改变 runtime authority。
4. formal tests覆盖：
   - source manifest object 构造后被修改；
   - public contract copy exact durations被改成 [33]；
   - public compute dtype被改成 float32；
   - public chunk frames被清空/改写；
   - resolver最终仍使用构造时 [17,61] 与 manifest required chunk；
   - bad [33] / bad dtype / missing required manifest chunk 仍 fail。
5. GPT 独立重放 exploit：
   public = {compute_dtype=float32, exact=[33], chunks={480:24}}
   resolved exact = [17,61]
   resolved chunk[256] = 68
   validate resolved PASS
   validate exact=[33] -> ValueError

## Other source findings retained PASS

- child relative Phase1B parent only adds:
  - robocasa_exact_window_policy.py
  - robocasa_exact_window_policy_test.py
- official raw12→raw15 / state16→state15 private helper bridge；
- no copied rotation implementation；
- 17-row WAM row0 clean/noisy/mse/loss semantics；
- ActionProcessor raw15→pad64/no-normalization；
- H_pred/chunk16, obs17, R<=16 corrected contract；
- manifest full exact-duration authority + fixed Edge chunk capability；
- caller-supplied tokenizer config preservation including WAN_VAE_PATH；
- current legacy Nano/Edge chunk32/[33] reject；
- no core/model/packing/loss/old recipe/H100/trainer/inference/server/eval modifications。

cx final-tree author self-test:
- Phase1A+1B+2 targeted pytest: 137 passed
- final tree rerun: 137 passed
- Ruff check PASS
- Ruff format --check PASS
- diff-check PASS

作者自测不替代 ds Evidence。

## Authorized ds Evidence

工作目录：/disk/rl/psm_wma_v3

Fresh Evidence dir：
/tmp/psm_wma_v3_phase2_ds_evidence_r1/

### A. exact pair / scope lock

1. fetch root V3 and child v3-local-ttt
2. verify formal root object 471b7fec4f50296efb3a328735dc2611b900995f exists
3. formal root gitlink must be ce07cb6f4a3f7792d85b7583ff6c8bda0bfa0cb0
4. child HEAD and origin/v3-local-ttt must equal ce07cb6f...
5. diff name-only from Phase1B parent 21e60d6e... to ce07cb6f... must be exactly:
   - cosmos_framework/data/generator/action/datasets/robocasa_exact_window_policy.py
   - cosmos_framework/data/generator/action/datasets/robocasa_exact_window_policy_test.py

### B. target pytest CPU/offline

From child workdir run Phase1A + Phase1B + Phase2:
- robocasa_exact_window_cache_test.py
- robocasa_exact_window_source_test.py
- robocasa_exact_window_policy_test.py

Environment:
CUDA_VISIBLE_DEVICES=''
COSMOS_DEVICE=cpu
HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1
LD_LIBRARY_PATH=''
PYTHONPATH=.
OMP_NUM_THREADS=1
MKL_NUM_THREADS=1

Use existing V3 venv:
 /disk/rl/worktrees/cosmos-framework-v3/.venv/bin/pytest
with -q -o addopts='' --tb=line

Expected: 137 passed, 0 failed/error.

### C. static

Changed Phase2 files:
- robocasa_exact_window_policy.py
- robocasa_exact_window_policy_test.py

Run:
- Ruff check
- Ruff format --check
- git diff 21e60d6e..ce07cb6f --check
- repeat exact scope name-only

### D. independent immutable-authority probe

Run a small CPU/offline Python probe against formal child:
1. construct exact=[17,61], chunk={256:68}, bfloat16
2. mutate public contract to exact=[33], chunk={480:24}, float32
3. resolve from current Edge tokenizer candidate
4. assert resolved exact == [17,61]
5. assert resolved chunk[256] == 68
6. validate resolved PASS
7. validate exact=[33] raises ValueError

Save raw output.

### E. persistence

Save every raw command output, timestamp, exact SHAs, scope, pytest, Ruff/format/diff, immutable probe and summary into fresh Evidence dir.

PASS iff all A/B/C/D green.

任一失败：
- stop
- preserve full outputs
- return GPT
- ds does not repair code
- no GPU/training/simulation/real training assets

## Boundary

Even PASS only closes synthetic/local CPU/static Phase2.
It does NOT authorize:
- Phase3 video_latent transport / OmniMoT cache-hit
- Local-TTT integration changes
- real cache/source asset validation
- GPU/training/inference/simulation/SR
