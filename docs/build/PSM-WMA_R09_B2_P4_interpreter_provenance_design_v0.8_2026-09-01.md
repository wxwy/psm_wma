# R09-B2 P4 Interpreter Provenance 静态设计 v0.8

**状态**：draft，待三方审核。v0.8 仅在 v0.7 上加入 ChatGPT review `2026-09-01_R09_B2_P4_interpreter_provenance_design_v07_8a1bbf5_e4dbea6.md` 要求的 native-loader environment grammar；不改变 process tree、request digest、loader、profile/source/staging 或训练语义。

## Native-loader environment grammar

execution request 的 `host_native_tcb` 新增 verifier-owned `native_loader_environment`：

```json
{
  "set": {},
  "unset": [
    "LD_AUDIT", "LD_ASSUME_KERNEL", "LD_BIND_NOT", "LD_DEBUG", "LD_DEBUG_OUTPUT",
    "LD_LIBRARY_PATH", "LD_ORIGIN_PATH", "LD_PRELOAD", "LD_PROFILE",
    "LD_SHOW_AUXV", "LD_TRACE_LOADED_OBJECTS", "LD_USE_LOAD_BIAS", "GLIBC_TUNABLES"
  ],
  "inherit_allowlist": []
}
```

这是精确的“全部 absent” profile，不允许 caller 注入 loader 搜索/审计/preload/tunable 变量。若未来生产命令确实需要其中任一变量，当前 Gate fail-closed，必须另建版本化设计/审核，而不能临时继承或放宽。

parent TCB 在使用 lexical child 前：

1. 从空环境构造 child effective environment：仅 D005 verifier-owned `environment.set`、固定 locale/rank protocol 与上述 native-loader grammar；所有 listed variable均 absent；
2. 在**这个相同环境**中重算 child ELF、dynamic loader和完整 transitive native dependency closure，并同 execution request 的 frozen canonical `(soname,path,sha256)` 列表比对；
3. 使用同一个 effective environment spawn outer/P5 child；P4 agent 向 torchrun worker转发的仅允许 rank/world keys也在 verifier-owned allowlist内，worker loader重验；任何 ambient `LD_*`、`GLIBC_TUNABLES`或未经允许的 rank/native key均不进入 child。

loader在 Python启动后断言 `os.environ` 对 native-loader grammar精确一致；但安全性不依赖此迟到检查，parent preflight与subprocess `env=` 已在 native loader执行前保证。永久 CPU-only negatives：同一 exe/dependency/request下分别注入 `LD_PRELOAD`、`LD_AUDIT`、`LD_LIBRARY_PATH`、`GLIBC_TUNABLES`，均必须在 dependency resolve/child spawn前 FAIL；正例证明 parent resolved list与child effective environment一致。

## 保留与授权边界

v0.7 的直接 lexical `--no-python` worker、`-I -S -B -c` verified-bytes loader、out-of-band request SHA、parent Python-install manifest、host-native TCB、copy-only mode staging与全部已有 tests保持不变。仅请求 `APPROVE_TO_IMPLEMENT_P4_INTERPRETER_PROVENANCE`；批准后仅 root loader/bootstrap、P4/P5 tools及标准库 CPU tests。P4 record重冻、P5 export/compose、torchrun/GPU/训练/B2-T仍需独立审核。
