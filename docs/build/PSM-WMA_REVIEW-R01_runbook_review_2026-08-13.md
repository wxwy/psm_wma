# REVIEW-R01 独立审查报告

**任务 ID**：REVIEW-R01
**审查对象**：`docs/build/PSM-WMA_G0_R01_implementation_runbook_v0.1.md`（Review Candidate）
**审查人**：Kimi（独立只读审查，未参与 Runbook 编写）
**日期**：2026-08-13
**固定基线**：根仓库 `cbdf544e61549c774626db1f0fd820292b6eceb4`；`cosmos-framework@103c5d1687d290b050e4890f48ff7a38b12742ef`
**环境**：`/root/venvs/psm_wma`；checkpoint `/gemini/code/models/Cosmos3-Edge-Policy-DROID`
**性质**：只读审查。未修改任何文件（本报告除外）、未执行正式推理、未提交/push。

## 审查结论：REQUEST_CHANGES

文档结构和 CLI 锚点核验整体扎实（两条命令的所有 flag 均与 `103c5d1` 源码逐字一致），但存在两处 HIGH 级可执行性缺口：**Gate JSON 要求的关键指标在当前命令下没有任何采集来源**，机器可读判定链断裂，不满足 DOC-R01/REVIEW-R01 的验收条件。

---

## BLOCKER

无。两条启动命令本身均可在固定提交上成立。

## HIGH

### H1. peak VRAM 与 warmup/steady latency 无采集手段，PASS 判据不可满足

- **问题**：Runbook 要求记录 peak VRAM 和 warmup/steady latency（行 124、168、177），Gate JSON 强制 `peak_vram_gb`（行 208），但两个官方入口都不产生这些数据：
  - `cosmos_framework.scripts.inference` 的 `benchmark.json` 只有 `{"all": {...}, "average": {...}}` 秒表（`cosmos_framework/inference/common/inference.py:243-260`）；且 Phase B 命令未传 `--warmup/--num-iterations`（默认 `warmup=0, num_iterations=1`，`common/args.py:813-816`），不存在 warmup/steady 拆分。inference 路径全仓无 `max_memory_allocated` 接线。
  - `action_policy_server_robolab` 每次请求只 log `prompt=... seed=...`（`cosmos_framework/scripts/action_policy_server_robolab.py:580`），无 latency/VRAM 日志；`--output-dir` 只收到 `console.log`/`debug.log`（`inference/common/init.py:239-252`）。模型卡 "inference latency is reported by the server"（checkpoint `README.md:326`）指的是 vLLM-Omni stack，不是本 PyTorch server。
  - Runbook 全文没有任何 nvidia-smi 采样、`torch.cuda.max_memory_allocated` 包装或客户端计时指令。
- **证据**：上述 file:line；Runbook 行 124/168/177/208 的判据与产物能力脱节。
- **最小修复**：在 Phase B/C 各加一段明确的采集步骤（如 `nvidia-smi --query-gpu=memory.used --format=csv -lms 500` 后台采样到 `artifacts/g0/r01/vram.csv`，或在允许的独立汇总脚本内调用 `torch.cuda.max_memory_allocated`）；Phase B 增加 `--warmup 1 --num-iterations 3`（注意 `--benchmark` 是 `num_iterations>1` 的前置，`common/args.py:825-826`），或在 Runbook 中明示 warmup/steady 由客户端计时产生。
- **阻止 REVIEW-R01 通过**：是。

### H2. Gate JSON 无生产者，关键字段无填充来源

