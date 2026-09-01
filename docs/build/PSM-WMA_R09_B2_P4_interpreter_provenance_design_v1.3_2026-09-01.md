# R09-B2 P4 Interpreter Provenance 静态设计 v1.3

**状态**：draft，待三方审核。v1.3 替换被 GPT implementation review 否决的 v1.2 implementation wiring；保留 lexical launcher、wrapper definition/invocation 语义及 fail-closed 原则，逐项关闭 review `2026-09-01_R09_B2_P4_interpreter_provenance_implementation_v12_dd50469_2c0290f.md` 的六个 HIGH 和 source-clean MEDIUM。

## 1. 两阶段对象与禁止边界

静态 D005 不再包含已存在的 `staging_root`、path-dependent closure 或 runtime allowlist。它只冻结 source/install/payload manifest、staging grammar、outer/worker/P5 template、root bootstrap bytes SHA和所需 request schema。`outputs.run_root` 在 static 阶段必须不存在。

仅未来获独立执行授权的 parent preflight 才能在 final `<run_root>/import_staging/<run-token>` copy-only materialize，重算 manifest，再从该**最终 canonical path**解析 `$ORIGIN/RPATH/RUNPATH` closure。preflight 产生 execution request；agent/worker只能读取，任何 drift/重命名/写入均 FAIL。P5 始终仅在独立 attempt staging 下运行，D005 run root 前后必须 absent。

## 2. 受验证 process tree

parent 在 child spawn 前以 stdlib 验证 request/bootstrap SHA、full-clean source/install/closure/staging。outer agent argv 与 worker argv 都是 lexical venv launcher：

```text
<venv>/bin/python -I -S -B -c <FROZEN_STDLIB_LOADER> <request-abs> <expected-request-sha>
```

loader 读取 request bytes 一次，先比对 out-of-band SHA，再验证 root bootstrap Git blob/current bytes SHA，`compile/exec` 已验证 bytes；无 root Python 文件可在此前由解释器直接打开。outer 使用 PyTorch `torch.distributed.run --no-python <lexical-python> -I -S -B -c <loader> <worker-request> <sha>`；worker request 额外绑定 mode、rank key allowlist 与 agent-derived digest。direct `python -m cosmos_framework...`、direct exporter script、无 `-I/-S/-B`、无 `--no-python`、无 SHA token 全部永久 FAIL。

P5 child 同一 loader/request grammar，绝不以 `[python, exporter.py]` 直接执行。

## 3. Python native-load complete analysis

execution preflight 从 final staging manifest 自己枚举全部 regular `*.py`，并要求与 frozen payload manifest精确相等；caller `python_payloads` 不能缩小 universe。所有 source AST 均进入 direct/wrapper analysis；额外 `hidden.py` 即使 candidate/allowlist共同遗漏也 FAIL。

wrapper admission支持 module function 和 class method（FQN含 class）。每个定义只有一个显式路径参数、无 decorators/escape/variadic/default/closure；body只能 direct approved native API 或 direct admitted wrapper。所有 AST context（含 function bodies）都扫描 invocation/escape：alias/reassignment/container/callback/return/decorator/reflection/unknown dispatch/nonliteral target均 FAIL。verifier完整展开 `_Classes.load_library -> torch.ops.load_library -> ctypes.CDLL`，冻结 definition、invocation、chain及最终 literal/fixed target记录；candidate sets只可与 independently recomputed sets完全相等。

## 4. ELF bytes-derived closure

preflight 从 final staging/base payload的真实 ELF bytes 自行解析 `PT_INTERP`、`DT_NEEDED`、`RPATH/RUNPATH`、dynamic loader imports和callsite/string record，递归得到 `seed ∪ closure` canonical object/SHA集合。closure metadata、undefined symbols、loader targets与SHA不是 caller fields；target必须真实存在、canonical且哈希重算一致。`dlsym`、function pointer、computed target、unpaired loader site一律 FAIL。shared-forgery（双方删去实际 Python/ELF second site）永久 FAIL。

## 5. Full-clean 与永久回归

production root、submodule和每个 VCS source 均要求 `git status --porcelain=v1 --untracked-files=all` 空；untracked shadow 永久 FAIL。CPU-only mocks必须覆盖：旧 direct launch/P5 script拒绝、request SHA/bootstrap drift、final-path `$ORIGIN` drift、hidden Python shared forgery、class-method PyTorch chain、wrapper alias/container/callback/return/reflection、真实 ELF parser shared forgery、untracked shadow以及既有环境/closure negatives。

本设计只请求 `APPROVE_TO_IMPLEMENT_P4_INTERPRETER_PROVENANCE`；仍禁止真实 staging/venv/external checkout、P4 record重冻、P5 export/compose、torchrun、GPU、模型/数据/训练/评测/推理/B2-T。
