# PSM-WMA G2 M08 固定源码执行交接 v1.0

状态：**执行准备文档；M08/M09 TODO，所有真实运行 NOT_RUN。** 日期：2026-11-17 CST。
本轮只整理已有入口、验收条件和缺件，不增加模型功能、重跑 CPU 或启动 GPU。
执行侧尚未对本交接 ACK，不把发布文档写成已开工。

## 1. 唯一执行对象与已知证据

| 身份 | 固定值 |
|---|---|
| 模型源码 Root | `41464b051ef8e02711dbfa37d379d2b14c7c57f4` |
| Child / Root Gitlink | `9370c3858532b4d61630138431145c8360e86eb0` |
| 候选 | [Root Draft #60](https://github.com/wxwy/psm_wma/pull/60)、[Child Draft #17](https://github.com/wxwy/cosmos-framework/pull/17) |
| A / C / D 最终 Child | `4209b151ecc11ab2043b9d08037d43b5e3903618` / `26243dae9be7a2ab7ef5d544f8759b398ce917f9` / `6991142cb94256f497347db40f58ad0ee3f482aa` |
| 本文来源 | 单独 Root docs 分支 `v3-g2-model-m08-handoff-20261117`；其提交号仅标识文档，不替换上面的模型 Root |

[B 最终交接](../collab/codex/reviews/2026-11-17_G2_Model_B_Core_Integration_Handoff.md)及
[最终作者证据](../../artifacts/g2_model_integration_final/README.md)保留原始日志、JUnit、scope diff 和 36 文件来源核对。
唯一最终单轮结果是 **636 PASS / 1 SKIP / 0 fail/error**；skip 为原真实资产 preflight 缺路径。
这些是作者 CPU 结果。Owner 侧 [#56 回读评论](https://github.com/wxwy/psm_wma/issues/56#issuecomment-6945927554)
确认源码来源与已存证据，审核类型为 COMMENT；没有独立重跑 CPU、GPU/FSDP 或执行批准。

正式 V3 本次只读刷新仍为 `7a357620b4cc1f6817749c8a8275771cfbb4049c`，
正式 Gitlink / Child `v3-local-ttt` 仍为 `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`。
本文不推进上述分支，也不将任意后继 docs HEAD 作为训练源码。

## 2. 执行顺序及依赖

以下是 M08 内部执行顺序，不另设一轮模型设计或通用接口审批。
复用[构建计划 §5](PSM-WMA_G2_model_build_plan_v1.0_2026-11-17.md#5-集成验收矩阵m07m08)。

| 优先级 / 内容 | 最小输入 | 本轮状态与通过范围 |
|---|---|---|
| P0：受控 CUDA 数值 / 反向 | 固定源码、现有兼容 GPU runtime、明确的受控权重/输入/seed、实际 CUDA 探针 | BLOCKED：独立驱动/运行方案未交付；运行 NOT_RUN。不依赖 DATA_B/C；受控 PASS 不能关闭完整真实样例 Gate |
| P0：受控多 rank FSDP | 上项输入、实际多 GPU 布局、调用真实 FSDP 入口的探针 | BLOCKED：驱动/目标布局未交付；运行 NOT_RUN。验证 collective/presence/注册/反向，不等于真实 G1 权重与训练恢复通过 |
| P0：完整训练、Local inner、TRAIN_A→B 与 DCP | 已验 G1/Edge/Wan、完成的 smoke recipe、实际 DATA_B/C 和 DATA_C provider、目标 FSDP 布局 | BLOCKED：资产与 provider 尚未冻结；沿现有 Phase5，不新建训练循环 |
| P1：真实输入与服务 | DATA_B/C 对齐清单、当前 rollout provider、真实 loaded-weight/config hooks factory、Session coordinator | BLOCKED：provider/factory/资产未冻结；D 服务仅单模型 rank，B1 与 mixed B 均在该边界内 |
| P2：正式运行参数 M09 | 上述实测、初始化来源、资源/成本与比较清单 | TODO；正式 R1/R2、长训练、900EP 未启动 |

不能因 DATA_B/C 未齐而把受控 CUDA 探针也写成数据阻塞。
反之，随机权重或合成窗口的 GPU PASS 不能替代真实数据、checkpoint、Local 内层或完整恢复验收。
D 多 rank Session cache 明确不支持；**训练 FSDP 必须独立验收**，不能用服务限制推断其通过或失败。

## 3. 当前探针缺口与复用边界

固定 Child 的 `g2_core_test.py:47`、`g2_integration_test.py:36` 将 attention 替换为 CPU 参考实现；
`g2_core_test.py:336` 的 FSDP 验证替换了并行边界。
因此修改 `CUDA_VISIBLE_DEVICES` 或把这些 pytest 结果重新计数，不能作为 P0 GPU/FSDP 证据。
本轮未交付或执行独立 M08 CUDA/FSDP 驱动，也不伪造一个不存在的 CLI。

执行侧可先准备独立 `/tmp` 诊断驱动，保存其完整源码与 SHA256、精确命令及实际 import origin，
直接调用固定代码的生产 attention dispatcher、MoT/Omni 公共方法及真实 FSDP 初始化。
不得从 CPU fixture 继承 kernel/FSDP monkeypatch；不得在服务器修改或提交生产代码。
驱动及数值标准须在运行前固定，具体解释器/GPU/shape/预算待执行方案填写。

复用入口：

- 模型方法、参数与 G/L 接线：[B ABI](PSM-WMA_G2_B_Core_ABI_2026-11-17.md)，
  数据载体唯一导入 `cosmos_framework.model.generator.mot.g2_contracts`，不另建 dataclass。
- 训练：Child `examples/psm_wma_robocasa_corrected_phase5.py:1297` 的 `--g2-recipe`；
  [C 实际 runbook](../collab/codex/reviews/2026-11-17_G2_Model_C_Training_Handoff.md#可执行-runbook)。
- 服务：原 `cosmos_framework.scripts.action_policy_server_robocasa`；
  [D 原 B1/mixed B2/cache on-off 命令与变量表](../collab/codex/evidence/2026-11-17_g2_model_d_inference/SERVER_RUNBOOK.md)。
  必须使用实际 factory、事务 lease/slot/manifest；不构造假 provider 或重写服务缓存。

## 4. 运行前填写的最小清单

| 项目 | 必须固定的内容；未知保持缺件 |
|---|---|
| source | 本文 §1 的源码 pair、Root tree Gitlink、干净隔离工作区、实际模块 import origin、外部探针源码哈希 |
| runtime | 现有解释器绝对路径、Torch/CUDA/attention backend、GPU 型号与授权设备、精度、实际 FSDP mesh/ranks；不升级环境 |
| checkpoint | 同一 G1 model-only 初始化的完整已验 receipt/shard 身份、`model/.metadata` SHA256、G1 config SHA；metadata SHA 本身不证明所有 shard 完整 |
| data | DATA_B state15 来源；DATA_C split/index/alignment/provider；实际 decision-window IDs、raw15 标签/EEF10及 Local chronology；DATA_A/B/C 与 TRAIN_A/B 分开记录 |
| spatial/text | 每 episode 初始静态增强文本及模板/tokenizer、最终有效 tokens/positions/dropout、logical state/physical owner、view 内容和 mask SHA、geometry/membership/VAE recipe、top variant |
| training | 有界 smoke 的 S_A/S_B、committed-consumer 目标、b_stream/world、各组 warmup/decay/min/horizon、保存边界；recipe 内 `grad_accum_steps=1` |
| service | 实际 G2 checkpoint/config/EMA 选择及 versions factory、当前 rollout provider、Session coordinator、有限 cache 预算、guidance=1、单模型 rank |
| assertions/limits | 每个张量的比较规则与 abs/rel 标准、梯度/冻结/恢复断言、运行步数/时长/内存上限、失败停止条件；在运行前填写 |
| outputs | 新的独立证据目录、各 rank 日志/JSON、原始比较结果、checkpoint/Local sidecar、退出码和 owned cleanup 记录；私有原始数据留服务器 |

实际样本从 DATA_C 索引取，不用任务名推断路径。按原计划选择不少于 3 个 decision windows，
覆盖初始 Local 缺席与后续存在、view 更新与引用、正常/空文本、B1/mixed B。
`with_robot` 默认；`without_robot` 在其独立内容/引用及匹配配置下验证。
#54 旧 VAE 人审及限定 A2 样例结论继承，不重复 producer/VAE 或将其标作 DATA_B/C 已完成。

## 5. 现有精确命令模板（本轮未执行）

先在专用执行 worktree 检出固定源码及其 Gitlink；不得在活动 G1 工作树操作。
以下只读断言必须在该执行 worktree 成功。本文 docs 分支 HEAD 会故意不满足源码 Root 断言。

```bash
set -euo pipefail
export G2_ROOT_SHA=41464b051ef8e02711dbfa37d379d2b14c7c57f4
export G2_CHILD_SHA=9370c3858532b4d61630138431145c8360e86eb0
export LD_LIBRARY_PATH=''
export PYTHONPATH=.
cd "${G2_ROOT:?dedicated fixed-source worktree}"
test "$(git rev-parse HEAD)" = "$G2_ROOT_SHA"
test "$(git rev-parse HEAD:cosmos-framework)" = "$G2_CHILD_SHA"
test "$(git -C cosmos-framework rev-parse HEAD)" = "$G2_CHILD_SHA"
test -z "$(git status --porcelain)"
test -z "$(git -C cosmos-framework status --porcelain)"
```

完成的配对 recipe 做配置校验，不建模型/provider、不训练：

```bash
cd "$G2_ROOT/cosmos-framework"
"${G2_PYTHON:?existing interpreter}" -m examples.psm_wma_robocasa_g2_recipe \
  --check "${G2_R1_RECIPE:?completed bounded R1 JSON}" \
  --pair-with "${G2_R2_RECIPE:?completed bounded R2 JSON}"
```

Phase5 真实资产 preflight 使用下列命令的全部参数并额外加 `--preflight`，
可用同一 `G2_PYTHON -m examples.psm_wma_robocasa_corrected_phase5` 执行；
其读取真实资产/索引/tokenizer与源锁，**不证明 forward/backward 或 FSDP 已通过**。
以下为后续有界执行模板，只有输入与运行范围固定后才交给执行侧；不是本轮启动指令：

```bash
cd "$G2_ROOT/cosmos-framework"
"${G2_TORCHRUN:?existing environment torchrun}" \
  --nproc-per-node="${G2_WORLD_SIZE:?must match recipe.training.world_size}" \
  -m examples.psm_wma_robocasa_corrected_phase5 \
  --phase "${G2_PHASE:?fresh or resume}" \
  --g2-recipe "${G2_RECIPE:?completed bounded smoke JSON}" \
  --job-name "${G2_JOB:?separate r1_g2_ or r2_g2_ namespace}" \
  --output-root "${G2_OUTPUT_ROOT:?owned output root}" \
  --source-root "${G2_SOURCE_ROOT:?verified raw15 source}" \
  --cache-root "${G2_CACHE_ROOT:?verified exact-window latent cache}" \
  --dataset-index-root "${G2_DATASET_INDEX_ROOT:?verified prebuilt index}" \
  --edge "${G2_EDGE:?verified Edge checkpoint}" \
  --vae "${G2_VAE:?verified VAE file}" \
  --base-checkpoint "${G2_G1_CHECKPOINT:?same verified G1 DCP}" \
  --root-worktree "$G2_ROOT" --expected-root "$G2_ROOT_SHA" --expected-child "$G2_CHILD_SHA" \
  --ga 1 --num-workers 0 --transform-rng-mode legacy_global \
  > "${G2_LOG:?new owned invocation log}" 2>&1
```

先固定 `CUDA_VISIBLE_DEVICES` 与上述 runtime 清单，不复用本地 CPU venv 充当 GPU 环境。
`G2_PHASE=fresh` 为严格 G1 model-only 初始化；`resume` 为同 job 的完整状态恢复，
pair/recipe/namespace 不变。recipe 会覆盖 CLI 的 batch/GA/world/budget，必须自身有界且 GA=1。
固定实现拒绝 G2 使用旧 `--stop-after-iter`、`--formal-execution-until` 或 G1 cross-pair override，
不得借这些旧参数绕过 G2 预算/恢复身份。

服务完整命令保持 D runbook 单一来源。cache 对照仅切换
`--g2-cache-enabled` / `--no-g2-cache-enabled`，其余权重、输入快照、seed、Local 事务和配置相同；
mixed B2 仍为一个模型 rank。G2 未验 diffusion-layer residual cache 必须按实际配置边界处理，
不编造覆盖参数、不为此全局关闭旧 G1 优化。

## 6. 必须落盘的断言与结果

| 验证 | 必须记录的实测证据 |
|---|---|
| CUDA 数值 / UND | 实际生产 kernel/backend；原生 two_way 与前置 UND 的相同 tokens/positions/type/pad/dtype；post-norm hidden、每层 base KV 与转换后的 GEN KV；正常/空/混长与 padding |
| Global / Local | 所有 GEN 层 `[Global;Local;Text;NativeGEN]` 各分支 presence/长度/sample offsets；none/local-only/global-only/both，B1/packed mixed 单独与合批隔离；原生 positions/loss mask 不变 |
| 反向 / 禁用 | 动作 loss→Global 非零有限梯度；冻结 GEN 时仍能反传 Global；TRAIN_B 的 GEN norm 未误 detach；Global-off 输出/梯度/初始化和 forward RNG 回归，无 Reader/零占位；零 Value 与移除分开比较 |
| 实际 FSDP | 各 rank 参数 inventory/state_dict/optimizer 完整；一 rank Global 缺席、另一存在，以及空文本/全部缺席；collective 序列、grad presence、reshard与阶段切换完成，无挂起或缺梯度 |
| Local / 阶段 / 恢复 | Local inner 确有更新且冻结慢权重不变；commit/abort/frontier；完整 GA/optimizer 成功边界才 A→B；连续运行与恢复后的 model/optimizer/groups/LR/Global moments、stage/counters、Local 与 RNG 对照；真实 DCP save/load，不是仅序列化字典 |
| 真实数据 / 服务 | 初始静态文本、DATA_B state15与DATA_C窗口/标签/选图因果对齐；cache fill/hit/miss/内容-geometry-mask变化；至少三次 replan，reset/task switch、两 Session/mixed B隔离、retry无重复Local commit；原始输出及 `/info` resolved settings |

同一输入、权重、RNG、版本签名与应精确恢复的状态按精确规则比较；浮点输出遵守运行前固定的逐项标准。
BF16/compile 原生物化边界要独立验证，不用 eager/CPU 相等替代。
**cache-off 仍走 G2 前置文本链**；单纯 cache on/off 相等不能替代 native two_way 对前置 UND/KV 的数值比较。
任何数值偏差必须保留首个分歧层/步与原始度量，不在失败后放宽标准。

建议各次调用在新证据目录保存 `source.txt`、`runtime.json`、`resolved_inputs.json`、
`command.sh`、`probe.py`（若使用）、`rank_N.log`、逐 case `comparisons.json`、
实际生成的 inventory/result JSON、DCP/sidecar 清单和 `result.json`。
这些是回填要求，不表示固定代码会自动生成所有文件；其现有训练输出包括
`g2_parameter_inventory_before_load_rank_N.json` 与 `g2_training_result_rank_N.json`。

结果逐项使用 PASS / FAIL / BLOCKED / NOT_RUN：

- PASS 仅针对已实际运行且断言和证据完整的 case，并注明受控或真实资产范围。
- 缺实际驱动/资产/factory/资源/参数则 BLOCKED；未执行则 NOT_RUN。不得写空 PASS。
- 异常、NaN、OOM、数值/梯度/源身份/恢复不符或 owned cleanup 失败为 FAIL；停止本次 owned invocation，保留原日志，不停止其他任务或自动扩大资源重试。

执行回执必须写明源码 pair、实际驱动 SHA、输入/recipe/checkpoint 身份、runtime、命令与退出码、
每 case 结果、日志/JSON/DCP 本机路径及未运行项。私有图片/张量/checkpoint 不上传 GitHub。
若暴露源码缺陷，回 #56 以最小证据认领，由唯一文件作者修复并发布新固定 pair；
旧 pair 结果留存，不能静默改动当前执行对象。

## 7. 收口条件

B 负责接收并归档同一 pair 的执行证据、定位接线问题；A/C/D 仅按已定位缺陷协作，停止独立扩展功能。
执行侧 ACK、驱动/命令、资产清单和真实结果尚未交付，M08 保持 TODO。
只有真实样例、目标 FSDP/Local/DCP 恢复、数据与服务边界的相应证据齐备，才判断 M08 是否完成并进入 M09。
正式 V3/Gitlink 合并、正式 R1/R2 与 900EP 仍需各自后续安排；本交接不启动这些动作。
