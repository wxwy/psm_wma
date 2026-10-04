# PSM-WMA V3 — V2→Latest Cosmos-Framework Migration Detailed Design v1.0

Date: 2026-10-04  
Status: design authority for the active V3 H3-F training / online Local-TTT / RoboCasa evaluation route.

## 1. Purpose

V3 is **not a clean-room rewrite of V2**. Its purpose is to forward-port the working V2 Local-TTT
semantics onto the latest supported Cosmos-Framework base while preserving checkpoint compatibility
and explicitly recording every intentional semantic delta.

The migration rule is:

> V2 behavior is inherited unless this document explicitly lists a V3 delta or latest-upstream
> authority requires an API adaptation.

No adapter, evaluator, cache builder, or inference server may silently redefine the training ABI.

## 2. Repository lineage

Current audited lineage:

- NVIDIA upstream authority: `NVIDIA/cosmos-framework@cf5d68c00d97ccd2480a2320ed652b92dec63102`
- V2 reference branch: `wxwy/cosmos-framework@e3dc9ecce0a4a7223245dc4f5b5efde7b709fd92`
- V3 child before this redesign: `wxwy/cosmos-framework@da6a9b972575af829af63e7747fad2fd73ae8157`

GitHub ancestry check shows V3 is **128 commits ahead and 0 commits behind**
`NVIDIA/cosmos-framework@cf5d68c...`. Therefore V3 is already based on the latest audited upstream;
this redesign does **not** rebase or rebuild the branch.

The existing V3 history and all model checkpoints remain immutable assets.

## 3. iter500 checkpoint decision

The formal H3-F long-run training contract was authorized on:

- root `e272a589ce2204f5b4324e79c0f1227d855f3e97`
- child `f89876a4bb013d9a48d622db776996ded295884b`
- profile `v2_semantic_generation+local_v3_raw15`
- data profile `official_v30_raw15`

The iter500 DCP produced by that training route remains the canonical evaluation checkpoint.

**No retraining is required by this migration remediation.**

Reason: the H3-E/H3-F training route intentionally used:

- official policy RGB path for the native outer loss; and
- the frozen B1 episode-level dual-camera causal latent cache only for Local-TTT evidence.

The current defect is in online inference/evaluation evidence materialization, not in the checkpoint
parameter ABI.

No parameter names, tensor widths, optimizer groups, or checkpoint keys are changed by the planned
inference remediation.

## 4. Upstream RoboCasa policy authority

Latest upstream RoboCasa `camera_set="left_wrist"` is the authority for policy observations.

Per source step:

```text
left RGB  [3,256,256] ─┐
                       ├─ pixel concat on width → composite RGB [3,256,512]
wrist RGB [3,256,256] ─┘
                                      ↓
                              causal Wan2.2 VAE
                                      ↓
                         policy vision latent [48,Tz,16,32]
```

Training uses a 33-frame observation window for the H3-F chunk32 route.
The causal tokenizer maps `T_pixel = 4n + 1` to `T_latent = n + 1`.

This composite policy latent is used by the native Cosmos policy/generation path. It is **not**
the Local-TTT evidence ABI described below.

## 5. V2 invariants and intentional V3 deltas

### 5.1 Inherited V2 semantics

The following remain semantic invariants:

- only **executed** actions may become Local evidence;
- predicted-but-not-executed chunk members never update fast state;
- consumer step 0 is Local-neutral;
- evidence for consumer `s>0` is sourced from `s-1`;
- evidence chronology is contiguous and exactly-once;
- Local inner loss only updates fast state; native policy loss is the outer objective;
- Local prefix enters the policy action path;
- fast-state update is transactional with the native outer/generation success boundary;
- reset prevents cross-episode state leakage;
- exact replay is idempotent; changed replay fails closed;
- slow Local parameters and generation/action parameters are checkpointed normally;
- inference fast state is ephemeral.

### 5.2 Intentional V3 deltas

These differences from V2 are frozen V3 ABI, not migration accidents:

1. RoboCasa source: `robocasa365_official_v30`, train catalog 9036.
2. Action evidence: raw15 instead of V2 ego20.
3. Policy chunk: chunk32 / 33 observation frames in H3-F training.
4. Local runtime names:
   - V2 `evidence_encoder` → V3 `encoder`
   - V2 `ttt_core` → V3 `core`
5. H3 grouped training: 8 stable slots/rank, T16 segment, GA2 grouped window.
6. H100 mesh: dp_shard8 for generation + Local slow parameters.
7. **Local visual evidence representation**: V3 H3-F uses B1 episode-level dual-camera
   causal-endpoint latents, not the V2 composite exact-window latent.

The seventh item is a checkpoint ABI because iter500 was trained with it.

