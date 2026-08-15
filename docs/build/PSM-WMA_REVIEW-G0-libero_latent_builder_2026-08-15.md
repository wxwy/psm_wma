# REVIEW — G0 LIBERO latent 缓存构建脚本（commit a5633ea）

- 审查人：Kimi（独立只读审查，未修改任何文件、未运行编码）
- 日期：2026-08-15
- 对象提交：根仓库 `a5633ea`（feat: add Cosmos LIBERO latent cache builder）
- 重点文件：`tools/g0/build_cosmos_libero_latent_dataset.py`（同提交另有 `tools/g0/build_cosmos_rgb_latent_cache.py`，一并参考）
- 基线：cosmos-framework 子模块当前工作区版本（审查时未动）

## 审查结论

**REQUEST_CHANGES**

核心编码语义（归一化、4n+1 temporal padding、concat_view 布局、latent shape、source_frame_indices、instruction 提取）逐项对照当前源码核验通过；但存在 2 个 HIGH 级问题，必须在全量执行前修复，否则产出的缓存报废或不可追溯。

## HIGH（阻止通过，全量执行前必须修复）

### HIGH-1 `--image-size` 默认 192，与训练契约 256 不符

- 问题：脚本默认 `--image-size 192`（`tools/g0/build_cosmos_libero_latent_dataset.py:56`），而 LIBERO 训练契约是 256。
- 证据：
  - `cosmos-framework/cosmos_framework/configs/base/experiment/action/posttrain_config/action_policy_libero_nano.py:203-204`：`chunk_length=16, image_size=256  # concat_view -> 256x512`
  - `action_policy_libero_all_nano.py:202-203` 同样 256
  - 数据集类默认 `image_size: int = 256`（`libero_lerobot_dataset.py:75`）
- 补充核验：192×384 不会触发崩溃——`get_vision_data_resolution` 按 `min_dim <= 256` 归入 `"256"` 桶（`cosmos_framework/utils/generator/data_utils.py:106-108`），编码 chunk window 相同；但 latent 空间尺寸为 12×24 而非契约的 16×32，且 `image_size` 未写入任何 metadata/manifest，事后无法区分缓存来源分辨率。
- 最小修复：默认值改为 256；episode metadata 与 manifest 顶层增加 `image_size` 字段。
- 是否阻止：是。

### HIGH-2 断点续跑产出残缺 manifest

- 问题：跳过已存在 episode 时直接 `continue`（`build_cosmos_libero_latent_dataset.py:84-86`），`manifest_rows` 只收集本次新编码的 episode；结束时第 129-143 行整体覆写 `dataset_manifest.json`。任何续跑都会把先前 run 的 episode 从 manifest 抹掉；中途崩溃同理（manifest 只在正常结束时写出）。
- 最小修复：启动时加载已有 manifest（或扫描已有 `.pt` 重建条目），合并去重后再覆写。
- 是否阻止：是。

## MEDIUM（不阻塞，但影响可追溯性与健壮性，建议同批修复）

### MEDIUM-1 写入非原子

- `torch.save(output_path)` 直接写最终路径（94-117 行）。进程中断留下截断 `.pt`，续跑时第 84 行将其视为完成品跳过 → 静默坏数据。
- 最小修复：写 `*.tmp` 后 `os.replace` 原子改名。

### MEDIUM-2 uint8 量化用截断而非四舍五入

- 第 90 行 `(video * 255.0).clamp(0, 255).to(torch.uint8)` 为截断。浮点误差可使 `k/255*255 = 127.999…` 截断为 127，产生系统性 -1 LSB 偏差。
- 最小修复：`.round()` 后再 `.to(torch.uint8)`。

### MEDIUM-3 provenance 缺口

- episode metadata（102-114 行）与 manifest（129-143 行）均未记录 `vae_path`、脚本版本/commit、`split`、`fps`。同提交的 `build_cosmos_rgb_latent_cache.py` 有记录 `vae_path`。
- 最小修复：补齐上述字段，供 Gate 机器核验。

## LOW

