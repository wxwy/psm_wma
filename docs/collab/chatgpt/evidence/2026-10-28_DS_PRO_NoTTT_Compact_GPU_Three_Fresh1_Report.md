# DS_PRO — V3 No-TTT Compact Cached Video 0/1 GPU Forward/Loss/Gradient Parity（三次 Fresh1 训练）

> **证据来源**：2026-10-28 DS_PRO 经用户提供的全文报告，GPT按提供的数值、执行顺序和引用路径归档。**本文件不是 DS原生 JSONL、Rank日志、Checkpoint或在服务器上独立复测**，不得据此代替 frozen GPU Parity Gate 的逐参数证据。DS称 local Root `8c3d0562` 领先 origin/V3 `4c9990f5` 三个 evidence 文档提交；本次 GitHub 远端未能获取 `8c3d0562` 对应commit，不以其作为正式 implementation target。

- Gate 声明：`GPU_NUMERIC_PARITY_NOT_RUN` → GPU Forward/Loss/Gradient parity。
- 日期：2026-10-28。DS角色：ds_pro（运行验证，无生产代码修改）。
- 代码实际目标：Root历史 NoTTT implementation `49df7f3c2e0ba8ef5871f9dd490e41fbc3dc5da9` / Child+Gitlink `746c5cf2f2324104a62fb71510343aa40d3976c5`。
- DS称已获Owner同意在GPU4–7与旧正式NoTTT共存。报告实际使用 `scripts/train_v3_matched_no_ttt_4gpu.sh` 的 `fresh 1`，真实Optimizer Step + DCP Save。该执行形态与先前“仅 Forward/Backward、不Optimizer/不Checkpoint”的隔离数值等价 Harness合约**不同**；具体Gate判定请见对应独立Review。

## 1. 运行身份和条件（DS报告）

- 新建三套互不相同的 Fresh Job，均使用 `CUDA_VISIBLE_DEVICES=4,5,6,7`、`world4/GA4/B8/T16/K4`、`--max-iter 30000 --warmup 500 --save-iter 100`， `--formal-execution-until 1`。
- A compact1: `no_ttt_compact1_gpu_parity_world4_ga4`。
- B compact0: `no_ttt_compact0_gpu_parity_world4_ga4`。
- C compact1 repeat: `no_ttt_compact1_gpu_parity_r2_world4_ga4`。
- `PSM_V3_COMPACT_CACHED_VIDEO` A/C=1、B=0；其余环境声称相同。
- Python `psm_wma/cosmos-framework/.venv/bin/python`，torch2.10.0+cu128，HF offline。
- 输入：RoboCasa target-atomic source + verified index + exact-window cache；DROID Base `Cosmos3-Edge-Policy-DROID-dcp`，Wanu VAE path按DS报告，EDGE tokenizer；区别包括三个不同的 Job namespaces（而非“只有 Compact env 不同”的严格同进程A/B实验）。
- 上一CPU验证已通过：`cached_latent_required=True`，CPU model batch payload逻辑值一致，但本报告未包含同一次GPU重放的逐Rank Frozen Batch内容等价证明。

## 2. Rank0 Iter1 telemetry（DS报告）

| Run | compact | outer_loss | action_loss | vision_loss | total_grad_norm_rank_local |
|---|---|---:|---:|---:|---:|
| A | 1 | 14.937467575073242 | 1.2275960445404053 | 0.2661505937576294 | 3.706259250640869 |
| B | 0 | 14.937467575073242 | 1.2275960445404053 | 0.2661505937576294 | 3.7076737880706787 |
| C | 1 | 14.937467575073242 | 1.2275960445404053 | 0.2661505937576294 | 3.7086875438690186 |

- DS称三次 `actual_consumer_identity_sha256` 均为 `9207fc67…7830`（仅短写，没有给出完整字符串/各Rank证据）；每Job rank0 `valid_consumers=512`、8 tasks ×64、`telemetry_errors=[]`、missing/nonfinite gradients=0。
- Scalar Loss三次回传值完全相同（按所给精度），而非给出了完整模型输出 Tensor 逐位比较。
- 算数复核：`abs(B−A)=0.0014145374`，相对A约`0.03817%`；`abs(C−A)=0.0024282932`，相对A约`0.06552%`。仅代表 **rank0_local_fsdp_shard 梯度范数**，不能据此证明任意单独参数的梯度值相同或“不确定度是唯一原因”。
- DS称 `compact1 peak_reserved=29.84GiB`、`compact0=30.68GiB`；是不同 Fresh进程的内存记录，属于单次观测。

## 3. DS提供的 DCP 完整性标记里的“组件 SHA”

| Run | model metadata SHA256 | optim metadata SHA256 |
|---|---|---|
| A compact1 | `4e32a2fb032d79337a53f5ba41ac984828de7488c6c36bbef925c7196e80a21e` | `082fb015f5cc797e0f2250e3e107c496482118cae9976e853f15f21671a594a5` |
| B compact0 | `4648a14a518596d97765dff55ed1f7bd489215a14cbff3971ad7ab2ac655cbaf` | `dc889173ad5c5f762f5ddadde5936b718aac6bab6cf69e593c315fbd92e2bd74` |
| C compact1-r2 | `bc727b02c5b76f202061cc1c0f775454effa7166df448771af79d9e970e42f7d` | `402f4eeca5417d88801a422c82f6b0df328b22385dae60115f879f49cf755f70` |

- DS称上述值来自 `checkpoints/iter_000000001/complete.v1.json`，文件尺寸三次相同（model rank0..3每个3370522797 bytes，optim rank0 2850560422、rank1..3 2847686572，trainer rank0 28702/rank1..3 27441，scheduler rank0 14506，四个rank sidecars各1150）。
- **源码释义**：Child `cosmos_framework/checkpoint/dcp.py:_component_witness` 返回 `metadata={size,sha256}` 以及 `files={shard filename: size}`。因此表格里的SHA是**DCP元数据文件 .metadata SHA**，并不是 Sharded Model/Optimizer Tensor Values 的SHA，不能用于推断权重更新的数值差异及运行间噪声。
- DS称因磁盘容量在100%后删除 **A/B/C三个独立测试Job的 `checkpoints/`**，释放约72G；保留三个新Job的 monitor/launches/config/JobIdentity。报告声称未碰旧正式NoTTT/S1 Job/Owner资产。Checkpoint清理权限归Owner本地管理决策；GPT不另开磁盘容量Gate，也不据此请求恢复已删DCP。

## 4. DS结论（原样区分于GPT Verdict）

DS自评：Forward/Loss `PASS`、Gradient `PASS`（同compact1模式两次范数变化0.065%大于A/B模式间0.038%）、单步DCP SHA差异解释为GPU运行非确定性，旧Job未受影响，未测试原 NoTTT生产 Job跨Checkpoint切换或大于1 iter。

GPT审核见 `docs/collab/chatgpt/reviews/2026-10-28_V3_NoTTT_Compact_GPU_Forward_Loss_Gradient_Parity_Evidence_Review.md`。**这些DS自评不是formal Gate verdict**。