- **问题**：行 194-213 定义了 `R01_edge_policy_droid_smoke.json` 的最小 schema，行 31 只允许"新增独立的结果汇总脚本"，但 Runbook 未定义该脚本的存在、输入或填充规则。其中 `policy.latency_ms`、`world.shape/finite`、`peak_vram_gb` 在官方产物中均无对应来源（见 H1、M2）。AGENTS.md 行 20 要求"不得用文字结论替代 JSON 产物"，当前状态下执行者无法合规地产出这份 JSON。
- **证据**：`docs/build/PSM-WMA_G0_R01_implementation_runbook_v0.1.md:31,194-213`；两个入口的产物能力见 H1。
- **最小修复**：在 Runbook 中新增一节定义汇总脚本（建议名如 `tools/g0/collect_r01_gate_json.py`）的输入（preflight 输出、benchmark.json、policy_server.log、客户端日志、vram 采样）、字段映射规则和校验方式；或显式声明该脚本属于 R01 允许的新增范围并给出接口契约。
- **阻止 REVIEW-R01 通过**：是。

## MEDIUM

### M1. Reasoner 产物路径层级不精确

- **问题**：per-sample 输出写到 `<output_dir>/<sample_name>/`，sample_name 取输入文件名 stem（`cosmos_framework/scripts/inference.py:51-52`，`common/args.py:892-896`）。Phase B 的实际产物是 `artifacts/g0/r01/reasoner/reasoner/reasoner_text.txt` 与 `.../reasoner/reasoner/sample_outputs.json`（`inference/inference.py:1947-1953`），`benchmark.json` 在 `-o` 根（`scripts/inference.py:70-73`）。行 29、124 和 §8 目录树（行 184-191）未体现 `reasoner/reasoner/` 双层结构，复跑核验时可能误判文件缺失。
- **最小修复**：§6 PASS 和 §8 目录树写明实际路径。
- **阻止**：否，但必须修正。

### M2. world rollout 只在 WebSocket 响应中返回，无落盘、无 server 侧 shape/finite 记录

- **问题**：`--decode-video` 的视频经 VAE decode 后放在响应 `outputs["video"]`（`action_policy_server_robolab.py:614-618`），server 不写盘也不记录其 shape/finite；行 176 的 PASS 判据和 Gate JSON `world` 字段的取证点完全依赖外部 RoboLab client 的日志行为（本地不可验证），§8 产物树也没有视频/其元数据的存放位置。这是"宣称验证 world pathway 但无观测点"的漏洞。
- **最小修复**：明确 world 字段的取证点（client 端从 msgpack 响应读取 `video` 并记录 shape/finite 到指定文件），在 §8 产物树中加入对应文件；若 RoboLab client 不暴露该数据，则声明为 `BLOCKED_CLIENT_ASSET` 的触发条件之一。
- **阻止**：与 H2 联动，world 字段无来源前不能机器判定。

### M3. "action_chunk_size=32 来自 checkpoint.json 和 server 默认值"机制描述错误

- **问题**：行 154。server 读取 `checkpoint.json` 后只消费 `config_file/experiment/experiment_overrides`（`action_policy_server_robolab.py:88-112`），`policy` 块从未被访问；本 checkpoint `config_file: null`，全部值回落到硬编码常量 `:65-70`（恰与 checkpoint.json 相同：32 / 15.0 / droid_lerobot）。数值正确，机制错误，换成 config_file 非空的 checkpoint 时会误导。
- **最小修复**：改为"server 硬编码默认值与 checkpoint.json 的 policy 块一致（32/15.0/droid_lerobot），本 Runbook 显式传参不依赖该巧合"。
- **阻止**：否。

## LOW

### L1. `preflight.log` 无产生步骤

- **问题**：§8 目录树（行 187）列出 `preflight.log`，但 §5 Phase A 两段命令（行 64-95）均未 tee/重定向到该文件。
- **最小修复**：Phase A 命令追加 `2>&1 | tee ../artifacts/g0/r01/preflight.log`（注意 §5.1 的 `exit "$missing"` 与管道的退出码交互，建议 `set -o pipefail`）。
- **阻止**：否。

### L2. §5.2 版本核验只打印不比对

