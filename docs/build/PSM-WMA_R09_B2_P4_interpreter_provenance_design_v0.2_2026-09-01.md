# R09-B2 P4 Interpreter Provenance 静态设计 v0.2

**状态**：draft，待三方审核。v0.2 替换 v0.1 的 distribution provenance 与 child startup 方案，以关闭 ChatGPT review `2026-09-01_R09_B2_P4_interpreter_provenance_design_55392c1_dc5a799.md` 的两个 HIGH 和一个 MEDIUM。本文件不执行 P4 record 重冻、P5 export/compose、torchrun、GPU、模型/数据/权重读取、训练、评测或推理。

## 1. 保留的根因与 launcher 身份

P5 r2 attempt 在 compose 前用 uv base Python 导入 `pydantic` 失败，因 P4 将 `<root>/cosmos-framework/.venv/bin/python` `resolve()` 后写入 D005/P5 argv。v0.2 保留 v0.1 已定义的 lexical launcher、raw symlink payload/文件类型、base realpath/base SHA256、`pyvenv.cfg` 与两 backend pair-equality 约束：`command.argv[0]` 必须逐字为 lexical launcher，绝不以 realpath 启动；旧 P4 v2 record 与两个已消费 P5 attempt 均保留且不得重跑。

## 2. 独立的环境与 payload 真源

P4 新 schema 新增 `environment_provenance`，它不是从当前 venv 自证，而是由 verifier 从 frozen Cosmos Gitlink 的 tracked blob 独立导出：

```json
{
  "resolution": {"python_full_version": "3.13.*", "sys_platform": "linux", "platform_machine": "x86_64", "dependency_groups": ["cu130"]},
  "tracked_sources": {"pyproject_toml_sha256": "...", "uv_lock_sha256": "..."},
  "locked_wheels": [{"normalized_name": "pydantic", "version": "2.12.5", "wheel_filename": "...", "wheel_sha256": "..."}],
  "installed_payload": [{"normalized_name": "pydantic", "version": "2.12.5", "wheel_sha256": "...", "record_sha256": "...", "payload_sha256": "..."}]
}
```

精确规则如下。

1. verifier 从 Gitlink 对应 commit blob 读取 `pyproject.toml` 与 `uv.lock`，同时要求当前 tracked bytes 与 blob 一致、两仓 full-clean。它以 `CPython 3.13`、Linux/x86_64、`cu130` dependency group 为唯一目标环境；该四元组、两源文件 SHA 与解析得到的 package/version/wheel SHA 列表均是 verifier-owned。任何未能以 stdlib `tomllib` 精确求值的 marker、group 或 lock schema 均 FAIL，不猜测或降级。
2. 锁定解析所需的每个 wheel archive 都是一个单独 external asset：绝对 canonical path、文件 SHA256、wheel filename 都必须等于 Gitlink `uv.lock` 中该 package/version/平台的唯一 wheel。缺 wheel、多个候选或 wheel SHA 不匹配均 FAIL；不访问网络、不运行 uv/pip。
3. 对每个 wheel，verifier 用 `zipfile`/CSV 读取 wheel 内 `.dist-info/RECORD`。每个 wheel-record 中带 SHA256 的 importable payload 必须在 venv site-packages 存在且字节 hash 一致；wheel-record 未哈希的 importable `.py`/extension/data payload 一律 FAIL。由 installer 生成且不属于 wheel import payload 的 console scripts 不能进入批准的 child path，因而不纳入允许集。
4. venv 中的对应 `.dist-info/RECORD`、`METADATA`、`direct_url.json`（若存在）和所有已批准 importable payload 也分别 hash，并以排序后的 `(relative_path, sha256)` canonical JSON 形成 `payload_sha256`。观察值必须同时等于 verifier 由已绑定 wheel 导出的期望 payload；不能只与新写的 P4 record 自洽。缺项、额外同名 distribution、版本不符、RECORD 自改、Python/原生扩展任一字节变化均 FAIL。
5. package set 是锁定解析的完整 runtime closure，不采用当前安装 METADATA 的 `Requires-Dist` 反推；解析目标、`pyproject.toml`/`uv.lock` blob SHA、wheel archive SHA 与 payload SHA 都写入 P4 record 作为证据。若实际 compose 需要而 lock resolution 不含的 distribution，必须先新建设计/审核，不能临时白名单。

