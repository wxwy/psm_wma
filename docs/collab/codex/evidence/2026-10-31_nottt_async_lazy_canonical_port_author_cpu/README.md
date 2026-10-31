# Current-V3 No-TTT async/lazy port: author CPU evidence

Formal Root `c66ade95b044d3664cd782d43d7917a604425db3`; Child/Gitlink
`baf1b5bf46853e9849a91518803b9738fc216235`. Evidence and ledger commits are
docs-only successors, not replacements for these implementation identities.

Final targeted run: **43 passed, 0 failures/errors/skips** (33 receiver/source
and 10 regression cases). Ruff0.12.7 check/format and AST14 PASS; worktrees clean
and exact source hashes unchanged during execution. Original commands and
environment are preserved. This is author CPU evidence, not DS independent
execution, real DCP Resume, GPU throughput, model training or deployment approval.

`object_equivalence.json` proves all13 transferred paths are exact donor224c
objects and the other1,255 Child objects remain current canonical0ae. Six
production paths are required because currentV3 lacked the Issue9 async binding;
seven are approved test/support paths. Whole training trees equal accepted donor,
while current EvalV2 inference/simulation/evaluation objects remain preserved.
Root launchers equal both canonical and tested donor. Issue13 code is absent.

`formal_source_bindings.json` binds14 checked Python files to formal Git objects.
`root_implementation.diff`/`child_implementation.diff` show complete baseline-to-
formal scope. `run_gate.py` is the exact external runner used; it requires a new
external output directory and explicit worktree/Pair. `audit.py` is the original
fixed-worktree Git-object-only audit. Adapt paths explicitly before rerunning.

`preliminary/` is the earlier7-case wiring check, all repeated in final43; do not
add7 to43 as unique cases. Prefinal Root784 E402 annotation placement correction
was comment-only and is documented in scope_and_limits.json. The final Pair
passed the unmodified Ruff rules. No original301 or full58 retest was performed.

Tests use synthetic local parquet/latents, temporary receipts/vocabulary, tiny
CPU models and real CPU worker spawn/Trainer lifecycle. Resume checks cover
model/optimizer/scheduler/iteration/RNG/Frontier and Consumer continuity with
workers0→8/rank0 and8→8/rank3. They do not read formal checkpoints. The overlap
trace is CPU Source/Transform versus synthetic compute, not CUDA performance.

Raw logs retain dependency/worker-affinity warnings and an async-exit
resource_tracker warning about2 semaphore objects. Selected worker-cleanup
assertions passed; this is not a blanket claim of zero leaked OS resources.
No real data/model/GPU or formal Job was accessed, and no canonical merge or
training Resume is authorized by this author result. Historical DS/GPT1.61x
performance acceptance remains identified as historical evidence only.
