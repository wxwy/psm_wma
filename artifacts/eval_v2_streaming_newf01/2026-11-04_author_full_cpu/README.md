# NEW-F01 exact-pair full author CPU evidence

**869/869 PASS**, zero failures/errors/skips, Shell exit0, `gate.status=PASS`,
`source_unchanged=true`. One full new-pair run; old846/narrow35 results not reused.

- Formal Root: `551b03621507dde52303f54290d4fea89d66e8da`.
- Unchanged Child/Gitlink: `82fa270e8cdb76b3e1a4e94adf0c7ce2b497884e`.
- Groups: inference182 + PhaseA278 + PhaseB234 + media89 + streaming86.
- 90 watched source SHA256 entries before/after match; 66 static files pass.
- [Author result / DS handoff](../../../docs/collab/codex/reviews/2026-11-04_EvalV2_Streaming_551b0362_82fa270e_Author_Full_CPU_PASS_DS_Handoff.md).

[Summary](final_summary.json) · [Original Gate JSON](gate.json) ·
[Original merged JUnit](junit.xml) · [Shell exit](author-full-after-code-review.shell.exit) ·
[Launch command](author-full-launch-command.txt) · [Environment](environment.json) ·
[CPU overrides](environment_overrides.json) · [Before hashes](source_sha256.json) ·
[After hashes](source_sha256_after.json) · [Read-only peer audit](peer_evidence_audit.md).

Each test group's `.xml` and `.log` remains directly browseable. `os_scenarios`
contains CPU pipeline and budget-fault witness JSON; the complete raw Store,
process and cleanup evidence is in [cpu_evidence.tar.gz](cpu_evidence.tar.gz).
13,664,718 bytes /107,474 archive entries; [SHA256SUMS](SHA256SUMS):
`763f6e9105ae3ea5358edff2d7f90ab99b24517467c6750caa41672fce080b4a`.
Dependency caches, bytecode and ephemeral Server capability files excluded;
all original logs/diagnostics/whitespace otherwise preserved.

This is author evidence, not independent DS acceptance. See [scope](evidence_scope.md)
for actual Batch observations, synthetic boundaries and small CPU DCP API use.
No real training checkpoint/data, remote-server file access/copy, GPU run,
canonical V3/G2 merge or M/B Resume relaxation. Later docs/ledger commits do not
replace the Formal Pair above.
