# R09-B2 P5 static exporter/verifier/CPU fixtures review

- Request: `ba0ecde91608b99c5390ec0a6f9ea3d4bf6d05d1`
- Implementation: `b4bebff6039b05e74d591a06d3cd386875081bfd`
- Final reviewed root: `30f3ce6d3a73e60c49a3feefea3e6252d168bf33`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **REQUEST_CHANGES**

## Findings

### HIGH — exporter has no D005-bound parent orchestrator; child compose is directly callable

`tools/g0/export_r09_b2_p5_resolved_config.py:85-153`

The helper functions correctly parse the frozen trailing overrides and can construct a sanitized child environment, but no parent execution path actually binds those pieces together. `main()` directly accepts `--child-request/--child-output` and calls `_child()`. `_child()` trusts only `payload["toml"]` and `payload["overrides"]`; it does not verify the P4 D005 record, current cwd, interpreter identity/SHA, exact effective environment, backend, or recorded production provenance before invoking `load_experiment_from_toml`.

The current implementation therefore does not implement the approved fresh-child contract. A caller can supply an arbitrary request JSON and trigger production compose under the caller's current cwd/interpreter/environment.

Required before static export can be requested:

- add a parent-only path that takes the frozen recurrent/TTT P4 D005 records as inputs;
- verify the D005 pair/provenance first;
- derive TOML and ordered overrides exclusively through `parse_d005_command`;
- build the child environment exclusively through `sanitized_environment`;
- launch each backend in its own fresh canonical interpreter with exact D005 cwd/env/PYTHONPATH;
- make the child verify current cwd/interpreter/env against the parent request before compose;
- collect the child resolved tree and build the full approved `effective_launch + resolved_config + provenance` envelope.

The child mode may remain internal, but it must not be the only externally callable export path.

### HIGH — verifier only compares the pair; identically forged common fields can PASS

`tools/g0/verify_r09_b2_p5_full_config_diff.py:42-93`

`verify_pair()` currently validates only schema string, backend labels, a small P3 check, and whether pair differences are allowlisted. It does not independently validate each envelope against the frozen P4 D005, P1 production manifest, P3 PASS evidence, production source/Gitlink, exact world/budget, exact argv/environment, output roots, or exporter provenance.

Therefore any common field forged identically on both sides is invisible to `diff_paths()` and can PASS. Examples include setting both sides to a fabricated production source, fabricated P1/P4 hashes, `world_size=99`, altered common budget, altered precision/seed/cache/manifest, or a common forged resolved-config value.

The existing CPU fixture itself demonstrates this trust gap: the positive pair omits most of the required v0.2/v0.3 envelope fields and still PASSes (`tools/g0/test_r09_b2_p5_full_config_diff.py:17-25`).

Required:

- define and enforce the exact envelope schema/required fields;
- independently bind each backend envelope to the frozen P4 D005/P1/P3 evidence and production source before pair-diff logic;
- validate exact world/budget/argv/env/derived output fields per backend;
- add a permanent negative where the same forbidden common value is changed on both sides and the verifier must FAIL.

### HIGH — P3 backend contracts are caller-owned through `--contracts`

`tools/g0/verify_r09_b2_p5_full_config_diff.py:42-50, 95-100`

The verifier accepts an arbitrary external `--contracts` JSON and only checks that the envelope backend contracts equal that caller-supplied object. This is self-consistent rather than verifier-owned. A forged contracts file plus matching forged envelopes can satisfy `_p3_checks()`.

This does not implement v0.3, which requires the verifier to independently recompute recurrent/TTT contracts from the common frozen P3 artifact using verifier-owned selector rules.

Required:

- remove caller ownership of the P3 contract;
- load the frozen P3 artifact/PASS verifier identity and recompute the expected recurrent/TTT contract internally, preferably by reusing the verifier-owned selector constants/rule already frozen by P3/P4;
- add a regression where both envelopes and an external/self-consistent contract are forged together and must still FAIL.

### MEDIUM — selector path allowlist is still more permissive than the design

`tools/g0/verify_r09_b2_p5_full_config_diff.py:67-82`

For per-index differences under P3 `selector_keys` and `/resolved_config/optimizer/keys_to_select`, `_allowed()` accepts membership in the union/one side's selector set rather than requiring each backend's complete resolved selector field to equal its exact verifier-owned ordered list. This can admit a reordered or duplicated selector sequence in cases where the list lengths align.

Required: validate the complete selector/config-membership field per backend against the exact verifier-owned backend contract first; path-level diff allowlisting should then only describe the expected difference, not establish correctness.

## Positive observations

- canonicalization rejects non-finite floats and distinguishes callable FQNs;
- D005 trailing overrides are frozen in order to the exact two 100-update overrides;
- environment helper starts from the allowlist rather than overlaying the full parent;
- child rejects pre-imported experiment/Hydra state and checks CUDA did not become initialized;
- the supplement correctly tightened backend label, TTT switch, and local-history backend values.

These are good building blocks but are not sufficient to authorize the actual static export yet.

## Gate decision

`APPROVE_TO_REQUEST_P5_STATIC_EXPORT` is **not granted**.

No config export, `load_experiment_from_toml` execution, `launch`, `Config.validate`, `instantiate`, trainer/model/dataloader/optimizer/checkpoint construction, CUDA, `torchrun`, GPU, training, evaluation, inference, P5 closure, or B2-T is authorized by this review.
