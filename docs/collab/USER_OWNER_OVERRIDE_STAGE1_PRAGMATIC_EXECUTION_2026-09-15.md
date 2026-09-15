# User Owner Override — Stop governance over-engineering and enter Stage-1 execution

Date: 2026-09-15
Owner intent: restore the critical path to real PSM-WMA / TTT execution: request pair -> Stage-1 materialization -> source receipt -> single-GPU smoke -> training.

This document is a **User Owner Override / execution directive**. It is **not** a formal review verdict and **must not** be interpreted as a request to create another lateral governance Gate.

## Decision

The current Stage-1 request path has accumulated governance work that is no longer proportional to the research objective. The project is not trying to build a formally verified capability-attestation system; it is trying to produce a reproducible Stage-1 artifact and get the TTT path onto GPU.

Effective immediately, stop extending the V25/V26/V27 line for live Python-object continuity, host-owned continuation, IPC/session/lease continuity, OS-level capability attestation, or equivalent object-identity proof machinery.

Do not create V28/V29/etc. for the same class of governance concern unless a concrete execution failure demonstrates that such machinery is actually required for correctness or reproducibility.

## Retain the already completed reproducibility boundary

The following work remains valid and should be reused rather than restarted:

- ContractV05 / complete pre-C closure;
- P0 exact root/path/blob/raw-length/SHA identities;
- P1 exact eight-object identities;
- ReplayBinding exact scalar/items/rows identities;
- exact JSON / Markdown / patch bytes and canonicalization;
- six-key environment contract;
- exact output / cwd / index / evidence paths;
- designated absence / output absence checks;
- freshness checks / nine-entry local freshness domain;
- child Gitlink identity;
- existing CPU/static positive and negative tests;
- exactly-once write intent, exact readback, hard-stop/no-retry semantics where they are directly useful.

These are sufficient as the reproducibility and fail-close boundary for this research project.

## Explicitly no longer required

Do **not** block Stage-1 on proving any of the following:

- a reviewed Python object is the same in-memory object later used for C;
- a session/lease object remains continuously live during review;
- a unique Python registry owner exists for the plan;
- a separate OS host owns continuation authority;
- anonymous/private IPC preserves plan identity;
- consumer/guard/verifier require additional OS-level attestation beyond frozen code/version identity;
- object identity / capability identity needs to be stronger than immutable code commit + exact executable/config identity.

These concerns are outside the necessary scope of the current PSM-WMA / TTT research prototype.

## New execution model: pragmatic immutable-commit provenance

From now on, execution provenance is defined by the following frozen tuple:

1. final root commit SHA;
2. child Gitlink SHA;
3. exact request JSON bytes + SHA256 / git-blob identity;
4. exact request Markdown bytes + SHA256 / git-blob identity;
5. exact Stage-1 materialization command / config;
6. resulting authority-root / source-evidence receipt hashes;
7. exact GPU smoke command / config / checkpoint identity.

The frozen commit contents are the authority for the code path. Python object identity is not part of the provenance model.

## Immediate execution sequence

Use the latest implementation that already passes ContractV05 / freshness validation as the frozen execution candidate. Do not restart the implementation.

Before writing the request pair, perform one non-consuming preflight that checks only execution-critical facts:

- root SHA is the intended frozen execution candidate;
- child Gitlink SHA is the intended frozen child;
- repository state required for execution is clean / understood;
- exact final JSON / Markdown bytes are already determined;
- SHA256 / git-blob identities match frozen expected values;
- output paths are exact and absent as required;
- materialization command/config passes dry-run or static validation;
- no stale/foreign root/child/config is being used.

If this preflight passes, proceed directly to generate the new v0.5 request pair.

## After request pair generation

The intended critical path is now:

`frozen root+child`
`-> non-consuming execution preflight`
`-> generate exact v0.5 request pair`
`-> byte-for-byte / SHA verification`
`-> independent exact-request review`
`-> Stage-1 materialization`
`-> authority tuple / source-evidence receipt`
`-> minimal receipt verification`
`-> single-GPU smoke`
`-> training`

Do not insert live-object/session/IPC/host-attestation Gates back into this chain.

## What still counts as a legitimate blocker

A new blocker is legitimate only if it can cause one of the following concrete failures:

- wrong code version executes;
- wrong child/model version executes;
- wrong path is written or read;
- exact request bytes are not reproducible;
- Stage-1 materialization cannot be reproduced;
- output/receipt is corrupted or ambiguous;
- GPU command/config/checkpoint is wrong;
- runtime/model/data failure would invalidate the experiment.

A concern about Python-object identity, session continuity, capability ownership, or IPC attestation by itself is **not** a legitimate blocker under this Owner Override.

## Gate discipline

Do not create one new Gate per newly noticed field, reviewer wording issue, object identity concern, or provenance cosmetic.

If an execution-critical omission is found before request generation:

1. fix the whole class of analogous omissions in one pass;
2. rerun the existing preflight/tests;
3. produce one consolidated formal candidate;
4. continue the critical path.

Only create a new Gate when there is a genuinely different execution authority boundary with direct consequences for correctness, reproducibility, data integrity, or GPU execution.

## Status reporting to user

From now on, user-facing status should contain only:

- `v0.5 request generated`: yes/no;
- `Stage-1 materialization`: PASS / FAIL / not started;
- `source receipt`: complete / incomplete;
- `single-GPU smoke`: PASS / FAIL / not started;
- `training`: started / not started;
- one concrete blocker, if any.

Do not count additional governance-document churn as progress unless it directly removes a blocker on this path.

## Immediate next action expected from Codex

1. acknowledge this Owner Override;
2. stop V25/V26/V27 host/session/IPC continuation work;
3. select and record the latest already-validated frozen execution candidate root/child pair;
4. run the minimal non-consuming execution preflight above;
5. if PASS, generate and verify the new v0.5 request pair;
6. move directly toward Stage-1 materialization and then single-GPU smoke.

The objective is now explicit: **stop proving that the write mechanism is impossible to substitute; freeze a reproducible code version and execute the research.**