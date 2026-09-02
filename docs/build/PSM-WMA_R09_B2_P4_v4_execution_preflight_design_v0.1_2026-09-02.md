# R09-B2 P4-v4 Execution-Preflight 设计 v0.1

**状态**：draft。本 Gate 只实现 root-side preflight tooling 与 CPU 标准库测试；不授权 preflight 实际运行。

## 前置与边界

唯一前置为 P4 interpreter-provenance v1.3 与 P5 v0.9 static tooling 已关闭。历史 P4-v2 D005、已有 P5 envelope 或 caller 提供的 closure 均不可替代本 Gate。

禁止：真实 staging、record/refreeze、P5 export/compose、`load_experiment_from_toml`、torchrun、GPU、模型/数据/checkpoint I/O、训练/评测/推理、B2-T。

## 静态 request/record 合同

每 backend 固定未来产物路径为 `artifacts/g0/r09/b2/p4_execution_preflight_v4/<backend>/{request,result,verification}.json`。tooling 必须生成/核验 canonical JSON、三份 SHA 链、production Git/current-byte identity、final run-root/staging identity、readonly roster/payload manifest、lexical `-I -S -B -c` loader、bootstrap Git/current-byte、empty effective/native environment、runtime sys.path、Python native-load 与 ELF closure 记录。

真实执行获得独立批准后，parent 才可一次性在最终 canonical `<run_root>/import_staging/<token>` copy-only materialize；tooling 必须在该最终路径重算 manifest、Python universe、ELF closure 和 roster。任何 symlink、路径替换、未列文件、可写 staging、SHA/loader/environment drift 均 FAIL；agent/worker/P5 只读该 record。

## 实现与测试

仅新增/扩展 root `tools/g0/` preflight builder/verifier，复用 `r09_b2_interpreter_provenance.py` 和 P5 v4 verifier grammar。CPU tests 使用临时目录和 stdlib mock，覆盖 request/result/verification schema、final-path substitution、roster/manifest drift、hidden Python、ELF second-site、loader/bootstrap drift、environment/sys.path drift；不得创建真实 staging 或调用 compose。

## 后续门

静态实现经三方 `APPROVE_TO_IMPLEMENT_P4_V4_PREFLIGHT_STATIC_TOOLS` 后才能编码；实现 closure 经三方批准后，才可单独申请一次真实 preflight 执行。P5 export、B2-T 与 Local Memory 训练仍分别需要后续独立 Gate。
