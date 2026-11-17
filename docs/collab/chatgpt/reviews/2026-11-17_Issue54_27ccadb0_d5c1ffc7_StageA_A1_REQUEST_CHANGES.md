# Issue #54 / Draft PR #55 — GPT independent Stage A A1 review

Date: 2026-11-17. **Verdict: REQUEST_CHANGES.**

## Exact scope and authority

- Formal implementation Root: `27ccadb051a71adf348ee14206d7ac59e9195d36`.
- Unchanged Cosmos Child/Gitlink: `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`.
- PR #55 is stacked on unmerged #53; base `d36caf0fc35f3a84b739dc8df58ab992eb9f6917`, reviewed #53 implementation `778d1ed8a031429fd857c980fc872d4c85123cd1`.
- PR #55 head observed before this review-only publication: `2624bbc54795e50e3ac238bf0925bcd1b4247b6a`, a documentation/receipt commit, not the implementation target.
- V3 observed: `fe1089fb925d86697bebd9bef18608d9c9eae87b`; server production root remains `875ad79189a4aaa903849b6a5a4cea0eaf62e523`. nav local G2 remains `70eb7b447e65d793b0ebe18b258291ce46f057c1`.
- Scope is A1 code/CPU and real-source contract probes. A2's worker/ACK/recovery/new-source VAE adapter is explicitly not delivered and is **not treated as an unexpected A1 defect**.
- Owner's handoff and later clean `floor_top` / marked `floor_top_w_rbs` naming decisions remain authoritative. No requirement to redo the approved #53 encoder or change its storage format.

## Independent execution

Created a clean detached Root/Child checkout on the authorized server; the production checkouts were not switched or edited. Used the existing interpreter, without creating an environment, installing packages or using the former dependency overlay:

```text
/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin/python
Python 3.13.11; Torch 2.10.0+cu128; pytest 9.0.2; NumPy 2.2.5;
Pillow 12.2.0; MuJoCo 3.3.1; Pandas 2.2.3; PyArrow 21.0.0; Ruff 0.12.7.
```

`CUDA_VISIBLE_DEVICES=''`, fixed-source PYTHONPATH, `PYTHONDONTWRITEBYTECODE=1`; no model/weights/GPU were loaded. Tests used isolated temporary outputs. No server commit/push, training, original cache overwrite, unrelated process stop or data deletion.

| Independent check | Result |
|---|---|
| Original #53 tests | **283/283 PASS**, 0 failures/errors/skips, 10.09 s |
| New Stage A tests | **50/50 PASS**, 0 failures/errors/skips, 1.41 s |
| Producer/marker/viewer regression | **45/45 PASS**, 0 failures/errors/skips, 1.57 s |
| Original approved test identities | Exactly all 283 retained |
| Author-tested source versus fixed checkout | **201/201 hashes match** |
| Source before/after all review execution | **201/201 unchanged**, Root/Child worktrees clean |
| Existing #53 core, original test files and two CLIs | Byte-level Git diff unchanged; new `streaming.py` is separate |
| Ruff new/existing selected rules; 13-file format | PASS |
| JS syntax, variants smoke, actual loadEpisode on synthetic package | PASS |
| New synthetic protocol construction and strict verifier | PASS |
| New independent expected-correctness regressions | **3 FAIL**, reproducing the two finding classes below |
| Real authoritative caption loading | **4/4 named sample calls FAIL** |
| Real GT role calls, one existing sample per 18 tasks | 18 returned BOUND; **semantic completeness is not established**, and two concrete omissions were found |

The three author skips were genuine missing-dependency cases. They execute and pass in the existing server environment. Thus the existing regression result is 378 passing cases, not 375 plus skips. The three reviewer failures are separate and must not be counted as passing tests.

## F1 — P1: the real flat task-table layout is rejected

**Location:** `g2/offline/language_context.py:101–109`, with the failing validation at lines 54–61 and propagation through `atomic_6views_run.py::publish_profile`.

The current target-atomic `meta/tasks.parquet` has:

```text
task_index: int64
__index_level_0__: string   # the authoritative instruction text
```

