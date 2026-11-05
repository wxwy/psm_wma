# Issue18 R05 Action decode — incremental Code Gate request

Date: 2026-11-05 (Asia/Shanghai). Author: Codex. **Author targeted CPU PASS; GPT Code Gate PENDING.**

## Exact implementation and source scope

| Identity | Full SHA |
|---|---|
| New Formal Root | `f4871059cf28a7e2142325738decbf1d53c3148b` |
| New Child / Root Gitlink | `b3098008375c275a36dd2f50cbaf757bedf493ea` |
| Requested baseline Root | `c9fa60b7134fda8fb848c29c148f25c7a8901892` |
| Requested baseline Child | `4e9c8104ffd15a373b576bc35ee608de1b60eea1` |

Both isolated branches: `v3-r05-action-decode-compile-20261105`. Owner request-only Root `8004106fd3c1e357439c53c3f134933e5c1a5bf0` is a direct child of baseline c9fa; it and subsequent task-claim documentation are retained. Evidence/Inbox successors are bookkeeping, not replacement Formal SHAs. Root formal commit changes only Gitlink, SESSION and TODO. No Root production source changes.

Child changes exactly four files under `cosmos_framework/model/generator/mot/`:

- `cosmos3_vfm_network.py`: replace the two decode `llm2action` calls with `_project_action_predictions`. The new private Tensor-only method returns the original `self.llm2action` result directly.
- `parallelize_vfm_network.py`: compile that projection instead of the entire `_decode_action`, with the same `compile_options`. Other heads, including `_project_action_tokens`, retain their existing behavior.
- `parallelize_vfm_network_test.py`: update the expected compile target name only; retain all scope/options assertions.
- New `action_decode_compile_test.py`: 26 CPU cases using the actual network, packing classes, installer and projectors.

Decoder metadata, noisy-index/domain alignment, gather, unpack/scatter, output dictionary mutation, clean zero dtype and dummy branch remain eager and otherwise unchanged. The dummy path retains `action2llm → optional modality embedding → llm2action`, including `0 * preds_action.sum()`. For absent Action/tokens it retains the original dummy output rather than substituting zeros. No new Module/Parameter, state key, detach, cast, catch/fallback or recompile-budget change.

AST checks prove the complete prior decoder body differs only in the two callees; the helper only calls `llm2action`; the two encode methods are unchanged; prior encode test bytes are unchanged. Compile installation differs only in the decode target and explanatory docstring. Static forward CUDA-graph scope retains its original static policy.

## Raw author CPU evidence

[Evidence summary](../../../../artifacts/vfm_action_decode/2026-11-05_cpu/final_summary.json), [raw final JUnit](../../../../artifacts/vfm_action_decode/2026-11-05_cpu/formal-targeted/junit.xml), [original command and environment](../../../../artifacts/vfm_action_decode/2026-11-05_cpu/formal-targeted/command.json), [evidence README](../../../../artifacts/vfm_action_decode/2026-11-05_cpu/README.md).

| Check | Actual result |
|---|---|
| Controlled baseline RED | 4/4 expected FAIL, each real `FailOnRecompileLimitHit` in `_decode_action:1249`, default limit8, 8 completed requests / 8 graphs |
| Final clean-Pair CPU | **77/77 PASS**, 26 new + 51 prior, exit0, zero failure/error/skip; 8 GPU/L1 cases explicitly deselected |
| Source identity | Exact new Pair, both trees clean before/after; all 1229 recorded source fingerprint entries unchanged |
| B1–8 long sequence | Four FP32/BF16 × local-enabled/disabled groups, 1024 requests each, **2 graphs each**, cap8, no reset within a sequence |
| CPU Inductor | FP32 and BF16, 32 mixed requests each, real forward and backward; **3 graphs each**, cap8 |
| Old eager vs new eager | **96/96 bit-exact** outputs, dtypes, input/full parameter gradients including None-vs-zero, matching state keys and within-model parameter identities |
| Compiled vs eager | AOT-eager and Inductor outputs/gradients pass explicit FP32/BF16 tolerances |
| Ruff / format / syntax | Four changed Python files PASS; source-scope/AST checks PASS |
| Author-side peer audit | Separate agent read-only inspection: no new blocking finding; did not execute tests or edit source |

