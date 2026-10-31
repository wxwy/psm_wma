# No-TTT console: full initialization, then progress

Owner Issue13 update: before core Trainer `Starting training...`, show complete
stdout/stderr; show the boundary line itself; after it, show only Rank0
`[CorrectedV3][progress]`. Keep all raw bytes on disk, exit/error reporting,
owned-process cleanup and unique logs. Current running Resume is untouched;
the new version is for later launches after review.

Base canonical Root `cee6f53eef345579c3db1124148f350fd2edc618` /
unchanged Child `6c83596d6a259e89c4cd3e79424024983426ac3d`.
Candidate Root branch `v3-nottt-console-start-boundary-20261031`, isolated only.

## Source seam and minimal implementation

Child `cosmos_framework/trainer/__init__.py:330` currently calls
`log.info("Starting training...")` after checkpointer.load, iteration admission,
dataloader positioning and distributed model setup. `utils/log.py` defaults to
Rank0 and formats INFO with timestamp, relative source path, line and function;
ANSI colors/machine fields are optional. Neither Child file is modified.

Only production change is Root `scripts/no_ttt_console.py`:

- New supervisor starts in full-display mode. It writes each raw chunk to its
  existing file first, then streams initialization bytes to terminal immediately,
  including incomplete lines, large messages and split UTF8. No extra buffering
  until model loading finishes, no additional training import/dependency.
- Recognize a complete newline-terminated plain `Starting training...` message or
  actual Cosmos INFO Trainer/train log; ignore optional ANSI/CR for recognition,
  preserve original bytes for display. Quoted config strings, rank prefixes,
  other sources/functions and non-INFO logs do not switch mode.
- Echo the boundary before a one-way switch; subsequent noise in the same read
  is already filtered. Existing bounded progress framing remains, detector runs
  only before training. No marker means full visibility continues, not silence.
  A new launch/Resume gets a new full-display state.
- Keep raw logging, file modes, failure codes/tails, SIGINT/SIGTERM, process
  ownership/teardown and original command/env behavior. No launcher changes.

## Narrow author CPU scope

New19 boundary cases use real CPU pipes and fake subprocesses: formatting,
ANSI, byte fragments, live unfinished initialization, same-read boundary,
false positives, buffer bounds/invalid UTF8, EOF, initialization failure and
per-launch reset. Keep all21 original console cases, updating only display
expectations/fixtures required by the new contract; raw/error/cleanup assertions
remain. Existing6 synthetic shell→console→real CPU profile/Trainer-binding cases
emit a synthetic start line and verify full prefix+progress, not actual training.

Expected46 cases; final JUnit is count authority. Scoped Ruff0.12.7 check/format
and syntax4 Python files, clean exact Pair and fingerprints before/after. Verify
whole Child/Gitlink, both standard launchers, all other code objects and previous
cleanup/main functions unchanged. Freeze raw commands/logs/JUnit/source hashes.
No old84/49 suite replay, GPU experiment, model/data/DCP/server/simulator or live
Resume access. No tests skipped/xfail or weakening of failure/cleanup conditions.

Commit new Root with same Child, author CPU evidence and fresh GPT incremental
review request, publish isolated candidate only, then STOP. No V3 merge or
runtime start is included in this task.