`load_flat_captions()` converts the table with `to_pylist()` but only normalizes the inverse layout when `task_index` is absent. Because the actual table *does* contain `task_index`, its string index is never mapped to the `task` field required by `resolve_caption_rows()`. The latter sees `text=None` and raises:

```text
ContractError: invalid or duplicate authoritative task table
```

Direct calls to the unmodified production function failed on all four prescribed real samples: CloseBlenderLid/000000, CloseFridge/000502, NavigateKitchen/002104 and PickPlaceDrawerToCounter/005077. Each call requested the valid initial raw frame and the actual `ep_meta.lang`; no renderer or VAE was needed to expose the incompatibility.

The repository-safe reviewer test creates an invented two-row Parquet dataset with the same column layout and reproduces exactly this exception. Existing Stage A caption tests pass dictionaries already containing a `task` key; they do not execute this actual Parquet normalization path.

**Impact:** language-enabled Stage A production cannot publish these real episodes. In the current producer the loader is reached after the expensive spatial stages, so blindly running full production would waste those stages before the same failure.

**Minimum correction:** explicitly support the actual authoritative string-index layout, preserving text byte-for-byte and task IDs. Retain valid alternative supported layouts, reject ambiguous/inconsistent columns and duplicate IDs, and preserve frame/episode identity and `ep_meta.lang` cross-checks. Do not modify the dataset, fall back to `ep_meta.lang` as an unverified replacement, infer task IDs from row order, or weaken authority checks. Add an actual temporary-Parquet regression; use existing PyArrow.

## F2 — P1: BOUND can omit required independent task objects

**Locations:** `g2/offline/task_entities.py:11–12` and `:49–55`; task-table-driven tests at `g2/tests/test_stage_a_contracts.py:89–140` and the blender fixture at `:159–175`.

### F2a: CloseBlenderLid omits the manipulated lid

In the inspected real CloseBlenderLid/000000, the body and lid are separate source instances:

```text
fixture:blender_main_group                 -> body entity
fixture:blender_main_group_auxiliary_main_group -> BlenderLid entity
```

The rule table binds only the Blender fixture. The result is `binding_status=BOUND` with the body only; the separate BlenderLid SG entity is not in `TaskEntitySet.entity_ids`. Enumerating all parts of the body's source instance does not fix a *different source instance*.

The original handoff explicitly calls for binding Blender **and BlenderLid** for this empty-fixture_refs task. The actual task initialization also places a free auxiliary lid next to the blender. The current test puts a synthetic `lid` part under the Blender source and therefore cannot detect this layout.

### F2b: CounterToStove omits the named source container

For real PickPlaceCounterToStove/004540, the instruction specifies taking the object **from a plate** and placing it **in a pan**. The source metadata/SG distinguishes:

```text
object:obj           -> moved item
object:container     -> destination container
object:obj_container -> source plate
```

The current rule includes the first two plus the stove but omits `obj_container`, still returning BOUND. This is a relevant source/reference object, not a distractor. The independent invented fixture reproduces the omission.

**Impact:** enhanced facts and downstream object-driven View selection consume the incomplete `entity_ids`. The missing lid/plate is not described. If an omitted entity has additional associated directions, those directions are not selected on its behalf. The latter is a consequence of the selector's input contract, **not a claim that this review re-rendered these episodes and measured their exact lost directions**.

**Minimum correction:** derive complete required roles from initialization/task semantics, including separately instantiated auxiliary objects and explicit source containers. Preserve exact source/part mapping, ambiguity rejection, all-part handling, and exclusion of actual distractors/initialization-only references. Do not patch specific episode numbers or add all fixtures/object_cfgs indiscriminately. Keep the distinction between a reference counter and an exclusive destination.

Use independently specified expected roles in tests rather than constructing both inputs and expected outputs solely by looping over the implementation's `FIXTURE_RULES/OBJECT_RULES`; that tests self-consistency but cannot reveal omissions in the table itself. Add the two exact reviewer layouts and check role completeness in representative samples for each of the 18 task classes. No embedding/LLM retrieval is needed.

## What passed, and what remains unproven

Code inspection and the independently rerun synthetic/native-unit tests support keeping the current module split and the clean/marked implementation direction:

