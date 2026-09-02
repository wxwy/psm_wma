# ChatGPT independent review — R09-B2 P4-v4 preflight materialization design v0.1

- Verdict: `REQUEST_CHANGES`
- Design commit: `887fb8194bdea6539e5f8a031032f899813e8fec`
- Formal request / reviewed branch head: `9dd1126e833114fc98564ec784984ffec3707332`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Reviewed design: `docs/build/PSM-WMA_R09_B2_P4_v4_execution_preflight_materialization_design_v0.1_2026-09-02.md`
- Previous closed anchor: ChatGPT `fd0055020f4aa9a4f66800b4b018062ee3ce982f`
- Scope: design only. No real request/preflight/staging/P5/GPU/training authority is granted.

## Summary

The transition from closed full-admission parsing to a future CPU-only reservation helper is directionally sound, and the public CLI hard-stop remaining in place is correct. However, v0.1 does not yet define an implementable authority object or an internally consistent filesystem/state-machine contract. The blockers below are new materialization concerns; they do not reopen the already-closed nested/full admission validators.

## HIGH — helper cannot prove “same admitted request” from a plain dict

Design `:22` requires the helper to accept only the canonical in-memory request returned by the same `load_execution_request(raw)` and to reject an unverified or reparsed request. Current `load_execution_request()` returns an ordinary mutable `dict[str, object]`. A helper whose only authority inputs are that dict plus a filesystem primitive cannot distinguish the original admitted object from a deep copy/reparse with identical content. Content equality proves request bytes/content, not same-invocation admission provenance.

This must be frozen before implementation. Preferred remediation: introduce a private admission-capability wrapper without changing any closed nested schema/validator, e.g. a new private `_admit_execution_request(raw)` that calls the existing `load_execution_request(raw)` unchanged and returns an opaque `_AdmittedRequest` containing the validated dict plus exact raw/request SHA. The materialization helper accepts only that capability, not a bare dict. Equivalent capability designs are acceptable if they do not add ambient/global authority and do not weaken the existing loader.

Do not solve this with a global object-id registry, ambient mutable state, or by simply accepting any dict that “looks valid”; those do not satisfy the stated same-admission requirement.

## HIGH — nonexistent run-root contract conflicts with the mkdir allowlist

Design `:24`, `:28-34` says each backend run root must be nonexistent before reservation, but the only allowed writes are described as mkdir of two `<run_root>/import_staging/<run_token>` directories. The already-closed `run` contract explicitly defines each run root as a future-nonexistent path. If `<run_root>` does not exist, creating the leaf requires creation of at least the `run_root` and `import_staging` parents as well; a leaf-only `mkdir` cannot succeed, while `mkdir(parents=True)` performs additional writes not present in the stated allowlist.

Freeze the exact reservation footprint and creation sequence. For each backend, state every directory that may be created, e.g. whether the authorized footprint is exactly:

```text
<run_root>/
<run_root>/import_staging/
<run_root>/import_staging/<run_token>/
```

and whether this is three explicit nofollow-safe mkdir operations per backend. Bind all created paths back to `request.run.<backend>.identity.root` and `run_token`. The test allowlist must match the exact production primitive; do not hide recursive parent creation inside a broad `parents=True` abstraction.

Also remove/clarify the current `nonempty directory` and `token mismatch` wording unless an independent path/token authority is explicitly defined: a run root that must be nonexistent cannot simultaneously be an accepted empty/nonempty directory state, and a helper that derives the staging leaf directly from the request token has no external token to “mismatch” against.

## HIGH — two-backend reservation is not atomic under the stated state machine

Design `:28-30` permits only `ADMISSION -> RESERVED -> STOPPED`, forbids cleanup/retry, and describes `RESERVED` as both backend reservations having been obtained. But the two backend paths are distinct and will require sequential filesystem mutations. Even after all prechecks succeed, the first backend mkdir can succeed and the second mkdir can fail because of a race, `EEXIST`, permissions, injected I/O failure, etc. That leaves a partial footprint which is neither `ADMISSION` nor `RESERVED`, while cleanup/retry is forbidden.

The fixture requirement at `:40` only covers “second backend check fails -> zero mkdir”; it does not cover failure of the second actual create after the first create succeeded.

Freeze a truthful terminal model before implementation. The practical option under the existing no-cleanup/one-shot discipline is to define an explicit terminal partial/poisoned state (name is up to the design), with:

- exact allowed partial footprints for failure after each mkdir step;
- no cleanup and no reuse of the affected run-root/token identity;
- deterministic surfaced result/error semantics;
- fixtures injecting failure at every mutation point, including after recurrent reservation but before/during TTT reservation.

If the design instead insists on true all-or-nothing `RESERVED`, it must provide a single atomic filesystem authority capable of reserving both distinct roots; ordinary sequential `mkdir` is not such an authority. Do not call the current sequence “atomic” without resolving this.

## Accepted parts

No objection to the following v0.1 boundaries:

- public `main()` remains SHA-bound and hard-stopped after this static implementation Gate;
- no real request, P4 preflight, candidate, record/refreeze, P5 export/compose, GPU, model/data/checkpoint I/O, training/eval/inference;
- no new subprocess/PATH/network/ambient-environment authority in the materialization helper;
- fixed backend order;
- no source copy/payload generation/publication in this helper;
- a later separate exact-request execution Gate is still mandatory.

## Required v0.2 closure

A remediated design should therefore freeze, at minimum:

1. an implementable admitted-request capability/provenance boundary;
2. the exact per-backend directory footprint and mkdir sequence for future-nonexistent run roots;
3. a truthful failure/partial-state contract for errors after the first filesystem mutation, with per-step injected-failure fixtures;
4. exact token/path authority wording consistent with the helper’s actual inputs;
5. unchanged public CLI hard-stop and all existing execution prohibitions.

Only after those points are frozen should `APPROVE_TO_IMPLEMENT_P4_V4_PREFLIGHT_MATERIALIZATION_STATIC_TOOLS` be granted.
