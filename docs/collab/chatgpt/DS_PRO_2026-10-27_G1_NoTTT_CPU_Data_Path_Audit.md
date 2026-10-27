# DS_PRO — V3 G1 vs No-TTT 数据处理异常耗时专项审计

- **日期**: 2026-10-27
- **角色**: ds_pro（只读审计；不改生产代码、不停训练、无高负载实验）
- **正式 Root**: `49df7f3c`（任务指定；live HEAD `b8ee0403` 为其文档提交后代）
- **正式 Child / Gitlink**: `746c5cf`（`746c5cf2f2324104a62fb71510343aa40d3976c5`，工作树干净；本报告全部代码结论均基于该 SHA）
- **执行边界**: 只读文件/日志/tmux pane；CPU-only 微基准（单进程、秒级、低负载）；未触碰 GPU、未改任何生产代码、未停训练。

---

## 0. 结论先行

No-TTT 的 ~22.5s 数据准备关键路径 = **`source_read` 4.78s（loader.begin，data_prepare 计时外）+ `transform` 16.72s（materialize，data_prepare 计时内）**。而 G1 整个 GA window 的 data_prepare（读+transform 全含）只有 **4.57s / 250 consumers = 18.3ms/consumer**。

**根因（有证据链）**：per-consumer transform 的成本被 `reflection_pad_to_target` 的 **reflect-pad（视频占位符 6.7MB → 20.4MB）** 主导，而该 pad 对 torch 线程数极度敏感：

| torch 线程数（本机实测） | 1 | 4 | 8 | 16 | 32 | 96 |
| --- | --- | --- | --- | --- | --- | --- |
| reflect-pad 单次 median | **40.7ms** | 20.5ms | 13.8ms | 10.4ms | **9.3ms** | 10.7ms |

- **No-TTT 主进程 torch 以 1 线程运行**：`/proc/<rank>/environ` 含 `OMP_NUM_THREADS=1`，torch 2.10 实测 `get_num_threads()==1`；代码中没有任何地方给主进程覆盖（`no_ttt_cpu_loader.py:59` 的 `torch.set_num_threads(1)` 只在 worker `_worker_init` 内，正确）。→ transform ≈ 34ms/consumer（与 1 线程 40.7ms 同量级）。
- **G1 主进程 torch 多线程**：G1 tmux 会话环境无 `OMP_NUM_THREADS`，torch 默认 96 线程 → pad ≈ 10ms + 读 ~8ms ≈ 18.3ms/consumer（与 G1 实测吻合）。

**最值得优先修复（二选一，按收益排序）**：

1. **【代码级，收益最大】消除“常量零视频”的逐 consumer 冗余 pad**（详见 §7）。视频占位符 `cached_pixel_placeholder(compact=False)` 恒为 `torch.zeros((3,17,256,512))`（worker 端还强制校验 `count_nonzero==0`），pad 输出恒为 `torch.zeros((3,17,480,832))`——**492 次/step 计算完全相同的常量张量**。直接把占位符在 canvas 尺寸 `(3,17,480,832)` 上分配（或缓存一次 pad 结果），VideoResize 会因 `orig==target` 完全跳过 resize 与 pad。预计 transform 16.72s → <1s，关键路径 ~~21.5s → **~~6-7s**。
   - 涉及位置：`cached_pixel_geometry.py::cached_pixel_placeholder`、`transforms.py:210-218`（reflect-pad）、`no_ttt_cpu_loader.py:476`。
2. **【环境级，零代码风险，收益次之】去掉 No-TTT 训练进程的 `OMP_NUM_THREADS=1`（或设为 ~8-16）**。8 个 worker 已在 `_worker_init` 自行设 1 线程、不受影响。预计 transform 16.72s → ~~6-7s，关键路径 → **~~10-12s**。注意不要放任默认 96 线程（4 rank×96=384 线程会竞争，实测 96 线程整链路反而更慢）。

> 
> 附带的**正确性观察**（非本审计结论，但直接相关）：两 run 训练喂给模型的 pixel video 均为全零占位符（`compact_cached_video=false`）。这使上述冗余 pad 完全成立；若设计意图是“pixel 恒零、仅 latent 承载视觉”，则冗余 pad 可安全消除；若意图是真实像素，则属另一层面的配置/实现问题，需 owner 裁决。

---

## 1. 任务 A — 运行配置核对

