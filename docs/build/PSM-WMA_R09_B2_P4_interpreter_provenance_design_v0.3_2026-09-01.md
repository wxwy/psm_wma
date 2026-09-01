# R09-B2 P4 Interpreter Provenance 静态设计 v0.3

**状态**：draft，待三方审核。v0.3 替换 v0.2 的 P4 install-profile、source-type 与 CPython getpath 定义，以关闭 ChatGPT review `2026-09-01_R09_B2_P4_interpreter_provenance_design_v02_516b5ef_8ebe4d1.md` 的两个 HIGH 与一个 MEDIUM。v0.1/v0.2 和旧 P4/P5 attempt 均保留为历史；本文件不授权实现、record 重冻、compose/export、GPU、训练或任何 runtime Gate。

## 1. 固定的 P4 install profile

P4 D005 的冻结入口是 `cosmos_framework.scripts.train`，不是仅能 compose 的最小环境。新版 verifier-owned profile 精确为：

```text
python_full_version = 3.13.*
sys_platform = linux
platform_machine = x86_64
project_extras = ["train"]
dependency_groups = ["cu130"]
```

它从 P4 frozen command 的 training entrypoint 与 Gitlink `pyproject.toml` 的 `[project.optional-dependencies].train`、`[dependency-groups].cu130` 共同导出，不从当前 venv 或 P5 compose 结果推断。P4 pair verifier 必须对两 backend 逐值要求该完整 profile；遗漏 `train`、遗漏/替换 `cu130`、添加其它 extra/group 均 FAIL，即使 base/Hydra/Torch 恰好可导入。永久负例必须覆盖“base+cu130 完整但 train 缺失”。

`pyproject.toml`、`uv.lock` 都从 frozen Gitlink 的 commit blob 读取，并逐字比对 current tracked bytes；两仓 full-clean 仍是前提。stdlb `tomllib` resolver 必须在这一精确 profile 下处理 lock marker/source 分支；不支持、歧义或多解均 FAIL，不调用 uv/pip/网络。

## 2. 完整 closure 的 source-type grammar

lock resolution 的每个 package 必须恰好属于下列类型，未知类型 FAIL；不会静默排除任何训练时可导入的 payload。

| 类型 | 独立真源与 installed 验证 |
| --- | --- |
| first-party editable `cosmos-framework` | 仅信任 frozen Gitlink 的 tracked source tree：verifier 从 commit blob/current bytes 重算 tree digest；不信任 editable `.dist-info`。实际 `_editable_impl_cosmos_framework.pth` 是允许的**惰性**安装证据，raw bytes 必须恰为 production framework canonical path，并记录 SHA；P5 `-I -S` 不处理它，bootstrap 只手动加入该已绑定 source tree。 |
| registry wheel | Gitlink `uv.lock` 的 package/version/平台唯一 wheel filename+SHA 是真源。对应 wheel archive 是单独 external asset；`zipfile` 读取 wheel RECORD，所有 hashed importable `.py`/native extension/data 均逐字匹配 site-packages，未哈希 importable payload、缺失/额外同名 distribution、RECORD/METADATA 篡改均 FAIL。 |
| Git/VCS（当前 `lerobot`、`megatron-core` 若由 train profile 解析进入） | lock 中 URL+commit 是 source identity。每个 source 必有独立、absolute/canonical、clean checkout external asset，HEAD 必为 lock commit，tracked tree digest 从该 commit blob/current bytes 双重重算；installed payload 须与该 source checkout 的可导入 tree 映射逐文件 hash 一致。source checkout 缺失、dirty、commit/tree/payload 不符或不可确定 mapping 一律 FAIL；不退化为当前 `.dist-info/direct_url.json` 自证。 |

每个已安装 distribution 的观察 RECORD、METADATA、`direct_url.json`（若存在）以及排序 `(relative_path,sha256)` `payload_sha256` 都写入 P4 evidence，但只能与上述 verifier-owned source truth 比较，不能自行成为 expected truth。

