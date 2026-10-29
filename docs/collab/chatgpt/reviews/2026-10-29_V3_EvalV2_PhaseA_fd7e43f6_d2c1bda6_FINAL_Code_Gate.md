# GPT independent Phase A Code Gate — Dynamic Reusable Sim Slots (2026-10-29)

## 1. Formal target and binding

**Verdict: `APPROVE_CODE` — Phase A production source Code Gate ONLY.** No substantiated blocking source-level defect in the reviewed exact Formal Pair. This is NOT DS independent CPU approval and NOT native/GPU/EGL/RoboCasa/900 or Phase B authorization.

| Authority | Frozen value |
| --- | --- |
| Formal Root implementation | `fd7e43f6630a436ab3d83edcd3ce9d1516b342d1` |
| Formal Child / Root Gitlink | `d2c1bda62880dbeee196f70945e5bc430b73f4b6` |
| Isolated candidate branch | `v3-eval-v2-slots-a-20261028` (both repos) |
| Previous approved source-only baseline | Root `4769d711777c20a72dd7a3f6071a96f08ad8abb0` / Child `2d4a42590fead00ea16f6ae5902e2bc8382b07e2` |
| Root direct parent | `1ac82af40a95587dd3f5e016dbc6a7e73ebeb9c2` |
| Child direct parent | `2d4a42590fead00ea16f6ae5902e2bc8382b07e2` |
| Handoff/Evidence documentation ref | `711ee8be40311d3cade19946cee4e23e508c3727` (bookkeeping ref, **not** Formal Root implementation SHA) |

I independently fetched the Formal Root Git tree from GitHub and observed `cosmos-framework` mode `160000`, exactly Child `d2c1bda62880dbeee196f70945e5bc430b73f4b6`. Both formal commits exist. Current canonical `V3` documentation HEAD is independent from this candidate. Nothing here merges or updates the implementation branch.

**Frozen contract:** `docs/collab/chatgpt/requests/2026-10-28_V3_EvalV2_Dynamic_SimSlots_LocalTTT_Batch_Owner_Implementation_Directive.md` (Phase A implemented now, M=1/B=1, Phase B design first after Phase A Gate), with still-binding D1–D5 in `2026-10-28_V3_RoboCasa_EvalV2_r2_CANONICAL_LATEST_OWNER_CONTRACT.md`. Previous Stage2 corrected FINAL `APPROVE_CODE` is historical and exact-pair scoped. The earlier alleged D1 F1 commit/cancel race was **WITHDRAWN**; it is not a current blocker and must not be fixed speculatively.

## 2. Incremental actual source review

I reviewed the whole Phase A source delta, not merely the last small Root commit. Root baseline→Formal Pair contains non-Phase-A documentation/evidence bookkeeping commits; the technical scope is the new/revised Phase A runtime/config/identity/example/test/runbook and Child code. Child `2d4a4259..d2c1bda6` is one commit, changing seven files (new `eval_v2_slot.py`, adapter, worker, Scheduler, Store, Contract, Evidence). No model/optimizer/trainer/Vendor or old V1 evaluation changes are part of this Phase A implementation delta.

| Contract behavior | Actual source and independent reading | Gate |
| --- | --- | --- |
| Dynamic G/N, M=1/B=1 | Root `config.py:26–27,50–55,103–120` accepts a GPU list and Task subset, explicitly rejects unsupported M/B. Root `runtime.py:56–58` bounds active physical workers to `min(G,N)`; `_server` is cached by physical worker. `identity.py:64–75` removes Task-count-dependent 18-resident-env capacity constraint. | **ACCEPT source** |
| Physical reusable Sim Slot, no Task-affinity | Child `scheduler.py:91–135` dispatches ordered logical items to *any idle physical worker*, preserving strict round barrier `:134–142`. Root `runtime.py:171–350` caches actors by physical worker, not Task; Child `eval_v2_worker.py:17–105` dispatches owned socket messages to one reusable `SimSlot`. | **ACCEPT source** |
| Cross-Task env lifecycle | Child `eval_v2_slot.py:28–63,81–128` attests allowed Task and dataset metadata; different Task → `env.close()` → new grant checked against immutable Store → `native.make_env()`, same Task reuses object; `initialize()` resets on every logical Episode. Forbidden switches and dirty states fail closed. | **ACCEPT source** |
| Episode-local Fast Weight/session | Child `eval_v2_slot.py:130–207` admits scene before Session and requires native `local_session.reset_ack` before CLEAN, quarantines on failed Local cleanup. Child `eval_v2_adapter.py:72–221` creates a new Local client per Episode, passes completed evidence through unchanged original native action policy, checks cleanup and returns per-Episode IDs/frontier. Existing service state remains `session_id`-keyed, no Slot-keyed Fast State. | **ACCEPT source**, actual tensor numerics **UNTESTED** |
| Explicit sampling honesty | Child `store.py:407–463` records immutable Task-environment grants with monotonically allocated per-Task ordinals and versioned per-environment seeds; `eval_v2_slot.py:139–146` reports real per-env seed/reset index/physical Slot. Root `runtime.py:390–455` binds admission then requires final response equality; Child Store/Evidence reject conflicting Core scene provenance. It does not claim previous contiguous 50-reset streams or scene replay. | **ACCEPT source** |
| D1–D5 preserved | Child `scheduler.py:18–28,91–181` retains Episode-major strict barrier/Resume skip/commit-vs-cancel lock; Child `store.py:585–844` retains scene admission/4-strike Owner-pending and immutable valid success/failure. Root `runtime.py:351–515,679–697` preserves after-step strict outcome, process fault scoping, Core commit, cleanup, and media independence. | **ACCEPT source** |
| Late unexpected Slot exit after final Core | Root final code `runtime.py:620–625` checks every still-owned physical actor even after a final Core finishes; `runtime.py:679–697` cancels **before** registering affected fault. A late exit retains immutable Core but blocks clean qualification until fresh positive recovery. Author provided RED pre-last-commit/ GREEN exact-pair CPU case. | **ACCEPT source** |

