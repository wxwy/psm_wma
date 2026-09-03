# R09-B TTT v0.2.1 Continual Local Memory 静态 Source Audit v0.2

**状态**：REVIEW。

**任务**：`G0-R09-B-TTT-V02-STATIC-SOURCE-AUDIT`。

**设计 authority**：`docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.2.md` 与修订 `v0.2.1`（root `9074e4eb7f399e69beb0e0409bb01b0452fe9ed1`）。

**实现基线**：root `3659aeba6387c790cfa4be25a8e102bb1d142985`，`cosmos-framework` HEAD/Gitlink 均为 `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`。
**本文件权限**：只读/static source audit；没有修改 Cosmos 实现，没有导入或运行 torch，没有读取模型、训练数据或 checkpoint，没有使用 GPU。

## 0. 结论与调整后的实现路线

v0.2.1 的算法合同在当前 Cosmos 扩展点上可实现，但**不能只替换**现有
`TTTLocalMemoryBackend`。现有数据路径把 window 当作彼此独立的 packed sample，Local
runtime 每次从 `state=None` 回放最长 16 步历史；训练器又在每个 microbatch 后立即
backward。若直接换 backend，会继续重复写历史、丢失跨 call state，或让未 detach 的
图跨越已经 backward 的 microbatch。

后续实现必须依次关闭四个独立 seam：

1. CPU-only functional KVB core：四成员 fast pytree、learned Q/K/V/W0、逐 sample
   feature-mean update、更新后读取、整树 reset/detach；
2. chronological segment adapter：把 window stream 变成 episode 内连续、最多 16 个
   control timestep 的 segment，segment 内有图、segment 间只 carry detached 数值；
3. native outer-loss adapter：保留 Cosmos 原 vision/action flow loss 定义，但对所有有效
   `(episode,t)` 累积 numerator/denominator，消除 padding、microbatch、accumulation 和 rank
   对权重的影响；
4. inference state owner：在 action server 顶层 `torch.inference_mode()` **之前**完成
   W-only update，并通过普通 detached Local token 进入原 Cosmos inference。

因此新的构建顺序应为：本 source audit 独立审核 → CPU algorithm/gradient implementation
design → CPU functional implementation/contract → chronology/loss integration design 与实现 →
bounded GPU train smoke → inference persistent-state design/smoke → optimizer/config/P3/P4/P5
重新冻结 → 正式 LIBERO 4-in-1 训练。旧 B2-T authority 不能复用。

## 1. Current implementation / gap map

