# Evaluation V2 Stage2 — implementation review request

2026-10-28. Author CPU complete; request **GPT Code Gate**, not training or simulation authorization.

| Object | Exact identity |
| --- | --- |
| Formal Implementation Root | `4769d711777c20a72dd7a3f6071a96f08ad8abb0` |
| Formal Child / Gitlink | `2d4a42590fead00ea16f6ae5902e2bc8382b07e2` |
| Isolated Root and Child branch | `v3-eval-v2-stage2-20261028` |
| Root direct parent | `1404c34e6cb46df68368d877c296bf95a5bcc9f4` |
| Child parent | `746c5cf2f2324104a62fb71510343aa40d3976c5` |
| Approved Design Root / prior Child | `1fd3ad42075032bd0137ac9a76306169aaa45032` / `746c5cf2f2324104a62fb71510343aa40d3976c5` |
| GPT design verdict | `APPROVE_DESIGN` in `docs/collab/chatgpt/reviews/2026-10-28_V3_RoboCasa_EvalV2_r2_D1_D5_1fd3ad42_746c5cf2_design_review.md` |
| Canonical V3 docs lock consumed | `4c9990f5bfab4544fe9edc69ba7227a07ef1ed8e` (Child746 unchanged) |

Owner explicitly authorized Stage2 production wiring+CPU on independent candidates after that design approval. Canonical V3 approval and concurrent unrelated NoTTT Owner records were merged **into the candidate**, append-only Inbox tails preserved. Neither candidate is merged back into V3 or `v3-local-ttt`. Later author Evidence/Inbox documentation commits do not replace this Formal Root.

## Actual implementation, not another prototype

- **D5:** production `RoundScheduler` runs the real root runtime with frozen Episode-major dispatch, same-round worker parallelism and strict barriers. Both dry-run and runtime eligibility use the same slot disposition. Resume skips verified success and normal failure; a sole Owner-released hole still executes even when all later slots are valid.
- **Native:** actual default Worker path verifies runtime/module source/metadata/library identity, constructs pinned `native.make_env` and retains one Task environment object. The adapter calls the original `run_policy`, HTTP payload and Local client; raw15→env12, state15,16 actions per replan and completed evidence sequence are reused. No Cosmos/model/Local algorithm reimplementation. Native hooks are optional;58 legacy CPU regressions verify their defaults.
- **D4:** strict initial predicate precedes any prediction/Local begin. Degenerate success resamples. Only known safe sampling/type failures with positive physics probes retry; fourth consecutive recoverable error becomes explicit Owner-pending skip.32 total admissions remain bounded. Action-loop predicate/runtime errors cannot become policy failure.
- **D2:** actual actions/predictions/Local cleanup/scene metadata are staged once, validated, sealed and fsynced; an atomic whole-directory rename publishes the valid Core into the empty public Episode slot. Core identity and private chronology are checked on reuse; corrupt/truncated/oversized/FIFO evidence rejects. No completed Core is overwritten.
- **D1/D3:** actual process registry binds PID/start/PGID/session, inherited socket nonce and exact attempts; finite cancellation, parent-death and owned group cleanup. Resume closes old groups before fresh stream health and scoped fault resolution; a valid same-slot replacement resolves pre-Core errors. Post-Core faults require health-only recovery and never rerun Core. Ordinary Resume does not release skipped initialization slots; an external targeted Owner decision uses a separate `authorize` command.
- **Media:** optional bounded CPU encoder with bounded queue/frame/video payload, independent error records, no strict MP4 decoding in SR path or duplicate video copies. Native Local end+reset precede encoder waiting. Forced/uncertain process cleanup is a clean-execution fault after preserving Core, not a policy failure or a reason to repeat that valid Episode.
- **Operational:** cold model hash plus approved trusted-input fingerprint cache, exact model/config/vendor/Task identity, explicit Action Server chunk16 and owned listener validation, private import caches, loopback HTTP without inherited proxies, resource guards and live terminal progress. Fresh preflight caches cannot create/adopt the Run before exclusive namespace creation. Shared Episode wall deadline covers initialization and execution. No legacy catalog/history scan.

Root direct-parent diff:27 files (+4570/−1), including new files, Gitlink and bookkeeping. Child diff:13 files (+2380/−10), only new evaluation modules/native adapter+worker and two narrow optional-hook files. Existing root Queue, training, DCP, vendor and frozen legacy/prototype files are unchanged. Review the actual source/patches; the counts are not a verdict.

## Evidence and CPU limits

`docs/collab/codex/evidence/2026-10-28_eval_v2_stage2_author_cpu/` has raw final JUnit/logs/command/environment, static output,49 Git Blob bindings, exact Root/Child patches, retained draft failures, synthetic artifacts and a portable CPU replay command. Final **200 passed (142 production-path +58 legacy),0 fail/error/skip;86.73s pytest**.34 changed Python files pass Ruff0.12.7 check/format/AST; wrapper shell syntax/help pass. Test/static source hashes agree before/after and with the Formal Pair; the actual committed source guard passed clean.

Production900 synthetic test: exact900 dispatches/50 barriers,450 success/450 normal failure,41.070s; p95 claim~28.31ms, Core commit~4.01ms, summary max~2.93s,8223 JSON disk reads/86814 immutable-cache hits. Mock3 models/18 environments only. Real CPU HTTP exercises17 native completed actions/two replans/Local acknowledgements/reset. Small actual FFmpeg **encoding**, stall/process/cancellation/parent-loss tests use no real model or simulator. No DCP tensors are loaded/saved. Author evidence is not DS independent acceptance.

## Remaining Gates and review request

Resource policy proposes3 resident model servers and18 Task actors/6 per GPU, bounded by declared caps, owned RSS and NVML thresholds. This is **not** proof of actual EGL/VRAM capacity or constant EGL lifetimes: native reset can reconstruct MuJoCo models/contexts. Source/runtime identity is not proof of0.5.1 data-generation physics equivalence. CPU package versions are not native vendor certification. Real Local-TTT/model correctness, CUDA physical IDs,18-actor resource growth, media backpressure and interruption→Resume must be measured in a separately authorized tiny Canary with its own namespace.

Request GPT fresh incremental **Code Gate** on this new pair, covering D1–D5 actual production wiring, atomic Core trust, predicate/media/Local boundaries, input identity and process lifetime. Do not reopen the approved design simply because documentation HEAD changes; assess implementation changes. Then DS performs independent focused CPU replay in a clean exact-pair worktree. No automatic merge, real Action Server, GPU, RoboCasa,900 benchmark, old431 migration/cleanup or training operation follows this author submission. Codex stops after candidate publication and exact remote readback.
