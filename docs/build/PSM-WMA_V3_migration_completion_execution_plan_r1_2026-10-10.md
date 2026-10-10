# V3 Migration Completion — staged execution plan r1

Date: 2026-10-10. Owner authorized execution of the migration-completion plan in the current conversation.

## Authority and current scope

This is a forward-port completion, not a merge of V2 into the newer host. V2/v2 and the original accepted Formal30k source remain immutable. Original training Child: `71e03c8501c94a2ad5fed60955af657d3f945b85`; previous unverified optimization candidate: `98cb4fd0cc59e71f27543d67fa33cbf4f3703657`. The user manually stopped the job around iter800. The latest complete host DCP has NOT been independently inspected in this execution.

Implementation Child for MC-01: `95c82d12d6780fedf8becda18cbd36d550adaadf` on `v3-local-ttt`. Root target remains `V3`. Frozen configuration digest remains the expected value `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`; no real preflight was run here, so it is not a newly measured digest.

MM SESSION/TODO and all old evidence are retained unchanged. This plan records staged task ownership without overwriting MM's ledger.

## Execution sequence

| ID | Status | Owner | Dependency | Acceptance |
|---|---|---|---|---|
| MC-01 Monitoring / bounded async hardening | REVIEW | GPT code; DS independent execution | Current optimization candidate | New deterministic queue tests, durable logging, replay-aware summaries, nonempty/rank-complete file checks; complete project CPU/Ruff Gate on the exact pair |
| MC-02 Actual asset and same-job Resume Gate | BLOCKED on MC-01 | DS execution; GPT adjudication | Full MC-01 PASS plus actual complete checkpoint inventory | Real source/window/action/state/latent/token and next-plan parity; actual frozen digest; model/optimizer/scheduler/RNG/Local sidecar recovered at one boundary; workers0 reference and workers2 candidate require evidence |
| MC-03 Corrected Full Policy / simulator | BLOCKED on MC-02 | GPT integration; DS GPU/sim | Authorized trained checkpoint, exact source pair | Required-mode two replans; completed-only evidence; reset/replay; 48/128-step scopes; Local on/off matched-input intervention; no historical B1/iter500 inference substitution |
| MC-04 Evaluation identity / failure evidence | TODO, before bulk screening | GPT | MC-03 interface validated | Evaluation identity binds checkpoint/source/config/task protocol/seed/R; reject incompatible resume; per-step predicted_raw15/canonical_raw15/submitted_env12; save partial video and episode error on runtime failure |
| MC-05 18-task screening | BLOCKED on MC-03/04 | DS | Stable corrected full policy + strict eval identity | Every intended task recorded, separate runtime errors from behavioral failures, preserve all videos, never advertise partial SR as complete |
| MC-06 Latent-only and throughput | TODO, separate implementation Gate | GPT + DS profiling | Stable resumed path and baseline timings | Remove unnecessary placeholder pixels through a metadata-only seam with exact prompt/sequence-plan/latent/loss/gradient parity; then compare workers0/2/4 and RSS/I/O |
| MC-07 Secondary donor capabilities | TODO / deferred | GPT | Main RoboCasa result stable | Task-exposure and optional state/consumer fingerprints; label obsolete LIBERO entries; restore LIBERO/history controls only under a separately scoped experiment |

MC-03..07 are NOT implemented or validated by this commit. Dataset Index construction is already resolved and is not reopened.

## MC-01 implementation

- `cosmos_framework/utils/ordered_prefetch.py`: extracted stdlib-only one-member future queue. It owns submitted futures before each submit, including partial-submit failure; reads finish out of order but consumption remains frozen-order. Exceptions propagate after drain. No model, RNG, Frontier or checkpoint owner in this helper.
- `robocasa_async_segment_prefetch.py`: retains the existing prepared-raw / ordered-main-thread-transform split and constructor ABI. Each worker now also shallow-copies the LeRobot wrapper, still sharing its preloaded immutable HF table. Existing per-worker LRU limit2 is unchanged; thread safety and LRU efficiency still need real-host evidence.
- `psm_wma_robocasa_formal_monitor.py`: journal writes before optional stdout; refuses to append to an incomplete existing JSONL rather than corrupting/truncating evidence; derives replay-aware curves after iteration rewind; rejects nonfinite JSON; DCP audit checks nonempty files and expected ranks rather than file count alone; independent one-metric PNGs and consistent summary output.
- `tools/v3/run_migration_cpu_gate.py`: exact Root/Child/Gitlink and clean-source checks, protected MM notes, CPU/offline environment, no inherited torchrun process-group context, syntax output outside source, Ruff0.12.7 and fixed focused pytest list, stop at first failure, immutable evidence directory, before/after source hashes. No Git fetching, GPU, DCP deserialization, training, resume, package install, reset or clean.

No change in this increment to the mathematical trainer, Local core, model forward, dataset authority, optimizer, scheduler, FSDP2 fix or DCP serializer. Cached Video removal and evaluator changes are deliberately excluded.

## Honest validation boundary

Local test environment: Python3.13.5 / pytest9.0.2 / torch2.10.0+cpu. Only the standalone transport, monitor, and Gate-runner contracts were executed. The original Monitor source was materialized byte-for-byte and checked against Git blob `823c3f494bf1449c11b3cd7e37c3317100a09dd4`; its retained test file was checked against blob `92883fd8981a59452d075c08d19d81195dfb7e63`.

The new safety suite first reproduced 10 failing cases and 2 passing cases against that old Monitor. After remediation, the new queue suite + original Monitor tests + added safety tests + Gate-runner tests yield 50 passed / 0 failed / 0 skipped. PNG generation used synthetic records only. These checks do not prove Local-TTT numeric parity, LeRobot concurrency safety, real DCP resume, or H100 performance.

Ruff is unavailable in the local working environment; LeRobot and pyarrow are also absent. Therefore full MC-01 is OPEN until DS runs the exact-source Gate. Never describe these 50 standalone passes as a complete project CPU Gate or as GPU/Resume approval.

## DS execution boundary

Use the existing single project directory and existing verified training Python environment. Safely fetch/fast-forward only the named V3 refs, preserve MM notes and evidence, and pin the exact execution Root/Child provided by the owner handoff. Do not automatically follow an unrelated newer branch head.

Run `python tools/v3/run_migration_cpu_gate.py --root-worktree "$PWD" --expected-root <exact execution Root> --expected-child 95c82d12d6780fedf8becda18cbd36d550adaadf --evidence-dir <new external directory>` from the Root. The formal review/owner handoff supplies the actual Root hash.

Return `gate.json`, all generated logs/XML, dependency versions, and the exact pair. On any failure or missing dependency stop; do not edit code, install packages, weaken Ruff, discard failed tests, modify DCP, or launch GPU. CPU PASS alone does not authorize resume. In particular the existing Phase5 `--stop-after-iter` is fresh-only; do not invent `--phase resume --stop-after-iter` as a bounded resume command.
