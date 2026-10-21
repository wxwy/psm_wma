# PSM-WMA V3 — iter4000 DS_PRO 独立 CPU 及只读目标机准备 Evidence Intake / Real Integration Gate

日期：2026-10-21
本 review 是**新执行前 integration-readiness/Evidence Gate**；既有 CPU-static MEDIUM-05 formal pair 未变化，不重复代码审查或重跑已审测试。
Formal implementation Root：`6405c9dae02e81be5f267e79e27995c3df7fb988`
Child/Gitlink：`2d128ed5a07601cdd424974f99b67832eafeeb41`（unchanged）
现有详细 CPU-static APPROVE：`docs/collab/chatgpt/reviews/2026-10-21_V3_iter4000_MEDIUM05_6405c9da_incremental_review.md`
审查依据：用户转交的 DS_PRO 2026-10-21 目标机报告、GitHub 精确版本 root queue、Child Action Server、OmniSetupOverrides/CheckpointOverrides/ModelLoader、SafeLocal DCP 契约。DS 原始日志位于执行机目录，当前 Remote Desktop 设备 offline，GPT **未亲自读取或执行 DS 的本机 Evidence**。

## Verdict / scope

**`REQUEST_CHANGES` — iter4000 真实 Server/Simulator Integration Gate。**
- 此 Gate 的新的 HIGH-06 是独立发现的 **Root Queue ↔ 实际 Child /info 身份协议不一致**。现有 synthetic HTTP fixture 未模拟 Child 路径归一化，不能替代真实接口契约。
- 先前 CPU-static `APPROVE` 仍是该限定 Scope 的历史记录，并不自动使 real execution Ready；本 Gate 不批准 GPU。
- DS 报告独立 CPU 测试（30 passed +41 subtests）、Ruff、four-task exact set、`/proc` stand-in、配置/端口的小文件预检均 PASS。基于报告的信息记录为 **DS attested**, 而非 GPT 读取原始本地 evidence 复验。
- DS 报告八张 GPU 全占用，**GPU_RELEASE=BLOCKED**；这本身独立禁止当前启动。

## HIGH-06 OPEN — Queue expects DCP root, Child /info reports normalized /model

- Severity: **HIGH**。
- Root `scripts/eval_robocasa_18task_queue.py:83-90,351-360,386-394`：Queue 以 `checkpoint = .../iter_000004000` 为身份 expected 值、传同路径给 server，并要求 `/info.checkpoint.resolve()==checkpoint`。
- Child `cosmos_framework/inference/args.py:1437-1445`：`OmniSetupOverrides.build_setup()` 调用 `_build_checkpoint()`。
- Child `cosmos_framework/inference/common/args.py:677-688`：若传入的 checkpoint 目录含 `model/`，则主动把 `setup_args.checkpoint_path` 规范化为 `.../iter_000004000/model`。DS 已报实际目标存在 `model/`。
- Child `cosmos_framework/scripts/action_policy_server_robocasa.py:600-638,676-690,890-913`：在 `build_setup()` 后 `self.cfg.checkpoint_dir=setup_args.checkpoint_path`；`get_info()['checkpoint']=self.cfg.checkpoint_dir`，因此必返回 `.../iter_000004000/model`，并非 Queue 所期待的父目录。
- Queue 的 `validate_server_info` 会在服务 Ready 时 `ValueError("action server checkpoint mismatch")`，零仿真启动，即使模型加载成功。原 `tools/v3/eval_robocasa_queue_identity_test.py:_info` 直接返回 input checkpoint 根路径，未模拟真实 Child 的规范化行为，造成此接口缺陷被 synthetic 通过覆盖。
- Frozen contract violated：/info checkpoint identity 必须是同一个 iter4000 Model DCP，严禁错迭代/旧 server；本实现把规范化后的**正确** Model DCP 误判为错误模型。
- **Codex acceptance**：只修改 root `scripts/eval_robocasa_18task_queue.py` 与定向 CPU 测试，严格验证 Child 报告的 canonical `(requested_checkpoint / "model").resolve()`（或与该 Child 严格等价的 DCP 规范化规则），同时保留请求时的 checkpoint 根身份、config/hash及其他 /info fail-closed、Popen listener owner；不接受任意父目录/尾缀、也不能跳过 checkpoint 检查。新测试应基于实际 Child `CheckpointOverrides._build_checkpoint` 的规范化行为或同源真实契约 fixture，证明正确 `/model` PASS、错误 iter/model 或其他任意路径 FAIL，1/2 GPU 或最小 4Task×5 CPU end-to-end 仍 PASS。不得改 Child、trainer、DCP、run optimizer或已验证锁机制。生成新 exact implementation SHA/Evidence，重新申请 **新 Pair** 增量审核。不许直接跑 GPU 修复。

