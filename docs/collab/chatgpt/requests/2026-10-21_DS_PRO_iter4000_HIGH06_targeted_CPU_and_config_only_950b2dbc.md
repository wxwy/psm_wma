# DS_PRO — V3 iter4000 HIGH-06 定向 CPU 复验 + 真实 Action Server Config 解析（GPU 检查取消）

日期：2026-10-21。**Owner 最新裁决**：本轮不检查 GPU 资源、不执行 `nvidia-smi`、不汇报 GPU 进程/利用率/显存、不为评测停止任何训练。Owner 将自行决定何时停止训练、释放 GPU。此裁决覆盖此前 HIGH-06/iter4000 所有 DS 指令中要求“当前 GPU 资源核验”的部分。

**Scope**：CPU-only、只读生产文件与已有 Checkpoint model-only metadata；允许外置临时合成 fixture/Evidence。不得启动 CUDA 模型、Action Server、RoboCasa 仿真、GPU preflight、训练；不得修改 Root/Child 源码、Config、DCP 或删除旧证据。

## 精确 formal implementation pair

- Root：`950b2dbc6ad112205153a18dc0f733812db30706`
- Child/Gitlink：`2d128ed5a07601cdd424974f99b67832eafeeb41`
- Queue Blob：`cb829cec0e43c09e8298e9d896a473b7b8285739`
- 最新 root `origin/V3` 文档 HEAD 不得代替 Implementation Root。独立检测 clean detached Root/Child/Gitlink、before/after status，禁止 `reset --hard`/`clean -fd`/force。遇到 SHA 不一致，报告 BLOCKED，不拿旧 `6405c9da` 或 `ca936c8e` 的工作区执行。
- GPT 正式审核：`docs/collab/chatgpt/reviews/2026-10-21_V3_iter4000_HIGH06_950b2dbc_incremental_review.md` — `APPROVE` **仅 CPU 静态整改**。本轮 DS 是独立执行验证，非重复 GPT 技术审核。

## A. HIGH-06 定向独立 CPU 复验

在 Root 工作区中，确保 Python 能从 **当前 Root、Root/scripts、Root/cosmos-framework** 加载模块，设置 `CUDA_VISIBLE_DEVICES=''`、HF/Transformers offline、外置 PYTHONPYCACHEPREFIX 和 Evidence，不能污染 Root/Child。

仅执行以下 **5 个聚焦 unittest 方法**（如选用 pytest 则保证等价收集）：

```bash
python tools/v3/eval_robocasa_queue_identity_test.py \
  ServerIdentityTests.test_real_child_checkpoint_builder_model_path_passes_exact_identity \
  ServerIdentityTests.test_effective_info_exact_fields_and_malformed_values_fail_closed \
  QueueIntegrationTests.test_four_tasks_five_episodes_complete_on_one_two_or_four_workers \
  QueueIntegrationTests.test_wrong_checkpoint_config_and_mode_stop_before_simulator \
  QueueIntegrationTests.test_same_iteration_other_job_and_unnormalized_parent_are_rejected -v

ruff check --config cosmos-framework/.ruff.toml \
  scripts/eval_robocasa_18task_queue.py tools/v3/eval_robocasa_queue_identity_test.py
ruff format --check --config cosmos-framework/.ruff.toml \
  scripts/eval_robocasa_18task_queue.py tools/v3/eval_robocasa_queue_identity_test.py
```

核验：真实固定 Child 的 `CheckpointOverrides._build_checkpoint` 源方法（由 CPU fixture 读取并执行）将 root 解析到 `/model`；正确根通过；错误迭代、相同 iteration 的其它 Job、错误父路径均 fail-closed，零 `sim_calls`；1/2/4 Worker 的 4Task×5 **合成**输出均 `COMPLETE`、20条、RC0、无残留自有线程/进程。严格区分模拟结果和真实 SR/MP4。

记录 test method/subtest 计数、所有命令和 RC、正/负 Witness、Ruff 输出、版本和完整性；失败即 BLOCKED，不绕过断言或修改代码。已关闭的早期 30+41 套件**不要整套重跑**。

## B. 真实 G1 `config.yaml` 的 Action Server 解析核验（CPU/只读）

