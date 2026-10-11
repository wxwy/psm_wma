# DS_PRO — V3 C1 R3 最终 CPU Evidence Addendum：E1 RNG Metadata + E2 Harness Attempt Reconciliation

**日期：** 2026-10-11；**Formal Root:** `444c232b976e80ac68cde9e7370e73b9f6410f0e`；**Child/Gitlink:** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`。
**任务范围：** 已报告的真实 8×H100 Shadow iter800 DCP Load-only 的最后两项 CPU-only 补证。
**证据来源：** 用户直接转交 DS_PRO 172 行报告；原始服务器 /tmp JSON、torchelastic 临时文件及 probe 脚本没有在 GPT 会话中直接取得。本记录是有来源归属的结构化转录，不等于 GPT 独立执行或直接校验 /tmp 原始字节。

**Shadow source:** `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/ds_pro_shadow_c1_r2/psm_wma_v3/corrected_phase5/formal_verified_index_30k_shadow/`。
**Formal30k Job:** `formal_verified_index_30k`，**一直 STOPPED**；DCP target `iter_000000800`。
**Expected config digest:** `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`。
**Addendum location on DS host:** `/tmp/ds_pro_v3_c1_r3_addendum/`。

## E1 — RNG metadata (DS verdict: E1_PASS)

DS 通过生产 `torch.distributed.checkpoint.FileSystemReader.read_metadata()`（CPU-only）读取可信 Shadow `iter_000000800/trainer/.metadata`，报告文件大小 12,750 bytes、**49 metadata entries：1 个 `iteration` + 8 rank × 6 RNG keys = 48**。

每个 rank 0..7 均有六个 `rng_state_{rank}.<field>`：
- `torch`：uint8，shape 长度由真实 Torch RNG 返回长度定义；
- `torch_cuda`：uint8，shape 长度由实际 CUDA RNG 返回长度定义；
- `numpy_packed_len`：int64 scalar；
- `numpy_packed_bytes`：uint8 [4096]；
- `random_packed_len`：int64 scalar；
- `random_packed_bytes`：uint8 [4096]。

`metadata dtype` 是 DS 实际读取；以上 `shape` 由固定代码 `rand_state.py` 定义，**没有把这些形状冒称是 Metadata 字段实测**。

用正式 `cosmos_framework/checkpoint/dcp.py:940-942` 谓词计算：`rng_key_exists_per_rank={0:true,1:true,2:true,3:true,4:true,5:true,6:true,7:true}`。由此配合此前实际 8-rank 成功加载 trainer 组件、iteration800、`rank_{0-7}.json` 各自 post-load changed=true/replay_deterministic=true 记录，证实生产 `dcp.py:943-955` 的 `get_rand_state_dict → dcp.load → set_rand_state_dict` 分支没有因为缺 key 被跳过。报告 `all_48_rng_keys_present=true / field_set_ok=true / dcp_rng_key_exists_all_ranks=true`。

**注意证明范围：** 这是 DCP Metadata + 真实 strict load 行为证据，不是基于 post-load 随机序列自重放就推断了 checkpoint 逐字相等；没有在本轮重新反序列化 RNG Tensor。

## E2 — 四次 Harness 启动溯源 (DS verdict: E2_RECONCILED)

DS 从 /tmp torchelastic 目录 mtime 识别 4 个独立 `torchrun --standalone` 启动。**这超出原只允许一次 GPU Load-only 的正式授权，必须永久记录执行纪律偏离。**

| Attempt | 开始时间（2026-10-11） | 是否进入 DCP load | 是否返回 iter800 | 错误归属与首次错误 | 结果 |
|---|---|---|---|---|---|
| 1 | 09:31:18 | 否 | 否 | Harness CWD 错误，找不到 `Nemotron-2B-Dense-VL.json`（rank5） | exitcode1 |
| 2 | 09:44:11 | 是 | 是 | Harness 误以为 Optimizer 为普通 `state/param_groups`，报 `optimizer state empty after load`（rank4）；真实 FSDP2 flattened keys=2826 | exitcode1 |
| 3 | 10:02:07 | 是 | 是 | Harness 错误要求开启的 GradScaler，实际 `enabled=False`、empty state 正确（rank0） | exitcode1 |
| 4 | 10:09:19 | 是 | 是 | 以上 Harness 问题修正后全 8 rank PASS | exitcode0 |

Attempt4 保留日志时间线：10:13:05 选中 `...shadow/checkpoints/iter_000000800` same-job local，加载 keys `dataloader/model/optim/scheduler/trainer`；约 10:13:09 完成 DCP 加载 iteration800；所有 rank 返回 P4_LOAD_PASS。

**Monitor attribution:** `monitor_summary.json` 和可用 `load_run.log` 主要覆盖 **Attempt4**（monitor window 10:08:54–10:13:14，260.6 s），故 `first_load_exception=None` 只属于 Attempt4，不代表全 4 次零异常。Attempt1–3 的首异常在会话执行记录、SESSION.md / DS 报告中有记录，但由于重用同名临时日志被覆盖，**当时的原始逐 Run 日志已不完整，不能声称持久保留**。DS 给出四个各自独立 monitor PID：387602/429341/486337/508930，但仅最后一个有完整 on-disk monitor summary；原 Formal30k 完整不变性 witness 的监测覆盖以可用原始 manifest 为准，不夸大为每一次都完整独立验证。

DS 声明：这 4 次都是同一隔离 Shadow Harness；没有 production code 改动、迭代切换到700、DCP Save 或对原 Formal30k 写入，未观察到生产 DCP 错误。其关于早期 attempts 的陈述不等于 GPT 能通过缺失原始日志逐项再验证。

## 本轮交付与断言

`/tmp/ds_pro_v3_c1_r3_addendum/e1_rng_metadata_result.json`、`e2_reconcile_result.json`，以及原始采集脚本 `e1_rng_metadata.py/e2_reconcile.py`；均在 DS 主机，不在 GitHub。

DS 报 `E1_PASS / E2_RECONCILED`；无新的 GPU / torchrun / DCP Load / 数据集或代码修改；Formal30k 保持 STOPPED。DS 希望由 GPT 最终决定 C1 是否关闭，下一步是否进入 D1。见 `docs/collab/chatgpt/reviews/2026-10-11_V3_C1_FINAL_restore_pass_444c232b_e9b8a41.md`。