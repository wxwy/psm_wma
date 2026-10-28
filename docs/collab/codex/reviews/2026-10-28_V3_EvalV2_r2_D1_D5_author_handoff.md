# Evaluation V2 r2 — D1–D5 author handoff / fresh Design Review request

2026-10-28 Asia/Shanghai. **Design + isolated CPU prototype only; STOP before production.**

| Object | Exact identity |
| --- | --- |
| Formal r2 Design/Prototype Root | `1fd3ad42075032bd0137ac9a76306169aaa45032` |
| Child / Gitlink (unchanged) | `746c5cf2f2324104a62fb71510343aa40d3976c5` |
| Prior reviewed r1 Root | `dc750f8e258d10a33e7a195cf907926b1c98bd7f` |
| Latest canonical D1–D5 Owner contract | V3 `b59d1faf486765271295a00ee5e20e4d239e0163` |
| Latest V3 consumed at publication | `0b179e8f611ede5200cae2f9485c1a601774778e` (unrelated Compact resource docs) |
| Isolated candidate | `v3-eval-v2-design-r2-20261028` |

Following evidence/ledger HEAD does not replace the Formal Design Root. Canonical V3 was not updated by this task. Production `scripts/`, `configs/`, `third_party/`, Child source and Gitlink have ZERO diff against r1 and latest canonical source. No GPU/Action Server/simulator/native rollout/DCP/training/history431 IO.

## Reading ACK before edits

Full D1–D4 contract was read at9858e70b and ACK committed `bfbcdcf9`; added D5 and the entire updated contract were read atb59d1faf and ACK committed `5ae38125`, BEFORE D5 source changes. Both ACKs were pushed and remain ancestors of the formal Root. Explicit record: `docs/collab/codex/reviews/2026-10-28_EvalV2_r2_Codex_reading_ACK.md`; exact binding in Evidence `ACK_and_contract_binding.json`.

GitHub Issue #7 API returned Forbidden (GraphQL and REST). ACK uses the explicitly allowed handoff/Inbox channel; no Issue comment is claimed. Latest requirements are the canonical D1–D5 contract, not a choice among old opinions. Whole-Task replay/fixed per-Episode seed/scene reconstruction/media-gated SR/automatic skip retry are withdrawn and absent from r2.

## Implemented in the isolated prototype

| Contract | Actual prototype path | Acceptance |
| --- | --- | --- |
| D1 scoped fault lifecycle | `store.py` process errors, owned cleanup, recovery certificates, immutable resolutions | Old missing-attempt fault requires same-index valid retry after cleanup/new health; committed-result late fault uses explicit execution-only recovery. Current faults block. Faults/history retained, resolutions revalidated. Per-Task isolation and global qualification distinct; open Workers prevent clean qualification. |
| D2 claim/commit recovery | `store.py` intent->directory->ready, numbered attempt/events, exclusive Core commit | Task+slot four init boundaries; before/after Core; coordinator/claim crash; ownership/foreign/asynchronous responses reject; lost/ambiguous authority BLOCKED without deletion; critical faults persist before terminal event. |
| D3 Episode-only Resume | `store.py`, `scene_test.py` | Valid success AND behavioral_failure immutable;37 only if uncommitted,0..36 unchanged, sparse later valid slots survive. New actual seed/stream/reset boundary; no old scene/RNG replay or fixed SHA seed. |
| D4 initial scene admission | `admission.py` + persistent initialization ledger | Typed precheck before model/action/Local, bounded degenerate rejection, independent error streak and total budget, fourth recoverable error Skip, safe continuation, explicit one-use Owner permit only. Counter survives crash; unsafe faults stop. ENV_REBUILT explicit. |
| D5 real scheduler wiring in prototype | `scheduler.py` -> Store claim -> token-bound Core commit | Frozen original Task order, Episode-major900 plan; same-round async dispatch and strict barrier; Fresh/Resume same scan, authoritative skips; tickets prevent bypass/duplicate/stale GPU claims, cancellation preserves in-flight positions. |

Scientific SR is environment post-step authority with horizon behavioral failure. Invalid/Pending/Skipped/exhausted slots keep full SR null, partial SR explicitly conditional. Late process fault does not rewrite scientific outcomes. Media is diagnostic, no automatic ffmpeg or copied videos; all old431 compatibility intentionally excluded. Summaries and episode index are rebuilt views, never admission authority.

