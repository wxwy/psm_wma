# R09-B2 P4-v4 Execution Request `interpreter` v0.4 fixture-remediation review

## Verdict

`REQUEST_CHANGES`

Target:
- implementation/remediation: `3217d020818a1fcae26ae1064e4a83907dad29d9`
- request: `6043ad1433cac5c0da8618276e8bb6f142272abc`
- approved design: `be6260348f35d8606d11709fc1748c2b63690293`
- prior review: `7e8b8ff8ff6966a8ee978faa567492e652e6d1cd`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Accepted remediation

The prior fixture-matrix gap is substantially reduced. This commit adds identity-rehashed permanent negatives for:
- `realpath` and `realpath_sha256` record drift;
- host-Git symlink rejection;
- ambient `PATH` shadow irrelevance;
- 12-slot loader mutations for `FROZEN_STDLIB_LOADER`, request SHA, root, bootstrap relative path, bootstrap SHA, host-Git slot;
- old 11-slot, extra argv, direct exporter, and `-m` forms.

It also strengthens `verified_loader_argv()` by checking that the supplied request SHA matches the actual request bytes.

No new implementation-path blocker was found in the 12-slot bound-host-Git logic.

## Remaining closure blockers

### HIGH 1 — lexical-path retarget negative is still not implemented

The approved v0.4 fixture contract and prior review require a real lexical launcher retarget test, not only mutation of the frozen record fields.

Current remediation mutates `lexical_interpreter.realpath` / `realpath_sha256` in the request record. That proves record drift is rejected, but it does not prove this case:

1. create lexical launcher symlink `venv-python -> base-A`;
2. freeze the valid four-field lexical record;
3. replace/repoint the lexical symlink to `base-B` while keeping the original request record;
4. `validate_interpreter()` must fail specifically on `lexical interpreter differs`.

This is required because the frozen authority is intentionally lexical-path + resolved-target identity; actual retargeting is the threat model.

### HIGH 2 — recursive ELF dependency no-pathname-reopen fixture is still missing

The v0.4 design explicitly requires both:
- root host-Git object single-fd/no-reopen; and
- recursive dependency no-pathname-reopen.

The existing `test_host_git_root_uses_one_open_and_no_path_read` only proves the root Git executable is opened once. The closure walker still resolves and opens `PT_INTERP` / `DT_NEEDED` dependencies recursively, and no permanent test currently proves those dependency bytes are consumed from their no-follow fd without a later pathname re-read/reopen.

Required static CPU fixture:
- exercise `_host_git_closure()` over at least one real dependency;
- instrument dependency read path (e.g. `_read_canonical_regular_nofollow` / `os.open`) and prohibit `Path.read_bytes` for closure objects;
- prove each dependency's parsed/hash bytes are exactly the bytes returned from its bound no-follow fd, with no second pathname read used for authority.

## Scope

Only the two missing permanent CPU fixtures above are required. Do not broaden the implementation path unless a fixture exposes a real defect.

Still forbidden:
- real preflight;
- staging/materialization/candidate generation;
- record/refreeze/evidence publication;
- P5 export/compose or authority population;
- torchrun/GPU/CUDA;
- model/data/checkpoint I/O;
- training/eval/inference/B2-T/Local Memory training.