- **问题**：行 87-102 只 `rev-parse` 打印，`BLOCKED_VERSION_DRIFT` 依赖人工对照行 7 的哈希，无自动断言。
- **最小修复**：加 `test "$(git -C cosmos-framework rev-parse HEAD)" = 103c5d1...` 形式的显式比较。
- **阻止**：否。

### L3. 治理：Runbook 未提交；根仓库 gitlink 仍指向 `5d6dedc`

- **问题**：`git status` 显示 Runbook 为 untracked，根仓库 `cbdf544` 的 `cosmos-framework` gitlink 为 `5d6dedc7bac4e8ec4d2b6fb002655bff68e5e5f0`（`git ls-tree HEAD`），工作区检出 `103c5d1` 但未提交。即"固定基线"在根仓库提交层面并不包含新子模块指针，checkout `cbdf544` 的复跑者会得到旧框架。按 AGENTS.md"每步记录对应提交哈希"，当前为 `未提交`。
- **最小修复**：DOC-R01 收尾时提交 Runbook 并更新根仓库子模块指针（属后续步骤，不属本次只读审查范围）。
- **阻止**：否，但 DOC-R01 转 DONE 前必须完成。

### L4. Gate JSON 缺 provenance 与请求级明细字段

- **问题**：schema（行 194-213）有 `repo_commit/cosmos_commit/checkpoint_path/exception/status`，但缺 torch/cuDNN 版本、`LD_LIBRARY_PATH`、seed、server 端口/分辨率等 provenance，latency 也只有单个 `latency_ms` 而无逐请求数组（行 168 要求"每次记录"）。作为"最少包含"可接受，但 R 系列 Gate 的可复现性会受损。
- **最小修复**：增加 `env`（torch/cudnn/ld_library_path）、`run_config`（seed/chunk/fps/port）、`policy.latency_ms_requests[]` 字段。
- **阻止**：否。

---

## 逐题核验结论（对应审查要求 1-9）

1. **结构完整性**：前置资产、命令、工作目录、环境变量、GPU/网络、断言、PASS/FAIL/BLOCKED、失败分流、回填字段齐全；缺"指标采集步骤"与"Gate JSON 生产者"（H1/H2）。
2. **CLI 一致性**：两条命令的全部 flag 拼写、默认值与 `103c5d1` 源码逐字一致；`--checkpoint-path` 接受本地目录（`common/args.py:577-595`）；`Cosmos3-Edge-Policy-DROID` 不在 registry，必须用本地路径——Runbook 写法正确。
3. **三路径充分性**：Reasoner 路径自足可靠；Policy 与 World 都依赖外部 RoboLab client，且 world 无独立观测点（M2）；`BLOCKED_CLIENT_ASSET` 不得降格 PASS 的规定（行 179）正确。
4. **checkpoint 适用性**：diffusers 布局被原生支持，无需 consolidated export（`inference/model.py:234-241,696-712`）；Reasoner 权重保留（`config.json:54` `exclude_reasoner_weights_from_checkpoint=false`）；需要的外部资产仅 RoboLab client，Runbook 已正确将其列为外网确认项。
5. **action 断言**：`[32,8]` 与 server 实际行为一致（模型产 33 行含 1 state 行，drop 后 `[32,8]` float32，gripper 通道取反，`action_policy_server_robolab.py:592-595`）；`history_length=1` 无历史帧需求；`domain_name=droid_lerobot`、`action_dim=8`、`conditioning-fps=15` 与 checkpoint.json 一致；模型卡 canonical `[16,8]` 与 server `[32,8]` 的区分（行 154 后半句）与 `README.md:306-352` 一致，处理得当。
6. **环境**：`/root/venvs/psm_wma` Python 3.13.13、PyTorch `2.10.0+cu130`、`torch.backends.cudnn.version()=91501`；`nvidia/cudnn/include/cudnn_version.h` 确认 cuDNN 9.15.1；`nvidia/cu13/lib` 与 `torch/lib` 均不含 `libcudnn.so.9`，Runbook 的 LD_LIBRARY_PATH 顺序（cudnn/lib 首位）正确且与 SESSION.md 已验证结论一致。
7. **产物与 Schema**：schema 含 status/blocker/exception/peak_vram_gb，但缺采集手段（H1）、缺生产者（H2）、缺请求级 latency 与 env provenance（L4）。
8. **范围与治理**：未越 R01 范围，未触碰 frozen/locked 文档，R01-R06 顺序未违反；治理瑕疵仅 L3。
9. **上游 5 提交语义影响**：**无 R01 语义变化**。`0ee5086`（DROID normalizer 修复）只改 dataset `__getitem__` 路径（`data/generator/action/datasets/`），serving 路径用 `_DummyDataset` 且不加载任何 normalizer（`action_policy_server_robolab.py:273-275,571`），二者独立；但需在 R03/R04 注意该修复改变训练数据侧归一化行为。`103c5d1`/`f525204`/`43eb9ea` 为 guardrail 修复，Runbook 用 `--no-guardrails` 规避（且 `103c5d1` 恰好修复了 reasoner Markdown 输出经 `| tee` 时被误报 blocked 的 bug，方向有利）。`a98dec0` 为 FSDP2 梯度累积修复，训练侧，与 R01 无关。

