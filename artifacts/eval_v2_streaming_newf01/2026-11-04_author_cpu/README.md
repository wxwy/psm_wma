# NEW-F01 narrow author CPU evidence

Formal Root **551b03621507dde52303f54290d4fea89d66e8da**; unchanged Child/Gitlink
**82fa270e8cdb76b3e1a4e94adf0c7ce2b497884e**. Previous Formal00e119cc.

[Author handoff / requested incremental Code Gate](../../../docs/collab/codex/reviews/2026-11-04_EvalV2_Streaming_NEW_F01_Author_Handoff.md)
(repository path: `docs/collab/codex/reviews/2026-11-04_EvalV2_Streaming_NEW_F01_Author_Handoff.md`).

- [Final machine summary](summary.json): clean exact-pair **35/35 PASS**, no failures/errors/skips, exit0, 1239 before/after source hashes unchanged; this is a narrow author gate.
- [Final raw JUnit](formal-targeted/junit.xml), [log](formal-targeted/pytest.log), [command/environment](formal-targeted/command.json), [OS proofs](formal-targeted/os_proofs.json).
- [Old RED](old-red/junit.xml): expected4FAIL at unchanged old production; [first new run](new-green/junit.xml):33PASS/2FAIL due missing external adjacent fixture; [original-path OS rerun](os-green/junit.xml):2PASS. All failure history retained, no assertion/source modification for the invocation fix.
- [Static/delta proof](static.json), [incremental patch](incremental.patch), [independent agent's read-only review](peer_review.md).
- [Complete raw evidence archive](cpu_evidence.tar.gz), [SHA256SUMS](SHA256SUMS):545616bytes/292entries/SHA256 `a73c700396c4771ee61604acfbf3d0c6c692b6dd8c7a589d0203286598de32c5`.

Archive includes raw source fingerprints, local generated OS process/fault/cleanup
records, run/static/packaging scripts and identical RED test bytes. Token files
are excluded. No remote-server files were accessed/copied. No full author Gate,
DS/GPU/H100/model/real evaluation, V3/G2 merge, or M/B Resume relaxation occurred.
Historical846PASS is not new-pair acceptance. Full new-pair collection is expected
to add23 tests (869 total); it was not run and still requires the next review gate.

Raw JUnit/pytest tracebacks and patch context retain their original whitespace.
An all-artifacts whitespace diff check can report those forensic originals;
production/test/doc diff hygiene passed separately. Evidence bytes are not
normalized after execution.
