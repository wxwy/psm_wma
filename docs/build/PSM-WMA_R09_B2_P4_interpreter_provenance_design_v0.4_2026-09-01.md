# R09-B2 P4 Interpreter Provenance 静态设计 v0.4

**状态**：draft，待三方审核。v0.4 继承 v0.3 的 exact install profile/source-type/getpath contract，并关闭 ChatGPT v0.3 review `2026-09-01_R09_B2_P4_interpreter_provenance_design_v03_5e513e7_a5f546f.md` 的 P4 normal-startup、bytecode 与 untracked-import-root 问题。本文件不授权实现、P4 record 重冻、P5 export/compose、GPU、训练、评测或推理。

## 1. P4 与 P5 共用的无 site 启动模型

新版 P4 D005 不再直接以 normal-site Python `-m torch.distributed.run` 启动。它的冻结 argv 改为 lexical venv launcher：

```text
<lexical-venv-python> -I -S <frozen-root>/tools/g0/r09_b2_p4_bootstrap.py --mode=p4-train -- <frozen torch.distributed.run argv>
```

P5 同样以 `-I -S` 调用该 root-owned、tracked bootstrap 的 `--mode=p5-compose`。bootstrap 在任何 third-party/project import 前只用 stdlib 完成 v0.3 的 lexical/base/cfg/profile/source/payload/getpath 审计，构造受控 import staging root 与 exact runtime path；只有随后才以 `runpy.run_module("torch.distributed.run", run_name="__main__")` 执行原 D005 launcher module。P4 的 `training_argv` 必须仍逐字保存原本的 `torch.distributed.run` 参数、`cosmos_framework.scripts.train`、TOML 和 ordered overrides；bootstrap 不是另一个训练入口、不得重排/增删训练参数。

因此 P4 与 P5 都不执行 normal `site`：`.pth`、`sitecustomize`、`usercustomize` 在两种模式均无 guard 前执行时机。D005 schema 升级并拒绝旧 direct-`-m` v2 record；P4/P5 verifier 逐字验证 wrapper argv、bootstrap source Git blob/current bytes SHA、mode、training_argv 与所有 v0.3 provenance。

## 2. 无 bytecode 的受控 staging import root

bootstrap 不把 production framework、VCS checkout 或原 venv site-packages 直接插入运行时 `sys.path`。在静态验证后，它在 D005 派生且新鲜的 run-local staging directory 中，以 stdlib hard-link（不可 link 时 copy）物化以下已验证 payload：

1. frozen Gitlink 的 `cosmos_framework` tracked import tree；
2. v0.3 registry-wheel expected payload；
3. v0.3 Git/VCS expected import trees。

物化规则是 verifier-owned：只允许已在 source truth manifest 中的 relative regular files和必要目录；拒绝 symlink、device/FIFO、`__pycache__/`、任意 `*.pyc`、`.pth`、`sitecustomize.py`、`usercustomize.py`。生成完成后重算 staging manifest，必须逐项等于已验证 source payload manifest；staging 必须新建、位于 D005 run root、无预存内容且不在任何 source/venv/cache root 内。设置 `PYTHONDONTWRITEBYTECODE=1`；bootstrap 也拒绝 staging 在运行前出现 pycache/pyc。

runtime `sys.path` 因而精确为：base stdlib、base lib-dynload、staging first-party source、staging site-packages。它不包含原 production framework、任一 VCS checkout、原 venv site-packages、cwd、script directory、zip 或外部路径。base `python313.zip` 的唯一 absent getpath candidate 继续在 bootstrap 早期被 exact-match 后删除，不进入 runtime path。

这使 Python 无可读的本地 cached bytecode；受控 `.py` payload 只能由 source/wheel/VCS truth 加载。任何 sourceless pyc、缓存 pyc、或未声明的 import root 都无法参与 P4/P5 import。静态 P5 compose 不写字节码；未来 P4 train 若库尝试写 bytecode，`PYTHONDONTWRITEBYTECODE=1` 使其不落入 staging/source root。

## 3. `.pth` 与 source clean 语义

原 venv `.pth` roster 仍作为安装 provenance 记录并严格绑定 raw SHA：`_editable_impl_cosmos_framework.pth`、`_virtualenv.pth`、`a1_coverage.pth`、`distutils-precedence.pth`，因为 `-I -S` 从不处理它们。它们的 import target 不成为任何 P4/P5 runtime import root；staging 中也不复制 `.pth`。新增、缺失或字节变化 FAIL。永久 test 对含 import 的允许 pth 维持 sentinel，证明在 bootstrap 前和运行 path 构造后均未执行。

“clean source”精确定义为 production root、`cosmos-framework` submodule 及每个 VCS external checkout 均满足 `git status --porcelain=v1 --untracked-files=all` 空输出，HEAD/locked commit、Gitlink、tracked tree digest 与 current bytes 全部相等。每个 source tree 在 staging 前后都按 manifest 枚举；任何 untracked `.py`、package directory、extension、namespace fragment、symlink 或 pyc 都导致 FAIL。registry wheel/venv site-packages 也以 exact manifest，而非宽松目录包含关系，拒绝额外 importable payload。

## 4. 新的永久 CPU-only 回归

除 v0.3 tests 外，必须新增：

| 场景 | 预期 |
| --- | --- |
| P4 D005 direct normal `-m torch.distributed.run`，或 bootstrap/mode/training argv 任一变化 | FAIL |
| executable `.pth` 内容不变但其 import target payload 改变 | P4/P5 均不执行 target；staging/provenance FAIL |
| source/site-packages 内 tampered valid `__pycache__/*.pyc` 或 added sourceless pyc | FAIL |
| staging 中 pyc/pycache/pth/customize、symlink、额外/缺失/改写 payload | FAIL |
| production/VCS root 存在 untracked import shadow | FAIL |
| staging manifest 正例与 `PYTHONDONTWRITEBYTECODE=1` | PASS，且 no pyc write |

测试只构造临时小树并 mock/run stdlib bootstrap path；不 import Hydra/Pydantic/Cosmos，不 compose，不新建/修改实际 Gate venv，不运行 torchrun/GPU/模型/数据。

## 5. 实施与后续 Gate

若三方批准，只允许新增 root bootstrap 工具并修改 P4/P5 verifier、exporter及其标准库 CPU tests；不触碰子模块。static implementation review 后，P4 新 record 重冻、P5 export 和训练都仍须独立三方审核与明确执行授权。旧 P4 v2 与两个 P5 attempts 永不重跑。

本设计仅请求 `APPROVE_TO_IMPLEMENT_P4_INTERPRETER_PROVENANCE` 或 `REQUEST_CHANGES`；不授权其它操作。