## 已核验的源码锚点清单

- `cosmos_framework/scripts/inference.py:22,47-52,70-90`（CLI、sample 子目录、benchmark.json）
- `cosmos_framework/inference/common/args.py:533,557-595,625,685,754,799,811-826,874,892-896`（全部 flag 与默认值）
- `cosmos_framework/inference/common/inference.py:134,243-260`（benchmark 产物结构）
- `cosmos_framework/scripts/action_policy_server_robolab.py:65-71,88-112,299-359,364-365,501-504,506-595,613-630`（server CLI/默认值/请求 schema/`[32,8]` 切片/decode-video）
- `cosmos_framework/data/generator/action/datasets/{cosmos3_action_lerobot.py,droid_lerobot_dataset.py}`（0ee5086 diff，dataset-only）
- `cosmos-framework/inputs/reasoner/reasoner.json`（纯文本，无媒体依赖）
- checkpoint：`checkpoint.json`（chunk 32 / fps 15.0 / droid_lerobot）、`config.json:54,87,199`、`model_index.json`、`model.safetensors.index.json`（4 个引用文件全部存在非空）、`vae/diffusion_pytorch_model.safetensors`（1.4GB）、`README.md:306-352`
- 环境：`cudnn_version.h`（9.15.1）、`torch 2.10.0+cu130 / cudnn 91501`、`jq-1.6` 可用
- Git：根 `cbdf544`、子模块 `103c5d1`、`5d6dedc..103c5d1` 恰好 5 个提交

## 已执行的只读命令及关键结果

- `git rev-parse HEAD`（两根仓库）、`git status --short`：基线哈希吻合；`M cosmos-framework`、Runbook untracked。
- `git log/show/diff 5d6dedc..103c5d1`：5 个提交，`0ee5086` 全 diff 已读，确认 dataset-only。
- `ls/cat` checkpoint 目录与 `checkpoint.json`、`config.json`、`model_index.json`；Python 解析 `model.safetensors.index.json`：4 个权重文件全部存在非空。
- `/root/venvs/psm_wma/bin/python -c "import torch..."`：版本与 cuDNN 如上（未加载 checkpoint）。
- `ls nvidia/{cu13,cudnn}/lib`、`grep cudnn_version.h`：LD_LIBRARY_PATH 顺序正确。
- 两个只读 explore 子代理：inference CLI/产物与 policy server/RoboLab 客户端逐项核验（结论已并入上文）。

## 未执行的验证及原因

