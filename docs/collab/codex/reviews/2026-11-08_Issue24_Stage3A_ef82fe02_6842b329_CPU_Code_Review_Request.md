# Issue24 / Issue23 Stage3A — author implementation and focused CPU Code Gate request

Date: 2026-11-08 (Asia/Shanghai). Author: Codex. Status: **REVIEW REQUESTED**.
This is author evidence, not GPT approval, independent DS acceptance, or a real
model numerical/performance/SR result.

## Exact source authority

| Object | Full SHA |
|---|---|
| Formal Root implementation | `ef82fe02ee73e3c804b83ffbd68c5123c1377fa2` |
| Child / Root Gitlink | `6842b329f71fff8b9813b2d00b83edfc61e3e505` |
| Frozen Root design base | `afd0b21f1f994bdf2b21cfbaa4a260ced8eeaaf9` |
| Approved Stage1 Child base | `0a2119782fb5078fee3359f9ef7383d788744458` |

Both isolated branches are `v3-stage3a-issue24-20261108`. Root evidence/Inbox
successors are metadata only and do not replace the Formal Root above. Official
V3 and Child `v3-local-ttt`, prior PR4/5/6 and evaluation/training jobs are untouched.
The complete implementation range is design base → Formal Root, not merely the
last Root commit. The Child range is approved Stage1 base → final Child.

