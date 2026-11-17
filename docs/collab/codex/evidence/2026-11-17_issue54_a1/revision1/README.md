# Local peer findings and author revision

This is local code review, not GPT server acceptance. The original probes and
JSON observations were copied byte-for-byte from the reviewer for fixed Root
`dab6ebf5ad35348b9aea9db079a74ea41bb14fe7` / Child `d5c1ffc7`.
The probes intentionally reproduce invalid acceptance on that *old* candidate;
they are not green expectations for the corrected implementation.

Three P2 findings: missing viewer COMPLETE episode/count fields; accepting a
1x1 PNG against a 64x64 projection; rejecting a legitimate Island retirement
after 0.4mm motion crosses the separate 0.3m connection threshold. New behavior
is covered by `test_stage_a_review_edges.py` and the actual viewer loadEpisode
Node test. The first pass had45 new tests; revision adds5 distinct cases.

`development_green.log` is overlapping author development coverage, not added
to the final result. `final_*` logs/JUnit, `source_before/after.json` and
`gate.json` below are the latest author CPU/static evidence. Original parent
evidence is immutable. Replay into a fresh directory:

```bash
ISSUE54_EVIDENCE_OUT=/tmp/issue54_a1_review_replay_new \
  bash docs/collab/codex/evidence/2026-11-17_issue54_a1/commands.sh
```

No GPU, new environment, private data or native runtime used. Consumer/ACK/
queue recovery/new-source VAE adapter remain next-batch TODO.