## Evidence anomaly: `optim/` missing though complete marker includes it (read-only investigation required)

- DS reported: `complete.v1.json` 声明 `components.optim.metadata` (sha256 and length) but iter4000 DCP 中 `optim/` 目录不存在。
- Child `cosmos_framework/checkpoint/dcp.py:1312-1313,1401-1420,1499-1520,1590-1669`：`SafeLocalDistributedCheckpointer.COMPONENTS = ("model", "optim", "scheduler", "trainer")`；`validate_checkpoint` 会逐个确认 witness；缺 `optim/.metadata` 必然校验失败。不能把 marker 的 `complete=true` 当作完整性通过。
- **不直接推定模型推理一定失败**：在本 Child 代码中，`CheckpointOverrides._build_checkpoint` 将本地 DCP 定位到 `iter/model`，`Cosmos3OmniModel.from_pretrained_dcp` 使用 `FileSystemReader(model_dir)` 加载 model-only。单纯缺 optimizer 与模型参数加载是不同合同；但它确实是 G1 SafeLocal 训练恢复/发布完整性异常。
- **DS read-only acceptance**：精确打印 `iter4000/optim` 是否目录/symlink、`optim/.metadata` 是否存在、complete marker 的对应条目/真实 files、`SafeLocalDistributedCheckpointer.validate_checkpoint(path,world_size=8)` 非破坏性结果或等价组件见证；比较源训练目录与 target path 是否是不同镜像/拷贝，抽查相邻 DCP 仅用于溯因。保持训练和全部原 DCP 原样，不补写、删除、覆盖，也不宣称 full checkpoint 正常。按影响归属另起 G1 checkpoint integrity ticket；评测以 model-only 运行仍需真实 GPU 初次 load 验证。

## Other readiness gaps (not additional code findings)

- DS 汇报 `job_identity.h_pred=16`，但 Action Server 在 Child `_extract_chunk_length_from_config` 里从 `config.dataloader_train.chunk_length / num_action_per_chunk` 推导实际 `/info.action_chunk_size`，无此字段会 default=32；在只读环境应核对这个具体解析值=16，而非以 job identity 的 h_pred16 代替 server resolved result。
- 已有端口预检 `8900,8901` 是**过去一刻的观测**；实际运行前重检。8× GPU 全占用，0张可分配；建议后续 Owner release 空闲2张而非默认8张，只有在设备空闲时才能做真实 server /info canary，再评估 4×5 episodes。
- 保持 four-task exact set、seed0（环境）、sampler seed0、R16、Local required、raw15、state、left_wrist、fps20、完整task级resume与独立 output namespace；不得跨旧 Root 复用 digest 或把 partial SR 当 final。
- DS 原 Evidence 在本机 `/mnt/data1/data_v2_0617/dspro_verify_iter4000_6405c9da_20261021/evidence/`，当前不可被 GPT 直接读取。若需正式 Evidence Gate Closure，请通过可访问的归档或小型带hash元数据/测试日志交接；不能用聊天文字代替真正机器证据。

## Immediate handoff

**Codex**：HIGH-06 root-only 最小 Path normalized identity fix + CPU负例 → 新 formal pair、CPU证据 → GPT复审；其他代码不要扩散。
**DS_PRO**：只读定位 `optim/` mismatch + Actual config chunk resolver（不得GPU或修改DCP）；GPU/端口仍 blocked，原 30+41 CPU 无需每次重跑。
**Owner**：当前不放行真实 GPU/Server/Simulator/20 episodes。未来 GPU 空闲、HIGH-06 新Pair closed、目标机 /info/proc及模型权重首次加载合格后再单独授权。

当前只有 Integration Gate `REQUEST_CHANGES`，上一 CPU-static Gate `APPROVE` 不重复或改写。
