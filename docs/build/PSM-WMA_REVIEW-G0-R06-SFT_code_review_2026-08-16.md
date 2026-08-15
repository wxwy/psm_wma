# PSM-WMA REVIEW-G0-R06-SFT 代码审查（第一轮）

- 日期：2026-08-16；审查人：Kimi（只读，未执行正式训练/评测）
- 对象：root `0c6ac07` → 修复后 `372f902`；cosmos-framework `fea74b2` → 修复后 `92814ca`
- 结论：**REQUEST_CHANGES**

## 已验证通过（附证据）

1. **R12 schema 读取正确**：实测 `episode_000000.pt` 的 `latents.cosmos_concat_view` 为 `[55,48,16,32]` FP16、`indices.source_frame_indices` 步长 4；`latent_cache.py:63-64` 的读取键与之匹配。
2. **窗口切片机制**：`get_window` 对 start=0/1/4/5/100 均返回 `[5,48,16,32]`；`torch.searchsorted` + 等值校验防错位（latent_cache.py:74-85）。
3. **parity 门控与回退链完整**（实测）：无 parity 文件 → `enabled=False` → `get_window` 返回 None → 样本不带 cache 标记 → 模型走在线 `_encode_vision_x0_tokens`（omni_mot_model.py:3889-3926 的 else 分支）。
4. **模型 bypass 形状正确**：`[T,C,H,W]` permute→`[1,C,T,H,W]`，与 `_encode_vision_item` 返回约定 `[...,C,T,H,W]` 一致（omni_mot_model.py:3641）。
5. **task_index=0 过滤位置正确**：在 train/val split 之前按 episode 首行 task_index 过滤（libero_lerobot_dataset.py:168-172）。
6. **窗口序号==源帧偏移**：`get_window_identity` 的 `idx-prev` 与 `_build_item` 的 `start=ep_starts[ep]+(idx-prev)` 同构（libero_lerobot_dataset.py:190-196 vs 233）。
7. **配置接线实测正确**（92814ca 修复后）：`task_index=0`、`use_latent_cache=True`、`latent_cache_root/parity` env 插值解析、`max_iter=500`、`grad_accum_iter=1`。
8. py_compile 全部 PASS；cosmos `git diff --check 05e0586..92814ca` PASS；root parity 工具 EOF 问题已由 Codex 在 `82fd98b` 自行修复。

## 发现

### HIGH-1 parity 证据没有生产者（阻塞 cache 启用）

`tools/g0/check_r06_latent_cache_parity.py` 只校验外部 JSON 的 `latent_max_abs_diff`/`loss_max_abs_diff`，但**没有任何代码生成该证据**（无脚本、无单测）。另外从机制上，严格 parity（atol 1e-5）大概率不成立：cache 是整段 episode 因果 VAE 编码的切片，在线路径是独立 17 帧窗口编码，且 `latent_cache.py:76` 的 `aligned_start = start - start%4` 使 start%4≠0 的窗口实际取的是向前最多 3 帧的 latent。

最小修复：新增 parity 生成脚本——同一批窗口（必须覆盖 start%4∈{0,1,2,3} 且 start>0）分别走 cache 路径和在线路径，记录 latent/loss 的 max_abs_diff 与语义偏移量，输出证据 JSON；PASS 才启用 cache，FAIL 保持在线并在报告中如实记录。

### HIGH-2 collector 与 eval summary 契约不匹配（Gate 恒 FAIL）

`tools/g0/collect_r06_sft_gate.py:56-58` 读 `evaluation.get("status", evaluation.get("pass"))`，但 `closed_loop_eval.py` 的 summary.json 字段是 `overall_success_rate/total_episodes/task_results[].episode_results[]{success,steps,error}`，**没有 status/pass 键** → eval_pass/repeat_pass 恒 False → Gate 恒 FAIL。同时缺 Runbook §7 的 SR>0、action finite、重复性 diff==0 断言。

最小修复：直接从 summary 字段计算（`overall_success_rate>0`、episode 全 `error==null` 且 steps 满 520），并比对两次运行 `actions/task_000/episode_*.json` 的逐位一致性。

### HIGH-3 cache 路径没有消除真正的瓶颈（视频解码）

