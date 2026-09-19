# LIBERO policy server torch.compile override audit

Date: 2026-09-19

## Scope

Ad-hoc runtime hotfix audit; this is **not** a formal R09-B Gate closure token.

Implementation pair:
- root: `12f8af8870fe539aa321f6ef54e261dc9cf5a84d`
- child/Gitlink: `6b09063657eb1b2235d6b058f90d53cdd5c9e89e`
- root parent reviewed for the bug: `e8bdfd15822dabc930af80254a3cdf121dc98e05`
- child parent reviewed for the bug: `8c07e9ecf3c0815c9f54839c4474813fc3bcb0d7`

## Independent root-cause verification

The DS report is correct in substance.

1. `ActionServerArgs.build_setup_overrides()` creates `OmniSetupOverrides` from checkpoint fields and does not map the experiment's nested `model.config.compile.enabled` into the flat inference setting.
2. `ParallelismOverrides.use_torch_compile` defaults to `True`.
3. `OmniInference._get_compile_config()` rebuilds a new `CompileConfig` with `enabled=setup_args.use_torch_compile`.
4. Therefore an experiment that declares `model.config.compile.enabled=false` can still enter compiled inference through the standalone LIBERO server.
5. With Local Memory present on the second/subsequent request, `MemoryPrefixContext.validate()` contains data-dependent tensor reads such as `sample_offsets[0].item()`, which are incompatible with the observed compiled path/guards.

The temporary `/tmp/eval_server_run.py` monkeypatch is therefore a valid diagnostic workaround, but not an acceptable production fix.

## Implemented remediation

Child `6b09063657eb1b2235d6b058f90d53cdd5c9e89e` now:
- adds `apply_model_compile_setting()` in `cosmos_framework/scripts/action_policy_server_utils.py`;
- loads the resolved experiment config before `OmniInference.create()`;
- copies exact `model.config.compile.enabled` into `setup_args.use_torch_compile` when the field is a boolean;
- leaves the inference default unchanged only when the experiment field is absent/malformed;
- adds three regression tests covering explicit false, explicit true, and absent-setting behavior.

Root `12f8af8870fe539aa321f6ef54e261dc9cf5a84d` updates the `cosmos-framework` Gitlink to that child.

This is intentionally narrower than changing `memory_prefix.py` or globally forcing eager inference.

## Evidence assessment

Accepted evidence:
- DS completed the LIBERO end-to-end path with the compile switch forcibly disabled: 220 environment steps, 82 predict requests, no code error, and actions/mp4/predictions produced.
- That evidence strongly supports the diagnosed failure mechanism.

Not yet accepted as closure evidence:
- the successful run used the temporary wrapper/monkeypatch, not implementation pair `12f8af8870fe539aa321f6ef54e261dc9cf5a84d` / `6b09063657eb1b2235d6b058f90d53cdd5c9e89e`;
- no GitHub workflow run exists for child `6b09063657eb1b2235d6b058f90d53cdd5c9e89e` at review time;
- the new unit tests are committed but have not been observed executing by this reviewer.

## Current verdict

**SOURCE_FIX_ACCEPTED / EVIDENCE_ONLY_RECHECK_REQUIRED**

Production blockers: **0**

Evidence-only blockers: **1**

Required acceptance:
1. launch the native LIBERO server from root `12f8af8870fe539aa321f6ef54e261dc9cf5a84d` / child `6b09063657eb1b2235d6b058f90d53cdd5c9e89e` with the temporary monkeypatch removed;
2. verify startup logs resolve `use_torch_compile=False` from `model.config.compile.enabled` for the TTT checkpoint;
3. execute at least two sequential predictions in the same Local-Memory episode so the second call carries a non-empty Memory Prefix;
4. observe no torch.compile guard/data-dependent-value error and normal action output;
5. preferably repeat the existing 220-step task-0 smoke to confirm the full HTTP/simulator path remains healthy.

Task SR=0 for `iter_200` remains a model-quality result and is not evidence of a server/code failure.

No formal Gate closure token is issued by this review.
