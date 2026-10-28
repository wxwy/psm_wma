# GPT independent incremental Design Gate — Evaluation V2 r2 / D1–D5

**Date:** 2026-10-28 Asia/Shanghai. **Verdict: `APPROVE_DESIGN` — Design + isolated CPU prototype scope only.** No production implementation, no DS independent CPU, no real GPU/model/RoboCasa acceptance, and no merge authorization.

## 1. Frozen formal source / lineage

| Role | Exact identifier |
| --- | --- |
| Formal r2 Design/Prototype Root | `1fd3ad42075032bd0137ac9a76306169aaa45032` |
| Child / Gitlink | `746c5cf2f2324104a62fb71510343aa40d3976c5` (unchanged) |
| Prior formal r1 Design Root | `dc750f8e258d10a33e7a195cf907926b1c98bd7f` |
| r2 Formal implementation parent | `cb5bde818542d73da03c4f1abc9ba05fc4a13ddb` |
| Author handoff/Evidence HEAD (not formal source) | `9e6968c9183beb365980afbf5db9d9097ec207c5` |
| Candidate branch | `v3-eval-v2-design-r2-20261028` |
| Frozen Owner contract source | `docs/collab/chatgpt/requests/2026-10-28_V3_RoboCasa_EvalV2_r2_CANONICAL_LATEST_OWNER_CONTRACT.md` at `b59d1faf486765271295a00ee5e20e4d239e0163` |
| Previous Gate | r1 `REQUEST_CHANGES` for D1 / D2; later Owner addenda added D3–D5 |

Direct Git compare against r2 source's **immediate parent**: only `SESSION.md`, `TODO.md`, one new 116-line r2 design doc, ten isolated prototype/test files under `tools/v3/episode_eval_v2_prototype/` (new admission/scheduler + revisions to prior contract/scene/store). **No changes to `scripts/`, `configs/`, `third_party/`, Child source, Gitlink, model weights or training.** Comparing raw r1→r2 contains intervening approved V3 audit ledger/bookkeeping from merged V3 and is *not* a valid claim that r2 itself made those production changes. Candidate is a separate unmerged branch.

Author ACK ancestry corroborated: r2 Formal Root is a descendant of previously published D5 ACK `5ae38125484be51954da46606de6a60ba3880b91`, with 3 subsequent commits. `docs/collab/codex/reviews/2026-10-28_EvalV2_r2_Codex_reading_ACK.md` explicitly names D1–D5 and superseded choices. No direct Issue#7 ACK is claimed; its API access was reported forbidden to Codex.

## 2. Evidence verification: source-bound author tests, not independent rerun

Original frozen evidence: `docs/collab/codex/evidence/2026-10-28_eval_v2_r2_D1_D5_author_cpu/` (Evidence HEAD `9e6968c9`).

- Fetched original JUnit, not only author summary: `tests=104, failures=0, errors=0, skipped=0, duration=287.051s`; 104 actual `<testcase>` entries. Module breakdown: `contract_test=32`, `scene_test=3`, `store_test=44`, `admission_test=13`, `scheduler_test=12`.
- Fetched author `committed_source_binding.json`, independently fetched all **10/10** corresponding source Git Blobs at exactly `1fd3ad42`, all matched. Ruff 0.12.7 check/format, AST syntax, `git diff --check`, 10 source SHA entries: author-frozen logs report PASS; no independent tool execution of these checks is claimed.
- Author synthetic 18×50=900 exactly and SR=450/900=0.5, 50 round barriers, 900 dispatched slots, mock 3 model loads and18 environment constructions. These are **mock CPU counters/records**, not real model load/GL sessions, scene equivalence, real RoboCasa episodes or performance proof.
- Test timing notable: `scheduler_test.test_900_exact_episode_major_dispatch_real_store_path_and_index_no_model_per_episode` ~177.891s of author CPU, and 50-skipped-long-diagnostics report test ~36.3s. This is a measurable CPU-only prototype overhead / scale signal. It does not invalidate the design contract, but Stage2 must profile read amplification, filesystem ledger complexity and coordinator lock contention with real worker count rather than assume negligible scheduling cost.
- GPT has inspected remote source/JUnit/Evidence. **GPT did not run pytest/Ruff on a local detached checkout**, access the DS_PRO server, or execute a real GPU/simulator/model; no DS independent CPU result exists for r2.

## 3. D1–D5 contract → actual behavior → evidence → disposition

