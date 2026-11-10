# Issue #35 — Attention 现有 trace 与真实输入补采状态

Codex 作者诊断记录，2026-11-10 CST。**状态：`BLOCKED_REAL_INPUT_CAPTURE_NOT_GATE_PASS`。**
不是 GPT 独立审核，不申请重复审核未变的 Stage2，也不关闭 Issue #35。

## 固定实现与边界

- Formal Root：`18be4a80a5ae4d97bc7d287034d24efab847c496`。
- Child / Gitlink：`193627f42f4cd1ba6d563aefb8fa8f9428ecb56d`。
- 诊断分支：`v3-local-prefix-attention-issue35-20261109`，文档基线 `523aa26a5c2484c3547dc31db038d7eaed063dea`。本次没有修改生产代码或 Gitlink，没有新的实现 Formal Pair。
- 已读取正式 Stage2 更正报告 `docs/collab/chatgpt/reviews/2026-11-09_Issue31_Stage2_18be4a80_193627f4_PrefixPack_APPROVE_CODE_CorrectedGate.md`。限域 `APPROVE_CODE` 保持；作者原 benchmark `NOT_MET` / exit2 保留，不把内部 1.05× 当 Owner 门槛。
- No-TTT 不重跑。历史总体 mean616.26ms / 280次与 seed4603 P50736.75ms / 55次属于不同统计口径；不能混用。No-TTT 与 Local checkpoint 不同，不做同权重机制因果结论。
- 没有修改训练、VAE、TTT、Sim 调度、M/B/K/Resume 校验、模型权重或运行中的其他任务；没有恢复人工 GPU 负载，没有 V3 合并或900EP/SR评测。

## 1. 新的可复核发现：812 次源码路径不等于812次 causal GPU计算

只解析已存在的 Stage2 GPU02 profiler，**没有为此重跑模型**。原实验为真实 Local iter15000 / B1 / 30步 / 28层、固定合成输入，Text KV 两边均开启，仅 Pack OFF/ON。它不是本 Issue 要求的真实目标请求。

| 单次已归档 profile | Pack OFF | Pack ON |
|---|---:|---:|
| causal Flash SM90 kernel 次数 | 28 | 28 |
| causal kernel GPU时间之和 | 0.286817ms | 0.277605ms |
| GEN/noncausal Flash SM90 kernel 次数 | 840 | 840 |
| GEN kernel GPU时间之和 | 12.046020ms | 11.958062ms |
| Varlen prepare kernel 次数 | 868 | 868 |
| Varlen prepare GPU时间之和 | 2.876468ms | 2.771284ms |
| 含 Flash 名称的融合前后处理 kernel 次数 | 1736 | 1736 |
| 这些融合 kernel GPU时间之和 | 3.574335ms | 3.558014ms |
| 全部 kernel 次数（不含 memcpy/memset） | 34869 | 34612 |
| 全部 kernel GPU时间之和 | 154.652024ms | 153.509342ms |
| `flash_attn_3::_flash_attn_forward` CPU inclusive | 144.435793ms / 868次 | 141.351444ms / 868次 |
| 嵌套 `flash_attn_3::fwd` CPU inclusive | 80.109400ms / 868次 | 78.619611ms / 868次 |

CPU 两行有嵌套，**不能相加**；CPU、GPU有重叠，也不能相加成阻塞时延。GPU work sum 和 timeline union 均单独保存在派生 JSON 中。融合 kernel 同时包含必要工作，不能全部当作可删除开销；这些 CPU 数字也不是 dummy UND 或 metadata 的独占 self time。

868次与 `28次首次causal + 840次GEN` 一致；840=`28×30`，后续命中路径为812=`28×29`。源码仍构造 dummy UND 并调用 two-way dispatch，但本 profile 中并没有再出现812个 causal GPU kernel。`get_gen_seq()` 只取字典的 `full_only_seq`，与编译器消去未使用 causal 输出的解释一致。**未逐 hit 检查编译器 IR，不将此推广为所有 shape/backend 的保证。**

