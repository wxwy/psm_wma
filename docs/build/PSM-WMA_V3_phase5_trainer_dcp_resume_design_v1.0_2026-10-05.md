# PSM-WMA V3 Corrected — Phase 5 Trainer / Optimizer / DCP / Resume Integration Design v1.0

日期：2026-10-05
状态：GPT frozen design authority for Phase5 debug implementation；production promotion仍受 Phase3.5 thresholded REAL_PARITY_PASS 限制。

## 1. 目标

Phase5只把 Phase4 Corrected exact-window Local-TTT 接入 native Cosmos trainer / optimizer / DCP / same-job resume：

```text
Phase3 exact-window cached SFT
  + Phase4 ExactWindowRankPlanner
  + Phase4 ExactWindowSegmentProducer
  + Phase4 GroupedLocalMemoryWindow
      -> ImaginaireTrainer microstep loop
      -> native Cosmos outer loss
      -> generation + Local slow optimizer
      -> scaler-aware optimizer success
      -> candidate Local live publish
      -> DCP model/optim/scheduler/trainer/dataloader(Local runtime)
      -> exact same-job resume
```

Phase5不做：
- online inference/server
- RoboCasa simulator/eval/SR
- full target-atomic cache rebuild
- Phase6 closed-loop behavior
- production promotion while Phase3.5 thresholded Gate remains open

## 2. Parent authority

必须继承：
- Corrected V3 detailed design v3.0
- Phase1A/1B/2/3 closed contracts
- Phase4 Local-TTT integration design v1.2
- Phase4 debug implementation tree `474ce9fd6ce848890a080ae9e2c568a0e2e0fb63` as interface reference
- Phase4 debug closure review `docs/collab/chatgpt/reviews/2026-10-05_V3_phase4_debug_scratch_closure_474ce9f.md`
- current native DCP implementation `checkpoint/dcp.py`
- historical H3-C/H3-D/H3-F only as donor, not authority

Phase5 production root/child remain unchanged until later promotion Gate.

## 3. Frozen data / Local geometry

Canonical policy/data:
- corpus authority = exact_window_v1 cache
- source authority = matching flat LeRobot v3 source
- policy video_latent = [5,48,H,W]
- raw action = 15D
- state = 15D
- H_pred = 16
- observation/current+future window frames = 17
- max model action width after transform = 64
- cached_latent_required = True
- online VAE fallback = False

Local:
- T = runtime.core.ttt_tbptt_steps; default16; T32 and other positive tested values remain valid
- B_stream = planner.b_stream; default8
- active_ga = planner.active_ga; default2
- K_local = runtime actual value; default formal profile may remain K4, K1 is legal and uses exact-zero slot-query init
- T/B/GA/K are separate axes; checkpoint profile must bind actual values, not historical constants.

## 4. KEEP / ADAPT / RETIRE

### 4.1 KEEP

Keep current concepts and upstream code:
- `ImaginaireTrainer.train` outer loop
- `GroupedLocalMemoryTrainer` subclass concept
- native `model_ddp.training_step(...,_local_memory_prefixes=...)`
- callback order around forward/backward/optimizer/zero-grad
- `GroupedLocalMemoryWindow` candidate/live transaction from Phase4
- scaler-aware optimizer success concept
- scheduler step only after optimizer success
- `checkpoint/dcp.py` model/optim/scheduler/trainer/dataloader structure
- trainer DCP state: grad_scaler + iteration + per-rank RNG
- dataloader rank-pkl callback seam
- strict same-job resume versus external warm-start distinction
- existing FSDP `register_fsdp_forward_method(model,"scan_local_memory")`
- generation + Local slow trainable profile; reasoner frozen

`checkpoint/dcp.py` and `parallelize_vfm_network.py` should require zero Phase5 diff unless a separately reviewed blocker proves otherwise.

### 4.2 ADAPT

