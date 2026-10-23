# CPU fault witnesses — 2026-10-23

Locked source: Root Implementation `a4b22b929175e462b6a8db57ad2abee7e220dd37`, Child `c9f21040f462a114d597fc83773cb9b6a9e96214`; audit docs baseline `81055c909d6547ed4eb607fd0cc746af4bee7c0a`.

Both recorded final commands exited 0: **the witnesses reproduced current defects; this is not production PASS or DS/GPT acceptance**. No full repository Ruff/pytest, CUDA/FSDP/model, real Kitchen/rendering, training/data/DCP operation occurred. Simulator inputs, prediction/Local client, runtime and process evidence are explicit doubles. Original functions perform the recorded result/Attempt/Resume validations. The thread witness selects the exact launch Try AST; the gradient witness selects the exact two Guard methods and uses real two-rank CPU Gloo/SGD.

- `behavior.json`: oracle failure on the evaluator's second check, metadata exception and missing lang produce `error=null`, COMPLETE and Resume skip. The first oracle call inside fake env.step succeeds, reflecting that real Kitchen.reward also calls it. A partial Thread.start failure leaves the earlier thread alive without stop; the probe then joins its own synthetic worker.
- `gradient.json`: six scenarios on both ranks. Missing all gradients on one nonempty Rank and callback-cleared gradients incorrectly pass; per-parameter None and empty-Rank controls pass; globally missing and Rank1 Inf fail on both ranks as expected. Empty tensors stand in for empty local shards; no real DTensor/FSDP execution is claimed.

`commands.json` contains actual commands, cwd and external-cache/offline environment. For reproduction, use the relevant CPU dependencies, set `PSM_AUDIT_ROOT` and PYTHONPATH to the exact isolated checkout and **choose a new empty external `PSM_AUDIT_OUTPUT`**. Do not run against a different source pair or overwrite this archive. No real checkpoint/dataset is an input. The scripts write only to the external output directory, never beside the archived script. The immutable source hashes are in the result JSON.

Archive checksums:

- behavior_probe.py: `de8e6254f512d0afb2847caf59f5566a5e1d39f5bab1aeb14c5ee5c8f9c4e646`
- gradient_probe.py: `c817446d2beac87fd3a9fd3ac5c1372dcce49cfc15c848eb6d4fbf58994eece6`

No production source or test was modified to obtain these observations. Findings and minimal remediation proposals are in the parent review report.
