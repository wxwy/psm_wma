# ChatGPT Independent Review — R09-B2 P4-v4 candidates deterministic-order remediation

- Implementation: `6577f1c420fc43fd4070690ae05512cb7e61eaa5`
- Request ledger: `651f380728bafd1cf7eeafcbd8893e8c506da53d`
- Previous candidates closure review: `4fa74b8d56a7aa762e633f2059fee0d6deff086b`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Verdict

`APPROVE_TO_CLOSE_P4_V4_EXECUTION_REQUEST_CANDIDATES_STATIC_TOOLS`

## Findings

The remediation changes only the two candidate/backend iteration sites from the unordered `RUN_KEYS` set to the frozen backend order `("recurrent", "ttt_fast_weight")`.

This is a valid deterministic-order fix. The previous set iteration could vary with `PYTHONHASHSEED`, changing which backend/error branch is reached first in negative fixtures such as the derived-leaf ancestor-symlink case. The fixed tuple preserves the accepted/rejected domain and all existing candidate/run cross-bindings while making validation order stable.

No new contract regression was found. Remaining uses of `RUN_KEYS` for exact set equality/type membership do not create the same branch-order instability. The request-head Gitlink remains the frozen `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`.

This verdict closes only candidates static tooling. It does not authorize candidate materialization, run-root/staging creation, real P4 preflight, record/refreeze/evidence publication, P5 export/compose, torchrun/GPU/CUDA, model/data/checkpoint I/O, training/evaluation/inference, B2-T, or Local Memory training.
