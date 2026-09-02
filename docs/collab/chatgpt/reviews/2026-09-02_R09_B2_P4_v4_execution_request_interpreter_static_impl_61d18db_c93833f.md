# R09-B2 P4-v4 Execution Request `interpreter` static implementation review

## Verdict

`REQUEST_CHANGES`

Target:
- implementation: `61d18db3894ca65f68740aa0fac86e5f307b7c49`
- request: `c93833f1cdda73743ed1cc23e8bc93c03d4ea33a`
- approved design: `7b699eef95257b90793cfd08940d53b85a6de884`
- prior ChatGPT design approval: `c4a9b09e5a3582a094e0dc64cf490bace4c2378a`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## HIGH 1 — host Git ELF SHA and closure are not bound to the same single-fd bytes

`validate_interpreter()` first reads `host_git.path` with `_read_strict_regular_nofollow()` and computes `elf_sha256` from `git_raw`. It then calls `_host_git_closure(git_path, git_raw)`.

However `_host_git_closure()` immediately discards the supplied top-level `raw` by reopening `current` through `_read_strict_regular_nofollow()` before parsing it. Therefore:

1. ELF SHA is bound to fd/raw A;
2. pathname may change;
3. closure is recomputed from a second open/raw B.

This violates the approved v0.3 contract that the host Git executable uses single-fd `O_NOFOLLOW` + same-fd `fstat` + single raw for its ELF identity/closure authority.

Required remediation:
- for the root host Git object, consume the already-bound `git_raw` directly; do not reopen `host_git.path` inside `_host_git_closure()`;
- recursively discovered closure objects may each be opened once with no-follow/fstat and then parsed from those exact bytes;
- add a permanent regression proving the top-level host Git path is opened exactly once and that closure parsing consumes the same raw used for `elf_sha256`.

## HIGH 2 — source Git authority is still established with ambient `git` before `host_git` is validated

`load_execution_request()` currently executes:

`validate_entry -> validate_source -> validate_interpreter`.

`validate_source()` uses `_git()`, whose command is the ambient executable name `git` resolved through process `PATH`. Only afterwards does `validate_interpreter()` independently validate the request's absolute `host_git.path`.

Consequences:
- a PATH-shadow `git` can supply fake `rev-parse`, `status`, `ls-tree`, `show`, and `ls-files` results during source authority validation;
- successful validation of `host_git` afterwards does not retroactively prove those source Git operations used that executable;
- the request-bound host Git TCB therefore is not actually the Git authority consumed by the source section.

This is exactly the boundary left open by source closure: execution must not proceed until Git executable authority is frozen/consumed.

Required remediation:
- validate the non-Git-derived `host_git` executable identity first;
- perform authoritative source Git operations with that exact absolute executable path, not ambient `git`;
- restructure section orchestration as needed so source Git authority is finalized only after the trusted host Git executable is established;
- ensure bootstrap/loader static checks do not silently reintroduce ambient-PATH Git as an authority;
- add a PATH-shadow fixture where a fake `git` would make source validation pass if ambient lookup were used; the validator must ignore/reject the shadow and consume only the bound host Git executable.

## HIGH 3 — implementation closure evidence does not cover the permanent v0.3 interpreter fixtures

The new execution-preflight test file adds only two interpreter-specific test methods:
- positive interpreter admission;
- combined outer identity / truncated argv / host ELF digest drift.

The existing provenance tests cover basic lexical-symlink preservation and a basic verified-loader grammar, but do not establish the complete v0.3 permanent set claimed by the closure request.

Still missing as explicit permanent interpreter-request authority regressions include at least:
- lexical launcher bytes drift with outer identity recomputed, proving failure reaches lexical authority rather than outer identity;
- resolved-target bytes drift;
- lexical path retargeted to a different realpath;
- host Git symlink/replacement;
- host Git closure drift;
- ambient PATH shadow / no self-verification;
- loader flag reorder, FROZEN_STDLIB_LOADER drift, root drift, bootstrap-relative drift, bootstrap SHA drift, request SHA drift, extra argv, direct exporter / `-m` rejection at the interpreter-request validator boundary;
- no pathname reopen for host Git top-level bytes.

The stated `15/15 + 16/16` total is not sufficient evidence that the approved interpreter-request contract's permanent negative matrix is closed.

## Positive findings

The implementation correctly:
- embeds the exact four-field frozen lexical-interpreter record;
- restores the full 11-slot `verified_loader_argv()` grammar and compares rebuilt argv exactly;
- uses absolute strict-resolved host Git path and bytes-derived ELF metadata/recursive closure logic;
- preserves the final unconditional execution hard-stop;
- does not authorize or execute staging, preflight, P5 export/compose, GPU, model/data/checkpoint I/O, training/eval/inference, B2-T, or Local Memory training.

## Authorized next step

CPU/static remediation only:
1. same-raw host Git closure binding;
2. eliminate ambient-Git authority from source/loader static validation by consuming the bound host Git executable;
3. complete permanent interpreter-request CPU fixtures;
4. submit a new implementation SHA for independent closure review.

No real P4-v4 preflight or staging is authorized.
