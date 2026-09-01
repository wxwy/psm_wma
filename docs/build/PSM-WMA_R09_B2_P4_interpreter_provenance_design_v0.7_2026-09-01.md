# R09-B2 P4 Interpreter Provenance 静态设计 v0.7

**状态**：draft，待三方审核。v0.7 仅在 v0.6 已批准方向上关闭 ChatGPT review `2026-09-01_R09_B2_P4_interpreter_provenance_design_v06_4ca7f12_fa97814.md` 的 request TOCTOU 与 native-runtime TCB 边界；不改变 `--no-python` direct lexical worker、`-I -S -B -c` loader、source/profile/staging 或训练语义。

## 1. argv 外部锚定 request digest

每个 parent 在 spawn 前以 canonical JSON bytes 写入 request，立即重读并计算 `expected_request_sha256`。该 digest 不是 request 内字段，必须作为 child argv 的独立 token：

```text
<lexical-python> -I -S -B -c <FROZEN_STDLIB_LOADER> -- \
  <absolute-request-path> <expected-request-sha256> <mode>
```

P4 agent/worker/P5 child 三种 request 都适用；P4 agent 将 worker request 的 absolute path + expected digest 原样写进 `torch.distributed.run --no-python <lexical-python> ...` 的 frozen cmd_args。P4/P5 verifier 从 verifier-owned request construction重新 canonicalize/derive该 digest，并逐 token 比较 argv；request self-declared digest 不参与信任。

loader 仅一次读取 request bytes，先计算 SHA256 并与 argv token 精确匹配，再 JSON parse/validate任何 request field，再读取/verify/compile/exec bootstrap bytes。same-path request replacement、request SHA token 改写、worker request/path/digest 与 agent 派生不等均必须在 bootstrap side effect 前 FAIL。

## 2. 显式 host-native TCB

P4 不把 ELF loader、kernel、系统 libc/driver 或 child Python executable 依赖的系统 native libraries 伪称为 Gitlink/Python-payload evidence。它们是 execution-request 层的 **host-native TCB**，必须显式记录：

```text
host_native_tcb = {
  parent_interpreter: {path, sha256},
  child_elf: {path, sha256},
  dynamic_loader: {path, sha256},
  resolved_native_dependencies: [{soname, canonical_path, sha256}],
  platform: {sys_platform: linux, machine: x86_64}
}
```

parent TCB 在 child spawn 前，以 stdlib/受控 `ldd`-equivalent解析 child executable 与 manifest 中实际 bootstrap-used base-prefix extension 的 ELF dependencies，要求无 relative/search-path ambiguity、无缺失/重复/非 canonical dependency，并逐项比 execution request frozen list。任何 base-prefix native dependency 或解析后的 system dependency path/SHA 变化均 pre-spawn FAIL；系统 native 层的正确性因此是明确、身份绑定的 host execution assumption，而不是由项目代码/venv静默承担。

P4 record 继续独立绑定 base executable、stdlib/lib-dynload payload manifest；host-native TCB 则是启动该 record/child 的 execution request provenance。永久 CPU-only negative包含“base executable不变但 request 替换”“base-prefix extension 依赖 SHA/路径改变”两种；后者必须在 child/loader/bootstrap 启动前拒绝。

## 3. 保留与授权边界

v0.6 全部合同不变。测试仅临时树、stdlib/mock，不执行 torchrun/compose/GPU/模型数据。仅请求 `APPROVE_TO_IMPLEMENT_P4_INTERPRETER_PROVENANCE`；若批准只可实现 root loader/bootstrap、P4/P5 tools与CPU tests。P4 record重冻、P5 export/compose、torchrun/GPU/训练/B2-T仍需独立审核。
