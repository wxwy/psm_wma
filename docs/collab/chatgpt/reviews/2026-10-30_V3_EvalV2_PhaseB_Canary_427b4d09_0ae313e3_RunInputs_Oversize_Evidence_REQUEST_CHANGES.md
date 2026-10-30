# V3 EvalV2 Phase B 真实共享 GPU Canary — Run Inputs Oversize Evidence Gate

- 审核日期：2026-10-30（CST）。
- **Formal Root**：`427b4d09cdd8070820a39b93ebf2ff832a23e359`。
- **Child / Gitlink**：`0ae313e329d290fc6b8a50fda1112820fb7ac485`。
- 本次为**新增真实 Canary Evidence 的增量审核**；formal 生产代码未变化，**不重复**前一版 Shared-GPU Code/CPU Gate。V3 其后的 NoTTT docs-only 提交不是本次生产 target。
- **本轮 Verdict：`REQUEST_CHANGES`（真实 Canary Evidence Gate，生产阻断）**。既有 Shared-GPU CPU63 / Ruff PASS 作为原 scope 的历史事实保留，不得被外推为真实 GPU Canary PASS。
- Evidence 来源：DS_PRO 用户粘贴的 2026-10-30 现场报告；本会话不能直接读取 DS 服务器 `/tmp/ds_pro_canary_gpu_20261030/evidence/` 下原始 stdout/log/JSON，故 `20989831 B`、`123363` 资产及 GPU7 现场资源属于 **DS_REPORTED / RAW_NOT_INDEPENDENTLY_VERIFIED**。下面代码路径独立取自 GitHub 精确 SHA。

## 独立 Finding

### F5-P1 HIGH — 无界 vendor probe 内容进入有界 `run_inputs.json`，真实 Fresh 必败

- Root `scripts/robocasa_vendor.py:62-132`：`audit_source()` 对每个未跟踪资产验证 SHA，并将所有资产哈希作为 `untracked_asset_sha256` 返回；`:203-231` 的 `evaluation_runtime` 含这张清单，并以 canonical SHA256 得到 `runtime.digest`；`:260-286` 同时保留包含 `PSM_RUNTIME` 全量 JSON 的原始 stdout/stderr。
- Root `scripts/robocasa_eval_v2/identity.py:148-169,201-216`：`prepare()` 使用真实验证的 `runtime.digest` 计算独立 `runtime_identity`，但又把整张 `runtime` 清单和 `runtime_probe_evidence`（含原始 stdout）一起塞进 `inputs`。
- Root `scripts/robocasa_eval_v2/cli.py:119-144`：Fresh 经 `store.create()` 后在锁内调用普通 `write(run_inputs.json, inputs)`，后续仍用普通 `read()`。完整 payload 超限时不进入 Runtime/Sim，更不会有 B=2 GPU 测试。
- Child `cosmos_framework/evaluation/robocasa_v2/store.py:30,75-99,117-124`：`MAX_JSON=256*1024`，普通 read/write 必须受此上限保护；已存在的 `write_report` 仅允许 `summary.json` 且上限16MiB，不能被误用来存 21MB vendor 证据。
- Root `third_party/robosuite_patches/README.md:99-109` 已明确规定：原始 `runtime_probe_evidence` 与稳定 manifest 分离，作为证据持久化，**不进入 Resume equality data**。当前 `run_inputs.json` 的内容与此契约不一致。
- 因此，DS 观察到的 `ValueError("oversized JSON")` 是真实数据规模下可由源码机械证实的生产缺陷；**不是共享 GPU 拒绝、不是配置错、也不是需要提升所有 JSON 上限的理由**。

### F5-P2（正确保护，不能绕过）

- `identity.py:52-64` 的 `verify_source` 对 Root/Child 污染及 Gitlink drift 的 fail-closed 是预期行为。DS 本地放宽 `store.py` 的临时改动遭拒，不能作为新缺陷；正式 Candidate 必须形成新的精确 Root/Child/Gitlink 并从 clean worktree 执行。
- 先前 `iter_000009900` 被训练轮换删除属于启动资产时效问题，现场更换完整 `iter_000010000` 后暴露上述生产 blocker；重跑前仅需重新确认 checkpoint 完整、可稳定读取，不扩大任务范围。

