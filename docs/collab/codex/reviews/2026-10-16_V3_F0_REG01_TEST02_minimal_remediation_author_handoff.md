# F0 REG-01 / TEST-02 — minimal remediation author handoff

Date: 2026-10-16. Status: **candidate implemented; independent acceptance pending**. This author report is not a GPT verdict.

| Item | Exact SHA |
| --- | --- |
| New Root implementation | `9e51c94a6d5dba41bd37423b9db8e634ca433789` |
| New Child / Gitlink | `7cae7c3049310ccc3b7e44ce9769534e152d1f26` |
| Child parent | `0fb7f587f56048a8ffaa12e2fdb7891abc0fb021` |
| Previous reviewed Root | `b3b64732efb225c3ee08b1d9f317a90228112b29` (`REQUEST_CHANGES` remains) |
| Preserved V3 review/instruction HEAD | `ef9dd04464c8ac1ad08257b1f7cefb9ce7edea0b` |

New isolated branch in both repos: `v3-f0-reg01-fixture-20261016`. Root integrates the prior candidate history plus the latest GPT review/instructions without changing their contents. The Inbox append conflict retained both ledger blocks. No force push or V3 production merge. Later evidence/docs commits must not replace this implementation Root in validation identity.

## Two-file Child change

**F0-REG-01:** `examples/psm_wma_robocasa_corrected_phase5.py:739`: move the existing missing-`--dataset-index-root` ValueError guard to the start of preflight, before Namespace-dependent reads. No new guard or changed error string. Within `preflight`, Namespace rejection still precedes its `_load_runtime()` call, data/config/Trainer loading and all writes. The existing main/distributed initialization protocol is not changed by this patch. The production AST differs only in the order of the same preflight statements; every other top-level statement/function is unchanged.

The original `examples/psm_wma_robocasa_corrected_phase5_test.py::test_formal_and_resume_require_accepted_index_before_data_open` file is byte-identical to the reviewed Child (SHA256 `6b3582d101b57c9a2057ca84bd5edea76cc54df98fd5ebe5c6abed0881b6b60b`). Its original Fresh/Resume pytest assertions are retained. A new real-CLI negative verifies missing Index takes precedence even with an existing/foreign identity, never calls Namespace/runtime helpers, and preserves old bytes/mtime. Existing accepted-Index namespace rejection tests continue passing.

**F0-TEST-02:** `examples/psm_wma_robocasa_phase5_f0_test.py:167`: include `megatron` and `megatron.core` in the same temporary external-dependency sandbox as synthetic torch. Installed real Megatron no longer evaluates torch annotations against an incomplete fake torch. This does not uninstall, disable or modify Megatron in production. The actual imported Trainer takes its **Megatron-present** branch; the constructor fixture supplies the matching synthetic parallel configuration before reaching the unchanged writer-failure assertions. A new test checks that host Megatron is never accessed under fake torch and original host module identities are restored afterward.

All nine original `TrainerTests` names and assertion ASTs are unchanged; no skip/xfail/deletion or production-method monkeypatch was added to evade them. Actual Trainer method execution and prior synthetic model/device boundaries remain. Production `trainer/__init__.py`, DCP/RNG, Grouped Local/Native/optimizer, original regression file and Root launcher were not edited.

## Author CPU evidence and limits

Evidence: `docs/collab/codex/evidence/2026-10-16_V3_F0_REG01_TEST02_author_cpu/`.

- Python 3.12.14, pytest 9.0.2, Ruff 0.12.7. Direct unittest: 28 methods green. Pytest: **28 methods +32 subtests**, 0 failed/0 skipped, 1.97s; JUnit has 60 cases. The two runners execute the same suite; counts are not additive.
- Ruff check / format --check and syntax pass for both changed files and the unchanged affected original regression/Trainer files. Child `git diff --check` passes.
- Controlled external-module import collision: old fixture produces 9/9 `AttributeError: module 'torch' has no attribute 'dtype'`; new fixture executes the same nine tests with 9/9 success, no skips. Exact names, baseline tracebacks and fixed output are archived. This uses an explicit annotation-evaluating external module stand-in, **not the actual V2 Megatron environment**.
- The unchanged original Index regression function/helper AST executes with original `pytest.raises` assertions against the actual old/new preflight: old Resume fails with identity FileNotFoundError; new Fresh/Resume pass. This isolated function run does not imply full original-module collection was executed.
- `gate.json` records commands/cwd/return codes and SHA256 values checked against the committed Child; `scoped_probe.json` proves only production guard reordering, unchanged regression file and unchanged assertions for all nine cases.

**Actual full V2 dependency environment is not available on this CPU author machine.** The full-import Phase5 regression and nine TrainerTests in that environment remain mandatory DS checks. Local success is not a full-env closure or new Gate PASS. No model, real DCP, dataset scan, GPU or torchrun was used.

Root's merge preserves upstream GPT Markdown exactly, including its existing two-space line breaks. Whitespace diagnostics on those inherited review/request documents are not rewritten; authored Child source/static checks above pass.

## Unchanged contracts and accepted prior evidence

The baseline frozen F0 contract remains byte-identical, SHA256 `8f3e6d3c617e428e1142578266849f7da4f99390403678e732fc7470201b7fcd`; the remediation instruction supplies this narrow error-order/fixture amendment. Native Packed128 constant, budget parser/Trainer wiring, 30000/500/100 schedule, launcher, namespace/lease/claim/config snapshot and training-identity implementations are unchanged. Exact Pair is intentionally different, so its version-bound identity/digest must be used; no old job is relabeled or resumed.

| Prior DS evidence accepted by GPT | New diff impact |
| --- | --- |
| Two-process CPU Gloo agreement/writer errors | Collective and Trainer code unchanged; missing-Index preflight error precedence intentionally corrected. Prior shared-core witness may be reused after DS verifies scope. |
| Real configured Phase5 Preflight / full config serialization | With accepted Index, Namespace/runtime/config code is unchanged; only missing-argument failure order differs. Reuse prior positive witness after exact diff confirmation. |
| Persistent-volume namespace/locking/old-file protection | Lifecycle/namespace/lease code unchanged; preserve prior evidence; new missing-Index negative has additional byte/mtime witness. |

These are retained historical accepted witnesses, not newly executed results on this Pair. Storage sizing still requires authentic DCP metadata; B1 rank capture files are not DCP-size authority. No storage forecast or production change is added here.

## Stop and independent verification

DS request: `docs/collab/chatgpt/requests/2026-10-16_DS_PRO_V3_F0_REG01_TEST02_CPU_reverification_9e51c94a.md`. DS must verify exact new clean detached Pair, unchanged original regression, full-V2 nine cases/all F0 tests, V3 minimal suite and static/source boundaries. GPT Fresh Incremental Review follows those results. **F0-REG-01/F0-TEST-02 are implemented but not independently closed.**

F1 is not started. No GPU/Fresh/Resume/Formal30k, DCP/RNG, Local-TTT or frozen B1 change is authorized by this handoff.
