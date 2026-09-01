# R09-B2 P5 full resolved-config diff design review

- Request: `04082e44dfb1ad8424ce072594d19b251736387c`
- Design commit: `142f69b68095a2cb62ec4bea9282ff2563936630`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **REQUEST_CHANGES**

## Findings

### HIGH — P5 must replay the exact production compose path, including D005 trailing argv overrides

`cosmos_framework.scripts.train` does not consume a pre-resolved TOML tree. It calls `load_experiment_from_toml(args.sft_toml, extra_overrides=args.opts)`. That loader validates the structured TOML, builds Hydra overrides, imports the base/experiment Python config, calls `load_config`, resolves OmegaConf interpolation, and applies trailing command-line overrides last.

The P4 D005 freezes `trainer.max_iter=100` and `trainer.save_zero_checkpoint=true` as trailing argv tokens. The current design only says the exporter parses structured TOML/config under the D005 environment; it does not explicitly require parsing the exact D005 argv grammar and feeding those same trailing overrides through `load_experiment_from_toml`.

Required design change:

1. The exporter must derive TOML path and extra overrides from the exact verified P4 D005 `command.argv`; no parallel/manual override list.
2. It must call the same production compose path, i.e. `load_experiment_from_toml(<frozen TOML>, extra_overrides=<frozen trailing overrides>)`, or an explicitly proven equivalent wrapper around the same functions.
3. Any mismatch between D005 argv and exporter inputs must fail closed.
4. Permanent negative test: omit/change/reorder the `trainer.max_iter=100` or `trainer.save_zero_checkpoint=true` D005 override and require FAIL.

### HIGH — recurrent and TTT exports need fresh-process isolation

The production experiment module reads `PSM_R09_B1_TTT_ENABLED` at module import time and constructs module-level config objects. `cosmos_framework.configs.base.config.make_config()` imports the shipped experiment module, while Python module state, Hydra `ConfigStore`, and `GlobalHydra` are process-global. Reusing one Python process for recurrent then TTT can therefore reuse the first backend's imported config/registration state and produce a false-equal diff.

Required design change:

- Each backend export must run in its own fresh interpreter subprocess with the exact D005 environment contract; do not compose recurrent and TTT sequentially in one long-lived Python process.
- The subprocess must use the canonical interpreter and framework cwd/PYTHONPATH bound by the D005.
- Parent semantic environment must be sanitized according to D005 `set/unset/inherit_allowlist`; merely calling `os.environ.update()` is insufficient.
- Export subprocess must not call `launch`, `Config.validate`, `instantiate`, distributed init, trainer/model/dataloader construction, checkpoint loading, or CUDA APIs.
- Permanent regression: deliberately attempt two-backend sequential composition in one process or pre-import the experiment under the wrong backend and prove the approved exporter path does not inherit that state.

### HIGH — “reject non-JSON-safe” is incompatible with the real complete Config tree unless object canonicalization is specified

`Config.to_dict()` is based on `attrs.asdict`, but the production base config contains Python objects such as `trainer.type = ImaginaireTrainer`; Lazy config trees may also contain callable/class targets. A literal JSON-safe-only exporter would therefore reject a valid production config or be tempted to drop those fields, neither of which proves a full config diff.

Required design change:

Define a deterministic canonicalization grammar before implementation, including at least:

- primitives / null;
- dict with string keys;
- list/tuple with deterministic normalization;
- attrs/dataclass/config containers recursively;
- Python class/callable/Lazy target encoded by stable fully-qualified `module.qualname` (or another reviewed stable identifier), never `repr()` with addresses;
- enums/path-like values normalized explicitly;
- unresolved OmegaConf interpolation is forbidden after production compose;
- unsupported arbitrary objects fail closed rather than being stringified or omitted.

The verifier must compare the canonicalized complete tree, including target/type identities, and fixtures must show that changing a callable/target identity produces FAIL.

### HIGH — launch controls named in the design are not all members of the resolved Config tree

The design says the diff proves equality for world size, offline/env controls, TTT switch, output root, P1/P3 bindings, etc. Several of these are external launch controls rather than attrs fields in `Config`: for example `WORLD_SIZE` is derived from the one-process torchrun contract, `PSM_R09_B1_TTT_ENABLED` is an environment switch, and `JobConfig.path_local` is a property derived from `IMAGINAIRE_OUTPUT_ROOT` rather than a field serialized by `attrs.asdict`.

Therefore a `resolved_config` JSON tree alone cannot prove all claims in the current design.

Required design change:

Export and verify an explicit machine-readable envelope such as:

```text
{
  provenance: ...,
  effective_launch: {
    command/launcher-derived world_size,
    exact semantic environment,
    budget,
    P1/P3/D005 bindings,
    derived job.path_local/output root
  },
  resolved_config: <canonical production Config>
}
```

The diff allowlist must distinguish config-tree paths from launch-envelope paths. Actual optimizer membership should remain bound to P3 evidence rather than being invented as a resolved-config field; only the resolved selector/config value belongs in the config tree.

### MEDIUM — provenance must distinguish production source, exporter source, and evidence commit

P4 records preserve production source root `ddb4e0e` / Gitlink `21d064f`, whereas a future P5 exporter will live at a later root commit. The P5 artifact should record these separately rather than using one ambiguous `source` field:

- production source / P4 recorded source;
- Gitlink/submodule;
- P5 exporter/verifier source SHA/commit;
- exact P4 recurrent/TTT record SHAs and P4 verification SHA;
- P1/P3 input SHAs;
- later evidence commit separately at closure time.

A later root-only tooling commit must not silently become the production config source being compared.

## Gate decision

`APPROVE_TO_IMPLEMENT_P5_STATIC_DIFF` is **not** granted yet.

Revise the P5 design to make the exact production compose path, fresh-process backend isolation, canonical object grammar, launch-envelope coverage, and split provenance explicit. This is a root-only design/static change; no config export execution, `torchrun`, GPU, model/dataloader/optimizer construction, checkpoint loading, training, evaluation, or inference is required for the remediation.
