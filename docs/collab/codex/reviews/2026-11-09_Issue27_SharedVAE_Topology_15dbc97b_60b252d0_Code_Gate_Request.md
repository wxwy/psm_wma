# Issue27: general shared-VAE topology — fresh Code Gate request

Author: Codex. Date: 2026-11-09 CST. Status: **AUTHOR_CPU_PASS; independent
GPT Code Gate requested**. This is an implementation/evidence handoff, not an
independent approval, hardware acceptance or merge authorization.

## Frozen authority

| Object | Exact SHA |
| --- | --- |
| Formal Root | `15dbc97bf13437905ec38247382834067e5341ae` |
| Child / Root Gitlink | `60b252d05157b2753d2caebae32b11c878504bbe` |
| Root base, official V3 at claim/publication precheck | `e58cef1f53d2382d39c871ce5a50e4acdd5ce268` |
| Child base, official v3-local-ttt | `b0dbd115d03e801ec4d0788c30ee0b0e9655d4db` |
| Previous V3 pinned Child | `00f30235da6ffb085a9304ef6501ede509203092` |

The last two Child bases have identical complete tree
`c4c33db6ecfb9508c44c5b28df3cc81f5b1e0361`. New Child derives from the official
merged branch without source drift. Both new isolated branches are
`v3-shared-vae-topology-issue27-20261109`; create NEW independent Draft PRs to
Root V3 and Child v3-local-ttt. Prior merged Root25/Child7 are not updated.
Evidence/ledger-only successor Root commits do not replace Formal Root.

Owner's final Issue27 clarification is authoritative: support every legal
resource/capacity bounded Server/Sim combination. One Server/one Sim, one/eight
and two/sixteen total Sims are representative tests, never an allowed-value list.
No new runtime/scheduler, rollback, training changes or official branch update.

## Production increment to review

Root changes only `scripts/robocasa_eval_v2/config.py` and `shared_vae.py`:

- General shared-history validation and frozen `execution.shared_vae` identity
  are independent of the optional original single A/B/C measurement identity.
  Configure general operation with `single_latency_arm: null`.
- Existing Runtime creates configured Servers/Sim slots. Supervisor keeps one
  Worker per physical Sim/render GPU, enrolls it separately with each Policy
  Server and routes each Session to its Policy Owner, keyed by both GPUs.
- Reused Workers must match the next Policy's actual VAE identity, clock and
  frozen constructor. Session/Policy capacities derive from existing slot maps;
  actual READY limits are checked before admission. Private FD credentials,
  Registry, reservations and owned-only lifecycle remain.

Child changes only six production modules:

- `evaluation/robocasa_v2/contract.py`: strict general shared-history identity;
  original full M/B/resource/Resume comparison and single measurement identity.
- `scripts/action_policy_server_robocasa.py`: accept configured Policy1..8,
  report actual cap/wait, stage each member's original current-frame boundary.
- `inference/robocasa_batch_transactions.py`: original Native READY executor;
  yield to already-admitted preparation tasks queued behind its pump instead of
  serializing all feature requests into B1. No wait for absent peers. Original
  deadlines, seal/fault ownership, ACK/replay and atomic snapshots stay intact.
- `inference/robocasa_boundary_capture.py`: ordered per-member observation of
  existing B1 current encodes; full original RGB/model/lease/deadline checks;
  all group boundaries stay private unless every member succeeds. No extra
  Encode1, no VAE B8 and no native model method change.
- `inference/robocasa_vae_worker.py` and `robocasa_vae_daemon.py`: bounded
  multiple Policy epochs within one run/manifest; each slot still pins its own
  epoch and increasing generation. Default standalone capacity remains one
  Policy epoch. Existing session/queue/byte/resource limits remain bounded.

Worker encoding remains **Bvae1/wait0**, exact fifteen signed frames plus one
committed current boundary and sixteen causal T1 updates. No-TTT/server_vae,
optional single-instance A/B/C metadata, source/physical identity, Local math,
sampling, scheduler authority and full M/B Resume identity are preserved.
Original round task-count/M8 limits and streaming M32 behavior remain; general
shared Policy cap1..8 is independent. Hardware/pending work still bounds activity.

Four new Root CPU files and six new Child CPU files cover the increment. One
existing three-case test now explicitly selects single measurement C, retaining
its original B1/wait0 rejection for that optional measurement mode. New general
mode acceptance is tested separately. No other existing tests are weakened.

## Exact-pair author evidence

Raw directory: `docs/collab/codex/evidence/2026-11-09_issue27_shared_vae_topology/`.
See `summary.json`, `author-01/gate.json`, full original JUnits/logs and
`artifact_hashes.json`. Exact clean worktrees/Gitlink were checked before running;
all source fingerprints match afterward. Only bookkeeping follows this run.

