# ChatGPT Independent Review — R09-B2 P4-v4 Execution Request `entry` Contract v0.7

## Verdict

`APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_ENTRY_STATIC_TOOLS`

## Reviewed objects

- Root design: `99562b62366134d87c192b7258ef0a9365a18f8f`
- Review request: `a39642bbe16b1c9e2a98c3042a99d8fef924a590`
- Frozen submodule/Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Prior blocking review: `1bf0d3bf65364162bb885bca0646cd880b212dba`
- Design file: `docs/build/PSM-WMA_R09_B2_P4_v4_execution_request_entry_design_v0.7_2026-09-02.md`

## Findings

### PASS — prior root revision width blocker is closed

v0.7 correctly separates Git object identity from SHA256 fields:

- `root_revision`: exactly 40 lowercase hex, matching this repository's current Git object format;
- `git_blob_sha256`: exactly 64 lowercase hex;
- `current_sha256`: exactly 64 lowercase hex;
- `identity_sha256`: exactly 64 lowercase hex.

The prior v0.6 defect that required a 64-hex `root_revision` is therefore closed.

### PASS — entry grammar remains exact and non-self-authorizing

The contract freezes the literal entry path:

`tools/g0/r09_b2_p4_v4_execution_preflight.py`

The entry object has an exact key set and string-only values. `identity_sha256` is computed from canonical JSON after removing its own field. The design explicitly states that accepting the 40-hex revision grammar is not Git authority.

The later `source` section remains responsible for independently proving:

- revision resolvability;
- root Gitlink;
- entry Git blob bytes;
- current entry bytes;
- Git blob/current-byte equality.

The request, current HEAD, or entry section cannot self-authorize those facts.

### PASS — permanent CPU negative coverage is appropriately frozen

The implementation must preserve tests covering at least:

- valid 40-hex revision accepted at grammar level;
- 64-hex revision rejected;
- 39/41-character revision rejected;
- uppercase revision rejected;
- non-hex revision rejected;
- extra entry key rejected;
- non-literal tool path rejected;
- SHA / identity drift rejected;
- existing single `O_NOFOLLOW` fd read regression remains PASS;
- the exact raw bytes used for request SHA remain the bytes parsed;
- immutable execution-contract regression remains PASS.

## Authorized scope

Only the following work is authorized:

- root static parser/validator implementation for the v0.7 `entry` grammar;
- stdlib CPU tests for that grammar and the frozen regressions above.

## Explicitly not authorized

This review does **not** authorize:

- real P4-v4 preflight execution;
- staging/materialization;
- candidate creation;
- record/refreeze;
- evidence publication;
- P5 authority updates;
- P5 export/compose;
- torchrun;
- GPU/CUDA;
- model/data/checkpoint I/O;
- training/evaluation/inference;
- B2-T;
- Local Memory training.

The `source`, `interpreter`, `environment`, `run`, `candidates`, `backends`, and `authorities` nested contracts remain separate future review objects.
