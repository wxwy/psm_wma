# PSM-WMA G0-R01 执行产物复核报告

- **日期**：2026-08-13
- **审查者**：Kimi（独立复核）
- **对象任务**：G0-R01（执行方 Codex，状态 REVIEW）
- **审查依据**：`docs/build/PSM-WMA_G0_R01_implementation_runbook_v0.1.md` §5-§10
- **审查性质**：只读复核，未修改任何文件、未执行正式推理
- **结论**：**APPROVE**（附 2 个 MEDIUM 收尾项，转 DONE 前关闭）

## 1. 逐项核验（Gate JSON vs 原始证据）

Gate JSON：`artifacts/g0/r01/R01_edge_policy_droid_smoke.json`，status=PASS，blocker/exception 为 null，missing_evidence 为空。

| 项 | Gate JSON | 原始证据 | 结果 |
|---|---|---|---|
| cosmos_commit | `103c5d1687d290b050e4890f48ff7a38b12742ef` | `git -C cosmos-framework rev-parse HEAD` | 一致，等于固定基线 |
| repo_commit | `2e6fc13cabe90bbd429421b643a9d0019c8484f1` | 当前根仓库 HEAD | 一致（见 MEDIUM-2） |
| checkpoint 完整性 | true | `preflight.log`：4 个索引引用文件 + `vae/diffusion_pytorch_model.safetensors` 全部存在且非空 | PASS |
| env | python 3.13.13 / torch 2.10.0+cu130 / cuDNN 91501 / LD_LIBRARY_PATH cuDNN 首位 | 与已验证环境一致 | PASS |
| Reasoner latency | warmup [14591.4, 14435.2] ms；steady 6 项（约 13.23–13.40 s） | `reasoner/benchmark.json` 逐值相符（2 个计时键 × warmup 1 / 3 次迭代，对应 `--warmup 1 --num-iterations 3`） | PASS |
| Reasoner 输出 | finite=true | `reasoner/reasoner/sample_outputs.json` status=success；`reasoner_text.txt` 非空、无 NaN/Inf | PASS |
| Policy | shape [32,8]，finite，2 次 timed 请求（5961.4 / 6002.9 ms） | `robolab_client_metrics.json` 一致；`policy_server.log:24` 记录 `domain='droid_lerobot' action_dim=8 chunk=32 fps=15.0 num_steps=4 seed=0 deterministic` | PASS |
| World | shape [33,528,640,3]，finite | metrics 记录 uint8、min 0 / max 255；server 配置 `encode_exact_durations=[33]` 与 33 帧吻合 | PASS |
| peak_vram_gb | 13.69140625 | `policy_vram.csv` max=14020 MB，14020/1024=13.69140625 精确一致；`reasoner_vram.csv` max=6918 MB≈6.76 GiB | PASS |
| server 加载 | — | `policy_server.log:11` VAE 从 registry 路径 `Wan2.2_VAE.pth` 加载成功；全部日志无 error/exception/traceback | PASS |
| 请求-服务端对应 | — | server 日志 3 次 UniPC 采样（num_steps=4）与 client 3 次请求（1 warmup + 2 timed）时间戳一一对应 | PASS |

Runbook §10 的四项 PASS 条件（checkpoint、Reasoner、Policy、shared Generator/world）均有机器可读证据支撑，不存在"未实际验证却宣称 PASS"。

## 2. 审查发现

### MEDIUM-1：实际客户端与 Runbook §7.2 指定路径不一致，未记录

- **问题**：Runbook §7.2 指定在 RoboLab 客户端容器执行 `policies/cosmos3/run.py --task BananaInBowlTask`；实际使用本地自写最小客户端 `tools/g0/run_r01_policy_client.py`。
- **证据**：`tools/g0/run_r01_policy_client.py:12-57`（openpi msgpack 协议、单调时钟计时、逐请求读取 action/video 并断言 shape/finite，满足 §7.2 证据契约）；`artifacts/g0/r01/robolab_client.log` 为直接 JSONL，非 RoboLab 输出。
- **影响**：不影响本次 Gate 结论，但复现者按 Runbook 会走到不可用的命令路径。
- **最小修复**：Runbook §7.2 补记本次以 `tools/g0/run_r01_policy_client.py` 替代 RoboLab run.py 的事实，并将该脚本纳入提交。
- **是否阻止 DONE**：是（文档一致性收尾，分钟级）。