`ActionLatentCacheDataset.__getitem__`(action_sft_dataset.py:56-72）仍调用底层完整 `_build_item`（含 torchcodec 视频解码）,cache 只省掉 GPU 端 VAE encode。R04/R05 实测瓶颈是 CPU 解码（53s/step 的大头），当前设计拿不到主要提速，与 mowa 参考（cache 替代解码）不一致。附带风险：`_build_item` 解码失败时会 `random.randint` 重采样换 idx(libero_lerobot_dataset.py:215-226)，而 wrapper 用原始 idx 取 latent → **latent 与样本错配**。

最小修复：cache 启用且 parity PASS 时，dataset 侧跳过视频解码（仅构造 prompt/action/元数据 + cache latent）；并保证 latent 取用与实际返回样本的 idx 一致（重采样后用最终 idx 取）。

### MEDIUM-1 probe TOML 缺 vae_path

`action_policy_libero_edge_r06_probe.toml` 没有 `[model.tokenizer] vae_path`，会落回实验默认的相对路径 `pretrained/tokenizers/video/wan2pt2/Wan2.2_VAE.pth`（本地不存在，可能触发外网下载或 FileNotFoundError)。最小修复：补 `vae_path = "${oc.env:WAN_VAE_PATH}"`。

### LOW-1 collector loss 键口径

`_metrics` 读 `"loss"` 键；R05 metrics 用 `total_loss`。与 R06 实际 step-metrics wrapper 的键名对齐即可。

### LOW-2 OmegaConf 空默认值语法警告

`${oc.env:LIBERO_LATENT_CACHE_ROOT,}` 触发 grammar 警告；建议 `${oc.env:LIBERO_LATENT_CACHE_ROOT,''}`。

## 是否阻塞 REVIEW-R06-SFT 通过

是。HIGH-1/2/3 与 MEDIUM-1 修复并复验前，不启动正式 500 步训练；probe 可在 MEDIUM-1 修复后先跑。

## 二轮复审（root e09c640 / cosmos adbffd6,2026-08-16)

结论：**APPROVE**（附 2 个 LOW 观察项，不阻塞）。

### 四项修复核验

- HIGH-1 ✅ `tools/g0/generate_r06_latent_cache_parity.py` 为真实 VAE 双路径探针：`_load_video` 在线编码 vs cache 切片对比，覆盖 start=1..5(start%4 ∈ {0,1,2,3} 且全 >0),`semantic_shift_frames` 如实记录；layout 核对无误(_load_video 返回 [T,C,H,W] float[0,1] → uint8 → [C,T,H,W] → encode;split="full" 合法）。checker 增加 coverage 与 start>0 断言。注意:loss 项目前是 mean(latent²) 代理（脚本 docstring 已声明），且按机制预期 start>0 窗口大概率 parity FAIL → cache 保持禁用、训练走在线——这是诚实的安全结果。
- HIGH-2 ✅ collector 改为直接计算：`overall_success_rate>0` + 全 episode `error==null` 且 `steps==520`；新增 `--eval-actions/--repeat-actions` 两轮 action JSON 文件级逐位比对；loss/total_loss 双键兼容。
- HIGH-3 ✅ latent cache 移入 `_build_item`(libero_lerobot_dataset.py:301-331):cache 命中跳过 `_load_video`，以 zeros 占位 `[17,3,256,512]`;latent 用实际窗口的 `window_start_frame` 绑定，重采样错配路径消除。实测 task0 过滤 37/38 episodes、8982 窗口；cache 命中时 video 全零占位、latent [5,48,16,32]、action [16,10] 完好、identity 一致。
- MEDIUM-1 ✅ probe TOML 已补 `vae_path = "${oc.env:WAN_VAE_PATH}"`;LOW-2 env 空默认值语法已改 `'...''` 形式。

### 复验命令与结果

- py_compile(cosmos 5 文件 + tools 3 文件）PASS;`git diff --check`(cosmos 05e0586..adbffd6、root 3933d6f..e09c640)PASS。
- TOML 解析：主/probe 均合法，experiment=max_iter/tokens/vae_path 正确。
- 定向单测（无 GPU):task0+cache 数据集构建与取样 PASS（上述数值）。

### 遗留 LOW（不阻塞）

- LOW-A:外层 `ActionLatentCacheDataset` 包装仍会在样本上覆写 `vision_latent_cache`（用原始 idx)；仅在 cache 命中路径无解码就无重采样，理论错配仅剩"非解码异常触发重采样且两窗口均 cache 命中"的极小概率场景。
- LOW-B:collector criteria 的 `closed_loop_success_rate_gt_zero` 与 `closed_loop_episodes_520_no_error` 共用 eval_pass，子条件失败时无法区分。

### 下一步（待用户确认后执行）

1. 5 步显存探针（在线路径，51200 tokens,ga=1);
2. parity 探针（GPU，约 5 窗口 VAE 编码，1-2 分钟）产出 parity 证据 JSON。