两 run 均在同一主机 `data`（/mnt/data 与 /mnt/data1 为本机双 NVMe），8×H100。

| 项 | G1 (`packed128_droid_fresh_g1_20261019`) | No-TTT (`no_ttt_packed128_droid_fresh_30k_world4_ga4`) |
| --- | --- | --- |
| 运行窗口 | 2026-10-19 ~ 10-26（iter 1-27705，已结束） | 2026-10-26 ~ 至今（iter ~1816+） |
| world_size / GPU | 8 / GPU0-7 | 4 / GPU4-7 |
| b_stream / t / ga | 8 / 16 / 2 | 8 / 16 / 4 |
| num_workers 历史 | {0: 27822, 4: 8, 16: 5}（≈99.9% 为 nw0） | 0（主进程 loader；另有 8 个 No-TTT CPU spawn worker） |
| full_segment_prefetch | False（末 1005 iter 全 False） | n/a（No-TTT 专用 loader） |
| compact_cached_video | **False** | **False** |
| rank_shared_episode_reader | False | False |
| 分辨率 / 相机 | 480 / left_wrist | 480 / left_wrist |
| transform 配置 | append_* 全开、format_prompt_as_json=True、max_action_dim=64 | 同左（逐项一致） |
| chunk_length | 32（被 `synchronize_legacy_chunk_length` 归一化为 16） | 16 |
| 训练进程 OMP_NUM_THREADS | 未设置（torch 默认 96 线程） | **=1**（torch 1 线程） |

config 语义差异仅 7 处（chunk_length、job.name、local_memory_enabled、data_parallel_shard_degree、optimizer.keys_to_select、grad_accum_iter、trainer.type），**无任何 transform/分辨率/占位符差异**。

---

## 2. 任务 B — 数据路径逐函数对比

### No-TTT（`matched_no_ttt.py` + `no_ttt_cpu_loader.py`）

- GA0（`matched_no_ttt.py:265-268`，**data_prepare 计时外**）：`window.begin()` + `loader.begin(plan)`
  - `_begin`（`no_ttt_cpu_loader.py:401-436`）：对 4 member × 8 request 逐个 `producer.prepare(request, raw_getter=source_reader.read_at)`（mmap 读 episode）→ `_cpu_tree(snapshots, clone=True)` 深拷贝 → pickle 打包发给 8 worker。**`source_read_ms`=4.78s**。
  - 8 worker（`RawDataset.__getitem__`，`_worker_init` 设 1 线程）：`recipe.read` 用 mmap reader 重建窗口、`compact_cached_video=True` 只传形状元数据（`_mp_zero_video` 标记）、`torch.save` 打包返回。`worker_prepare_ms_sum`=2.79s（并行重叠）。
- 每个 GA member（`matched_no_ttt.py:269-274`，**data_prepare 计时内**）：`loader.materialize(request)`
  - `_materialize`（`no_ttt_cpu_loader.py:445-497`）：`next(iterator)` 取包（raw_wait 0.26s）→ `torch.load` 解包（decode 0.59s）→ **`row["video"] = cached_pixel_placeholder(compact=False)`（6.7MB 零张量）** → `prepare(request, raw_getter=rows.__getitem__)` → 每 consumer `wrapped._transform(...)`（**`transform_host_ms`=16.72s**）→ `producer.materialize(prepared)`。

### G1（nw0 主路径，`local_memory_grouped.py`）

- 每个 GA member（`local_memory_grouped.py:330-350`，**data_prepare 计时内**）：`segments = tuple(produce(request) for request in requests)`
  - `ExactWindowSegmentProducer.produce` = `materialize(prepare(request))`（`robocasa_exact_window_local.py:445-446`）
  - `prepare`（:323-354）：`raw.__getitem__` 读 17 个 raw item（含 source + cache latent + 身份校验 + 占位符分配）
  - `materialize`（:356-443）：每 consumer `wrapped_sft._transform(dict(item), resolution)`（:410-412）
- G1 的 nw8 分支（仅 13 iter）走 `robocasa_async_segment_prefetch` + `ordered_prefetch`，非主体，不展开。

### 操作对比表