因此当前不能以源码路径次数估算浪费毫秒，不能承诺删除 dummy causal 就能缩小真实 No-TTT 差距。Varlen 的 GPU计算和 CPU 调用开销仍值得调查，但没有据此提交 Attention 生产补丁。

原始 trace SHA256：

- Pack OFF `profile_baseline.json`：`49c633835e923e09a17f6c0a0d6fea339d3389da34a8227c1ef125110222f8e3`，87678366 bytes。
- Pack ON `profile_optimized.json`：`abbf14ce5144f035ac9b988bfdc6662fd70704970f13ef376e531b2b5f98bad5`，81583325 bytes。
- 原 `kernel_counts.json`：`49339a3992d9dbcf27f851b23efafe2173e843aea6dc5c32d3b0fa2c807e96a2`。
- 新的服务器派生 `trace_reduction.json`：`05c0d0e923c61a670c9882d2d9b7caad0f7029decac258f0e1101e5ee9522b34`。

Reducer exit0；前后重新哈希原 trace 未变，分类次数与原 kernel_counts 交叉检查一致。单次 instrumented profile 不是稳态延迟分布，也不是新的加速验收。

## 2. 真实完整输入仍未取得，动作差异保持未定因

现有真实记录的目标仍为 K1 replan2/source_step32 与 K16 replan4/source_step64；旧/新 raw15 max_abs分别0.0049707889556884766、0.007069587707519531。已读目标 `predictions.jsonl` 的结构：有 Action、RGB/Visual摘要及FW范数/inner-loss标量；`raw_trace` 只有12个事件及计时元数据。原始运行目录未找到保存的 PT/NPY/NPZ/safetensors完整请求。**这些记录不能还原完整 FastState/Prefix、全部输入、噪声和 RNG。**

已准备外部、显式 opt-in 录制工具：原生 `torch.save` 保存完整请求、previous/candidate FastRecord、Prefix、CPU/CUDA/NumPy/Python RNG，记录原生 `_prepare_inference_data` 返回值和输出动作。保留张量 stride/storage_offset/alias，避免 `.cpu().clone()` 改变布局。没有改生成开关、精度、编译上限、权重或原生身份检查。

只尝试一次短补采 `capture01`：使用原配置 K1/seed4603/Policy GPU6/Sim+VAE GPU4，配置只改 output_dir/base_port，计划到source_step32后仅向自己的协调器发送SIGINT，由原生Runtime清理；K16计划到64。实际 K1 在渲染初始化前停止，未取得请求，K16没有启动：

```text
RuntimeError: selected physical render GPU must have one provable EGL device
cosmos_framework/simulation/robocasa/render_devices.py:267
```

独立原生 EGL 检查同样失败。EGL可枚举8个device，但没有返回DRM PCI或CUDA handle。用纯ctypes、`python -S` 检查，CUDA可见性为空/未设置两种情况都返回DRM节点null / EGL_BAD_PARAMETER(0x300c)，因此不是仅由Torch导入或Python录制钩子导致。

现场还确认：`/dev/dri/renderD132` 存在，sysfs对应期望 `0000:98:00.0`；mode0660/gid993，当前远程执行身份uid1004仅在group1004中，`os.access`读/写均false。**这与无法取得原生物理证明构成当前环境阻塞；尚未证明节点权限是接口失败的唯一原因。** 没有chmod、改组、提权运行或伪造PCI/EGL索引，没有关闭身份校验。需要可访问该节点且原生EGL证明通过的已有授权执行环境，或已有完整冻结输入，才能继续。

三个owned进程（Policy、共享VAE、Sim Actor）的关闭回执与对应原始注册记录相同；cleanup.live_group均false，当前对应进程组均为空。GPU4与GPU6在最终核验时均0MiB/0%利用率。没有有效Episode或SR结果。