| 层 | 当前真实入口与 `file:line` | 当前 I/O、carry/detach/reset | v0.2.1 结论 |
| --- | --- | --- | --- |
| trainer | `Trainer.train()`：`cosmos_framework/trainer/__init__.py:305-423`；`Trainer.training_step()`：`:450-513` | 每个 microbatch 调 `model_ddp.training_step()`，立即以 `loss/grad_accum_iter` backward；累计满 16 才 optimizer step。没有 sequence numerator/denominator 或 Local state owner。 | **需新增 adapter**；不能让未 detach fast graph跨 microbatch backward。 |
| production training model | `OmniMoTModel.training_step()`：`cosmos_framework/model/generator/omni_mot_model.py:1161-1407` | 输入一个普通 packed batch；先 `_get_training_inputs()`，再按 sample 采 noise，单次 Cosmos forward 和 scalar loss。 | 可复用 Cosmos forward；需在 packing 前按 chronology 产生每个 item 的 Local token。 |
| Local injection | `_inject_local_history()`：`omni_mot_model.py:962-1019` | 输入历史字段 `[B,H,...]`；调用 runtime 后把 `[B,1,32]` token 写回 batch；无 state 入参/出参，无 identity/order/reset。 | **替换调用合同**：新 runtime 接受 one-step evidence + segment metadata + carried state；不得回放 H。 |
| evidence encoder | `LocalEvidenceEncoder`：`cosmos_framework/model/generator/mot/local_evidence.py:16-103` | visual `[B,H,96]`、action `[B,H,10]`、age/dt/mask → `[B,H,256]`；masked exact zero。 | 投影和 mask 逻辑可复用；正式流固定逻辑 `H=1`，age=1；state adapter仍禁用。 |
| current TTT | `TTTLocalMemoryBackend`：`local_evidence.py:202-252` | `W[B,32,256]` + pending/last/flags；每 4 valid update，目标 `e[:32]`，LR=0.1；evidence、W、token全 detach，`create_graph=False`；`state=None` 时 zero init。 | **整体替换**；仅类所在模块/外接 backend seam 可复用。旧五成员 state、目标和 detach 语义全部 superseded。 |
| Local runtime | `LocalHistoryRuntime`：`local_evidence.py:255-302` | backend 分支 `replay(evidence, mask)`，丢弃 returned state；每次 call fresh。 | **需改接口**；显式传回 state，或由单一 chronology owner 管理；不得把 state 隐藏在 batch sample。 |
| Local adapter | `Cosmos3VFMNetwork.__init__()` 与 `_encode_local_memory()`：`cosmos3_vfm_network.py:226-230,941-962` | `[N_local,32] -> [N_local,2048]`，加 modality embedding，作为 clean packed token；初始 zero：`:283-290`。 | 完全复用；TTT 不进入 backbone。 |
| model construction | `OmniMoTModel.set_up_model()`：`omni_mot_model.py:285-330` | backend 外接在 `net.local_history_runtime.recurrent_backend`；TTT 当前未带 Q/K/V/W0 config。 | 可复用注册位置；需新增 config-driven `D_ttt/D_ff/inner_lr/tbptt_steps`。 |
| model config | `OmniMoTModelConfig`：`configs/base/defaults/model_config.py:298-309`；recipe：`action_policy_libero_edge_all.py:54-93` | `local_history_horizon=16` 同时承担历史宽度；backend env selector为旧 B1。 | **需拆分** `runtime_evidence_steps=1` 与 `ttt_tbptt_steps=16`；旧 B1 selector不能作训练 authority。 |
| optimizer | recipe selectors：`action_policy_libero_edge_all.py:204-226`；substring selection：`utils/generator/optimizer.py:141-240` | 旧 TTT selector只有 encoder + 两个 adapter，明确漏掉未来 QKV/W0；未选参数会被 `requires_grad=False`。 | 后续重冻四个 prefix；不能沿用旧 3-selector/count。 |
| checkpoint | `OmniMoTModel.state_dict()`：`omni_mot_model.py:4519-4564` | `net.*` 注册 parameter/buffer正常入 DCP；runtime 返回的临时 state不入 checkpoint。 | QKV/W0 属 slow checkpoint；`W_t` 不注册、不进 model/optimizer checkpoint。严格 sequence resume另行设计，首版非目标。 |
| native noise | `_get_train_noise_level_vision/action()`：`omni_mot_model.py:1720-1866`；`_add_noise_to_input()`：`:1930-2048` | flatten 后每 packed sample 独立 sigma；action 默认复用该 sample 的 vision sigma，但不同 sample 不共享；每个 action tensor独立 `randn`。 | 当 `(episode,t)` 映射为独立 packed item 时已满足跨 item独立；无需改 noise 数学，只需 chronology adapter保持一 item 一 draw。 |
| native loss | `_compute_losses()`：`omni_mot_model.py:1526-1654`；`compute_flow_matching_loss()`：`algorithm/loss/flow_matching.py:18-90` | modality 内先 per-instance，再 batch mean；action caller丢弃 per-instance值；trainer再固定除以 accumulation=16。 | **需最小 loss adapter**导出 time-weighted native per-item scalar及 valid mask，再做 accumulation/rank 全局有效步 mean。 |
| dataloader/packer | `B2ManifestAwareIterableDataset`：`action_sft_dataset.py:95-143`；`IterativeJointDataLoader._iter_synchronous()`：`joint_dataloader.py:953-1044` | manifest wrapper逐 record校验 identity；packer从一个 suite连续取最多 128 个 sample后普通合并，不保留 sequence 轴。 | identity可复用；需 segment grouping/metadata与边界断言，不能把普通 B 误当 episode state batch。 |
| production inference | `ActionPolicyRunner.predict_policy_batch()`：`scripts/action_policy_server_libero.py:931-977`；serial：`:979-1121` | 请求只有 image/prompt/domain/image_size；整个 `generate_samples_from_batch()` 在 `torch.inference_mode()`；没有 rollout identity、executed action、done/reset或 Local state。 | **需新增独立 inference seam**；Local update必须在 inference_mode 前，且 request/state ownership需单独设计。 |
| closed-loop caller | client payload：`simulation/libero/closed_loop_eval.py:235-295`；vector env loop：`:1193-1263` | 客户端知道 env slot/done/实际执行 action，但未发送给 server；active slot会压缩重排。 | 必须显式发送稳定 rollout/env identity、step、previous executed action与 reset/done，不能用 batch row作 state key。 |