## 最小整改范围（交给 Codex 实现，不由 DS 修改生产代码）

1. **保持 vendor probe 验证强度完全不变**：不得停止对安装资产的逐 SHA 验证，不删真实 `runtime.digest`，不跳过 `collect_runtime()`，不关 `verify_source()`。
2. 将 Fresh/Resume 持久化的 `run_inputs.json` 降为真实下游所需的**有界、稳定身份摘要**：保留 `inputs["runtime"]["digest"]`（`runtime.py:297,365` 的实际消费点）、模型/任务/库/路径/根子仓身份及原有 runtime_identity/manifest 约束；不要存完整 asset hash map 或 raw stdout。要审阅所有对 `inputs` 的真实读取点，不能为缩小文件删掉必需身份字段。256KiB 普通 JSON 上限不变。
3. 完整经验证的 `evaluation_runtime` + `runtime_probe_evidence` 以**独立、只追加/不覆盖的内部 Evidence** 持久化，使用专用路径限制的大记录原子写入口（例如严格限定 `_internal/runtime_probe/*.json`，独立限额64MiB）。复用既有 safe-path/no-symlink、O_EXCL/no-follow、fsync 和目录同步合同，不给所有 `read/write` 开通任意 `limit` 绕过；超过专用上限仍 fail-closed，不截断。真实 Runtime 启动前须已有可审计完整 Evidence 和小 `run_inputs`。保存路径位于隔离 Eval output，不进入 Root/Child source tree。
4. **Resume** 仍以运行时重新验证得到的 `runtime.digest` / 派生 `runtime_identity` 与 immutable Manifest 一致为准；独立证据（尤其含 warning 的 stdout）不进入 `run_inputs`、其 `digest(anchor)` 或 scientific equality。不可通过 `replace=True` 改写此前运行时证据。当前无成功写入的大 `run_inputs` 历史对象，无需引入兼容迁移。
5. 原代码接口尽量少改：预计 Root `scripts/robocasa_eval_v2/{identity.py,cli.py}`，Child `cosmos_framework/evaluation/robocasa_v2/store.py` 专用 writer（如确需），以及相邻 `tools/v3/eval_v2_production_tests/` 定向测试。不得动 Queue/Batch/LocalTTT/NoTTT/训练、checkpoint、GPU 配置或测试验收语义。

## 新候选验收

- 合成 CPU 大型 `collect_runtime`：至少覆盖 `>256KiB`，建议再覆盖与现场同量级 `>16MiB`，**必须通过公开 Fresh/Resume CLI** 而非 helper-only；`run_inputs.json < 256KiB`、运行时 `inputs.runtime.digest` 正确、独立 Evidence 完整可读/可哈希，resume source/manifest/model identity 仍严格，且同一次 `fresh` 失败后新 namespace 执行不复用污染目录。
- 对比 1 个相同 stable `runtime.digest` 但 raw stdout 不同的 Resume，验证前者可通过、后者只改变独立 Evidence，不污染 anchor equality；对应真实 runtime digest 改动必须拒绝 Resume。
- 普通 ledger 仍 256KiB 严格拒绝；大 Evidence 专用路径可写、错误路径、超限、symlink、partial/publish failure 均 fail-closed；无法写入完整 Evidence 时不得启动 Runtime 或伪造成功 Summary。
- 旧 CPU 回归按影响面窄跑，Ruff/format/compile/diff-check PASS；新 Root/Child/Gitlink exact Pair 提交后 GPT **fresh incremental Code Gate**，不对旧 Pair 重审。
- GPT 批准新源码后，由 DS 在独立 clean Pair 上**只重新运行原授权 1GPU/2Sim/B2/4 Episode Canary** 并提交真实 B=2 hit、VRAM/latency、4结果及视频与 cleanup 证据。不是授权 900、NoTTT Job 切换或新增长跑。

## 当前阶段裁决

- `SHARED_GPU_CODE_QUICK_CPU=PASS`（历史 scope 不变）。
- `REAL_GPU_CANARY=BLOCKED_BY_PRODUCTION_F5_P1`。
- `REAL_CANARY_EVIDENCE_VERDICT=REQUEST_CHANGES`。
- 先实施最小持久化修复；不应在旧 SHA 上改配置、反复 Fresh 或升级全局 JSON 容量来绕过。
