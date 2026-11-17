# Evidence publication readback

This note preserves the first publication rather than silently replacing it.

After publishing review-only commit `691c53034fee6a8b1427a5282489602637835ce7`, the connector-published synthetic files were fetched back on the authorized server and compared with the original execution artifacts.

- `test_review_source_contracts.py` is byte-identical to the script actually executed: SHA256 `860424fa81b6447cb361d7272ff0a365dfef6ef6087b0a3f51ab97f63fd306e0`.
- The initially transferred `reviewer_probes.log` had one transcription difference in pytest's display abbreviation on line 23: `pan_A` was written where raw pytest had `...A`. The preceding full AssertionError, all three test failures, line locations and count/timing were correct. It is retained as the initial non-byte-exact transcript.
- **`reviewer_probes.raw.log` is the canonical exact raw log copy**, matching the server's `reviewer_probes.log`: SHA256 `795bbe0f97da6e5ef0273295198b88a920ef141cb22149a0098cc9ab94bcfa11`.

The formal report's server hashes always referred to the untouched server artifacts. The aggregate `derived_review_summary.json` is explicitly a derived summary, not a copy of the complete server audit. Real-source JSON, full JUnit and private source data remain server-only.

No execution or result changed. Formal implementation remains `27ccadb051a71adf348ee14206d7ac59e9195d36`, Child `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`, verdict REQUEST_CHANGES for F1/F2. This correction adds evidence only and does not change any product or test file under g2/ or tools/.
