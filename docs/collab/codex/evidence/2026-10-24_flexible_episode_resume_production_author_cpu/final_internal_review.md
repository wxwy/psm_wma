# Frozen production Resume — final author-team read-only delta inspection

Date: 2026-10-24 (Asia/Shanghai). Scope is limited to the three recently closed
production integration points below. This is an internal source inspection,
not GPT's formal verdict or DS_PRO independent acceptance. No tests were run
and no production source was edited during this inspection.

## 1. Current producer provenance

`scripts/robocasa_resume_cli.py:79` records actual current Root/Child separately
from the reused Episode sources; an invocation without new execution records
`runtime_probed=False` and no claimed current runtime digest. When new execution
is planned, the verified runtime/source/config metadata replaces that view-only
observation (`:284-303`). The CLI explicitly assigns a copied value to
`store.current_provenance` before `begin_invocation()`; the immutable invocation
manifest persists it in `scripts/robocasa_resume_store.py:541-550`, while
`resume_plan.json` also retains `view_producer`. Existing reused EpisodeRef
provenance is not rewritten by this assignment. This closes the previous risk
of an empty or fabricated producer record, including the all-reuse path.

## 2. Final re-scan failure remains an observable PARTIAL result

`scripts/robocasa_resume_cli.py:422-435` starts with the executor's existing
errors. An exception from the final authoritative source scan adds a typed
`final_source_revalidation` error and substitutes an empty verified-source set;
it does not fall back to the earlier trusted snapshot. The following
`_revalidate_selected_sources()` (`:179-205`) removes reused entries that cannot
be revalidated and preserves their source references in explicit errors.
The final report therefore receives those errors and no unproven completions
(`:441-460`), retaining current job/cleanup evidence and diagnostic media.
`build_report()` cannot return COMPLETE, non-null formal SR or exit code zero
while these invocation errors exist. Empty-source catalog publication does not
repair or relabel old evidence. Ordinary final re-scan exceptions are thus
recorded in the final PARTIAL view rather than escaping without that view or
silently retaining a stale COMPLETE result.

## 3. Source callback inherits the same deadline and cancellation event

`scripts/robocasa_resume_execution.py:324-350` gives the native full-attempt
validator the Task deadline/stop event, then checks cancellation/deadline both
before and after the completed-source callback. The callback receives those
same objects as `validation_deadline` and `validation_stop`; the CLI forwards
them into `read_reserved_batch()` (`scripts/robocasa_resume_cli.py:373-381`).
Store forwarding is explicit at `scripts/robocasa_resume_store.py:664-668` and
`:365-379`. The Episode scanner and media validation apply them at source,
Attempt, Episode and decoder boundaries. TimeoutError/InterruptedError are
re-raised ahead of the ordinary corrupt-source quarantine catches
(`scripts/robocasa_episode_resume/episode_evidence.py:483,599,646`),
so cancellation cannot become a harmless excluded Episode. If this callback
fails after native completion, the native COMPLETE marker stays truthful, but
the executor still records the independent source-revalidation error; overall
invocation completion does not follow from Episode coverage alone.

## Inspection conclusion and fixture evidence note

No new blocker was found within these three deltas. The observed code follows
the approved separation of original Episode evidence, current invocation view,
and infrastructure-error status. This conclusion does not reopen the design
Gate, broaden the implementation scope or authorize real execution. Final
combined CPU results remain the Parent's separate evidence task.

The old Queue fixture was adapted without deleting or skipping its 43 test
definitions. Its first fail-fast run recorded **34 passed, 68 subtests passed,
1 failed** in 774.09s (JUnit103 cases with one failure). The only failure was
the fixture expecting one of two legitimate detections of the deliberately
terminated Action Server: the live supervisor won before the new post-wait
guard. The corrected assertion accepts only those two exact server-exit
messages and additionally checks the precise Task/stage, return code -15,
non-live Server/Simulator groups, nonzero invocation exit,20 completed Episode
records and null SR. That single test then passed in20.46s with no skip.
Both initial and focused raw logs/JUnit remain in the external `queue/`
directory. They are not relabeled as a successful whole-file final run.
