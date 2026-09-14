# Stage-1 v1.7 request-instance recovery design v1.4

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V14`。
**状态**：仅 docs-only remediation；不复用任何已消费的 construction authority。

## 前序事实与唯一 future tuple

v1.2 的 C 已消费且零 request-pair 输出；v1.3 仅提出 producer/consumer 方向，未冻结 byte-exact
consumer seam。二者不得重试、补写或解释为执行权。future request 仍唯一为：

```text
formal_parent = 08d5828cdb4c12afa3b798ff01826c91ceb8755a
child_gitlink = 93a89ba61306d840a008813f62f26a34d54850f4
json_path = docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.3.json
markdown_path = docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.3.md
```

本文件 Gate literal 必须逐字用于 live Inbox、SESSION、TODO、future request 与所有 verdict；不能以旧
`...RECOVERY-DESIGN` 或 `...V13` 替代。

## future single-C deterministic consumer seam

P0（冻结 object acquisition）与P1（injected-byte projection）仍为non-consuming。只有本版获同pair
三方 `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` 后，才可获得一次 future C。
C 仍在第一个 freshness observation 前开始并永久消费。

C producer 在内存生成`json_raw`和`markdown_raw`，并同时生成**唯一** `patch_raw`。编码是下列确定性函数，
不得人工复制、换行、escape、重新序列化或从stdout重建：

```text
encode_add(path, raw) = b"*** Add File: " + path.encode("utf-8") + b"\n" +
                        b"".join(b"+" + line + b"\n" for line in raw.splitlines())
patch_raw = b"*** Begin Patch\n" +
            encode_add(json_path, json_raw) +
            encode_add(markdown_path, markdown_raw) +
            b"*** End Patch\n"
```

Preconditions are mechanical: both raw values are UTF-8; each ends in exactly one LF; neither contains CR; neither
contains a line beginning `*** `; each path is frozen byte-for-byte; and both designated paths are absent. Producer
binds `(len(patch_raw), sha256(patch_raw), patch_raw)` together with JSON/Markdown raw length/SHA and the JSON Git-blob
preimage OID. The only consumer invocation is exactly `apply_patch(patch_raw)`; its argument is the producer tuple's
unchanged `patch_raw` object, not a displayed/logged/context-reconstructed string. A future executor must preserve that
opaque handoff in one process/tool call and reject any decoder, shell redirection, Python file I/O, temporary file or
alternate patch grammar.

Immediately after the single consumer returns, C reads only the two designated paths and requires byte-for-byte equality
with the producer `json_raw`/`markdown_raw`, then checks canonical JSON, detached Markdown five-field identity, JSON
length/SHA and JSON Git-blob preimage OID. No second write is allowed.

`apply_patch` is not assumed atomic. If it fails, returns a non-success result, creates neither file, creates only one
file, or either equality/identity check fails, C records terminal `BLOCKED_AUTHORITY_NOT_CLOSED:request-patch-handoff`.
Any residue remains untouched as failure evidence; C may not delete, overwrite, complete, repair or retry it. PASS only
means both exact files exist and C hard-stops for independent request review.

## Boundaries

This design itself authorizes no construction, materialization, launcher/materializer, source/checkpoint/manifest/data/
cache I/O, collection/receipt/record/publication, child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation,
inference or LIBERO4IN1.

Requested verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or
`REQUEST_CHANGES(file:line)`.