Adapt:
- trainer planner type -> `ExactWindowRankPlanner`
- trainer producer -> `ExactWindowSegmentProducer`
- materialization -> exact requests via producer.produce
- grouped trainer active_ga from planner/config, not fixed2
- native collate batch size dynamic 1..B_stream, not hard max8
- resume frontier type -> `ExactWindowCatalogFrontier`
- resume slot count -> planner.b_stream
- resume profile H_pred16 / frames17, not chunk32 / frames33
- resume identity fields -> episode.uid / task_class / source_digest
- config digest -> Corrected cache/source/policy/Local geometry
- trigger loader microsteps -> max_iter * active_ga
- formal observer expected forward/backward count -> plan/request geometry, not constant32
- launcher paths -> corrected cache/source/base-DCP route
- optimizer inventory -> actual allowed-name set; Local count derived from model, not hard-coded 165312 when K changes

### 4.3 RETIRE from corrected active route

Do not use:
- `robocasa_grouped_segment.RankLocalGroupedPlanner`
- `StageARoboCasaEpisodeBinder`
- `materialize_member` old B1/Stage-A route
- historical `CatalogFrontier`
- chunk32 / consumer33 resume profile
- fixed 8-slot resume assumptions
- fixed GA2 trainer code
- B1 cache probe authority
- Stage-A checkpoint/config as corrected data authority
- old H3-E catalog count/digest assumptions

Historical files can remain for provenance/tests.

## 5. Corrected trainer binding

`GroupedLocalMemoryTrainer.bind_grouped_stream` should accept:

```python
planner: ExactWindowRankPlanner
producer: ExactWindowSegmentProducer
config_digest: str
```

Hard checks:
- producer.catalog is planner.catalog
- planner.catalog.wrapped_sft raw dataset is Phase3 `RoboCasaExactWindowCachedDataset`
- planner.catalog T == model Local runtime T before training
- planner.active_ga == config.trainer.grad_accum_iter
- planner.b_stream > 0
- no pre-existing grouped binding
- exactly one DCP dataloader state callback authority

Do not bind a per-episode callback/binder.

## 6. Dynamic GA on upstream train loop

Upstream `ImaginaireTrainer.train` already:
- initializes `grad_accum_iter=0`
- calls subclass training_step for every fetched trigger
- increments optimizer iteration only when returned `grad_accum_iter==0`
- resume raw fetch count = iteration * config.trainer.grad_accum_iter when CP=1

Therefore corrected trainer must use:

```text
config.trainer.grad_accum_iter = planner.active_ga
```

For microstep g:
- require `0 <= g < active_ga`
- g=0 -> `window.begin()`
- g>0 -> existing pending window required
- run plan.members[g]
- if g < active_ga-1: return next g+1, no optimizer, no live publish
- if g == active_ga-1: optimizer transaction; success -> return 0

No hardcoded tuple (0,1), no hardcoded return 1.

Formal Phase5 profile requires context-parallel size=1. If CP is enabled, fail closed pending a separate design because trigger counting/resume semantics would change.

## 7. Corrected segment materialization

For one member:

```python
segments = tuple(producer.produce(request) for request in window.plan.members[g])
```

Requirements:
- length == planner.b_stream
- request/segment slot order unchanged
- no old binder/catalog imports
- no video decode or online VAE
- payload still carries Phase3 `cached_latent_required=True`

## 8. Native same-index batch

`collate_grouped_native_batch`:
- accepts any non-empty tuple of payload dicts
- no historical upper bound 8
- grouped window already guarantees current n_i <= B_stream
- reuse `custom_collate_fn` / `JointDataLoader` native packing ABI
- must preserve `video_latent` packed nesting
- no duplicate transform/collate path

Formal tests:
- n=1,3,8
- terminal n_i<B
- cached video_latent ABI
- raw action transformed 17x64 with raw authority 17x15 retained as applicable

## 9. Optimizer inventory

Allowed trainables are exactly:

Generation:
- moe_gen
- time_embedder
- vae2llm
- llm2vae
- action2llm
- llm2action
- action_modality_embed

Local:
- local_memory_runtime.encoder.*
- local_memory_runtime.core.*
- local_memory2llm.*
- local_memory_modality_embed

Reasoner:
- frozen
- zero selected reasoner parameters

No VAE/tokenizer parameters.

Inventory validation:
1. build expected names from actual model named_parameters using allowed prefixes/keys;
2. selected optimizer parameter IDs must map exactly to expected names;
3. every expected parameter requires_grad=True;
4. every non-expected parameter requires_grad=False;
5. Local parameter total is reported from actual model, not universally hard-coded;
6. canonical K4 formal run may separately assert its known count, but K1/K8/K16 must remain legal profiles.

