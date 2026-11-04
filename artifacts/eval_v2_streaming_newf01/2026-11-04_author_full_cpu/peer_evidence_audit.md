# Required independent read-only author evidence audit

Reviewer: `/root/review_requirements`, another agent as required by Root AGENTS.
No project/test execution, file edits, commits or DS/GPU dispatch by reviewer.

Exact Root551b03621507dde52303f54290d4fea89d66e8da /
Child82fa270e8cdb76b3e1a4e94adf0c7ce2b497884e.

The reviewer's final read-only observation:

- Five raw suites182+278+234+89+86 contain869 unique cases, matching mergedJUnit;
  no failures/errors/skips, shell0.
- 90 source hashes before/after/current recomputation match, including the new
  test; clean exact worktrees; 66 static files passed.
- Both pipeline witnesses each have900 unique Core,900 Session,64 Slot and max64
  simultaneous ownership; same-Task multiple EP overlap;7200 Core inventory file
  hashes match.
- Both NEW-F01 OS cases record budget fault,0 Core, two active Slots,3 owned
  processes closed, pending/jobs0 and outsider survival.

Limits noted by reviewer: actual observed max Batch3/2 does not establish B8/B16
saturation or GPU performance; SIGTERM/BrokenPipe failure-containment diagnostics
remain; tiny synthetic CPU DCP API is used by tests, so original Gate's coarse
`dcp...NOT_RUN` marker must not be read as no DCP library calls.

This is a read-only audit of author-produced evidence, not an independent DS Gate
run or a new technical Code Gate. Existing GPT APPROVE_CODE remains scoped to
the unchanged exact Formal Pair; DS independently executing it is still pending.
