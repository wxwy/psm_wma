# GPT 独立复验 — G2-N6-F1-A2 固定实现 `e7308332`

**结论：APPROVE（严格限定 F1-A2 官方 `object_cfgs.info.cat` 类别与来源门禁）；F1-B 真实整屋导出仍 OPEN。**

- PSM-WMA frozen runtime SHA：`e73083324055af459d2c6c65bb52bda142bb4833`，父提交 `08a1bbb14db4aa5b05a51724f27a60c72f826c87`；native 同步实现仍 `2009fae35d86579bb22c273fb97ec1bf0835b533`；Cosmos Gitlink `1ca308055fc41fb69efaeb9efaa23808f164a18e` 不变。
- GPT 在 data **新隔离源码副本**核对 `22/22` 个 `g2/` 文件 Git blob SHA 对 GitHub HEAD 完全一致；未改写 V3、nav_sg、N5、PR 或原始 MJCF/状态。
- 独立 CPU：相同 31 项新测试在原 `7c12caea` **6 FAIL/25 PASS**，在本提交 **31/31 PASS**；完整 G2 Python **160/160 PASS，0 failure/error/skip**。
- 真实 RoboCasa Layout 1 `ep_meta.object_cfgs[0]` 的 `obj`：默认来源保留 `obj_groups=['tool','utensil']`，并单独保留 `fine_category=info.cat:whisk`、`coarse_type=type:object`；显式 `source_category_field='info.cat'` 得 `whisk`。
- `object_cfgs[1]` 的 `distr`：没有 groups/obj_type/cls，默认和显式 `info.cat` 均正确映射 `soap_dispenser`；`coarse_type=object` 独立保留。两者均绑定真实编译 MuJoCo body（`obj_main` ID181、`distr_main` ID182），实际 `geom_audit_row` 在 frame0/200 均一致，**52 项源自真实 object_cfgs 的错误输入变体全部拒绝**。
- 动态状态：`obj` frame0→200 世界系位移约 0.120525m，`distr` 约 0.000039m，原有 `source_sha256` 与 N5 状态行 SHA 完全对齐。
- 新 SHA 的四帧 **TEST_ONLY 声明子集**导出成功：Layout1 4个真实 WallAccessory + `obj_g0`（5 visual geoms，34,368点/帧）；Layout10 5个 WallAccessory（22,188点/帧）；四帧 `completion_scope=DECLARED_VISUAL_GEOMS_ONLY`、`training_ready=false`、`full_scene_source_certified=false`。**不得将这些 `COMPLETE` marker 或所选点的有效颜色比例解释为整屋扫描成功**。

## 本批之外的新 F1-B 真实资产阻塞

当把 Layout1 `distr_g0` 也加入 `g2.sim.prescan.export` 时，现有 `sample_surface()` 在真实 mesh 上直接报 `ContractError: degenerate visual triangle`。GPT 逐面检查真实已编译 MuJoCo mesh：
- `obj_g0`：4048 faces、0 退化三角面。
- `distr_g0`：7920 faces，**128 个零面积退化面（1.616%）**；这些面几何面积总和严格为 0 m²。

**F1-B 最小要求**：审计并安全过滤严格零面积/数值退化三角面，保留原始 `face_id` / UV 对应与被丢弃面计数、面积、比例；不得把 0 面积三角形生成虚假的世界点，不能静默接受大量非零面积/不可审计 mesh。补真实场景负控与数值回归后，再单独复验 Layout1 的 `obj+distr` 和完整整屋材质。此项**不否决 F1-A2 类别修复本身**。

## Gate 状态

| Gate | Verdict |
|---|---|
| F1-A2 `info.cat` / coarse / groups / compiled body | **APPROVE** |
| 四帧声明子集、来源/状态哈希与 scope | **PASS (TEST_ONLY)** |
| Layout1 `distr_g0` 完整视觉网格导出 | **F1-B BLOCKED** |
| Layout1/10 整屋真实颜色与来源人工认证 | **OPEN** |
| nav_sg 普通 Floor/Wall/Island、真实 YOLOE/SigLIP、六图人工 | **OPEN / NOT_RUN** |
| PSS/Cosmos 训练 | **NOT_AUTHORIZED** |

### 服务器独立原始证据（不上传私有模型或数据）

`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_n6_f1_a2_gpt_accept_20261108/evidence/`

- `f1a2_independent_cpu_tests_summary.json`、对应 RED/GREEN/160 JUnit XML 和日志。
- `f1a2_independent_actual_object_category_body.json`、`f1a2_four_frames_partial_export_summary.json`、`f1a2_real_degenerate_mesh_diagnostic.json`。
- `f1a2_GPT_independent_acceptance.json` (summary)，`f1a2_GPT_independent_review.md`（本文件）。

**最终决定：允许将 F1-A2 的来源类别功能冻结为完成；Codex 下一步独立提交 F1-B 真实 mesh 几何处理与整屋角色/材质审计。不要将 F1-B 尚未完成误表述为已批准 N6 全流程、Cosmos 输入或训练。**