## 2. Full fast-state pytree proposal

### 2.1 首版数值候选（留待 implementation-design Gate 冻结）

| 字段 | 候选 | 审计依据 |
| --- | --- | --- |
| `D_e` / `D_local` | 256 / 32 | 当前 encoder 与 Local adapter接口，`model_config.py:300-309`。 |
| `D_ttt` | 64 | 对 256-d evidence 做 4× bottleneck，仍高于 32-d Local output；不继承旧 `W[32,256]`。 |
| `D_ff` | 128 | `2 * D_ttt` 的小型两层 fast MLP；单 sample持久 state仍低于 25 KiB bf16。 |
| activation | `SiLU`，无参数、非 inplace | 当前 Local readout已使用 `nn.SiLU()`（`local_evidence.py:117-121`），无需新依赖或额外 state。 |
| bias | 两层均启用 | v0.2.1 canonical pytree明确含两个 bias。 |
| fast storage dtype | `bfloat16` production；CPU reference=`float32` | LIBERO Edge recipe precision为 bf16（`examples/toml/sft_config/action_policy_libero_edge_all.toml:27`）；CPU contract按 v0.2.1 使用 fp32。 |
| inner compute | K/Q/V 与四叶 fast functional计算、loss、`autograd.grad` 均提升 `float32`；update结果 cast回 storage dtype | 避免 bf16 feature-mean/inner gradient累计；cast必须保持训练图。 |
| `inner_lr` | config scalar首版候选 `0.1`，finite 且 `>0`；不是 parameter/buffer | 与旧 prototype只共享数量级，不共享算法；必须在 implementation design 中做显式批准，不能硬编码。 |

### 2.2 四成员 exact inventory

| canonical member | proposed registered W0 name（完整前缀 `local_history_runtime.recurrent_backend.`） | per-sample shape | storage / compute | fast/slow与 optimizer/checkpoint | init/reset/TBPTT | bytes/sample |
| --- | --- | --- | --- | --- | --- | ---: |
| `W.fast_in.weight` | `w0_fast_in_weight` | `[128,64]` | bf16 / fp32 | runtime值是 fast，普通 optimizer/checkpoint均否；对应 W0 是 slow，optimizer/checkpoint均是 | episode init与 partial reset复制 W0；TBPTT仅 detach value | 16,384 |
| `W.fast_in.bias` | `w0_fast_in_bias` | `[128]` | bf16 / fp32 | 同上 | 同上 | 256 |
| `W.fast_out.weight` | `w0_fast_out_weight` | `[32,128]` | bf16 / fp32 | 同上 | 同上 | 8,192 |
| `W.fast_out.bias` | `w0_fast_out_bias` | `[32]` | bf16 / fp32 | 同上 | 同上 | 64 |

