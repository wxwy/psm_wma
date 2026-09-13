# Authority-root execution snapshot annex v0.8

v0.8 is a docs-only replacement of the v0.7 launcher artifact.  Candidate parent, Gitlink, frozen input
bytes, bootstrap, argv, environment and every execution prohibition are unchanged.

- Payload: `PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py`; exact UTF-8 raw length is
  `13969` bytes and SHA-256 is
  `b7923b212f40bba8580711793a5b9a5ef5ab2c2b1f62b0b44c6d6ee93882d666`.
- The inert third base64 argv copy is removed.  The sole third `RAW` value is its frozen compact JSON lexical
  bytes, so the raw payload, `-c` program bytes and actual argv all have one authority source.
- Native Git does not report an identity for the directory it created.  Therefore a pathname bind after a successful
  `worktree add` cannot prove that it is continuous with that mutation.  The launcher now fail-closes with
  `ROLLBACK_INCOMPLETE` before accepting any post-add pathname as owner authority; it neither binds nor removes a
  potentially foreign CLEAN directory.  A later, separately authorized execution design must retain a causal
  creation identity during the native mutation before it can enable the successful path.
- FD closing derives durable descriptors by listing then `fstat`-validating candidates, thereby excluding the
  transient descriptor used by `/proc/self/fd` enumeration while retaining the exact durable `{3,4,5}` invariant.
- CPU-only temporary witnesses directly invoke `capture_owned()` for the post-add-missing terminal result and
  invoke `close_to_keep()` in a forked child with injected extra descriptors.  They directly invoke
  `run() -> capture_owned() -> cleanup()` against temporary native Git worktrees for both verified cleanup and
  foreign-CLEAN replacement; the existing temporary native Git, handoff and route witnesses remain in the same
  test file.
- `add_and_capture()` is the exact first-mutation boundary.  Temporary native-Git fixtures prove a nonempty target's
  nonzero `worktree add`, a successful add followed by injected parent `commondir` drift, and a successful add whose
  original CLEAN is renamed then replaced by a Git-valid copied worktree before any ownership bind.  All terminate
  `ROLLBACK_INCOMPLETE`; the foreign replacement remains present and is never treated as owned.

This annex requests no materialization verdict.  It neither runs the launcher nor authorizes real source or
checkpoint I/O, collection, receipt, publication, child changes, GPU, training, evaluation, inference or
LIBERO4IN1.