初版诊断结果把 `intentional_early_stop=true` 写成固定值，实际没有等到capture_ready，不能称为成功后的主动停止。原结果不改写，`diagnostic_status01/02`明确更正；01中的 `no_ttt_rerun=false` 字段名称也有歧义，02明确用 `no_ttt_executed=false`。这些都是诊断元数据更正，不是生产异常或成功证据。

## 3. 诊断工具验证与限制

- 本地 CPU snapshot 初检3/3PASS；增加原生 `_Record` / `ContinualTTTFastState` / Prefix后4/4PASS，0失败/错误/跳过，Shell0。覆盖BF16/FP32、非连续view/expand/scalar、共享存储、原生GenerationDataClean/SequencePlan/ActionProcessingRecord，以及保存操作不改变RNG。不是完整CPU Gate或真实GPU回放。
- 发现原生 `launch_environment` 会把Child放到PYTHONPATH首位，遮蔽外部 `sitecustomize.py`。诊断入口现仅恢复probe优先级，其他原生启动环境字段逐项相等；先按SHA验证并串行执行服务器已有startup helper，再挂显式Policy构造器记录器。不修改原helper或生产源码。
- `bootstrap02`调用原生CLI/Policy `--help`均exit0，hook_loaded=true、class_instrumented=true、model_initialized=false；没有加载模型或创建环境。原startup helper SHA为 `b80f9d0a2f876a4a66bd02dcc097ba7a7efb1ac46321a0cecb4fbffee3dbdf74`。
- 录制钩子尚未在真实请求中验证。修正后未盲目启动capture02。CPU serialization和帮助命令成功不等于真实采集成功。
- 当前probe的Ruff检查通过，原初静态问题记录保留。`probe_before_format/`保留CPU/启动检查执行时的自有诊断代码；格式整理的AST对比在 `formatting_equivalence.json`。capture_driver仅另作lambda→def，egl_probe仅拆分复合import；实际模型相关snapshot/hook/bootstrap/reducer AST一致。
- 初次补采之前的第一版外部钩子没有冻结完整版本索引，不能用当前工具哈希冒充该次执行版本。补采无模型请求，生产Root/Child身份与原始失败记录仍可独立核验。

## 4. 证据、复现与下一步

公共证据目录：`docs/collab/codex/evidence/2026-11-10_issue35_attention/`。只包含Codex自写诊断代码、本地CPU原始JUnit/日志、派生统计和哈希；**没有导出服务器原始配置、图像、checkpoint、张量或原始profiler/运行日志文件**。

服务器私有证据：`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_codex_issue35_attention_20261109/`。保留capture01、bootstrap02、EGL探针、原始状态更正和不可覆盖的索引。75文件的 `server_artifact_index02.json` SHA256为 `4c9eac160fc6f27d210ef2560347c557b518fccbb1c4bf2c34d262ee3aaf8e29`，原始文件不外传。现场Root/Child/Gitlink前后相同，两个工作树tracked状态干净。

只读trace复现命令（选择未存在的输出文件名）：

```bash
cd /mnt/data/shenzhen/szrobot/logs/.tmp_backup/_codex_issue35_attention_20261109
/usr/bin/python3 -S reduce_existing_trace.py \
  --input-dir ../_codex_issue31_prefix_pack_20261109/gpu02 \
  --output trace_reduction_fresh.json
```

下一步仍是取得完整真实输入后，在同一Local权重、同一噪声/时间步/状态/Prefix下分别回放旧路径、Stage1、Stage2，找出首次逐张量差异；并在该真实请求上补齐CPU独占开销与GPU分段证据。只有证据显示必要性才改生产代码、提交新Formal Pair。**当前既未证明旧/新真实动作等价，也未证明缓存存在生产缺陷；不追加Attention优化，不重跑No-TTT，不要求重复审核旧Pair。**