The `M>1` / true batch Local-TTT method is deliberately absent, rather than claimed implemented by raising `max_sessions`; the existing required Local-TTT server batch rejection remains untouched. This is **correct Phase A scope**.

## 3. Actual Evidence assessment and limits

Author's final frozen directory (documentation/evidence commit, **not formal source target**):
`docs/collab/codex/evidence/2026-10-28_eval_v2_phase_a_author_cpu/final03/`.

- Independently fetched the actual `final03/junit.xml` header: `tests=255`, `errors=0`, `failures=0`, `skipped=0`, `time=178.035`. Also fetched `final03/exit.json` with `exit_code=0`, `frozen_source_match=true`, and `pytest.log` tail: `255 passed, 1 warning in 178.04s`. One `pynvml` FutureWarning is not a test failure.
- Independently read final `static_final03/static.json` commands: author reports Ruff `0.12.7` check/format and 37 AST files, Bash syntax/help, source checks, all zero exit. This is original author log evidence, not GPT locally rerun static/pytest.
- Independently used GitHub `fetch_file` for **15/15 directly relevant frozen source/test Git Blob bindings**, all matching author `formal_source_bindings.json`: Child Contract/Evidence/Scheduler/Store/Adapter/Slot/Worker; Root Config/Identity/Runtime; five key Root production tests (Runtime/Scheduler/Slot/Slot-transport/Worker). Author lists 52 total source bindings and an 85-file artifact hash manifest; **I do not claim to have individually rehashed all 52/85**.
- Actual source test coverage inspected: the G={1,2,3,4,8}×N={1,2,4,7,18} dynamic matrix, TaskA/Ep0→TaskB/Ep0→TaskA/Ep1 lifecycle, Session reset ACK/quarantine/Resume, faithful model/physics boundary doubles, production Worker socket bridge, both commit/cancel orderings, sparse Core/Owner-skip Resume, late-zero-exit after last Core. `synthetic_900_metrics.json` author records 900 dispatches/50 barriers, three fake physical Slots/servers, 900 fake env creations, 450 fake successes/450 fake behavioral failures. This is **CPU synthetic**, not real RoboCasa SR.
- **Remaining validation limitation:** author and GPT have **NOT** executed real RoboCasa/MuJoCo/EGL, actual Cosmos model/DCP, GPU Load, true on-device W0/Fast Weight tensor semantics, VRAM or measured native 900 throughput. DS_PRO has not independently rerun Phase A CPU. No approval of these by this Gate.

## 4. Blockers and nonblocking caveats

**Current blocking findings: NONE substantiated for Phase A source-level Code Gate.** No old withdrawn F1 or Stage2 source verdict is copied as a blocker; this is a fresh review of a changed Formal Pair.

Nonblocking operational observations, not acceptance claims:
- `Kitchen.hard_reset=True` may rebuild MuJoCo resources on each episode; one reusable *process* is not a guarantee of cheap native scene reset. Real Task-switch/EGL memory/time must be measured in the separately authorized Canary.
- When `N<G`, Runtime lazily uses the first N selected GPUs, but `resources.check` conservatively checks **all configured selected GPUs** for ownership/budget. This can refuse a run if an unused selected GPU is busy. A conservative preflight refusal is not a source safety/correctness blocker; document actual behavior and do not claim unused selected GPUs are exempt from admission.
- `M=1` under global Episode-major order may construct up to900 Task environments for18×50, a deliberate resource/memory-vs-initialization tradeoff; no throughput superiority over the old resident-Sim candidate is established.

## 5. Exact Code Gate decision and next gates

**`APPROVE_CODE`** at **Formal Root `fd7e43f6630a436ab3d83edcd3ce9d1516b342d1` / Formal Child+Gitlink `d2c1bda62880dbeee196f70945e5bc430b73f4b6`**, **only** for Phase A source-level production implementation and author CPU evidence. It is not approval to merge or run models.

**Next required:** DS_PRO focused independent CPU on a clean checkout of this exact Root+Child pair, with frozen JUnit/static/source-binding replay, behavior-focused Slot/task switch/session ACK/quarantine, initial-success/4-error Owner skip, late-exit/commit-cancel both orderings, sparse Episode Resume, and process ownership proof. Then separate GPT incremental Evidence Gate. Any real GPU/Cosmos/DCP/RoboCasa/EGL Task-switch/Local-TTT semantic Canary, full 900 Episode run, V3/Child merge or training/checkpoint work requires explicit later Owner approval. **Phase B may enter design only after this Phase A code decision; Phase B multi-Sim/multi-session/true batch production edits require a fresh, separate Design Gate before implementation.**

This decision becomes formal only after this Detailed Review **and** an append-only entry in `docs/collab/chatgpt/CODEX_INBOX.md` are both published and independently read back.