- 未执行正式 inference / policy server 启动（审查范围禁止正式推理，且需 GPU 与启动前告知流程）。
- 未实际加载 checkpoint 验证 forward finite——属 G0-R01 执行阶段任务。
- RoboLab client（`policies/cosmos3/run.py` 的 `--num-envs/--headless` 与视频日志行为）本地无法验证——外部仓库 NVlabs/RoboLab，需要外网确认；已通过上游 GitHub 与模型卡交叉确认命令形式。
- `openpi-client` numpy 元数据冲突（SESSION.md 已知例外）未重新核验——与 R01 Runbook 文本无关。

## REVIEW-R01 是否满足验收条件

**不满足。** 验收条件要求"一致性、可执行性和源码锚点审查通过"。一致性（锚点）基本通过，但可执行性存在 H1/H2：按当前文本执行 R01，执行者无法合规产出 Gate JSON 中的 `peak_vram_gb`、`policy.latency_ms`、`world.shape/finite`，机器判定不可完成。

## 可逐项关闭的修复清单

1. **H1** — Phase B 增加 warmup/iteration 参数或外部计时步骤；Phase B/C 增加明确的 VRAM 采样步骤与产物路径；修订行 124、168、177、208 使判据与采集手段一一对应。
2. **H2** — 新增一节定义 Gate JSON 汇总脚本的名称、输入、字段映射与校验；明确每个 schema 字段的数据来源。
3. **M1** — §6/§8 写明 `reasoner/reasoner/` 实际产物层级与 `benchmark.json` 位置。
4. **M2** — 明确 world rollout 的客户端取证点与落盘文件，加入 §8 产物树。
5. **M3** — 修正行 154 关于 checkpoint.json 默认值来源的机制描述。
6. **L1** — Phase A 命令输出落 `preflight.log`（注意 pipefail 与退出码）。
7. **L2** — §5.2 增加提交哈希的自动比对断言。
8. **L4** — Gate JSON 增加 env/run_config/逐请求 latency 字段。
9. **L3** — DOC-R01 收尾时提交 Runbook 与根仓库子模块指针（后续步骤，本次只读审查不执行）。

修复 1-8 后可重新进入 REVIEW；修复均不改变 Runbook 的范围与 Gate 语义，可在 v0.1 的修订记录或 v0.2 中完成。

---

# 复审记录（2026-08-13，第二轮）

**复审结论：APPROVE**（附 2 条非阻塞 LOW，L3 按约定留待 DOC-R01 收尾）

Codex 修订后复审，逐项对照首轮修复清单独立核验：

| 项 | 结论 | 复审证据 |
|---|---|---|
| H1 | **CLOSED** | Phase B 新增 `--warmup 1 --num-iterations 3`（Runbook 行 135-136；flag 与约束核实于 `common/args.py:813-816,825-826`，`--benchmark` 前置已满足）；warmup 键前缀 `[warmup] ` 核实于 `common/inference.py:227-233`；Reasoner/Policy 各加 `nvidia-smi --query-compute-apps=used_memory --loop-ms=500` 采样到 `reasoner_vram.csv`/`policy_vram.csv`（行 123-126、158-161）；PASS 判据行 145、217 与采集手段一一对应。 |
| H2 | **CLOSED** | 新增 §8（行 221-234）定义 `tools/g0/collect_r01_gate_json.py` 的命令、字段映射与 FAIL/BLOCKED 规则；脚本实测：空证据下 `collect()` 返回 `BLOCKED`（`BLOCKED_MISSING_EVIDENCE/CLIENT_ASSET/MISSING_VRAM`），commit 现场读取正确，env 捕获 torch `2.10.0+cu130`/cuDNN `91501`。关键格式耦合点静态核验通过：`SampleOutputs.status` 顶层字段存在（`common/args.py:1013`），健康运行不会被误判 FAIL。 |
| M1 | **CLOSED** | 行 145 与 §9 目录树（行 244-248）写明 `reasoner/reasoner/` 双层结构与 `reasoner/benchmark.json`，与 `scripts/inference.py:51-52,70-73` 一致。 |
| M2 | **CLOSED** | §7.2 行 193-208 定义客户端证据契约：从 WebSocket 响应读取 `action`/`video`、单调时钟计时、写 `robolab_client_metrics.json`、video shape 不提前固定、无法暴露即 `BLOCKED_CLIENT_ASSET`；汇总脚本 `collect_r01_gate_json.py:86-120` 消费并校验 world shape/finite。 |
| M3 | **CLOSED** | 行 179 已改为"server 硬编码默认值与 checkpoint.json policy 块一致，显式传参不依赖该巧合"，机制描述准确。 |
| L1 | **CLOSED** | §5.1 行 65-86 `set -o pipefail` + `tee artifacts/g0/r01/preflight.log`，vae 断言并入同一日志块；§5.2 `tee -a`。 |
| L2 | **CLOSED** | 行 97-98 显式 `test ... = 103c5d1...`；汇总脚本 `EXPECTED_COSMOS_COMMIT`（`collect_r01_gate_json.py:17`）二次把关。 |
| L4 | **CLOSED** | schema 行 267-270 增加 `env`（含 torch/cudnn，超出首轮要求）、`run_config`、`latency_ms_requests[]`、warmup/steady 数组。 |
| L3 | **OPEN（按约定）** | Runbook、本报告、`tools/` 仍 untracked；根仓库 gitlink 仍 `5d6dedc`。属 DOC-R01 收尾提交动作，复审不执行。 |