- [Owner task #24](https://github.com/wxwy/psm_wma/issues/24)
- [Root incremental implementation diff](https://github.com/wxwy/psm_wma/compare/afd0b21f1f994bdf2b21cfbaa4a260ced8eeaaf9...ef82fe02ee73e3c804b83ffbd68c5123c1377fa2)
- [Child incremental implementation diff](https://github.com/wxwy/cosmos-framework/compare/0a2119782fb5078fee3359f9ef7383d788744458...6842b329f71fff8b9813b2d00b83edfc61e3e505)
- Frozen design and acceptance matrix remain unchanged in `docs/collab/chatgpt/designs/2026-11-08_Issue23_Stage3_*`.
- Child implementation/API/limitations: `docs/designs/issue24_stage3a/README.md`.

## Implemented Stage3A boundary

1. Native Sim copies pre-action RGB and canonical raw15; only a successful actual
   `env.step` return emits its scoped Actor completion. Root checks the enrolled
   Actor/Lease and original committed native response; Policy Owner verifies the
   canonical issued action and completion ledger. Sim never receives the global
   Owner token, Worker control capability or signing key. HMAC alone is not treated
   as execution evidence. Trust is explicitly `registry_same_trust_domain`, not
   cryptographic proof of physics or a new OS security boundary.
2. A default-no-op observer captures the original Policy current-frame Encode1
   Visual96 before latent crop, without invoking a second encode. Boundary visual,
   FastState and cached Response publish through the existing atomic MemorySnapshot.
   Owner-only boundary skip advances all four real source frontiers atomically:
   source0 + Worker1..15, then source16 + Worker17..31. Indices are never renumbered.
   Missing/mismatched cache, post-step evidence, identity, epoch, deadline, action
   or feature signature fails closed; no PNG/server-VAE fallback in C.
3. C uses existing OnlineMemoryRequest, model-owned causal16×T1 updates and the
   existing native prepare/commit/abort/replay/ACK/session machinery. Preparation
   runs on the existing model executor outside the actor admission lock; only a
   prepared candidate enters native READY. C is B1/wait0. B retains16 Policy
   Encode1 + T16; A/off creates no history Worker. Failed prepare/End requires
   proven drain or quarantine, retaining the original first error.
4. Root owns one run-level Worker Registry peer per selected Sim GPU, private FD
   bootstrap, scoped Session channels, bounded resources and owned-only process
   cleanup. Worker lifetime does not depend on a Sim process. Both Policy/Worker
   hash actual loaded tensors/scale/config; actual loaded parameter CUDA UUID/PCI
   must match the selected device. NVIDIA-only EGL vendor env is Sim-only. These
   real-device checks are implemented and CPU-negative-tested, not hardware proven.
5. One immutable Replan budget starts before payload/feature waits and covers TTT,
   generation/retries/ACK. Float conversion only tightens it. Cleanup has a separate
   bounded budget. A/B/C single profiles, full execution identity and resources are
   explicit. The Child contract adds only the authorized opt-in identity shape;
   legacy exact schemas, full M/B Resume comparison and source guards stay strict.
   No design invariant conflict or unresolved DESIGN_DELTA was identified.
6. Bounded raw host spans and correct-stream CUDA-event records support first/steady
   Replan, history/current VAE, TTT, prefix, queue, HTTP/IPC, generation and lifecycle.
   Compute intervals are separate from exposed waiting and overlap is retained.
   Missing GPU events/drop/overflow are incomplete, never synthetic timing. Raw
   sidecars are atomic; Core contains only path/hash/count. Post-publication commit
   and ACK records use bounded `PSM24_POLICY_TRACE` lines in the owned Policy log.
   EGL is included in env.step where separate observation is unavailable.

Root changes: configuration/identity, shared VAE lifecycle/Owner bridge, resources,
startup and runtime glue, plus focused tests. Child changes: boundary/evidence/trace
modules, real Wan daemon, sparse Worker protocol, scoped Sim adapter and existing
Policy/Local Memory/native transaction integration, plus tests. Ruff formatted
the changed Python scope; some existing-model diff is formatting. Training
configs/parameters/semantics and official branches were not changed.

## Exact-pair author CPU result

**PASS: 654 top-level tests plus 207 subtests; zero failures/errors/skips.**
JUnit suite `tests` attributes total **861** including the207 subtests; XML has
**654 testcase elements**. These are not861 independent top-level tests.
Ruff check/format: PASS on all36 changed Python files. Shell exit0,
`gate.status=PASS`, `source_unchanged=true`, identical before/after source snapshots.

| Group | Top-level PASS / XML testcase elements | Subtest PASS | JUnit suite tests |
|---|---:|---:|---:|
| Stage3, Stage1 Worker, native feature/HTTP/Sim |359|207|566|
| Root lifecycle/config/physical-resource contracts |152|0|152|
| Existing Session/dual-mode/TTT/batch/Sim protection |143|0|143|
| Total |654|207|861|

CPU uses real local HTTP, Unix IPC and owned subprocesses where applicable, with
synthetic Env/encoder/model and CPU tensor substitutes. Assertions cover canonical
issued actions/post-step rejection; real indices/two chunks/two Episodes; all4
frontiers; signature/replay/session/epoch rejection; one current encode; exact CPU
T16 vs16×T1 state/prefix equivalence; atomic commit/abort/replay; READY outside lock;
frozen deadline/retry/ACK; Worker peer survival/private FD/owned cleanup/external
process isolation; resource/manifest/legacy protections; bounded trace integrity.
No real VAE/model/Sim numerical or performance conclusion follows from these tests.

Final invocation (already executed once at the exact clean Pair):

```bash
cd /workspace/work/psm-wma-stage3a-issue24
/workspace/.venvs/psm-wma-cpu/bin/python \
  /workspace/work/issue24-stage3a-evidence/run_cpu_gate.py \
  --root /workspace/work/psm-wma-stage3a-issue24 \
  --expected-root ef82fe02ee73e3c804b83ffbd68c5123c1377fa2 \
  --expected-child 6842b329f71fff8b9813b2d00b83edfc61e3e505 \
  --evidence-dir /workspace/work/issue24-stage3a-evidence/author-04
```

Python3.12.14 / torch2.10.0+cpu / pytest9.0.2 / Ruff0.12.7. CUDA disabled;
HF/transformers offline; pytest plugin autoload disabled; numeric threads1;
exact whitelisted overrides, argv/cwd/timeouts and timings are archived. No
dependencies installed, real checkpoint/dataset read, or remote server accessed.

## Raw evidence and previous failures

Archive: `docs/collab/codex/evidence/2026-11-08_issue24_stage3a/`.
`author_result.json` is the machine summary; `author-04/gate.json`, all3 original
JUnit XML/log pairs, original source identity/snapshots, version/env/static logs
are authoritative author output. `artifact_sha256.json` inventories archive bytes.
The exact runner/formatter are archived as `.py.txt`, not installed as new launchers.
Additional Registry process/process_closed records and synthetic complete/overflow-negative
raw traces are included with provenance. Registry process_closed records are not a
Root IPC CLOSED receipt; that Root receipt was asserted in memory. Overflow trace
is deliberately incomplete. Earlier gate.json files omit the failing group summary
on early exit; corrected machine attempt counts derive from the original JUnit,
not from absent gate fields. The raw gate/JUnit/log bytes remain unchanged.
Tmp caches/bootstrap/actor configs/inherited env are excluded; no private key or
real server file is published. Actual local process/FD/IPC lifecycle records are under `author-04/os_lifecycle/`,
with original-path provenance. Both report external process survival and owned exit0;
Root proof records Worker survival after Sim End. These CPU fixtures are not
hardware evidence; test assertions/JUnit must not be mislabeled hardware proof.

Earlier attempts are retained byte-for-byte, not overwritten or counted as final
PASS. Every attempt had `source_unchanged=true`:

| Attempt | Root / Child prefixes | Actual result and correction |
|---|---|---|
|author-01|c9456eb8 /2ced1808|357 PASS,2 FAIL,+207 subtests; Root/legacy NOT_RUN. Failed/cancelled prepare had drained but omitted quiescent metadata. Fixed proven-quiescence publication; uncertain drain remains quarantined.|
|author-02|305af76c /05cf413f|359+207 and152 PASS; legacy135 PASS,8 FAIL. Truthy dynamic Mock markers incorrectly enabled C hooks. Changed all new admission checks to explicit `uses_shared_vae is True`; old assertions retained.|
|author-03|141243da /68015f4c|359+207 and152 PASS; legacy135 PASS,8 FAIL. AST-only legacy fixture lacked new optional `get_trace`/`nullcontext` globals. Added only imports/namespace; all original assertions retained. Narrow development check8/8 PASS is archived separately.|
|author-04|ef82fe02 /6842b329|All654+207 PASS; this alone is final exact-pair evidence.|

## Open independent Gates and explicit limitations

Requested next: GPT independent **APPROVE_CODE / REQUEST_CHANGES** for this exact
Stage3A Pair and raw CPU evidence. No prior approval is inherited as approval of
this integration. Published evidence/Inbox commits and Draft PR availability are
not reviewer acknowledgement or Gate closure.

- Real Wan BF16 / Local checkpoint / H100 / EGL / RoboCasa: NOT_RUN.
- P0 A/B/C1Server×1Sim, PolicyB1/H16 raw latency and paired SR: NOT_RUN; separate
  Owner execution authorization after Code Gate. A uses native No-TTT checkpoint;
  B/C must share the same Local checkpoint and conditions. Cross-checkpoint SR
  differences cannot establish the isolated causal effect of online TTT.
- C currently accepts frozen eager BF16 Wan; an incompatible installed AOT backend
  fails closed. Supporting a different backend requires a separately reviewed change.
- B4/B8 Action feature admission is disabled; Stage3B numeric/action/SR/throughput
  acceptance is separate. No claimed latency, throughput or SR improvement.
- V3 merge/deployment, real900EP, training changes and old-run Resume: NOT_PERFORMED.
  M/B Resume consistency remains strict. No automatic polling or execution claimed.
