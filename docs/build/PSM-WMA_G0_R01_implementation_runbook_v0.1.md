# PSM-WMA G0-R01 实现与执行 Runbook v0.1

- **状态**：Approved
- **日期**：2026-08-13
- **上游**：`PSM-WMA_G0_runtime_execution_plan_v0.6_aligned.md`
- **目标 checkpoint**：`nvidia/Cosmos3-Edge-Policy-DROID`
**固定框架提交**：`cosmos-framework@103c5d1687d290b050e4890f48ff7a38b12742ef`

## 1. 范围

R01 只验证官方 checkpoint 的原生能力和运行成本，不修改 PSM、LIBERO、Agent 或 Cosmos 核心代码：

1. checkpoint 文件完整；
2. Reasoner pathway 可生成有限文本；
3. DROID Policy pathway 可返回有限的 `[H,8]` action；
4. shared Generator/world rollout 可生成有限输出，或由 policy 请求明确走过 Vision/Action shared Generator；
5. 记录 GPU、VRAM、warmup/steady latency 和运行配置。

R01 不验证 LIBERO 适配、训练、closed-loop SR 或 Memory。云端容器未挂载 GPU时状态为 `BLOCKED_NO_GPU`，不是 `FAIL`。

## 2. 复用入口

| 能力 | 入口 | 说明 |
|---|---|---|
| 通用推理 | `cosmos_framework.scripts.inference` | Reasoner 与通用 Generator smoke |
| DROID Policy server | `cosmos_framework.scripts.action_policy_server_robolab` | 官方 WebSocket Policy 路径 |
| DROID Policy client | RoboLab `policies/cosmos3/run.py` | 官方模型卡指定客户端 |
| Reasoner 输入 | `inputs/reasoner/reasoner.json` | 纯文本，不依赖外部媒体 |
| 推理产物 | `reasoner_text.txt`、`sample_outputs.json`、`benchmark.json` | 由官方推理路径生成 |

本 Gate 不修改模型逻辑。独立汇总脚本 `tools/g0/collect_r01_gate_json.py` 只读取 runtime 证据并生成 Gate JSON。

## 3. 前置资产

```text
仓库根目录       /gemini/code/psm_wma
框架根目录       /gemini/code/psm_wma/cosmos-framework
checkpoint       /gemini/code/models/Cosmos3-Edge-Policy-DROID
Python 环境       /root/venvs/psm_wma
Gate 产物目录    /gemini/code/psm_wma/artifacts/g0/r01
```

运行容器要求：

- Linux + NVIDIA GPU，Ampere 或更新架构；
- CUDA >= 12.8；
- Python >= 3.10；
- 使用已安装的 `/root/venvs/psm_wma`；
- 启动 Python 前设置本环境已验证的 CUDA/PyTorch 动态库路径；
- Policy closed-loop 需要 RoboLab 客户端资产和可访问的 WebSocket 端口。

依赖安装、RoboLab 下载和任何外网访问必须单独取得用户确认，不属于本 Runbook 的自动步骤。

## 4. 启动前告知模板

每次运行前向用户明确展示：目的、完整命令、工作目录、环境变量、GPU/外网需求、输入、产物和 PASS/FAIL/BLOCKED 判据。不得只回复“开始跑 R01”。

## 5. Phase A：CPU 预检

### 5.1 Checkpoint 索引完整性

工作目录：`/gemini/code/psm_wma`。不加载模型、不使用 GPU、不访问外网。

```bash
set -o pipefail
mkdir -p artifacts/g0/r01
checkpoint=/gemini/code/models/Cosmos3-Edge-Policy-DROID
missing=0
{
  while IFS= read -r file; do
    if [[ ! -s "$checkpoint/$file" ]]; then
      printf 'MISSING_OR_EMPTY %s\n' "$file"
      missing=1
    else
      printf 'OK %s %s bytes\n' "$file" "$(stat -c %s "$checkpoint/$file")"
    fi
  done < <(
    jq -r '.weight_map | to_entries[].value' \
      "$checkpoint/model.safetensors.index.json" | sort -u
  )
  test -s "$checkpoint/vae/diffusion_pytorch_model.safetensors" || {
    printf 'MISSING_OR_EMPTY vae/diffusion_pytorch_model.safetensors\n'
    missing=1
  }
  exit "$missing"
} 2>&1 | tee artifacts/g0/r01/preflight.log
```

断言：索引引用文件全部存在且非空；`vae/diffusion_pytorch_model.safetensors` 额外存在且非空。

当前记录：2026-08-12 已执行，PASS。正式 R01 复跑时仍需再次执行，防止资产被替换。

### 5.2 版本与 GPU 容器核验

```bash
cd /gemini/code/psm_wma
test "$(git -C cosmos-framework rev-parse HEAD)" = \
  103c5d1687d290b050e4890f48ff7a38b12742ef
git rev-parse HEAD | tee -a artifacts/g0/r01/preflight.log
git -C cosmos-framework rev-parse HEAD | tee -a artifacts/g0/r01/preflight.log
uv --version
test -x /root/venvs/psm_wma/bin/python
nvidia-smi --query-gpu=index,name,memory.total,driver_version \
  --format=csv,noheader | tee -a artifacts/g0/r01/preflight.log
```

