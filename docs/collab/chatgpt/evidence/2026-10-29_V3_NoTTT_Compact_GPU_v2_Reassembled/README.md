# v2 No-TTT Compact 4-rank GPU parity — Uploaded split artifacts

User supplied one 573-line v2 Harness and sixteen rank JSON chunks. Four 7,344-line JSON objects independently reconstructed and parsed (rank0–3). The first 2,000-line fragment is identical for all four ranks, appearing as uploaded pieces 5,6,10; uploaded pieces 14,15 also match byte-for-byte. No distinct chunk was lost.

Chunk index (uploaded part numbers): rank0=[5,14,16,17]; rank1=[6,11,12,13]; rank2=[10,7,8,9]; rank3=[5,2,3,4].

Local reconstructed SHA256 (UTF-8/LF):
- rank0: `10ff7564e70d2d726ea3510202ba0d0a11d4602ce8618534cf345d239d0c6748`
- rank1: `1bf095cbb5803a4fd3b96ba335bba850994f50935fd6dfc5eba600d47a375260`
- rank2: `f72b61abd6ccd8df402d3cde8412f5e0bb0daa5247bf0f51362da6df4e21cd08`
- rank3: `132c81ec536a981d04c62fee867d2b63943169b7e51fcd07397970f2807ac4a0`

The Harness was transmitted through a rich text channel that converted some Python dunders to Markdown-style `**version**`, `**name**`, `**main**`. This text is archived exactly as provided but is not known byte-identical to the executed server Python source; do not execute it as-is.

Review findings: 294 optimizer-selected gradients across all ranks and strict FAIL_PARITY are supported. `input_fingerprint` stores merely the strings `list`/`int` for each top-level batch value, rather than nested tensor values; non-scalar output fields are stored as shape/dtype or truncated repr. The claimed full native input/output content parity was not directly tested. This is an Evidence-only limitation, not a confirmed Compact production bug.
