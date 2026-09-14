# Stage-1 v1.7 request-instance design v0.9

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`。

本版仅关闭 v0.8 review 的两项 HIGH；保留 v0.7 的 P0/P1/C、C-before-freshness 消耗、one-attempt/no-retry 与全部禁止范围。

## P0 唯一 closed immutable-object allowlist

P0 只能从下表已经存在的 Git object 读取，拒绝所有其他 root/path/blob：

| object | root/path/blob | identity | role |
|---|---|---|---|
| replay base | `08d5828cdb4c12afa3b798ff01826c91ceb8755a:docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py` / `af19a9eb66ecaf8bd0b92a48ab1867f105026658` | 18966 bytes; `8b0fad39857fb72e3a3eb317f4acf6f2d6e94e196935f52f07d6170e79c678dd` | injected `base_source` |
| replay helper | `50b0bffeb4c94b0994d7c7bf705077fb51a9e48f:tools/psm_wma/stage1_v17_launcher_replay.py` / `74455fce6ca90ede8d9935d893a7a74f5667c687` | SHA-256 `8f55dc32a77810d848c10ac55501754f741d42bd3ef3fbc386f0814b2a6d5e82` | pure replay authority |
| adapter | `08d5828cdb4c12afa3b798ff01826c91ceb8755a:tools/psm_wma/materialize_immutable_source_authority_root.py` / `4a51bddd15ec9a88883e3071cc550de85721599b` | 91814 bytes; `87e22fac98e61ba9fbf5e0c1adaf3f620365f35a04a266576c5bce4b83e9e816` | P1 adapter input |
| projection helper | closed root `079167743685247d6aae62a671436e834411a3cb:tools/psm_wma/stage1_v17_request_projection.py` | closed injected-byte helper only | P1 projection |

P0 records source commit/path/blob/raw length/SHA for table objects only. It must not read any future request root, ambient worktree or arbitrary stored copy.

## Derived outer dataflow

P0 acquires and verifies base, helper/binding and adapter; it then derives `outer_payload_bytes` only by `replay_outer_payload(base_source, binding)`. The derived output must be exactly 18875 bytes with SHA-256 `658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8`. It is a derived result, never a Git path/blob object. Only this derived outer plus the verified adapter bytes enter P1.

Requested verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or `REQUEST_CHANGES(file:line)`.
