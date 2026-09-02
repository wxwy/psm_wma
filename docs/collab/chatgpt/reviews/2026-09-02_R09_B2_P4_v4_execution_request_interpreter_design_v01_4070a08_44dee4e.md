# R09-B2 P4-v4 Execution Request `interpreter` v0.1 design review

## Verdict

`REQUEST_CHANGES`

Target:
- design: `4070a086d18740e73185829fd74fd43a493355dd`
- request: `44dee4ed63fcbb8efd49a1e497cf4aa9c1607b8c`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## HIGH 1 — v0.1 replaces the frozen lexical-interpreter identity instead of reusing it

The already-frozen interpreter provenance v1.3 implementation contract defines the lexical interpreter record as exactly:

`{path, sha256, realpath, realpath_sha256}`

and `lexical_interpreter()` intentionally binds both the lexical launcher bytes and the resolved target bytes. `verified_loader_argv()` rejects any interpreter record with a different key set.

Current v0.1 instead proposes `python_path, python_git_blob_sha256, python_current_sha256` and requires `python_path` to be strict-resolved / non-symlink. That is not an additive execution-request binding: it changes the already-approved identity model, discards `realpath` / `realpath_sha256`, and can reject a valid lexical venv launcher merely because the launcher is a symlink.

Required:
1. Do not invent a replacement Python identity schema.
2. Reuse the frozen lexical interpreter record verbatim: `path, sha256, realpath, realpath_sha256` (or embed it as an exact nested object).
3. The execution request may add source/install authority around that record, but must prove `lexical_interpreter(Path(path)) == frozen_record`; it must not require the lexical launcher itself to be non-symlink or silently collapse it to realpath.
4. Add permanent CPU negatives for lexical launcher drift, resolved-target drift, and lexical-path→different-realpath retargeting.

## HIGH 2 — `loader_args` grammar is incompatible with the frozen verified-loader argv

Frozen provenance v1.3 admits only the loader grammar built by `verified_loader_argv()`:

`<python> -I -S -B -c <FROZEN_STDLIB_LOADER> <request_abs> <request_sha> <root_abs> <bootstrap_relative> <bootstrap_sha>`

Current v0.1 describes `loader_args` as only:

`-I,-S,-B,-c,<bootstrap digest>,<absolute request path>,<request SHA>`

This omits/replaces required frozen fields:
- literal `FROZEN_STDLIB_LOADER` source passed to `-c`;
- verified root absolute path;
- bootstrap relative path;
- bootstrap SHA position/semantics.

It therefore cannot be validated by the existing `is_verified_loader_argv()` / `verified_loader_argv()` contract and risks creating a second launcher grammar.

Required:
1. Freeze interpreter section by reference to the exact existing `verified_loader_argv()` grammar, not a new abbreviated argv encoding.
2. The request should bind all loader inputs needed to reconstruct and compare the exact argv: lexical interpreter record, request path/SHA, root, bootstrap relative path/SHA, and the frozen loader source identity.
3. Permanent negatives must include missing/reordered isolation flags, changed `FROZEN_STDLIB_LOADER`, root/bootstrap path drift, direct exporter/script, `-m`, extra argv, request/bootstrap SHA drift.

## Git executable note

The design also says `git_path` is under source root and is verified using source-revision `git show` bytes. This must be reconciled with the actual frozen provenance model before implementation. If Git is an external executable rather than a tracked root artifact, source Git blob authority cannot be fabricated for it. Freeze the actual authority source (tracked install artifact, external immutable executable identity, or separately reviewed install provenance) explicitly.

## Scope

Only design/static remediation is authorized. Do not implement this v0.1 as written.

Still forbidden:
- real preflight
- staging/materialization
- candidate generation
- record/refreeze
- P5 export/compose or authority population
- torchrun/GPU/CUDA
- model/data/checkpoint I/O
- training/eval/inference/B2-T/Local Memory training
