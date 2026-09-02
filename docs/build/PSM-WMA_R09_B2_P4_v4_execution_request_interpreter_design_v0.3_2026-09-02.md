# R09-B2 P4-v4 Execution Request `interpreter` 静态合同 v0.3

**状态**：draft；合并 GPT=`a20a42a` 与 Kimi/MM 对 v0.2 的结论，仅申请 root static parser/validator tooling 与 stdlib CPU fixtures。前置 source closure=`b0581d8`/`a9c2eb3`，全部复用 provenance v1.3 的既有 identity 与 loader grammar。

`interpreter` 精确键为 `lexical_interpreter,host_git,loader_argv,identity_sha256`。`lexical_interpreter` 必逐键等于 `lexical_interpreter(Path(path))` 的冻结四字段 `{path,sha256,realpath,realpath_sha256}`；不得要求 lexical launcher 非 symlink、不得替换、删减或重命名任何字段。永久覆盖 launcher bytes drift、resolved target drift 与 lexical path 重定向到不同 realpath。

`host_git` 精确键为 `{path,elf_sha256,closure_sha256}`：`path` 为绝对 strict-resolved non-symlink regular executable，单 fd `O_NOFOLLOW`+same-fd `fstat`+single raw 绑定 ELF SHA；ELF interpreter、DT_NEEDED、RPATH/RUNPATH 与递归 canonical object SHA 集由 bytes 重算 closure SHA。不得 `PATH`/`which`/shell lookup/relative path/shebang，且 source Git authority 的 bootstrap 计算不得使用 candidate `host_git` 自证。

`loader_argv` 必为完整 11 槽 list，且字节级等于既有 `verified_loader_argv(lexical_interpreter, request_path, request_sha256, root, bootstrap_relative, bootstrap_sha256)`：`[python_path,-I,-S,-B,-c,FROZEN_STDLIB_LOADER,request_abs,request_sha,root_abs,bootstrap_relative,bootstrap_sha]`。validator 必先 `is_verified_loader_argv()`，再独立重建并逐元素相等；不得定义第二种缩写 grammar。

venv 未追踪 payload/base/cfg/lock-RECORD 链继续按 provenance v1.3 在 `lexical_interpreter` authority 外由 source/install binding 验证；不得伪造 Git blob。CPU fixtures 必覆盖四字段 drift/repoint、Git ELF/closure/symlink/PATH shadow、自证 git、11 槽 argv 缺失/重排/FROZEN loader/root/bootstrap/request SHA drift、direct exporter/`-m`/extra argv、无 pathname reopen。

请求 `APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_INTERPRETER_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 `file:line`）。禁止真实 preflight、staging/materialize、record/refreeze、P5 export/compose、torchrun、GPU、模型/数据/checkpoint I/O、训练/评测/推理、B2-T 或 Local Memory 训练。
