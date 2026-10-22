# RoboCasa Batch C manual evaluation — author handoff

Date: 2026-10-22. Status: **REVIEW / AUTHOR_CPU_PASS_PENDING_GPT_AND_DS**.

## Exact implementation

| Identity | Full SHA |
| --- | --- |
| Root implementation on V3 | `a2f3a6a367395b2f2a6006cfc4e7c9effa606713` |
| Child / Root Gitlink | `c9f21040f462a114d597fc83773cb9b6a9e96214` |
| Development baseline Root | `24a726734bbab5411160e3c11a8b46135fceb570` |
| Integrated baseline Child | `30db22a3586c0270611753dc2ca0deb10ec27833` |
| Existing integrated G1/A/B implementation | `9ae01344ffe82a3b403732aa61cce3dd7fb5055a` |
| Unchanged reconstructed robosuite vendor | `1ac174585293ed998ffc9cf73e47439798cf6f6c` |

Root and Child source refs: `v3-robocasa-manual-c-20261022`. Root implementation was fast-forwarded to V3 without force. Later evidence/Inbox commits are bookkeeping; they do not replace the formal implementation SHA above. G1/A/B implementation is inherited from current V3, not from an older isolated candidate. G1 training source, its frozen configuration/identity/DCP and running isolated worktree were not changed or accessed.

## Delivered behavior

- `scripts/run_robocasa_eval.sh` invokes the lightweight queue. Strict `psm_wma_robocasa_eval_v1` YAML, CLI > YAML > defaults, unknown/duplicate keys and invalid types rejected; executable Python paths preserve venv symlinks. One GPU maps to one serial task worker and Local-TTT slot0. Explicit GPU/task/episode/checkpoint/media/timeouts/output/resume parameters are supported. `tasks=all` means exactly18 underlying metadata task classes; subset selection and duplicate-source rejection use `env_args.env_name`, not paraphrases.
- `--list-tasks` performs metadata-only discovery. `--dry-run` reads actual checkpoint/config/source/vendor identity and selected simulator imports using CPU, displays complete per-worker command/environment templates, and creates no output namespace, server port, model or Kitchen. It is not GPU resource reservation. Runtime probe failures retain diagnostic stdout/stderr; missing installed runtime correctly rejects startup.
- Existing Batch B `build_verified_evaluation_identity()` is wired into the real queue, using the same PYTHONPATH as the actual simulator. Raw probe logs are separate from immutable manifest identity. Child reruns the pinned helper before vendor/env construction, requires the same digest and full selected-task set, persists its attestation, and uses verified official horizons without a fallback or repeated1.5× multiplier. Runtime and recorded dataset-generator versions/unknown commits remain distinct; no physics equivalence claim.
- Environment MP4 and initial PNG can be disabled. Generated video `none` does not decode or save it; `first` saves the first prediction separately for **each episode**; `all` saves each replan with source-step and frame-count manifest. Enabled MP4/PNG must actually decode, not merely exist. Raw15, canonical raw15, submitted env12 action and prediction JSONL remain mandatory. No policy/Local-TTT algorithm or action decoder change.
- Exclusive run identity/namespace lease, invocation-specific resolved parameters/runtime logs and historical summary snapshots preserve provenance. Each task uses exclusive `attempt_0001`, etc. Only a complete matching task with typed results, matching Episode records/audits, actual valid media, in-process runtime and successful owned-group cleanup witness is skipped. Failed/partial tasks retain evidence and restart from episode0 in a new attempt. `Task/Attempt` identity prevents cross-task and cross-attempt mixing. Corrupt COMPLETE/legacy output rejects; no episode stitching or evidence overwrite.
- Batch A fresh-server/task isolation, owned PID/PGID termination/reaping, full worker error propagation and formal/partial SR separation are preserved. Final media validation observes task wall deadline and cancellation; decoder uses the same owned-process cleanup to reap FFmpeg descendants. Actual Numba/MPL/XDG caches are external temporary directories, avoiding dirty pinned source on later tasks. Explicit HF_HOME is preserved, otherwise its cache is external too.

Owner operations are documented in `docs/eval/robocasa_manual_runbook.md`; the example YAML is `configs/eval/robocasa_g1_iter8900.example.yaml`. The runbook commands remain subject to the combined gate and separate Owner execution authorization.

## Diff and author CPU evidence

Evidence directory: `docs/collab/codex/evidence/2026-10-22_RoboCasa_Batch_C_manual_eval_author_cpu/`.

Root source diff: **13 paths**, including Gitlink, SESSION/TODO, new helpers/launcher/YAML/runbook and CPU tests. Child diff: **3 paths** (`closed_loop_eval.py`, new `closed_loop_eval_manual_test.py`, optional attempt binding in `rollout_evidence.py`). Exact unified diffs are `implementation-root.patch` / `implementation-child.patch`; final source SHA256 are in `source_checks.json`. B patchset/runtime-helper/lock and all training, optimizer, RNG, DCP, Local-TTT math remain unchanged.

