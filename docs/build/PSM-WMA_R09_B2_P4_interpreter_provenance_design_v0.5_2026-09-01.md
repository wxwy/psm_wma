# R09-B2 P4 Interpreter Provenance 静态设计 v0.5

**状态**：draft，待三方审核。v0.5 继承 v0.3/v0.4 的 profile、source、staging 与 getpath 合同，并关闭 ChatGPT v0.4 review `2026-09-01_R09_B2_P4_interpreter_provenance_design_v04_befc5ed_55d9526.md` 的 worker、bytecode、P5 freshness、hard-link 问题。本文件不授权任何实现或运行。

## 1. 完整 P4 进程树的 bootstrap contract

P4 outer agent 仍以 lexical interpreter `-I -S -B <root>/tools/g0/r09_b2_p4_bootstrap.py --mode=p4-agent` 启动，但冻结的 inner launcher 改为 PyTorch `torch.distributed.run --no-python`，training script 必须逐字为 root-owned executable wrapper：

```text
torch.distributed.run --standalone --nnodes=1 --nproc-per-node=1 --no-python \
  <frozen-root>/tools/g0/r09_b2_p4_worker_exec.sh \
  --worker-module=cosmos_framework.scripts.train --sft-toml=<relative-toml> <ordered-overrides>
```

`r09_b2_p4_worker_exec.sh` 只做 argv grammar/rank-environment handoff，并 `exec` lexical interpreter `-I -S -B <bootstrap> --mode=p4-worker -- ...`；它不使用 shebang Python、`PYTHON_EXEC` 或 normal Python startup。worker bootstrap 在任何 torch/project/third-party import 前复验同一 record 的 lexical/base/profile/source/payload/staging contract、以及 torchrun 注入的 rank/world variables；随后以 `runpy.run_module("cosmos_framework.scripts.train", run_name="__main__")` 运行冻结 module/argv。

P4 record 必须保存并由 verifier 独立重算四层 argv：outer bootstrap、torchrun agent、`--no-python` worker wrapper、worker bootstrap/training module。任何 direct `python -u [-m] cosmos_framework...`、`PYTHON_EXEC`、缺 `--no-python`、wrapper/source SHA/mode/argv/rank environment 不符均 FAIL。标准库 CPU test 以 mocked PyTorch 2.10 `config_from_args`/agent launch capture 证明 worker 只能得到 wrapper，且 wrapper 最终 argv 恰为 `lexical -I -S -B bootstrap --mode=p4-worker`；不 import torch 或启动 distributed。

P5 是单 child：`lexical -I -S -B bootstrap --mode=p5-compose`，没有 torchrun worker。P4 agent/worker、P5 都在 bootstrap 第一条 third-party import 前断言 `sys.flags.dont_write_bytecode` 与 `sys.dont_write_bytecode` 均为 true；`-B` 是 argv 固定部分，不依赖被 `-I/-E` 忽略的 `PYTHON*` 环境变量。

## 2. mode-specific fresh staging 与 output 边界

staging 使用**copy-only**物化（`shutil.copyfile` + explicit mode，不允许 hard-link、reflink、symlink），以 source truth manifest 的 regular importable payload 构造 no-pyc tree。staging 后重新 hash；修改源文件后 staging bytes/manifest 必须不变。`-B` 与 `sys.dont_write_bytecode=True` 禁止第三方 import 向 staging 产生 bytecode，且 bootstrap 在 import 前后均扫描、任一 `__pycache__`/`.pyc` 都 FAIL。

每种 mode 的 root 由 parent/verifier 而非 child 推导并写入 request：

| mode | staging root | freshness |
| --- | --- | --- |
| `p4-agent`/`p4-worker` | 仅在未来已独立批准的 P4 execution 中，`<D005 run_root>/import_staging/<run-token>` | 创建前 D005 `run_root` 必不存在；agent 创建一次，worker 只消费同一 readonly staging。 |
| `p5-compose` | `<P5 attempt_dir>/import_staging/<backend>` | attempt_dir 是 P5 parent 创建的临时目录；必须在 production root、D005 run_root、evidence root、exporter root 之外。P5 绝不得创建、进入或成为 `outputs.run_root` 的祖先/后代；canonical P5 output 仍只在 verifier PASS 后 rename。 |

P5 parent 在启动 children 前验证 production `outputs.run_root` 不存在，并在 child 结束后再次验证它仍不存在；任何 P5 staging path overlap、预存、symlink escape 或 run_root mutation均 FAIL。P4 worker request 只接受 agent 生成、manifest 已验证且 readonly 的 staging root；禁止 worker 二次创建/覆盖。

## 3. 保留的 source/path trust boundary

v0.3 的 `train` extra+`cu130` group、editable/registry/VCS source grammar、Git tracked+untracked full-clean、exact `.pth` roster（但 staging 不复制）、base absent `python313.zip` candidate 与 exact runtime path全部不变。所有 runtime imports 仅来自 copy-only staging plus base stdlib/dynload；source/venv/VCS checkout/cwd/script/zip/external site-packages均不在 runtime `sys.path`。

## 4. 永久 CPU-only 验收

除已有负例外，必须增加：

1. mock PyTorch 2.10 worker command：`--no-python` wrapper PASS；任何 direct Python worker、`PYTHON_EXEC`、少 `-I/-S/-B`、错误 mode/rank argv FAIL；
2. 执行实际临时 `-I -S -B` bootstrap 形状，import staged source module，断言 `sys.dont_write_bytecode` 和没有任何 pyc；
3. P5 attempt staging 正例不创建/触碰 D005 `outputs.run_root`；任何 overlap/escape/mutation FAIL；
4. staging 后篡改 source，staging payload/manifest仍逐位不变；hard-link inode equality 是 FAIL；
5. agent creates once/worker readonly reuse，worker create/overwrite 是 FAIL。

tests仅临时小树、stdlib/mock，不运行 torchrun/distributed/compose，也不触碰实际 Gate venv、模型、数据或 GPU。

## 5. 审核请求与边界

本设计仅请求 `APPROVE_TO_IMPLEMENT_P4_INTERPRETER_PROVENANCE` 或 `REQUEST_CHANGES`。若批准，只允许 root bootstrap/wrapper、P4/P5 verifier/exporter与标准库 CPU tests；P4 record 重冻、P5 export/compose、torchrun、GPU、模型/数据/训练/评测/推理/B2-T仍须独立审核与授权。旧 records/attempts 永不重跑。
