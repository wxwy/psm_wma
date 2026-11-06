# Issue22 Local-TTT pipeline design — draft before implementation

Start Root `8aeb2442993620ee4513834a73064a4ea1eca38c`, Child `1ca308055fc41fb69efaeb9efaa23808f164a18e`. Isolated branch `v3-local-ttt-pipeline-issue22-20261107`. Owner issue: https://github.com/wxwy/psm_wma/issues/22 . No official Gitlink update or running evaluation changes.

## G0: reusable current feature boundary

Policy `_prep_policy_item` and independent Encode1 use `prepare_robocasa_composite_frame`. WAM condition frame0 reaches Omni causal-prefix encoding with T=1; ordinary Wan encode starts with fresh caches and its first-frame chunk. The reusable value is the full padded, normalized Wan return's current latent **before** `_remove_padding_from_latent`. Independent Encode1 pools this full canvas; pooling the cropped Policy x0 changes Visual96 (even canonical256 input can pad/crop). Capture only during the existing inference call, with exact per-sample input/output binding. No extra encode, no fallback on missing/reordered/different input. Numerical CPU proof must precede production changes, with real Wan implementation and synthetic weights; full DCP/GPU results stay explicitly unrun.

## Proposed bounded causal work flow (subject to G0)

1. Successful policy generation stages current-frame feature with the response transaction. Its publication follows the same atomic commit as Fast/Visual/Response. The feature is bound to lease/session/episode/frontier and canonical preprocessed image digest.
2. After each actual successful `env.step`, a bounded asynchronous sender submits that completed pre-action composite/raw15 with exact source step. No future/failed action evidence enters the pipeline. Client enqueue must not wait for encoding/scan; capacity exhaustion raises a visible error rather than silently dropping or growing unboundedly.
3. Server accepts validated completed evidence into a separate bounded queue/frontier. First boundary source step matches the cached policy feature (zero Encode1); other source steps each get independent Encode1 with clean VAE state. Never encode a 16-frame history video.
4. One existing model executor handles each evidence unit (Encode1 plus model-owned scan T=1) and native generation, keeping the GPU lock ownership singular and avoiding concurrent telemetry/cache mutation. Generation ready work has priority with bounded progress for evidence. Replan scheduling first satisfies its exact dependency frontier; it must not wait on a future its own worker needs to execute.
5. Fast-state work is a detached unpublished candidate tail rooted at the last committed snapshot. Replan validates complete history bytes/order/frontier and only consumes the matching tail. All Fast/Visual/Response publication remains the existing one-snapshot transaction; rollback/retry cannot skip uncommitted evidence. Telemetry sums/counts cover the whole evidence segment.
6. Exact duplicate evidence is idempotent; changed bytes, source gaps/order, stale epoch, reset/new episode, aborted generation and worker errors fail closed. End/close drains/fences all owned work before ACK/reuse. No-TTT never creates this machinery or new Local kwargs.

## CPU and performance evidence

After G0: T16 vs sixteen T1 model-owned scans (state, final prefix, inner loss sums/counts, adapted steps and action inputs); 16-history uses15 independent Encode1; causal client/server overlap, Session/epoch/lease isolation; duplicate/out-of-order/changed retry/abort/reset/error/cleanup; existing transaction and No-TTT regressions. Timings distinguish composite/PNG, Encode1, Visual96, fast update, queue, native generation, Sim stepping. GPU timing needs events or synchronization. CPU controlled overlap/timing is not H100 speedup or real Ep/h. Real before/after P50/P95/Ep/h remains pending Owner authorization; no GPU benchmark or900EP during L2000/L4000.

Draft PR and exact Child candidate SHA with CPU raw logs/JUnit/source fingerprints go to GPT. Root records integration instructions only; do not automatically update V3 Gitlink or merge. Preserve training/cache schema/scientific identity/Resume semantics and old run results.
