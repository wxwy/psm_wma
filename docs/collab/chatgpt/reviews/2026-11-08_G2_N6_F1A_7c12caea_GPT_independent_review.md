# GPT independent review | G2-N6-F1-A | 7c12caea | 2026-11-08

**Verdict: REQUEST_CHANGES（局部通过，真实 object_cfgs 类别兼容待修）**。

- 固定实现 `7c12caea2c0a4b9acc24d40da9e7c5a5345888f3`，基于 `f1e4f1f0`；native `2009fae3` 未改；Gitlink `1ca30805` 未改。
- GitHub 固定 SHA 下 20/20 个 `g2/` 源/测试文件 Git blob hash 与本次新隔离服务器源码完全一致。
- data 服务器真实 RoboCasa JSON/MJCF/states 未外传，旧 N5 / P0 / V3 / nav 生产目录均未修改。
- 独立 Python：**129/129 PASS**。固定新身份测试 **30/30 PASS**；相同测试在旧源码 **30 项中 16 项 FAIL**（符合作者报告核心 RED→GREEN）。
- 两个真实源的完整 source/row state SHA 与 N5 对齐；四帧独立 `g2.sim.prescan.export` 成功。官方 fixture dictionary `source_kind=ep_meta`、`source_category=WallAccessory` 与实际 MuJoCo 祖先 body 一致，每 fixture 6 组坏输入拒绝。
- N6 texture UV 输出对照先前 N5 point cloud：Layout1 / Layout10 **RGB byte-for-byte exact**，XYZ 最大差分别 7.00e-12m / 8.11e-12m。
  
## Real frame scope

| Scene | Full compiled geoms in audit | Official WallAccessory visual geoms selected | Selected points/frame | f0/f200 | Full scene |
|---|---:|---:|---:|---|---|
| layout1 | 1020 | 4 | 22128 | 0、200 均 PASS | 整屋未认证 |
| layout10 | 2115 | 5 | 22188 | 0、200 均 PASS | 整屋未认证 |

四份输出具有 `completion_scope=DECLARED_VISUAL_GEOMS_ONLY`、`training_ready=false` 和 `full_scene_source_certified=false`。**当前工具会为声明子集写 COMPLETE，不能把该 marker 解释为整屋完成。** 没有真实独立整屋来源审核，`verify_full_scene_review(...,None)` 全部拒绝。注意：`source_audit.full_scene_review_eligible=true` 即使在几乎全部 geom 被 TEST_ONLY auxiliary 排除时也会出现，不能将 eligible 作为人工接受证明。

## Blocking: official `object_cfgs` source shape still incomplete

位置：`g2/sim/prescan.py:89-100`，特定漏洞在 `('obj_groups','obj_type','cls')` 字段白名单。

原始 Layout1 `ep_meta.object_cfgs`：
- `obj` 索引0：`obj_groups=['tool','utensil']`，新版允许；源 `info.cat=whisk` 也应被保留为细分类别来源。
- `distr` 索引1：没有上述任一字段，但有 `type='object'` 与 `info.cat='soap_dispenser'`。新版在读取真实记录时仍抛出 `ContractError: official object category provenance is missing`，即使显式指定 `source_category_field='info.cat'` 仍失败。

这与 F1-A “官方对象列表身份及类别校验”验收条件冲突：请 Codex 在保持 strict pointer/唯一名称的前提下，支持 `info.cat` 的原始嵌套来源（必要时保留 `type` 的独立粗类型，不能把广义 type 伪装成细类），补 `obj`/`distr` 两类真实结构与负控。**不允许将其换成 `source_kind=mjcf` 静默绕过官方类别证明**。

## Gate limits

F1-A fixture＋source scope：PASS；F1-A object_cfg category coverage：REQUEST_CHANGES；四帧真实局部颜色导出：PASS，**仅是 4/5 个墙面配件，不是完整建筑**；native 普通结构根、整屋视觉材质、真正模型推理、Room/Island 六图、训练：OPEN/NOT_RUN。

## Evidence (data server, no private file uploads)

`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_n6_f1_a_gpt_accept_20261108/evidence/`
- `f1a_independent_129_tests.log/.xml`
- `identity_baseline_RED.log/.xml` 和 `identity_fixed_GREEN.log/.xml`
- `f1a_real_four_frames_gpt_report.json`
- `real_source_old_visual_uv_parity.json`
- `f1a_gpt_independent_review.json`

**Decision:** 请 Codex F1-A2 最小修复上述真实任务物体类别，同时保留 129 测试／完整 geom 审计／subscope gate，生成新固定 SHA 后再交 GPT 复验。不要在此之前宣布整屋来源通过或进入 Cosmos 训练。
