# R09-B2 P4-v4 Execution-Preflight Materialization 设计 v0.2

**状态**：draft，替代未批准的 v0.1；待三方审核。本版仅申请实现 future CPU-only reservation tooling，不申请创建或执行真实 execution request、P4 preflight、candidate、record/refreeze、P5 export/compose、GPU 或训练。

## 1. 固定前置与不变边界

前置 full static admission closure 为 root=`baf8581cac45cb2afd004e982bd867a4835edc7d`、implementation=`8535a8c670268e044f5f70eb2d53015897d8d956`、ChatGPT=`fd0055020f4aa9a4f66800b4b018062ee3ce982f`、Gitlink=`21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`。v0.1=`887fb8194bdea6539e5f8a031032f899813e8fec` 未获批准；ChatGPT review=`9727516` 的三项 implementation blocker由本版关闭。

不得改动已关闭 nested request schema、`load_execution_request()`、P5 final-evidence grammar、P3 snapshot 或 authority。公开 `main()` 必继续以 single-fd request SHA→full admission→无条件 hard-stop 结束；它不得调用本版 helper。

## 2. 唯一 admitted-request capability

实现新增 private immutable `_AdmittedRequest` capability，字段精确为 canonical `raw: bytes`、`request_sha256: str` 与由该 raw 同次 `load_execution_request(raw)` 返回的 request object。唯一构造入口是 private `_admit_execution_request(raw)`：它先调用既有 loader 成功，再重算 `request_sha256(raw)`，最后构造 capability。materialization helper 的唯一 authority 输入是此 capability，拒绝 bare dict、raw、reparsed/deep-copied request 或全局/object-id registry。

capability 不写入磁盘、不进入 JSON、不可由 CLI/ambient/global state 构造。helper 只从 capability 内的既有 `request["run"]` 读取 canonical `identity.root` 与 `run_token`；没有独立外部 token 或 path 输入，因此不存在“token mismatch”输入类别。

## 3. 精确目录 authority 与 precheck

helper 仅可在显式注入的测试 filesystem primitive 下工作；其 namespace parent 也是显式输入，必须为既有 canonical directory、绝对、无 symlink ancestor。两个 `request.run.<backend>.identity.root` 必为该 namespace 的 direct child、彼此不同、由已关闭 request validator 保证为 future/nonexistent，且不与 source/candidate/其他 backend 重叠。helper 不读取 cwd、环境、PATH 或任何 ambient path。

对每个固定顺序 `recurrent`、`ttt_fast_weight`，唯一路径由 admitted request 派生：

```text
<run_root>/
<run_root>/import_staging/
<run_root>/import_staging/<run_token>/
```

六个路径均在任何 mkdir 前按 nofollow lexical rule预检：每个预期 parent 的现存部分均为实目录且无 symlink；每个待建目录均不存在；三个路径及两 backend footprints 两两不重叠。任何 precheck FAIL 时零 mkdir。

## 4. 精确创建序列与 truthful partial terminal

所有 precheck 成功后，唯一允许的创建顺序为：recurrent 的 root、`import_staging`、token leaf，随后 TTT 的同三步。每一步是一次显式、不带 `parents=True` 的 nofollow-safe mkdir；不得递归创建、rename、copy、删除或 cleanup。每次 mkdir 后立即以 nofollow stat 确认只创建了该预期实目录。

成功时 helper 返回 private `ReservationResult(status="RESERVED", created_paths=<ordered six paths>)`，之后只能 `STOPPED`，不代表 source 已 materialized，也不产生 candidate/P5 payload。

任一 mkdir/stat 在第 *n* 个 mutation 点失败时，helper 返回或抛出唯一 private `ReservationPoisonedError`，包含精确 ordered prefix `created_paths[:n-1]`、failed path 与原始失败类型；其语义为 `POISONED` terminal。该 prefix 是唯一允许的 partial footprint，身份 (`run_root`,`run_token`) 永久消耗：禁止 cleanup、retry、repair、rename、reuse 或转为 RESERVED。未发生 mutation 的 precheck FAIL 不进入 POISONED。该模型如实表达普通顺序 mkdir 无法跨两个 root 原子提交的事实。

## 5. 禁止范围与无副作用 CLI

helper 不得读取或调用 Git、subprocess、Python child、P5 exporter/verifier、`stage_atomic_publication()`、网络、torch、GPU、模型/数据/checkpoint；不得 source copy、manifest/roster/ELF/Python closure 枚举、payload/candidate/evidence/Git commit。测试唯一 I/O 是显式临时 namespace 中上述六种目录及其 nofollow stat；`TemporaryDirectory` 退出回收仅是 fixture 生命周期，不构成 helper cleanup。

公开 CLI 仍永远 hard-stop，因此本 Gate 后生产运行的零目录创建是验收条件。真实 request/preflight/materialization 须另起 exact-request Gate 并获三方 `APPROVE_TO_EXECUTE_P4_V4_PREFLIGHT_CPU_ONLY`。

## 6. 静态实现、fixtures 与验收

若获批准，只能修改：

- `tools/g0/r09_b2_p4_v4_execution_preflight.py`；
- `tools/g0/test_r09_b2_p4_v4_execution_preflight.py`。

stdlib fixtures 必证明：bare dict/raw/reparse 不能调用 helper；capability SHA/raw/request binding；六步成功固定顺序和精确 footprint；每个 precheck 拒绝均零 mkdir；在每一个六步 mkdir/stat mutation 点注入失败时 exact poisoned prefix、failed path、无 cleanup/重试；成功或 poisoned identity 均不可第二次使用；不访问 ambient、不调用 subprocess/P5/child；`main()` hard-stop 且零 reservation。

```text
cd /disk/rl/psm_wma
python -B -m unittest tools.g0.test_r09_b2_p4_v4_execution_preflight -v
python -m py_compile tools/g0/r09_b2_p4_v4_execution_preflight.py tools/g0/test_r09_b2_p4_v4_execution_preflight.py
git diff --check
```

仅 CPU、无网络/GPU、无模型/数据/checkpoint 输入；产物仅临时测试目录。PASS 要求全部 fixture、编译、diff-check 成功且 CLI 零 reservation；任一越界 I/O、未定义 partial footprint、CLI 调用 helper 或任何禁止路径为 FAIL。

本版请求 verdict：`APPROVE_TO_IMPLEMENT_P4_V4_PREFLIGHT_MATERIALIZATION_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 `file:line`）。
