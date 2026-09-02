# R09-B2 P4-v4 Execution Request `interpreter` static remediation review

## Verdict

`REQUEST_CHANGES`

Target:
- implementation: `077e7a73c51550045c6d334f55f56cc774bc7967`
- request: `5d450f483aaf05ed8e7d68caba62bee8217919c1`
- approved design: `7b699eef95257b90793cfd08940d53b85a6de884`
- prior ChatGPT review: `11df4fcc979d16ac610a56a20996f3ffdeecd4de`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Prior blockers status

The three blockers from `11df4fc` are closed in this remediation:
1. host Git root ELF SHA and recursive closure now reuse the same already-bound root fd/raw instead of reopening the root executable;
2. source Git checks now receive the already-validated absolute `host_git` path and no longer use ambient `git` for source authority;
3. permanent CPU regressions now cover lexical drift, closure drift, relative host Git, loader reordering, and root host-Git no-path-reopen.

## HIGH — runtime frozen loader still invokes ambient `git`

File: `tools/g0/r09_b2_interpreter_provenance.py`, `FROZEN_STDLIB_LOADER` / `verified_loader_argv()`.

The execution-request validator now correctly validates `host_git` first and uses that exact absolute executable for source/bootstrap verification. However the actual source frozen into the child `python -c` argv still contains:

`subprocess.check_output(['git','-C',str(root),'show','HEAD:'+relative])`

Therefore the child runtime does not consume the interpreter section's validated `host_git` authority. It performs a fresh executable lookup through ambient `PATH`, while the contract explicitly rejects PATH/which/shell lookup and unbound executables.

This creates a split authority model:
- parent/static source/bootstrap checks -> validated absolute `host_git`;
- actual verified-loader child -> ambient `git`.

Required remediation:
1. Make the runtime `FROZEN_STDLIB_LOADER` use the already-bound absolute host Git executable, not bare `git`.
2. Bind that absolute path into the frozen loader argv/request grammar in an unambiguous reviewed way. If this necessarily changes the previously frozen 11-slot v1.3 loader grammar, first publish a narrowly scoped provenance/loader contract addendum and obtain design approval rather than silently creating a second grammar.
3. Add a permanent CPU regression proving an ambient PATH shadow `git` is never invoked by the admitted loader path; only the bound absolute host Git may be used.
4. Keep direct exporter / `-m` / extra argv rejection and the existing unconditional hard-stop.

## Scope

Only CPU/static design/tooling remediation is authorized. No real preflight, staging/materialization, candidate generation, record/refreeze, P5 export/compose, torchrun/GPU/CUDA, model/data/checkpoint I/O, training/eval/inference, B2-T, or Local Memory training is authorized.
