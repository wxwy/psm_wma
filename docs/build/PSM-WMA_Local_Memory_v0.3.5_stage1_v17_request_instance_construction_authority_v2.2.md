# Stage-1 v1.7 request-instance construction authority v2.2

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-CONSTRUCTION-AUTHORITY-V22`。
**状态**：docs-only；不执行真实 pre-C、C 或 request-pair 写入。

## 唯一目的

在已关闭 `ContractV05`、`FreshnessGuardV1` CPU/static Gate 后，为一份从未存在的 future v0.5 JSON/Markdown pair 定义一次且仅一次 construction authority。v1.8/v0.4 authority 已永久消费且零输出，绝不重试、补写或复用。

## 授权前完整 rehearsal

真实 pre-C 必须先完成并封存同一不可复制 `SealedPreCPlanV1`：C01--C15 exact closure、九条 local freshness identities、remote pre-C-only query facts、唯一 `PatchConsumerV1` 与 `FreshnessGuardV1` identity、strict-UTF-8 canonical JSON/Markdown/patch bytes、exact two output paths、post-write verifier、same-object `patch_text` handoff。pre-C 不写输出、不调用 consumer；任一缺失或 drift 均在 C 前停止且 authority 未消费。

## C 的唯一事务

获得独立 construction approval 后，C 仅执行：

```text
sealed FreshnessGuardV1 -> FRESH
→ exactly one opaque apply_opaque_v1(descriptor, sealed patch_text)
→ sealed byte-for-byte readback of exact pair
→ hard stop pending independent pair review
```

C 不接收 Closure/path/query/name/schema/bytes 参数；不做 discovery、remote query、动态 import、格式生成或路径推断。guard `STALE`/`UNKNOWN`/异常及所有 call 后失败均消费 authority、禁止 retry/repair/cleanup/第二次 call。

## 验收

- C 前所有未来 C 对象、bytes、callable、lease、environment、outputs/readback 已封存；
- C 只有上述四步；
- 成功只产生 future pair，随后 hard stop，不授权 materialization/source-evidence/GPU/训练；
- 独立三方批准后才可执行这一次 C。

Requested verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or `REQUEST_CHANGES(file:line)`.

仍禁止：真实 pre-C/C、request-pair、materialization、source-evidence、真实 I/O、child/runtime/config mutation、GPU/CUDA/torchrun、训练、评测、推理、LIBERO4IN1。
