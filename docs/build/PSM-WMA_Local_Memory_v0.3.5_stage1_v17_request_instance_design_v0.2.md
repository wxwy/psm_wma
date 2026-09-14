# Stage-1 v1.7 request-instance design v0.2

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`。
**状态**：v0.2 docs-only remediation；显式 supersede v0.1 的 construction-time I/O authority 表述。

本设计只定义在三方同pair批准后构造一份 docs-only exact request 的最小只读观察权限；不授权 materialization、launcher execution 或任何运行时产物。v1.6 authority 已耗尽，不能复用。

## 冻结依赖

- formal parent=`08d5828cdb4c12afa3b798ff01826c91ceb8755a`，launcher base blob=`af19a9eb66ecaf8bd0b92a48ab1867f105026658`，raw=`8b0fad39857fb72e3a3eb317f4acf6f2d6e94e196935f52f07d6170e79c678dd`，bytes=`18966`。
- frozen replay implementation root=`50b0bffeb4c94b0994d7c7bf705077fb51a9e48f`：module blob/raw=`74455fce6ca90ede8d9935d893a7a74f5667c687` / `8f55dc32a77810d848c10ac55501754f741d42bd3ef3fbc386f0814b2a6d5e82`；test blob/raw=`a38bd4536d48c5178c63c595e4e02980b15af998` / `af00b4a19c027f0a59e74eb3c30e772b9a1aaecf93f7d16d60a714a7cabccff3`。
- canonical replay output remains parser=`2336/1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333` and outer=`18875/658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8`.

## 唯一 construction-time I/O allowlist

只有本设计获同pair三方 `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` 后，才能为**一份** future request 进行下列零 mutation、只读观察：

1. 读取冻结 formal parent 的 commit/tree/blob 身份与 launcher base 原始字节；将 object ID、raw bytes length/SHA 与 replay 输入绑定进 request。
2. 读取当前工作树的 `.git` identity 与 `.git/config` 原始字节；记录其 length/SHA，不改写 config、HEAD、index 或 refs。
3. 读取冻结 local ref，并仅执行一次 `git ls-remote origin refs/heads/V2`。该精确 remote-ref query 是唯一允许的网络操作；必须把命令、完整原始输出及其 bytes length/SHA 绑定进 request。不得 fetch、push、查询其他 remote/ref，或访问任何服务。
4. 只检查设计指定的 clean-root、index、ref、evidence 与 pending 目标路径是否不存在；不得创建目录、文件、artifact 或 ref。

以上 allowlist 不包含 source/checkpoint/manifest/data/cache 内容 I/O、collection/receipt/record/package/publication、runtime/service I/O、launcher/materializer/import-as-entrypoint、子模块或运行时修改，及 GPU/CUDA/torchrun、训练、评测、推理或 LIBERO4IN1。

## Construction contract

允许的构造输出路径固定为根仓 docs-only：

```text
docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.1.md
docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.1.json
```

Future construction must run the frozen pure helper against injected verified formal-parent blob bytes, then take the one same-round allowlisted zero-mutation snapshot. Canonical JSON must bind: observation time; formal/base/replay identities; `.git`/config raw identities; local and remote-ref raw observations; designated absence results; selection/config/bootstrap bytes; parser argv; six-key environment; owner-FD insertion; replay output; cwd/index/evidence targets; and the JSON's own whole bytes/SHA.

No fallback base, mixed formal parent, stale observation, inferred default, reordered argv/environment, duplicate owner-FD, request-byte mismatch, absent/extra allowlisted observation, or any non-allowlisted I/O is permitted. Each condition must fail as `BLOCKED_AUTHORITY_NOT_CLOSED` before `os.execve`; construction failure does not authorize retry under this design. The resulting exact request still needs an independent same-pair three-party request review before it can grant a single Stage-1 attempt.

Requested verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or `REQUEST_CHANGES(file:line)`.
