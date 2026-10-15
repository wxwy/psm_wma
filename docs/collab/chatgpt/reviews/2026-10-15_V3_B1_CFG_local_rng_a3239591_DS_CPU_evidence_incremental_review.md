# V3 B1 CFG Local RNG — a3239591 independent DS CPU evidence incremental review

**Date:** 2026-10-15  
**Reviewer:** GPT, independent code/evidence/Gate  
**Formal implementation pair:** Root `a32395911c9913a5e02eb8a17e0bac11fe9ff4e0` / Child `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`  
**Prior root:** `46e9cc0e5dc97a1f7f813b2a332b095aa1062a4a`  
**Verdict:** `REQUEST_CHANGES` — **EVIDENCE-ONLY**. Production diagnostic fix has no confirmed code blocker in reviewed diff. **No GPU authorization.**

## 1. Verified GitHub diff and frozen boundary

At review time `v3-gateb1-numeric-implementation-20261014` pointed exactly to `a32395911c9913a5e02eb8a17e0bac11fe9ff4e0`; child Gitlink exactly `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`. Parent was `46e9cc0e...`. The diff touched only `tools/gates/v3_gateb1_producer_cfg.py` and `tools/gates/test_v3_gateb1_producer_cfg.py`. Frozen SOURCE Index8 `b159f459.../937066ff...`, TARGET Packed128 `c4731bca.../c8dabbb3...` are distinct; newer V3 Gitlink `1d56320c...` must not be substituted.

New B1 path creates a per-consumer local `random.Random(seed).random()` draw, shallow-copies the native ActionTransformPipeline and TextTokenizerTransform, disables CFG on the tokenizer copy and applies the same caption dropout before native tokenization; no mutation of process-global RNG state in the adapter. Main-thread, `num_workers=0`, key, class provenance, rate, and one-call checks remain. Old B0 global scoped RNG remains untouched.

Frozen SOURCE/TARGET TextTokenizerTransform source uses `random.random()` for caption CFG. Diagnostic Child `8f3672d1` uses `transform_draw(random.random)` at its caption CFG site; verify default/no-context scope preserves native behavior, including payload bytes. These are distinct source forms and not to be conflated.

## 2. Independent DS_PRO evidence received (report pasted by Owner)

DS says clean detached worktree; 23/23 compile, 23/23 Ruff zero findings, 149/149 pytest; 12/12 independent specialized checks. The new five tests cover local keyed draws, background threads, provenance/rate, duplicate/absent tokenizer, and non-main-thread refusal. DS reports 8f child ABI, a `random.seed(seed); random.random()` vs `random.Random(seed).random()` equality of `0.05192744157456752`, global RNG state preservation, 2x replay `('', [0])`, worker rejection, old Owner authorization SHA rejection, and no CUDA/DCP/model/torchrun activity.

These results support the reported code fix and remove the *old single-active-thread blocker* at synthetic CPU level; the execution report is not independently attached raw stdout/stderr or a full frozen-native payload comparison.

## 3. Current sole blocker — HIGH / Evidence-only

**Location:** `tools/gates/test_v3_gateb1_producer_cfg.py:134-230` (new synthetic `ActionTransformPipeline` and `TextTokenizerTransform` fixtures); `tools/gates/v3_gateb1_producer_cfg.py:20-80` (native runtime clone).  
**Root cause:** Current reported local-RNG replay witnesses use a synthetic native-named tokenizer yielding `('', [0])`; no directly inspectable real SOURCE/TARGET frozen Native TextTokenizerTransform token tensor bytes/hash or real prompt JSON/payload hash from two identical ConsumerKey runs. The DS summary calls out a 12-check pass but does not include requested hash/identity artifacts. The diagnostic Child's `transform_draw(random.random)` and the frozen legs' `random.random()` must be shown to produce identical observable caption/token payload under the actual frozen recipe and no interfering scoped draw authority.
**Frozen contract:** DS request `docs/collab/chatgpt/requests/2026-10-15_DS_PRO_V3_B1_P0_threaded_CFG_local_RNG_fix_a3239591_CPU_gate.md` §3(3), frozen r2 `docs/collab/chatgpt/designs/2026-10-15_V3_GateB1_r2_numeric_Owner_frozen_preGPU.md` §2: exact transformed CFG and token payload, not merely equality of Bernoulli RNG numbers or synthetic outputs.
**Acceptance:** DS (no GitHub changes) supplies a focused CPU-only /tmp evidence artifact binding exact diagnostic/Source/Target Child SHAs, same ConsumerKey/seed and controlled representative native JSON prompt; records native Tokenizer exact caption, dtype/shape and full token tensor SHA256 (plus transformed payload digest as applicable), Source vs Target vs B1 on both dropout and non-dropout cases, and replay with a live background thread plus the original global RNG state. Demonstrate the `transform_draw` default/no-scope case, or fail closed if extra ContextVar scoping changes it. This should use authentic native implementation and a safely constructed authentic tokenizer processor, not the synthetic class. No full data, DCP, GPU, or prior 149 test rerun. If real native CPU execution is impracticable, provide an independently auditable equivalent plus its limitations for further reviewer adjudication.

## 4. Disposition

- `REQUEST_CHANGES`: evidence-only, no established production implementation blocker; avoid changing the SHA unnecessarily.
- Existing DS 23 compile, 23 Ruff, 149 tests and 12 checks are acknowledged; **do not rerun them solely for this finding**.
- Old P0 GPU Smoke `46e9cc0e` remains BLOCKED before completed iter1301; no numerical equivalence witness.
- Old Owner GPU receipt exclusively binds `46e9cc0e`, rejected for new `a3239591`. New P0 authorization NOT GRANTED.
- Closed B0/451GB/old CPU Gate unchanged. Gate M and Formal30k remain HOLD. Final V3 full-repo review deferred.
