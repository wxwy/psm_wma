# Matched No-TTT — author implementation handoff / fresh review request

2026-10-25 (Asia/Shanghai). Status: **REVIEW**, author CPU only. No GPU/training/real-model/server/simulator authorization inferred.

## Exact implementation pair

- **Root V3: `7c083215e9f39ed4b5b3ff64010e415ad62dfdf4`**.
- **Child/Gitlink: `20b5fa639c405a515933da109529e3e2c04de88d`**.
- Root parent: `48d1eb7f21f26be459bf78259d9678a8118e27c1`; Child parent: `813a550dab5d6b5b5e3be90d38bb97527956b4dc`.
- Source commits non-force published/read back on V3 / v3-local-ttt and both isolated `v3-matched-no-ttt-20261025` branches. Following evidence/documentation HEAD is not an implementation replacement.
- Earlier Flexible Resume fixture review/DS approvals remain scoped to their original pair; they are not this new training profile's approval.

## Implementation

The new training command form is `bash scripts/train_v3_matched_no_ttt.sh fresh 30000`, **only after separate review/DS/S0/GPU authorization** and the runbook's real asset/env setup. The launcher always supplies `--no-ttt`, world8, T16/B8/GA2, synchronous workers0, schedule30000/500/100. The default G1 launcher and active G1 assets/worktree are unchanged.

The corrected Phase5 read-only lifecycle gains a narrow opt-in profile. It shares the accepted catalog/planner/producer/transform/collator and model/outer-loss path, disables Local before model construction, selects only the identical seven Generation groups and uses independent MatchedNoTTTTrainer. The model may not contain Local runtime/projection/embed parameters. The native call omits the private prefix argument entirely; no Local scan/inner-loop/fast-state/Local transaction is instantiated. Inert T/K config fields are not a claim that TTT executes.

One native forward/backward per GA member; real valid counts weight the same native scalar by `n_member / n_window`, retaining G1 rank-local normalization, original native auxiliary weights and terminal partials. CPU controls compare exact Consumer order and weighted Generation gradient with the **actual current G1 Local Window** reference; this does not require G1 and No-TTT model predictions to agree.

A new per-rank frontier callback persists only committed data progress, rank/world/seed/B/T/GA and source/config identities. Its strict format is incompatible with G1's Local sidecar; failed/pending windows reject save, skips/nonfinite gradients reject frontier publication. F0 namespace lease and immutable canonical config, F1 atomic all-rank completion and strict RNG restore remain in the shared existing checkpointer. No changes to those mechanisms were made. CPU roundtrip is a toy optimizer/frontier test, not real DCP/CUDA validation.

Default G1 source compatibility is preserved: absent `--no-ttt` retains the original Local overlay/trainer/digest/producer metadata; the existing main-factory regression and all existing F0 TrainerTests pass without changing their assertions. Saved No-TTT YAML records chunk16, actual producer chain and disabled Local status. A real Edge recipe is fully serialized to YAML/pickle in CPU tests without loading official assets or model weights.

Inference uses new `configs/eval/robocasa_matched_no_ttt.example.yaml` and `scripts/serve_v3_matched_no_ttt.py`: canonical No-TTT job/config/checkpoint identity, Generation-only selector, raw15/state15/H16/Packed128/left_wrist/state ABI checks, explicit off/raw15/chunk16 flags. `--dry-run` reads only identity/config/path presence. Existing native server/client support off; existing required-TTT Queue, Local result-validation/Resume rules and vendor pins are intentionally unchanged. This does **not** claim the unified required-TTT Queue can already execute baseline off-mode or that a new No-TTT SR protocol has been accepted.

## Author evidence

`docs/collab/codex/evidence/2026-10-25_matched_no_ttt_author_cpu/`:

- Final frozen **16 groups: 434 passed, 42 successful subtests, 5 skipped, 0 failure/error**, 23.66s. JUnit top-level testcase elements439; subtests are not additional testcase elements. The five pre-existing optional real-asset/CUDA skips are explicitly enumerated in STATUS; every new No-TTT case executes without skip/xfail.
- Real tiny Cosmos network constructor has LocalMemoryRuntime replaced by an assertion that must never be invoked; action/vision projectors still exist. No GPU kernels/model forward executed in this constructor test.
- Full/terminal/count1 packing, exact G1 ordering and weighted gradient; ordered stochastic transforms; successful optimizer-only frontier commit; same-state next Consumer/loss/optimizer/scheduler; wrong schema/iteration/rank/config/source/counter/Local state; NaN/Inf/hook contamination/skipped step; no Local parameter inventory; data/namespace/DROID gate and inference identity negatives.
- Complete real-recipe No-TTT YAML/pickle/semantic serialization; existing G1/F0/native data/mask/cache/prefix/telemetry regressions. No old test was loosened/deleted. Real official model loading, real assets and FSDP/CUDA were not executed.
- Ruff0.12.7 **check + format --check9**, Python syntax9, bash syntax, frozen-source/committed-blob checks and protected-prefix diff checks PASS.
- Raw final stdout/JUnit, exact command/environment, source hash freeze, collection-to-JUnit mapping, source patches, raw earlier collection/errors/full01 failures, CPU dependency manifest, iteration notes and SHA256 artifact manifest retained. The initial artifact-mapping collection attempt had an external-runner sys.path issue; corrected collection only adds per-file attribution, does not rerun or manufacture PASS results.

## Remaining acceptance, not additional implementation authorization

1. GPT fresh incremental review of **this pair**, especially shared default G1 compatibility, actual per-consumer objective, strict No-TTT frontier and off-mode inference contract.
2. DS_PRO clean detached independent CPU on exact pair using frozen command, retaining the five declared optional skips separately; do not relabel author results as DS.
3. DS real-input S0 must compare cache/corpus/source/index receipt, official DROID/VAE assets, seed/partition/Consumer trace, native action/state/vision masks and optimizer/scheduler against the chosen immutable G1 reference. Fixed shape alone does not prove matched real assets. CPU dummy paths do not establish this fact.
4. Owner separately authorizes world8 config/model/gradient canary and formal Fresh100 + Save→Resume100→101→500. The runbook includes the commands but this delivery does not run them or assert a GPU-ready 30k baseline.
5. Matched evaluation must align environment/vendor/task/seed/horizon/guidance/max-steps and use off at server/client; no mixed Local-vs-No-TTT Resume catalogs. Existing G1/iter12000/checkpoints/config/job identity and old results remain immutable.

Runbook: `docs/build/PSM-WMA_V3_Matched_No_TTT_training_runbook_v1.0_2026-10-25.md`.

**Stop after publication/readback for GPT/DS.** No current training/evaluation worktree update, model/Action Server startup, GPU, real checkpoint access or simulator execution occurred.
