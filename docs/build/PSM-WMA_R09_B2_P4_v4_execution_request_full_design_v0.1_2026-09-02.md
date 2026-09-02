# R09-B2 P4-v4 Execution Request full admission 静态合同 v0.1

**状态**：draft。仅申请 future root request parser admission 与 stdlib CPU fixture；不申请也不执行真实 request、P4 preflight、run/candidate/staging materialize、record/refreeze、P5 export/compose、GPU 或训练。

前置八个 static section 已独立关闭：`entry`、`source`、`interpreter`、`environment`、`authorities`、`run`、`candidates`、`backends`。full admission 只定义它们在同一 canonical request raw 中的确定性串联，不重定义任一 section 的 schema、snapshot 或 authority。

`load_execution_request(raw)` 必继续只接受 canonical JSON、exact `REQUEST_KEYS`、固定 schema version 与 frozen `execution_contract`；并依以下固定顺序验证：`entry` → `interpreter.host_git` → `source`（传入已验证 absolute host Git）→ `interpreter`（复用同一 host Git）→ `run` → `candidates` → `backends` → `authorities`。`authorities` 固定调用 `validate_authorities_pair(request["authorities"], request, Path(request["source"]["root"]), git_path)`；其中 root 与 git_path 必为同一 invocation 已通过 source/interpreter 验证的对象，禁止 PATH/which/bare Git/fallback/新 authority 输入。authority validator 自身是唯一环境-D005 projection binding；full admission 不调用旧 `validate_environment_pair()` 或 D005 `verify_pair()`，不引入第二份 environment/P3 allowlist。

成功返回仅为已验证的内存 request object；不得创建目录、打开 future run/candidate/staging 路径、写 JSON、调用 exporter/verifier、启动 child、torchrun 或访问网络/GPU/模型/数据/checkpoint。`main()` 的 request SHA single-fd binding与无条件 `RuntimeError("P4-v4 execution requires a separately reviewed frozen execution request")` hard-stop 必保持；full admission PASS 绝不构成执行授权。

CPU fixtures 必覆盖：full valid synthetic request 经全部八 section 后仅 hard-stop；每一 section 的 reidentified mutation均 FAIL；host Git/root object identity 通过 spy 证明传入 source/interpreter/authorities 为同一已验证对象；authorities 的历史 record/verifier/environment binding 在 full route 仍被触发；拒绝调用 `validate_environment_pair`、`verify_d005_pair`、P5 exporter/verifier、subprocess（除已关闭 authorities 所需的固定 host-Git historical blob lookup）；hostile ambient independent；future run/candidate roots 不存在且未创建。fixture 可 mock 已关闭 source/interpreter/authorities 的底层 I/O 以只检验 route，不得构造真实 execution request 或触发 preflight。

若批准，仅修改 `tools/g0/r09_b2_p4_v4_execution_preflight.py` 与其 stdlib CPU test；随后必须对 implementation 重新三方 closure review。禁止真实 P4 preflight、candidate/run/staging/materialize、record/refreeze/evidence publication、P5 authority/export/compose、torchrun、GPU/CUDA、模型/数据/checkpoint I/O、训练/评测/推理、B2-T 与 Local Memory 训练。请求 verdict：`APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_FULL_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 `file:line`）。
