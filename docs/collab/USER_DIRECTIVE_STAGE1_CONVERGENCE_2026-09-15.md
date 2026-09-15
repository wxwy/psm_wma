# User Directive — Stage-1 convergence and no-more-discovery-in-C

Date: 2026-09-15
Owner intent: accelerate the critical path to Stage-1 materialization -> source-evidence closure -> single-GPU smoke -> training.

This is a **user execution directive**, not a formal review verdict and not a request to create another lateral governance Gate.

## Why this directive exists

Recent Stage-1 request construction repeatedly failed because requirements were discovered incrementally after implementation/review had already started. The recurring pattern has been:

1. implement the latest reviewer request;
2. submit a new exact pair;
3. discover another inherited constraint;
4. open another remediation cycle;
5. sometimes consume one-shot C authority before the missing constraint is discovered.

The goal now is to stop reviewer-driven requirement discovery and make Codex close the entire inherited contract before the next construction attempt.

## Required execution strategy

### 1. Build one complete requirement matrix before the next construction

Aggregate all requirements inherited from the active Stage-1 v0.5/v1.7/V18/V21/V31 line and all currently relevant ChatGPT/MM/DS `REQUEST_CHANGES` into one matrix.

Every row must include:

- requirement ID;
- source/version that introduced it;
- exact frozen expected literal/value/identity;
- implementation location;
- positive test;
- foreign-but-self-consistent negative test where applicable;
- PASS/FAIL.

Do not submit the next implementation/construction review until the matrix is 100% PASS.

### 2. Collapse all Stage-1 pre-C truth into one machine-readable ContractV05

The complete contract must explicitly bind at least:

- P0 source objects: root/path/blob/raw length/SHA;
- P1 injected objects: all eight exact name/length/SHA identities;
- ReplayBinding: all scalar fields, parser argv items, eight parser rows, eight source rows;
- `.git` identity/config/local V2;
- remote V2 query and extracted advertised V2 identity;
- local/remote fixed authority-ref absence;
- exact six-key environment;
- owner-FD contract;
- exact cwd/index/evidence/output paths;
- exact designated absence paths;
- consumer callable/capability identity and ABI;
- final JSON/Markdown/patch canonical bytes and identities;
- post-write verifier identity and exact readback requirements.

These truths must not remain scattered across historical docs with implicit inheritance.

### 3. Identity checks must prove equality to frozen truth, not self-consistency

Forbidden pattern:

`declared_sha == sha(actual)`

when `declared_sha` is supplied by the same untrusted object.

Required pattern:

`actual == frozen_expected`

or equivalent comparison against an independently frozen literal/identity.

For every identity-bearing field that could be replaced with a foreign-but-self-consistent value, add a negative test proving that such substitution fails before the consumer is invoked.

### 4. Run one complete non-consuming rehearsal before requesting construction authority

The rehearsal must cover the complete future path in memory / CPU-static form:

`ContractV05`
`-> exact final JSON bytes`
`-> exact final Markdown bytes`
`-> exact patch bytes/text`
`-> sealed consumer callable/capability`
`-> full typed closure`
`-> simulated exactly-once apply`
`-> byte-for-byte readback verification`

All positive and negative cases must PASS before another real C attempt is requested.

### 5. C is a transaction commit phase, not a discovery phase

After C begins, no new discovery or interpretation is allowed.

C must be reduced to exactly:

`freshness snapshot -> exactly one opaque write -> byte-for-byte readback -> hard stop`

The following are forbidden inside C:

- name/callable discovery;
- path inference;
- schema construction or repair;
- dynamic import lookup;
- string/patch generation;
- deciding identities;
- resolving inherited requirements;
- adding new fields or observations.

If any of these are still necessary, pre-C is not complete and C must not start.

### 6. Stop opening one Gate per newly discovered field

Do not create a new lateral Gate for each path, field, hash, callable, bytes/str seam, or review comment.

If a missing item is found before C, update the requirement matrix, sweep the entire class of related fields for analogous omissions, fix them together, rerun the complete rehearsal, and then submit one consolidated formal SHA.

Only create a new Gate when there is a genuinely different execution authority boundary or a material safety/reproducibility boundary that cannot be represented inside the existing ContractV05/pre-C closure.

### 7. Keep formal implementation SHA immutable after review submission

Once an implementation commit is submitted as the formal target, do not rebase or replace it merely to preserve `SESSION.md`, `TODO.md`, Inbox, or review-ledger history.

Coordination/review records should be append-only commits after the formal implementation commit. The formal implementation pair should remain immutable unless implementation content actually changes.

### 8. Status reporting should stay on the critical path

For user-facing status, report only:

- requirement matrix / complete pre-C rehearsal: PASS or not;
- exact request pair generated: yes/no;
- Stage-1 materialization: PASS/FAIL/not started;
- source-evidence receipt closure: complete/not complete;
- single-GPU smoke: started/result;
- training: started/not started.

Do not treat additional provenance-document churn as project progress unless it removes a concrete blocker on this path.

## Immediate expected next action

Use the current `stage1_v17_pre_c_rehearsal.py` work as the base; do not restart the implementation.

Before the next exact-pair review/construction attempt:

1. create/check the complete requirement matrix;
2. verify ContractV05 covers every inherited requirement above;
3. run a systematic foreign-but-self-consistent drift matrix across all identity-bearing fields;
4. run the complete non-consuming end-to-end rehearsal;
5. only after all of the above PASS, request closure/construction authority.

The objective is not to satisfy only the most recent reviewer comment. The objective is that the next review has no hidden inherited Stage-1 contract item left to discover.
