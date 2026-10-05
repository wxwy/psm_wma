# PSM-WMA V3 Corrected — Phase 6 Online Inference / Simulator / Evaluation Design v1.1

日期：2026-10-05  
状态：GPT revised design authority candidate；docs-only。v1.1 supersedes v1.0 before implementation authorization。Phase6 implementation、production promotion、GPU/simulator execution 均未由本文自动授权。

## 1. 目标

Phase6 将 Corrected V3 的 episode-persistent Local-TTT 从已关闭的 training/debug contracts 接到 online RoboCasa action path：

```text
actual obs_t
  -> official left|wrist composite
  -> same spatial preprocessing
  -> T_pixel=1 Wan Encode1 -> z_t
  -> V2 visual96
  + completed canonical executed raw15 history
  -> OnlineLocalMemory fast update
  -> Local prefix
  -> official policy generation
  -> official raw15 decoder
  -> env12
  -> env.step succeeds
  -> only then publish completed evidence
  -> next Local update / next replan
```

本文只冻结 online/server/client/eval 的 correctness contract。  
不改变 Phase1A/1B/2/3/4/5 数据、trainer、DCP、FSDP、attention 或 optimizer contracts。

## 2. Parent authority

Phase6 必须继承：

- `PSM-WMA_V3_Local_TTT_on_latest_Cosmos_RoboCasa_detailed_design_v3.0_2026-10-04.md` §5–10、§19–26、§30、§42–50；
- `PSM-WMA_V3_corrected_implementation_mapping_v0.1_2026-10-04.md`；
- Phase2 raw15/state15/H_pred16 closure；
- Phase3 cached-latent / Wan contract；
- Phase4 debug implementation/closure：Local visual96、model-owned scan、fast-state semantics；
- Phase5 debug scratch `afb9ca8d9f8ec080518a838f56a681073eb4b495` 仅作 corrected Local runtime/model interface reference；
- official RoboCasa server/state/action decoder/simulator behavior from production child source audit。

Production root/child 在本文冻结期间保持：

- root before Phase6 design：`ecf7723a9df2aab782f792fd0fd6fa065b6df807`
- child/Gitlink：`b673ceda5a9ff058abb31224b7006f2d87771ad2`

Phase3.5 thresholded production parity 仍 OPEN。本文不构成 production promotion waiver。

## 3. Source-audit findings

### 3.1 KEEP

保留：

1. `inference/local_memory_online.py`
   - per-session state；
   - prepare / commit / abort；
   - exact replay fingerprint；
   - reset；
   - model-owned `scan_local_memory`；
   - inference-only fast state，slow params read-only。

2. `scripts/action_policy_server_robocasa.py`
   - official prompt/state/action processing；
   - serial `/predict`；
   - server model lock；
   - Local prepare -> generation -> commit / exception abort transaction；
   - `_local_memory_prefixes` action path；
   - required-mode batch inference rejection，第一 Gate 保持 serial。

3. simulator：
   - `closed_loop_eval.compose(obs)` 的 `left_wrist`：
     `agentview_left | wrist`，upright，256x512；
   - official rollout/success/video logic；
   - state token；
   - server HTTP transport。

4. official `decode_15d_to_env12` semantics：
   - rot6d Gram-Schmidt；
   - mode threshold；
   - base clip / arm-only zero；
   - gripper clip；
   - env12 layout。

### 3.2 RETIRE from Corrected active route

下列仅保留历史文件，不得被 corrected Phase6 active modules import/use：

- `inference/robocasa_causal_evidence.py`
- `model/generator/mot/robocasa_latent_evidence.py`
- `RoboCasaCausalEvidenceStream`
- episode-long causal Wan encoder state
- separate left/wrist VAE
- B1 endpoint/floor mapping
- B1 `mean48 + RMS48` visual96
- wire version `b1_causal_endpoint_visual96_executed_action15_v5`
- format `robocasa_dual_camera_rgb_raw15_v2`

### 3.3 Current implementation blockers

**BLOCKER A — visual ABI wrong**

Current `robocasa_local_memory_policy.py` explicitly implements frozen B1 dual-camera causal-endpoint visual evidence.  
Corrected route requires a single completed pre-action `left|wrist` composite and independent `T_pixel=1` Encode1.

**BLOCKER B — evidence chronology wrong**