总元素数 `8,192 + 128 + 4,096 + 32 = 12,448`；bf16
`state_bytes_per_sample = 24,896`（128 个并行 state 数值副本为 3,186,688 bytes，约
3.04 MiB）。该数字只计算持久 fast tensor payload，不含 higher-order graph/activation。

**禁止隐式成员**：canonical fast pytree只有上述四个 tensor。`initialized`、episode key、
next start、valid mask和 `steps_since_detach` 是 chronology owner 的控制 metadata，不是可学习
fast tensor，不注册为 parameter/buffer，不计入 model checkpoint；SiLU无参数；首版没有
normalization state、activation parameter、momentum、learned eta或额外 readout。

## 3. Slow parameter inventory proposal

下表是首版**拟议** exact registered names；形状以 `D_e=256,D_ttt=64,D_ff=128,
D_local=32,Edge hidden=2048` 计算。Edge hidden source为
`model/generator/reasoner/nemotron_3_dense_vl/configs/Nemotron-2B-Dense-VL.json:4`。

| 组 | exact registered name | shape | dtype | ordinary optimizer | model checkpoint |
| --- | --- | --- | --- | --- | --- |
| encoder | `local_history_runtime.encoder.visual_proj.weight/bias` | `[256,96]` / `[256]` | bf16 | 是 | 是 |
| encoder | `local_history_runtime.encoder.action_proj.weight/bias` | `[256,10]` / `[256]` | bf16 | 是 | 是 |
| encoder | `local_history_runtime.encoder.age_embedding.weight` | `[65,256]` | bf16 | 是 | 是 |
| encoder | `local_history_runtime.encoder.dt_proj.weight/bias` | `[256,1]` / `[256]` | bf16 | 是 | 是 |
| encoder | `local_history_runtime.encoder.norm.weight/bias` | `[256]` / `[256]` | bf16 | 是 | 是 |
| dormant readout | `local_history_runtime.readout.mlp.0.weight/bias` | `[256,512]` / `[256]` | bf16 | 否 | 是 |
| dormant readout | `local_history_runtime.readout.mlp.2.weight/bias` | `[32,256]` / `[32]` | bf16 | 否 | 是 |
| K | `local_history_runtime.recurrent_backend.key_proj.weight/bias` | `[64,256]` / `[64]` | bf16 | 是 | 是 |
| Q | `local_history_runtime.recurrent_backend.query_proj.weight/bias` | `[64,256]` / `[64]` | bf16 | 是 | 是 |
| V | `local_history_runtime.recurrent_backend.value_proj.weight/bias` | `[32,256]` / `[32]` | bf16 | 是 | 是 |
| learned W0 | `local_history_runtime.recurrent_backend.w0_fast_in_weight` | `[128,64]` | bf16 | 是 | 是 |
| learned W0 | `local_history_runtime.recurrent_backend.w0_fast_in_bias` | `[128]` | bf16 | 是 | 是 |
| learned W0 | `local_history_runtime.recurrent_backend.w0_fast_out_weight` | `[32,128]` | bf16 | 是 | 是 |
| learned W0 | `local_history_runtime.recurrent_backend.w0_fast_out_bias` | `[32]` | bf16 | 是 | 是 |
| Local adapter | `local_memory2llm.weight/bias` | `[2048,32]` / `[2048]` | bf16 | 是 | 是 |
| Local modality | `local_memory_modality_embed` | `[2048]` | bf16 | 是 | 是 |

参数计数候选：encoder `45,312`；QKV `41,120`；learned W0 `12,448`；Local adapter
及 modality `69,632`；合计 `168,512` trainable Local slow elements。另有 dormant readout
`139,552` 个 frozen、checkpointed elements，故 Local runtime/adapter 总注册元素候选为
`308,064`。配置 scalar `inner_lr` 不属于参数或 checkpoint tensor。

