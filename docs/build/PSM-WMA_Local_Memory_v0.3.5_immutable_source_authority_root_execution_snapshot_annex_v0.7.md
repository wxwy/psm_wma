# Authority-root execution snapshot annex v0.7

v0.7 supersedes only the v0.6 launcher artifact.  The candidate parent, Gitlink, input bytes, bootstrap, argv,
environment and all prohibitions remain unchanged.

- New payload: `...authority_root_launcher_payload_v0.7.py`; its formal raw length/SHA are verified after commit.
- Ordinary `.git` accepts neither `config.worktree` nor `commondir`; both absence predicates are retained and
  rechecked before/after every native Git command.
- Backing handoff checks non-symlink regular `0600` pathname identity after reader-open and after target handoff.
- Any failure of the first `worktree add`, including nonzero return or post-command route drift, terminates as
  `ROLLBACK_INCOMPLETE`.  This conservative path never reports ordinary failure while administrative residue is
  unproven.
- Direct temporary witnesses are the v0.7 witness core/test; they cover pathname/mode, replacement, commondir,
  add-failure, FD-set and cleanup classifiers.  Remaining full native Git causal witnesses are mandatory before
  any materialization verdict.

No launcher is run by this document.  It does not authorize materialization, source/checkpoint I/O, child, GPU,
training, evaluation, inference or LIBERO4IN1.
