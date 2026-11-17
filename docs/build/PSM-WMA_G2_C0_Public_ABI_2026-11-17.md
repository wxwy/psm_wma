# G2 C0 公共接口与唯一文件负责人

C0 schema `psm_g2_c0_v1`。模型语义依据 v2.2 (Root7a357620)，实现基线 Child d5c1ffc7。
固定 Child C0：`ec9356fafd1fd18cc0bd552b7eb23428f59df7f6`；Root C0为包含本文件和该Gitlink的实现提交（完整SHA在 #56 发布回执中）。
此批只有公共边界与 synthetic CPU，不声称 UND/Reader/GEN 已集成。A/C/D 共用一个 dataclass 来源：

```python
from cosmos_framework.model.generator.mot.g2_contracts import (
    GlobalMemoryConfig, SpatialView, SpatialProjection, RasterMapping, ViewIdentity,
    G2SampleIdentity, EffectiveTextBatch, UNDLayerKV, UNDTextFeatures,
    ReaderOutput, PrefixLayout, TextCacheSignature, GlobalCacheSignature,
    TrainingStage, ParameterGroup,
)
```

## 唯一作者、依赖与认领

|路线|唯一修改范围|依赖/交付|
|---|---|---|
|A (ACK6943452748)|`mot/global_memory.py`、必要空间编码模块、对应 tests；A专属handoff|C0→Reader/独立projector；不改 B 主模型|
|B (ACK6943487277)|`mot/g2_contracts.py`/fixtures/tests、`memory_prefix.py`、`unified_mot.py`、`omni_mot_model.py`、`cosmos3_vfm_network.py`、必要attention/config/carrier/FSDP；公共TODO/SESSION|C0→UND/联合prefix→固定 A/C/D 集成|
|C (ACK待核对)|共享 `action/utils/json_formatter.py`/`transforms.py`、训练数据适配、warm-start/optimizer/阶段/checkpoint与配方/tests|C0→共享文本/训练；不复制 B 载体、不import inference|
|D (ACK待核对)|`mot/inference_text_kv_memory.py`、现有 Policy Server/Session/Global/text缓存、对应 tests|C0+B公开模型API→缓存；B不改此文件|
|离线 #54|根仓 `g2/offline`、原producer/SG/views/逐view VAE；DATA_B/C后续|模型只消费其返回值；不恢复场景/重判阈值|

文件移交先在 #56 明确，才由唯一作者修改。各路只写自己的 handoff；B汇总公共账本。
固定SHA在 #56 C0发布评论及 B handoff登记，历史基线不是C0。

## 字段、shape 与实际来源

- `SpatialView` 每样本 tuple，可变 view 数，完整 `[C,H_z,W_z]` 浮点 latent、同设备 bool `[H_z,W_z]` mask。无固定10图/Island槽；缺方向不建 view。实际C/H/W/dtype由已验收 recipe确定，fixture C4 仅测试。scope/direction是实际类别，room/island仅分组身份。每逻辑view/episode一个离线文件，不绑定存储到模型。
- `SpatialProjection` 保留 #54 `projection_from_renderer` 的原始reference origin/axes、right/up/forward、uv_min、W/H、mpp、米制画幅、flip/pixel-center。`RasterMapping`保留 preprocess_rgb original/resized/canvas HW及半开content_box，四侧padding可从box导出。无默认原点/单位轴，缺字段失败。不把投影平面坐标称物体XYZ。A负责数值编码/归一化/PE；其候选规则需注明版本，B不重复实现。
- `ViewIdentity` 区分 image owner/content、geometry、membership、recipe；`G2SampleIdentity` 区分decision frame与不晚于它的logical state。C必须拒绝future owner，保持scene/episode/subtask绑定；Dataset/provider负责内容与source验证，不把 dataclass结构验证称数据验收。
- `EffectiveTextBatch` 是共享formatter/tokenizer/dropout**最终**条件。每样本未padding的tokens及原生 `[3,L]` mRoPE positions、一次dropout决定和身份；包含实际native special tokens。空条件可有native specials；确实0有效tokens时L=0。C唯一抽样；Reader/GEN共同使用，checkpoint重算不重抽。R1/R2删除idle字段，旧G1语义不变。
- `UNDTextFeatures.hidden` 最终post-norm `[B,Lmax,D_text]`，右pad+bool mask。`layers`逐层packed有效文本 `[sum(L),Hkv,Dhead]`。`UNDLayerKV.key` 在UND k_norm之后、GEN key norm/RoPE之前；`value`为UND V，cos/sin保存同一native位置的RoPE。B在GEN当前参数下应用 `k_norm_und_for_gen` + RoPE；不能把独立reasoner旋转后的raw KV直接当GEN KV，不detach可学习norm。维度由实际模型读取。
- A接口约定：`GlobalMemoryReader(text_dim=..., config=GlobalMemoryConfig)`；`prepare_task_queries(text: UNDTextFeatures) -> Tensor[B,64,512]`；`read_visual(task_queries, views: tuple[tuple[SpatialView,...],...]) -> ReaderOutput`；`forward(text, views)`可组合二者。`GlobalMemoryProjector(model_dim=..., config=...)`，`forward(tokens: Tensor[B,64,512]) -> Tensor[B,64,D_model]`；projector包含独立Global模态标识。A实现算法；B注册/初始化/调用。若作者选择不同类名/签名先在 #56 明确兼容映射。
- `PrefixLayout`独立G/L长度/presence与总offset；概念 `[G;L;Text;NativeGEN]`；关闭为0行，不是64零行。M04扩展现有MemoryPrefixContext保留旧Local API，不改k_local语义。
- Signature精确绑定Session、checkpoint/UND/GEN/Reader/projector/geometry encoding/position/dtype、有效文本/dropout、top variant、稳定排序selected views及其content/owner/geom/membership/recipe、projection、raster、mask版本。不包含每步无条件递增frame或未选中view。D仍须有限缓存、reset/retry及tensor storage的不可变快照；训练不能跨step缓存可学习输出。
- 阶段仅 `TRAIN_A`/`TRAIN_B`/`R1`；组 `global`/`gen`/`action_adapter`。C掌管实际selector/LR/optimizer，所有参数互斥完整；Local slow/UND/VAE冻，Local inner运行，GEN冻仍允许Global梯度。DATA_A/B/C绝不映射训练阶段。

## 尚缺与边界

真实DATA_B state15与DATA_C索引未交付；静态语言/双top最新source遵从 #54最新Owner说明。
当前 #54已审核4ad0fe73；其旧 `clean/w_rbs` 名称由C显式映射 `without_robot/with_robot`，模型不猜路径。
几何具体数值编码/mask交集规则由A交付版本；真实checkpoint、预算、GA/batch/预热等待样例。
C0无nn.Module实例化，不消耗新增初始化RNG。真实UND/KV/GEN梯度、FSDP/GPU/cache on-off均NOT_RUN。

## CPU复现

Child cwd，已有CPU解释器，无联网/权重/数据/GPU；fixtures用显式合成几何：

```bash
CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu LD_LIBRARY_PATH='' PYTHONPATH=. OMP_NUM_THREADS=1 \
  /workspace/.venvs/psm-wma-cpu/bin/python -m pytest --noconftest -o addopts='' \
  cosmos_framework/model/generator/mot/g2_contracts_test.py -q \
  --junitxml=../artifacts/g2_model_b_c0/junit.xml
```

PASS：无failure/error/skip、有效/空文本/元数据/独立prefix身份及错误输入拒绝通过。
这只验ABI，不能累计为端到端通过。原始日志/static在同证据目录。