- LOW-1：`latent_shape` 用 `json.dumps` 存为字符串（124 行），应直接存 list，便于机器判定。
- LOW-2：`episode_frame_indices` 实为全局行号（`np.flatnonzero(dataset._row_episode == episode_index)`，87 行），非 episode 内帧号，命名误导；建议改名 `global_row_indices` 或减去 episode 起始行。
- LOW-3：instruction 只存 `" | "` 分隔的第一个变体（48 行）；训练时 `ai_caption` 随机选变体（`libero_lerobot_dataset.py:292`）。若声称"原文保存"，建议存完整字符串。

## 已核验正确的源码锚点

| 审查点 | 结论 | 证据 |
|---|---|---|
| 归一化 `uint8/127.5-1` | 与契约一致 | `omni_mot_model.py:3533-3534`（`_normalize_uint8_vision_item`） |
| 4n+1 padding 必要性 | 接口有硬断言，不自补齐 | `wan2pt2_vae_4x16x16.py:873-876` |
| 末帧 replicate padding | 合理；接口内部再 zero-pad 到 window 倍数并裁回，不重复计数 | `wan2pt2_vae_4x16x16.py:889-893, 956-958` |
| concat_view 布局 | 第三人称左+手腕右水平拼接 `[T,C,H,2W]`，训练按单 vision item 编码 | `libero_lerobot_dataset.py:325-327`；`action_policy_libero_nano.py:203-206` |
| latent shape/layout | `[B,16,T_lat,H/16,W/16]` → 存 `[T,16,h,w]` fp16，与 metadata 一致 | `wan2pt2_vae_4x16x16.py:856-859`；脚本 96、109 行 |
| source_frame_indices=4i | Wan VAE 首帧 prime + 每 4 帧一组，因果端点即 4i | `wan2pt2_vae_4x16x16.py:878-880, 943-952` |
| instruction 提取 | `_episodes`/`_tasks` 结构匹配，v2.x/v3.0 均兼容 | `base_dataset.py:74-88`；脚本 40-48 行 |
| 分辨率桶 | 256×512 与 192×384 均归 "256" 桶（window 68），192 不会崩 | `data_utils.py:106-108`；`wan2pt2_vae_4x16x16.py:1401-1405` |
| `tokenizer.model.model` 属性链 | `Wan2pt2VAEInterface.model`（WanVAE，1412 行）→ `WanVAE.model`（1201-1204 行） | 静态确认 |

## 已执行的只读命令及关键结果

- `git log --oneline -5`、`git show a5633ea --stat`、`git show a5633ea -- tools/g0/build_cosmos_rgb_latent_cache.py`：确认提交范围（5 文件，+261 行，两新脚本 + SESSION/TODO/MEMORY 文档）。
- 通读 `tools/g0/build_cosmos_libero_latent_dataset.py`（148 行全文）。
- 通读 `wan2pt2_vae_4x16x16.py` encode 路径（840-969、1195-1245、1370-1480 行）与 `omni_mot_model.py` `_encode_vision_item`/`_normalize_uint8_vision_item`（3520-3640 行）。
- 通读 `libero_lerobot_dataset.py`（57-181、270-333 行）与 `base_dataset.py`（55-99 行）。
- `Grep` 定位 `_encode_vision_item`、`get_vision_data_resolution`、LIBERO 配置中的 `image_size`/`chunk_length`/`camera_mode`。

## 未执行的验证及原因

- 未运行任何编码（含单 episode 冒烟）：审查要求不运行全量编码，且 VAE 编码属正式推理，需另行确认。
- 实际显存占用与长 episode 耗时未验证。
- 因此 `tokenizer.model.model.to(device)` 属性链、bf16 输入转换（`WanVAE.encode`，1224-1228 行）仅静态确认。

## 修复关闭清单（REVIEW 转 DONE 的验收项）

1. [ ] HIGH-1：`--image-size` 默认改 256；metadata/manifest 记录 `image_size`。
2. [ ] HIGH-2：manifest 续跑合并（加载已有或扫描重建），不丢历史 episode。
3. [ ] MEDIUM-1：`torch.save` 走 tmp + `os.replace`。
4. [ ] MEDIUM-2：uint8 转换加 round。
5. [ ] MEDIUM-3：补 `vae_path`、代码版本/commit、`split`、`fps` provenance 字段。
6. [ ] LOW-1/2/3：shape 存 list、重命名全局行号字段、存完整 instruction 原文。

修复后需复审；复审通过并经用户确认后方可全量执行。
