# No-TTT Compact GPU parity — user-provided six-file evidence, 2026-10-29

These six items came directly from the user's ChatGPT file uploads, **not** from a live training server or the author's remote branch. They are source evidence, not an independently re-executed parity test.

- `DS_PRO_summary.md`: full uploaded 416-line DS_PRO report, preserved as textual evidence.
- `gpu_paired_harness_as_pasted.txt`: uploaded 445-line harness retained as plain text because the upload contains Markdown-corrupted dunders `torch.**version**` and `if **name** == "**main**"`; as pasted it **does not compile**. This is a source-fidelity warning, not proof that the executed server version was invalid.
- `rank0.json`–`rank3.json`: complete supplied JSON objects, parsed and normalized for JSON compatibility by replacing non-breaking-space indentation with ordinary spaces; no result values changed.
- The harness's output schema has `intrinsic_noise`, `compact_effect`, and `diagnostic`; it does **not** have a `grad_parity` key.
- Upload SHA256 (unmodified original files, calculated on mounted bytes):
  - DS_PRO_summary.md: `b0fd0af09b553681d44872dfc91a52538a595f55092cc5f6b2acff0c4b63ab41`
  - gpu_paired_harness_as_pasted.txt: `d7f40de8af7d7197a725790cdefa01ae845360ef112311510d840e0cdb6d9f90`
  - rank0.json: `a7ba3cd45f483ebf77f2014686384fc70029985ba8ece887c3bde3620409eeea`
  - rank1.json: `b7ccdf528bf5c5cf3a74022afa46ca687d4e961be62661ec3cdfe7fe9831a9c5`
  - rank2.json: `089c06bb93cfd72b0a2d036aa6366dbdc4633f2c7b2cc6ff6a5bba0eaa57297b`
  - rank3.json: `4b08a6b1097bf2eb15c154c50a41fe3fc66c541378a18e75ccd373ecb42cef34`
- Frozen source implementation remains historical root `49df7f3c2e0ba8ef5871f9dd490e41fbc3dc5da9`, child/Gitlink `746c5cf2f2324104a62fb71510343aa40d3976c5`.
- The reviewer found serious Evidence-only issues: the harness did not perform production optimizer-selected parameter freezing, used a non-frozen heuristic for `local_pass`, and did not directly compare complete native input/output and unchanged model buffers. See the matching review in `docs/collab/chatgpt/reviews/`.
- No production code, training job, checkpoint, GPU configuration, or data was changed by this archive.