判据：

- 子模块提交不等于固定提交：`BLOCKED_VERSION_DRIFT`；
- `/root/venvs/psm_wma/bin/python` 不存在：`BLOCKED_ENV_NOT_READY`；
- 云端未分配 GPU：`BLOCKED_NO_GPU`；
- GPU 已挂载但 CUDA/PyTorch 不可用：`FAIL_ENV`。

## 6. Phase B：Reasoner Smoke

工作目录：`/gemini/code/psm_wma/cosmos-framework`。需要 GPU；本地 checkpoint 和纯文本输入不要求外网。使用 `--no-guardrails` 防止额外下载 guardrail 模型。

```bash
cd /gemini/code/psm_wma/cosmos-framework
source /root/venvs/psm_wma/bin/activate
export LD_LIBRARY_PATH=/root/venvs/psm_wma/lib/python3.13/site-packages/nvidia/cudnn/lib:/root/venvs/psm_wma/lib/python3.13/site-packages/torch/lib:/root/venvs/psm_wma/lib/python3.13/site-packages/nvidia/cu13/lib:/usr/lib/x86_64-linux-gnu
mkdir -p ../artifacts/g0/r01/reasoner
nvidia-smi --query-compute-apps=used_memory --format=csv,noheader,nounits \
  --loop-ms=500 > ../artifacts/g0/r01/reasoner_vram.csv &
vram_sampler_pid=$!
trap 'kill "$vram_sampler_pid" 2>/dev/null || true' EXIT

python -m cosmos_framework.scripts.inference \
  --parallelism-preset=latency \
  -i inputs/reasoner/reasoner.json \
  -o ../artifacts/g0/r01/reasoner \
  --checkpoint-path /gemini/code/models/Cosmos3-Edge-Policy-DROID \
  --seed=0 \
  --benchmark \
  --warmup 1 \
  --num-iterations 3 \
  --no-guardrails 2>&1 | tee ../artifacts/g0/r01/reasoner.log
reasoner_status=${PIPESTATUS[0]}
kill "$vram_sampler_pid" 2>/dev/null || true
wait "$vram_sampler_pid" 2>/dev/null || true
trap - EXIT
exit "$reasoner_status"
```

PASS：进程退出码 0；生成非空 `reasoner/reasoner/reasoner_text.txt`；`reasoner/reasoner/sample_outputs.json` 状态成功；文本中无 NaN/Inf；`reasoner/benchmark.json` 含 warmup 与 3 次 measured timing；`reasoner_vram.csv` 含数值。

## 7. Phase C：DROID Policy / World Smoke

### 7.1 启动官方 Policy server

工作目录：`/gemini/code/psm_wma/cosmos-framework`。需要 GPU；本地 checkpoint 不要求外网。端口 `8000` 只作为当前默认值，冲突时显式改用空闲端口并记录。

```bash
cd /gemini/code/psm_wma/cosmos-framework
source /root/venvs/psm_wma/bin/activate
export LD_LIBRARY_PATH=/root/venvs/psm_wma/lib/python3.13/site-packages/nvidia/cudnn/lib:/root/venvs/psm_wma/lib/python3.13/site-packages/torch/lib:/root/venvs/psm_wma/lib/python3.13/site-packages/nvidia/cu13/lib:/usr/lib/x86_64-linux-gnu
mkdir -p ../artifacts/g0/r01/policy_server
nvidia-smi --query-compute-apps=used_memory --format=csv,noheader,nounits \
  --loop-ms=500 > ../artifacts/g0/r01/policy_vram.csv &
vram_sampler_pid=$!
trap 'kill "$vram_sampler_pid" 2>/dev/null || true' EXIT

python -m cosmos_framework.scripts.action_policy_server_robolab \
  --checkpoint-path /gemini/code/models/Cosmos3-Edge-Policy-DROID \
  --host 0.0.0.0 \
  --port 8000 \
  --domain-name droid_lerobot \
  --action-chunk-size 32 \
  --action-dim 8 \
  --conditioning-fps 15 \
  --format-prompt-as-json True \
  --seed 0 \
  --deterministic-seed \
  --decode-video \
  --output-dir ../artifacts/g0/r01/policy_server \
  2>&1 | tee ../artifacts/g0/r01/policy_server.log
```

server 硬编码默认值与当前 checkpoint `checkpoint.json` 的 policy 块一致（chunk 32、fps 15.0、domain `droid_lerobot`）；本 Runbook 显式传参，不依赖该巧合。Runtime 必须区分模型卡 canonical `[16,8]` benchmark 与当前 server `[32,8]` 配置，禁止混报 latency。

### 7.2 RoboLab client 请求

此命令在已准备好的 RoboLab 客户端容器中执行，会连接 Policy server。RoboLab 资产获取属于外网操作，必须事先确认。

