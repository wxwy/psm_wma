# R09-B2 P5 full resolved-config diff design v0.3 review

- Request: `5eb3ca9c6e91e1cf268116d55a51d8e146398ecb`
- Design root: `a1aa4ff58c967303b3daa5fa573f6894132b123f`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **APPROVE_TO_IMPLEMENT_P5_STATIC_DIFF**

## Findings

No blocking findings within the requested P3-binding scope.

The v0.3 design resolves the remaining ambiguity from v0.2 by separating P3 common evidence identity from backend-specific contract fields:

1. P3 artifact path/SHA and PASS/provenance identity must match across recurrent and TTT and remain bound to the common approved attempt-6 evidence.
2. `backend_contract.selector_keys` and `backend_contract.optimizer_membership_sha256` are the only P3 binding values allowed to differ by backend.
3. Those backend-specific values are not accepted merely because they differ; the verifier must independently recompute/check each side against the verifier-owned recurrent or TTT contract from the common P3 artifact.
4. Missing/extra backend-contract fields, cross-wiring recurrent and TTT contracts, non-verifier-owned selector/membership values, or any P3 path/SHA/PASS-identity mutation must fail.
5. The permanent CPU fixtures explicitly include the real P4 shape: same P3 path/SHA plus different correct backend contracts must PASS, while the corresponding mutations must FAIL.

This removes the v0.2 contradiction between requiring common P3 evidence equality and allowing the backend-specific selector/membership contract to differ.

## Gate decision

`APPROVE_TO_IMPLEMENT_P5_STATIC_DIFF` is granted narrowly for root-side implementation under `tools/g0/` of the P5 exporter, verifier, and standard-library/CPU fixture tests according to the v0.2 + v0.3 design contract.

This approval does **not** authorize static config export execution, `launch`, `Config.validate`, `instantiate`, trainer/model/dataloader/optimizer/checkpoint construction, CUDA, `torchrun`, GPU, training, evaluation, inference, P5 closure, or B2-T. After implementation review, any real static export still requires a separate execution approval.