| Requirement | Direct r2 source evidence | Tests (author CPU) | Design disposition |
| --- | --- | --- | --- |
| **D1** Scoped Process Errors, historical retention, explicit recovery instead of permanent poisoning | `store.py:295–326,328–354,712–864,866–996`: immutable per-stream fault, positive cleanup, later healthy stream certificate, exact failed-slot valid retry or explicit post-Core execution-only resolution; summary distinguishes scientific SR from `results_qualified` and open worker streams | `store_test.py:186–260,389–446`: old fail → same-slot retry, late fault with numeric SR, cross-Task, bad probe/cert/forged resolution, provisional until cleanup | **CLOSED at Design Gate** |
| **D2** Crash-safe Task/Slot claim and exclusive Core commit | `store.py:230–266,355–437,507–554,587–711`: intent→directory→ready and fail-closed ambiguity, immutable attempts with lease, fsynced exclusive Core result, stale token checks | `store_test.py:78–185,263–310,344–388`: injected init/claim/commit crash edges, malformed/lost authority, byte/inode preservation, no duplicate/foreign response | **CLOSED at Design Gate** |
| **D3** Episode37-only retry, no old Scene reproduction, valid success+failure immutable and sparse later slots | `contract.py:13–15`; `store.py:507–625`; actual stream/seed + reset index in valid Core; `rows()` allows gaps, previous legitimate failures are immutable | `store_test.py:78–112`; `scene_test.py:66–100`; `scheduler_test.py:168–235`: ep0–36 preserved,37 retry only if missing,38 valid skip, new stream seed no false RNG-continuity claim | **CLOSED at Design Gate** |
| **D4** Typed pre-action reset success rejection, fourth consecutive recoverable init error skipped, Owner-only retry, safe resources/limits | `admission.py:11–46`; `store.py:448–505,565–685`; `contract.py:72–90`: separate degenerate/exception counters, 32 total candidate limit, fourth error exact skip, positive safe-recovery callback, explicit persisted Owner reference | `admission_test.py:51–265`; `scheduler_test.py:209–235,283–303`:3 errors then admission, legal True breaks error streak,4 errors owner skip, later rounds continue, 50 skipped report, no automatic retry | **CLOSED at Design Gate** |
| **D5** Real Episode-major slot/Task dispatch order, same-round 3 worker concurrency, strict barrier, exact Resume skip | `scheduler.py:18–165` actually invokes Store claim→commit, persisted dispatch tickets and round barriers; manifest `task_order` not sorted; results/index report sorted by (episode index, task order) | `scheduler_test.py:53–303`: 900 exact real-Store mock dispatch,3 ThreadPool asynchronous workers, 50 round barriers, multiple crash points/valid failure skip, owner skip37 + valid38, duplicate ticket rejection | **CLOSED at Design Gate** |

**Additional frozen C requirements**: `EnvironmentOutcome.check_after_step` typed env predicate; manifest success_latch1, required Local semantics; non-success at horizon is valid `failure`, improper early terminal is Invalid. `try_media()` no ffmpeg or media-gated SR, no automatic video copy. Old431/run lineage not imported. These are CPU-only design contracts, not claims Child real path already changed.

## 4. Design decisions accepted; production risk/Gates remain

1. **32 total scene-admission samples per logical slot per Owner-authorization round** is an author-proposed **bounded design default**, not an Owner quote. It is explicit in frozen manifest, separate from Owner's hard **four consecutive initialization errors → skipped**, and supports later Owner-controlled targeted retry. Acceptable for r2 design; Stage2 must preserve both counters/trace and make this configurable only via a new immutable scientific protocol version.
2. **Proposed runtime**: three persistent checked Model Servers,18 retained Task simulator processes (6 EGL Task contexts per GPU when3 GPUs), sticky Task ownership and at most one active Local-TTT Episode session per Server. **No real feasibility evidence** yet. If native capacity/NUMA/rendering/VRAM constraints fail, return `BLOCKED_RESOURCE` and seek a revised plan, not silently degrade to900 full model reloads or 900 unbounded EGL rebuilds. GPU7 prior EGL SIGABRT remains independently unresolved; no automatic exception swallowing or unauthorized reset.
3. The fresh D5 protocol may interleave policy RNG across Task switches on resident model servers. It is **not** scientifically identical to the old task-major one-Server-per-Task/50 consecutive reset protocol. Record Task ordering/actual Seed/stream/physical worker/Local resets, ensure all compared policies share versioned scheduling and scene-admission conditions, and do not assert matched old RNG stream.
4. **Native adapter mandatory later**: new explicit production launcher; strict post-`env.step()` `env._check_success` (legacy Child currently swallows exceptions), pre-inference initial-success admission, no policy/Local for rejected scene, exact Local begin/ack/record_completed/end/reset, raw15→env12 and real action evidence; Core Invalid vs BehavioralFailure; native source+checkpoint identity, per-worker PID/start/PGID/port ownership and health; bounded video encoding (C), no final ffmpeg. A production failure after scientific commit cannot overwrite SR, but unresolved process health must remain visible.
5. **Owner authorization integration**: prototype `authorize_retry(... owner_ref)` is a ledger API and does **not authenticate** the human Owner. Stage2 must provide externally reviewed Owner-granted re-test targeting; generic automated Resume must never call it. Positive cleanup/health probes are synthetic callbacks now; Stage2 must bind actual pid/start/session proof, never trust simply a caller-supplied boolean.
6. **Performance**: author synthetic900 test alone ~178s, 104-test suite ~287s. Stage2 must measure p50/p95 coordination/slot-commit overhead, index rebuild and Ledger I/O, avoid O(N²) repeated scans on each event. This is **nonblocking design feedback**, not a claimed native performance regression.

## 5. Verdict and next Gate boundary

**`APPROVE_DESIGN` — all D1–D5 resolved at the frozen design/isolated-CPU prototype Gate, zero currently substantiated Design blockers.** Prior r1 D1/D2 now marked `CLOSED (Design scope)`; D3/D4/D5 new requirements `CLOSED (Design scope)`. No `APPROVE` for implementation, production wiring, DS CPU gate, real model/GPU/EGL, or 900 physical Episodes. The r2 `104 passed` belongs solely to author evidence; independent DS_PRO CPU and native Canary are **not run**.

**Next permissible work only after separate Owner/Codex scope approval**: Stage2 isolated candidate **production implementation** with its own new Formal Root/Child SHA, test/probe and focused static/CPU Code Gate; independent DS_PRO CPU acceptance; separately authorized small real RoboCasa Canary (scene precheck, video independence, Local reset, scheduler/resources, GPU7 exclusion if still unstable); Owner alone authorizes fresh900. No merge V3 now, no change to training/Checkpoint/old431, no automatic server/GPU launch.

This review is formal only after its detailed Markdown and append-only entry in `docs/collab/chatgpt/CODEX_INBOX.md` are both published and remote-verified.
