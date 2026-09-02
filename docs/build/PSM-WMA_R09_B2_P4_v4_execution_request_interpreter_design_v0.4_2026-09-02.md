# R09-B2 P4-v4 Execution Request `interpreter` 静态合同 v0.4

**状态**：draft；仅整改 implementation=`077e7a7` 的 ChatGPT/MM `REQUEST_CHANGES`，申请 root static parser/validator tooling 与 stdlib CPU fixtures。

继承 v0.3 的 exact `interpreter={lexical_interpreter,host_git,loader_argv,identity_sha256}`、four-field `lexical_interpreter`、host Git single-fd ELF/recursive closure 及拒绝 PATH/which/shell/relative/shebang。v0.3 的 loader runtime 仍在 `FROZEN_STDLIB_LOADER` 内以 bare `git` 执行 bootstrap Git show，形成 parent 与 child 的 split authority；本版只消除此处。

`loader_argv` 由 v0.3 的 11 槽提升为唯一 12 槽 grammar：`[python_path,-I,-S,-B,-c,FROZEN_STDLIB_LOADER,request_abs,request_sha,root_abs,bootstrap_relative,bootstrap_sha,host_git_abs]`。`host_git_abs` 必字节等于 `interpreter.host_git.path`，即已用 same-fd `O_NOFOLLOW`/ELF closure 验证的 absolute strict-resolved non-symlink executable。child loader 将该槽作为唯一 Git executable，精确调用 `[host_git_abs,"-C",root,"show","HEAD:"+relative]`；不得读取 `PATH`、不得 `which`、不得 fallback bare `git`。`verified_loader_argv()`/`is_verified_loader_argv()` 与 `FROZEN_STDLIB_LOADER` 必同步冻结为该 12 槽唯一 grammar；旧 11 槽、direct exporter、`-m`、extra/missing/reordered slot 均永久拒绝。

parent 必先验证 host Git，再以此 executable 验 source Git、bootstrap Git 与 child loader runtime。候选 `host_git` 不得自证：其 ELF/current-byte closure 完成前不得运行任何 Git 子命令。CPU fixture 必覆盖：lexical launcher/realpath/retarget drift，host Git ELF/closure/symlink/relative/PATH shadow，root single-fd raw 无 reopen 与递归依赖无 pathname reopen，12 槽重排/FROZEN loader/root/bootstrap/request SHA/host Git drift、direct exporter/`-m`/extra argv，且每项变异均重算 outer identity 以命中目标分支。

请求 `APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_INTERPRETER_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 `file:line`）。禁止真实 preflight、staging/materialize、record/refreeze、P5 export/compose、torchrun、GPU/CUDA、模型/数据/checkpoint I/O、训练/评测/推理、B2-T 与 Local Memory 训练。
