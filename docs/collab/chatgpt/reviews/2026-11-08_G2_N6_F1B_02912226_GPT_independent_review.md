# GPT Independent Review — G2-N6 F1-B / `02912226` / 2026-11-08

**Verdict: APPROVE（严格限于精确零面积面采样与全 geom AUDIT_ONLY 预审）；整屋真实颜色/来源认证仍 BLOCKED，未获 Full-GT Gate。**

## 固定实现与独立证据

- 固定 PSM `029122268ea535d8b3c74c0b3fb2b0d0302a828f`，基础 `28926f6c64db37e9cc71e9cdf24f27a60c72f826c87`；native `2009fae35d86579bb22c273fb97ec1bf0835b533`、Cosmos Gitlink `1ca308055fc41fb69efaeb9efaa23808f164a18e` 保持未改。
- 从 GitHub 固定 SHA 独立读取/复用源码，在 data 全新隔离目录，**26/26 个 G2 文件 Git blob SHA 逐个精确一致**。未修改 V3、N5/N6 正式 repo、训练/缓存、原始 MJCF/状态/模型，未外传私有资源。
- 原生 RoboCasa Python/MuJoCo CPU 独立运行 **207/207 G2 tests PASS，零失败/错误/跳过**。

## 真正的 Layout1/10 mesh 验证

- Layout1 `obj_g0`：4048 原编译三角面 / **0** 精确零面丢弃 / sampled **12240 points** / UV material valid。
- Layout1 `distr_g0`：7920 原编译三角面、**128 个严格零面积面**，保留 **7792**；`discarded_area_m2=0`、原始 local face IDs 未重排，`mesh_facetexcoord` 仍用原索引，原始编译全 geometry SHA 保留；sampled **23376 points**、真 UV bilinear asset-albedo 有效。这关闭此前 `degenerate visual triangle` 对正常任务对象的误阻塞。
- 实际低预算负控：`distr_g0` 1000点预算，原 face ID 333 判定需要1002点，拒绝且只写 source/state-bound `sampling_failure.json`；**没有 precolored.txt、manifest 或 COMPLETE**。

## 两场景四帧真实 TEST_ONLY 声明子集导出

| Scene | frames | sampled true asset-albedo points/frame | included visible source mesh | All geoms audited |
|---|---|---:|---|---:|
| Layout1 | 0 / 200 | **57,744** | 官方 fixture 4个 + `obj_g0` + `distr_g0` | 1,020 |
| Layout10 | 0 / 200 | **22,188** | 官方 fixture 5个 | 2,115 |

- 四帧原 N5 `source_sha256` 与 `mujoco_fullphysics` row SHA 精确匹配。先前 F1-A2 通过的 Layout1 34368点/帧和 Layout10 22188点/帧，**新旧解析后的 XYZRGB+color_valid 点数据逐行数值完全一致（未声称原始文本文件逐字节一致）**。新增 `distr` 为源身份明确的视觉点，而不是原像素修改。
- 四帧的 `completion_scope=DECLARED_VISUAL_GEOMS_ONLY`、`training_ready=false`、`full_scene_source_certified=false`，未经外部审核 `verify_full_scene_review` 拒绝；**不能把这个局部 COMPLETE 或所选点 100% 有效颜色冒充整屋完整度**。视觉资产来源 hash 随源码更改符合预期。

## 整屋原始 geom/material 预审（新增工具实测）

在**没有角色声明**的严格输入下，`g2.sim.asset_inventory` 对 Layout1/10 两帧全部 1020/2115 个 geom 执行编译源/状态/几何/材质审计，未猜测角色，全部保持 `UNCLASSIFIED`、`AUDIT_ONLY`、无点云、无 COMPLETE、`surface_color_coverage_measured=false`。

| Source audit | Layout1 | Layout10 |
|---|---:|---:|
| All compiled geoms | 1020 | 2115 |
| Geometry valid | 1019 | 2113 |
| Conservatively rejected geometry | 1 | 2 |
| Group1 nontransparent geom candidates | 277 | 548 |
| Group1 textured candidates | 212 | 477 |
| Textured single-face probe valid | 84 | 175 |
| Textured single-face unsupported / invalid | 128 | 302 |
| Still UNCLASSIFIED roles | 1020 | 2115 |

**以上只是单面 probe，不是整屋真实 RGB 覆盖率，更不能把 MuJoCo group1 当官方 source role**。具体空缺主要是 textured box/cylinder 等 primitive projection（Layout1 textured box 116 + cylinder4，Layout10 textured box 295），及少量纹理 mesh UV/opacity。需要全表面采样和独立来源审核。

**被拒绝的近退化正面积几何**：Layout1/10 `mobilebase0_g7_vis`（机器人 mesh）均拒绝；Layout10 `paper_towel_dining_area_group_g1` 也有 4 个非零近退化面。它们不能被当前的“只跳零面”策略暗中删除，需对原始来源逐 geom 判定保留/排除及可证处理。

官方 ep_meta fixture/body 祖先链候选统计（非角色认证）：Layout1 可见 Group1 的277个 geom 中，210个能匹配 fixture root、2个能匹配 task object root；Layout10 548个中485个能匹配 fixture root。剩余多数涉及机器人与独立 MJCF 几何，缺少官方 fixture key 不代表不存在。**全部需要 source/role/material reviewer 进一步确定，不能自动赋权为房屋 GT**。

## Codex 下一步最小要求（另建 F1-B2 Gate）

1. 从真实 `ep_meta.fixtures`、`object_cfgs`、编译 body ancestor、MuJoCo source assets 和视觉/碰撞几何逐个建立 **有来源依据的完整角色表**，保留 `UNCLASSIFIED` / ambiguity 及 robot exclusions；不能用 group、name 作为单独真值来源。重点检查墙/柜/地板与机器人。
2. 为真实 textured box（墙/柜等）和其他未支持 primitive 提供与 MuJoCo 采样约定一致的 UV/投影算法或严格部分颜色 gate，保留未知颜色 mask。补有效颜色的**全表面**统计、遮挡高层/下层的 BEV 对照，不把 proxy geom_rgba 当真实外观。
3. 对 paper-towel 非零近退化面做 source-specific triage，不能静默按阈值丢弃。机器人相关 mesh 若明确从 prescan exclude，要有验证来源和排除理由。
4. 重新产出 Layout1/10 frame0/200 的完整 source-bound candidate cloud+audit；先独立材料来源 Gate，再真实 nav_sg 快照、人工六图、Cosmos。首轮继续 `training_ready=false`，不可动 V3/Gitlink/训练。

## data 本地证据（无私人文件上传）

根目录 `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_n6_f1_b_02912226_gpt_accept_20261108/evidence/`。
- `f1b_207_independent.xml/.log`
- `f1b_real_obj_distr_compiled_face_uv_audit.json`、`f1b_real_fourframe_subset.log`
- `f1b_real_previous_valid_surface_exact_parity.json`、`layout1_distr_exact_zero_budget_negative/sampling_failure.json`
- `f1b_independent_fourframe_complete_compiled_geom_summary.json`、`f1b_independent_all_geom_material_breakdown.json`、`f1b_real_visual_source_parent_ancestry_coverage.json`
- `f1b_GPT_independent_review.json`（结构化结论）及本文件。

**Gate：F1-B exact-zero 和 inventory-AUDIT_ONLY 准予冻结；Full-house source role/material 不予通过；nav_sg #8 normal roots、真实模型、六图/Island 人工、PSS/Cosmos 仍 OPEN。**