## 复审新发现（非阻塞 LOW）

- **N1**：`collect_r01_gate_json.py:108-112` 把"timed 请求 < 2"折进 `policy.finite`，导致行 156 误报 `FAIL_ACTION_NONFINITE`（实际是没跑够请求，方向安全但标签误导）。最小修复：拆出独立 `FAIL_INSUFFICIENT_REQUESTS` 判据。
- **N2**：`collect_r01_gate_json.py:175-183` 的 `run_config` 硬编码 `port 8000/seed 0/num_steps 4`，与 Runbook 行 151"端口冲突时改用空闲端口并记录"冲突——改端口后 Gate JSON 会误报。最小修复：从 `policy_server.log` 解析或加 CLI 参数覆盖。
- **N3**：`tools/g0/__pycache__/` 已存在于工作区，提交前确认根 `.gitignore` 覆盖。

## 复审执行的只读/轻量验证

- 重读修订后 Runbook 全文与 `tools/g0/collect_r01_gate_json.py` 全文；`git status`/`git log`/`git diff SESSION.md TODO.md`。
- 静态核验格式耦合点：`common/args.py:997-1030`（`SampleOutputs.status`）、`common/inference.py:175-260`（warmup 计时键名与 benchmark.json 结构）、`inference.py:1914-1953`（reasoner 产物写出）。
- 轻量运行（已按 D005 告知）：直接调用 `collect()`（不走 `main()`，不写文件、不加载 checkpoint、不访问外网、仅 `nvidia-smi` 查询），空证据输出 `status=BLOCKED` 与预期 blocker 一致。

## 复审未执行的验证及原因

- 未用完整伪证据跑 `main()` 端到端 PASS 路径：需要写入临时证据文件，超出本轮授权；格式耦合的两个高风险点（status 字段、warmup 键名）已静态核实，Codex 在 SESSION.md 记录的伪证据验证（PASS/BLOCKED 断言）与静态核验结论一致。
- N1/N2 不影响 Gate 判定的正确方向，留作 G0-R01 执行前的小修或执行后回填。

## 最终结论

REVIEW-R01 验收条件**满足**：H1/H2 与 M1-M3、L1/L2/L4 共 8 项首轮问题全部关闭，汇总脚本实测可运行且 BLOCKED 语义正确。DOC-R01 可在完成 L3 提交（Runbook + 审查报告 + `tools/` + 根仓库子模块指针）后转 DONE；G0-R01 可进入认领。