```bash
cd "$ROBOLAB_ROOT"
python policies/cosmos3/run.py \
  --task BananaInBowlTask \
  --num-envs 1 \
  --headless 2>&1 | tee /gemini/code/psm_wma/artifacts/g0/r01/robolab_client.log
```

至少执行一次 warmup 和两次 timed request。客户端必须从 WebSocket 响应读取 `action` 和 `video`，用单调时钟包围每次请求，并写入 `/gemini/code/psm_wma/artifacts/g0/r01/robolab_client_metrics.json`：

```json
{
  "requests": [
    {
      "warmup": true,
      "latency_ms": 0.0,
      "action": {"shape": [32, 8], "finite": true},
      "video": {"shape": [33, 480, 640, 3], "finite": true}
    }
  ]
}
```

`video.shape` 以实际响应为准，不提前固定；必须非空、末维为 3 且全部 finite。如 RoboLab 客户端不暴露响应数组或无法写出该文件，则为 `BLOCKED_CLIENT_ASSET`。

PASS：

- server 成功加载 checkpoint；
- client 至少完成一个请求；
- action 为 `[32,8]`，全部 finite；
- `domain_name=droid_lerobot`、`action_dim=8` 与运行日志一致；
- `--decode-video` 返回的 world rollout 非空且 finite；
- warmup 和 steady latency、peak VRAM 有数值记录。

若 server 能生成 action 但 RoboLab 环境未准备好，状态为 `BLOCKED_CLIENT_ASSET`，不能宣称 Policy PASS。

## 8. Gate JSON 汇总

官方入口不直接生成 Gate JSON。在根仓库执行下列独立汇总命令：

```bash
cd /gemini/code/psm_wma
export LD_LIBRARY_PATH=/root/venvs/psm_wma/lib/python3.13/site-packages/nvidia/cudnn/lib:/root/venvs/psm_wma/lib/python3.13/site-packages/torch/lib:/root/venvs/psm_wma/lib/python3.13/site-packages/nvidia/cu13/lib:/usr/lib/x86_64-linux-gnu
/root/venvs/psm_wma/bin/python tools/g0/collect_r01_gate_json.py \
  --checkpoint /gemini/code/models/Cosmos3-Edge-Policy-DROID \
  --evidence-dir artifacts/g0/r01 \
  --port 8000 \
  --seed 0 \
  --num-steps 4 \
  --output artifacts/g0/r01/R01_edge_policy_droid_smoke.json
```

字段映射：Reasoner latency 来自 `reasoner/benchmark.json`；Policy latency/action/world 来自 `robolab_client_metrics.json`；peak VRAM 取两个 `*_vram.csv` 最大值；checkpoint 完整性来自 `preflight.log`；commit 由脚本现场读取。`--port/--seed/--num-steps` 必须与 Policy server 实际启动参数一致，端口变更时同步修改汇总命令。缺少必需证据时生成 `BLOCKED`，请求数不足、shape/finite 或 Reasoner timing 异常时生成 `FAIL`。

## 9. 统一产物

```text
artifacts/g0/r01/
├── R01_edge_policy_droid_smoke.json
├── preflight.log
├── reasoner.log
├── reasoner_vram.csv
├── reasoner/
│   ├── benchmark.json
│   └── reasoner/
│       ├── reasoner_text.txt
│       └── sample_outputs.json
├── policy_server.log
├── policy_server/
├── policy_vram.csv
├── robolab_client.log
└── robolab_client_metrics.json
```

Gate JSON 最少包含：

```json
{
  "gate": "G0-R01",
  "repo_commit": "",
  "cosmos_commit": "",
  "checkpoint_path": "",
  "checkpoint_index_complete": false,
  "gpu": [],
  "dtype": "bfloat16",
  "env": {"python": "", "ld_library_path": ""},
  "run_config": {"seed": 0, "port": 8000, "domain_name": "droid_lerobot", "action_chunk_size": 32, "action_dim": 8, "conditioning_fps": 15.0, "num_steps": 4},
  "reasoner": {"finite": false, "warmup_latency_ms": [], "steady_latency_ms": []},
  "policy": {"shape": null, "finite": false, "latency_ms_requests": [], "num_timed_requests": 0},
  "world": {"shape": null, "finite": false},
  "peak_vram_gb": null,
  "status": "PASS|FAIL|BLOCKED",
  "blocker": null,
  "exception": null
}
```

## 10. Gate 判定

`PASS` 必须同时满足 checkpoint、Reasoner、Policy 和 shared Generator/world 四项；任何 NaN/Inf、shape/domain 不符、模型加载异常或请求执行异常为 `FAIL`。缺 GPU、环境、端口或客户端资产为 `BLOCKED`，必须写明 blocker，不得降格为 PASS。

R01 PASS 后才能进入 R02/R03。R01 不提交训练 checkpoint，也不修改 `cosmos-framework`。

## 11. 回填字段

完成后回填 Detailed Design：GPU 型号、peak VRAM、Reasoner warmup/steady latency、Policy action chunk/采样步数、Policy latency、world rollout 是否实际 decode、checkpoint 与框架提交、所有 runtime drift。
