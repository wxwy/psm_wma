# R09-B2 P4-v4 preflight static closure review

## Request / implementation

- Request: `bef6ed8908ac836c3383d57d4341c588deca2e68`
- Implementation follow-up: `da6158e645d621fb69343135f7cd44a3131759a1`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Verdict

`REQUEST_CHANGES`

## Findings

### HIGH — real payload drift tests improved, but final closure path still incomplete

`da6158d` correctly replaces the previous minimal fake payload tests with P5 preflight payload fixtures for loader/runtime drift checks. This closes the previous concern that only mock payloads were tested.

However, the remaining closure proof still requires an unmocked end-to-end static admission regression through `stage_atomic_publication()` for every critical invariant.

Required permanent cases:

- full valid P4-v4/P5-valid pair -> PASS through `stage_atomic_publication()`;
- loader argv drift -> FAIL through admission;
- runtime sys.path drift -> FAIL through admission;
- token-only poison reuse -> FAIL through admission;
- run-root-only poison reuse -> FAIL through admission.

### HIGH — existing full pair admission evidence still needs real identity path coverage

The previous full pair test introduced `_path_identity` patching. This must be removed before closure. Path identity, run-root token binding, and staging identity must be exercised using real fixture paths.

## Positive observations

- Real P5 payload fixtures are now used instead of synthetic incomplete JSON for drift checks.
- Runtime sys.path and loader argv drift coverage moved closer to the actual P4/P5 grammar.
- Static-only scope is preserved; no execution/staging/refreeze/export/runtime authorization added.

## Gate decision

Not authorized:

`APPROVE_TO_CLOSE_P4_V4_PREFLIGHT_STATIC_TOOLS`

Allowed only:

- root static tooling changes;
- CPU-only regression tests.

Still prohibited:

- real preflight;
- staging;
- candidate materialization;
- record/refreeze;
- evidence publication;
- P5 authority update;
- GPU/training/B2-T.
