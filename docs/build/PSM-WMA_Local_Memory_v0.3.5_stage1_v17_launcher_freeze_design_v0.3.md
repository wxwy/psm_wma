# Stage-1 v1.7 launcher freeze design v0.3

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`

**请求的正向 verdict**：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_LAUNCHER_FREEZE_CPU_STATIC`。

## 范围与固定路径

本文件 supersede v0.2，仅冻结 root-only、stdlib-only、纯 replay helper 与 direct CPU/static
test 的实现设计。允许新增且只允许新增：

- `tools/psm_wma/stage1_v17_launcher_replay.py`
- `tools/psm_wma/test_stage1_v17_launcher_replay.py`

不提供 `main()`，不执行 Git、路径/FD/网络/`os.execve` I/O。未来 production wrapper（不属于
本 Gate）负责从 formal-parent Git blob 取得 base、核验 OID 后调用纯函数，并只能消费返回 bytes；
其 exec 入口须另行设计、实现、审核。v1.6 authority 已耗尽，本文不构造 v1.7 request 或任何
Stage-1 retry/materialization。

## 冻结公开 API 与错误合同

```python
@dataclass(frozen=True)
class ReplayBinding:
    formal_parent: str
    base_path: str
    base_blob_oid: str
    base_raw_sha256: str
    base_bytes: int
    parser_replacements: tuple[tuple[str, str, str], ...]
    source_replacements: tuple[tuple[str, str], ...]
    owner_fd_flag: str
    owner_fd_value: str
    expected_parser_bytes: int
    expected_parser_sha256: str
    expected_outer_bytes: int
    expected_outer_sha256: str

@dataclass(frozen=True)
class ReplayedOuterPayload:
    parser_argv_bytes: bytes
    parser_argv_sha256: str
    outer_payload_bytes: bytes
    outer_payload_sha256: str

class AuthorityReplayError(RuntimeError): ...

def replay_outer_payload(
    *, base_source: bytes, binding: ReplayBinding
) -> ReplayedOuterPayload: ...
```

`base_source` 是调用者已从 `formal_parent:base_path` 读取并以 `base_blob_oid` 绑定的原始
bytes；纯函数仅验证 length/SHA-256，不能自行读 Git。每一 parser replacement 为
`(flag, expected_old_value, new_value)`：flag 在解析后的 `RAW[2]` 中必须恰好一次，紧邻 value
必须等于 expected old，且只替换该 value。由此 `--cwd` 和
`--bootstrap-project-root` 即使旧值相同也可独立、无歧义地替换。重复 flag、缺失 flag、错误
相邻值、重排序、额外 target 或非唯一定位一律 fail-close。base 内 owner-FD flag 必须为零；仅在
`--bootstrap-project-root` 的 value 后插入相邻 `owner_fd_flag`, `owner_fd_value` 一次。

splice canonical parser 后，source replacement 为有序 `(old, new)` pair；每项只可命中一次，
不得缺失、重复、额外或非唯一。任何 base identity、RAW shape、owner-FD、parser target、source
target、长度或 SHA 漂移均抛出
`AuthorityReplayError("BLOCKED_AUTHORITY_NOT_CLOSED:<category>")`（至少
`base_identity`、`raw_shape`、`owner_fd`、`parser_target`、`source_target`、`replay_drift`）；不
返回部分 payload 且无副作用。

## canonical v1.6 binding（唯一测试输入）

- formal parent=`08d5828cdb4c12afa3b798ff01826c91ceb8755a`；base path=`docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py`；blob=`af19a9eb66ecaf8bd0b92a48ab1867f105026658`；raw SHA-256=`8b0fad39857fb72e3a3eb317f4acf6f2d6e94e196935f52f07d6170e79c678dd`；bytes=`18966`。
- owner pair=`("--bootstrap-owner-root-fd", "8")`；expected parser=`2336` bytes / `1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333`；expected outer=`18875` bytes / `658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8`。
- parser table（顺序固定）：

```text
(--formal-root, 9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5, 08d5828cdb4c12afa3b798ff01826c91ceb8755a)
(--cwd, /disk/rl/psm_wma/.authority-root-materialization-9dd2fb8, /proc/self/fd/8)
(--index, /disk/rl/psm_wma/.authority-root-materialization-9dd2fb8/.authority-root.index, /proc/self/fd/8/.authority-root.index)
(--bootstrap-project-root, /disk/rl/psm_wma/.authority-root-materialization-9dd2fb8, /proc/self/fd/8)
(--adapter-blob-oid, da782754b8e8efa0f3cae973aa68602dcda1c237, 4a51bddd15ec9a88883e3071cc550de85721599b)
(--adapter-raw-sha256, 091ea62d0a8b48429c67100c1395e62a300dc47a8d8f65c7046ba00f8205b5e9, 87e22fac98e61ba9fbf5e0c1adaf3f620365f35a04a266576c5bce4b83e9e816)
(--collection-module-blob-oid, eefde4e5b5a0965bbdcaa5390b9286a4c77f2665, 4e9f51a52e822e7e57b67aa6ff5eaab8613566c1)
(--collection-module-raw-sha256, 1b3353b0bd1342f1685062f962a7cbc1ba0dbf699bdc72c099ca470cb09cc340, 89eb3ee194f16665aea76ed4dcbaba803fc944d1e0b889d25be69d0831e68c67)
```

- source table（parser splice 后、顺序固定）：

```text
(9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5, 08d5828cdb4c12afa3b798ff01826c91ceb8755a)
(.authority-root-materialization-9dd2fb8, .authority-root-materialization-08d5828)
(da782754b8e8efa0f3cae973aa68602dcda1c237, 4a51bddd15ec9a88883e3071cc550de85721599b)
(62a7bbf5fcb609e52931639001e6db01df81f0de2a33afd41c0080eb8e903f68, bec6a57aab61fd888ef0eedce37adce227a38a299a9faded53b252c8b5901702)
```

## direct CPU/static 验收与互锁

tests 必须证明上述 canonical round-trip，并覆盖 duplicate-old-value（`--cwd` 与
`--bootstrap-project-root`）、错误 flag、错误紧邻值、reordered target、既存 owner flag、错误
adapter SHA、每种 source-table drift 和任何 base identity 漂移。仅可用 temporary bytes/fixtures；
不得调用 main 或访问 source/checkpoint/data/cache，不创建 clean root/index/ref/evidence。运行
`py_compile`、direct unittest、`git diff --check`。

实现须在本设计获三方同 SHA 正向 verdict 后才可开始；implementation close 后才能构造新的
v1.7 exact request，且必须重新观察 freshness，不得复用 v1.6 observation。本文不授权 child/runtime、
GPU/CUDA/torchrun、训练、评测、推理或 LIBERO4IN1。