## 6. Local visual evidence authority (iter500 ABI)

### 6.1 B1 source representation

The B1 cache stores the two native 256×256 cameras independently:

- `observation.images.robot0_agentview_left`
- `observation.images.robot0_eye_in_hand`

Each camera is encoded by the same frozen Wan2.2 causal VAE.

For an episode with F source frames, the canonical causal endpoint grid is:

```text
0, 4, 8, 12, ...
```

plus a terminal `F-1` only when the offline cache builder needs to close an incomplete tail.

Each cached camera latent:

```text
fp16 [48,16,16]
```

The two camera latents are fused only for Local evidence:

```text
left latent  [48,16,16] ─┐
                         ├─ width concat → [48,16,32]
wrist latent [48,16,16] ─┘
                                  ↓
                       channel mean48 + RMS48
                                  ↓
                            visual96 [96]
```

`latent_to_visual96()` is the sole visual96 authority.

### 6.2 Source-step mapping

For normal stream steps:

```text
endpoint(s) = 4 * floor(s / 4)
```

Therefore:

- steps 0..3 consume endpoint 0;
- steps 4..7 consume endpoint 4;
- steps 8..11 consume endpoint 8;
- etc.

This repeated-within-4-block behavior is what iter500 saw during training and must be reproduced
online.

### 6.3 Training chronology

For consumer step `s`:

```text
s = 0:
  no Local evidence
  policy payload receives no Local prefix

s > 0:
  evidence_visual = visual96(source_step=s-1)
  evidence_action = executed_raw15(s-1)
  fast_state <- TTT(fast_state, evidence_visual, evidence_action)
  resulting Local token conditions native policy outer loss for consumer s
```

The native policy payload itself still contains official composite `left|wrist` RGB and follows
the normal upstream RGB→Wan VAE route.

The Local B1 cache is never injected as the policy vision latent.

## 7. Correct online inference design

### 7.1 Policy replan chronology

Let the server return an action chunk and evaluator execute N actions before replanning.
N is evaluator-controlled; common values are 4, 8, or 16 and it is not hard-coded into Local-TTT.

For one replan interval:

```text
policy query at consumer c
  uses committed fast state W_c
  → returns action chunk

execute only N selected actions
  for i = 0..N-1:
    record pre-action left/wrist RGB at source step c+i
    record the raw15 action actually executed

next policy query at consumer c+N
  materialize those N completed evidence rows
  advance causal visual stream in source-step order
  advance Local fast state in source-step order
  generate next action chunk using the resulting Local prefix
  commit visual-stream state + fast state only if generation succeeds
```

### 7.2 Online causal VAE

Online inference must **not**:

- re-encode `frames[:current]`;
- encode each source frame as an unrelated T=1 image;
- reconstruct future training labels;
- use the composite policy image as the Local evidence representation.

Instead it replays the B1 causal endpoint process incrementally.

Two cameras are placed on the VAE **batch** dimension so they keep independent spatial streams while
sharing one causal encode call:

Prime endpoint 0:

```text
[2,3,1,256,256] → encode_streaming → [2,48,1,16,16]
```

where batch row 0 is left and batch row 1 is wrist.

Every next endpoint consumes exactly four new RGB frames per camera:

```text
[2,3,4,256,256] → encode_streaming → [2,48,1,16,16]
```

At source steps between endpoints, Local evidence reuses the last endpoint visual96.

Only a maximum of three not-yet-encoded RGB tail frames per camera are retained. Memory must not
scale with episode length.

### 7.3 Training label boundary

Future 4-frame latents used by the native causal video objective are training targets/labels.
Online Local-TTT does not reconstruct those targets.

The four-frame chunks used by the Local streaming encoder are different: they are already-observed
past RGB required to advance the **causal encoder state** to the next B1 endpoint.

## 8. Transactional visual-stream state

The causal VAE encoder state is part of the online Local transaction.

A request has:

- committed visual stream state;
- candidate visual stream state;
- committed fast state;
- candidate fast state.

Required order:

```text
restore committed VAE stream
  ↓
materialize new visual96 rows
  ↓
snapshot candidate VAE stream
  ↓
restore committed VAE stream
  ↓
prepare candidate Local fast state
  ↓
native policy generation
  ├─ success → commit BOTH candidate VAE stream and candidate fast state
  └─ failure → discard BOTH candidates
```

A failed generation must never advance one state machine without the other.

Exact response-loss replay must reuse the committed last-batch visual96/action fingerprint and must
not encode the same RGB again.

## 9. Wan tokenizer authority

Latest upstream already provides the required causal primitives:

- `encode_streaming()`
- `clear_encoder_cache()`

