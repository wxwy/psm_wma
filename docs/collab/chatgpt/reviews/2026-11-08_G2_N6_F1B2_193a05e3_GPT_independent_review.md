# G2-N6-F1-B2 固定 193a05e3：GPT 独立服务器复验

- 审查时间：2026-11-08 23:11 CST（Asia/Shanghai）。
- 固定实现：`193a05e3b250eb32dd7ee08165a368a6706e78ee`。
- Git tree：`ea6c22922c11f1a1edfd9193dbbc9d326a2ca167`。
- 作者交接：[Issue #26 / F1-B2](https://github.com/wxwy/psm_wma/issues/26#issuecomment-6722822036)。
- 前轮结论：[F1-B 02912226](https://github.com/wxwy/psm_wma/issues/26#issuecomment-6722340254)。
- 本文只发布独立复验摘要；原始资产、状态、点云、图片与逐项审计保留在 data。

## 1. 判定

**REQUEST_CHANGES：2 项 P2。**

固定候选的 259 项 CPU 测试、34 项源码身份、54 组软件纹理对照、旧有效子集四帧数值回归，以及 P0 harness 中相同 reader/fusion 组件的四帧运行均通过。保留前轮 exact-zero sampler 与 AUDIT_ONLY 全 geom 审计的通过结论。

本轮独立负控发现：

1. **P2-B2-01：显式 2D sRGB mesh 被标为有效，且可产生声明子集 COMPLETE。**
2. **P2-B2-02：include 被包含文档的根 wrapper 被错误计入 body 祖先或 default/asset 排除上下文，合法输入被误拒。**

两项均已在 MuJoCo 3.3.7 实际执行复现。当前真实 Layout1/10 没有触发这两项反例，不能据此声称它们已经污染当前整屋结果；它们仍是候选对外合同的正确性缺陷，需要修复。

**整屋来源/角色/材质未获批准。** Layout1 两帧仅得到 PARTIAL_SOURCE；Layout10 两帧被明确 visual 的纸巾网格正面积近退化面阻断。完整固定 native 2009fae35、普通感知结构、native 六图及人工验收均未关闭，`training_ready=false`。

## 2. 必修问题与复现

### P2-B2-01 — 显式 2D sRGB mesh 缺少有效性保护

位置：[g2/sim/source_geometry.py](https://github.com/wxwy/psm_wma/blob/193a05e3b250eb32dd7ee08165a368a6706e78ee/g2/sim/source_geometry.py)，`_legacy_surface_colors` 第 235–270 行及 `surface_colors` 第 279–291 行。

primitive 路径拒绝显式 2D sRGB；保留的 mesh UV 路径没有同等颜色空间检查。RGB 槽、2D 纹理、有效 mesh UV、非 texuniform 的合法输入仍按原始纹理字节插值，并返回 valid=true / reason=0。

独立夹具复用仓库 `mesh_scene`，将纹理替换为 8×8、每通道 128 的自建 PNG；分别指定 sRGB 与 linear。材质 emission=1、specular=0，关闭灯光/阴影干扰，使用实际 MuJoCo 3.3.7 + llvmpipe 渲染。没有使用真实房屋图像。

| 颜色空间 | B2 采样 RGB | CPU 渲染 RGB | B2 valid / reason | 实际导出 |
|---|---|---|---|---|
| sRGB | 128,128,128 | 55,55,55 | true / 0 | COMPLETE，color_valid_fraction=1 |
| linear 正控 | 128,128,128 | 128,128,128 | true / 0 | COMPLETE |

这里的 COMPLETE 仍仅指 DECLARED_VISUAL_GEOMS_ONLY，training_ready=false；并非已绕过整屋认证。问题是作者明确未支持的投影/编码情形仍被输出为有效颜色。**最低修复是保守置无效并给出原因，不要求本轮实现 sRGB 解码、过滤与输出编码。**

复现文件：

- `independent_srgb_mesh_probe.py`
- `f1b2_independent_srgb_mesh_probe.json`

要求：

- 在 mesh 的实际 RGB 2D 纹理选择路径检查显式 sRGB；保持默认/linear 已有效路径的数值。
- 增加 mesh sRGB negative、linear positive，以及 strict/partial 导出状态和 mask 的测试。
- 不把此项称为新 primitive 公式回归：它是旧 mesh 路径遗留、在 B2 新审计范围中仍存在的缺口。
- 当前真实输入核查：Layout1 有 3 个 RGB 槽显式 2D sRGB geom，均为 box；Layout10 为 0；两布局均没有这一配置的 mesh。Layout1 这 3 个 box 已正确保留为无效。

### P2-B2-02 — included document 根 wrapper 被赋予了错误语义

位置：[g2/sim/source_roles.py](https://github.com/wxwy/psm_wma/blob/193a05e3b250eb32dd7ee08165a368a6706e78ee/g2/sim/source_roles.py)，第 43–56 行。

当前处理 include 时对被包含 XML 的根节点直接调用 `walk`。MuJoCo 实际编译时去除该根 wrapper，把其子节点插入 include 所在上下文。于是根标签若为具名 body，被当作不存在的 body 祖先；根标签若为 default/asset，又被当作排除上下文。

最小场景是在真实 `fixture_body` 内 include 一个片段，片段子节点始终是同一个 box geom。只改变片段根 wrapper，四种输入都在 MuJoCo 3.3.7 成功编译，实际 geom body 均为 fixture_body：

| fragment 根 wrapper | 实际编译 body | B2 来源状态 | strict 导出 | allow-unclassified |
|---|---|---|---|---|
| mujocoinclude | fixture_body | SOURCE_BOUND | COMPLETE | COMPLETE |
| body name="ignored_wrapper" | fixture_body | SOURCE_UNRESOLVED | 拒绝 | PARTIAL_SOURCE，unknown=1 |
| default | fixture_body | SOURCE_UNRESOLVED | 拒绝 | PARTIAL_SOURCE，unknown=1 |
| asset | fixture_body | SOURCE_UNRESOLVED | 拒绝 | PARTIAL_SOURCE，unknown=1 |

strict 错误为 `unambiguous source-bound role evidence required`。后三种 partial 结果均无 COMPLETE。这是保守误拒和来源覆盖缺失，不是假通过。

复现文件：

- `independent_include_wrapper_probe_v2.py`
- `f1b2_independent_include_wrapper_probe.json`

要求：展开 include 时保持父级语义上下文，遍历被包含根的 children；继续保存真实原文件 hash、原 XML 路径和 include chain。增加上述四种根 wrapper 的实际编译/来源绑定回归，保留已有重名、循环、错误 body/source 等负控。当前真实两布局的全部 geom 均 SOURCE_BOUND，此反例没有触发当前房屋输入。

## 3. 独立运行环境与代码身份

所有工作在新隔离目录：

```text
/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_n6_f1_b2_193a05e3_gpt_accept_20261108/
  psm_source/
  runtime/
  evidence/
```

原参考环境是 Python 3.13.11 / MuJoCo 3.3.1。B2 的 primitive 投影固定于 MuJoCo 3.3.7，因此仅在上述新 runtime 目录安装 3.3.7，通过 PYTHONPATH 使用；原 venv 未修改。实际 NumPy 为 2.2.5。

- GitHub 固定提交的 G2 subtree 与隔离副本 **34/34 Git blob SHA 完全一致**，结束时再次核对。
- `surface_sampling.py` SHA256 保持：
  `763f945ae6f282abd7f69dbe7dbef9cb20d1990fa2a9f34159f6b63ae95cd967`。
- 使用空 CUDA_VISIBLE_DEVICES，OMP/BLAS 单线程。
- 软件渲染强制 Mesa/llvmpipe，实际 GL_RENDERER 为 `llvmpipe (LLVM 20.1.2, 256 bits)`；未运行 GPU、模型推理或训练。

| 项目 | GPT 独立结果 | 证据范围 |
|---|---|---|
| G2 pytest | 259 PASS，0 failure/error/skip | 原 207 testcase ID 全部保留，新增 52 |
| 作者 software_projection_check 原程序 | 54 组 / 864 点，最大 RGB 差 1 字节 | 自建 box 方向/材质组合 |
| sRGB primitive 负控 | 保持 unsupported | 不能推广成 mesh 同样已保护 |
| 代码身份与 sampler | 精确一致 | 不修改生产实现 |

864 点的直接渲染对照全部来自 box 夹具。该结果不应描述为 cylinder/sphere/ellipsoid 均已完成直接渲染验收。源码/单元测试、渲染夹具和真实房屋验收分别记录。

## 4. 真实两布局、四帧来源与角色

按原始 scene closure、ep_meta 和状态记录，恢复 Layout1/10 的 frame0、frame200。未重放 actions。全量 inventory 不提供角色时保持 UNCLASSIFIED / AUDIT_ONLY，无点云、无 COMPLETE。

| 项目 | Layout1 | Layout10 |
|---|---:|---:|
| 每帧全部 compiled geom | 1,020 | 2,115 |
| 每帧 SOURCE_BOUND 原节点 | 1,020 | 2,115 |
| geometry valid | 1,019 | 2,113 |
| geometry rejected | 1 | 2 |
| 单面材质 probe valid | 394 | 830 |
| 单面 probe unsupported/translucent | 625 | 1,283 |
| 因 geometry 拒绝而未 probe | 1 | 2 |

单面 probe 只表示探测接口结果，不是颜色覆盖率。全部 3,135 个 geom 的原节点证据与 compiled signature 在 frame0/200 间一致。model closure、真实 state row 与前轮原始输入对应一致。

进一步回溯实际 mesh.file→原资产 model.xml/class、primitive 生成器及精确几何配对、机器人组成/原 body、官方实例与 region 注册来源。仅将逐项有证据的角色绑定到新 inventory 的 signature/node hash：

| 角色 | Layout1 | Layout10 |
|---|---:|---:|
| robot | 79 | 79 |
| auxiliary | 93 | 177 |
| collision | 469 | 933 |
| visual | 218 | 497 |
| **UNCLASSIFIED** | **161** | **429** |
| 严格角色断言核对通过 | 859 | 1,686 |

这是有据的部分角色表，仍不是完整角色认证。未知项没有被改成 auxiliary。

- 全部非机器人 mesh 原资产 class 回溯完成：Layout1 visual94/collision109；Layout10 visual190/collision235，无未映射或角色冲突。每布局另有 72 个 robot mesh，归入上表 79 个 robot geom 的组成/body/原资产上下文证据，未计入此处 203/425 个非机器人 mesh。
- 两布局 79 个 robot geom 有 robot0_base 组成及原资产来源；真实 mobilebase 近退化 mesh 由该依据排除。
- Layout10 纸巾仍明确 visual；不能因采样失败改为 auxiliary 或 unknown。
- Layout1 两组无官方 fixture 身份的有限墙体使用 MJCF-only、同 body 精确 collision/visual 配对证据，没有伪造 ep_meta。
- Layout10 两个 basket spawn 根据原资产独立 spawn class 归 auxiliary。
- 未确认的正 alpha/group1 项仍有 Layout1 五个 Counter 顶面，以及 Layout10 十三个窗口背景/Counter 顶面。其他未知还含嵌套 region、handle、拆分 primitive 和透明液体；这些都不能据名称或透明度直接补成排除项。

完整逐项依据留在服务器 `f1b2_source_role_triage_by_reviewer.json`（7,321,325 bytes），SHA256：

`9539b43740b605ceb480a4d4728d6acc5ace935861a54fdb5075e4c500a9035f`

## 5. 实际 source-bound 候选导出

使用 `require_role_evidence=True`、`allow_unclassified=True`、`allow_partial_color=True`，所有已确认 visual 进入导出；未知角色保留完整 inventory 缺口。

### Layout1：两帧 PARTIAL_SOURCE，磁盘证据 PASS

| 项目 | frame0 | frame200 |
|---|---:|---:|
| 声明 visual / 实际采样 geom | 218 / 209 | 218 / 209 |
| 采样点数 | 1,110,591 | 1,110,591 |
| 有效颜色点 | 1,022,333 | 1,022,333 |
| 无效颜色点 | 88,258 | 88,258 |
| 有效颜色点占比 | 92.053060% | 92.053060% |
| 面积加权有效样本估计 | 94.803845% | 94.803845% |
| 未确认角色 | 161 | 161 |
| 状态 / COMPLETE | PARTIAL_SOURCE / 无 | PARTIAL_SOURCE / 无 |

218 中的另外 9 个 visual 当前透明，按现有规则未采样。无效点逐项原因两帧相同：

- UNSUPPORTED_APPEARANCE：1,452。
- TRANSLUCENT_SAMPLE：72,496。
- CUBE_FACE_TIE_DIFFERENT_COLOR：14,310。

这些比例只适用于已声明、已采样的表面；面积项是三角采样权重估计。它们既不是整屋颜色完整率，也不是连续表面覆盖认证。未知可见项、无效材质和真实源画面图案/方向人工核对仍待完成。

两帧 color_audit.npz SHA256 相同：

`70e526fdf2ef965650ff687ebb72aed1b9bc1087a03fc1de4adbd1ff7cd65d75`

实际使用 JSON 读回的 manifest 和 precolored.txt 路径，验证文件 hash/bytes、点数、原 cloud mask、geom/face/reason/面积以及 coverage 一致，均 PASS。frame 状态和 cloud hash 分别保留，未把相同颜色审计误当作相同动态状态。

**复验脚本更正：**初次 reviewer helper 将内存中的 export 返回值（reason 字典为整数 key）及 ndarray 传给面向磁盘文件的校验器，导致 Layout1 原日志出现错误 REJECTED 标签。原日志保留；未重新导出，通过正确接口复读已有文件后 PASS。权威结果为 `f1b2_source_bound_candidate_disk_verification.json`。这不是候选代码的第三个问题。

### Layout10：两帧在纸巾网格拒绝，无最终 cloud/manifest/COMPLETE

`paper_towel_dining_area_group_g1`，geom2095，原资产确认为 visual。原输入 6,094 面中，2 个精确零面 ID1977/2256 可按既有策略丢弃；另四面不是零：

| 原输入 face ID | 面积近似值（m²） | 精确有理数叉积判定 |
|---|---:|---|
| 1941 | 1.793788166013045e-15 | 严格大于零 |
| 2357 | 3.325828320374465e-15 | 严格大于零 |
| 2374 | 1.789972592506180e-15 | 严格大于零 |
| 2646 | 4.225609778114889e-15 | 严格大于零 |

精确判定基于实际输入 float32 所表示的坐标，不把浮点近零当精确零。两帧均触发 `SamplingFailure: nonzero near-degenerate visual triangle`，没有最终点云/manifest/COMPLETE。

这是仍然开放的真实资产/采样 Gate，既有严格策略按设计工作。不能为通过本轮而删这四个正面积面、降低阈值、替换资产或隐藏已知 visual 身份。后续若需支持这些面，应单独提出能保留正面积几何及原 face/UV 映射的数值方案并独立验收。

## 6. 旧有效子集与 native 的实际通过范围

### 旧子集四帧数值回归

沿用已在 F1-A2/F1-B 验收的 TEST_ONLY 声明子集，仅用于回归：

- Layout1：4 个 WallAccessory + obj + distr，57,744 点/帧。
- Layout10：5 个 WallAccessory，22,188 点/帧。
- 两布局各 frame0/200，与前轮 F1-B 对应数据逐行数值完全相同：XYZ 最大差 0，RGB 和 color_valid 精确相同。
- distr 仍只丢弃 128 个精确零面，保留 7,792 面及原 face ID→UV。
- 旧子集 metadata 对其他 geom 的测试排除不能充当新整屋角色依据，未用其绕过纸巾失败。

MuJoCo 从原 3.3.1 改为 B2 所要求的 3.3.7 后，使用未改的既有 geometry exporter、相同原 closure/state/已知 region 参数，在新目录重导出四帧 native geometry。新 source SHA 合法变化，未修改旧 manifest 或冒用旧 source hash：

| 布局 | 新 3.3.7 source SHA256 |
|---|---|
| Layout1 | ebaa20a17435c369f1dc2726af13c5e044afa23f351684c510166815bf7397a7 |
| Layout10 | 38cf4cbe5e74e33eaf98ececa8ebfece86e7a95381e5524a65c6810585085fe4 |

### P0 TEST_ONLY harness：相同 ColorCloudMap 组件四帧 PASS

现存可核实 binary 来自 P0 e86c384 harness。以下三份实际 catkin 源码与固定 nav_sg `2009fae35d86579bb22c273fb97ec1bf0835b533` 的 Git blob 精确相同：

| 文件 | Git blob SHA |
|---|---|
| mapping_8_3/mapping/src/utils/color_cloud_map.cpp | 5c91a9eafd8eeea69cc8f87152a0f3ec8727cf21 |
| mapping_8_3/mapping/include/mapping/utils/color_cloud_map.h | 87a949cd4cfd0507aa48ac88fbacd9608564525b |
| mapping_8_3/mapping/src/map_input/precolored_cloud.cpp | c56cb3195674e36e5a4523fe53ea29e1ecbe0ee4 |

binary SHA256：`1327d8f658bf47adbcbf6ed956613344fbbf1326805ad0712a7dd9d39f0ad36f`。libmapping.so SHA256：`1037f220604853b01101e0c949c20d5b9843d321c5cdcc24243a74c6d7920f4f`。

`gt_oracle_native.cpp` 与 `native_gate.sh` 不同于完整固定 2009fae35。因此本轮记录为“P0 TEST_ONLY harness + 相同 reader/fusion 组件”，**不记为完整 2009fae35 native 验收**。

使用新 3.3.7 geometry 和上述旧有效子集，projection slab=0.15–1.8m，独立未占用 ROS 端口；两布局 harness 均正常退出、GT_GEOMETRY_SMOKE_PASS/COMPLETE。读取实际 PLY 验证 vertex 数、有限 XYZ、RGB 范围和 hash；scene/source/frame/map 与输入一致：

| 布局 / frame | 输入点 | 接收点 | 无效色跳过 | native color voxels |
|---|---:|---:|---:|---:|
| Layout1 / 0 | 57,744 | 57,744 | 0 | 108 |
| Layout1 / 200 | 57,744 | 57,744 | 0 | 109 |
| Layout10 / 0 | 22,188 | 22,188 | 0 | 56 |
| Layout10 / 200 | 22,188 | 22,188 | 0 | 56 |

该输入仍使用 TEST_ONLY GT geometry/objects、NOT_CERTIFIED known region。它证明旧子集可以经过当前相同 reader/fusion 组件；并未验证 Layout1 的 111 万点 partial 候选、Layout10 的整屋候选或普通对象感知。没有从这些局部 native PLY 生成整屋六图并提交人工验收。

## 7. 下一轮交接范围

**下一批建议命名 F1-B2-R1，在独立候选分支只关闭上述两项 P2，提交新的固定 SHA。**

1. 给 mesh 显式 2D sRGB 补 conservative invalid guard 和 strict/partial/linear 正负控。
2. 修正 include 根 wrapper 语义，补四 wrapper 实际编译与来源绑定回归。
3. 保留原 259 项 testcase 与 207 项历史基线；保留 exact-zero sampler、原 face/UV、默认/linear mesh 数值、来源闭包、状态和证据防降格合同。
4. 作者只使用自建 CPU 夹具完成 RED/GREEN 与全回归，发布固定源码、测试和复验说明后交 GPT 服务器再验。无须为这两个代码问题下载服务器原始资产。
5. 真实 source-role 剩余 161/429 项、纸巾正面积面方案和真实材质图案/方向对照按各自证据继续处理。不得靠放宽角色、阈值或标记关闭 Gate。
6. 完整 native 固定构建及四帧、[nav_sg #8](https://github.com/wxwy/nav_sg/issues/8) 普通 Floor/Wall/Room/Island、真实 YOLOE/SigLIP 感知、native 六图与人眼几何/颜色验收仍待后续完成。

本轮不修改作者实现、V3、原 nav_sg 工作区、Cosmos Gitlink、原 PR、训练/缓存或原始数据；未合并、未创建 Draft PR、未启动 GPU/模型/rollout/训练。正式结果仅写入独立 docs review 分支及 Issue #26。

## 8. 封存索引

服务器证据根目录：

```text
/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_n6_f1_b2_193a05e3_gpt_accept_20261108/evidence/
```

机器复验汇总：`f1b2_gpt_independent_review.json`，SHA256：

`e550d6dca8f72422d7d2930a5e29f3e176f302df69ce40a1c24caaa5c4e77f18`

该 JSON 包含 28 份关键证据的 bytes/SHA256 索引、两项缺陷、真实角色与四帧摘要、正式 Gate 状态和 helper 更正说明。主要证据：

| 证据文件 | 用途 |
|---|---|
| f1b2_final_source_identity_verification.json | 34 文件固定身份、四帧节点/签名稳定性 |
| f1b2_259_independent.xml | 独立全测试 |
| independent_207_testcase_retention.json | 原 207 项保留 |
| software_projection_independent/software_reference.json | 实际 CPU 864 点渲染对照 |
| f1b2_independent_srgb_mesh_probe.json | P2-B2-01 |
| f1b2_independent_include_wrapper_probe.json | P2-B2-02 |
| f1b2_independent_fourframe_complete_compiled_geom_summary.json | 全 geom AUDIT_ONLY 四帧 |
| f1b2_source_role_triage_by_reviewer.json | 全量逐 geom 原始来源审查 |
| f1b2_paper_towel_exact_positive_triage.json | 正面积近退化精确证明 |
| f1b2_source_bound_candidate_disk_verification.json | 真实候选最终权威结果 |
| f1b2_legacy_subset_fourframe_parity.json | 旧子集四帧数值回归 |
| f1b2_nativegeometry_mj337_reexport_summary.json | 新版本 geometry 来源重绑定 |
| f1b2_p0_same_components_native_fourframe_verification.json | 受限 P0 native 四帧验证 |

所有点/面积/角色数量均有明确范围。F1-B2 不因测试全绿、局部 COMPLETE、软件夹具图片或点数增加而取得整屋认证。
