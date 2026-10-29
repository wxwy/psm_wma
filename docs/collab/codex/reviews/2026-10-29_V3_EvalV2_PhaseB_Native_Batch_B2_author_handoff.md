# Phase B second increment — native Batch / multi-Sim author handoff

2026-10-29. **Request incremental APPROVE_CODE / REQUEST_CHANGES. Author evidence, not a reviewer verdict.**

| Identity | Exact value |
| --- | --- |
| **Formal Implementation Root** | `323f0b2a3d4aa3b40d9d8f2eb0b94c9251299728` |
| **Formal Child / Root Gitlink** | `774c2edb93ec5a6ba85ba1124757064d7cc779a5` |
| Isolated Root/Child branch | `v3-eval-v2-batch-b2-20261029` |
| Approved first increment | Root `dc7757922d7273f50f3de23363d41e12e157a07f` / Child `4a938e41b0c335baca1c1d8f1caabc433b0e2001` |
| Exact first-increment verdict | `66a5b99c0a23312525ccbdc0fadb4655bc7d0b19`, B1-F1 CLOSED / B1-P1 WITHDRAWN |
| Approved full design | Root `b9c7cf1607ffd38f6e3349bdde0b35703a6d7684` / Child `d2c1bda62880dbeee196f70945e5bc430b73f4b6` |

Review the **second-increment delta** Rootdc775792→323f0b2a / Child4a938e41→774c2edb and its affected interfaces. Do not re-open unchanged Phase A/design/first-increment findings. Subsequent Evidence, peer-doc merges and publication receipt HEAD are bookkeeping and do not replace this Pair. Existing approved candidates and canonical V3/v3-local remain separate.

## Delivered production path

- Explicit `phase_b` evaluation profile; configurable G/M/B, useful `(Slot Index, GPU)` placement, one Server/model per used GPU and independent persistent Sim processes. Environment persists across same-Task Episodes and closes/rebuilds on Task switch. Existing default Phase A M1/B1 and legacy server endpoints remain guarded. No18-resident-environment assumption or claim that task-switch construction disappeared.
- Existing Episode-major scheduler, round barrier, Core store/admission/D1–D5 reused unchanged. Root registers after D4 admission only; Sim binds the coordinator assignment for exact run/manifest/physicalSlot/generation/Task/Episode/Attempt and uses its independent Fast State. Actual native action/evidence loop and raw15→canonical15→env12 conversion are reused. End ACK precedes Slot reuse; failed prediction cannot be retried externally as a new budget or delivered twice at the same frontier.
- Bounded queue of real owned tickets; full and partial batches, including B>M. **One call to actual production `model.generate_samples_from_batch` contains B observations, state/action carriers, prompts, domains, SequencePlans and prefixes**, not B calls to serial policy generation. Response includes immutable batch ID/size/index and exact assignment/key/frontier; client validates before delivery. CPU helper tests cover mixed hot/None/hot masks and sample offsets.
- Existing Local prepare/scan equation runs separately per Session. `commit_many()` validates/preallocates all members, then publishes one Fast/Visual/Response snapshot. Sealed batch faults roll back every uncommitted member; pre-seal cancellation isolates that queued request. Original deadlines survive upload/wait/retry/generation/drain;429/503 backoff is bounded by the same budget. Failed drain remains quarantine with no false End ACK. W0 and model/attention/diffusion/training/checkpoint/optimizer/Vendor source are unchanged.
- Bounded optional generated-video CPU spool and same model executor decode only when inference is idle; action publication/delivery does not wait for video. Sim background fetch validates mapping, fences delivery at End, ACKs media and records per-replan diagnostics. Spool/mapping/decode/write/drop errors do not change SR; unknown device/process cleanup is an infrastructure fault. One original environment/generated MP4 location, no videos_view copy or automatic strict FFmpeg decode.
- Same-run manifest freezes new execution profile/G/GPU IDs/M/B/wait/noise convention; both preparation and runtime reject profile drift. No historical migration or cross-source Resume override. Progress includes physical Slot and bounded batch telemetry; no added full Checkpoint hashing per batch.

Full wire/lifecycle/resource/manual-entry description: `docs/build/PSM-WMA_V3_EvalV2_PhaseB_Native_Batch_B2_Implementation_2026-10-29.md`. Sample: `configs/eval/robocasa_eval_v2_phase_b.example.yaml`; it is Canary-sized, with required EVAL_* paths, and confers no execution permission. Use a clean worktree at the frozen approved implementation Pair for any later authorized native execution, rather than substituting a docs-only HEAD for its identity.

## Final exact-pair author CPU

Evidence: `docs/collab/codex/evidence/2026-10-29_eval_v2_phase_b_native_batch_b2_author_cpu/`.

