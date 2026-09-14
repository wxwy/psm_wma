# Stage-1 v1.7 request-instance recovery design v1.5

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V15`。
**状态**：仅 docs-only remediation；不复用任何已消费 construction authority。

v1.4 的 future tuple、P0/P1/C lifecycle、single patch consumer 与 terminal residue policy保持；本版只关闭 DS 的 two precision findings。

## patch consumer type seam

Producer constructs `patch_raw: bytes` and validates UTF-8 strictly. It then creates exactly once
`patch_text = patch_raw.decode("utf-8", "strict")`; this is a type conversion, not decoding/reconstruction of content.
Consumer is exactly `apply_patch(patch_text)`. Before invocation it requires
`patch_text.encode("utf-8") == patch_raw`, and binds both `(len(patch_raw), sha256(patch_raw))` and
`(len(patch_text.encode("utf-8")), sha256(patch_text.encode("utf-8")))`. No other bytes/str conversion,
patch parser, escaping, formatting, stdout/context copy, shell redirection, Python write or temporary file is allowed.

## exact line encoder and round-trip witness

Both producer raws are UTF-8, contain no CR, end in exactly one LF, and contain no line beginning `*** `. Define:

```text
lines(raw) = raw[:-1].split(b"\n")
encode_add(path, raw) = b"*** Add File: " + path.encode("utf-8") + b"\n" +
                        b"".join(b"+" + line + b"\n" for line in lines(raw))
```

The pre-consumer witness must use in-memory fixtures covering an ordinary final line, an empty final content line and
consecutive empty lines. Its inverse removes exactly one leading `+` from every encoded payload line and joins payload
lines with `\n`, appending exactly one terminal LF; it must equal the original raw byte-for-byte for every fixture.
The actual producer then runs the same inverse witness against `json_raw` and `markdown_raw` before deriving
`patch_raw`. `patch_raw` is exactly one `*** Begin Patch\n`, the JSON add block, the Markdown add block, and one
`*** End Patch\n`.

After the single `apply_patch(patch_text)` returns, C still requires both files equal their original raw producer bytes.
Any conversion, witness, consumer, partial-residue or equality failure remains terminal and non-retryable.

This document authorizes no construction, materialization, runtime, source I/O, child mutation, GPU or training.
Requested verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or `REQUEST_CHANGES(file:line)`.
