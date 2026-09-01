# R09-B2 P5 isolated reviewed-root static-export execution review

- Request commit: `349a028ae288eee1f245f9d3ae2d131e36cf5a2f`
- Reviewed exporter/static-tools revision: `9ad602f93f5975f9ec7d033783b41052ca09107e`
- Evidence-root revision: `8bde8c12876219b1a36d50b604e05701bf550e3e`
- Frozen production revision: `ddb4e0eae97fb545d5239c1ddb6d4387170f3780`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **APPROVE_TO_RUN_P5_STATIC_EXPORT**

## Scope

This is a one-shot execution authorization for the exact CPU-only P5 resolved-config static-export command frozen in request `349a028...`.

It authorizes exactly one invocation of that command with:

- parent bootstrap: `/opt/conda/bin/python3.11 -I` from `/tmp`;
- exporter root: `/disk/rl/psm_wma_p5_exporter_9ad602f` at `9ad602f93f5975f9ec7d033783b41052ca09107e`;
- production root: `/disk/rl/psm_wma_p4_d005_retry` at `ddb4e0eae97fb545d5239c1ddb6d4387170f3780`;
- evidence root: `/disk/rl/psm_wma_p5_evidence_8bde8c1` at `8bde8c12876219b1a36d50b604e05701bf550e3e`;
- Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb` for all three roots;
- canonical output: `/disk/rl/psm_wma_p5_static_export_20260901`.

Any command, root, revision, Gitlink, output path, retry policy, or exporter/verifier code change requires a new execution review.

## Findings

### Previous HIGH is closed: reviewed identities are proven before project import

The frozen bootstrap now starts from `/tmp` with Python isolated mode and imports only standard-library modules before trust checks. It does not expose exporter or production code through `PYTHONPATH` before preflight.

Before inserting the exporter root into `sys.path`, the command independently checks, using `pathlib` and `subprocess` only:

- each root resolves to its exact frozen absolute path;
- each root HEAD equals its explicitly approved revision;
- each root Gitlink equals the frozen Cosmos revision;
- each submodule HEAD equals that Gitlink;
- each root and submodule is clean under `git status --porcelain=v1 --untracked-files=all`;
- the canonical output path is absolute, absent, and non-overlapping with every frozen root.

Only after those checks pass does the bootstrap insert the exact exporter root into `sys.path` and import `run_parent_export`. This closes the prior clean-but-moved-checkout / pre-import root-owned-code bypass.

### Requested execution remains narrow and fail-closed

No exporter/verifier/test code changed in this remediation commit; the change from the previous ChatGPT execution review is limited to the concrete execution request and status documentation. The actual exporter remains the previously reviewed `9ad602f...` code.

The authorized path remains limited to two fresh child resolved-config compositions through `load_experiment_from_toml`. The child contract forbids launch/validate/instantiate/trainer/model/dataloader/optimizer/checkpoint/distributed execution and fails if CUDA becomes initialized.

The parent still requires the P5 pair verifier to return `PASS` before atomically promoting the attempt directory to the canonical output. Any exception or verifier failure must leave the canonical output absent and retain the attempt `failure.json`; this approval permits no retry.

The production Cosmos `.gitignore` does not ignore arbitrary `.py` files such as `sitecustomize.py`, so the requested root/submodule untracked-file check covers the concrete root-owned startup-injection concern raised in the previous review.

## Gate decision

**APPROVE_TO_RUN_P5_STATIC_EXPORT** is granted for exactly one execution of the frozen command in request `349a028ae288eee1f245f9d3ae2d131e36cf5a2f`.

Success is not itself P5 closure. After execution, the generated canonical artifacts, verification result, exact command/runtime evidence, root revisions, and failure/success provenance must be submitted for an independent closure review.

This approval does **not** authorize:

- a second run or retry;
- changing any root/revision/path/environment/command;
- CUDA or GPU use;
- `torchrun` or distributed initialization;
- model, dataloader, optimizer, or checkpoint construction;
- weights/data/MP4 access;
- training, evaluation, or inference;
- P5 closure;
- B2-T or any later Gate.
