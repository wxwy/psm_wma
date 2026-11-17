# G2 B 公共接口、UND／联合 K/V 与固定源码集成交接

2026-11-17（Asia/Shanghai）。**源码／CPU集成候选已完成，待独立审核与真实执行；不是GPU/FSDP/训练批准。**
总任务[#56](https://github.com/wxwy/psm_wma/issues/56)，Root Draft #60，Child Draft #17。不自动推广V3/v3-local-ttt。

## 固定来源

| 阶段 | Root | Child / Gitlink | 范围 |
|---|---|---|---|
| 刷新后的正式基线 | 7a357620b4cc1f6817749c8a8275771cfbb4049c | d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2 | 保留190ea2e2后的新引用，不回退 |
| C0 | 739d39cf6498543b59d487d5925ef2a329040ac3 | ec9356fafd1fd18cc0bd552b7eb23428f59df7f6 | 公共合同／fixture，作者11 CPU PASS |
| B core | 4f90c875eda0ca53d997f64111b41ed531ac2900 | 7e888f217dfcddc35ed73782f65c6e0890c72c3a | UND／joint prefix／配置／FSDP，198 scoped CPU PASS |
| 历史部分集成 | b7ea01d71131189dd9c5b38f2857f9f4009e3b9c | 6d72d4d252c287fc8060bdc5a8db7f6cf959af1e | 当时C阶段待交付；442 scoped CPU PASS |
| **最终源码／CPU集成** | **本文当前Root提交；完整SHA见#56发布回执** | **9370c3858532b4d61630138431145c8360e86eb0** | **636 PASS / 1真实资产preflight SKIP / 0fail/error** |

以上都是独立固定来源，不以文档后继或测试数之和替换代码身份。B-core工作区 `/workspace/work/g2-b-core`、分支
`v3-g2-model-b-core-20261117` 保留；集成在 `/workspace/work/g2-integration`、两仓 `v3-g2-model-integration-20261117`。
正常merge/push，无force push、无服务器执行仓commit/push、无正式分支合并。最终Root唯一绑定上表Child。

| 路线 | 最终Child来源 | Root交接／原始证据来源 | B的处理 |
|---|---|---|---|
| A | 4209b151ecc11ab2043b9d08037d43b5e3903618 | 35a2580efd296bcf782d7cae38d4cb482a225a70 | 普通合入，4个Reader/spatial及测试blob保持 |
| C | 26243dae9be7a2ab7ef5d544f8759b398ce917f9 | 343421d6c2fb78d577739e118dbd600021c991d2 | 含68d84e8/f262d7ff/a9110f3及显式horizon；普通合入 |
| D | 6991142cb94256f497347db40f58ad0ee3f482aa | 0be8fd36b28fca81ce7343c7bd7ab1c673d94783 | 含初批209749e，hooks/cache/server及runbook普通合入 |

A/C/D所有唯一归属文件逐blob核对、祖先关系和scope diff见 `artifacts/g2_model_integration_final/`。
B没有手改A Reader、C formatter/trainer、D cache/server；新增接线和组合测试都在B归属。

## 唯一公共模型 ABI 与主干行为

导入 `cosmos_framework.model.generator.mot.g2_contracts`；C0 dataclass保持唯一来源。
[C0字段/几何/版本/归属合同](../../../build/PSM-WMA_G2_C0_Public_ABI_2026-11-17.md)、
[B core方法/配置/参数inventory/FSDP合同](../../../build/PSM-WMA_G2_B_Core_ABI_2026-11-17.md)。

- `EffectiveTextBatch` 是最终native causal UND span，包含实际BOS/EOS/start_of_generation与mRoPE、一次dropout身份。
  **使用整个frozen/hashable实例或完整字段签名，没有 `.identity` 属性。** 尾部EOG若存在仍在原full split。
- `G2ConditionBatch(text,views,...)` 同时用于 `training_step(...,_g2_condition=...)`／`data_batch['g2_condition']`
  以及 `generate_samples_from_batch(...,_g2_condition=...)`；原Local kwargs保留。native pack逐项校验tokens/positions/lengths。
- 一次冻结UND前向复用原生embedding、RoPE、causal attention、MLP、post-norm；给A逐token hidden及各层UND base KV。
  GEN读取时在当前GEN key norm和RoPE下转换，训练不detach该norm，不拿独立reasoner原始KV直接充GEN缓存。
- A实现64×512/8heads/FFN2048，语言1轮、视觉2轮，每轮memory SA＋FFN；B只注册／reset／调用A。
  所有GEN层使用各自现有GEN KV投影／norm，布局 `[Global;Local;Text;NativeGEN]`，只加K/V，不加Global/Local主干Query。
- Global/Local各自projector/modality、presence/length/offset独立。`k_local`只表示Local；Global不存在即零长度，
  不留零token。Global配置off不构造Reader、无新增初始化RNG，旧none/Local-only语义保留。
- GEN参数冻结仍有Global输入反向图。Global-enabled训练在全Global缺席rank／空语言CA分支增加标量零图依赖，
  不增加prefix/query、不运行缺席Reader；这是保持相同反向units/梯度清单的必要前提，实际FSDP仍需执行侧验证。
- Omni公开 `prepare_g2_text`、`prepare_g2_gen_text_kv`、`prepare_g2_task_queries`、`read_g2_global`、
  `project_g2_global`、`prepare_g2_global_kv`；`prepare_g2_condition`在采样循环前一次准备，FSDP root/层方法有注册。
  `g2_parameter_inventory()`给互斥完整names/new_state_keys，`set_trainable_names()`在resharded/zero-grad边界刷新flags/FSDP bookkeeping。
- D使用唯一 `stack_g2_prepared` 合批B1快照；有prepared Global tokens即可保持presence而不重载views。旧C版本不同opaque
  dropout IDs可组合hash保留；C最终v2改为策略身份，实际决定在dropped。训练不接旧GEN KV／预投影Global快照。

## C 训练与 D 服务实际接线

C最终 `TEXT_PROTOCOL=psm_g2_static_initial_text_v2`；共享JSON显式标初始空间上下文，R1/R2实际删除idle字段。
训练0.1 dropout一次决定；服务False；不重tokenize另一套文本，不读取当前state/SG/未来action生成静态事实。
原Dataset消费DATA_B state15／DATA_C provider，保留原raw15未来标签及EEF10，R1不访问Global资产。

C严格G1 model-only加载全部旧GEN/UND/适配器/Local键与shape，只允许B精确新增Global state初始化，不笼统strict=False；
不导入旧G1 optimizer/loader/RNG/live fast state。原optimizer factory预注册Global/GEN/action组，TRAIN_A冻结GEN、lr/wd=0；
TRAIN_B解冻GEN/动作，Global moments/clock保留。GEN/动作配对schedule含显式 `horizon_steps`，不按R1/R2总预算暗自缩放。
阶段只在完整GA backward→optimizer成功→Local/frontier commit→zero-grad后切换，scheduler与Local sidecar交叉核对恢复。
R1保留S_B和S_A+S_B，R2保留S_A边界和最终；主预算按实际committed consumers，另报GEN更新次数及计算成本。

D复用原Policy Server和Session/Batch事务，缓存同Session固定权重的view、UND/textKV、task queries、Reader/projected Global及各层GlobalKV。
完整key是C0签名加D唯一 `OnlineSpatialSnapshot.mask_content_ids` 实际bool mask SHA，view/global key都绑定、miss校核。
B未发布重复mask字段。owner/frame留作来源，不因仅owner/frame前进强制失效；未选中图不进key。有界预算/pin/异常释放保留。
权重原位/替换/config变更失效。**D Session cache构造和请求均拒绝world_size>1，含cache-off**，不声明分布式缓存支持。

首版G2明确guidance=1；CP/CUDA Graph/multiview/multi-control/旧MemoryState和未验diffusion-layer residual cache有显式边界。
没有全局关闭既有G1优化。当前C单Room adapter恰一mandatory top；Reader只验非空同variant。未来多Room的top基数/覆盖及真实数据
语义未验，不从可变view fixture推断未来能力，不在模型恢复场景或重判更新阈值。

## 最终单轮 CPU／静态证据

`artifacts/g2_model_integration_final/pytest.log`／`junit.xml`：**636 PASS、1 SKIP、零失败／错误，30模块，37.98s**。
唯一skip是旧 `test_optional_real_strict_snapshot10_preflight`，未提供真实exact-window cache/source/Edge/base/VAE路径；不删skip或放宽断言。
不与C0/B-core/442或A/C/D作者的56/405/361等重叠运行相加。

13项B-owned组合测试包括实际A Reader/projector、B native pack／MoT／vision-action头、C文本与控制器、D runtime/hooks：
正常/空文本与packing/pad，Qwen/Nemotron FP32/BF16 hidden/baseKV/GEN可比；全层G/L长度/presence、B1/mixed样本隔离；
冻结GEN的动作loss→Global，真实CPU Local core；两Session三轮replan cache-on/off结果进native动作头；严格加载无Global的G1状态，
TRAIN_A→B后恢复模型／optimizer／阶段／RNG与连续运行逐项相等、Local权重不变。
C原grouped/Local/GA/sidecar、真实单进程CPU DCP、2-rank Gloo、旧Phase5/No-TTT和D Session/Batch回归同轮运行。
Gloo不是FSDP，直接控制器/native-head fixture不是完整真实训练步；生产attention仍走项目dispatcher，测试只替换CPU参考kernel。

旧C0源码none/Local-only×B1/mixed输出、梯度、构造/forward RNG逐位相同；B保留legacy QKV/norm staging。
最终主要B文件strict Ruff/format通过，C/D作者static原始证据保留，旧文件仅保留已证明的I001债务。
失败迭代保留：C阶段组合测试初轮漏import、fixture设fused=False违反原optimizer要求，修为原生fused=True后通过；没有改生产optimizer。

## 精确复现与执行侧待定项

CPU小例（Child cwd）：

```bash
CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu LD_LIBRARY_PATH='' PYTHONPATH=. OMP_NUM_THREADS=1 \
 /workspace/.venvs/psm-wma-cpu/bin/python -m pytest --noconftest -o addopts='' \
 cosmos_framework/model/generator/mot/g2_integration_test.py -q
bash ../artifacts/g2_model_integration_final/run_cpu.sh
```

Python可用G2_CPU_PYTHON替换。源码须先checkout #56发布的固定Root，并检出其Gitlink；镜像不可用时可临时用
`git -c submodule.cosmos-framework.url=https://github.com/wxwy/cosmos-framework.git submodule update --init cosmos-framework`，不修改.gitmodules。

真实现有训练入口与fresh/resume完整参数模板：
[C runbook](2026-11-17_G2_Model_C_Training_Handoff.md#可执行-runbook)。不是新训练loop。
`examples.psm_wma_robocasa_g2_recipe --check ... --pair-with ...`只校验配置；真正Phase5 CLI含 `--g2-recipe`。
**smoke recipe内grad_accum_steps=1**，仅CLI --ga 1不够；正式batch/GA/预算待实测。

真实现有B1/mixed-B2、cache-on/off、EMA、lease/manifest/slot及factory命令：
[D server runbook](../evidence/2026-11-17_g2_model_d_inference/SERVER_RUNBOOK.md)。不另建服务。
provider及已验证loaded-weight/config versions factory未冻结，runbook显式BLOCKED，不拿fixture路径或task名充实际来源。

执行侧须填写：完整G1 checkpoint receipt/shard身份及metadata SHA、G1 config SHA、DATA_B/C清单／划分／alignment／state15／view/VAE recipe、
tokenizer与静态文本模板、geometry/membership/mask版本、当前rollout provider与初始化GT绑定、FSDP/batch、S_A/S_B、各组warmup/decay/min/horizon、
实际consumer目标、保存间隔、cache预算／loader factory。模板null值拒绝启动；DATA_A/B/C与TRAIN_A/B不混称。

真实样例至少保存：>=3 decision windows，B1/mixed-B，UND/native parity、全层prefix、动作梯度、Local inner/commit-abort、所有rank FSDP前后向、
TRAIN_A/B真实DCP边界恢复（模型/optimizer/Local/RNG）、cache on/off逐步输出和Session隔离。使用固定pair、同runtime/input/RNG和预先声明数值标准。

## 未运行／未批准

真实G1/Edge/Wan权重与DATA_B/C对齐、GPU attention/BF16/compile物化、实际FSDP／GPU阶段恢复、真实服务/rollout/仿真/闭环/SR、正式训练和900EP均NOT_RUN。
执行侧既有任务未停止、环境未升级、私有数据未外传。#52/#53旧VAE核心及人审PASS继承，不重复；#54仍为限定A2通过，完整生产/state15/联合对齐未就绪。
源码集成／CPU REVIEW不等于执行批准；M08/M09与真实运行参数继续待实测，不自动合并正式分支。
