# PSM-WMA V3 — old-profile H3-F readiness10 closure and current-profile revalidation gate

- Date: 2026-09-30
- Old readiness formal pair:
  - root `422899072dce46a1602ea76ef767d498c709f469`
  - child/Gitlink `00241445e17bccbec63f9c29ee75531712bc3de1`
- Old readiness verdict: **H3F_OWNER_LAUNCH_READINESS10_CLOSED_FOR_OLD_PROFILE**
- Current H3-F formal pair:
  - root `5c643045534fa080612239a6ba752a55226ef6c3`
  - child/Gitlink `69dcb48fa0e188f95d43590300dad7542b6a9ab5`
- Current long-run verdict: **BLOCKED_PENDING_REASONER_TTT_READINESS**

## What the old readiness proved

The owner-env launcher and grouped H3-F runtime were validated on the old H3-F trainable profile.

Evidence included:

- owner-env exact preflight PASS;
- 9036 train catalog and frozen manifest;
- save_iter=500;
- 30k scheduler / 500 warmup;
- 8×H100 readiness smoke, 10 optimizer iterations;
- 8/8 ranks PASS;
- exact 32/32/1/1 per optimizer iteration;
- finite native loss and gradients;
- final iter10 DCP complete;
- same owner facade / authority paths;
- fail-closed matrix PASS;
- median step wall around 138.3s under the observed co-resident environment.

This evidence is retained as a valid runtime/performance baseline for the old profile.

## Why it does not authorize the current 30k run

The old readiness optimizer inventory explicitly trained:

- moe_gen;
- time_embedder;
- vae2llm;
- llm2vae;
- action2llm;
- llm2action;
- action_modality_embed;
- local_memory.

The current H3-F formal pair intentionally changed the trainable profile to:

- `net.language_model.*` excluding parameters containing `_moe_gen`;
- `net.local_memory*`;
- all other parameters frozen.

This is a material training-contract change. It changes:

- optimizer inventory;
- optimizer state size;
- gradient path;
- memory footprint;
- compute time;
- formal config digest.

Therefore the old readiness cannot be reused as current-profile long-run authorization.

## Current readiness requirements

Revalidate the exact current pair:

- root `5c643045534fa080612239a6ba752a55226ef6c3`;
- child `69dcb48fa0e188f95d43590300dad7542b6a9ab5`.

The current readiness must prove:

1. CPU/static PASS;
2. owner-env exact preflight PASS;
3. selector = `[language_model, local_memory]`;
4. trainable profile = `reasoner_without_moe_gen+local_memory`;
5. selected reasoner parameter count > 0;
6. selected Local parameter count = 165312;
7. no selected `_moe_gen` parameter;
8. no selected H3-E action/generation host key;
9. finite, non-zero Reasoner gradient witness;
10. finite Local gradient witness;
11. 8/8 rank readiness PASS;
12. complete final DCP;
13. updated timing and memory evidence.

Because the trainable parameter set is much larger/different than the old profile, old timing and
memory numbers are contextual only.

Do not start the formal 30k run until this current-profile readiness closes.
