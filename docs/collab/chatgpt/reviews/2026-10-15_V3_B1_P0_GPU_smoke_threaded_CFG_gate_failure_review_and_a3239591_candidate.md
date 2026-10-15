# V3 B1 P0 GPU Smoke — Threaded CFG Diagnostic Gate Failure and Fix Candidate

**Date:** 2026-10-15  
**Reviewer:** GPT — Code/Evidence/Gate reviewer  
**Executor evidence:** Owner-pasted `DS_PRO — V3 B1 P0 GPU Smoke · 46e9cc0e · 2026-10-15`, 123 lines, real 8×H100 runs (Source only).  
**Old executable:** `46e9cc0e5dc97a1f7f813b2a332b095aa1062a4a` / Gitlink `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`.  
**New candidate executable:** `a32395911c9913a5e02eb8a17e0bac11fe9ff4e0` / Gitlink **unchanged** `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`.  
**Exact new diff:** `tools/gates/v3_gateb1_producer_cfg.py` and `tools/gates/test_v3_gateb1_producer_cfg.py` ONLY. No frozen Index8/Packed128 Child/Root, model, trainer, optimizer, DCP, numeric policy, B0 or datasets modified.  
**Status:** `OLD_SHA_P0_GPU_SMOKE_BLOCKED` / `NEW_SHA_CPU_VERIFICATION_PENDING` / `NEW_SHA_GPU_NOT_AUTHORIZED`. Do not inherit old CPU PASS or reuse old Owner GPU authorization for a different code SHA.

## 1. What the real GPU evidence establishes

SOURCE Index8 8×H100 initialization, distributed rank mesh, native model/optimizer construction, full original same-job iter1300 DCP restore **reached success** in the authenticated old-SHA job after changing CWD to frozen Child root. No NaN/OOM/CUDA/NCCL fault was reported. First actual `training_step → produce → scoped_python_cfg_rng` tripped B0's guard `threading.current_thread() is threading.main_thread() and threading.active_count()==1`. Real per-rank thread count 8–13 after model construction, so the guard always rejects the legitimate framework background threads even though producer has `num_workers=0`.

All SOURCE attempts ended before a completed iter1301. No evidence tensors/JSON or actual gradient/optimizer numeric pairs were produced. TARGET Packed128 was **correctly not launched**. Original iter1300/latest light immutability witness was unchanged, frozen worktrees clean. This is a **DIAGNOSTIC CFG GUARD incompatibility** with multi-threaded GPU process; **not** proven optimizer/data/model or Packed128 parity failure.

The first attempt's `Nemotron-2B-Dense-VL.json` FileNotFound was **launch CWD**: the original frozen Child's model config uses CWD-relative path. The next attempts launched with CWD = frozen Child root, correctly resolving it. All future GPU runbooks must explicitly `cd "$LEG_ROOT/cosmos-framework"` before each `torchrun`, without modifying frozen code.

## 2. Code root cause

Original diagnostic `tools/gates/v3_gateb1_producer_cfg.py` injected the B0 `scoped_python_cfg_rng`, which temporarily calls process-global `random.seed`, then restores the process-global state after `ActionTransformPipeline`. Its **single-Python-thread** gate was a valid fail-closed guard for B0 CPU-only offline planning; relaxing only `active_count()==1` would expose other framework threads to a transient global RNG state and could invalidate exact Source/Target CFG witness parity.

The frozen Child contract was checked directly:
- `ActionSFTDataset._transform` is **`ActionTransformPipeline`** in both frozen comparison legs, constructed with `format_prompt_as_json=True`, `cfg_dropout_rate=0.1`.
- In `ActionTransformPipeline.__call__` the JSON prompt formatter runs **before** `self.text_tokenizer(data_dict)`.
- Frozen `TextTokenizerTransform.__call__` calls exactly one `random.random()` for the caption CFG decision when `cfg_dropout_rate>0`. It otherwise delegates unchanged to the native `_processor.tokenize_text` and stores the token tensors.
- JSON prompt formatter has no random-site use in the frozen Source Child. No idle-field dropout augmentor is enabled for this JSON-format recipe; `num_workers=0` and main transform thread remain mandatory.
- B0 `ConsumerKey` seed is `stable_seed(key.scoped("cfg_dropout","caption"), domain="python_cfg")`.

## 3. New isolated B1 code implementation — candidate, NOT approved