Current `closed_loop_eval.run_policy` invokes `record_executed(...)` **before** `env.step(env_action)`.

Corrected chronology requires:

```text
retain pre-action composite
decode action
env.step returns successfully
THEN mark evidence completed
```

If `env.step` raises, Local consumer frontier must not advance.

**BLOCKER C — executed raw15 authority wrong**

Current evaluator records policy output `a` directly.  
Official decoder may canonicalize it by rot6d orthogonalization、mode threshold、base clipping/zero、gripper clipping.

Therefore pre-decoder prediction cannot be labeled `executed_raw15`.

**BLOCKER D — Encode1 parity not yet proved**

Existing Phase3.5 observational evidence proves offline cache Encode17(window) == online current Wan Encode17(window) for one task / three windows.

It does **not** prove:

```text
offline Z_t[0]
==
server-side Encode1(current composite)
```

Phase6 correctness depends on this separate parity.

**BLOCKER E — R/T coupling risk**

Current `OnlineLocalMemory.prepare` passes all newly completed rows in one scan.  
If evidence count exceeds `ttt_tbptt_steps`, core scan can reject it.

Corrected contract states H_pred、R、T are independent.

## 4. Corrected wire contract

New active wire identifiers must be incompatible with B1, for example：

```text
evidence_version = "corrected_composite_current_executed_raw15_v1"
evidence_format  = "robocasa_composite_rgb_canonical_raw15_v1"
```

Request `local_memory`：

```text
session_id
episode_id
consumer_step
reset
image_size              # must equal outer policy request image_size
preprocess_profile      # fixed corrected left_wrist spatial contract id
evidence = [
  {
    source_step,
    composite_image,       # pre-action left|wrist PNG
    executed_action,       # canonical post-decoder raw15
  },
  ...
]
```

Hard rules：

- one composite image per completed action；
- no separate left/wrist fields in corrected wire；
- no z/future latent sent by simulator；
- `image_size` and `preprocess_profile` are part of request/replay identity；
- one session may not silently change image_size/preprocessing profile；
- client has no Wan VAE dependency；
- source_steps contiguous and exactly-once；
- same frontier + identical bytes/actions = replay；
- same frontier + changed bytes/actions = fail-closed；
- no unbounded episode RGB history；only unacknowledged evidence plus server replay witness。

## 5. Single composite visual authority

Simulator-side visual source is exactly：

```python
compose(obs) == upright(agentview_left) | upright(wrist)
```

shape normally `[256,512,3]`.

Client records this same composite used for Policy at a replan step.

For intermediate executed actions within a policy chunk，retain the pre-action composite from current simulator observation before that `env.step`.

No Phase6 code may reconstruct corrected evidence by independently sending/combining left/wrist on server.

## 6. Shared spatial preprocessing

Phase6 must not create a second resize/pad implementation.

Extract/expose a minimal shared helper from current server spatial preprocessing，conceptually：

```text
prepare_robocasa_composite_frame(
    composite_uint8 [3,H,W],
    image_size
)
-> {
     source_uint8,
     padded_single_frame [3,1,H_pad,W_pad],
     padded_image_size,
   }
```

Both paths call the same helper：

1. Policy current input：
   - take prepared single frame；
   - repeat into current official policy temporal placeholder as required by existing sampler；
   - preserve prompt/sequence-plan semantics。

2. Local completed evidence：
   - take prepared single frame once；
   - no temporal repeat before Local VAE encode。

Tests must prove Policy frame0 and Local single-frame tensor are byte-identical spatially before temporal handling。

Because current Policy builds the temporal placeholder by repeating the current image before spatial padding, the extracted helper must also prove:

```text
repeat(current, T) -> existing spatial pad
==
shared single-frame spatial pad -> repeat(T)
```

for Policy frame content and image_size metadata. Any non-equivalence blocks refactor。

## 7. Corrected Encode1 helper

Add a corrected current-composite visual helper in project inference layer，not B1 modules。

Input：

```text
prepared uint8 [3,1,H_pad,W_pad]
```

Use loaded policy Wan tokenizer and the same normalization authority as current Cosmos vision encoding。

Output：

```text
z_t: fp32 [48,H_z,W_z]
visual96: fp32 [96]
```

where：

```python
visual96 = robocasa_current_latent_to_visual96(z_t)
```