| Final author suite | Result | Evidence |
| --- | --- | --- |
| Config70 + task/media57 + owned-process18 + actual Numba cache3 | **148 passed**,0fail/error/skip | `helpers.log`, `helpers.xml` |
| Child manual media/runtime + lifecycle/contract/Phase6/client/decoder | **58 passed**,0fail/error/skip | `child.log`, `child.xml` |
| Actual queue with synthetic policy/simulation boundaries | **29 passed +65 subtests passed**,0fail/error/skip | `queue.log`, `queue.xml` |
| Existing identity/episode/partial-video/screening regressions | **20 passed**,50deselected | `regressions.log`, `regressions.xml` |
| Ruff0.12.7 check + format; Python AST10 + bash syntax; source diff | PASS | `ruff_*.log`, `source_checks.json` |

Counts are **255 top-level cases +65 passed subtests**, not a full-repository test claim. Queue JUnit declares94 tests (29 testcase elements plus65 passed subtest events); all four final XMLs declare320 combined. The20-case regression selection intentionally excludes50 unrelated training/cache cases, not skips. Queue includes39 subprocess scenarios and actual tiny MP4/PNG encoding/decoding. It retains existing wrong checkpoint/config/chunk, stale/foreign listener, process exit, worker initialization, cancellation, timeout, reset/media failure and ignored-TERM child cleanup assertions. New cases cover dry/list without output/Popen, subset and full runtime task identity, dirty runtime, complete skip, retained partial/new task rerun, video/timeouts identity rejection. Real Numba JIT produces .nbi/.nbc only in the external cache while the tiny tracked Git source remains clean. Nested decoder cancellation verifies leader+grandchild reaped.

The internal author-team source review found and closed manifest-schema mismatch, cleanup-before-COMPLETE ordering, cache pollution and decoder descendant reaping concerns. `internal_source_review.md` is supporting author evidence, **not** GPT/DS independent acceptance.

Intermediate environment/author failures are explicitly retained in `intermediate_*.log`: missing NumBa interpreter selector, incomplete scripts/Child PYTHONPATH and the decoder deadline exception assertion corrected to its explicit TimeoutError contract. Earlier evolving-interface Queue runs remain external `/tmp` development logs and are not counted as final evidence. Final logs use final committed source hashes.

## Reproduction / DS_PRO CPU-only boundary

Use a clean detached worktree at exact Root/Child above. Do not sync a running G1 worktree. Use existing CPU-capable Python dependencies; GPU visibility stays empty. `PSM_NUMBA_PYTHON` can select an existing compatible CPU interpreter containing NumBa; it defaults to the pytest interpreter and missing NumBa fails rather than skips. The author used Python3.12.14, Ruff0.12.7, Torch2.10.0+cpu and a separate pinned NumBa0.61.2 interpreter.

Exact command/environment records are in `commands.json`. Core Root command:

```bash
CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 \
PSM_NUMBA_PYTHON=<NUMBA_CPU_PYTHON> PYTHONPYCACHEPREFIX=<EXTERNAL_CACHE> \
<CPU_PYTHON> -m pytest --noconftest -c /dev/null -p no:cacheprovider -q \
  tools/v3/robocasa_eval_results_test.py tools/v3/robocasa_eval_config_test.py \
  tools/v3/robocasa_processes_test.py tools/v3/robocasa_eval_cache_test.py \
  --junitxml=<NEW_EXTERNAL_EVIDENCE>/helpers.xml
```

Run queue separately with the same CPU environment and `-s tools/v3/eval_robocasa_queue_identity_test.py`, preserving raw witness stdout/JUnit. Child6 files and the filtered20 regressions are listed in `commands.json`. Ruff uses `--config cosmos-framework/.ruff.toml`; run `check` and `format --check` on the10 exact changed Python files and `bash -n scripts/run_robocasa_eval.sh`. No source/test skip/xfail or assertion relaxation is needed. Tests require no real checkpoint/data or installed full Cosmos/RoboCasa model stack; their deliberate simulation/import doubles must be labeled as such.

## Requested review and stop

Request GPT fresh incremental review of **a2f3a6a367395b2f2a6006cfc4e7c9effa606713 / c9f21040f462a114d597fc83773cb9b6a9e96214**, with unchanged Vendor1ac174. Then DS_PRO independently validates the approved scope, using new external evidence and no production edits. This does not inherit an official combined CPU PASS from older G1/A/B pairs or close real physical/runtime gates.

No GPU, real Action Server/Cosmos policy, Kitchen creation/reset/step, real DCP save/load, G1 worktree access or training/benchmark launch occurred. Actual DS-host dependency installation/imports, PandaOmron physics/base axes/camera/state, real policy loading/Local-TTT and real SR remain unverified by this author CPU delivery. Owner alone authorizes and manually executes canary→4×5→18×5 after combined acceptance. Codex stops after remote readback and this review request.