当前 `StatelessLocalReplayReadout` 仍作为 `local_history_runtime.readout.*` 注册但 backend
路径不调用（`local_evidence.py:297-302`）；它应为兼容 recurrent/stateless 路径保留、在
TTT optimizer 中冻结。不得使用宽泛的 `local_history_runtime` selector把这组 dormant
参数误选入。拟议四类 selector仍为：

```text
local_history_runtime.encoder
local_history_runtime.recurrent_backend
local_memory2llm
local_memory_modality_embed
```

exact count和 warm-start missing-key行为必须在后续 optimizer/checkpoint Gate 用实例化
inventory重新证明；本表不是旧 P3 authority。

## 4. Sequence action-forcing / loss audit

| authority | 当前事实 | 差距与最小 future seam |
| --- | --- | --- |
| per-item time/noise | packed B 个 item时，vision sigma为 `[B,1]`（非 diffusion-forcing），`_get_train_noise_level_vision()`一次抽 B 个值（`omni_mot_model.py:1800-1817`）；action默认取对应 item sigma（`:1930-1934`），每个 action item独立 `randn`（`:2017-2036`）。 | chronology adapter须把每个有效 `(episode,t)` 保持为一个 packed item；不得在 segment 维 broadcast。现有随机数学无需修改。 |
| native item loss | `compute_flow_matching_loss()`内部形成 `per_instance_weighted_loss[B]` 后立即 `.mean()`（`flow_matching.py:63-90`）；action调用丢弃第二返回值（`omni_mot_model.py:1586-1599`），且第二返回值当前还是未 time-weighted版本。 | 最小改动是在 loss helper暴露 time-weighted native per-instance scalar；vision/action各自保持原 channel/token/mask/time weighting，再按现有 `loss_scale=10`、`action_loss_weight=10` 合成 item scalar。 |
| valid-supervision mask | 当前 noisy condition mask只屏蔽模态内部 timestep；没有 chronology padding/context-only item mask。 | segment adapter必须产生 `outer_valid[B,T]`，只把真实、有 noisy target 的 window flatten进 numerator；padding/context-only不进入分母。 |
| accumulation/rank normalization | 当前每 microbatch先 batch mean，trainer固定除以 16（`trainer/__init__.py:484-495`）；sample-level选项也只按当前 batch/rank计数（`omni_mot_model.py:1491-1524,1642-1654`）。 | 当前只在每个 microbatch/rank valid count完全相等时偶然等价。后续需在 optimizer accumulation group上累计/预知 global valid denominator，并让每次 backward贡献 `global_numerator/global_denominator` 的等价权重；world-size因梯度平均需显式抵消。denominator=0时禁止 optimizer step。 |

KVB inner loss只驱动 state transition，不加到 `_compute_losses()`。Cosmos vision/action target、
condition mask、time weight及两项 recipe scale全部保持不变。

## 5. Inference context audit

当前嵌套图：

```text
closed_loop_eval active env slots
  -> HTTP /predict or /predict_batch（payload无稳定 rollout identity/action/done）
  -> ActionPolicyRunner._prep_policy_item()             # 普通 CPU tensors
  -> with self._lock
       -> with torch.inference_mode()                   # server :959 / :1061
            -> OmniMoTModel.generate_samples_from_batch # 自身还有 @torch.no_grad(), :2878
                 -> _prepare_inference_data()
                 -> get_data_and_condition()
                 -> Cosmos sampling
```

`generate_samples_from_batch()` 不调用训练用 `_inject_local_history()`；它只会消费调用者已
放入 batch 的 `local_memory`（`get_data_and_condition()`：`omni_mot_model.py:4210-4238`）。
因此唯一安全的最小插入边界是 server 的 lock 内、`torch.inference_mode()` 之前：

```text
ordinary observation / previous executed action / stable rollout identity
  -> frozen evidence encoder + frozen Q/K/V，输出普通 detached fp32 K/V/Q
  -> torch.enable_grad(): 仅四个 detached W leaf requires_grad
  -> one per-sample KVB update
  -> detach new W value；用更新后 W 读出并 detach Local token
  -> 写 batch["local_memory"] 并置 sequence_plan.has_local_memory
  -> 原 torch.inference_mode() + @torch.no_grad() Cosmos generate
```

