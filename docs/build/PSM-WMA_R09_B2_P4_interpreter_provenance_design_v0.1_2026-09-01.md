# R09-B2 P4 Interpreter Provenance 静态设计 v0.1

**状态**：draft，待三方审核。本文件只处理 P4 D005 对 Python venv 启动身份的错误绑定；不执行 config export、torchrun、GPU、模型/数据/权重读取、训练、评测或推理。

## 触发事实与范围

P5 的两次已批准一次性 export 都已按 fail-closed 规则执行且不得重跑。

- attempt-1：`/disk/rl/.psm_wma_p5_static_export_20260901.attempt-66cda875ff0c469aa3f9dfa374d69ac6/`，在 Python 3.13 自动补入 `LC_CTYPE=C.UTF-8` 时被环境 guard 拒绝；该问题已由 P5 locale contract 修复。
- attempt-r2：`/disk/rl/.psm_wma_p5_static_export_20260901_r2.attempt-077e7905a208464bbf78889ae3857eff/`，环境 guard 通过后、compose 前导入 `pydantic` 失败；canonical 输出目录未创建。

r2 child 实际启动 `/root/.local/share/uv/python/cpython-3.13.7-linux-x86_64-gnu/bin/python3.13`，它没有 `pydantic`。实际项目 venv `<root>/cosmos-framework/.venv/bin/python` 有 `pydantic==2.12.5`、Hydra、OmegaConf 与 torch。根因是 P4 verifier 将 venv 启动器 `resolve()` 成了 base binary，随后 P5 把 record 的 `interpreter.realpath` 当作 argv[0] 使用。此问题与 RGB、latent cache、GPU 或训练数据无关。

本方案只重新冻结 P4 的解释器 provenance，并使后续 P5 能在被绑定的 venv 入口中运行。旧 P4 v2 record 与旧 P5 attempt 均保留为历史证据；不覆盖、不重试。

## 新的 P4 interpreter schema

P4 record schema 升级为新版本（实现阶段确定精确字符串；不得复用 v2 名称），并将 `inputs.external_assets.interpreter` 与 `command.interpreter` 绑定为同一个对象：

```json
{
  "lexical_path": "/abs/root/cosmos-framework/.venv/bin/python",
  "lexical_sha256": "<symlink payload 或 regular-file bytes SHA256>",
  "realpath": "/root/.local/share/uv/python/.../bin/python3.13",
  "realpath_sha256": "<base executable SHA256>",
  "pyvenv_cfg": {"path": "/abs/root/cosmos-framework/.venv/pyvenv.cfg", "sha256": "..."},
  "site_packages": {"path": "/abs/root/cosmos-framework/.venv/lib/python3.13/site-packages", "manifest_sha256": "...", "distributions": [{"name": "pydantic", "version": "2.12.5", "metadata_sha256": "..."}]}
}
```

约束：

1. `lexical_path` 必须是 `<frozen-root>/cosmos-framework/.venv/bin/python` 的绝对、未解析路径；`command.argv[0]` 必须逐字等于它。禁止以 `realpath` 作为启动 argv。
2. `realpath` 绑定底层 base interpreter 的常规文件 SHA256，只证明二进制身份，不能替代 lexical launcher。
3. `lexical_sha256` 对 symlink 使用 `readlink()` 原始 payload 的 SHA256；对常规文件使用文件字节 SHA256。verifier 同时要求当前文件类型一致，防止 launcher 去虚拟化。
4. `pyvenv.cfg` 必须存在于 venv 根，绝对路径精确匹配并 SHA256 绑定。
5. distribution manifest 枚举 compose 所需的 `pydantic`、`pydantic-core`、`hydra-core`、`omegaconf`、`torch` 及其 `.dist-info/METADATA` 声明的直接运行依赖闭包。每项记录规范化小写 name、版本、METADATA SHA256，按 name/version 排序并以 canonical JSON 求 manifest SHA256。缺项、重复、metadata 缺失、版本/哈希变化或同名重复均 FAIL。
6. P4 verifier 只使用 pathlib/hash/metadata 文本读取；不 import venv package、不调用 Python、不 compose、不触碰 CUDA。

