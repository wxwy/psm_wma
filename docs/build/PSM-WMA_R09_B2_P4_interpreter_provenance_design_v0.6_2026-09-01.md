# R09-B2 P4 Interpreter Provenance 静态设计 v0.6

**状态**：draft，待三方审核。v0.6 保留 v0.5 的 `--no-python`、`-I -S -B`、copy-only staging 与 mode-specific freshness，且只关闭 ChatGPT v0.5 review `2026-09-01_R09_B2_P4_interpreter_provenance_design_v05_7072ad4_e834078.md` 的 shell、bootstrap-before-identity、base-Python trust anchor 三项。

## 1. 无 shell 的完整 outer/worker argv

删除 `r09_b2_p4_worker_exec.sh`。P4 outer 和 PyTorch 2.10 `--no-python` worker 都直接执行已绑定 lexical venv Python，且 argv 固定为：

```text
<lexical-python> -I -S -B -c <FROZEN_STDLIB_LOADER> -- <request-json> <mode>
```

agent 的 inner argv 固定为：

```text
torch.distributed.run --standalone --nnodes=1 --nproc-per-node=1 --no-python \
  <lexical-python> -I -S -B -c <FROZEN_STDLIB_LOADER> -- <worker-request-json> p4-worker
```

PyTorch `--no-python` 的 training script 因而恰为 lexical Python，所有后续 tokens都是上述 flags/loader/request；verifier 从 frozen PyTorch 2.10 launch grammar 独立重算四层 argv，拒绝 shell、shebang、`PYTHON_EXEC`、direct python worker、缺失/乱序 `-I -S -B` 或非 lexical worker executable。

## 2. 已验证 bytes 的 loader 与 bootstrap

`FROZEN_STDLIB_LOADER` 是 P4/P5 verifier-owned canonical `-c` string，包含在 record/request 的 `loader_sha256`，不从 root 文件读取。它仅 import 已由 parent 验证的 stdlib `hashlib/json/os/pathlib/sys`，并按以下顺序：

1. 读取 request 的绝对 path，验证 request canonical JSON SHA、mode、root/source/Gitlink/full-clean、output/staging ownership；
2. 以 `open(..., "rb")` **一次**读取 root bootstrap，验证 absolute containment、Git blob/current bytes SHA 与 request SHA；
3. 对已验证 bytes 使用 `compile(bytes, frozen_path, "exec")`/`exec`，不以脚本路径重新打开或直接执行 bootstrap 文件。

bootstrap 因而不是 argv 中首先由 Python file loader 打开的 root-owned代码；bootstrap bytes drift 的 negative 在其任意 side effect 前由 loader 拒绝。P4 agent、worker与P5 child均使用同一 loader，worker仍在 third-party import 前复核 request/staging/rank contract。

## 3. base Python 安装 trust anchor

执行请求显式冻结两层计算基：

1. **parent TCB**：启动 preflight 的 `/opt/conda/bin/python3.11 -I`，其 canonical path、executable SHA、`sys.base_prefix` 和 `sys.version_info` 写入 execution request；它是项目外 host TCB，不由 P4 source tree 自证。
2. **child Python installation**：lexical venv 的 real base executable 及 `<base-prefix>/lib/python3.13`、`lib-dynload` 的 verifier-owned manifest。manifest 是 sorted `(relative_path, file_type=regular, sha256)`，精确覆盖 bootstrap/runtime 可见的 `.py`、extension、data regular files；额外/缺失/非 regular/symlink/importable file均 FAIL。它与 base executable SHA、initial getpath vector、CPython3.13/Linux/x86_64 profile一起写入 P4 record。

在任何 lexical child spawn 前，parent TCB 用 stdlib重新计算 child base manifest、base executable/launcher/cfg/profile/source/payload、request 和 frozen loader digest；任一失败不 spawn child。此处 host parent TCB 是明确的、执行申请层绑定的外部信任假设，而非从 base executable SHA 静默推断。child loader 只在 parent manifest PASS 后使用其 stdlib；worker child仍由 loader/request 在启动时重验可用字段。永久负例：base executable不变但 bootstrap-used stdlib 或 lib-dynload payload变更时，parent拒绝且 child/loader/bootstrap均未启动。

## 4. 保留边界与测试

v0.5 的 P4/P5 copy-only staging、P5 output non-overlap、worker readonly reuse、`-B`+`sys.dont_write_bytecode`、train+cu130 profile、editable/registry/VCS provenance、exact pth roster、untracked-clean、no-pyc source/staging和absent python313.zip contract全部保持。

新增 CPU-only tests：

- mocked PyTorch 2.10 `--no-python` worker executable严格等于 lexical Python，不能是 shell；
- loader request/bytes positive，以及 bootstrap bytes改写时 no side effect 的 FAIL；
- parent base manifest positive，bootstrap-used stdlib与lib-dynload单文件改写的 pre-spawn FAIL；
- actual temporary lexical `-I -S -B -c loader` shape，no pyc与exact staging path PASS。

tests仅临时小树与 stdlib/mock；不运行 torchrun/distributed/compose，不创建或修改实际 Gate venv、source checkout、模型、数据或 GPU。

## 5. 审核请求

本设计仅请求 `APPROVE_TO_IMPLEMENT_P4_INTERPRETER_PROVENANCE` 或 `REQUEST_CHANGES`。批准后仅可实现 root loader/bootstrap、P4/P5 tooling与标准库 CPU tests；P4 record重冻、P5 export/compose、torchrun/GPU/模型数据训练评测推理/B2-T仍全部需独立审核与授权。