现有 request schema无法提供 `rollout_id/env_id`、control step、上一步实际执行 action或
reset/done，且 vectorized loop会压缩 active slot顺序（`closed_loop_eval.py:1216-1259`）。
因此 inference persistent state 当前**无可复用 owner**；需独立设计 request schema、
server state registry、异常/超时清理、partial done reset和串行/批量等价。不得用请求行号或
HTTP request ID冒充 env identity。

## 6. Chronological sampler / state ownership audit

| 必需 authority | 当前来源/行为 | 判定与 future seam |
| --- | --- | --- |
| episode/env identity | 训练 sample由 `LIBEROLeRobotDataset._build_item()`写 `episode_index/start_frame/task_index`（`libero_lerobot_dataset.py:412-448`）；suite由 joint loader写 `dataset_name`（`joint_dataloader.py:1027-1030`）。推理端无稳定 env identity。 | 训练 key必须至少 `(suite,episode_index)`；推理需新增 rollout key。 |
| segment start/end/done/valid | 当前无 segment schema或 done字段。dataset只按 window输出。 | 新 sequence manifest/adapter显式给 `segment_id,offset,valid,is_episode_start,is_episode_end`；episode identity变化或 end authority触发整树 reset。 |
| same-episode order | map dataset flat index在 episode 内递增（`libero_lerobot_dataset.py:281-295,412-418`）；P1 builder按 shuffled episode block后逐 index生成（`tools/g0/build_r09_b2_stream_manifest.py:41-50`）。 | 可复用生成语义；现有 verifier未硬断言同 episode `start_frame+1` 和 segment边界，需新静态断言。 |
| shuffle/sampler/packing | manifest模式禁 iterable shuffle、逐 record消费（`action_sft_dataset.py:125-143,352-360`）；recipe要求 `num_workers=0,in_order=True`（`action_policy_libero_edge_all.py:160-190`）；joint loader按 suite round-robin并一次 pack最多 128（`joint_dataloader.py:953-1044`）。 | window stream可作为输入，但必须重组为完整 TBPTT segment；普通 packed B不是 state batch。 |
| worker owner / handoff | manifest wrapper拒绝 worker进程（`action_sft_dataset.py:125-127`）。 | `num_workers=0` 可形成唯一 process owner；保持 fail-closed。 |
| rank owner | P1 header固定 `world_size=1,num_workers=0`（`build_r09_b2_stream_manifest.py:145-151`），verifier检查（`verify_r09_b2_stream_manifest.py:108-123`）。 | 首版正式候选维持单 rank，唯一 owner可证明；多 rank另行 Gate，不从当前设计推导。 |
| grad accumulation / optimizer boundary | recipe `max_samples_per_batch=128`、`grad_accum_iter=16`；trainer每 microbatch backward、16次后 step。 | 每个 microbatch必须由完整 `<=16` step segments组成；segment末 detach数值后才允许该 microbatch backward。不能保留跨 backward图。state每个真实 transition恰好前进一次。 |
| epoch/drop/retry/replay | manifest记录 epoch；dataset内部加载失败会随机重试（`libero_lerobot_dataset.py:398-410`），但 wrapper随后 identity mismatch并 fail；finite manifest迭代结束后重新建 iterator会从头开始。 | 禁止随机替代；首版中断/异常整 run fail。epoch identity须参与 reset/owner key。不得无记录重放。 |
| partial reset | backend有旧 `reset_mask()`，但 production runtime从未调用；训练/推理均无 per-owner reset入口。 | chronology owner按 episode/env done mask复制完整 learned W0，其他 owner bitwise不变。 |
| checkpoint/resume | DCP保存 model/optim/dataloader/trainer，但现有 fast state既不注册也无独立 artifact；`set_start_iteration()`只调整 joint-loader suite选择（`trainer/__init__.py:320-323`），未恢复 manifest child cursor或 fast state。 | strict sequence resume首版明确非目标；中断后从 fresh run/episode重启。未来若需要，另设 detached state+cursor artifact Gate，绝不把 W_t混入 model/Adam。 |

