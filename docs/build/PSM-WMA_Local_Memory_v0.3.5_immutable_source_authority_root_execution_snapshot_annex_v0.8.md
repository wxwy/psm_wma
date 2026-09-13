# Authority-root execution snapshot annex v0.8

v0.8 is a docs-only replacement of the v0.7 launcher artifact.  Candidate parent, Gitlink, frozen input
bytes, bootstrap, argv, environment and every execution prohibition are unchanged.

- Payload: `PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py`; exact UTF-8 raw length is
  `13802` bytes and SHA-256 is
  `546c24890618f43aff2f5af09d30c2de12c68ed7e632f79c426baa5012a13342`.
- The inert third base64 argv copy is removed.  The sole third `RAW` value is its frozen compact JSON lexical
  bytes, so the raw payload, `-c` program bytes and actual argv all have one authority source.
- Post-add ownership capture is an explicit no-follow directory-FD bind.  Any disappearance, replacement or
  binding failure after the possibly successful `worktree add` is converted to `ROLLBACK_INCOMPLETE`; it cannot
  escape as an ordinary lookup error.
- FD closing derives durable descriptors by listing then `fstat`-validating candidates, thereby excluding the
  transient descriptor used by `/proc/self/fd` enumeration while retaining the exact durable `{3,4,5}` invariant.
- CPU-only temporary witnesses directly invoke `capture_owned()` for the post-add-missing terminal result and
  invoke `close_to_keep()` in a forked child with injected extra descriptors.  They directly invoke
  `run() -> capture_owned() -> cleanup()` against temporary native Git worktrees for both verified cleanup and
  foreign-CLEAN replacement; the existing temporary native Git, handoff and route witnesses remain in the same
  test file.

This annex requests no materialization verdict.  It neither runs the launcher nor authorizes real source or
checkpoint I/O, collection, receipt, publication, child changes, GPU, training, evaluation, inference or
LIBERO4IN1.