The Phase4 helper/formula is the only Local visual96 formula。

Requirements：

- `T_pixel=1`；
- normal full encode，no retained causal encoder state；
- no streaming endpoint；
- no future RGB；
- no B1 mean/RMS；
- finite fp32 output；
- tokenizer contract matches training/cache authority；
- slow/model parameters read-only。

Current Wan T=1 path is a one-frame causal prime and yields one latent frame；Phase6 still requires real numerical parity before runtime acceptance。

## 8. Encode1 parity Gate

Before Phase6 runtime/simulator acceptance，prove on matching real RGB：

```text
cache exact-window Z_t[0]
vs
server-side spatial preprocessing + Wan Encode1(current RGB)
```

Compare the three-way witness：

```text
A = cache exact-window actual Z_t[0]
B = independent Encode1(current composite)
C = first latent from tokenizer encode of the server's repeated-current Policy visual input
```

Require A/B/C to share spatial preprocessing identity. C is obtained in a probe/helper; it does not require exposing an internal model callback。

Compare at least：

- A vs B padded z_t；
- B vs C first latent；
- A vs C first latent；
- post-native crop if Policy path crops；
- Local visual96 for A/B/C。

Metrics：

- exact_equal；
- max_abs；
- mean_abs；
- RMSE；
- finite；
- geometry。

Before the first real run, freeze the numerical acceptance threshold from an observational pass; exact equality may be accepted if observed, but must not be assumed from causality alone。

Current debug corpus may be used for bounded one-task observational scratch validation。

It must be reported separately from Phase3.5 production thresholded Gate；do not claim Phase3.5 `REAL_PARITY_PASS` from Phase6 debug evidence。

## 9. Policy current-z reuse

Correctness path does **not** require exposing Policy internal current z。

Default：

```text
completed pre-action composite
-> shared spatial preprocessing
-> independent Encode1
-> visual96
```

A policy-current-z callback is optional optimization only after proving same composite identity、geometry、z_t、Local prefix and action parity。

Phase6 v1 implementation should not add that callback unless separately reviewed。

## 10. Canonical executed raw15

Add one project helper around official decoder，conceptually：

```text
canonicalize_raw15_for_env(predicted_raw15, gripper_flip)
  -> submitted_env12
  -> executed_raw15_canonical
```

First output must be exactly existing official decoder result。

`executed_raw15_canonical` must re-decode to exact same submitted env12 under same decoder semantics。

Canonical fields derive from submitted command：

- base4 = submitted env base command after clipping/zeroing；
- mode = exact thresholded arm/base mode；
- EEF translation = submitted EEF translation；
- EEF rotation = submitted rotvec -> matrix -> canonical rot6d using same first-two-column convention；
- gripper = value whose decoder reproduces submitted gripper under same flip setting。

Hard test：

```text
decode_15d_to_env12(executed_raw15_canonical, flip)
==
submitted_env12
```

within frozen numerical tolerance for valid rotations、non-orthogonal predicted rot6d、mode±、base overshoot、gripper overshoot、arm-only base zero。

Do not infer executed action from post-step physical robot pose。

Log predicted_raw15、submitted_env12、executed_raw15_canonical；only the last is Local action evidence。

## 11. Simulator transaction chronology

For every actually executed action：

```text
pre_obs = obs
pre_composite = compose(pre_obs)
predicted_raw15 = queue.pop(0)
submitted_env12, executed_raw15 = canonicalize(...)
next_obs = env.step(submitted_env12)   # must return successfully

# only now
client.record_completed(
    pre_composite,
    executed_raw15
)
obs = next_obs
```

If decoder fails or `env.step` raises：

- no completed evidence；
- no consumer_step increment；
- no evidence sent at next request；
- rollout follows existing error handling。

Success/done after successful step does not invalidate that action：if env.step returned，that action is completed evidence。

Predicted-but-unexecuted chunk tail is never evidence。

## 12. Client state machine

Keep session_id、episode_id、consumer_step、first-request/reset、unacknowledged evidence list、exact acknowledgement。

Adapt row schema to composite+canonical raw15。

Required behavior：

- begin -> step0 / reset=True / empty evidence；
- each successful step appends exactly one row and increments frontier；
- payload sends only unacknowledged completed rows；
- acknowledge exact session/episode/frontier then clears pending rows；
- lost response may resend same bytes/frontier；
- end returns session for explicit server reset；
- reusing slot before end rejected。

