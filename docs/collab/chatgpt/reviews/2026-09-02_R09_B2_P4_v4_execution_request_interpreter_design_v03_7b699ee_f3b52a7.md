# R09-B2 P4-v4 Execution Request `interpreter` v0.3 design review

## Verdict

`APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_INTERPRETER_STATIC_TOOLS`

Target:
- design: `7b699eef95257b90793cfd08940d53b85a6de884`
- request: `f3b52a7682257f05fae5c5f748479acf441bcb6b`
- prior ChatGPT review: `a20a42aa1a2e199d73ca8068927234a3dc0f5c4e`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## PASS — frozen lexical-interpreter identity is reused exactly

v0.3 no longer invents a replacement Python identity. `interpreter.lexical_interpreter` is the frozen provenance-v1.3 four-field record `{path,sha256,realpath,realpath_sha256}` and must compare exactly against `lexical_interpreter(Path(path))`.

This preserves the intended lexical-launcher semantics: the launcher may be a symlink; both launcher bytes and resolved-target bytes remain independently bound. Permanent CPU negatives are required for launcher-byte drift, resolved-target drift, and lexical-path retargeting.

## PASS — frozen verified-loader argv grammar is reused exactly

v0.3 requires `loader_argv` to be the full 11-slot argv produced by the existing `verified_loader_argv(...)` contract:

`[python_path,-I,-S,-B,-c,FROZEN_STDLIB_LOADER,request_abs,request_sha,root_abs,bootstrap_relative,bootstrap_sha]`

The validator must first satisfy `is_verified_loader_argv()` and then independently reconstruct the argv and compare all elements exactly. This closes the prior abbreviated-loader blocker and prevents a second launcher grammar.

Required permanent negatives include isolation-flag omission/reordering, frozen loader drift, root/bootstrap path drift, request/bootstrap SHA drift, direct exporter/script launch, `-m`, and extra argv.

## PASS — host Git authority is separated from source Git authority

`host_git` is explicitly treated as an external host-native TCB rather than pretending it is a tracked source-root Git blob. The design requires absolute canonical non-symlink executable identity, single-fd `O_NOFOLLOW` / `fstat` / single-read ELF SHA binding, bytes-derived ELF/recursive closure identity, no ambient PATH/which/shell lookup, and explicitly forbids candidate `host_git` from self-proving the source Git bootstrap authority.

Implementation must preserve that non-self-verifying ordering: source/bootstrap authority must already be established independently before the candidate host Git record is admitted.

## Implementation acceptance scope

Authorized next work is only:
- root static `interpreter` parser/validator implementation;
- stdlib CPU fixtures covering the v0.3 negative matrix;
- supporting static documentation.

The implementation must keep the existing execution-request unconditional hard-stop after static validation.

Still forbidden:
- real P4-v4 preflight execution;
- staging/materialization/candidate generation;
- record/refreeze/evidence publication;
- P5 authority population/update or export/compose;
- torchrun/GPU/CUDA;
- model/data/checkpoint I/O;
- training/eval/inference/B2-T/Local Memory training.
