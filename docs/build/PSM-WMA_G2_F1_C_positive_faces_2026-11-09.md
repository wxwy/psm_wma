# G2-F1-C：默认保留全部正面积三角面

独立分支 `codex/g2-f1c-positive-faces`，精确父源码 `3b6c6055e36824be33ed947745aa3e5b839da832`。保留其后 R1 发布回执的五个纯元数据文件，不继承额外实现。固定候选 SHA 由本批 canonical Inbox 交接记录。

依据：[Owner / Issue26 正式 F1-C 指令](https://github.com/wxwy/psm_wma/issues/26#issuecomment-6730795142)。上一轮 R1 [独立评审](https://github.com/wxwy/psm_wma/blob/a9ef423f77e54d7bbd64f4104887245f29b0a0aa/docs/collab/chatgpt/reviews/2026-11-09_G2_N6_F1B2_R1_3b6c6055_GPT_independent_review.md)（blob `0a92ea6f6c5390a08c3760c9d42fff9321ca6f55`）只批准两个 P2 与无回归。**本轮 Owner 明确覆盖旧 sampler frozen / 正面积下限策略**，不改写历史评审。

## 正式行为与最小范围

- `surface_sampling.py`：默认仅跳过表示坐标的精确有理数叉积为零的面。所有有限正面积面都保留；原输入 face ID、barycentric UV 权重、原始全几何 SHA 不变。没有最小面积过滤，没有 remesh/替代面或资产角色修改。
- 非有限几何、数值溢出、非法参数、全零 mesh 和点数预算继续拒绝。每面点数仍由最长边/spacing 决定；平方范数可能下溢时用稳定 hypot 恢复边长，其余原 dtype 算术与采样顺序不变。极小面积但长边很长的面不享受预算例外。
- 原来的拒绝性字段被移除：`positive_face_cross_norm_min_exclusive`、`rejected_nonzero_near_degenerate_face_ids`。新 policy=`EXACT_ZERO_ONLY_RETAIN_ALL_POSITIVE`，用 `retained_near_positive_face_ids` 记录小正面，`retained_area_underflow_face_ids` 明示正面积在 float64 统计中下溢；这些面仍实际采样。
- `surface_coverage.py`：保留面计数依据精确正性，不能依据浮点面积 `>0` 漏面。每点近似面积权重下溢时保留零的数值近似，记录原 face IDs/点数和 `FLOAT64_UNDERFLOW`，面积加权有效色比例留空，不伪造正权重或整面连续颜色覆盖。
- `prescan.py` 只升级 hashed producer 字段为 `g2_sample_color_audit_v2`。`color_evidence.py` 对 v2 仅允许有显式、一致的整面下溢记录的零权重；负权重、记录缺失/错面/错点数、局部零权重均拒绝。旧 v1 及 genuine legacy 的正权重要求不变。四个 NPZ 数组与 snapshot 封存文件结构不变，防降格合同保持。

原分类/类别解析、R1 sRGB/include 两修复、MJCF/状态 loader、native 桥接与视图实现均不改。adapter 和 visual producer SHA 因代码/协议自然变化；原模型 closure 与几何/状态身份保持。不得改旧 manifest 或附件冒充新源码验收。

## 作者 CPU 验证

仅自建 MJCF/OBJ/UV/状态与数值边界；无真实 RoboCasa 输入、GPU、模型/rollout/训练、服务器文件读取或外传。

```bash
cd /workspace/work/psm_wma_n6
CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  /workspace/work/g2-gt-venv/bin/python -m pytest -q g2/tests \
  --junitxml=/workspace/work/n6_f1c_full.xml
```

最终 **291/291 PASS**，0 failure/error/skip。原 **274/274 testcase IDs 全保留**，包括历史259/207。按新政策修改两份旧测试中的六个案例断言，保留其历史名字/参数 ID；其余旧测试字节不变。新增同一冻结17项在旧3b6源码全部 FAIL，新版全 PASS。覆盖纯微面、最小次正规坐标、长细面、混合零面/正面、原编号、严格预算、float32/64 非零平方下溢、UV/动态身份和下溢磁盘证据负控。

```bash
CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  /workspace/work/g2-gt-venv/bin/python \
  docs/evidence/g2_f1_c_2026-11-09/compare_own_positive_surfaces.py \
  --baseline-root /workspace/work/n6_f1c_baseline \
  --candidate-root /workspace/work/psm_wma_n6 \
  --output /workspace/work/n6_f1c_positive_parity_reviewed
```

同一六几何、frame0/200，每帧6244点；XYZ/RGB/valid 数据行逐字节一致，原始几何/状态/边界相同；旧v1与新v2逐点附件均由新 verifier 从磁盘检查。新 adapter/visual producer 身份确实变化。自建编译 mesh 的 face14 为微正面、恰好3点且使用原 UV 有效颜色；face1/13/15 为零面、没有点。frame0→200移动12cm，来源/原face/颜色身份稳定。

另一 Agent 只读复核并关闭其 P2：平方范数下溢成较小非零值可能少算细小面预算，已改稳定长度条件并加入两个精确反例。测试开发中两次自建 fixture 断言/磁盘接口误用已修正，初始日志原样保留，不计作候选缺陷或正式 RED。作者测试与代码复核均不是 GPT 真实服务器验收。

证据：`docs/evidence/g2_f1_c_2026-11-09/`，含最终/旧版 RED 原始日志+JUnit、原274案例保留/变更索引、源码哈希、数值对照及代码复核。原始 log/XML 按字节封存，不做空白清洗。

## GPT 固定版本验收交接

在服务器**新隔离副本**检出新固定 SHA，源码 Git blob 必须与清单逐项一致，执行291项并单独检查原274 ID。之后在原服务器本地使用 Layout1/10 的原始 MJCF/assets/ep_meta/FULLPHYSICS0/200 和既有角色证据，四帧全新导出并用磁盘 verifier 核验 cloud/mask/face/reason/面积附件。

1. Layout1：与 R1 的有效数据行、来源 closure/state、原 mesh/UV 核对；无正面积遗漏或角色改写。
2. Layout10：检查纸巾原正面积 face1941/2357/2374/2646 都采样（服务器原型预期各3点），零面1977/2256无点、原几何 SHA保持；非有限/溢出与预算负控仍拒绝。具体数值以新固定源码真实运行结果为准，不能把原型的2135041点直接当正式事实。
3. 新 adapter/visual SHA，不复用旧 producer 附件；几何 closure/source/state 身份不应伪造变化。未知161/429继续未知，任何无效颜色如实保留，状态不得冒充整屋 COMPLETE；`training_ready=false`。
4. 人工 Layout10 彩色点云对照另做。完整固定2009 native四帧、普通结构/真实感知、六图/Island、PSS/Cosmos仍 OPEN；P0相同三组件的 harness 不是完整 native 验收。

所有私有资产、状态、图片、点云和逐部件原始审计留服务器。本轮不建 PR、不合并；V3、nav_sg、Gitlink、训练/缓存不改。固定 SHA 交接后按 Owner 指令继续独立的整屋角色来源分析，不把自测或分析报告当整屋通过。房间分割仍由 nav_sg 负责。
