# R09-B2 P4-v4 Execution Request `interpreter` v0.4 design review

## Verdict

`APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_INTERPRETER_STATIC_TOOLS`

Target:
- design: `be6260348f35d8606d11709fc1748c2b63690293`
- request: `5e35840c072f1231c698784477d8764060964564`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- prior ChatGPT review: `f79488df764b9700bcf361ebca6c37db92b57c6e`

## Review result

The prior single blocker is closed at design level.

v0.4 explicitly removes the parent/child split Git authority by extending the only admitted verified-loader grammar from 11 to 12 slots:

`[python_path,-I,-S,-B,-c,FROZEN_STDLIB_LOADER,request_abs,request_sha,root_abs,bootstrap_relative,bootstrap_sha,host_git_abs]`

The final `host_git_abs` must byte-equal `interpreter.host_git.path`, which is already independently established as an absolute strict-resolved non-symlink executable with same-fd `O_NOFOLLOW` current bytes and bytes-derived recursive ELF closure. The frozen child loader must use that path as the sole Git executable for bootstrap `git show`; ambient `PATH`, `which`, shell lookup, relative executable lookup, and bare `git` fallback are explicitly forbidden.

This correctly makes parent source Git verification, parent bootstrap verification, and child bootstrap Git verification consume the same already-bound host Git authority.

The design also correctly requires synchronized updates of:
- `FROZEN_STDLIB_LOADER`;
- `verified_loader_argv()`;
- `is_verified_loader_argv()`;
- permanent CPU fixtures rejecting the old 11-slot grammar, slot drift/reorder/extra/missing fields, host-Git drift, direct exporter, and `-m` launch.

No new design blocker was found. The Gitlink at the request commit remains exactly frozen.

## Authorized scope

Only implementation of the v0.4 root static parser/validator and stdlib CPU fixtures is authorized.

The implementation review must prove at minimum:
1. child loader indexes the 12th slot and never invokes bare `git`;
2. loader construction and validation both bind `argv[11] == interpreter.host_git.path` exactly;
3. old 11-slot loader argv permanently fails;
4. PATH shadow cannot influence parent source/bootstrap Git or child loader Git;
5. host Git remains non-self-authorizing: no Git command is run before its own ELF/current-byte/closure validation completes;
6. all previously frozen lexical-interpreter and host-Git negative fixtures remain in force.

Still forbidden:
- real preflight execution;
- staging/materialization/candidate generation;
- record/refreeze/evidence publication;
- P5 authority/export/compose;
- torchrun/GPU/CUDA;
- model/data/checkpoint I/O;
- training/eval/inference/B2-T/Local Memory training.