| 操作 | G1 执行位置 | No-TTT 执行位置 | 重复？ | 能否并行/重叠 |
| --- | --- | --- | --- | --- |
| mmap 读 episode / 重建窗口 | `prepare()`，nw0 主进程同步，data_prepare 内 | worker `recipe.read`（8 进程并行），与主进程 source_read 重叠 | 无 | 已并行（worker） |
| source 打包/传 worker | n/a（无 worker） | `_begin` 深拷贝+pickle（4.78s 内） | 无 | 固定串行 |
| video 占位符分配（6.7MB 零） | `__getitem__` 每 item | `_materialize` 每 consumer（:476） | **每次重复** | 可消除 |
| VideoResize（reflect-pad 到 20.4MB） | 每 consumer，`_transform` | 每 consumer，`_transform` | **完全相同、逐 consumer 重复** | **可消除（常量零视频）** |
| 文本 tokenize / action / seq_plan | 每 consumer | 每 consumer | 无（非冗余，但占比极小，见 §4） | 单线程受限 |
| segment 组装 | `materialize` | `materialize` | 无 | — |

---

## 3. 任务 C — 统一计时口径

### No-TTT cpu_loader 分项（136 条完整对象，iter 1777-1816，rank 中位数）

| 分项 | median | 备注 |
| --- | --- | --- |
| source_read_ms | **4.78s** | `_begin` 内，data_prepare **外** |
| worker_prepare_ms_sum | 2.79s | 8 worker 并行，与 source_read 重叠 |
| raw_wait_host_ms | 0.26s |  |
| decode_host_ms | 0.59s | torch.load |
| transform_host_ms | **16.72s** | materialize 内，data_prepare 内 |
| materialize_host_ms_including_transform | 16.86s | ≈ transform |
| collate_host_ms | 0.03s |  |
| step_window_host_wall_ms | 32.67s |  |

**关键路径 = 4.78 + 16.72 ≈ 21.5s ≈ 任务描述的 ~22.5s** ✓（source_read 与 transform 串行）。

### 统一 ms/Consumer（per rank）

| 口径 | G1（末 1000 iter median） | No-TTT（iter>1760 median） |
| --- | --- | --- |
| consumers / window | 250 | 497 |
| data_prepare（含 transform） | **4.57s** | 17.6s |
| **per-consumer data_prepare** | **18.3ms** | 35.4ms |
| transform 单独 per-consumer | ~12ms（推断，pad 10ms+其余） | **33.6ms**（实测 16.72s/497） |
| 完整数据路径 per-consumer | ~18.3ms | **43.3ms**（(4.78+16.72)/497） |
| valid_consumers_per_second_rank_local | 24.0/s | 15.3/s |

两 run 同机同代码，per-consumer transform 差 ~2.3x。

---

## 4. 任务 D — 17s Transform 分析（根因）

### 4.1 单 consumer transform 的构成（实测，精确复刻生产 pipeline：ActionTransformPipeline + 真实 tokenizer `Cosmos3-Edge-Policy-DROID`）

| 组件 | 成本（32 线程） | 说明 |
| --- | --- | --- |
| `video_resize`（reflect-pad，无 resize） | 9.03ms | 输入 256×512 竖图 → res480 目标 16:9 (832,480)，`scaling_ratio=min(...,1.0)=1.0` → **不做 BICUBIC，仅 reflect-pad** `transforms.py:210-218` |
| text tokenize | 0.13ms | 可忽略 |
| action / seq_plan | ~0.5ms | 可忽略 |
| **全 transform** | 9.7ms（32线程）/ 13.6ms（8线程）/ **40.1ms（1线程）** | **完全由 video pad 主导** |

### 4.2 为什么 No-TTT 是 ~34ms

- 主进程 torch 被 `OMP_NUM_THREADS=1` 钉在 1 线程（`/proc/1202529/environ` 实证 + torch 2.10 `get_num_threads()==1` 实证）。
- 1 线程 pad = 40.7ms ≈ No-TTT 实测 transform 33.6ms/consumer（差异来自真实 caption 更短/CPU 频率波动，方向一致）。
- G1 无该 env，torch 默认多线程 → pad ~10ms → 整链路 ~18.3ms/consumer。

### 4.3 为什么这是“纯冗余计算”

- 两 run `compact_cached_video=False` → 每 consumer video = `torch.zeros((3,17,256,512), uint8)`（`cached_pixel_geometry.py`）。
- worker 端还强制校验 `torch.count_nonzero(video)==0`（`no_ttt_cpu_loader.py:257`）。
- 反射补零的输出恒为 `torch.zeros((3,17,480,832))`——**同一常量张量被计算 492 次/step（No-TTT）/ 250 次/step（G1）**。
- 冗余耗时：No-TTT 492×33.6ms ≈ **16.5s/step**；G1 250×~10ms ≈ 2.5s/step。