No VAE import in client module。

## 13. Server Local adapter

Required mode additionally mandates model-owned Local scan:
- corrected adapter must pass `service.model.net.scan_local_memory`；
- if unavailable, fail closed；
- do not use `OnlineLocalMemory`'s direct-core fallback in required Corrected RoboCasa；
- FSDP-registered method requirement remains inherited from Phase4。

Keep outer transaction：

```text
prepare corrected evidence
-> Local candidate update
-> policy generation with candidate prefix
-> generation/output validation
-> commit Local state
exception -> abort
```

Replace B1 visual stream with corrected composite Encode1。

Server validates outer request `image_size` equals Local payload `image_size` and binds the preprocessing profile for the session. Replay digest includes both fields。

Server per session stores only：

- committed OnlineLocalMemory record；
- last committed replay wire fingerprint；
- optionally last materialized visual96/actions for exact lost-response replay；
- no episode causal VAE state；
- no pending left/wrist tail。

Status reports：

- session_id；
- episode_id；
- consumer_step；
- prefix_present；
- replay；
- encoded_steps（0 on replay；N only for newly materialized completed frames）；
- adapted_steps；
- inner_loss_mean；
- fast_state_norm；
- fast_update_norm。

Remove B1-only `visual_endpoint_step` / `visual_tail_frames` and B1 visual description。

## 14. R independent from T

Runtime evaluator constraint：

```text
1 <= R <= H_pred
H_pred = 16 current profile
```

Do not validate R against T。

Online evidence N may exceed scan max T；process in chronological chunks：

```text
for chunk in evidence.split(max_size=T):
    model-owned scan(chunk, state_in=current_state, create_graph=False)
    detach candidate -> current_state
```

No reset between chunks。

Final prefix must equal scalar per-step reference。

CPU tests：R=1/4/8/16 with T16；synthetic N>T (e.g. N20/T8)；split-vs-one-by-one token/final-state/telemetry parity。

## 15. Episode reset and isolation

Fresh episode：

- first policy request no evidence；
- prefix absent；
- W0 lazy until first completed evidence update。

Episode end：

- evaluator explicit reset in finally；
- server rejects reset during pending generation；
- after reset no fast state/token/replay witness。

Episode change without reset fails。No state crosses episodes or simulator slots。

## 16. Replay semantics

Lost response replay requires identical session、episode、consumer_step、source steps、composite bytes、canonical raw15。

Server must not run Wan Encode1 or Local update again；reuse committed/materialized result，mark replay。

Same frontier but any changed bytes/actions fails。

## 17. Serial first Gate

Required Local-TTT v1 supports only serial `/predict`。

`/predict_batch` with Local required remains fail-closed。

Online multi-session batching is deferred。

## 18. Inference memory bounds

Client stores only unacknowledged completed evidence。

Server stores bounded sessions、fast state/token、bounded replay witness；no episode RGB history、no causal VAE cache。

Telemetry must allow bounded-memory soak verification。

## 19. Off-mode regression

When `local_memory_mode=off`：

- Local payload rejected as before；
- policy preprocessing/generation/action output equivalent to pre-Phase6；
- Local Encode1 helper not called；
- batch inference remains available。

## 20. Evaluation harness

After corrected server/client closure，adapt root screening wrapper。

Keep persistent server/GPU、deterministic queue、fixed seed、MP4、per-task JSON、aggregate summary、resume by terminal result。

Per task/episode log at least：

- success；
- done_steps；
- replan count；
- prefix_present；
- adapted_steps；
- fast_state_norm；
- inner_loss_mean；
- inference latency；
- error；
- predicted/submitted/canonical-action diagnostic counters。

Resolved config logs independent H_pred、R、T。

## 21. Phase6 scratch parent and implementation scope

Implementation must start from a clean scratch descendant of:

`afb9ca8d9f8ec080518a838f56a681073eb4b495`

so Phase4/5 corrected interfaces are present. It must not start by changing production child `b673ceda...` or root Gitlink。

The scratch parent SHA and dirty-state check are part of Phase6 implementation evidence。

### 21.1 Allowed scope

Only after formal design review may cx modify scratch based on corrected Phase4/5 interfaces。

Allowed：

