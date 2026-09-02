# R09-B2 P4-v4 Execution-Preflight Materialization 设计 v0.1

**状态**：draft，待三方审核。本版仅申请实现 future CPU-only preflight materialization tooling；不申请创建或执行真实 execution request、run root、candidate、staging、P4 record/refreeze、P5 export/compose、torchrun、GPU、模型/数据/checkpoint I/O 或训练。

## 1. 前置与唯一范围

本设计以前置 full static admission closure 为唯一输入：root closure=`baf8581cac45cb2afd004e982bd867a4835edc7d`，implementation=`8535a8c670268e044f5f70eb2d53015897d8d956`，ChatGPT review=`fd0055020f4aa9a4f66800b4b018062ee3ce982f`，子模块 Gitlink=`21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`。它不修改已关闭的 request nested schema、P5 final-evidence grammar、P3 snapshot 或任何 authority。

现有 `tools/g0/r09_b2_p4_v4_execution_preflight.py` 的 `main()` 已完成 single-fd request SHA binding 与 full admission，并无条件 hard-stop。本版只定义将该 hard-stop 后的**未来、未调用**实现替换为显式 internal materialization helper 的静态代码与 stdlib CPU fixture；公开 CLI 在本 Gate 结束后仍必须 hard-stop，直至另一个同 SHA execution-request Gate 明确批准一次真实调用。

## 2. 复用入口与最小修改

仅允许修改：

- `tools/g0/r09_b2_p4_v4_execution_preflight.py`；
- `tools/g0/test_r09_b2_p4_v4_execution_preflight.py`。

复用而不重写 `read_execution_request()`、`load_execution_request()`、`validate_*()`、`verified_loader_argv()`、P5 的 `load_p4_v4_preflight()` 与 `stage_atomic_publication()`。不得改动 `tools/g0/export_r09_b2_p5_resolved_config.py`、`tools/g0/r09_b2_p4_v4_static_contract.py`、Cosmos 子模块或任何 frozen artifact。

## 3. Helper 输入与副作用边界

新增 private helper 仅接收已由同一次 `load_execution_request(raw)` 返回的 canonical in-memory request，以及显式注入的 filesystem primitive。它必须拒绝未验证或重解析的 request；不得读取环境、PATH、当前工作目录、网络、Git、Python child、P5 exporter/verifier、torch 或模型/数据/checkpoint。

它只可在测试用临时目录中证明以下机制：先对两个 future backend 身份做 nofollow/lexical/non-overlap/nonexistent 检查；任何一个检查失败时不创建目标；两个均通过后以固定 backend 顺序创建空的 private staging layout。它不得复制 production source、枚举 source、生成 payload、写 candidate、调用 `stage_atomic_publication()`、创建 Git commit 或发布证据。

## 4. 固定原子状态机

状态只允许 `ADMISSION -> RESERVED -> STOPPED`。`ADMISSION` 是既有 full parser 成功；`RESERVED` 只代表两个临时测试目录已以一次 mkdir 取得，并不表示 materialized；随后必须 `STOPPED`。没有 PASS、FAIL、retry、cleanup、rename 或 resume 状态。

任一 backend 的 root 已存在、路径为 symlink、祖先为 symlink、两 backend root 或 staging 重叠、token 不匹配、非空目录、第二次调用、环境/工具调用或写入白名单外路径，必须 fail-closed。失败后不得清理或尝试第二次创建；测试使用 `TemporaryDirectory` 的生命周期回收不构成 production cleanup 行为。

## 5. I/O allowlist 与禁止路径

测试允许的唯一 I/O 是由测试传入的临时根中，两个 `<run_root>/import_staging/<run_token>` 空目录的 mkdir 与最小 stat/nofollow 检查。生产 CLI 不调用 helper，因而不产生 I/O。实现不得新增 `subprocess` 调用；既有 admission 的 validated host-Git 读取不变。

永久禁止：source copy、manifest/roster 生成、ELF/Python closure 枚举、candidate payload、P5 payload verifier、child process、网络、GPU、torch、torchrun、模型/数据/checkpoint、P4 record/refreeze、P5 authority 更新、export/compose、训练/评测/推理/B2-T。

## 6. CPU fixture 与验收

stdlib fixture 必覆盖：成功的双 backend 固定顺序 reservation；第二 backend 检查失败时零 mkdir；每种 symlink/ancestor/overlap/existing/nonempty/token mismatch；重复调用；只写测试临时 allowlist；不访问 ambient environment；不调用 subprocess/P5/static publication/child；公开 `main()` 继续 hard-stop 且零 materialization。

验收命令（仅实现批准后、CPU、无网络/GPU、无输入资产、仅临时目录）：

```text
cd /disk/rl/psm_wma
python -B -m unittest tools.g0.test_r09_b2_p4_v4_execution_preflight -v
python -m py_compile tools/g0/r09_b2_p4_v4_execution_preflight.py tools/g0/test_r09_b2_p4_v4_execution_preflight.py
git diff --check
```

PASS：全部定向 CPU fixture、编译与 diff 检查通过，且 fixture 证明 CLI 无副作用。FAIL：任一拒绝断言、白名单外 I/O、工具调用或 CLI 不再 hard-stop。产物仅为测试临时目录，退出后不存在；不得落盘 artifact、candidate 或日志。

## 7. 后续 Gate 与停止条件

本版 implementation closure 不授权真实 execution request。只有另起、冻结具体 request SHA/source revision/run roots/candidate roots/attempt/token 的 execution Gate，且三方对该同一 SHA 明确给出 `APPROVE_TO_EXECUTE_P4_V4_PREFLIGHT_CPU_ONLY` 后，才可将已验证 helper 接入一次 CLI 调用。该后续 Gate 仍不授权 record/refreeze 或 P5 export/compose。

本版请求 verdict：`APPROVE_TO_IMPLEMENT_P4_V4_PREFLIGHT_MATERIALIZATION_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 `file:line`）。