### 6.1 当前阻塞的精确证明

现有 128-window microbatch可以在任意 episode offset处开始/结束；episode长度也不保证是
16 的倍数。若 runtime只在每 16 个 episode step detach，则 microbatch末可能留下少于 16
步的未 detach图，而 trainer已在该 microbatch立即 backward。下一 microbatch继续该 state
会引用已释放图；若强制在 microbatch末 detach，又会把 16 改成由 packing决定的短截断。

因此后续 chronology design 必须先形成**完整 segment是 trainer backward的原子边界**：
一个 packed microbatch可包含多个完整 segment，episode尾 segment可小于 16；同一 episode
的下个 segment只接收上个 segment末 detached数值。这样同一 transition只有一个 state
owner和一次 update，TBPTT语义也不依赖 128-window pack边界。

## 7. 最小实现面与 Gate 拆分

### Gate A：CPU algorithm/gradient implementation design（本 audit 通过后才可写）

冻结本文件候选值、functional API、四叶命名、W0初始化、higher-order gradient、容差、
内存预算和 exact CPU tests。预计实现锚点仅为：

- `cosmos_framework/model/generator/mot/local_evidence.py`
- `cosmos_framework/model/generator/mot/local_evidence_test.py`
- `configs/base/defaults/model_config.py`（仅新增禁用默认值，是否同 Gate由审核决定）

不接 production runtime、不跑模型/GPU。

### Gate B：chronology + native loss design/implementation

单独冻结 segment manifest/schema、state-owner API、packing映射、outer numerator/denominator、
zero-denominator和错误恢复。它至少涉及 dataset/manifest wrapper、joint loader或 model
pre-pack seam、`_inject_local_history()`及 loss/trainer adapter，必须单独审核，不能夹入 CPU
core commit。

### Gate C：受限 runtime

先 CPU integration，再单卡 bounded GPU train smoke；证明每 transition update一次、跨
segment value carry、16-step graph detach、QKV/W0收到 finite outer gradient、Cosmos原 loss
未改变。之后再另起 inference request/state-owner Gate。

### Gate D：训练 authority 重建

CPU/GPU/inference合同全部关闭后，重新生成 optimizer inventory、checkpoint/warm-start、
resolved config、A/B matched diff、P3/P4/P5 authority；旧 B2/P3/P4/P5算法绑定证据均不得
授权 v0.2.1 正式训练。

## 8. 本 Gate 验收与请求

本 source audit 已输出 v0.2.1 §6 要求的六类 exact 表，明确给出当前事实、阻塞和最小
future seam，并提出首版 `D_ttt=64,D_ff=128,SiLU,bf16 storage/fp32 inner compute,
inner_lr=0.1` 候选。审核应检查：

1. `file:line` 是否覆盖真实 production training/inference/sampler路径；
2. 四成员 fast pytree、W0 mapping、bytes和 slow inventory是否闭合；
3. 128-window pack与16-step TBPTT冲突判断是否正确；
4. native per-item noise已可复用、而 loss normalization必须加 adapter的判断是否正确；
5. inference-mode之前的插入边界及稳定 rollout identity缺口是否正确；
6. 后续 Gate拆分是否足以防止从 CPU core越权到 runtime/training。

请求 verdict：

```text
APPROVE_TO_DESIGN_R09_B_TTT_V02_CPU_ALGORITHM_IMPLEMENTATION
```

或带 `file:line` 的 `REQUEST_CHANGES`。批准仅允许下一步编写 CPU algorithm/gradient
implementation design；仍不授权 Cosmos实现、torch runtime、GPU、训练、评测、推理、
optimizer/config refreeze、P4/P5真实操作或 B2-T。