W0 stays selected even when an all-continuation optimizer window produces W0.grad=None. Do not synthesize zero W0 gradients; this preserves AdamW/weight-decay semantics frozen in Phase4.

## 10. Gradient safety

Before optimizer:
- unscale if scaler enabled
- all present selected gradients must be finite and dense
- at least one selected gradient must be present globally
- do not require every selected parameter to have grad on every window
- all-continuation W0.grad=None is legal
- GPU readiness must separately prove representative host + Local gradients on a fresh-containing window

Distributed nonfinite flag is all-reduced across ranks before optimizer.

## 11. Optimizer / scaler / scheduler transaction

Last GA member only:

1. all outer backward complete into candidate Local state
2. scaler.unscale_(optimizer) if enabled
3. finite-gradient check
4. callbacks/model pre-optimizer hooks
5. finite-gradient check again
6. call `window.finish(optimizer_step_success)`

`optimizer_step_success`:
- capture old scaler scale
- `grad_scaler.step(optimizer)`
- `grad_scaler.update()`
- if enabled and new scale < old scale -> optimizer considered skipped:
  - do not scheduler.step
  - return False
- otherwise scheduler.step
- return True

`GroupedLocalMemoryWindow.finish` publishes candidate live only on True.

On scaler skip / optimizer exception:
- candidate discarded
- scheduler not advanced on scale skip
- live frontier/sidecar/scheduler unchanged
- training step raises/fails closed
- no checkpoint at this failed boundary

## 12. Zero-grad and iteration boundary

After successful live publish:
- set grouped completed iteration = iteration + 1
- run zero-grad hooks
- optimizer.zero_grad(set_to_none=True)
- return grad_accum_iter=0
- upstream trainer increments iteration
- checkpoint may then save iteration N

Thus Local snapshot iteration must equal the DCP trainer iteration after the successful optimizer step.

## 13. DCP base checkpointer

KEEP `checkpoint/dcp.py` unchanged.

One DCP checkpoint already contains:
- model
- optim
- scheduler
- trainer:
  - grad_scaler
  - iteration
  - per-rank RNG
- dataloader:
  - rank-local grouped Local runtime state via callback

Same-job strict resume must require all five component groups relevant to current config.

Fresh warm-start from official Cosmos3-Edge-Policy-DROID-dcp:
- `load_training_state=False`
- load model weights only
- skip absent Local keys as explicitly configured
- Local slow params start from current initialized Phase4 model
- optimizer/scheduler/scaler/Local live state start fresh

Same-job resume:
- `load_training_state=True`
- no Local key skip
- model + optimizer + scheduler + scaler/RNG/iteration + rank Local dataloader state all restored

## 14. New Local checkpoint schema

Supersede historical:

`psm_v3_h3d_grouped_local_v1`

with corrected incompatible format, e.g.:

`psm_v3_corrected_grouped_local_v2`

Never silently accept v1.

Snapshot only when:
- `window.plan is None`
- no candidate pending
- successful optimizer/live publication complete
- iteration >= 1 for normal save (zero-step remains prohibited in this profile)

State fields:

```text
format
iteration
cache_manifest_sha256
cache_corpus_digest
source_binding_digest
config_digest
profile
frontier
scheduler
sidecar
```

Absolute machine paths are excluded from semantic identity.

## 15. Checkpoint profile

Profile must bind actual runtime values:

- rank
- world_size
- seed
- b_stream
- active_ga
- visual_dim=96
- action_dim=15
- evidence_dim
- ttt_dim
- fast_hidden_dim
- local_dim
- k_local
- T
- inner_lr
- max model action width=64
- H_pred=16
- consumer frames=17

Do not store historical chunk32/frames33.

## 16. Corrected frontier / slots

Resume frontier type:
- `ExactWindowCatalogFrontier`

Slot count:
- exactly `planner.b_stream`

Expected slot IDs:
```python
rank * b_stream + local_slot
```

not fixed 8.

For every committed scheduler identity:
- exact slot ID
- episode_id == episode.uid
- category == episode.task_class
- source_digest == episode.source_digest
- segment_id continuity with slot.next_segment_id
- cursor continuity

