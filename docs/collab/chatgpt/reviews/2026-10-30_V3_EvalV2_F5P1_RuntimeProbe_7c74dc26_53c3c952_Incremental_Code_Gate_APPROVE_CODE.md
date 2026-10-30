# V3 EvalV2 PhaseB F5-P1 — Runtime Probe 持久化最小整改：增量 Code Gate

- **日期**：2026-10-30（CST）；角色：ChatGPT 独立增量审核。
- **正式 Formal Root**：`7c74dc26ac4837f193727ecf847b9b64554c18b2`。
- **正式 Child / Root Gitlink**：`53c3c95202e14d3b72d236eee6899a80acf82989`，已从 Root 的正式 GitTree 核实。
- **上轮被阻断的生产 Pair**：Root `427b4d09cdd8070820a39b93ebf2ff832a23e359` / Child `0ae313e329d290fc6b8a50fda1112820fb7ac485`。
- **Author Evidence/交接**：`docs/collab/codex/evidence/2026-10-30_eval_v2_runtime_probe_F5/`，证据位于 bookkeeping commit `608f55dccff6077e276e78644af6a578b4087781`；该 SHA **不得代替正式 Root**。
- **正式结论：`APPROVE_CODE`（仅 F5-P1 有界持久化增量 + 作者合成 CPU Evidence）**。上一真实 Canary `BLOCKED` 记录继续作为历史；新 Pair **没有**真实 GPU Canary/Real Vendor/正式900通过的证据。

## 1. 实际差异范围（独立取自 GitHub exact SHA）

Root `427b4d09..7c74dc26` **单提交，4 项**：

1. `scripts/robocasa_eval_v2/cli.py`：在锁内把已验证的完整 `evaluation_runtime` + `runtime_probe_evidence` 和 `manifest_digest` 独立写到 `_internal/runtime_probe/<uuid>.json`，将 `inputs.runtime` 投影为只含已验证 `digest` 的紧凑字段，并移除 `runtime_probe_evidence`，保持其他身份/模型/Task/库/时钟字段；Fresh 只写一次 `run_inputs.json`，Resume 只读旧 anchor、不改写；每次 invocation 写入 Evidence 相对路径和 canonical SHA256。
2. `tools/v3/eval_v2_production_tests/entry_test.py`：只为既有 fake prepare 补必需 `runtime` 与 `runtime_probe_evidence` 字段。
3. 新增 `tools/v3/eval_v2_production_tests/runtime_evidence_test.py`，480 行、21 个用例；含大型 Fresh/Resume、真实小型 Git Root/Child + 原 `verify_source()`、身份漂移拒绝、写入失败和存储安全负例。
4. Child Gitlink 升级至下述准确 SHA。

Child `0ae313e3..53c3c952` **单提交、1 个文件**：`cosmos_framework/evaluation/robocasa_v2/store.py` 只新增 `MAX_RUNTIME_PROBE = 64*MiB` 与 `write_runtime_probe`。路径必须匹配 `_internal/runtime_probe/<32 lowercase hex>.json`；复用 `_publish` 的 no-symlink、临时文件 `O_EXCL|O_NOFOLLOW`、fsync、无覆盖 link、目录 fsync。**旧 `read/write MAX_JSON=256KiB` 与 `summary.json MAX_REPORT=16MiB` 未变。**

未改：`identity.py`、`robocasa_vendor.py`、`runtime.py`、`resources.py`、`model_identity.py`、Queue/Batch/LocalTTT/NoTTT/训练/Checkpoint。原逐资产 SHA 验证、`verify_source()`、manifest runtime_identity 与 Resume 的模型/配置/运行时身份检查保持原有权威。

## 2. 独立证据检查

