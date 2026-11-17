# G2 Model A — Global Reader 与空间编码交接

2026-11-17 CST。**A 模块实现及作者 CPU/static 完成，待 B 集成与独立审核。** 不代表完整 G2、GPU 或任务成功率验收。

## 固定来源与范围

| 对象 | 身份 |
|---|---|
| 开工核对的 Root V3 | `190ea2e2b674bcb18dea4701c8a27d1e16d40ccb` |
| 无损保留后续文档的 Root 基线 | `7a357620b4cc1f6817749c8a8275771cfbb4049c` |
| 正式 Gitlink / Child 起点 | `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2` |
| B C0 Root / Child | `739d39cf6498543b59d487d5925ef2a329040ac3` / `ec9356fafd1fd18cc0bd552b7eb23428f59df7f6` |
| **A 固定被测 Child** | **`4209b151ecc11ab2043b9d08037d43b5e3903618`**；直接父提交为 C0 |
| 两仓候选分支 / 独立工作区 | `v3-g2-model-a-reader-20261117` / `/workspace/work/g2-a-reader` |
| Child Draft | https://github.com/wxwy/cosmos-framework/pull/15 ，base 为 B 候选 |

[ACK](https://github.com/wxwy/psm_wma/issues/56#issuecomment-6943452748)、[producer 字段对齐](https://github.com/wxwy/psm_wma/issues/56#issuecomment-6943510790)、[取得 C0 后认领](https://github.com/wxwy/psm_wma/issues/56#issuecomment-6943646433)。先取得公开 C0 才提交正式模块；work/ 的独立准备没有成为公共 ABI。

相对 C0 仅新增四文件（383行生产、513行测试）：`mot/global_memory.py`、`mot/global_spatial.py` 及两者的 `*_test.py`，完整前缀 `cosmos_framework/model/generator/`。前者实现 Reader/final norm/独立 projector/modality，后者是唯一空间数值实现。

未改 B 的合同、unified_mot、omni_mot_model、memory_prefix、公共attention/FSDP，未改 Trainer/optimizer/checkpoint、Policy/Session、producer/latent_cache/tools/g2 或 Local 算法/参数。共享 SESSION/TODO/Inbox 由 B 汇总，A 没有并行覆盖。

**本 Root 候选只交本文与 A evidence，Gitlink 保持 d5c1ffc7。** 不把此 Root＋旧 Gitlink 称为已注册 A 的可运行完整模型配对；B 集成上述固定 Child 并绑定最终 Gitlink。Root 发布完整 SHA 在 PR/#56 回执记录，避免自引用。

## C0 接口与行为

```python
from cosmos_framework.model.generator.mot.g2_contracts import GlobalMemoryConfig
from cosmos_framework.model.generator.mot.global_memory import GlobalMemoryReader, GlobalMemoryProjector

cfg = GlobalMemoryConfig(enabled=True, top_view_variant="with_robot")
reader = GlobalMemoryReader(text_dim=actual_und_width, config=cfg, latent_channels=actual_recipe_channels)
projector = GlobalMemoryProjector(model_dim=actual_backbone_width, config=cfg)
task_queries = reader.prepare_task_queries(und_text_features)  # [B,64,512]
result = reader.read_visual(task_queries, selected_views)      # C0 ReaderOutput
global_prefix = projector(result.tokens)                     # [B,64,D_model]
# reader(und_text_features, selected_views) 等价组合前两个调用。
```

唯一载体为 C0 `UNDTextFeatures/SpatialView/RasterMapping/SpatialProjection/ReaderOutput`。latent_channels 默认48；C4测试显式传4。H/W由完整网格确定；text/model width由实际配置确定。B注册唯一两实例，不复制 projector；A提供 reset_parameters，含meta→to_empty初始化支持。

每样本 tuple 的 views 数量可变。逐样本 compact/dispatch，不串样本；允许多个Room/Island；缺方向不创建token。每样本必须有配置的top variant，拒绝错版/两版混入、重复view_id、跨world_frame、完全无有效patch的声明view。未实现跨样本varlen打包优化。

文本 mask 校验 C0 effective token 长度及右padding；先选有效hidden再适配，NaN padding不污染前反向。真实空条件有native specials就读取；长度0跳过语言CA贡献、保留FFN。Reader不抽dropout，不把正常hidden乘零伪装空文本，不持久化状态或修改调用方task_queries。

## 数值定义与依据

设计 v2.2 的 M-D02…M-D13、§4–5/16、构建计划M01/M02/M07为语义依据。**[O/V]** 64/512/8/2048与语言1/视觉2轮是Owner确认的实验起点；Perceiver[P01/P02]、Transformer Base[P05]只提供结构/规模先例，不证明最优/SR。下列额外取值均为 **A的版本化最小实现[实现/V]**，未声称Owner已全部冻结。

| 项 | 实际定义与理由 |
|---|---|
| 14D几何 | `[o(3),right(3),up(3),forward(3),width_m,height_m]`；MLP14→512→512 / SiLU，直接绑定producer正交投影，不推断RGB的物体XYZ/深度/法向 |
| 平面锚点 | `o=origin_world+uv_min_room[0]*right_world+uv_min_room[1]*up_world`；right/up已为world向量，不再次旋转axes_world；沿forward物体深度未定 |
| 米制尺度 | o与宽高除以10米，方向维不缩放；固定可逆缩放，使典型米制幅度适中，不是state15归一化或最优物理尺度 |
| 几何检查 | 两套basis正交单位，abs容差1e-5；extent≈W/H×mpp（rtol1e-6/atol1e-7）；pixel_center_offset=0.5；缺字段不填假值 |
| type | floor/room/island三scope＋floor_top/upper_up/plus_X/minus_X/plus_Y/minus_Y六方向，各512D表相加；raw Room/Island ID不作语义embedding，类型不是输入序号 |
| patch支持 | canvas cell与半开content_box交集正面积即保留，再AND C0 valid_mask；部分覆盖保留，完全padding删除；不依据颜色，不宣称VAE感受野独立 |
| patch锚点 | 交集中心逆resize/pad再按原画幅边缘归一化为UV；原尺寸因子抵消；v遵从rows_flipped；白色有效源内容仍有效 |
| PE | raw UV两维＋两轴 `sin/cos(π·2^k·(2UV−1))`，k=0…7，共34维，无bias Linear→512；固定多尺度，raw UV保留非周期量，频率数/尺度待样例验证 |
| norm/FFN | pre LayerNorm eps1e-5，FFN512→2048→512 / SiLU，final LayerNorm；复用仓库local_evidence的基本组件习惯，没有复制Transformer框架 |
| 初始化 | Linear Xavier uniform/bias0、LayerNorm weight1/bias0；queries/type/modality normal std0.02；依caller Torch seed可复现，64queries互异，无内部重设seed |
| 无冗余bias | attention Q/K/V/O无bias，K常量bias在softmax中不可辨识；projector Linear无bias，独立modality避免完全重复bias |

producer只读固定来源：#54审核 `4ad0fe7394cb62c4b5692fecaf6ce52963b8852c` 的 `spatial_metadata.py::projection_from_renderer`、`encoding.py::preprocess_rgb`、`storage.py::read_record`。实际字段包括reference origin/axes、world方向、uv_min、米制画幅、flip/projection_id，以及original/resized/canvas HW、padding/content_box。没有merge/改写producer、获取私有数据。

手算例：C0 origin(2,3,0)、right(0,1,0)、up(-1,0,0)、uv_min(-1,-2)给平面锚点(4,2,0)。48×64 canvas、有效y∈[8,40)、3×4 latent的v为0.875/0.5/0.125。256² canvas上171×256有效区、16²网格保留12×16=192patch，未先整图池化。

版本供B/C/D绑定config/checkpoint/cache：Reader `g2_reader_prenorm_silu_xavier_queries002_v1`；Spatial `g2_spatial_plane14_fourier8_overlap_centroid_v1`；mask `positive_area_content_intersection_v1`；projector `g2_global_linear_modality002_v1`。频率/除数为正式整数buffers，dtype转换不损其值，reset会在to_empty后重建。

## CPU/static与原始证据

原始目录：`../evidence/2026-11-17_g2_model_a_reader/`。

| 运行 | 来源/边界 | 结果 |
|---|---|---|
| pre-C0 scratch | work/私有准备，未绑定最终源码，不是生产ABI | 3 PASS，仅历史日志，不累计M02 |
| dev01 | C0＋待提交A文件，运行前格式化 | 56 PASS，0失败/错误/跳过；1125源码指纹不变 |
| **final01** | **clean固定Child4209b151**，无格式化 | **56 PASS（A45＋C0原11）**，0失败/错误/跳过；1125指纹及Git身份/状态不变；pytest7.32秒 |

四个A文件Ruff0.12.7 check/format、AST/语法和Git diff-check通过。复用已有Python3.12.14/Torch2.10.0+cpu/pytest9.0.2环境，无安装/升级；final01最大子进程RSS410.902MiB。参数清单明确是fixture：text_dim24/C4/model_dim80，共11,935,360参数；B按实际宽度重新列完整模型inventory，不把fixture数量当实际主干参数量。

覆盖单/多view、多Island、两种top、48通道完整网格、可变/部分patch、thin/odd padding、NaN padding前反向屏蔽、mixed B逐样本精确对照、同步view/meta重排（FP32 rtol/atol2e-5）、错配metadata敏感性、正常/空文本/native special、图像/语言/几何/type/PE影响、所有应训练参数有限非零梯度、独立projector、state_dict精确往返、查询初始化、meta初始化、两次实际视觉CA及仅64-token SA、无重型依赖导入。

**attention证据边界**：生产复用 `cosmos_framework.model.attention.attention`，无新生产backend。当前dispatcher只有GPU后端，CPU tests在该边界使用明确参考核，另用public-entry spy验证路由。56项不证明CUDA kernels/真实MoT/动作loss/FSDP通过。冻结下游linear的反向测试只证明A接线，不代表实际GEN接通或任务效果。

复现（固定Child、无需模型资产；输出换新路径）：

```bash
cd /workspace/work/g2-a-reader/cosmos-framework
CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu COSMOS_TRAINING=0 COSMOS_INTERNAL=0 \
LD_LIBRARY_PATH='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
/workspace/.venvs/psm-wma-cpu/bin/python -m pytest --noconftest -c /dev/null \
  -p no:cacheprovider -q \
  cosmos_framework/model/generator/mot/global_memory_test.py \
  cosmos_framework/model/generator/mot/global_spatial_test.py \
  cosmos_framework/model/generator/mot/g2_contracts_test.py \
  --junitxml=/workspace/work/g2-a-reader-rerun.xml
```

实际完整runner已原样归档为evidence的 `run_reader_cpu.py`。本次启动（Root cwd）：`/workspace/.venvs/psm-wma-cpu/bin/python work/run_reader_cpu.py --root /workspace/work/g2-a-reader --out /workspace/work/g2-a-cpu/final01 --expected-child 4209b151ecc11ab2043b9d08037d43b5e3903618`。展开命令/关键env/源码前后指纹/identity/JUnit/result/参数清单均在final01。PASS要求零失败/错误/跳过、静态通过、固定clean Child/源码不变，不以skip代替验收。

## 交接与未运行项

- **B**：集成固定A commit；注册唯一Reader/projector，按实际配置确定宽度/通道/设备/compute dtype并初始化；自定义prepare_task_queries/read_visual的FSDP注册和collective顺序归B；Global-off不创建模块。A未改任何主干/训练/采样调用。
- **C**：共用C0及A的patch_layout，避免第二套坐标/mask；保证recipe/grid、effective文本/dropout、scene/episode/subtask、非未来owner来源；所有A参数进入唯一Global组。A不重做资产source/recipe验收、state15或checkpoint策略。
- **D**：仅固定权重下缓存任务查询；视觉读出由查询＋当前views重新计算，无上一Global递归。缓存绑定上述版本及实际元数据/mask/选图/权重；module本身无Session缓存，不改变调用方queries或forward RNG。
- **NOT_RUN**：真实Wan/UND/GEN、CUDA公共attention前反向、联合prefix/实际动作loss、FSDP/分布式、两阶段训练/恢复、Session/cache-on/off、DATA_B/C真实对齐、rollout/闭环/SR/实际性能、全量评测。未推广正式V3/Child/Gitlink，未读取/外传服务器资产。

后续执行侧在B最终固定集成Root/Child上做真实样例。作者CPU PASS/Draft发布不自动关闭这些Gate。