At new exact CODE SHA `a3239591...`, only `v3_gateb1_producer_cfg.py` changes the **real B1 runtime** to `scoped_keyed_native_caption_transform(key, original_pipeline)`:
1. Validate B0 ConsumerKey, exact frozen class provenance, one-caption tokenizer, JSON prompt, no idle augmentor, caption key and 0.1 dropout rate; enforce **main transform thread** but **not** absence of unrelated FSDP framework background threads.
2. Draw the one B0-equivalent Bernoulli decision from **`random.Random(seed).random()` (a local RNG)**, rather than changing or borrowing process-global `random`. Preserve same per-Consumer seed.
3. `copy.copy()` the genuine native ActionTransformPipeline and its genuine TextTokenizerTransform, set **only the cloned tokenizer's** CFG dropout rate to 0 to avoid a second/global draw; inject the identical caption blanking decision immediately before calling **the native tokenizer implementation**. All other original native transform/JSON/tokenization/action logic remains.
4. Never patch `random.random` globally or mutate original native pipeline/tokenizer; restores original producer/SFT method overrides even on exceptions. Fail-close if tokenizer not called exactly once or called twice, wrong source, worker thread or unverified stochastic augmentation.
5. Existing B0 `scoped_python_cfg_rng` and its previously closed CPU tests remain **untouched**. Existing B1 Fake Producer tests remain compatible: a context yielding no alternate transform still uses the original transform.

Five new CPU synthetic regression tests added in `test_v3_gateb1_producer_cfg.py`: Consumer-dependent native CFG equality+global-RNG preservation (64 keys), an actual B1 producer-scope witness with a live background Python thread (two deterministic replays), unsupported CFG/rate/provenance rejection, missing/duplicate tokenizer calls rejection, and non-main-thread refusal.

**Qualification:** This source-level design is consistent with both frozen Child APIs, but it has NOT yet been run by independent DS_PRO CPU or real GPU at the new SHA. Any pending ABI issue (copy mechanics, actual tokenizer service, raw Native payload) requires DS evidence and a new code fix, not silent waiver.

## 4. Required independent DS_PRO Gate (no GPU)

- Detached clean diagnostic Root `a32395911c9913a5e02eb8a17e0bac11fe9ff4e0` / Child `8f3672...`; compare `46e9cc0e..a3239591` exactly two B1-only files.
- `python -m py_compile` 23 B1 impl/test files; `ruff check --no-cache` 23 files (0 findings); `pytest -q tools/gates/test_v3_gateb1_*.py` (prior 144 + five = expected **149**).
- Independently verify exact frozen Source and Target `ActionTransformPipeline` / `TextTokenizerTransform` ABI and no extra reachable global RNG site; no native model/GPU, no full preflight/451GB or original DCP loading.
- Producer main-thread/no-workers still required. Background threads must NOT block when unrelated; global random state cannot be altered by B1 adapter; stochastic per-Consumer payload hash must remain exact between independently replayed B1 legs.
- Any Ruff/test/ABI failure STOP with exact file:line and evidence; DS_PRO does not change GitHub. GPT handles source repair/review on new exact SHA.

## 5. GPU authorization is version-specific

An Owner approval was reported and verified in V3 at:
`docs/collab/chatgpt/approvals/2026-10-15_V3_B1_P0_GPU_co_resident_Owner_authorization_46e9cc0e.json`.
It binds old implementation SHA **`46e9cc0e...`**. The actual `_owner_receipt` compares its `implementation_sha` to the current diagnostic Root SHA, so it MUST reject this receipt for **`a3239591...`**. Do not modify/copy-edit/re-sign the old authorization in DS /tmp. A **new, explicit Owner P0 GPU authorization** binding the verified code SHA and original frozen pair, r2 policy SHA256 and original B0 checkpoint fingerprint is mandatory before any resumed GPU smoke.

Maintain co-resident 8×H100 min available VRAM and process non-interference; stop on environmental/real runtime fail-close conditions and do not use old diagnostic logs as parity evidence.

**Disposition:** old P0 smoke BLOCKED (no training step; no parity claim); new diagnostic CFG fix candidate committed, **CPU verification pending**; B1 GPU remains NOT AUTHORIZED for new code. Gate M and Formal30k HOLD. Closed B0 and datasets not repeated. Whole V3 audit deferred.
