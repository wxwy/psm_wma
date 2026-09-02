# R09-B2 P4-v4 execution-request static foundation review

## Request / implementation

- Request commit: `7916b36b01d88ff424ce549d4235f412c2dd87c9`
- Implementation commit: `add23d4dbd053e42cf1bdd113d6737b9454d3f0e`
- Parent design review: `13ed5310b89a0df3a10a10c7b31d2e97a7c27bc2`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Verdict

`APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_STATIC_TOOLS`

This is a narrow static-tooling authorization only. It is **not** `APPROVE_TO_EXECUTE_P4_V4_PREFLIGHT_CPU_ONLY`.

## Findings

### PASS — current entry has no reachable execution path

`tools/g0/r09_b2_p4_v4_execution_preflight.py` currently performs only:

1. argparse parsing of `--request` and `--request-sha256`;
2. regular-file / non-symlink admission for the request path;
3. SHA256 recomputation over current request bytes;
4. fail-closed rejection on SHA mismatch;
5. unconditional `RuntimeError` after SHA match.

There is no JSON parsing, staging creation, candidate creation, materialization, network access, torch import, CUDA/GPU access, model/data/checkpoint I/O, record/refreeze, P5 export/compose, training, evaluation, or inference path.

### PASS — CPU regression proves matching SHA still hard-stops

`tools/g0/test_r09_b2_p4_v4_execution_preflight.py` covers both SHA mismatch => FAIL and SHA match => unconditional hard-stop. Thus the current revision cannot accidentally turn a valid SHA into execution authorization.

## Requirements for the authorized next static step

Before any future execution request can be approved, static tooling must freeze and independently validate at least:

- exact execution-request top-level schema and no unknown/missing keys;
- exact entry/tool Git blob + current-byte identity;
- exact source revision and Gitlink/submodule identity;
- exact request SHA and canonical bytes;
- exact lexical interpreter identity and argv grammar;
- exact empty/sanitized environment and forbidden inherited variables;
- exact new run-root / candidate-root identities and freshness rules;
- exact dual-backend request identities, tokens, output paths, and pair invariants;
- P1/P3/P5 frozen authority identities;
- explicit no-network / no-GPU / no-torch / no-model-data-checkpoint contract;
- one-shot failure poison / no cleanup / no repair / no retry semantics.

Permanent CPU negatives should include symlink request, malformed/unknown/missing request fields, source/tool drift, wrong Gitlink, invalid interpreter/env/root identities, identity reuse, and SHA-preserving caller forgeries where verifier-owned frozen facts disagree.

## Gate decision

Authorized now:

- root `tools/g0/r09_b2_p4_v4_execution_preflight.py` static request parser/validator development;
- corresponding stdlib/CPU-only tests.

Still unauthorized:

- real P4-v4 preflight execution;
- staging or candidate materialization;
- record/refreeze or evidence publication;
- writing real `AUTHORIZED_P4_V4_EVIDENCE`;
- P5 export/compose;
- torchrun/distributed/CUDA/GPU;
- model/data/checkpoint I/O;
- training/evaluation/inference;
- B2-T or Local Memory training.