**424 passed,0 failure/error/skip =145 inference/transaction +255 Phase A +24 new runtime/profile/entry tests.** Ruff0.12.7 check/format, AST29, import origin, exact Root/Child/Gitlink, clean source and before/after fingerprints PASS. All99 previous inference test identities and all255 Phase A identities remain; old assertions/test sources unchanged. New B1 batch-profile reference also uses rtol0/atol0 for actions and real CPU Fast State.

Real CPU Local encoder/scan/state/publication, actual native input/action/prefix helpers and actual Client→Dispatcher→Actor/Runtime/Worker/Core path are exercised. Diffusion, WAN encoding/model weights, physical environment and kernel file evidence are explicit doubles. No native GPU, Cosmos weight load, RoboCasa/MuJoCo/EGL, real DCP or actual900 SR run. Original900-slot regression is synthetic scheduling only.

Selected final OS witnesses, with actual owned subprocesses, HTTP and PID/group cleanup receipts:

| CPU fixture | Model owners | Sim processes | Result / native invocation sizes |
| --- | --- | --- | --- |
| G1,N2,M2,B2,2Episodes/Task | 1 | 2 | execution intervals overlap;4 Core; batches B1×2,B2×3; completed Resume does no model/Sim/resource work |
| G2,N3,M2,B2,1Episode/Task | 2 | 3 | overlap;3 Core; B1×4,B2×1; correct per-GPU ownership |
| G1,N3,M2,B2,1Episode/Task | 1 | 2 | overlap;3 Core; B1×2,B2×2; Task switch and partial batch |
| Owned Server exits inside B2 Generation | 1 | 2 | scoped infrastructure errors, nonqualified report, all owned groups gone, unrelated process survives |

The negative Server receipt explicitly has **returncode23**, whose fixture source exits only inside an actual size>1 native invocation; this is checked in `os_qualification_verified.json`. No test-created private capability values were copied. Whitelisted raw process/close/timeline/log/Core summary artifacts are published under `os_witnesses/`; their manifests/results are explicitly synthetic, not benchmark evidence. Caches, capability files, fake checkpoint containers and unselected temp trees remain external.

The first clean intermediate Pair cd538b0d/774c2edb actually passed421 tests. A publication self-check then found the thin CPU wrapper ignored `main()`'s nonzero status: its wrong-pair JSON was BLOCKED while its shell code was0. This was a Root-tool defect, fixed with `SystemExit(main(...))` and3 new entry tests; final424 is bound to **323f0b2a/774c2edb**, with shell exit propagation checked. Prior421/RED/intermediate fixture text-mode/info-method/rotation failures are kept separately, never folded into final PASS. Production Child was unchanged by this correction.

Actual cloud clock probe remains **BLOCKED_KERNEL_IDENTITY_UNAVAILABLE** (timens/time namespace entries absent); no guard bypass. Tests feed bounded kernel bytes to the actual parser. Normal-exec active/children/domain checks in the actual target environments remain a native deployment prerequisite. No namespace subsystem or new design Gate was added.

## Reproduce and next boundary

```bash
python tools/v3/run_eval_v2_batch_b2_cpu_gate.py \
  --root-worktree '<EXACT_CLEAN_ROOT_WORKTREE>' \
  --expected-root 323f0b2a3d4aa3b40d9d8f2eb0b94c9251299728 \
  --expected-child 774c2edb93ec5a6ba85ba1124757064d7cc779a5 \
  --evidence-dir '<NEW_EXTERNAL_EVIDENCE_DIR>'
```

This is the unified final-candidate replay for later separately instructed DS execution. The command must return0 **and** gate.json PASS with zero failure/error/skip, correct identities and unchanged source. Preserve external temp process/cleanup receipts and synthetic OS witnesses along with JUnit/logs. Author execution is not independent DS CPU acceptance.

Source evidence includes incremental Child/full Root technical Diff, complete changed-file inventories, **61 frozen GitBlob/source bindings**, hashes of published artifacts and byte/AST identity checks on protected model, D1–D5 authority and closed original-deadline functions. Latest canonical peer docs through `9cc37557a538d5c9df29923aa069c5c17400f119` were preserved without acting on their unrelated Compact/GPU instructions; canonical V3 was not updated by Codex. Inbox archive and both live tails remain intact.

Request fresh GPT **APPROVE_CODE / REQUEST_CHANGES for second increment only**. After Child→Root candidate publication/readback, Codex STOP. Next is GPT review → one independent DS full-candidate CPU replay → separately Owner-authorized small1GPU/M2/B2 native Canary → separately authorized formal18×50. No canonical merge, DS job, GPU, real simulation/900, training/G1/old431/Checkpoint/RNG/Optimizer/Vendor/history operation occurs automatically.