- `cosmos_framework/inference/local_memory_online.py` — only sequential chunking/telemetry needed by corrected path；
- `cosmos_framework/inference/robocasa_local_memory_policy.py`；
- `cosmos_framework/inference/robocasa_local_memory_contract.py`；
- new corrected current-composite visual helper in inference layer；
- inference tests；
- `cosmos_framework/scripts/action_policy_server_robocasa.py` — minimal shared spatial preprocessing/helper seam and adapter wiring；
- `cosmos_framework/simulation/robocasa/local_memory_client.py`；
- `cosmos_framework/simulation/robocasa/eval_utils.py` — canonical decoder wrapper；
- `cosmos_framework/simulation/robocasa/closed_loop_eval.py`；
- simulator/client tests；
- corrected root eval wrapper/tests if needed。

Should remain diff-empty：

- Phase1A/1B/2/3 datasets；
- `checkpoint/dcp.py`；
- trainer/resume/optimizer；
- `parallelize_vfm_network.py`；
- attention；
- `memory_prefix.py`；
- Phase4 Local math unless separately reviewed blocker appears。

Historical B1 files remain but corrected active modules/tests must not import them。

## 22. Phase6A CPU/static acceptance

At minimum：

1. corrected wire rejects old B1 version/format；
2. client carries one composite，not two camera fields；
3. client has no Wan import；
3a. image_size/preprocess_profile bound to session/replay identity；
3b. changing image_size/profile mid-session fails；
4. cold S0 no prefix/evidence；
5. source steps contiguous/exactly once；
6. lost-response replay idempotent；
7. changed bytes/action same frontier reject；
8. corrected adapter no B1 causal/latent imports；
9. Encode1 helper T=1/no streaming state；
10. visual96 exact Phase4 formula；
11. Policy/Local shared spatial preprocessing parity；
11a. repeat-before-pad vs pad-before-repeat Policy equivalence；
11b. required mode cannot fall back to direct core scan；
12. Local online scalar reference parity；
13. N>T sequential chunk parity；
14. R1/4/8/16 legal independent T；
15. successful env.step publishes exactly one evidence；
16. decoder/env.step failure publishes zero；
17. done after successful step still records completed action；
18. unexecuted predicted tail ignored；
19. canonical executed raw15 re-decodes to env12；
20. clip/mode/rotation/gripper cases；
21. reset clears state/replay；
22. episode change without reset fails；
23. server prepare/generate/commit success；
24. generation failure aborts candidate；
25. corrected status/no B1 endpoint fields；
26. required mode serial only；
27. off-mode regression；
28. existing raw15/state/prompt server tests；
29. historical B1 import prohibition；
30. Ruff/format/py_compile/diff checks。

## 23. Phase6B real parity / bounded smoke

Scratch real tests only after fresh authorization。

Gate 1 — Encode1 parity：
- same strict cache/source RGB witness；
- cache `Z_t[0]` vs corrected server Encode1；
- z_t + visual96 metrics。

Gate 2 — no-policy online Local：
- real Wan + Local core；
- completed composite/raw15 sequence；
- finite fast state/token；
- reset/replay。

Gate 3 — server bounded request smoke：
- only after checkpoint candidate authority；
- S0 + at least two replans；
- required Local transaction。

Gate 4 — simulator smoke：
- only after production/GPU readiness authorization；
- 48-step then 128-step soak；
- env.step failure injection；
- MP4/telemetry。

## 24. Production/GPU boundary

Current Phase6 design/scratch does **not** authorize：

- promotion of `afb9ca8` or later scratch SHA into production child；
- root Gitlink change；
- formal GPU readiness；
- simulator SR screening；
- long training。

Phase3.5 thresholded parity remains OPEN unless Owner explicitly re-freezes/waives it。

## 25. Formal Phase6 success criterion

Phase6 corrected online path is accepted only when evidence demonstrates：

```text
same current visual definition
+ completed-action chronology
+ post-decoder action authority
+ episode-persistent fast state
+ replay/reset atomicity
+ H_pred/R/T independence
+ prefix in real action path
```

A nonzero fast state/status field alone is insufficient。

## 26. Current authorization boundary

Before formal review：

- cx must not modify Phase6 code；
- ds must not run Phase6 real parity/simulator；
- no GPU/simulator execution authorized。
