# ChatGPT review — Stage-1 v1.7 request-instance recovery design v1.8

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V18`
- Formal root: `6baadaf282bea673eb217c055bb7c837522e0267`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`
- Blockers: `0`; Design/Authority: `0`; Production: `0`; Evidence/identity: `0`; child/runtime: `0`.

## Formal target / scope

This is a fresh formal pair relative to the approved V17 recovery-design pair `d03cb28ca138090f50adc09d4e810713457353af / 93a89ba61306d840a008813f62f26a34d54850f4`.

The formal root changes only `SESSION.md`, `TODO.md`, and `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_recovery_design_v1.8.md`. Its formal tree binds `cosmos-framework` as mode `160000` exactly equal to `93a89ba61306d840a008813f62f26a34d54850f4`; no child/runtime implementation change is part of this target.

## Authority chain / chronology

V0.5 remains the controlling same-round zero-mutation construction-closure authority except where explicitly superseded. V1.0 freezes P0 immutable-object/literal authority. V15 freezes the strict byte-exact `patch_raw -> patch_text -> exactly one apply_patch(patch_text)` consumer seam. V17 was approved after restoring the omitted `.git`, local V2, remote advertised V2, and local/remote fixed-ref authority facts.

After that approval, only P0/P1 pure in-memory identity/projection checks were performed. The V18 design states those checks did not read output paths, environment, `.git`, refs, or remote state and did not write files; therefore C had not begun and the one-shot construction authority had not been consumed. Stopping before the first freshness observation is consistent with the frozen P0/P1 non-consuming lifecycle.

## Closure finding

V18 correctly resolves a genuine pre-C schema/path ambiguity without weakening V17:

- V17 inherited the phrase `designated candidate/record/receipt/publication absences`, but those Stage-2 names did not have frozen Stage-1 pathnames or field mappings.
- The earlier concrete Stage-1 authority request already froze the actual absence set as exactly four targets: clean worktree root, temporary index, evidence JSON, and pending evidence JSON.
- V18 makes those four targets the only permitted ordered `designated_path_absence` records, with exact absolute paths and Stage-1 roles, and explicitly excludes undefined Stage-2 candidate/record/receipt/publication semantics from this Gate rather than inventing paths.
- Each record is required to carry the frozen path, absence predicate/result, no-follow observation semantics, and canonical record identity; fixed local/remote authority-ref absence remains an independent authority field and cannot be substituted by path absence.
- V18 preserves the V17 same-round `.git` / config / local V2 / two remote queries / separately extracted advertised V2 / local+remote fixed-ref closure, six-key isolation environment, P0/P1 raw closure, owner-FD authority, cwd/index/evidence targets, detached canonical JSON/Markdown identity, strict single patch consumer, post-write byte equality, one-shot C, terminal residue semantics, and permanent no-retry.

This is a narrowing from an undefined label set to the concrete Stage-1 path set already evidenced by the older authority request; it is not a reduction of required Stage-1 authority.

No new Design, Production, Evidence, or child/runtime blocker was found.

## Verdict / boundary

`APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`

This approval is bound only to exact formal pair `6baadaf282bea673eb217c055bb7c837522e0267 / 93a89ba61306d840a008813f62f26a34d54850f4` and Gate `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V18`.

Authorization remains narrow: after the required same-pair multi-review approval condition is satisfied, exactly one future docs-only v0.4 request-pair construction is permitted, followed by independent exact-pair request review.

Still NOT authorized: Stage-1 materialization/execution/retry; launcher/materializer execution; real source/checkpoint/manifest/data/cache I/O outside the separately frozen construction observation allowlist; collection/receipt/record/package/publication; child/runtime/config mutation; GPU/CUDA/torchrun; training; evaluation; inference; LIBERO4IN1.