### MEDIUM-2：证据生成代码未提交，provenance 链不完整

- **问题**：Gate JSON 记录 `repo_commit=2e6fc13`，但产生证据时工作区存在未提交修改（`tools/g0/collect_r01_gate_json.py` modified；`tools/g0/run_r01_policy_client.py`、`tools/g0/sample_cuda_memory.py`、`artifacts/` untracked）。`2e6fc13` 不含生成证据的实际代码。
- **证据**：复核时 `git status --short` 输出。
- **最小修复**：提交 `tools/g0/` 与相关文档更新后，重跑 `collect_r01_gate_json.py`（秒级、无需 GPU）刷新 Gate JSON 的 commit 字段；按项目约定决定 `artifacts/g0/` 是否入库。
- **是否阻止 DONE**：是。

### LOW-1：mp4 未逐帧目检

- `policy_world_preview.mp4`（21,631 字节）内容未做视觉检查，当前环境不支持视频读取；shape/finite/值域已由 metrics JSON 断言覆盖，风险可忽略。

### LOW-2：驱动版本非常规组合

- `driver_version=470.57.02` 搭配 torch 2.10.0+cu130 非常规，但运行成功，仅作事实记录。

## 3. 已执行的只读命令

- `find/ls artifacts/g0/r01`：产物清单核对（17 个文件，覆盖 Runbook §9 全部约定产物）。
- 读取 `R01_edge_policy_droid_smoke.json`、`robolab_client_metrics.json`、`reasoner/benchmark.json`、`reasoner/reasoner/sample_outputs.json`、`reasoner_text.txt`、`robolab_client.log`。
- 解析 `reasoner_vram.csv`（550 行）与 `policy_vram.csv`（1183 行）求峰值。
- `grep` 全部日志文件检查 error/exception/traceback（无命中）；提取 server ready 行与 VAE 加载行。
- `git log cbdf544..HEAD`（2 个提交：`dde7621`、`2e6fc13`）、`git status --short`、`git rev-parse HEAD`、子模块 `rev-parse HEAD`。
- 读取 `tools/g0/run_r01_policy_client.py` 验证客户端协议与计时契约。

## 4. 未执行的验证及原因

- mp4 视觉内容检查：工具不支持视频读取（LOW-1）。
- 独立重跑三条 pathway：复核职责是检查证据链；正式重跑属执行方职责且需要 GPU。

## 5. 结论

G0-R01 的 PASS 有完整、一致、机器可判定的证据支撑，复核 **APPROVE**。MEDIUM-1/2 关闭（提交代码 + Runbook 补记客户端替代 + 重跑 collect 刷新 commit）后，G0-R01 可正式转 DONE，随后解锁 R02/R03。

## 6. 2026-08-14 收尾记录

- MEDIUM-1：已关闭。Runbook §7.2 已记录实际使用
  `tools/g0/run_r01_policy_client.py`，并记录用户批准的 RoboLab 基础设施豁免。
- MEDIUM-2：证据生成工具及原始产物已提交于 `6ea7c9d`；Gate JSON 将于本次状态
  收尾提交后重新汇总，刷新 `repo_commit` provenance。
- RoboLab `BananaInBowlTask` 未通过：Isaac Sim 在 Orion 虚拟 GPU 上报
  `No device could be created`、`CUDA being in bad state`。本次放通不将其记为
  PASS，也不宣称获得 RoboLab closed-loop 结果。
- 用户决策：R01 作为官方 checkpoint 原生能力 smoke 直接放通；后续以可在当前
  服务器运行的 LIBERO/MuJoCo EGL 路线继续 R02-R06，R06 closed-loop 仍是 Memory
  实验前的硬门槛。