从目标机**实际 G1 iter4000 对应的 config.yaml** 读取数据，不能把 `v3_job_identity.json:h_pred=16` 直接等同于 `action_chunk_size=16`。必须依据以下 **固定 Child 真实逻辑**：

- `cosmos_framework/scripts/action_policy_server_robocasa.py::_extract_chunk_length_from_config`；
- 扫描 `config["dataloader_train"]` 内嵌套的 `chunk_length` / `num_action_per_chunk`，按真实函数遍历及优先级取值；返回 None 时 Server fallback 默认 32；
- 记录实际命中的完整字段路径、原始值及最终 resolved `action_chunk_size`；要求等于16，否则 **BLOCKED**，只报告路径和原因，不修改配置或强加 CLI override；
- 登记真实 `CONFIG_FILE` 绝对路径、sha256，并可与已记录的 G1 `v3_job_identity` Config SHA 对照；只读输入。若 CPU Python 缺依赖或配置内容无法反序列化，明确 BLOCKED，不用人为写死16代替检验。

建议使用现有 Server Python + `cosmos_framework.inference.common.config.deserialize_config_dict` 读取 JSON/YAML 后，**读取 Child 函数源码而不是复制算法**，CPU-only 提取并执行原函数体。下面是供 DS 在已设置真实 `CONFIG_FILE`、`ROOT_WORKTREE`、`SERVER_PYTHON` 后使用的参考验证程序（不加载模型、不发 HTTP 请求）：

```bash
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 "$SERVER_PYTHON" - <<'PY'
import ast, hashlib, json, os
from pathlib import Path
from typing import Any
from omegaconf import DictConfig
from cosmos_framework.inference.common.config import deserialize_config_dict

root = Path(os.environ["ROOT_WORKTREE"]).resolve()
config_file = Path(os.environ["CONFIG_FILE"]).resolve()
child_source = root / "cosmos-framework/cosmos_framework/scripts/action_policy_server_robocasa.py"
tree = ast.parse(child_source.read_text(encoding="utf-8"))
func = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
            and n.name == "_extract_chunk_length_from_config")
ns = {"Any": Any, "DictConfig": DictConfig}
exec(compile(ast.Module(body=[func], type_ignores=[]), str(child_source), "exec"), ns)
config = deserialize_config_dict(config_file)
detected = []
def walk(obj, prefix):
    if isinstance(obj, (dict, DictConfig)):
        for key, value in obj.items():
            path = f"{prefix}.{key}"
            if key in {"chunk_length", "num_action_per_chunk"}:
                detected.append({"path": path, "value": value, "type": type(value).__name__})
            walk(value, path)
    elif isinstance(obj, (list, tuple)):
        for i, value in enumerate(obj):
            walk(value, f"{prefix}[{i}]")
walk(config.get("dataloader_train"), "dataloader_train")
resolved = ns["_extract_chunk_length_from_config"](config)
effective = resolved if resolved is not None else 32
result = {
    "config_path": str(config_file),
    "config_sha256": hashlib.sha256(config_file.read_bytes()).hexdigest(),
    "matched_fields": detected,
    "extractor_return": resolved,
    "action_chunk_size": effective,
    "verdict": "PASS" if effective == 16 else "BLOCKED",
}
print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
if effective != 16:
    raise SystemExit("BLOCKED: action_chunk_size does not resolve to 16")
PY
```

注意此静态读取不证明真实 GPU /info 已创建；真正 Server /info 仍属于**以后单独授权**的 canary。

## C. 交付与停止

输出一份简短 gate 报告，包含：

- 实际 Root、Child/Gitlink、Queue blob、工作区洁净、Python/Ruff 版本；
- HIGH-06 五项定向 CPU 方法的 PASS/BLOCKED、命令/日志/RC、错误路径 Witness；
- `config.yaml` 的真实字段路径与值、Child 解析 `action_chunk_size`、Config SHA；
- Evidence 完整路径或提交链接与文件 hash；未能读取/执行的部分如实注明；
- **无需 GPU 资源表或 GPU 检查**、不需要 Optimizer `optim/`、不查训练 Resume 完整性、不需要启动真实模型；
- 若发现问题，STOP 并反馈 GPT，不擅改生产代码。

本次按 Owner 指示只做上述两项。GPU 释放和未来真实仿真启动均由 Owner 另行决定与授权。