- 实际读取 GitHub 作者原始 `raw/final-formatted/junit.xml`：`tests=85, errors=0, failures=0, skipped=0`，解析得到**85 个不同测试名称**；对应 `console.log` 最终 `85 passed in 26.24s`、`execution.json` shell0、source before/after exact Formal Pair +10项源码SHA前后一致。包含21项新测试、15项旧 entry、49项旧 Store。**没有自行在 DS 服务器重跑85。**
- 直接读取归档原件 `large_case/_internal/run_inputs.json`：文件2,553字节，10类身份字段，`runtime={"digest":"0c05a671..."}`，无 `runtime_probe_evidence`；`verification_cache.json` 的 `anchor_sha256=fafdda6a...`。两次 `_internal/invocations/*.json` 分别指向不同 UUID Evidence，带不同 canonical SHA256。
- 大型合成 CPU test 生成150,000条资产SHA表并通过完整公共 Fresh→Resume；作者 raw JUnit 及 `V2_RUNTIME_EVIDENCE_WITNESS` 指示完整两份 Evidence 分别37,200,840与37,200,847字节，原始 raw stdout warning 改变但 runtime.digest、anchor/Cache/Core 逐位不变。作者发布了对应 `.json.gz` 的 SHA/长度及无损重构声明。**本审核未独立解压两份二进制 gzip，也未声称在服务器复核真实123,363资产；大尺寸与无损事实仍以原始测试断言及作者仓库证据为限。**
- 定向负例实际源码/JUnit 覆盖：`runtime/model/config/source_dirty/source_commit/child` 六类 Resume identity drift 在 Runtime/evidence append 前拒绝；Fresh/Resume evidence 写失败不构造 Runtime；旧 Fresh namespace 拒绝再用；普通256KiB JSON仍拒绝；专用64MiB超限、非法路径、UUID、symlink、覆盖、partial write/file fsync/link/directory fsync 错误。目录 fsync 失败可留下完整但无成功回执的诊断残留，错误不被吞掉。
- 作者 `handoff.json` 报告 Ruff/format/syntax/diff checks exit0；本审核已直接检查正式源码 diff 与相邻方法，**未独立运行 Ruff，且未取得独立 DS CPU 证据**。此限制不被误记为独立 Full Gate PASS。

## 3. Findings / Gate 裁定

- **F5-P1 HIGH：CLOSED。** 完整运行探针不再塞进受256KiB限制的 `run_inputs`；紧凑 Runtime Digest、Manifest、Model Cache anchor 与 Legacy Store 保护保持；Evidence 被有界且仅新增的独立原子文件承接。
- **本增量未发现新的阻断级生产 contract violation。** 专用 Evidence writer 的路径检查依靠固定两个目录名，真正 Eval output 归属由 CLI 构造 `root/_internal/runtime_probe/<uuid>.json` 保证；该代码仅作为此内部入口使用，未暴露任意 `limit` 参数。
- 原旧 Pair Canary `BLOCKED` 属既有 Evidence，不能被作者合成 CPU PASS 改写为真实 Canary PASS；若真实 Vendor 超过64MiB，仍应 fail-closed，不能静默截断或放宽全局 JSON。
- 本增量 **不要求重跑旧435 CPU**；即使作者静态/CPU通过也不允许宣称真实 RoboCasa、B=2命中、GPU显存、MP4或成功率已经通过。

## 4. Verdict / 下步范围

**`APPROVE_CODE`**：允许把此准确 Formal Root+Child 当作 F5-P1 的可测试候选；如已存在 Owner 对原定范围的授权，DS 只可在独立 clean exact Pair、稳定完整 Checkpoint、新 Eval output namespace 下，重复原来 **1 GPU × 2 Sim × B=2 × CloseFridge/OpenCabinet 各2 Episode（总4）** 的真实 Canary；须保留独立运行原件、真实 batch histogram、4Episode/MP4、state隔离、显存/latency与进程清理。失败保留 Evidence、不得自动扩大或转正式900。

**不授权**生产代码自动合并到远端 V3/Child、停止或迁移 NoTTT Job、对旧 SHA 打补丁、修改 GPU 共享限制、正式900 Episode、额外实验或把合成测试当作真实 GPU 结论。