V3 must expose a small public snapshot/restore state API around that existing cache. RoboCasa code
must not directly access tokenizer private fields such as `_enc_cache`.

The upstream model remains the normalization authority. RoboCasa inference must not duplicate
uint8→[-1,1] conversion.

## 10. Single-source code ownership

Active H3-F / online code authorities:

| Concern | Authority |
|---|---|
| policy RGB composition | upstream RoboCasa dataset/eval `left_wrist` composition |
| Wan RGB normalization + encode | `OmniMoTModel` / Wan tokenizer |
| B1 endpoint policy | `robocasa_latent_evidence.py` |
| visual96 transform | `latent_to_visual96()` |
| episode cache build | `tools/v3/build_robocasa_b1_h5_cache.py` consuming the endpoint authority |
| training chronology | `RoboCasaSegmentProducer` + grouped trainer |
| inference fast state | `OnlineLocalMemory` |
| inference visual stream | RoboCasa inference adapter using public Wan stream-state API |
| policy Local injection | `attach_local_prefixes()` |
| reset/replay/ack | RoboCasa Local client + adapter |

No second implementation of endpoint generation, visual96, VAE normalization, or Local chronology is
allowed.

## 11. Active route vs retained historical modules

The active production route is:

```text
official_v30
→ RoboCasaSegmentProducer / B1 reader
→ GroupedLocalMemoryTrainer
→ H3-F generation+Local checkpoint
→ action_policy_server_robocasa
→ OnlineLocalMemory
→ RoboCasa closed_loop_eval
```

Older `native`, `joint`, `local_s1`, detached-relay and pre-H3 experimental modules are retained
for history/tests but are **not production authorities**. They must not be imported into the active
route merely to reuse stale semantics.

This redesign intentionally avoids mass deletion because that would increase checkpoint and
regression risk.

## 12. Evaluation architecture

The simulator must keep `action_horizon/replan_steps` configurable.

The model may generate more actions than the evaluator executes. Only the executed prefix produces
evidence.

For the 18-task screening, the preferred parallel topology is:

```text
8 GPU workers
  each owns:
    1 model server
    1 RoboCasa evaluator process
    1 active Local session
  shared deterministic task queue
```

This avoids cross-session Wan encoder-state multiplexing and keeps failures isolated by GPU worker.

## 13. Acceptance gates

### CPU/static

Must directly prove:

1. endpoint policy is shared by builder/reader/inference;
2. N=4/8/16 replan boundaries work;
3. step 0..3 share endpoint0, 4..7 share endpoint4, etc.;
4. no episode-long RGB history is retained;
5. exact replay performs no second VAE advance;
6. changed RGB/action replay fails closed;
7. abort restores both visual-stream and fast-state transaction;
8. reset clears both;
9. policy composite RGB path is unchanged;
10. checkpoint parameter inventory is unchanged.

### Real Wan VAE GPU parity

Using identical source RGB, compare:

- offline B1 full-episode cache endpoint latent;
- online prime + 4-frame streaming endpoint latent.

Verify endpoint shape, fp16 materialization and visual96 parity within a frozen tolerance.

### Closed-loop smoke

On iter500:

- required Local mode;
- replan N=4,8,16;
- `adapted_steps` matches completed evidence count;
- prefix appears after cold start;
- fast state finite;
- server memory reaches a bounded plateau and does not scale with episode length;
- no chronology/replay/reset errors.

### Behavioral Gate

Only after parity/smoke are green:

- 18 target-atomic task classes;
- one fixed seed;
- iter500 unchanged;
- preserve per-task rollout MP4 and telemetry;
- report SR and task-level behavior.

## 14. Findings that this design supersedes

### CLOSED by design

- Rebuilding V3 from scratch: forbidden.
- Retraining iter500 solely because of the online adapter defect: not required.
- Treating the Local B1 latent as the policy composite latent: forbidden.
- Reconstructing training-only future labels at inference: forbidden.

### Current implementation blocker

`da6a9b97...` changed online evidence to independent T=1 encoding for every completed step.
That is bounded-memory, but it does **not** reproduce the B1 causal-endpoint distribution used by
iter500. It must be replaced by the transactional streaming-endpoint implementation in this
document before GPU evaluation.

The earlier full-history-prefix implementation reproduced causal history more closely but had
episode-length VAE work/memory growth and duplicated cache-builder semantics; it is also superseded.

## 15. Migration rule going forward

Every V3 change must be classified before implementation as exactly one of:

1. **upstream API adaptation** — behavior preserved;
2. **V2 semantic carry-forward** — behavior preserved;
3. **explicit V3 ABI delta** — behavior intentionally changed and documented here;
4. **experiment-only** — cannot become production authority without a new design Gate.

If a change cannot be placed in one category, implementation must stop until the design is updated.
