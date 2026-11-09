# G2-N6-F1-B2-R1 — GPT 固定 SHA 独立服务器验收

- 日期：2026-11-09（CST）
- 固定实现：`3b6c6055e36824be33ed947745aa3e5b839da832`
- Git tree：`4a5a888148c5670d628c3de6f4c0bdd6d6079f14`
- 作者交接：[Issue #26 / 6729052936](https://github.com/wxwy/psm_wma/issues/26#issuecomment-6729052936)
- 本轮基准：旧 `193a05e3` 的 GPT [`REQUEST_CHANGES` 两项 P2](https://github.com/wxwy/psm_wma/issues/26#issuecomment-6723181393)。

## 结论

**APPROVE（严格限定于 F1-B2-R1 两项 P2 修复与无回归 Gate）。** 不批准整屋来源/材料认证，不表示完整 nav_sg native 正常链路、六图或训练已通过。`training_ready=false`，`full_scene_source_certified=false`。

服务器全新隔离 Git sparse checkout 固定 commit，实际 HEAD/tree 与 GitHub 完全一致，**35/35 G2 blob SHA** 逐文件校验通过。运行时仅 `g2/sim/source_geometry.py`（增加 4 行）与 `g2/sim/source_roles.py`（include root wrapper/默认值记录）变化；原 259 测试文件未改。`surface_sampling.py` SHA256 仍为 `763f945ae6f282abd7f69dbe7dbef9cb20d1990fa2a9f34159f6b63ae95cd967`。新工作树 `git status` 干净。

| 固定 CPU 验证 | 独立结果 |
|---|---|
| R1 完整 G2 pytest | **274 passed，0 failure/error/skip** |
| 旧 `193a05e3` 运行本批相同 15 项测试 | **8 FAIL / 7 PASS** |
| R1 运行相同 15 项 | **15 PASS** |
| 测试 ID 保留 | **259/259**，其历史 207 项保留；新增 15 项 |
| 自建 sRGB mesh 实际 CPU llvmpipe | R1 invalid，strict 无 cloud/manifest/COMPLETE，partial `PARTIAL_COLOR` |
| 四种 included-root wrapper 实际 MuJoCo 编译 | 全部 `SOURCE_BOUND`，strict 导出通过 |

## P2-B2-01：显式 2D sRGB mesh — CLOSED

固定 193 的 legacy mesh 2D UV 路径把未支持的显式 sRGB 当作有效；R1 在字节采样前保守拒绝。复用上一轮 **GPT 自建负控**，使用 MuJoCo **3.3.7 + CPU llvmpipe（GL_RENDERER 实际含 llvmpipe）** 新源重跑，同时独立复跑作者三个 mesh 颜色空间软件对照。

| Mesh 纹理 | 实际渲染 RGB | R1 `color_valid` / reason | strict | partial |
|---|---|---|---|---|
| 显式 sRGB（素材 RGB128） | `[55,55,55]` | **false / UNSUPPORTED_APPEARANCE(1)** | `ContractError`，无 cloud/manifest/COMPLETE | `PARTIAL_COLOR`，有效率 0，未认证 |
| linear | `[128,128,128]` | true / 0 | 声明子集 COMPLETE | 声明子集 COMPLETE |
| default | `[128,128,128]` | true / 0 | 声明子集 COMPLETE | 声明子集 COMPLETE |

注意：sRGB 无效点仍可包含未定义语义的占位 RGB 字节（自建夹具为 `[255,255,255]`），**不能忽略 `color_valid=0` 将其当作真颜色**；逐点 reason=1、有效位=0 已独立核对。此处的子集 COMPLETE 不代表整屋认证，三个夹具均 `training_ready=false`。未实现 sRGB 颜色变换，也未宣称验证其他 primitive 或整屋渲染。

## P2-B2-02：included document root wrapper — CLOSED

重新运行上一轮 GPT 独立 MuJoCo 编译复现，而非仅依赖新增单元测试。片段根分别为 `mujocoinclude`、具名 `body`、`default`、`asset` 时，实际 compiled geom 都属于同一个 `fixture_body`。R1 四种情况均 `SOURCE_BOUND`、实际源节点数为 1、strict 和 allow-unclassified 均正确通过，没有假 `UNCLASSIFIED`。新单元测试覆盖真正的内层 body/default、嵌套 include chain、原始 XML path 和 hash。修复只忽略被包含文档**根**的假语义，未忽略合法子节点。

## 原始 RoboCasa Layout1/10 四帧真实数据复验

只读服务器原始 source closure、`ep_meta`、FULLPHYSICS 状态，使用原始角色证据声明与旧 native geometry manifest，按 R1 固定代码重新导出；未从服务器外传数据。先前局部声明子集四帧均再次通过：Layout1 frame0/200 每帧 **57,744 点**；Layout10 frame0/200 每帧 **22,188 点**。与前轮逐行 XYZ/RGB/color_valid 数值完全相同，最大 XYZ 差 **0 m**。Layout1 `distr` 仅丢弃 **128 个精确零面积面**，保留 **7,792 面**及原始 face ID/UV。

| 真实源绑定候选 | Layout1 | Layout10 |
|---|---|---|
| frame0 / frame200 | `PARTIAL_SOURCE` / `PARTIAL_SOURCE` | `REJECTED` / `REJECTED` |
| 已确定 visual（实际采样） | 218（209） | 已知 visual 纸巾面触发保护拒绝 |
| 每帧采样点 / 有效色点 | **1,110,591 / 1,022,333** | 无完整候选 cloud |
| 逐点数据 / color_audit 对照前轮 | **数据行 SHA 完全相同，NPZ 各数组完全一致** | 同一保护性拒绝 |
| 角色未知项 | **161** | **429** |
| COMPLETE / training_ready | 无 / false | 无 / false |

Layout10 `paper_towel_dining_area_group_g1` 的 face `1941、2357、2374、2646` 仍严格正面积但近退化，故 frame0/200 均保护性拒绝。原 6094 面中精确零面 `1977、2256` 与该四面区分处理。R1 未删正面积面、未降阈值、未把纸巾改作辅助角色。没有 cloud、manifest、COMPLETE；这不是本轮两个 P2 的失败，而是独立开放的真实资产/数值 Gate。

**身份绑定补充：** 原始几何 `source_sha256` 和 `model_source_sha256` 正确保持不变，frame0/200 `state.row_sha256` 匹配。由于生产视觉代码变化，**`visual_source_sha256` 与 `adapter_source_sha256` 正确变化**，未使用旧视觉 producer 身份伪装新工件。这个区分已做独立两帧 JSON 核验。

Layout1 的 92.053% 颜色有效率只针对**已声明且已采样**的表面；不是整屋覆盖认证。保留的 unknown roles、材质图案/方向、透明与 cube 边界必须单独验收。

## 尚未关闭的 Gate 和操作边界

本轮代码验收不取代：Layout1/10 剩余 **161/429** 个真实 geom 角色审定；Layout10 正面积纸巾面处理；真实整屋材质外观/颜色/方向人眼对照；完整固定 `nav_sg 2009fae35...` 原生四帧（前轮只有 P0 TEST_ONLY harness + 三个相同 reader/fusion 源码）；`nav_sg #8` 普通 Floor/Wall/Room/Island 结构；真实 RGB-D/YOLOE/SigLIP；六图+Island 人工 Gate；PSS/Cosmos/训练。原两布局未触发这两处 P2 的旧事实仍成立。

此轮未启动 GPU、模型、rollout 或训练；未改 V3、nav_sg 工作树、Gitlink、生产缓存或原 PR；未合并、未创建 Draft PR。仅新隔离服务器副本执行，只发布**文本摘要**和源码评审；MJCF、RGB-D、state、PLY、点云、逐项原始审计继续留在 data。

## 可追溯证据（data 服务器本地）

```text
/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_n6_f1_b2_r1_3b6c6055_gpt_accept_20261109/evidence/
```

- `r1_github_35_blob_identity.json` — 固定提交/tree、35 文件 blob。
- `r1_independent_274.xml`、`r1_baseline_193_red.xml`、`r1_independent_259_retention_and_redgreen.json` — 独立 GREEN/RED 与测试保留。
- `r1_independent_srgb_mesh_probe.json`、`r1_independent_include_wrapper_probe.json` — 两项 GPT 旧反例的新结果。
- `r1_authored_software_reference_reexecution/mesh_software_reference.json` — 作者三个自建 mesh 测试的独立环境重执行。
- `r1_legacy_subset_fourframe_parity.json` — 旧声明子集四帧完全数值一致。
- `r1_real_source_bound_fourframes_summary.json` — 真实候选四帧重导出/拒绝。
- `r1_correct_visual_vs_geometry_epoch_identity.json` — 几何 SHA 保持、视觉 producer SHA 更新。
- `r1_gpt_independent_acceptance.json` — 机器结论和重要文件 SHA256 封存索引。

**机器结论：** `APPROVE_SCOPE_LIMITED_TWO_P2_AND_REGRESSIONS`；`r1_gpt_independent_acceptance.json` SHA256 **`9fcbfb0a582351253af9b3c283f877086bfdedaf9084f8387f93015caefa4f48`**。下一轮不需重复修复两个 P2；应把资源放到真实角色完整性、纸巾正面积采样策略和完整 native/视觉人工 Gate。
