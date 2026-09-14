# Stage-1 v1.7 request projection preflight design v0.2

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-PROJECTION-PREFLIGHT-CPU-STATIC`。
**状态**：仅 docs-only v0.1整改；与v0.1冲突时以本文为准。无Git、remote、filesystem、subprocess、request输出或authority消费。

## 冻结实现范围与输入

获批准后只允许新增：

```text
tools/psm_wma/stage1_v17_request_projection.py
tools/psm_wma/test_stage1_v17_request_projection.py
```

唯一API为：

```python
project_request_closure(
    outer_payload_bytes: bytes,
    adapter_source_bytes: bytes,
) -> ProjectedRequestClosure
```

调用方必须先独立验证注入输入：outer=`18875/658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8`；adapter source=`4a51bddd15ec9a88883e3071cc550de85721599b/87e22fac98e61ba9fbf5e0c1adaf3f620365f35a04a266576c5bce4b83e9e816`。helper自身再次验证这两条identity；缺失或漂移即`BLOCKED_AUTHORITY_NOT_CLOSED:projection_input_identity`。adapter bytes仅用AST静态提取唯一顶层`bootstrap_payload`的允许return常量，不读路径、不执行代码。

## Frozen result schema

```python
@dataclass(frozen=True)
class ProjectedBytes:
    raw: bytes
    byte_length: int
    sha256: str

@dataclass(frozen=True)
class ProjectedRequestClosure:
    selection: ProjectedBytes
    config: ProjectedBytes
    parser_argv: ProjectedBytes
    parser_argv_items: tuple[str, ...]
    bootstrap: ProjectedBytes
    bootstrap_contract: ProjectedBytes
    outer: ProjectedBytes
    adapter_source: ProjectedBytes
```

`ProjectedBytes` 必须满足`byte_length == len(raw)`、`sha256 == hashlib.sha256(raw).hexdigest()`；所有比较按上述字段顺序逐项精确相等。bootstrap contract必须是`{"bootstrap_argv_sha256":...,"bootstrap_raw_sha256":...}`的UTF-8、sorted-key、compact JSON bytes。

## AST 与 argv contract

outer `RAW` 必须唯一且恰三项：前两项唯一接受`base64.b64decode`的name target和单个ASCII `str`/`bytes` literal argument；第三项必须为bytes/string JSON literal。adapter `bootstrap_payload()`必须唯一、零位置参数、函数末尾唯一return；return只接受递归`Constant(str|bytes)`及左右都允许节点的`BinOp(Add)`，禁止Name、Call、Attribute、format、container、控制流或其他node。

parser argv必须是canonical compact JSON、全量`str`数组、精确匹配冻结ordered flag/value table。允许重复**value**（canonical `--cwd`与`--bootstrap-project-root`均为`/proc/self/fd/8`）；拒绝重复、缺失或额外**flag**、flag/value错邻接、非字符串和任何whole-bytes/SHA漂移。

任一AST/identity/JSON/flag失败均只抛`AuthorityReplayError("BLOCKED_AUTHORITY_NOT_CLOSED:projection_<category>")`，绝不返回部分结果。

## CPU/static evidence 与互锁

测试只嵌入gzip/base64冻结outer及adapter fixture；不得`git show`、subprocess、network、路径读写或启动payload。覆盖positive、两输入identity、RAW target/arity、adapter signature/return node、base64/JSON、合法重复value、duplicate flag/adjacency、每个result identity、contract和partial failure。

本实现及测试成功仍不恢复v0.5 consumed authority，也不授予construction authority；需独立close review后再新建construction design。禁止materialization、launcher、source/checkpoint/manifest/data/cache/runtime I/O、child、GPU及训练。

Requested verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_REQUEST_PROJECTION_PREFLIGHT_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