Terminal slot:
- frontier slot uid=None / binding_epoch=None / cursor=0
- committed identity training_stream_end=True
- no saved fast state
- identity cursor == episode.segment_count-1

Continuation slot:
- uid resolves in planner.by_uid
- committed identity is non-terminal
- slot.cursor == identity.cursor+1
- saved fast state required

## 17. Sidecar state

For each continuation slot, save:
- exact SegmentIdentity
- exact SegmentProvenance
- four fast-state tensors

Saved tensors:
- CPU
- fp32
- finite
- ordinary Tensor, not Parameter
- grad_fn=None
- detached clone

On restore:
- validate all schema/identity/provenance/tensor fields before touching live
- move clone to Local core device
- validate state shape for batch1
- build candidate sidecar/scheduler/frontier entirely off-live
- single final `window._live = candidate` reference assignment

Any validation failure leaves prior live object byte/identity unchanged.

## 18. Planner validation during restore

Do not require historical `CatalogFrontier`.

Use corrected planner validation:
- expose or reuse a non-mutating ExactWindow frontier validator
- verify current frontier rank/capacity/uid/cursor/binding epoch
- deterministic queue identity remains reconstructible from seed/epoch/task/rank
- no machine path dependency

Avoid invoking a mutating/future-consuming planner action merely to validate the checkpoint.

A minimal public `validate_frontier` wrapper may be added to Phase4 exact-window planner in Phase5 if needed; it must not change planning semantics.

## 19. Config digest

Phase5 config_digest must include semantic authority at least:

- cache manifest SHA256
- cache corpus digest
- source binding digest
- fixed Edge policy/model identity
- raw15 / state15 / H_pred16
- max action width64
- T
- B_stream
- active_ga
- K_local
- ttt_dim
- fast_hidden_dim
- local_dim
- inner_lr
- optimizer allowed key profile
- optimizer LR / action LR multiplier / weight decay
- mesh/world-size profile
- scheduler/warmup/save cadence for the selected run profile

No absolute cache/source/output path in semantic digest.

## 20. Trigger loader

Adapt historical `GroupedTriggerLoader`:

```python
GroupedTriggerLoader(max_iter, active_ga)
```

- total microsteps = max_iter * active_ga
- `set_start_iteration(fetched)` range uses same total
- with CP=1, upstream resume fetch count = optimizer_iteration * active_ga
- every trigger payload may remain empty because exact samples come from producer
- no dataloader RGB/source decode

Formal tests:
- GA1/2/3 lengths and resume offsets
- resume at optimizer iteration N starts trigger N*active_ga
- no replay of completed member

## 21. Formal observer

Retire constant expectation fwd=32/bwd=32.

Expected native calls per grouped plan:

```text
sum over member:
    max(request.valid_count for request in member)
```

because each valid segment is prefix-valid and same-index callback occurs once for each index with >=1 active row.

Observer checks:
- actual forward == expected
- actual backward == expected
- pre_optimizer == 1
- post_commit == 1
- outer weighted objective finite
- Local telemetry sum/count/max finite
- gradient category metrics
- step wall / memory
- frontier epoch

Default full B8/GA2/T16 still yields 32 calls, but terminal windows and T32 are not forced to that number.

## 22. Corrected launcher / config

Historical H3F launcher is donor only.

Corrected launcher must use:
- exact flat source root
- exact_window cache root
- official base checkpoint
- current V3 child/root lock
- T/B/GA/K runtime values
- save_iter / output root

Retire active authority requirements for:
- STAGE_A_CHECKPOINT_PATH
- STAGE_A_CONFIG_PATH
- ROBOCASA_LATENT_CACHE_PROBE
- historical Stage-A binder/catalog

Canonical defaults:
- T=16
- B=8
- GA=2
- K=4
- inner_lr=0.1
- raw15/state15/H16

T/B/GA/K actual values are validated positive and bound into config digest/profile; experiments may change them if the model/runtime supports them.

Formal production GPU profile may remain 8x H100 dp_shard8. Current 24GB 4090 server is CPU/static/debug evidence only for Phase5.

## 23. FSDP

`parallelize_vfm_network.py` remains unchanged.

Must retain:
```python
register_fsdp_forward_method(model, "scan_local_memory")
```

