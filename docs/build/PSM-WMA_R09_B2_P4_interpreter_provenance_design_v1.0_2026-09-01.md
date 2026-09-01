# R09-B2 P4 Interpreter Provenance 静态设计 v1.0

**状态**：draft，待三方审核。v1.0 仅关闭 ChatGPT v0.9 review `2026-09-01_R09_B2_P4_interpreter_provenance_design_v09_8275d76_af8bccd.md` 的 P4 staging order 与 dynamic native-load completeness；保留所有既有启动、环境、source、native closure合同。

## 1. parent-first P4 staging

未来独立批准的 P4 execution 中，parent TCB 在 spawn outer agent **之前**、在原本不存在的 D005 run root 下创建唯一 `import_staging/<run-token>`，copy-only物化、重算 exact manifest、标为 readonly。parent以该最终 canonical staging layout计算 v0.9 的所有 ELF seed `RPATH/RUNPATH/$ORIGIN` closure，验证通过后才 spawn agent；agent/worker均只读取同一 staging，不能创建/改名/覆盖。

因此 D005 freshness 定义为“parent preflight前 run_root absent”；只有获批的 execution parent 可创建该 run root。P5 保持独立 `attempt_dir/import_staging/<backend>`，production/D005 run_root在 P5 child 前后均必须 absent。永久负例：同 ELF bytes移至另一个 staging target导致 `$ORIGIN`选中不同 `.so` 时，parent pre-spawn FAIL。

## 2. verifier-owned dynamic native-load grammar

`native_runtime_allowlist` 不再由 request 声明 completeness。expected entries 从 frozen source/config/ELF 的 verifier-owned `native_load_contract` 导出，request entries只能逐项等于 expected：

1. **Python sites**：verifier从 Gitlink tracked source blob 与 staging first-party/VCS source manifest 枚举 `ctypes.CDLL/PyDLL`, `torch.ops.load_library`, `torch.utils.cpp_extension.load`, `dlopen` wrapper等批准 API。每个 site必须有 frozen blob path、source-span SHA、approved component、literal soname或固定 path-construction rule、loading mechanism；未枚举 site、非 literal/无法决定的 path构造、environment-derived path均 FAIL。
2. **ELF sites**：verifier对每个 v0.9 ELF seed检查 undefined `dlopen/dlmopen` family symbols及对应 frozen byte-level callsite/string records。每个允许 site都需 component ELF SHA、symbol/callsite record、literal soname或 deterministic `$ORIGIN` rule、canonical target/SHA；额外 loader symbol/callsite/string candidate、indirect/non-deterministic construction或无法建立 one-to-one target都 FAIL。
3. **closure relation**：允许的 target若可通过 `DT_NEEDED`解析，必须已在 v0.9 closure；其余只可进入上述 exact allowlist。运行时请求/allowlist共同删去任一 frozen second trigger仍 FAIL，因为 verifier独立重新枚举 source/ELF sites并比较完整集合。

当前 profile 若含任何不可用这套静态 grammar完整证明的 plugin/driver/dlopen component，则 P4 Gate FAIL closed；不得以“系统已安装”或运行时观察补齐。该限制是设计期的明确可执行边界，不引入 runtime sandbox。

永久 CPU/static tests：两条 source/ELF native-load trigger中请求与allowlist共同遗漏第二条仍 FAIL；非字面/间接 dlopen FAIL；冻结 loader-site+target 正例 PASS；v0.9 disjoint ELF union与依赖漂移 negatives保留。

## 3. 边界

本设计仅请求 `APPROVE_TO_IMPLEMENT_P4_INTERPRETER_PROVENANCE`。批准后仅 root loader/bootstrap、P4/P5 verifier/exporter与CPU tests；不得 P4 record重冻、P5 export/compose、torchrun/GPU、模型数据训练评测推理/B2-T。旧 attempt永不重跑。