Final pytest ran for 61.60s (recorder wall time 67.188s). Development 77-PASS run is separately archived and is not added to the final test count. Old RED worktree had the untracked new test, so it was not globally clean; tracked production and Child identity remained exact 4e9. Same RED/GREEN test SHA256: `a3f8b194bd4cc6145b0d97fd68c308479cd61f8918beabe40adcdd7abab64554`. The controlled old final guard was `len(packed_seq.action.tokens) == 5`, matching the reported R05 failure class. This does not establish every guard or timing condition in the real server run.

The 96 eager references were generated from old production before modification; golden SHA256 `abdfe3824f44c347ada18834913d7abfbf175a25bca096241158ec6bba8be86c`. They are synthetic CPU tensors, not checkpoint files. Final production network SHA256 `12216ef9ffdf4ed8ff9359f89c4437a0280baf375ae19720bc6126f3467b2c87`.

Coverage includes real 15D/H16-shaped synthetic Action, ragged lengths, scalar/framewise domains, mixed clean/noisy samples, reordered noisy frames, absent Action/tokens, all three projector types, modality embedding on/off, invalid inputs, output sentinel preservation and dummy gradient connectivity. Clean Action zeros retain token dtype; absent Action retains the raw dummy projection result. No-noisy branches retain zero gradients where the old model had a live zero-valued graph, rather than changing them to None.

Environment: existing Python3.12.14, PyTorch2.10.0+cpu, pytest9.0.2, Ruff0.12.7, transformers4.57.1; GPU visibility and LD_LIBRARY_PATH empty, offline model access, BLAS threads1, isolated caches. No dependency installation or dependency-source modification for this task. The test backend chooser wraps `torch.compile` only to supply/count CPU eager, AOT-eager or Inductor backends while invoking the actual production installer/options. The external recorder does not wrap project behavior. Full commands, stdout/stderr, JUnit, source snapshots, witnesses, scripts and generated eager reference are in `cpu_evidence.tar.gz`; its SHA256 is listed in `archive_manifest.json` and `SHA256SUMS`. No server files were read or uploaded.

## Review and next execution boundary

Please review this narrow decode increment against baseline c9fa/4e9 and issue **APPROVE_CODE / REQUEST_CHANGES** for the exact new Pair. The prior encode approval is historical context, not an approval of this increment. Author-side peer inspection is not GPT or DS independent acceptance. This task did not repeat Issue17's full 869 tests or unrelated EvalV2 suites.

Not exercised: CUDA BF16 `grouped_mm` alignment, CUDA Inductor, actual FSDP lifecycle, CUDA graph capture/replay, whole-model inference, complete Local Scan/adaptation trajectories, GPU throughput, real DCP load or real RoboCasa. Local-enabled CPU action-head fixtures are not full Local-TTT acceptance. CPU bmm and timing do not prove H100 kernel correctness or performance.

After approval, GPT owns isolated integration with Issue17 Formal `551b03621507dde52303f54290d4fea89d66e8da` / `82fa270e8cdb76b3e1a4e94adf0c7ce2b497884e`, freezes a **new integrated Pair**, and performs the authorized real H100/RoboCasa validation with original `iter_000027700` DCP + matching config, real raw `[16,15]`, Local-TTT required and M16/B8. Check mixed B1–8, logits/actions as applicable, compile graph/guard evidence and throughput before interpreting the run. Actual checkpoint head width/padding/crop remains its own configuration; do not substitute a synthetic 16D model as real 15D acceptance. A 15D tiny CPU model also does not by itself establish CUDA alignment.

Strict M/B Resume consistency, Manifest/source verification, checkpoint/Session/Local-TTT algorithms, Issue17/G2 and official V3 remain unchanged. Do not ordinary-Resume R04's 648 or R05's 12 valid Core with the new source. Those results and run directories were not accessed or modified. Runtime R05 observations here come from the Owner/GPT request, not Codex server readback. No GPU/DS dispatch, V3 merge or old-run migration is authorized by this submission.