- clean base is retained; marked output derives from a copy; variants have separate owners and canonical direction identities;
- ARROW_ONLY/REUSE_ALL tests preserve the clean versus marked history;
- renderer member sets are shared with metadata, bidirectional associations and explicit top-variant selection are implemented;
- sealed source and final completion are distinct; A2-pending is not represented as VAE-complete;
- strict old readers and the approved cache core are not rewritten;
- declared new profile, file validation, reference checks, viewer and existing regressions passed.

These are scoped code/CPU/synthetic results, **not real new-profile F27 pixel acceptance**. A full real producer replay was not started after the source-contract blockers were demonstrated; no language-disabled run is substituted for a language-enabled pass. Real-source probes do not imply all 9,126 episodes or all role variants were audited.

A2 pending work (consumer, durable ACK, recovery/backpressure, new-source post-hoc adapter, final VAE publication) stays pending by design. State15, final joint alignment, model integration, full encoding and training remain outside this review.

## Evidence and replay

Canonical server evidence directory:

```text
/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_issue54_a1_review_27ccadb0_20261117/evidence/
```

It contains independent `pr53.log/.xml`, `stage_a.log/.xml`, `related.log/.xml`, source/environment manifests, real-source probe script/results, synthetic protocol outputs, and reviewer RED logs/XML. Original private metadata, images, weights and tensors stay on the server. Only aggregate derived review data and invented reproductions are published under:

`docs/collab/chatgpt/evidence/2026-11-17_issue54_27ccadb0/`.

Recorded server hashes:

- `result_audit.json`: `4360398062240d52e086977d5a6a3b51cd3e787153a19784b9b92321ac8eecc2`
- `real_source_contract_probes.json`: `0dc5d386507b03c9c8cbff590a999a96933fd1fe09a06c4672e28388a24cf715` (server-only)
- `source_before.json`: `0910bb754bd81f8dae588de32852a31707ca3e0b00c0c430769d71904db1d83e`
- `test_review_source_contracts.py`: `860424fa81b6447cb361d7272ff0a365dfef6ef6087b0a3f51ab97f63fd306e0`
- `reviewer_probes.log`: `795bbe0f97da6e5ef0273295198b88a920ef141cb22149a0098cc9ab94bcfa11`

From a checkout of the fixed Root/Child, with the existing environment:

```bash
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD/cosmos-framework:$PWD"
export COSMOS_DEVICE=cpu COSMOS_TRAINING=0 COSMOS_INTERNAL=0
PY=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin/python
$PY -m pytest -q -p no:cacheprovider g2/tests/test_view_vae_*.py \
  g2/tests/test_scene_view_event_index.py g2/tests/test_scene_view_index_package.py \
  g2/tests/test_scene_graph_compact_v3.py
$PY -m pytest -q -p no:cacheprovider g2/tests/test_stage_a_*.py
$PY -m pytest -q -rs -p no:cacheprovider g2/tests/test_atomic_6views_run.py \
  g2/tests/test_robot_pose_marker.py g2/tests/test_viewer_install.py
$PY -m pytest -q -p no:cacheprovider \
  docs/collab/chatgpt/evidence/2026-11-17_issue54_27ccadb0/test_review_source_contracts.py
```

The final command is expected to return three correctness failures on 27ccadb0. Replaying from the following review-only commit is equivalent for implementation files.

## Next Codex delivery and review scope

1. Fix F1 and F2 in the same PR #55 using a new fixed implementation SHA. Preserve prior evidence and the approved #53 core.
2. Retain all original 283 cases, Stage A 50 and related 45; make the three unchanged reviewer assertions GREEN. Add semantic role tests independent of the rule table and Parquet-layout tests.
3. Return exact source diff, commands, raw results, and explicit pending areas. Do not conflate the fixes with broad A2 worker work in the reviewed commit; A2 design may continue without changing this evidence.
4. GPT next performs a narrow review and real-source recheck, then the new-profile representative producer/pixel/metadata gate. Language template and production configuration remain candidate settings until sample acceptance.

**No merge, new environment, data overwrite, full production, state15 or training is authorized by this review.** The following evidence/documentation commit does not replace formal implementation 27ccadb0.