---

## 5. 任务 E — SHA / 交付格式 / 执行边界

- Root: `49df7f3c`（live HEAD `b8ee0403`，仅文档提交，代码与任务指定 child 一致）；Child/Gitlink: `746c5cf`（工作树干净，全部代码结论基于此）。
- 本文件即最终交付：`docs/collab/chatgpt/DS_PRO_2026-10-27_G1_NoTTT_CPU_Data_Path_Audit.md`。
- 执行边界：全程只读（文件/日志/tmux pane/进程环境）+ CPU-only 微基准（单进程、<3s/档、总 <30s，属低负载仿真，未触禁）；未改生产代码、未停训练、未做 GPU/CUDA/高负载实验。

---

## 6. 证据清单（file:line / 数据源）

1. **No-TTT 分项计时**：`no_ttt_cpu_loader.py:394-506`（`_begin`/`_materialize`/`finish`），输出经 tmux `nottt` pane（`/proc/1202529/fd/1 → /dev/pts/31`）捕获解析，136 条完整对象。
2. **transform 计时在 data_prepare 内**：`matched_no_ttt.py:269-274`（`with self._telemetry_stage("data_prepare"): loader.materialize(...)`）。
3. **source_read 在 data_prepare 外**：`matched_no_ttt.py:265-268`（GA0 `loader.begin` 在 stage 之外）。
4. **G1 data_prepare 含 transform**：`local_memory_grouped.py:330-350`（nw0 `produce` 在 data_prepare stage 内）；`robocasa_exact_window_local.py:410-412`（每 consumer 一次 `_transform`）。
5. **video 恒零占位符**：`cached_pixel_geometry.py::cached_pixel_placeholder(compact=False)=torch.zeros`；`robocasa_exact_window_cached_sft.py:131`；`no_ttt_cpu_loader.py:183,257,476`；两 run `data_pipeline_execution.compact_cached_video=false`。
6. **reflect-pad 无 resize 且线程敏感**：`transforms.py:188-218`（`scaling_ratio=min(...,1.0)` 禁止放大）；本机实测（1/4/8/16/32/96 线程，见 §0/§4）。
7. **OMP_NUM_THREADS=1（No-TTT）**：`/proc/1202529/environ`；torch 2.10 `OMP_NUM_THREADS=1 → get_num_threads()==1` 实测；全仓仅 `no_ttt_cpu_loader.py:59` 调用 `set_num_threads`（worker 内）。
8. **G1 无 OMP 限制**：G1 tmux `robo15train` `show-environment` 无 OMP/MKL/OPENBLAS；G1 `rank0.log` 无 num_threads 记录。
9. **monitor 数字**：G1 `train_rank0.jsonl`（末 1000 iter：data_prepare 4.57s、consumers 250、18.3ms/consumer、full_segment_prefetch=False、num_workers=0）；No-TTT `train_rank0.jsonl`（iter>1760：data_prepare 17.6s、consumers 497、35.4ms/consumer）。
10. **同机证据**：`hostname=data`；/mnt/data、/mnt/data1 均本机 NVMe（`df`）；两 run GPU 均为本机 8×H100。

---

## 7. 修复建议（提交给 owner/ChatGPT/cx 裁决，ds_pro 不实施）

### 建议 1（代码级，收益最大，需审核）

**消除常量零视频的逐 consumer 冗余 pad**：在 `compact_cached_video=false` 时让占位符直接以 canvas 尺寸分配（或首次 pad 后缓存共享），使 `VideoResize` 的 `orig==target` 分支直接跳过。影响面：`cached_pixel_geometry.py`、`no_ttt_cpu_loader.py:476`、G1 `__getitem__`。预估：transform 16.72s → <1s，关键路径 21.5s → ~6-7s。前提：确认 pixel video 恒零是有意设计（见 §0 正确性观察）。

### 建议 2（环境级，零代码风险，立即可做）

**启动 No-TTT 训练时取消 `OMP_NUM_THREADS=1`，或设为 8-16**（不要默认 96：4 rank×96 线程竞争，实测整链路反而更慢）。8 个 worker 不受影响。预估：transform 16.72s → ~6-7s，关键路径 → ~10-12s。