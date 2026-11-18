# G2-C：共享文本、数据适配、G1 warm-start 与两阶段训练交接

日期：2026-11-17（Asia/Shanghai）。状态：候选实现交 B 集成；作者 CPU/static 证据，不是独立审核结论或训练启动许可。

## 固定来源

- 开工及交付时 Root 远端 V3：`7a357620b4cc1f6817749c8a8275771cfbb4049c`；正式 Gitlink 始终为 `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`。
- 历史设计锚点：Root `190ea2e2b674bcb18dea4701c8a27d1e16d40ccb` / Child `d5c1ffc7`。未回退后继提交。
- **最终 Child：`26243dae9be7a2ab7ef5d544f8759b398ce917f9`**；分支 `v3-g2-model-c-training-20261117`；[Child Draft #18](https://github.com/wxwy/cosmos-framework/pull/18)。
- 固定依赖/PR base：`6d72d4d252c287fc8060bdc5a8db7f6cf959af1e`，只读分支 `v3-g2-model-c-training-deps-20261117`，包含 B C0 `ec9356fa`、B core `7e888f21` 及后继集成、A `4209b151`、D `6991142c` 和 B 已吸收的 C 首批。
- C 原创提交：`68d84e819d114c6ce817403afacad994b2fb8f35`（文本/idle）、`f262d7ff4156d83356e1d7f790adea2a61e85c6d`（native span/adapter）、`a9110f311f082836e9f1a56466bae66aca88e488`（训练/恢复）、`26243dae`（显式配对 LR horizon）。其余 merge 是原作者依赖，没有手改 A/B/D 文件。
- [开工 ACK](https://github.com/wxwy/psm_wma/issues/56#issuecomment-6943519070)。已按 AGENTS→SESSION→canonical live Inbox→TODO→MEMORY/DECISIONS→v2.2/build plan→Child AGENTS 阅读。现行 V3/Owner 授权覆盖旧 V2 三方实施门；读取执行治理技能仅用于交付边界核对，没有启动执行或申请 GPU 批准。
- Root 候选仅保存路线文档/证据，不提交 Gitlink，不覆盖 TODO/SESSION/Inbox。B 统一集成和公共账本。隔离目录 `/workspace/work/g2-c-training`，原活动工作树不变。

相对固定依赖的后继 diff 仅 **16 个 C 文件，2227 additions / 18 deletions**；见 [patch](../evidence/2026-11-17_g2_model_c/c_after_B_6d72.patch)、[原创提交历史](../evidence/2026-11-17_g2_model_c/c_owned_history.txt)。model/inference/scripts 保护目录与依赖完全一致，30 个受保护依赖 blob 有记录。

## 文件与现有入口

以下位置均指[最终 Child](https://github.com/wxwy/cosmos-framework/tree/26243dae9be7a2ab7ef5d544f8759b398ce917f9)，action 路径前缀为 `cosmos_framework/data/generator/`。

| 文件/位置 | 增量职责 |
|---|---|
| `action/utils/json_formatter.py:68`、`transforms.py:582` | `append_idle_frame_text` 开关；G1 默认不变，JSON/plain 都实际受控 |
| `action/utils/static_task_text.py:38`、`:101`、`:144`、`:189` | 静态任务资产、共享序列化/tokenizer、native 最终 span；不执行 UND |
| `action/datasets/g2_training_adapter.py:24`、`:56` | 注入 provider，消费 DATA_B state15 / DATA_C 选图，不实现转换/producer |
| `action/datasets/robocasa_exact_window_cached_sft.py:54`、`:187` | 原 Dataset 的可选 adapter/recipe；复用 exact-window/raw15/G1 latent/样本身份 |
| `data/generator/joint_dataloader.py` | 原 native collate 保留 mask/positions/身份/view 对象 |
| `trainer/g2_training.py` | 原生 optimizer 名称解析、分组、阶段 scheduler/policy、实际计数与比较 |
| `trainer/local_memory_grouped.py:291`、`:399` | view 搬运、`G2ConditionBatch`、完整 GA/optimizer/Local 边界提交 |
| `trainer/local_memory_grouped_resume.py:216` | 原 Local/frontier/RNG sidecar 外加阶段；旧 G1 schema 不变 |
| `checkpoint/g2_warm_start.py:23`、`:79` | 严格 model-only inventory/shape 校验后复用 SafeLocal DCP |
| `examples/psm_wma_robocasa_corrected_phase5.py:1297` | 原入口新增 `--g2-recipe`，默认仍走旧路径 |
| `examples/psm_wma_robocasa_g2_recipe.py`、`.template.json` | 配置 overlay、B inventory/hook 接线、实际参数清单；没有新训练 loop |
| `trainer/__init__.py:432` | 原事务保存点额外保留比较 checkpoint |

新增相邻测试在 `static_task_text_test.py`、`g2_training_adapter_test.py`、`trainer/g2_training_test.py`、`g2_grouped_integration_test.py`、`checkpoint/g2_warm_start_test.py`、`examples/psm_wma_robocasa_g2_recipe_test.py`。未复制 Dataset/Formatter/Trainer/Reader，未改 B 模型/FSDP、D 服务、A Reader 或离线 producer/Pose5 转换。

## C→B/D 共享文本合同

协议为 **`psm_g2_static_initial_text_v2`**。同一 Atomic episode/子任务的 `StaticTaskText` 由离线 provider 提供一次：原始/增强指令、episode/subtask、template/source/initial-context 身份，`context_scope="initial_spatial_context"`。C 不从当前 state/SG 或未来 action 合成增强事实。

共享 JSON 用现有 formatter，action 项明确写 `spatial_context_scope=initial_spatial_context`，删除 `idle_frame`。planned frames/fps/resolution/viewpoint 来自固定 `StaticTaskTextRecipe`，不从 clean state 行数、action 长度或 idle 统计推断。真实 action 标签和其他仍需的 idle 统计保留。

```python
from cosmos_framework.data.generator.action.utils.static_task_text import (
    prepare_static_task_text, effective_text_batch, effective_text_mask,
    resolve_consumer_text_dropout,
)
# training consumer materialization: decide once; replay keeps this bool
dropped = resolve_consumer_text_dropout(sample, recipe.cfg_dropout_rate)
sample.update(prepare_static_task_text(task, recipe, processor, dropout_applied=dropped))
# serving uses the same preparation with dropout_applied=False
text = effective_text_batch(
    [sample], recipe, special_tokens=model.llm_special_tokens,
    use_float_positions=model.config.diffusion_expert_config.enable_fps_modulation,
)
mask = effective_text_mask(text)
```

`processor` 为原 `TextTokenizerTransform._processor`，真实调用 `.tokenize_text(..., is_video=False, use_system_prompt=recipe.use_system_prompt)`。`text_token_ids` 保持原 native packer 所需的 tokenizer IDs；`effective_text_batch` 用同一个 `PackedSequenceBuilder.pack_text_tokens` 和实际 `model.llm_special_tokens`，提供**含 BOS/EOS/start-of-generation 的最终 IDs/native 3-axis mRoPE**。不能把原始 IDs 直接当最终 UND span。mask 为 right-padding validity；B 按 lengths 使用。最终条件身份是 `EffectiveTextBatch.identity`，不是原始 tokenizer 阶段的诊断字段。

`dropout_id` 仅表示 `consumer_once_v1+rate` 策略，实际决定在 `dropped`，所以 B `stack_g2_prepared` 可组合完整/空文本 B1 Session。相对 f262，v2 scope/策略身份会改变 formatter/条件身份，应按最终依赖重建服务缓存；函数签名不变。D 已有 adapter 直接调用共享函数，C 没改 server。

训练给 B `data_batch["g2_condition"]=G2ConditionBatch(text, views=...)`，R1 的 views 全为 `None`。B 的真实 UND 产生一次 features，Reader/GEN 共享；C 不预跑另一网络，不缓存训练转换 KV。空条件是真实 `tokenize_text("")` 后 native packing，不将完整 hidden 乘零。文本 dropout=0.1，重算不再抽样，不增加 Global/Local 整支路 dropout。

## 正式数据 provider 接口

`provider_factory="module:function"` 由配置注入，factory 收 `global_memory_enabled=bool` 并必须遵守 R1 lazy 关闭。通用 Cosmos 不反向 import 根仓 tools/仿真 producer；入口拒绝 `tools*`、`g2.offline*`、`g2.sim*` factory。正式入口要求 `identity==training.data_identity`、`evidence_scope=="verified_data_c"`、`split_identity==training.split_identity`；fixture 不准用于正式启动。

| provider 接口 | 内容 |
|---|---|
| `read_common(task_class, episode_index, decision_frame)` | `identity:G2SampleIdentity`、`static_task_text:StaticTaskText/dict`、`state15:CPU fp32[15]`、原 task/episode、`source_binding_digest`、`state15_space="data_b_model_input"` |
| `read_selected_views(identity, top_view_variant=...)` | 当前选中 `tuple[SpatialView,...]`；实际 latent/几何/resize-pad/mask/版本/owner 身份。R1 不解析或调用此方法 |
| `latent_channels` | R2 只读 VAE recipe 小元数据，传 B model config；R1 不访问 |

adapter 校验 exact decision frame、logical frame 因果、data/alignment/state15 recipe、原指令/初始文本/source binding，拒绝 Atomic episode 内换 subtask 隐藏文本漂移。state15 前 5 维来自 DATA_B；后 10 维须与原 EEF10 完全一致。仅替换 `action[0]`，未来真实 raw15 labels `action[1:]` 不改，既有 pad/action 处理继续复用。

R2 只加载选中 view，拒绝版本错误/非有限 latent/future owner/重复 view/错误 top variant。正常不存在方向由 provider 从 selected tuple 省略；已声明资产损坏的异常原样传播，不填假 latent。当前 adapter 要求一个 selected top；未来多 Room 多 top 合同改变先交 B/A/离线侧统一，不猜路径。logical/physical owner 差异保留；不读取未来 SG/专家未来图。

**DATA_B/C 未交付**：#54 最新回执仍将 state15/联合对齐列为待办。现有代码是正式 provider 的薄消费接口；测试显式 `fixture`，不是一份冒充正式 provider 的实现。真实数据对齐 **NOT_RUN**。

## Warm-start、阶段与恢复

同一已验证 G1 model-only checkpoint：校验全部既有 GEN/UND/动作与视觉适配/Local keys 和 shape，仅允许 B 声明的新增 `net.global_memory_reader.*`、`net.global_memory_projector.*` 初始化。缺旧键、shape 不符、额外未知键均加载前拒绝。CPU reference 最后 `strict=True`；DCP 核实 metadata 后用精确 Global allowlist 复用原 planner，不笼统 `strict=False`。

不导入旧 G1 optimizer/scheduler/loader/RNG/episode fast state；新 job 按原规则初始化 Local live state。G2 不沿旧 fresh 的 `local_memory` skip。`init_checkpoint_identity` 当前是 `model/.metadata` SHA256，绑定执行侧已验收 checkpoint receipt；它本身不是所有 shard 内容 checksum，正式权重来源/完整性仍须执行侧已验证资产清单，本轮未读真实 checkpoint。

| 配置/阶段 | 可训练组 | 峰值 LR |
|---|---|---|
| R1 | GEN＋action adapter；Global off，`g2_text_enabled=True` | GEN `1e-5`；动作三项 `5e-5` |
| R2 TRAIN_A | 新 Global Reader/spatial/projector | `5e-5` |
| R2 TRAIN_B | 原 Global＋GEN＋action adapter | Global `5e-5`；GEN `1e-5`；动作三项 `5e-5` |

动作项为 B inventory 的 `action2llm/llm2action/action_modality_embed`。GEN 用 B 实际 inventory（含普通生成适配、`k_norm_und_for_gen`），不用旧 G1 子串漏项。互斥且每个应训练参数恰好归组一次。UND/VAE/Local outer 不进 optimizer；A 期预注册 GEN，但冻结/无 grad/lr/weight_decay=0。Local inner autograd/fast update 继续运行；inner_lr 等、原 loss、optimizer betas/eps/decay/fused 与 callbacks 从 SHA256 绑定的 G1 config 继承，不另选算法/目标。

`GroupSchedule` 必填 `warmup_steps/decay/min_factor/horizon_steps`，按本组已完成 updates 计时。GEN 在 B 独立 warmup；Global clock/moments/step 跨 A/B 保留。R1/R2 共享 GEN/action schedule 完整参数（含 horizon），同 GEN 更新次数下 LR 序列一致；短运行截取声明曲线，超出 horizon 保持 min，不按各自总时长重缩放。

GEN forward 不包 `no_grad`。最后 GA backward 后 `prepare_commit` 对齐 rank 阶段/计划/clock，SUM 实际 valid payload 个数，预算在 optimizer mutation 前校验。原 optimizer 成功→原 Local/frontier commit→zero_grad→stage commit，只有完整边界可 A→B。只调用 B `set_trainable_names`，不换 Parameter/optimizer，不清 Global/data/RNG/Local/frontier；底层 FSDP 注册/reshard/解冻仍归 B。

同 job 保存 `psm_g2_training_stage_v1`，原 Local sidecar 外包 `psm_g2_grouped_stage_v1`；恢复比较 scheduler/Local sidecar 的阶段、plan/参数身份、各组 updates/实际 consumers 和 iteration。缺失/冲突即拒绝，不从 step 猜阶段。G2 off 时保留原 G1 sidecar/schema/path。

R0 不新增训练。R1 保留 `S_B`、`S_A+S_B`；R2 保留 `S_A` 边界及最终 `S_A+S_B`。`validate_comparison_plans` 校验共同 init/data/split/text/state15/LR/预算；`validate_actual_comparison_budget` 用已提交实际 counter 比主预算，不用 nominal batch/step。辅助取同 GEN updates；时间/显存等计算成本从原 telemetry 另报。

## 固定 CPU 证据

**最终 405 PASS、1 SKIP、32 subtests PASS，零 FAIL/ERROR，22 模块**；[原日志](../evidence/2026-11-17_g2_model_c/final02/pytest.log)、[JUnit](../evidence/2026-11-17_g2_model_c/final02/junit.xml)、[summary](../evidence/2026-11-17_g2_model_c/final02/summary.json)、[模块清单](../evidence/2026-11-17_g2_model_c/final02/test_modules.txt)。数量不与前序或 A/B/D 作者结果累加。

| 必需覆盖 | CPU 范围 |
|---|---|
| 旧 formatter golden、JSON/plain idle 开关 | 新静态文本测试＋原 transforms，旧断言未削弱 |
| future action/window/current SG/state/clean 行数不改非 dropout tokens | shared pipeline、固定 planned recipe、显式 synthetic processor |
| 训练/服务序列化/tokenizer/final specials/mRoPE/空文本 | shared helper＋B native packing＋D 实际 hooks/Session/cache 组合 |
| 一次 dropout/重算/混合正常与空文本 | 存 bool 再调用不 draw，B carrier stack |
| R1 不访问 Global | provider 对 view method/payload/channels 访问即抛错；B 小模型不建 Reader |
| warm-start 全 Local/缺键/shape | 小模型 strict load＋真实单进程 CPU DCP metadata/planner；分布式 shell 为替身 |
| 分组完整/冻结无 decay | CPU AdamW 非零 decay、原生 OptimizersContainer/DCP state；B inventory keynorm |
| TRAIN_A Global 经冻结 GEN 梯度 | A 实际 Reader/projector＋tiny B MoT/reference attention；另 B native action-head 集成 |
| Local slow 冻结/inner 仍变 | 实际 ContinualTTTLocalMemoryCore、原 grouped scan |
| A→B moments/data/RNG/Local/frontier/所有 rank | 原 grouped/planner/producer/事务、GA/terminal 实际计数；2-rank **Gloo** 合计/分歧拒绝，非 FSDP |
| 边界前/正好/后恢复/旧配置 | 1/2/3 of 4 更新的完整状态相等；缺/冲突 sidecar 负例；旧入口/Local 回归 |
| 配对 LR/正式配置缺失 | R1 更长预算与 R2 B 段实际 GEN/action LR 相等；缺 horizon/正式值拒绝，模板 exit 2 |

实际参数清单（均逐项列 name/shape/numel/group/trainability/LR）：

- [CPU fixture A/B](../evidence/2026-11-17_g2_model_c/final02/actual_cpu_fixture_parameter_inventory.json)：30 Parameters；Global 4/40 elements、GEN 2/20、动作 5/29、冻结 19/186。
- [A Reader＋tiny B](../evidence/2026-11-17_g2_model_c/final02/actual_a_reader_tiny_b_parameter_inventory.json)：139 Parameters；Global 71/11,898,416 elements、GEN 37/7,096、动作 2/80、冻结 29/8,048，附实际 TRAIN_A grad 标志/范数。该组件使用 synthetic loss，不冒称完整 Edge/action loss。
- 完整 Edge/FSDP inventory **NOT_RUN**。真实入口在 checkpoint load 前写 `g2_parameter_inventory_before_load_rank_N.json`，完成后写 `g2_training_result_rank_N.json`，执行侧核对真实清单，不能用小模型替代。

复用现有 Python 3.12 / Torch `2.10.0+cpu` / Transformers `4.57.1` / pytest `9.0.2` / Ruff `0.12.7`，未安装/升级依赖。19 个 C Python 文件 lint/format/syntax PASS，1149 tracked source/config 指纹前后相同，30 保护 blob 一致。唯一 SKIP 是旧 `test_optional_real_strict_snapshot10_preflight` 缺真实 source/cache/Edge/base/VAE 路径。

`author_iterations/` 保留早期失败：fixture 缺字段、mask collate wrapper、旧 source-string 回归、误读 B tuple 返回值及对应修复。`final01` 是 a911 的 404 PASS 旧证据，之后显式化配对 LR horizon；**最终只认 final02**，不合并计数。

## 可执行 runbook

### CPU 复现

在 Root 候选目录，Child 为最终 SHA，指定现有环境和**不存在**的输出目录：

```bash
G2_C_PYTHON=/path/to/existing/env/bin/python \
G2_C_RUFF=/path/to/existing/env/bin/ruff \
G2_C_EXPECTED_CHILD=26243dae9be7a2ab7ef5d544f8759b398ce917f9 \
G2_C_EVIDENCE_DIR="$PWD/work/g2_c_cpu_recheck" \
bash docs/collab/codex/evidence/2026-11-17_g2_model_c/run_cpu.sh
```

脚本拒绝覆盖证据，检查 clean SHA/保护目录，记录环境/source before-after，跑 22 模块/参数导出/旧入口 help/不完整 recipe exit 2。PASS=非 skip CPU 用例全通过、零 error、源不变；缺依赖/源不符 BLOCKED，失败保留日志，不改环境。作者 Root 不改 Gitlink，CPU 脚本允许此状态；真实入口必须是 B 已固定匹配的 Root/Child/Gitlink。

### 执行侧真实入口（本轮未执行）

复制 Child `examples/psm_wma_robocasa_g2_recipe.template.json` 为独立 R1/R2 JSON，填齐 null：已验收 G1 checkpoint metadata/完整 receipt、SHA256 绑定 G1 config、DATA_C factory/划分/对齐/state15/view recipe、tokenizer/固定生成尺寸时长、`S_A/S_B`、实际 consumer 目标、batch/GA/world、各组 warmup/decay/min/horizon、保存间隔。R1 Global off/global_schedule=null，R2 on，共享字段配对校验。**smoke 的 recipe 内 grad_accum_steps=1**；仅 CLI `--ga 1` 不够，因为 recipe 覆盖 CLI。不使用 fixture 值冒充正式最优值。

仅配置校验（不建模型/provider、不训练）：

```bash
cd "$G2_ROOT/cosmos-framework"
"$G2_PYTHON" -m examples.psm_wma_robocasa_g2_recipe \
  --check "$G2_R1_RECIPE" --pair-with "$G2_R2_RECIPE"
```

以下为真实存在的原 Phase5 CLI；变量由 B 固定集成 pair/执行方案提供，无 GPU 数量/checkpoint/步数默认。fresh=model-only G1 初始化；resume=同 job 所有状态恢复，recipe/源 pair/namespace 不变：

```bash
cd "$G2_ROOT/cosmos-framework"
: "${G2_TORCHRUN:?existing environment torchrun}"
: "${G2_ROOT_SHA:?B integrated Root with matching Gitlink}"
: "${G2_CHILD_SHA:?B integrated Child containing this candidate}"
: "${G2_WORLD_SIZE:?must equal recipe.training.world_size}"
: "${G2_PHASE:?fresh or resume}"
: "${G2_RECIPE:?completed R1 or R2 JSON}"
: "${G2_JOB:?r1_g2_ or r2_g2_ namespace; same for resume}"
"$G2_TORCHRUN" --nproc-per-node="$G2_WORLD_SIZE" \
  -m examples.psm_wma_robocasa_corrected_phase5 \
  --phase "$G2_PHASE" --g2-recipe "$G2_RECIPE" --job-name "$G2_JOB" \
  --output-root "${G2_OUTPUT_ROOT:?new output root}" \
  --source-root "${G2_SOURCE_ROOT:?verified raw15 source}" \
  --cache-root "${G2_CACHE_ROOT:?verified G1 exact-window latent cache}" \
  --dataset-index-root "${G2_DATASET_INDEX_ROOT:?prebuilt verified index}" \
  --edge "${G2_EDGE:?verified Edge checkpoint directory}" \
  --vae "${G2_VAE:?verified VAE file}" \
  --base-checkpoint "${G2_G1_CHECKPOINT:?same validated G1 DCP}" \
  --root-worktree "$G2_ROOT" --expected-root "$G2_ROOT_SHA" --expected-child "$G2_CHILD_SHA" \
  --ga 1 --num-workers 0 --transform-rng-mode legacy_global
```

真实 preflight 用上述同一参数加 `--preflight`：读取真实资产/索引/tokenizer、校验源锁，不替代 forward/backward。作者 Root 候选 Gitlink 仍 d5，直接执行会按源锁拒绝；须由 B 先固定集成 pair。

真实 Gate 至少验证完整 warm-start/参数 inventory、真实 action loss→Global 梯度、冻结不变/Local inner 更新、FSDP 所有 rank 的 A→B 注册/reshard/collective、真实 DCP 边界恢复、DATA_B/C identity/state/view 因果对齐、R1 不开 Global 大资产、实际 consumer 主预算与 GEN updates 辅助比较。NaN/缺梯度、预算漂移、损坏资产或身份不符停止并留证据；CPU Gloo/名义 batch 不能替代。

## NOT_RUN

真实 G1/Edge 权重、正式 provider/真实 state15 联合对齐、完整 Edge 参数清单、CUDA/BF16、真实 FSDP/多 rank GPU 阶段切换恢复、正式 R1/R2、全量评测均 **NOT_RUN**。本轮没有 GPU 任务、环境升级、旧 checkpoint/数据改写、正式分支合并或 Gitlink 变更。B 以最终固定集成 pair 复验，不把本路线作者 CPU 结果作为执行批准。
