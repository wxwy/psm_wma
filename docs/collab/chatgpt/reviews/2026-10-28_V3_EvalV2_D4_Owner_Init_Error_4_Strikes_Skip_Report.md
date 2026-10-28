# Owner clarification — Eval V2 D4: >3 consecutive initialization errors → SKIP, REPORT, OWNER RESUME DECISION

Date: 2026-10-28. **New Owner direct instruction**:

> “异常 → 记录初始化错误，也重新 reset()，要是一个episode初始化错误次数连续超过3次，就跳过这个episode；记录，报告，让我决策是否resume。”

This is a **Design Contract update**, not a production code review, real-runtime verification or authorization.

## Exact decision / binding

- Earlier r1 formal design/prototype Root `dc750f8e258d10a33e7a195cf907926b1c98bd7f` and Child `746c5cf2f2324104a62fb71510343aa40d3976c5` remain unchanged; r1 Design Gate stays `REQUEST_CHANGES`.
- Previously logged D4: `docs/collab/chatgpt/reviews/2026-10-28_V3_EvalV2_NavigateKitchen_Reset_Already_Success_Evidence_Design_Addendum.md`. This file **supersedes the D4 initial-precheck EXCEPTION branch only**. D1/D2/D3 and no-scene-reproduction Owner decision remain applicable.
- All decisions target **new fresh900 Evaluation V2**, not the prior431 Episodes. No original-run repair or replay is requested.

## Frozen per-logical-Episode behavior

1. On a candidate scene, perform `env.reset()`, then strict pre-action `env._check_success()` check (or equivalent native initialization/readiness checks). This stage ends **before any model inference, policy action or Local-TTT Episode mutation**.
2. If reset and precheck succeed with `initial_success == False`, **accept** this scene and execute exactly one normal Episode. Its policy outcome uses native environment success after executed steps, and an official-horizon no-success result is a **valid behavioral failure**, not a reason to resample.
3. If reset/precheck succeed with `initial_success == True`, this is `DEGENERATE_INITIAL_SUCCESS`: reject this candidate scene, log the rejection and draw a new scene. **Not** an initialization exception; counts separately against the existing D4 bounded scene-admission limit, never as a policy success/failure.
4. If initialization or initial-success precheck **raises or returns invalid result**, increment a per-logical-Episode **consecutive initialization error** counter and persist each error; perform a safe new reset/reinitialization where supported. On **first, second, third consecutive errors**, retry. On the **fourth consecutive error**, because `4 > 3`, **stop that logical Episode** and set `SKIPPED_INIT_ERROR`; never spin indefinitely.
5. A successful initialization/precheck (whether `initial_success==False` or `True`) breaks the **consecutive error streak**. The already documented separately bounded D4 scene-admission total remains applicable so alternating successes/degenerate scenes/errors cannot loop indefinitely. If the previous total bound is exhausted, produce a separate explicit `SCENE_ADMISSION_EXHAUSTED` diagnostic.
6. An Episode skipped for init errors is **not** Success, Behavioral Failure, or a completed Core Episode; it is an unresolved logical slot, not part of SR numerator/denominator and never silently replaced with another slot. If `ep_037` is skipped, the evaluator can continue with `ep_038..049` after safe environment recovery, preserving already-valid `ep_000..036` results.
7. **No automatic Resume of skipped slots**. Surface the exact skipped Episode IDs, reason and evidence in the final summary for **Owner decision** whether to resume/retry those slots; if authorized later, re-sample new scenes (no old Scene/RNG replay required). Existing valid successes and behavioral failures must never be retried.
8. Do not treat an unrecoverable native process crash/uncleared Session/hardware state as a recoverable reset exception. Safety requires proper worker/process teardown or explicit stop; this per-Episode skip policy cannot suppress unsafe infrastructure failures.

## Evidence and reporting

For every rejected or failed initialization candidate, persist under the relevant logical Task/Episode and an immutable, bounded attempt ID: index and attempt ordinal, exception type/message/phase, time, actual seed/stream ID and reset ordinal when known, `initial_success`/degenerate flag if available, diagnostic environment provenance, whether teardown/restart was safe. No media is required for the record or SR.

Publish in `summary.json` / per-Task summary / `episodes.jsonl`: `skipped_init_error_count`, `initialization_error_attempt_count`, `degenerate_initial_success_count`, `scene_admission_exhausted_count`, IDs of skipped slots, attempted/accepted sampling streams, final per-Episode `status` and reference to persisted attempts. **Overall formal SR stays null until all900 logical Episodes have one valid Core Success/Behavioral Failure; partial valid-only SR may be displayed but must be labeled.** Do not mark `COMPLETE` while skipped slots remain.

## Required r2 Design / CPU acceptance tests

- `ep_037` has 1, 2, 3 consecutive initialization errors, then successful initialization → a single valid Core Episode result, with three logged errors, no unnecessary skip.
- `ep_037` has **four consecutive errors** → exact `SKIPPED_INIT_ERROR` (0 policy actions, 0 model inference, 0 Local-TTT mutation), and user-visible skipped-slot report; `ep_038` can proceed if environment safe, `ep_000..036` bytes unchanged; no automatic ep37 rerun.
- Error streak resets after a successful precheck even for degenerate initial success; degenerate rejection count separate, total scene attempts bounded; predicate exception never coerced to `False`.
- Crash before/after persisting attempts, process death during reset, invalid precheck type and safe worker replacement → do not produce duplicate logical Episode or corrupt the skip ledger.
- `ep_037` is still skipped at final → formal `sr=null`, `partial_sr_valid_only` conditional, no `COMPLETE`. After **separately authorized Owner Resume**, exactly that missing slot can be filled without re-running any valid prior/later result.
- Prevent skipping as a reward-selection technique: ordinary `behavioral_failure` never triggers init retry, missing/undecodable video never changes initial error count or core result.

**Production implication**: r1 prototype `Store.rows()` assumes a contiguous prefix and cannot presently admit `ep_038` while `ep_037` remains unresolved. The new r2 design must explicitly introduce separately tracked skipped-slot / attempt state and allow non-contiguous valid result indices **without** fabricating Episode37 completion or reusing completed Episode IDs. This is a new D4 acceptance, not an implementation already present.

No merge V3, training, GPU/simulator restart, old431 modifications, or production launch authorized.