## P5 的受控消费与 import 前断言

P5 parent 只从通过新版 P4 pair verifier 的 record 构造 child request。request 与 envelope 保留完整 interpreter object，不降维为 `{realpath, sha256}`。实际 child 命令使用 `lexical_path`。

在任何 `hydra`、`pydantic`、`cosmos_framework` import 前，child 必须 fail-closed 验证：

1. `sys.executable` 逐字等于 `lexical_path`，其 symlink/regular 形态正确；`Path(sys.executable).resolve()` 等于 `realpath` 且 base binary SHA256 匹配。
2. `sys.prefix` 逐字等于 `<root>/cosmos-framework/.venv`，且 `sys.base_prefix != sys.prefix`。
3. `pyvenv.cfg` 与 distribution manifest 重新验证。
4. `sys.path` 必含已绑定 `site_packages.path`；任一优先级更高、且不在 D005/Python 标准库允许来源的 `site-packages` 必 FAIL。
5. 既有 cwd、精确 D005 环境（含 `LC_CTYPE=C.UTF-8`）与未提前 import 约束继续逐项验证。

禁止向 uv base interpreter 安装包；禁止重建或修改项目 `.venv` 作为修复手段。

## 实现边界与迁移

实现获批后仅允许以下 root 工具及标准库 CPU tests 的最小修改：

- `tools/g0/verify_r09_b2_p4_d005.py`：新增 interpreter schema 与 lexical/base/cfg/manifest verifier，删除把 launcher 去虚拟化的 `resolve()` 语义。
- `tools/g0/test_verify_r09_b2_p4_d005.py`：fixture 改为 lexical symlink、`pyvenv.cfg` 和最小 `.dist-info/METADATA` tree，不调用实际 Python。
- `tools/g0/export_r09_b2_p5_resolved_config.py`、`tools/g0/verify_r09_b2_p5_full_config_diff.py`：只更新 P4 request/envelope 解析、child argv 与 import 前 preflight；不改变 resolved-config diff 白名单。
- 相应 P5 标准库 CPU tests：覆盖新的 request/envelope 字段和启动前拒绝。

完成实现后，旧 P4 D005 v2 仍不可用于 P5。必须在新的 clean、isolated P4 worktree 重新生成两份 `FROZEN_NOT_EXECUTED` record 与 pair verification；其 source/evidence SHA 将与旧记录不同。随后 P5 需要新的 static implementation review、新的冻结 request hash、三方独立执行授权和新的 canonical output root。旧 attempt-r2 绝不重跑。

## 永久测试与失败分流

| 场景 | 预期 |
| --- | --- |
| 正常 lexical symlink + base binary + cfg + manifest | P4 pair PASS |
| argv[0] 或 P5 child executable 改为 `realpath` | FAIL |
| lexical symlink payload、文件类型或 lexical SHA 改变 | FAIL |
| base binary SHA、`pyvenv.cfg` 路径/哈希改变 | FAIL |
| `pydantic`/`pydantic-core` 缺失、版本/metadata 哈希变化、重复同名 distribution | FAIL |
| child `sys.prefix == sys.base_prefix` 或绑定 site-packages 不在 `sys.path` | import 前 FAIL |
| locale/cwd/environment/pre-import Hydra contamination | 维持既有 FAIL |
| 两 backend P4 interpreter object 不同 | pair match FAIL |

静态测试 PASS 只说明 contract 可验证，不授权 P5 export。P4 静态 record 审查未通过则停止在 `G0-R09-B2-P4-INTERPRETER-PROVENANCE`；P4 通过而 P5 child preflight 失败，则保留一次性 attempt 证据并回到该 contract 的根因修复，不放宽 manifest、环境或 interpreter 检查。

## 审核请求

本设计请求三方仅给出 `APPROVE_TO_IMPLEMENT_P4_INTERPRETER_PROVENANCE` 或 `REQUEST_CHANGES`。批准后才实现上述 root-only 工具和 CPU tests；任何 P4 record 重冻、P5 export、GPU、torchrun、模型/数据/权重访问、训练、评测和推理都仍需后续独立审核与明确执行授权。
