# R09-B2 P4 Interpreter Provenance 静态设计 v1.1

**状态**：draft，待三方审核。v1.1 仅修订 v1.0 native-load enumeration universe/detector grammar；parent-first staging、all-ELF closure、loader及其它合同不变。

## 1. 完整枚举宇宙

verifier-owned Python native-load analysis的输入是 copy-only staging manifest 内**所有** approved `*.py` regular payload：first-party editable、registry wheel、VCS 三类均不得遗漏。每个 `.py` 解析为 AST；任何未解析、编码异常、source缺失或被排除的 executable Python payload均 FAIL。registry-wheel PyTorch/分布式/CUDA helper与项目源码使用同一 site grammar；shared-forgery negative 必须在 registry-wheel Python file加入第二个 trigger并同时从request/allowlist删去，验证仍 FAIL。

ELF native-load analysis的输入是 `native_seed_union ∪ resolved_native_closure` 的完整去重 canonical object 集，而不是只扫初始 seed。closure object 的额外 dlopen site也必须生成/匹配 expected allowlist；negative为 seed无loader symbol、transitive object有遗漏第二 site时 FAIL。

## 2. 精确 fail-closed detector grammar

Python AST detector只认可以下直接、可静态解析的 call forms，并要求 path/soname为 string literal 或 verifier-owned immutable fixed-path rule：

| API symbol | 允许形式 |
| --- | --- |
| `ctypes.CDLL`, `ctypes.PyDLL`, `ctypes.cdll.LoadLibrary`, `ctypes.pydll.LoadLibrary` | direct qualified name或单层 `from ctypes import` alias，literal/fixed path |
| `torch.ops.load_library` | direct fully-qualified name或由固定 import alias静态解到该 FQN，literal/fixed path |
| `torch.utils.cpp_extension.load`, `load_inline` | direct FQN/fixed alias，所有 source/path 参数必须为 verifier-owned fixed values |

AST 中对上述 modules/symbols 的 `getattr`、`globals`、`locals`、`eval`、`exec`、`__import__`、reassignment、star import、container/closure/function-pointer转发、非 literal path、unknown wrapper或不能静态解析的 alias均 FAIL。其它可能加载 native code的 API 在其规则未纳入本表前同样 FAIL，不以“etc.”或运行时观察跳过。每一 approved call生成 frozen `{source_relative_path, source_span_sha256, resolved_fqn, mechanism, target_rule, canonical_target, sha256}`；request allowlist必须等于 verifier重算的全体记录。

ELF detector只认可 ELF dynamic table中的 `dlopen/dlmopen` family imports与 frozen callsite/string records的 one-to-one literal/fixed `$ORIGIN` target。`dlsym`、function pointer、computed string、unmatched loader import/string或不能建立 target关系均 FAIL。所有 static graph target仍须在 closure/allowlist且具path/SHA。

## 3. 边界

当前 profile 如含任何无法满足这份 grammar的 staged Python/ELF component，P4 Gate显式 FAIL closed，不重写allowlist、不从运行时捕获补齐。本设计仅请求 `APPROVE_TO_IMPLEMENT_P4_INTERPRETER_PROVENANCE`；批准后仅 root tools/CPU tests，P4 record重冻及一切执行仍独立审核。
