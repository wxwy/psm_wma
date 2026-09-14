# Stage-1 v1.7 request-instance design v1.0

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`。

本版只落实 v0.9 formal review 的唯一 HIGH：不再从测试、环境、历史推断或额外 Git object 获得 `ReplayBinding`。P0 直接以本文件的完整、顺序敏感字面值实例化唯一 canonical binding；任一字段、行数、行序、身份或预期输出漂移均在 replay 前 fail-close。v0.9 的 closed object allowlist、P0/P1 non-consuming、C-before-first-freshness 的唯一消费与 no-retry 语义全部不变。

## P0 closed immutable-object allowlist

P0 仅可读取下表三个已有 Git object；`ReplayBinding` 不是第四个可读取 object，而是下节的完整 frozen literal。拒绝 future request root、worktree、测试对象、环境、历史副本及任何未列 root/path/blob。

| object | root/path/blob | identity | role |
|---|---|---|---|
| replay base | `08d5828cdb4c12afa3b798ff01826c91ceb8755a:docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py` / `af19a9eb66ecaf8bd0b92a48ab1867f105026658` | 18966 bytes; SHA-256 `8b0fad39857fb72e3a3eb317f4acf6f2d6e94e196935f52f07d6170e79c678dd` | injected `base_source` |
| replay helper | `50b0bffeb4c94b0994d7c7bf705077fb51a9e48f:tools/psm_wma/stage1_v17_launcher_replay.py` / `74455fce6ca90ede8d9935d893a7a74f5667c687` | 5582 bytes; SHA-256 `8f55dc32a77810d848c10ac55501754f741d42bd3ef3fbc386f0814b2a6d5e82` | pure replay implementation |
| adapter | `08d5828cdb4c12afa3b798ff01826c91ceb8755a:tools/psm_wma/materialize_immutable_source_authority_root.py` / `4a51bddd15ec9a88883e3071cc550de85721599b` | 91814 bytes; SHA-256 `87e22fac98e61ba9fbf5e0c1adaf3f620365f35a04a266576c5bce4b83e9e816` | P1 injected adapter bytes |

P1 reuses only the previously closed injected-byte projection helper `079167743685247d6aae62a671436e834411a3cb:tools/psm_wma/stage1_v17_request_projection.py` / blob `4a6e2c1b488ee8cb31f585b04f88a1d1780a9368`; it is not read by P0 and no other helper object is allowed.

## Canonical ReplayBinding literal authority

P0 constructs exactly this `ReplayBinding`, without loading `test_stage1_v17_launcher_replay.py` or any other source of values:

```text
formal_parent = 08d5828cdb4c12afa3b798ff01826c91ceb8755a
base_path = docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py
base_blob_oid = af19a9eb66ecaf8bd0b92a48ab1867f105026658
base_raw_sha256 = 8b0fad39857fb72e3a3eb317f4acf6f2d6e94e196935f52f07d6170e79c678dd
base_bytes = 18966
owner_fd_flag = --bootstrap-owner-root-fd
owner_fd_value = 8
expected_parser_bytes = 2336
expected_parser_sha256 = 1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333
expected_outer_bytes = 18875
expected_outer_sha256 = 658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8

parser_replacements (ordered, exactly 8):
1. (--formal-root, 9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5, 08d5828cdb4c12afa3b798ff01826c91ceb8755a)
2. (--cwd, /disk/rl/psm_wma/.authority-root-materialization-9dd2fb8, /proc/self/fd/8)
3. (--index, /disk/rl/psm_wma/.authority-root-materialization-9dd2fb8/.authority-root.index, /proc/self/fd/8/.authority-root.index)
4. (--bootstrap-project-root, /disk/rl/psm_wma/.authority-root-materialization-9dd2fb8, /proc/self/fd/8)
5. (--adapter-blob-oid, da782754b8e8efa0f3cae973aa68602dcda1c237, 4a51bddd15ec9a88883e3071cc550de85721599b)
6. (--adapter-raw-sha256, 091ea62d0a8b48429c67100c1395e62a300dc47a8d8f65c7046ba00f8205b5e9, 87e22fac98e61ba9fbf5e0c1adaf3f620365f35a04a266576c5bce4b83e9e816)
7. (--collection-module-blob-oid, eefde4e5b5a0965bbdcaa5390b9286a4c77f2665, 4e9f51a52e822e7e57b67aa6ff5eaab8613566c1)
8. (--collection-module-raw-sha256, 1b3353b0bd1342f1685062f962a7cbc1ba0dbf699bdc72c099ca470cb09cc340, 89eb3ee194f16665aea76ed4dcbaba803fc944d1e0b889d25be69d0831e68c67)

source_replacements (ordered, exactly 8):
1. (9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5, 08d5828cdb4c12afa3b798ff01826c91ceb8755a)
2. (.authority-root-materialization-9dd2fb8, .authority-root-materialization-08d5828)
3. (da782754b8e8efa0f3cae973aa68602dcda1c237, 4a51bddd15ec9a88883e3071cc550de85721599b)
4. (62a7bbf5fcb609e52931639001e6db01df81f0de2a33afd41c0080eb8e903f68, bec6a57aab61fd888ef0eedce37adce227a38a299a9faded53b252c8b5901702)
5. (7538, 9406)
6. (7e1c0ecc2161984a88ea0d0eae82f9f7ced709ca919f0302f74a3a068e08c9b8, ccd8ee2772d666707c919e6a20376c997771b9ff068fe0432fdaa96c686ab097)
7. (2427, 2336)
8. (72777bd7305c760c48c069eafd068f1a538383a6fdb8d40258acf3d8fc3b7ae2, 1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333)
```

Before replay, construction verifies all three object identities, every literal scalar, both table counts and exact ordering, and rejects any alternate field or source. It then calls only `replay_outer_payload(base_source, binding)`. The result must be exactly the expected parser identity and derived outer `18875` / `658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8`; the outer is derived bytes, never a Git object. Only verified derived outer plus verified adapter bytes enter P1.

## Consumption boundary

P0 acquisition/identity/literal construction and P1 injected-byte projection are non-consuming. C starts immediately before its first freshness observation, consumes the sole construction authority, and any C failure is terminal with no retry. This design creates no request, no output path and no runtime action.

Requested verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or `REQUEST_CHANGES(file:line)`.

Still prohibited: request construction before same-pair approval; all materialization/retry, launcher/materializer execution, source/checkpoint/manifest/data/cache I/O, child/runtime mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.