| Suite | Top-level PASS | Successful subtests | Fail/error/skip |
| --- | --- | --- | --- |
| Child Stage3/shared-VAE original + new | 472 | 207 | 0/0/0 |
| Root lifecycle/config/source/IPC | 289 | 0 | 0/0/0 |
| Legacy No-TTT/Local/Batch/Sim | 143 | 0 | 0/0/0 |
| Streaming capacity/resources/startup completion | 61 | 0 | 0/0/0 |
| Total | **965** | **207** | **0/0/0** |

JUnit suite `tests` total is **1172**, containing965 top-level testcase elements
and207 subtests, not1172 independent top-level tests. **83 new top-level cases**
are enumerated in `new_testcases.json`. Development runs are not added again.
Ruff check/format and syntax19 changed Python files PASS; shell exit0,
gate.status=PASS, source_unchanged=true; native constructor/identity unchanged.

Focused behavioral evidence:

- Config/property and public YAML/CLI preview cover representative and other
  legal shapes, independent Policy caps1..8 and streaming M32. Actual Root
  server argv is accepted by Child strict options with every intended Slot and
  original cap; no Policy B1 fallback. Generic M/B/wait/Worker-resource identity
  changes fail the real Store lock/Manifest check without changing persisted data.
- Same model executor deterministic interleaving places seven preparation tasks
  behind an already-queued pump; actual generation is one batch8 and histogram
  is{8:1}. All caps1..8 map results to original Sessions, with replay/ACK. Empty
  peer queues do not wait even when the configured window is1000ms. Deadline
  exhaustion during generation aborts the whole sealed group with no snapshot.
- Actual production service method performs one native generation for N1/2/4/8,
  with exactly N original B1 encodes. Ordered capture matches singleton boundary
  bytes, preserves pre-crop semantics and rejects missing/extra/swapped/expired
  observations. One failed member prevents all group publication.
- Eight authenticated15+1 histories use actual HMAC/Owner admission, T1 Local
  math and atomic multi-member snapshots. No historical decode/encode;128 causal
  single-step updates, Session separation, exact replay and isolated End/reset.
- Real supervisor/Worker subprocess/private FD/Unix IPC/Owner HTTP routes cover
  one/one,one/eight,two/sixteen; two Policy Servers sharing one render GPU start
  exactly one Worker. A three-Server shape also passes. Derived READY limits,
  all leases, per-Policy owners, isolated End, Worker exit0, IPC cleanup and a
  surviving unrelated CPU process are asserted. `os_behavior/` holds the proofs.
- Worker CPU tests cover multiple epochs, up to32 live Sessions, Bvae histogram
  only1, signed-result binding, wrong capability/run/manifest/slot epoch/stale
  generation/capacity rejection. Original Worker failure/backpressure/drain tests
  and existing source guards remain in the author Gate.

Authoritative old RED: `red-final-test-bytes/`: two expected failures at the
old Root single-topology and Child Policy-B1 guards. Only final new test files
are injected; old production hashes are identical. `tests_injected=true` makes
the dirty fixture explicit. Final GREEN verifies identical test hashes. Earlier
RED/development formatter/kernel/token/baseline-placement mistakes are retained,
including the initial static harness failure; none are counted as passing Gate.

## Reproduction and boundary

Working directory `/workspace/work/psm-wma-shared-vae-issue27`:

```bash
/workspace/.venvs/psm-wma-cpu/bin/python \
  /workspace/work/issue27-shared-vae-evidence/run_cpu_gate.py \
  --root /workspace/work/psm-wma-shared-vae-issue27 \
  --expected-root 15dbc97bf13437905ec38247382834067e5341ae \
  --expected-child 60b252d05157b2753d2caebae32b11c878504bbe \
  --evidence-dir /workspace/work/issue27-shared-vae-evidence/author-01
```

For independent reproduction check out the exact clean Pair and choose a NEW
evidence directory. Archived runner: `runners/run_cpu_gate.py`. It sets CUDA
visibility empty, offline model libraries, pytest autoload off, numeric threads1
and external caches. Python3.12.14, torch2.10.0+cpu, pytest9.0.2, Ruff0.12.7,
OmegaConf2.3.0; exact versions and overrides are archived.

Cloud Linux lacks timens proc entries: the existing explicit CPU kernel-identity
fixture supplies those records while exercising the unchanged production parser.
Encoders, diffusion generation and environment execution are controlled doubles;
real Local math, protocol/authentication, state, service methods, process/IPC/HTTP
are exercised. This is not a native-clock, real Wan/DCP, EGL, Action numerical,
throughput or SR acceptance. No server files or checkpoints were accessed/copied.

Next: fresh independent GPT incremental Code Gate for this exact Pair. Only after
that, separately authorize a bounded real multi-session GPU smoke. Preserve the
previous single-B1 functional/performance results as history; do not claim they
prove new multi-Sim performance. No repeated SR/900EP, training, automatic V3 merge
or modification of running jobs belongs to this task.
