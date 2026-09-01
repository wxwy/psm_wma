# R09-B2 P5 full resolved-config diff design v0.2 review

- Request: `77b313c47903e0a7c388c1e405bf19bdc637ad70`
- Design root: `f004e4d1869967659617f7c85e8b2c88342b1340`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **REQUEST_CHANGES**

## Findings

### HIGH — P3 common evidence identity and backend-specific contract are still contradictory in the diff rules

The v0.2 design correctly allows backend-derived selector/config-membership differences, but later states that `P1/P3 binding` must be equal value-for-value across recurrent and TTT.

That is not true for the already-closed P4 pair. The two D005 records intentionally share the same P3 artifact path/SHA, while `inputs.p3_inventory.backend_contract` is backend-specific:

- recurrent: recurrent selector keys and recurrent optimizer-membership SHA;
- TTT: TTT selector keys and TTT optimizer-membership SHA.

Therefore an implementation that follows the literal `P1/P3 binding ... must be equal` requirement will reject the canonical P4 pair, while an implementation that broadly exempts all P3 binding differences risks weakening the common-evidence binding.

Required design change: split the P3 contract explicitly into two classes.

1. **Must match exactly across backends:**
   - P3 artifact path;
   - P3 artifact SHA256;
   - P3 verifier/PASS evidence identity if carried in the P5 envelope;
   - common production source/Gitlink provenance.
2. **Must differ only according to the verifier-owned backend contract:**
   - `selector_keys`;
   - `optimizer_membership_sha256` / equivalent backend-specific selector contract;
   - any resolved-config selector fields directly derived from `PSM_R09_B1_TTT_ENABLED`.

The JSON-Pointer allowlist should name these backend-specific P3 paths explicitly rather than relying on the ambiguous phrase `P1/P3 binding`.

Add a permanent fixture using the actual P4 shape: same P3 path/SHA but different recurrent/TTT backend contract must PASS; changing P3 path/SHA on one side must FAIL; changing the backend contract to a non-verifier-owned value must FAIL.

## Accepted parts of v0.2

The previous production-semantics blockers are otherwise addressed sufficiently for implementation once the P3 rule above is clarified:

- exact D005 argv is parsed to recover TOML and trailing overrides, then production `load_experiment_from_toml` is used;
- recurrent and TTT compose in separate fresh canonical-interpreter subprocesses;
- the child uses the D005 cwd/PYTHONPATH and a fail-closed environment built from the D005 environment contract rather than overlaying the parent environment;
- the canonical grammar preserves the full config and gives deterministic identities for attrs/dataclass/container, callable FQN, Enum and path values, rejecting unsupported objects/interpolation residue;
- the artifact separates `effective_launch` from `resolved_config` and separates production source, exporter source and later evidence source;
- actual optimizer parameter membership remains bound to P3 rather than being invented as a Config field;
- implementation remains root-only static tooling and does not authorize config export execution, `Config.validate`, instantiate, trainer/model/dataloader/optimizer/checkpoint construction, CUDA, torchrun, GPU, training, evaluation or inference.

## Gate decision

`APPROVE_TO_IMPLEMENT_P5_STATIC_DIFF` is **not** granted yet.

Revise only the P3 common-vs-backend-specific binding rule and its negative fixtures, then resubmit the design. No config export or runtime execution is needed for this remediation.