site-packages 的 `.pth` roster 是一个单独的严格对象：当前 profile 允许且仅允许 `_editable_impl_cosmos_framework.pth`、`_virtualenv.pth`、`a1_coverage.pth`、`distutils-precedence.pth` 的精确 basename/raw SHA，任何新增、缺失或字节变化 FAIL。它们在 `-I -S` 下均不执行；永久 test 对每个含 `import` 的允许 `.pth` 放置 sentinel，证明 bootstrap 前 sentinel 未触发。`sitecustomize.py`、`usercustomize.py` 一律不存在；`pyvenv.cfg` 必须精确含 `include-system-site-packages = false`。

## 3. `-I -S` initial getpath 与 runtime path grammar

child 仍以 lexical venv launcher、`-I -S` 启动，因而在 bootstrap 前没有 site/.pth/customize/user-site 执行。`-S` 时不能用 `sys.prefix` 识别 venv；bootstrap 从已绑定 lexical path 推导 `<root>/cosmos-framework/.venv`，再验证 `pyvenv.cfg`、base binary、profile/source/payload。

对于已绑定 base executable SHA，P4 verifier 机械派生且 P5 bootstrap exact-match 的 initial getpath vector 是：

```text
<base-prefix>/lib/python313.zip     # 唯一允许的 zip candidate，必须不存在且不会保留
<base-prefix>/lib/python3.13        # existing stdlib directory
<base-prefix>/lib/python3.13/lib-dynload  # existing dynamic-extension directory
```

该 absent zip 是 CPython 3.13 getpath 的唯一可接受非目录项；它必须精确等于上述 base-prefix candidate，不能存在、不能被 import、且在 bootstrap 验证后从 runtime path 删除。任一其它 zip、不存在路径、cwd/script directory、user/system/external site-packages、乱序、重复或 symlink-equivalent duplicate 都 FAIL。P4 record 保存 derived initial vector 作为证据，verifier 与 child 均重算而不接受 caller supplied vector。

全部 provenance 完成后，bootstrap 以 `resolve(strict=True)`、唯一 canonical path 和固定顺序将 runtime `sys.path` 重写为：

1. base stdlib；
2. base `lib-dynload`；
3. exact production `<root>/cosmos-framework` tracked source；
4. exact bound venv site-packages。

然后才 import Hydra/Pydantic/Cosmos。D005 的 `PYTHONPATH` 仍逐字环境合同的一部分，但 `-I` 忽略它；source path 的生效只能来自上面已验证的第 3 项。

## 4. 实现与测试边界

获批后仅允许 root P4 verifier/tests、P5 exporter/verifier/tests 的最小实现，且新版 schema 必须拒绝旧 v2 records。不得新建/改造 venv、调用 compose、访问模型/数据或启动 GPU。

永久 CPU-only tests 至少包括：

- 缺 train extra、替换/遗漏 cu130 group；
- registry wheel payload/RECORD/extension 篡改、VCS commit/tree/payload 篡改、editable source/pth 篡改；
- 允许 `.pth` 含 import 仍在 `-I -S` 下 inert，以及新增 `.pth`、customize、system-site 的 FAIL；
- exact absent `python313.zip` candidate 的 PASS，存在/任意其它 zip/initial path 向量异常的 FAIL；
- lexical argv 被 realpath 替换、base/cfg/lock source change、runtime path order/duplicate/external path、backend pair interpreter/profile 不等的 FAIL。

static implementation review通过后，P4 record 重冻、P5 export 和后续训练仍分别需要新的三方审核与执行授权；旧 P5 attempts 绝不重跑。

## 5. 审核请求

本设计仅请求 `APPROVE_TO_IMPLEMENT_P4_INTERPRETER_PROVENANCE` 或 `REQUEST_CHANGES`。不授权 P4 record 重冻、P5 export/retry/compose、CUDA/GPU、torchrun、模型/dataloader/optimizer/checkpoint、weights/data/MP4、训练、评测、推理或 B2-T。
