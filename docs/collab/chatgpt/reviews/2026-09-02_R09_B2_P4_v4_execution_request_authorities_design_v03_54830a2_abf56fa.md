# R09-B2 P4-v4 Execution Request `authorities` v0.3 design review

## Verdict

`APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_AUTHORITIES_STATIC_TOOLS`

Target:
- design: `54830a20cab3e2d9995781faf1244684c6bd02d0`
- request: `abf56fabb8ef114ca55ee7c134a9fc9061be1458`
- previous ChatGPT review: `203b252b7dce5404693e1af6d055513b6719a0c0`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Review result

The two blockers from v0.2 are closed.

1. Historical Git-object lookup is now explicitly inside the already-closed interpreter trust boundary. `validate_authorities_pair(..., git_executable)` must receive the same validated absolute, non-symlink `request.interpreter.host_git.path`, and the only admitted lookup argv is exactly `[git_executable, "-C", root, "show", historical_revision + ":" + historical_verifier_relative_path]`. Bare `git`, PATH/which/shell/fallback, a different Git executable, or a different `-C` root are rejected.

2. Historical `verification.json` semantic grammar is now fully frozen rather than left as an implementation-defined “expected keys” concept. The design fixes the top-level roster, `checks` roster, `matched` roster, both backend rosters, boolean typing/value requirements, schema version, status, and `distinct_outputs`.

The historical-authority model is also internally coherent with the frozen artifacts inspected during review:
- records are historical D005 v2 records and bind historical source `ddb4e0eae97fb545d5239c1ddb6d4387170f3780` plus the frozen Gitlink;
- historical verification is intentionally pretty-printed and is byte-bound first, then semantically decoded;
- current request source is not falsely equated with the historical source;
- the only historical-to-current semantic bridge is the already-closed environment projection/object/P3 grammar;
- current `verify_pair()` / current-source `validate_environment_pair()` are explicitly forbidden as proof of the historical pair.

No new design blocker was found.

## Implementation review requirements

Static/CPU implementation review must prove at least:
- exact schema and self-identity rejection for `authorities` and `d005_pair`;
- fixed historical artifact paths/bytes and historical source/verifier bindings;
- root-relative, no-`..`, no-symlink, regular-file, single-fd/single-raw reads with no pathname reopen;
- exact host-Git argv and PATH-shadow/bare-Git/different-Git rejection;
- historical verifier blob SHA binding from the historical revision;
- record canonical JSON/backend/schema/status/self-digest checks;
- exact pretty verification byte binding plus every frozen nested roster/type/value negative;
- swap/duplicate bindings and source/verifier drift rejection;
- current request environment projection/effective/native/P3 cross-binding using the already frozen environment constants, without a second allowlist/P3 mapping;
- ambient environment independence;
- existing entry/source/interpreter/environment regressions remain green.

Authorization is static tooling and stdlib CPU fixtures only. No current-source D005 refreeze, real preflight, staging/materialization, candidate generation, record/refreeze, evidence publication, P5 export/compose, torchrun/GPU/CUDA, model/data/checkpoint I/O, training/eval/inference, B2-T, or Local Memory training is authorized.
