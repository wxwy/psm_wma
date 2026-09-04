# ChatGPT re-review — R09-B TTT v0.3.2 C5A invalid-row chronology remediation @ f030e36

Date: 2026-09-04

## Verdict

**REQUEST_CHANGES**

Formal Gate:
`G0-R09-B-TTT-V032-C5A-CHRONOLOGY-OWNER-SEGMENT-IMPLEMENTATION`

Formal implementation pair:
- root remediation SHA: `f030e36b3f866e38793533512bfc5bbda9f98743`
- child/Gitlink: `26b08e8b1a8861ea8903027b6bef3e9eda1509e2`
- frozen C5A design authority: `bbe0444eaa8c08f05ca5a5eea0e331253d263592`
- immediately preceding implementation pair: root `3c2d8808dd04d5d3a7a49aaf3b2236d493994a05` / child `87bd7f71ac6eddbcf753f0b2365eea4747145b7b`

Review-start remote `V2` was locked to exact root `f030e36b3f866e38793533512bfc5bbda9f98743`; its Gitlink is exactly `26b08e8b1a8861ea8903027b6bef3e9eda1509e2`.

Scope check:
- child `87bd7f7... -> 26b08e8...` is exactly one commit ahead;
- only `cosmos_framework/model/generator/mot/c5a_owner_segment.py` and adjacent `c5a_owner_segment_test.py` changed;
- root `3c2d880... -> f030e36...` only advances SESSION/TODO, the Gitlink and carries the prior ChatGPT review;
- no production/runtime Cosmos wiring, config/optimizer/checkpoint/trainer/inference/parallelization, GPU/CUDA/torchrun, real model/data/cache/checkpoint I/O, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 scope drift was found.

## Closed relative to 3c2d880 / 87bd7f7

The current remediation materially closes the all-invalid-row promotion defect:
- `_Pending.valid_rows` records materialization validity;
- `commit()` promotes state/chronology/replay/reverse-index only for valid indices;
- an all-invalid owner row no longer gets `_last_timestep` or committed replay;
- the B>1 fixture now proves owner `a` valid / owner `b` invalid produces one C5 write, commits only `a`, and leaves `b` absent from committed chronology;
- the pending invalid replay fixture now also proves replay shape metadata and zero-extra-write lookup.

These are real closures and no scope drift was found.

## Findings

### 1. HIGH — mixed temporal validity can still create a committed chronology hole

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:185-252`
- specifically `materialize_many()` recording arbitrary `valid[B,T]` and `commit()` selecting all valid indices then setting `_last_timestep` to the last valid source timestep.

**Root cause:** admission allocates contiguous pending timesteps before materialization, e.g. `t0,t1,t2`. The new `commit()` filters invalid rows but does not require the per-owner valid mask to be a contiguous prefix/suffix shape compatible with chronology. For `valid=[True, False, True]`, C5 performs writes for `t0` and `t2`, commit promotes replay/index for those two rows, omits `t1`, then sets `_last_timestep=2`. The next admission of `t3` is accepted as contiguous even though committed chronology/replay has a hole at `t1`.

**Contract violation:** v0.6 makes C5A the sole chronology authority and freezes contiguous source admission plus exact replay/reverse-index semantics. Filtering invalid rows after chronology allocation is not sufficient if later valid rows can leap across an invalid source.

**Acceptance condition:** freeze and enforce a chronology-safe validity grammar before C5/commit. A current-design-compatible option is: for each owner, valid rows that may commit must form a contiguous prefix of the pending segment (or otherwise an explicitly frozen contiguous set from the current committed cursor); once a row is invalid, no later row in that owner segment may be valid. Reject illegal masks before Encoder/C5 mutation, or redesign the transaction so skipped rows never allocate chronology and later rows are renumbered consistently. Add direct T>1 fixtures for `[True,False,True]` rejection and legal prefix cases, verifying per-owner C5 writes, `_last_timestep`, replay/index keys and next contiguous admission.

### 2. HIGH — remaining acceptance-tail evidence is still incomplete

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment_test.py:230-320`
- prior same-Gate review: `docs/collab/chatgpt/reviews/2026-09-04_R09_B_TTT_v032_C5A_acceptance_tail_remediation_3c2d880.md`

**Remaining direct gaps:**
1. fresh new-epoch same owner/source identity/timestep is still only tested with the same source bytes; changed-byte fresh-epoch reuse remains untested;
2. backward-failure rollback still lacks an exact before/after snapshot of committed fast state, `_last_timestep`, committed replay values/metadata, reverse identity index and epoch;
3. abort rollback compares committed key sets but not the committed `ReplayRecord` values/shape/presence themselves;
4. pending replay now proves presence/shape/graph-free/zero-write, but still does not directly compare the replay numerical value to the corresponding materialized row.

**Acceptance condition:** after Finding 1 is fixed, add direct fixtures for the four evidence details above and retain all current v0.6 coverage. Re-run the isolated CPU selector and report exact count plus py_compile and child/root diff-check.

## Evidence note

Root/project status for this submission records the updated isolated CPU evidence; those commands were not independently rerun in this connector environment and are treated as submitted evidence. Source inspection above independently blocks closure.

## Required next submission

Remediation remains restricted to the approved isolated C5A CPU boundary. Finding 1 requires a production-semantics/code fix unless the design is explicitly amended and re-approved; Finding 2 is tests-only unless stronger fixtures expose another defect. A new root/child implementation pair requires fresh same-SHA review.

Still prohibited:
- production/runtime Cosmos wiring;
- config/optimizer/checkpoint/trainer/inference/parallelization;
- GPU/CUDA/torchrun and real model/data/cache/checkpoint I/O;
- training/evaluation/inference;
- P4/P5, B2-T and LIBERO4IN1.
