# R09-B2 P4-v4 Execution Request `environment` 静态合同 v0.1

**状态**：draft；仅申请 root static parser/validator tooling 与 stdlib CPU fixtures。本合同承接已关闭的 `entry`、`source`、`interpreter` sections；不授权真实 P4-v4 preflight、staging/materialize、candidate、record/refreeze、P5 export/compose、torchrun、GPU/CUDA 或训练。

## 1. 目的与边界

`environment` 是未来 P4 candidate 写入最终 P5 payload 的唯一环境 authority。它不从 Codex、shell、tmux 或 parent `os.environ` 继承任何值；也不在本静态步骤创建目录、读取模型/数据/checkpoint 或启动 child。

该 section 固定为：

```text
{
  "effective_environment": {"set", "unset", "inherit_allowlist", "sha256"},
  "native_loader_environment": {"set", "unset", "inherit_allowlist", "sha256"},
  "identity_sha256": "<canonical-sha256-without-self>"
}
```

所有 key/value 均为字符串；两个 `sha256` 分别是删除自身字段后的 canonical JSON SHA256，外层 `identity_sha256` 是删除自身字段后的 canonical JSON SHA256。额外、缺失、非 lowercase 64-hex digest、非 canonical list 顺序均 FAIL。

## 2. Empty-parent effective environment

两个环境对象均强制 `inherit_allowlist=[]`。`native_loader_environment.set={}`；其 `unset` 与 `effective_environment.unset` 精确为 P5 v4 已冻结的有序 `P5_FORBIDDEN_ENVIRONMENT`：

```text
GLIBC_TUNABLES, LD_AUDIT, LD_ASSUME_KERNEL, LD_BIND_NOT, LD_DEBUG,
LD_DEBUG_OUTPUT, LD_LIBRARY_PATH, LD_ORIGIN_PATH, LD_PRELOAD, LD_PROFILE,
LD_SHOW_AUXV, LD_TRACE_LOADED_OBJECTS,
LD_USE_LOAD_BIAS, MASTER_ADDR, MASTER_PORT, PYTHONPATH, RANK, WORLD_SIZE,
LOCAL_RANK
```

实现必须使用一份无重复的冻结 tuple，并须与 P5 的 tuple 字节序逐项相等。任何 `set` key 落入此 forbidden 集合、`set`/`unset` 相交、native loader 有 set 项、或 parent 环境值影响输出均 FAIL。

`effective_environment.set` 只能来自已经由 P4 D005 verifier 验证的 `environment.set`，并须在同一 source/asset authority 下由后续 section 独立重算其 path/value binding；本 section 本身不自证路径、资产或 D005。它只固定投影规则：剔除所有 forbidden key，保留其他 D005 固定键值；不得引入新键。`PYTHONPATH` 永不进入 effective environment，未来只由已验证 `runtime_sys_path` section 表达。

P5 child 的最终 effective map 必须由该 `set` 加 P5 固定 `LC_CTYPE=C.UTF-8` 从空 map 构造；该 locale 不允许写入 request `set` 或被 unset。

## 3. 双 backend 不变量

recurrent 与 ttt_fast_weight 的两个 environment sections 必须各自有效，且 `native_loader_environment` 完全相等。比较两个 `effective_environment.set` 时，唯一允许不同 key 是 P3-owned `PSM_R09_B1_TTT_ENABLED`：recurrent 精确为 `"0"`，TTT 精确为 `"1"`。该键必须存在；其他任意 key/value 差异、任一 backend 缺该键、或任一 backend 使用错误值均 FAIL。

静态 validator 不得以“空差异”或环境父进程碰巧相同作为通过理由；它必须对 pair 逐键比较，且不调用 `os.environ`、`subprocess`、网络、torch 或 GPU API。

## 4. 永久 CPU fixtures 与后续边界

实现后的 stdlib CPU fixtures至少覆盖：正例；outer/effective/native identity drift；额外/遗漏/重排 forbidden key；allowlist 非空；native set 非空；forbidden set key；parent environment shadow 无影响；P3 key 缺失、反转、额外 backend 差异；以及 locale 注入仅在 P5 projection 后发生。每项 request mutation 都重算外层 identity 以命中 section validator。

本设计只请求 `APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_ENVIRONMENT_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 `file:line`）。`run`、`candidates`、`backends`、`authorities` 仍是独立 sections；在它们全部经独立静态 closure 及具体 execution request 三方批准前，`APPROVE_TO_EXECUTE_P4_V4_PREFLIGHT_CPU_ONLY` 不得重新申请。
