# R09-B2 P4-v4 Execution Request `authorities` v0.2 design review

## Verdict

`REQUEST_CHANGES`

Target:
- design: `cdbb43d41d36bb40674eebf085969b3b6aaf086b`
- request: `9ec066b23dd294c6707abdd026b611d03bb4f7f4`
- prior ChatGPT review: `44fec94b7418bf5d8972e927c14bf92e43fbe2bc`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Accepted remediation

The two v0.1 design blockers are conceptually closed:

1. The contract now explicitly models the authority as **historical D005 v2 evidence**, rather than pretending the historical pair is a current-source v4 pair.
2. Record raw-byte binding and verification semantic decoding are separated: recurrent/TTT records remain exact canonical JSON bytes, while the historical pretty-printed `verification.json` may be bound by exact raw SHA and then decoded for semantic checks.
3. Historical source and historical verifier Git-blob identity are explicitly separated from the current execution-request `entry/source` tuple.
4. Current request linkage is limited to the already closed environment projection grammar, rather than running the current verifier over historical records.

This is the correct authority model for the existing frozen evidence.

## HIGH 1 — historical Git blob lookup does not freeze consumption of the already-validated host Git executable

The design says `validate_authorities_pair(authorities, request, root)` obtains the historical verifier with `git show <historical_source.root_revision>:<historical_verifier.relative_path>`, and later states that the fixed Git-object lookup is the only allowed subprocess operation.

However, the contract does not explicitly require that this lookup use the **already validated absolute host Git executable** from the closed interpreter section. The function signature itself has no `git_executable` parameter, and the prose does not state the exact argv source such as `request["interpreter"]["host_git"]["path"]` after interpreter validation.

That leaves an implementation-permitted ambient `git` / PATH lookup, which would reopen the same authority split already eliminated in interpreter v0.4.

### Required design remediation

Freeze the TCB explicitly, for example semantically equivalent to:

- `request.interpreter.host_git.path` is the only admitted Git executable for the historical blob lookup;
- it must already have passed the closed `validate_host_git()` / interpreter authority before authorities validation consumes it;
- argv must be the exact absolute executable plus `-C <root> show <historical_revision>:<relative_path>` (or another explicitly frozen equivalent);
- no bare `git`, PATH lookup, `which`, shell, fallback, or self-verification is permitted;
- add permanent PATH-shadow / wrong-host-git fixtures.

Do not silently change the interpreter contract; consume its already-frozen authority.

## HIGH 2 — `verification.json` “exact expected check keys” are not actually frozen in the design

The design requires the decoded historical verification object to have the frozen verifier schema, `status="PASS"`, and “exact expected check keys” all true. But it never enumerates those exact keys or gives a canonical frozen object/key-set/hash from which implementation must derive them.

The existing historical verification contains more structure than just recurrent/TTT `record_digest` checks, including the pair-level matched checks and the historical verifier-specific check roster. Without freezing the exact nested key sets, implementation can choose its own interpretation of “expected”, creating a second verifier grammar.

### Required design remediation

Freeze the historical verification semantic grammar explicitly. At minimum specify exact nested key sets for:

- top-level verification object;
- `checks.recurrent`;
- `checks.ttt_fast_weight`;
- `checks.matched`;
- any other historical pair-level boolean check such as the frozen output-distinctness check if present in the bound artifact.

All required boolean values must be exactly `true`; added/missing/retyped keys must fail. Prefer a single frozen constant/object derived from the historical verifier/artifact rather than prose such as “expected check keys”. Add added/missing/false/non-bool fixtures for each level.

## Non-blocking confirmation

The historical-v2 model may intentionally keep the historical source tuple unequal to the current request source. The current request source remains independently protected by the already closed source section, while historical D005 semantics are cross-bound only through the closed environment projection. That scope separation is acceptable.

The design also correctly keeps `IMAGINAIRE_OUTPUT_ROOT` and `PYTHONPATH` ownership deferred to later run/runtime contracts and does not authorize refreeze or execution.

## Authorized next step

Design-only remediation for the two blockers above, then resubmit the new exact design SHA for independent review.

No real preflight, staging/materialization, candidate generation, record/refreeze, evidence publication, P5 authority/export/compose, torchrun/GPU/CUDA, model/data/checkpoint I/O, training/eval/inference, B2-T, or Local Memory training is authorized.