GPU readiness must prove:
- model-owned scan materializes Local slow params under FSDP
- mixed fresh/continuation batch works
- all-continuation does not touch W0
- optimizer sees intended generation + Local parameters after parallelization

No second scan method / no second registration.

## 24. Implementation files

Phase5 scratch implementation may MODIFY:
- `cosmos_framework/trainer/local_memory_grouped.py`
- `cosmos_framework/trainer/local_memory_grouped_test.py`
- `cosmos_framework/trainer/local_memory_grouped_resume.py`
- `cosmos_framework/trainer/local_memory_grouped_resume_test.py`
- corrected Phase5 launcher/example (new preferred over mutating historical H3F)
- optional minimal `robocasa_exact_window_local.py` public frontier validator only if required

Should remain unchanged:
- `checkpoint/dcp.py`
- `parallelize_vfm_network.py`
- Phase1A/1B/2/3 datasets
- memory_prefix / attention
- inference/server/eval

## 25. CPU/static acceptance

At minimum:

Trainer:
1. active_ga=1/2/3 mapped exactly to grad_accum_iter
2. optimizer runs only last member
3. scheduler once per successful optimizer
4. scaler skip -> no scheduler, no Local publish
5. optimizer exception -> no Local publish
6. later-GA failure -> no Local publish
7. dynamic B native batch 1/3/8
8. exact producer/planner binding identity
9. no historical grouped imports
10. corrected cached-latent payload reaches native collate

Optimizer:
11. selected names exactly generation+Local
12. W0/encoder/KQV/slot_queries/bridge included
13. reasoner excluded/frozen
14. K-dependent Local count handled
15. all-continuation W0.grad=None accepted
16. nonfinite present grad fails before optimizer

DCP:
17. corrected format v2
18. dynamic B/GA/T/K profile
19. H16/frames17 profile
20. ExactWindowCatalogFrontier type
21. dynamic slot IDs
22. terminal no-fast rule
23. continuation fast required
24. source/corpus/config mismatch fail
25. fp16/nan/Parameter/grad_fn fast fail
26. two-phase restore zero live mutation on every failure
27. uninterrupted vs save/restore next plan/loss/grad parity
28. rank-local dataloader callback save/load
29. same-job missing rank pkl fail
30. external warm-start does not require Local pkl
31. zero-step checkpoint prohibited

Trigger/config:
32. GA1/2/3 trigger length/offset
33. config digest changes on semantic T/B/GA/K/cache/source changes
34. machine path relocation does not change semantic digest
35. H_pred16/raw15 contract
36. checkpoint fresh vs same-job resume semantics

Regression:
37. Phase4 focused suite
38. native joint prefix gradient tests
39. Phase1A/1B/2/3 tests
40. existing DCP tests relevant to dataloader wrapper

Static:
- Ruff check
- Ruff format --check
- py_compile
- git diff --check
- forbidden-file diff check

## 26. GPU readiness Gate

Run later on the training server, not current 24GB debug host.

Readiness before formal training:
- exact root/child candidate lock
- 8x H100 expected formal profile, or separately frozen replacement
- official base DCP fresh load
- corrected exact cache/source authority
- no online VAE encode on cached path
- finite native outer loss
- generation + Local gradient inventory
- two GA members/default profile
- exactly one optimizer/scheduler step
- candidate publish only after optimizer success
- DCP saved with model/optim/scheduler/trainer/dataloader per rank
- kill/restart same-job resumes next optimizer iteration
- resumed next plan/fast state/loss finite and continuous
- scaler state/RNG/optimizer/scheduler restored
- no missing/unexpected Local model keys on same-job resume

Recommended staged GPU Gate:
A. 1 optimizer iteration fresh
B. 3 optimizer iterations + save
C. kill + resume to 5
D. readiness10
E. only then formal longer run

## 27. Governance

Current authorization after this design freeze:
- cx may implement Phase5 only in scratch/debug worktree after GPT review/freeze
- ds may run CPU/static only after fresh implementation review
- no production child/root Gitlink promotion
- no formal GPU training until later Gate
- Phase3.5 thresholded production Gate remains separate and open

Phase5 design closure does not imply Phase3.5 REAL_PARITY_PASS.
