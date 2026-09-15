# Stage-1 v1.7 exact-plan pre-C authority v2.3

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-EXACT-PLAN-PRE-C-AUTHORITY-V23`。
**状态**：docs-only；由 V22 `REQUEST_CHANGES` 收敛而来。

## 唯一目的

只授权一次真实、non-consuming 的 pre-C rehearsal，以获得未来不可逆 C 所实际使用的唯一 capability / guard / verifier 的精确身份。它不授权 C 或任何 pair 写入。此拆分是 V22 审核指出的实质 authority 缺口，不是字段、路径或格式的横向 Gate。

## pre-C 前冻结的执行边界

pre-C 只允许读取并封存，绝不调用 `apply_opaque_v1`，绝不创建、删除、改写或修复任何路径。它必须一次性完成并产生不可复制 `SealedPreCPlanV1`；C01--C15、九条 freshness identity、remote-pre-C-only 事实、strict UTF-8 JSON/Markdown/patch bytes、exact 两输出路径、same-object `patch_text`、六键环境及 output/readback absence 均沿用 ContractV05，不得重新推断。

对三个实际 host callable，pre-C 同时封存下列 literal，而非只做 self-consistency 校验：

| role | 必须封存并供下轮审查的 identity |
| --- | --- |
| PatchConsumerV1 | provider、module、path、source blob SHA-256、callable qualname、ABI、transport、descriptor identity |
| FreshnessGuardV1 | provider、module、path、source blob SHA-256、callable qualname、ABI、transport、九条 typed lease-domain SHA identity |
| post-write verifier | provider、module、path、source blob SHA-256、callable qualname、ABI、transport、exact readback paths/bytes predicate |

每个 `path` 是 canonical repository-relative path；每个 blob 是从该 path 的 exact bytes 取得的 SHA-256；callable 只能由该 frozen module 解析一次。任何缺项、非唯一解析、blob/path/qualname/ABI/transport 不匹配、remote query 发生在 C-time、或任何 write intent，均为 pre-C FAIL：停止且 C authority 未消费。

## pre-C 的唯一产物和 hard stop

pre-C 只在进程内形成 sealed plan；不得写 request pair、receipt、cache、sidecar 或 evidence 文件。结束后必须输出一份只读 exact-plan review record，其中逐字列出上表三组 literals、九条 identities、pair raw SHA/length、patch SHA/length、two paths、six-key environment、local/remote V2 与 authority-ref facts、designated absences 以及 post-write predicate。随即 hard stop。

该 record 的独立三方 exact-plan approval 是唯一允许进入 C 的后续门；它一次性审查所有 future C inputs，不再分拆 provider/path/field Gate。

## 被批准后的 C（本 Gate 不授权）

只有 exact-plan review 全批准后，C 才严格为：

```text
sealed literal FreshnessGuardV1 -> FRESH
→ one sealed literal PatchConsumerV1.apply_opaque_v1(descriptor, same patch_text)
→ sealed literal verifier byte-for-byte readback
→ hard stop
```

C 不解析名称、不 import、不查询、不生成 bytes、不推断路径；任意 call 后失败或异常都消费 C authority、禁止 retry/repair/cleanup/第二次 call。

## 验收与请求 verdict

- 批准范围仅为一次真实 non-consuming pre-C，且该 pre-C 不产生 filesystem 输出；
- 真实 C、request pair、materialization、source-evidence、child/runtime/config mutation、GPU/CUDA/torchrun、训练/评测/推理/LIBERO4IN1 仍禁止；
- pre-C 后必须以 exact sealed-plan 的 root/child pair 重新独立三方审核，不能复用本 Gate approval。

Requested verdict: `APPROVE_TO_EXECUTE_R09_B_TTT_V035_STAGE1_V17_EXACT_PLAN_PRE_C` or `REQUEST_CHANGES(file:line)`.