## Author CPU Evidence — not DS or native execution

**104 passed,0failures,0errors,0skips,287.051s**, five test modules. Ruff0.12.7 check/format, AST10 Python files, frozen10 SHA + committed blobs PASS. One CPU Torch import pynvml deprecation warning; CPU Torch RNG tests assert CUDA remains uninitialized.

- Actual prototype scheduler dispatched900 unique fake slots in exact Episode-major order,50 barriers,450 synthetic success/450 failure,SR0.5. Separate3 asynchronous CPU workers prove completion may reorder while dispatch/barriers remain ordered.
- Before/after commit, in-flight, between Tasks, round-boundary cancellation/Resume: exact valid-result bytes and inodes preserved, no valid failure retest. Skip37 + valid38 ordinary Resume skip; only an explicitly released missing37 dispatches.
- Four-error skip LIVE within a round is a deferred gap, not success; next round waits for other Workers. Degenerate precheck does not count an Episode. Unsafe initialization becomes Process Error, not four-strike continuation.
-50 skipped Episodes with four long errors each originally exposed an oversized-report failure. Direct negative `report_bound_red` retained; final test publishes PARTIAL/null SR/all50 IDs and all diagnostics. Only derived summaries have a finite16MiB bound; Core/ledger256KiB remains, report-bound misuse and contradictory admitted-reset data reject.
- All earlier iterations/failed traces are under `prior_iterations/` with separate source hashes/commands/JUnit/exit, never aggregated. Prior101PASS was a previous source version, not extra104 cases. Earlier r1 65PASS likewise not inherited as r2 approval.

Evidence: `docs/collab/codex/evidence/2026-10-28_eval_v2_r2_D1_D5_author_cpu/` includes original final JUnit/log/command/env, static logs,10 committed source bindings, true full and prototype-only r1->r2 patches, protected-path proof, artifact SHA256 index, actual test-created fake900 directory archive and long-error summary. These samples are NOT real rollouts/model loads/EGL evidence and must not enter production.

Reproduce from clean detached formal Root/Child with outputs outside source:

```bash
CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPATH=<ROOT> HF_HOME=<TMP>/hf MPLCONFIGDIR=<TMP>/mpl XDG_CACHE_HOME=<TMP>/cache \
  <CPU_PYTHON> -m pytest --noconftest -c /dev/null --rootdir=<ROOT> -p no:cacheprovider \
  -q -s -x tools/v3/episode_eval_v2_prototype --junitxml=<NEW_EXTERNAL_DIR>/junit.xml
```

Actual author watchdog600s is test-only; no production timeout changed. CPU Python3.12.14/Torch2.10.0+cpu/NumPy2.2.6/pytest9.0.2. Native real-assets/full-repo CPU/GPU/DS independence are not claimed.

## Concrete design choices for review / remaining boundary

Canonical r2 design: `docs/build/PSM-WMA_V3_RoboCasa_Evaluation_V2_design_r2_2026-10-28.md`.

1.32 total reset/admission samples per logical slot Owner-authorization round; fourth consecutive recoverable error still skips sooner.32 is a proposed concrete manifest budget, not an Owner quote. Exhausted/Skipped remain Owner-pending.
2. Runtime proposal:3 checked resident model Servers and18 retained Task environment processes,6 bounded EGL contexts per GPU, sticky Task ownership, one active Local Episode session per Server. Measured RSS/VRAM/context/Local isolation gate required; capacity failure BLOCKED_RESOURCE, never silently900 reloads/rebuilds. Mock counters are design lifecycle witnesses only.
3. Actual Stage2 server/PID ownership probes, native reset observation routing, model/Local/action chronology, source verification, bounded encoder/spool, physical resource admission and real simulator compatibility are NOT implemented here. Store lower-level helpers support focused tests; new RoundScheduler is the governing isolated coordinator with enforced tickets while attached.

Request GPT fresh incremental **D1–D5 Design verdict** for the exact pair, then STOP. No claim the old r1 REQUEST_CHANGES is closed by author tests. No V3 merge, automatic production wiring, DS launch, Canary or900 real test authorization. Current G1/NoTTT/old evidence remain untouched.
