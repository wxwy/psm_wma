# R09-B2 P4-v4 Execution Request `interpreter` v0.2 design review

## Verdict

`REQUEST_CHANGES`

Target:
- design: `e69f278b18664202b7c5c424401a13a31b33c320`
- current V2 review context: `77e9081262e4a47a9731f17177986fe2618e3b8f`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- prior ChatGPT review: `a936c7088986aac8ba5fa8ccb7fe29b76dc4adcc`

v0.2 improves the Git authority model: host Git is no longer fabricated as a source-root Git blob, and the design now treats Git as an absolute host-native ELF/closure TCB. However the two ChatGPT v0.1 blockers are not yet closed.

## HIGH 1 — frozen lexical-interpreter identity is still replaced instead of reused verbatim

Frozen interpreter provenance v1.3 defines the lexical interpreter identity exactly as:

`{path, sha256, realpath, realpath_sha256}`

`lexical_interpreter()` intentionally allows a lexical launcher that resolves to another executable and binds both lexical bytes and resolved-target bytes. `verified_loader_argv()` consumes that exact record.

v0.2 instead defines top-level fields:

`python_path, python_payload_sha256, python_base_path, python_base_sha256, ...`

and globally states that paths are `strict-resolved, non-symlink regular file`. This still changes the frozen identity semantics. In particular a valid lexical venv launcher may be a symlink; requiring `python_path` itself to be strict-resolved/non-symlink collapses or rejects the lexical identity that provenance v1.3 deliberately preserves.

Required remediation:
1. Reuse the frozen lexical interpreter record verbatim, preferably as an exact nested object such as:
   `python={path,sha256,realpath,realpath_sha256}`.
2. Require recomputation equivalence:
   `lexical_interpreter(Path(python.path)) == python`.
3. Do not require the lexical launcher path itself to be non-symlink or equal to realpath.
4. Any venv payload/base/cfg/lock/RECORD authority may be additive, but cannot replace or rename the frozen record.
5. Permanent CPU negatives: lexical launcher bytes drift, resolved target drift, and lexical path retargeted to a different realpath.

## HIGH 2 — loader grammar remains an abbreviated second grammar

Frozen provenance v1.3 only admits argv equivalent to `verified_loader_argv()`:

`<python> -I -S -B -c <FROZEN_STDLIB_LOADER> <request_abs> <request_sha> <root_abs> <bootstrap_relative> <bootstrap_sha>`

v0.2 still defines `loader_args` as:

`-I,-S,-B,-c,<bootstrap digest>,<absolute request path>,<64-hex request SHA>`

This still omits/replaces required frozen fields and ordering:
- literal `FROZEN_STDLIB_LOADER` source after `-c`;
- `root_abs`;
- `bootstrap_relative`;
- the existing bootstrap SHA position/semantics.

Therefore v0.2 still cannot be validated by the frozen `verified_loader_argv()` / `is_verified_loader_argv()` contract and would create a second launcher grammar.

Required remediation:
1. Do not define an abbreviated `loader_args` grammar.
2. Freeze the exact inputs required to reconstruct the existing `verified_loader_argv()` result: exact lexical interpreter record, request abs path/SHA, source root abs path, bootstrap relative path/SHA, and frozen loader source identity.
3. Static validator must reconstruct the exact frozen argv and compare byte/string-for-string against the request binding.
4. Permanent negatives: changed `FROZEN_STDLIB_LOADER`, missing/reordered `-I/-S/-B/-c`, root drift, bootstrap-relative drift, bootstrap SHA drift, request path/SHA drift, direct script/exporter, `-m`, and extra argv.

## Accepted improvement

The host Git authority direction is now acceptable in principle: absolute non-PATH executable, bytes-derived ELF/closure TCB, no fabricated source-root Git blob. Keep that direction, but bind it independently from the Python lexical-interpreter record.

## Scope

Only interpreter design/static remediation is authorized. Do not implement v0.2 as written.

Still forbidden:
- real preflight
- staging/materialization
- candidate generation
- record/refreeze
- P5 export/compose or authority population
- torchrun/GPU/CUDA
- model/data/checkpoint I/O
- training/eval/inference/B2-T/Local Memory training
