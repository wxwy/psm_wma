# R09-B2 P4 Interpreter Provenance 静态设计 v1.2

**状态**：draft，待三方审核。v1.2 保留 v1.1 的 all-staged-Python、full-ELF-closure 与 fail-closed 语义，仅关闭 ChatGPT addendum `2026-09-01_R09_B2_P4_interpreter_provenance_design_v11_ff183a9_538d414_addendum.md` 指出的 PyTorch 通用 native-load wrapper 定义误拒绝。

## 1. 两层 Python native-load grammar

verifier 仍对 copy-only staging manifest 的全部 approved `*.py`（first-party、registry wheel、VCS）建立 AST；任何 source 缺失、非 regular、不可解析、未列入 manifest 的 `.py` 均 FAIL。每个 native-load 相关节点必须落入下列二选一，不能静默跳过：

1. **直接调用**：沿 v1.1 的 direct FQN/fixed alias 调用 `ctypes.CDLL/PyDLL/cdll.LoadLibrary/pydll.LoadLibrary`、`torch.ops.load_library`、`torch.utils.cpp_extension.load/load_inline`；target 必须是 literal 或 verifier-owned fixed-path rule。
2. **已冻结 wrapper 定义及调用**：仅允许 module-level 函数或 class method 的完整 FQN；无 decorator、closure、`*args/**kwargs`、default/keyword-only 参数、container/return 包装或重新赋值。wrapper body 的 native effect 只能是一次直接 approved API 调用，或一次对另一 admitted wrapper 的 direct FQN/fixed alias 调用；target 只能是该 wrapper 的一个显式位置参数，链式传递时参数位置必须一对一保持。定义 record 为 `{wrapper_fqn, defining_source_relative_path, definition_span_sha256, parameter_index, callee_fqn, effect_kind}`。

wrapper 定义本身不要求 literal target；它不是 runtime load。verifier 从完整 AST universe 独立建立 wrapper summaries，再独立收集对每个 admitted wrapper 的**所有**调用。每次调用都必须是 direct FQN/fixed alias，实参必须 literal 或 verifier-owned fixed-path rule；verifier 沿 admitted wrapper 链展开至底层 API，生成 `{invocation_source_relative_path, invocation_span_sha256, wrapper_chain, final_fqn, target_rule, canonical_target, sha256}`。没有调用的 PyTorch 通用 wrapper 只留下 definition record，不产生 allowlist target。

`torch.classes.load_library(path) -> torch.ops.load_library(path) -> ctypes.CDLL(path)` 可作为两个冻结 wrapper summary + 一个固定调用的链式正例；不以文件名或 PyTorch 专属白名单豁免。

## 2. 逃逸与完备性

wrapper object/FQN 出现在 direct invocation 以外的任何位置均 FAIL：`getattr`、`globals/locals`、`eval/exec/__import__`、star import、reassignment、attribute mutation、container/dict/list/set/tuple、return/yield、decorator、callback/argument forwarding、function pointer、unknown alias 或无法静态解析的 dispatch。wrapper 调用的 nonliteral target、未定义/多定义 wrapper、循环 wrapper graph、无法完整枚举 invocation set 一律 FAIL。

request 的 `wrapper_definitions`、`wrapper_invocations`、direct Python records、ELF records和 `native_runtime_allowlist` 都只是 candidate；verifier 以 frozen manifest/AST/closure独立重算，要求每个排序 JSON 集精确相等。共同漏掉第二个 fixed invocation、registry Python second trigger或transitive ELF second site均 FAIL。

## 3. ELF 与既有合同

v1.1 的 ELF universe仍精确为 `native_seed_union ∪ resolved_native_closure`。仅 dynamic-table `dlopen/dlmopen` family 加 frozen one-to-one literal/fixed `$ORIGIN` target允许；`dlsym`、function pointer、computed string、unmatched import/string与不能解析的 target关系继续 FAIL。v1.0 parent-first final P4 staging，v0.9 all-ELF closure，v0.8 sanitized loader env及更早 lexical launcher、verified-byte loader、request SHA、source/profile contracts均不变。

## 4. 永久 CPU-only regressions

- generic wrapper definition + 一次 fixed invocation：仅 definition summary、invocation record、allowlist全相等时 PASS；
- 同一 wrapper 的 nonliteral invocation、alias/container/callback/reflection escape均 FAIL；
- 两个 fixed invocations而 request/summary/allowlist漏第二个 FAIL；
- PyTorch 风格 `torch.classes.load_library(path) -> torch.ops.load_library(path) -> ctypes.CDLL(path)` 明确 wrapper-chain 正例；
- registry-wheel second trigger、transitive-ELF second loader-site omission、`dlsym`/function-pointer/computed ELF target、旧 v1.1 direct-call negatives继续 FAIL。

本设计仅请求 `APPROVE_TO_IMPLEMENT_P4_INTERPRETER_PROVENANCE`。批准后仍只允许 root P4/P5 tooling 与标准库 CPU tests；禁止 P4 record重冻、P5 export/retry/compose、torchrun、GPU/CUDA、模型/数据/训练/评测/推理、P5 closure与 B2-T。
