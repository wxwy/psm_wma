# Stage-1 v1.7 launcher freeze design v0.2（已被 v0.3 supersede）

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`

**请求的正向 verdict**：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_LAUNCHER_FREEZE_CPU_STATIC`。

> 历史设计。flag/position-aware parser contract、exact replacement tables 和具体 allowlist
> 以 `PSM-WMA_Local_Memory_v0.3.5_stage1_v17_launcher_freeze_design_v0.3.md` 为准。

## 目的与边界

v1.6 的一次 Stage-1 authority 在外层临时 wrapper 的 payload SHA 重演失败时零 mutation
退出；该 authority 已耗尽且不得重试。此文档只冻结一个 root-only、stdlib-only、纯
launcher-replay module 与 direct temporary CPU/static tests 的实现合同；不构造 v1.7
request，也不授权 Stage-1 materialization。

模块不执行 `git`、不访问项目路径、不开 FD、不调用 `os.execve`，也不提供 `main()`。
未来经独立授权的 production wrapper 负责从 `formal_parent` 的 Git blob 读取 base，并在
调用此纯函数前验证 blob OID；它只能消费本模块已核验的输出，不能在本模块外手写或替换
payload。测试只调用纯函数，不触及 production wrapper 或任何真实 I/O。

## 冻结公开 API 与失败合同

实现只暴露下列 stdlib 数据类、异常和纯函数（名称、参数和返回语义不得漂移）：

```python
@dataclass(frozen=True)
class ReplayBinding:
    formal_parent: str
    base_path: str
    base_blob_oid: str
    base_raw_sha256: str
    base_bytes: int
    parser_replacements: tuple[tuple[str, str], ...]
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

`base_source` 是调用者已从 `binding.formal_parent:binding.base_path` 取得、并已将 Git
blob OID 绑定为 `binding.base_blob_oid` 的原始 bytes；纯函数先检查其 length 与 SHA-256
等于 binding，随后解析 `RAW[2]`。它拒绝 base 内既存 owner-FD flag，唯一在
`--bootstrap-project-root` value 后插入相邻的
`binding.owner_fd_flag`, `binding.owner_fd_value`。`parser_replacements` 与
`source_replacements` 都是有序、无重复 key 的 `(old, new)` pair：前者只能对已解析 argv
的完整 value 作一次替换，后者只能在 splice parser 后的 Python source 作一次替换；缺失、
额外、重复或非唯一命中均属 `replay_drift`。函数按这两张冻结替换表重演 parser 与 outer payload，并逐项检查
返回的 parser/outer bytes 与 SHA-256。失败一律抛出
`AuthorityReplayError("BLOCKED_AUTHORITY_NOT_CLOSED:<category>")`，其中 category 至少区分
`base_identity`、`raw_shape`、`owner_fd`、`insert_position`、`replay_drift`；不返回部分
payload，也不执行或触发副作用。可选的未来 exec 入口不属于本 Gate，必须独立设计、实现和审核。

## 冻结 v1.6 identity 与测试矩阵

- formal parent=`08d5828cdb4c12afa3b798ff01826c91ceb8755a`；base path=`docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py`；Git blob=`af19a9eb66ecaf8bd0b92a48ab1867f105026658`；raw SHA-256=`8b0fad39857fb72e3a3eb317f4acf6f2d6e94e196935f52f07d6170e79c678dd`；bytes=`18966`。
- canonical parser=`2336` bytes / `1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333`；canonical outer payload=`18875` bytes / `658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8`。
- direct temporary CPU/static tests 必须分别证明 canonical round-trip，以及错误 base raw SHA、错误 adapter SHA、既存 owner flag、错误插入位置和任一 source-level drift 都按上述异常合同 fail-close；不得调用 `main()`、创建 clean root/index/ref/evidence、访问 source/checkpoint/data/cache。

## 最小范围与后续互锁

- 本 Gate 仅允许新增 root `tools/psm_wma/` launcher-replay module、其 direct temporary
  CPU/static test、设计/记录；child Gitlink 不变。`py_compile`、direct unittest 与
  `git diff --check` 必须通过。
- 该 implementation 获三方同 SHA 正向 verdict 后才可编码；实现 close approval 后才可由其
  frozen bytes 构造新的 v1.7 exact request。该 request 必须重新观察 freshness，绝不复用
  v1.6 observation 或其耗尽 authority。
- 本文及其可能的 implementation 均不授权 request construction、任何 Stage-1 retry 或真实
  source/checkpoint/data/cache I/O、child/runtime、GPU/CUDA/torchrun、训练、评测、推理或
  LIBERO4IN1。
