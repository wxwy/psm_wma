# ChatGPT Independent Review — R09-B2 P4-v4 Execution Request FULL admission v0.1

- Review target design: `f1d6554e0b428ecfbdd92f6a0cfe633e5f5cafc1`
- Formal request / ledger HEAD: `48159fd776b393e065707e9faaebc41677155d61`
- Previous ChatGPT anchor: `4f0ba5e0cc3256d6d3931ded3895526cf2cedd69`
- Gitlink independently confirmed at request HEAD: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Scope: design only; no real request creation, preflight, run/candidate/staging materialization, record/refreeze, evidence publication, P5 export/compose, GPU/CUDA, model/data/checkpoint I/O, training/eval/inference.

## Verdict

`REQUEST_CHANGES`

The full-admission architecture is directionally correct: canonical root request, deterministic validation order, one validated host-Git path reused across source/interpreter/authorities, authorities as the sole environment↔historical-D005 binding route, and permanent `main()` hard-stop. No nested static section is reopened.

Two design-level issues must be corrected before implementation authorization.

## Blocker 1 — source-root “same validated object identity” is impossible under the already-closed source interface

The design requires the `root` and `git_path` passed through source/interpreter/authorities to be “the same invocation already-validated objects”, and requires a spy fixture proving source/interpreter/authorities receive the same root object.

However, the frozen `validate_source(value, entry, git_executable) -> None` interface does not accept a root `Path` object and does not return one. It creates `root = Path(value["root"])` internally, validates it, then discards that local object. Therefore the full layer cannot reuse the exact same root object in `validate_authorities_pair(...)` without modifying the already-closed source validator contract, which contradicts the v0.1 statement that full admission only composes existing sections and does not redefine them.

Required remediation: freeze value/canonical-path binding instead of impossible object identity for source root. Recommended exact contract:

1. call `validate_source(value["source"], value["entry"], git_path)` unchanged;
2. after it returns, construct `source_root = Path(value["source"]["root"])` from the same parsed immutable request;
3. pass that single `source_root` object to `validate_authorities_pair(...)`;
4. fixture proves `git_path` object identity is reused across source/interpreter/authorities, while source-root binding is proved by exact canonical value / same parsed `source.root`, not by claiming identity with `validate_source()`'s inaccessible local `Path` object.

Do not change `validate_source`'s signature/return behavior merely to satisfy this full-layer fixture.

## Blocker 2 — subprocess fixture rule conflicts with inherited source validation unless scoped to “no new full-layer subprocess path”

The design says CPU fixtures reject `subprocess` except the authorities historical verifier lookup. But the already-closed `validate_source()` performs fixed host-Git calls through `_git()` / `subprocess.run` for clean-root, revision, Gitlink, tracked-file and blob checks. A full valid route that genuinely invokes source validation therefore cannot literally satisfy a blanket “no subprocess except authorities” rule.

Required remediation: define the fixture boundary precisely. Either:

- mock the closed source/interpreter/authorities lower-level I/O and prove the **full admission layer introduces no new subprocess path**, while still spying that the correct closed validators are called in order; or
- explicitly allow the already-frozen source Git subprocess calls plus the authorities historical Git lookup, while forbidding any additional subprocess / P5 / child / torchrun path.

The preferred option is the first because this task is route-only static composition.

## Accepted design points

- Canonical JSON, exact `REQUEST_KEYS`, schema version and frozen `execution_contract` remain admission prerequisites.
- Proposed validation order is compatible with existing dependencies: entry → host Git → source → interpreter → run → candidates → backends → authorities.
- `validate_authorities_pair(...)` is the correct unique environment↔historical-D005 route; full admission should not call `validate_environment_pair()` or `verify_d005_pair()` separately.
- `main()` currently reads the request once, checks request SHA, calls `load_execution_request(raw)`, then unconditionally raises `RuntimeError("P4-v4 execution requires a separately reviewed frozen execution request")`; preserving this is correct.
- No real future run/candidate/staging path may be created or opened by full admission.

## Required next step

Submit a full-admission v0.2 design that fixes the two wording/interface contradictions above. No implementation is authorized by this review.