这使 lock/wheel archive 成为独立真源，已安装 `.dist-info/METADATA` 或 `RECORD` 无法单独改写后获得 self-consistent PASS。

## 3. 无 startup-code 的 P5 bootstrap

P5 child 固定用 lexical launcher 启动 `-I -S` 的 stdlib bootstrap。`-I` 忽略环境 `PYTHONPATH` 和 user site，`-S` 禁止 `site` 初始化、`.pth`、`sitecustomize` 与 `usercustomize`。P5 不调用 `site.addsitedir()`，也不在 guard 前 import 任何 third-party/project module。

Python 3.13 的 `-S` 下不得假定 `sys.prefix` 仍为 venv。因此 bootstrap 从已绑定 lexical path 推导 venv 根并验证 `pyvenv.cfg`；只在所有 lexical/base/cfg/lock/wheel/payload 检查完成后，显式重写 `sys.path`。其精确 canonical grammar（按顺序、去重且 symlink-equivalent 只可出现一次）是：

1. base interpreter 的 `sysconfig` 标准库目录与动态扩展目录；
2. exact production `<root>/cosmos-framework`（替代被 `-I` 忽略的 D005 `PYTHONPATH`，仍把该环境键逐字记录/核验）；
3. exact 已绑定 venv `site-packages`。

bootstrap 开始时的 `sys.path` 每项必须属于第 1 类；重写后每项必须逐项等于上述列表，且不得有 zip、cwd、脚本目录、user/system/external site-packages 或任何未批准路径。所有路径以 `resolve(strict=True)` 的 canonical path 比较；lexical launcher 本身仍按 raw lexical payload 单独比较。随后才 import Hydra/Pydantic/Cosmos 并 compose。

`pyvenv.cfg` 必须含并精确绑定 `include-system-site-packages = false`。v0.2 明确拒绝 site-packages 中任意 `.pth`、`sitecustomize.py`、`usercustomize.py`：它们在 `-I -S` 下不会执行，且在 payload/site-packages 审计中发现任一即 FAIL，而不是选择性绑定。该策略同时拒绝所有外部 site-packages，不论优先级。

## 4. 实现边界与永久回归

获批后仅允许 root `tools/g0/verify_r09_b2_p4_d005.py`、`tools/g0/test_verify_r09_b2_p4_d005.py`、P5 exporter/verifier 与对应标准库 CPU tests 的最小修改。P5 child argv/request/envelope 必须完整携带新版 interpreter/environment object，并以 `lexical_path -I -S` 启动；resolved-config diff 白名单不变。

永久 CPU-only、无网络/compose/GPU 回归至少包括：

| 场景 | 预期 |
| --- | --- |
| 正常 lexical symlink、锁定 wheel、完整 payload、`-I -S` path grammar | PASS |
| argv[0] 或 child executable 改为 realpath | FAIL |
| launcher payload/类型、base binary、cfg、lock/pyproject blob/current bytes 改变 | FAIL |
| wheel 缺失/多候选/SHA 错，installed RECORD/payload/extension 改变或额外同名 distribution | FAIL |
| `.pth`、`sitecustomize.py`、`usercustomize.py`、system-site=true、任意 external site-packages | FAIL |
| `-S` bootstrap 初始 path 含非 stdlib，或重写后顺序/重复/canonical path 不符 | import 前 FAIL |
| 两 backend interpreter/environment provenance 对象不同 | pair match FAIL |

实现 static tests PASS 后仍须重新审核实现；随后才可在新的 clean isolated P4 root 生成新的 `FROZEN_NOT_EXECUTED` records。P5 export 还需要新的 request hash、全新 canonical output 与三方独立执行授权。旧 attempt 绝不重跑。

## 5. 审核请求

本设计仅请求 `APPROVE_TO_IMPLEMENT_P4_INTERPRETER_PROVENANCE` 或 `REQUEST_CHANGES`。不授权 P4 record 重冻、P5 export/retry/compose、CUDA/GPU、torchrun、模型/dataloader/optimizer/checkpoint、weights/data/MP4、训练、评测、推理或 B2-T。
