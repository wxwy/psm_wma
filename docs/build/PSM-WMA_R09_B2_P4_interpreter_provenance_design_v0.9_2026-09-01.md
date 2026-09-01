# R09-B2 P4 Interpreter Provenance 静态设计 v0.9

**状态**：draft，待三方审核。v0.9 仅扩展 v0.8 host-native TCB 的 closure seed set，以关闭 ChatGPT v0.8 review `2026-09-01_R09_B2_P4_interpreter_provenance_design_v08_1761668_d8934dc.md` 的唯一 HIGH；不改变环境、loader、worker、staging或训练语义。

## 完整 runtime native closure

在 v0.8 的 empty native-loader environment 中，verifier-owned seed set 不再仅是 child Python。它是所有 approved runtime manifest 中 ELF regular file 的排序并集：

1. lexical/base interpreter ELF；
2. base `lib-dynload` 的所有 ELF extension；
3. copy-only staging 中 registry wheel、editable first-party、VCS source 的所有 ELF extension、package-owned `.so` 与任何 approved native executable；
4. bootstrap/runtime 显式调用的每个 native executable。

对每个 seed，parent TCB 解析 `PT_INTERP`、`DT_NEEDED`、`RPATH/RUNPATH/$ORIGIN`，在完全相同的 v0.8 sanitized environment 中得到 canonical dependency graph；所有 graph 取 deterministic sorted union，写入 execution request `host_native_tcb.resolved_native_closure=[{seed_relative_path, soname, canonical_path, sha256}]`。缺失、ambiguous search、relative/unresolved origin、非 canonical/重复 object、ELF 类型不符或任一 digest变更均 pre-spawn FAIL。

不在静态 `DT_NEEDED` graph 的 runtime `dlopen`/driver/plugin 一律不隐式允许。它们必须列为 verifier-owned `native_runtime_allowlist`：每项有 triggering approved component、absolute canonical path、SHA256、用途和加载机制；parent在 spawn 前绑定其身份，runtime path 只能载入该 allowlist。未列出或无法以 deterministic source/provenance证明的 native load使 Gate fail-closed，需另版设计/审核。CUDA/driver/plugin 不因“系统已安装”自动进入 allowlist。

永久 CPU/static tests：

- child/base与staged extension不变、仅该 extension依赖的外部 `.so` path/SHA 改变 → pre-spawn FAIL；
- 两个 staged ELF 各有不相交 dependency，verifier必须输出/验证两者 union；
- unlisted runtime dlopen/plugin → FAIL，精确 allowlist path/SHA正例才 PASS；
- v0.8 `LD_*` 注入 negatives继续 PASS为拒绝。

## 保留与授权边界

v0.8 all-absent loader environment、direct lexical worker、external request SHA、verified-bytes loader、base payload manifest、copy-only mode staging、P5 output isolation及所有 source contracts保持不变。本设计只请求 `APPROVE_TO_IMPLEMENT_P4_INTERPRETER_PROVENANCE`；批准后仅 root tooling/CPU tests，P4 record重冻/P5 export/compose/torchrun/GPU/训练/B2-T仍独立审核。
