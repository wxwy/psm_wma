# G2-F1-C（aef1ec04）与来源分析（dcd8a93d）— GPT 真实服务器独立验收

- 日期：2026-11-09（CST）。
- F1-C 固定 SHA：`aef1ec04d631ef23c9b3f04dd2ab0f11344e2f21`；tree：`3c1a4475354b7711a556ca1ab9abe9e010be6b49`。
- 角色分析固定 SHA：`dcd8a93da1f2c9ad4285140f70bb9f8c3a310cff`；tree：`c3b8f041a62d102646e70686f5cfaf5d42c41200`。
- 作者交接：[Issue #26 comment 6731248850](https://github.com/wxwy/psm_wma/issues/26#issuecomment-6731248850)；上一轮 GPT 已批准 R1：[comment 6729550170](https://github.com/wxwy/psm_wma/issues/26#issuecomment-6729550170)。
- **独立结论：F1-C `APPROVE_LIMITED_REAL_FOURFRAME_GEOMETRY_COLOR`；角色分析工具 `APPROVE_AUDIT_ONLY`。全场景真实角色认证、完整 native、六图及训练均没有通过。**

## 1. Git 身份和 CPU 回归

从 GitHub 固定两个 commit 在 data 服务器创建**全新隔离源码工作区**；源码本地取回后独立校验每个 `git hash-object` 与提交里的 tree blob：

| 验收 | 实测 |
|---|---|
| F1-C | 固定 HEAD / tree 精确匹配，**36/36** G2 blob 一致 |
| 角色分析 | 固定 HEAD / tree 精确匹配，**38/38** G2 blob 一致 |
| 角色工具对 F1-C 的更改 | 36 个既有 G2 blob **逐一完全一致**，包括采样源码 |
| F1-C 独立 pytest | **291/291 PASS**，0 failed/error/skip |
| 分析工具独立 pytest | **336/336 PASS**，0 failed/error/skip |
| 测试案例保留 | 原 R1 274/274 ID 完整保留；F1-C 增 17；分析工具增 45 |
| 旧 R1 源码运行同一 17 个新测试 | **17 FAILED**；新 F1-C 17 全 PASS |

F1-C 原 `surface_sampling` 正面积阈值策略已经正式更换。实测默认保留所有有限正面积三角面；只跳过有理数精确叉积为零的面。原始 face ID/UV/triangle hash 不改，预算、非法/非有限边界和平方范数下溢数值防护保留。新颜色审计协议 `g2_sample_color_audit_v2` 明确标记浮点面积/权重下溢，不伪造连续表面覆盖；磁盘附件完整核验。

## 2. 真实 RoboCasa 四帧 — 原始资产、状态及颜色新导出

按固定源码 `aef1ec04`，在服务器本地读取原有、未修改的真实 MJCF/mesh/material、原 episode state FULLPHYSICS、`ep_meta`、source-bound role map 和已验证 MuJoCo 3.3.7 native geometry manifest。每帧**全新**写 cloud / manifest / color_audit，复从磁盘独立验证 hashes、color_valid / reason / 原始 triangle ID、geometry/row source 与视觉 producer 新纪元。

| 布局/帧 | 实际采样点 | 有效颜色点 | 与上一轮对照 | 状态 |
|---|---:|---:|---|---|
| Layout1 frame0 | **1,110,591** | **1,022,333** | R1 数据行 SHA 完全相同 | PARTIAL_SOURCE |
| Layout1 frame200 | **1,110,591** | **1,022,333** | R1 数据行 SHA 完全相同 | PARTIAL_SOURCE |
| Layout10 frame0 | **2,135,041** | **1,990,229** | GPT 先前真实原型数据行 SHA 完全相同 | PARTIAL_SOURCE |
| Layout10 frame200 | **2,135,041** | **1,990,229** | GPT 先前真实原型数据行 SHA 完全相同 | PARTIAL_SOURCE |

- Layout1 实际采样 209 个 visual 几何（声明 visual 218 个，另 9 透明）；颜色有效率为 **92.053060%**，仍有 161 个未知来源角色。
- Layout10 实际采样 472 个 visual 几何（声明 visual 497 个，另 25 透明）；颜色有效率为 **93.217367%**，仍有 429 个未知来源角色。
- Layout10 **纸巾架** `paper_towel_dining_area_group_g1` 的原本被阻断的正面积面 `1941,2357,2374,2646` **每面生成 3 点（12 点均 color_valid/reason=0）**；真正零面积面 `1977,2256` 生成 0 点；原 geom mesh SHA `ca19d046c06afb271a0581dcf323e9a2091d98e0ff7072cd978dca9de438e05c` 不变；没有按面积滤除有效面。
- 原始模型 closure/source identity 与 state row 在四帧与原 native 几何文件匹配；新视觉代码正确生成新 `adapter_source_sha256` / `visual_source_sha256`，没有复用旧生产者 SHA 或冒用旧附件。所有 4 帧磁盘级 `verify_color_evidence` 均 PASS。
- 所有结果 `training_ready=false`、`full_scene_source_certified=false`，**没有 `COMPLETE` 标识**。声明子集颜色有效率**不是整屋覆盖率**；无法确认的对象/材质与关系仍是开放任务。

## 3. 新角色分析工具在原始四帧上运行 — AUDIT_ONLY PASS

固定 `dcd8a93d` 的 `g2.sim.asset_inventory` 在原始 Layout1/10 的 0/200 独立重新生成全部 geom 源记录，随后新 `g2.sim.role_review` 成功匹配同一场景两帧并输出逐 geom ledger + 未知项假设模板。所有来源节点/编译体身份和 state archive 均通过校验。

| | Layout1 | Layout10 |
|---|---:|---:|
| 全部编译 geom | **1,020** | **2,115** |
| 已有（尚非本轮重审的）角色声明 | 859 | 1,686 |
| 未独立确认的角色 | **161** | **429** |
| 新工具生成未知项模板 | 161 | 429 |
| 自动写入角色映射 | 0 | 0 |
| 状态 | AUDIT_ONLY | AUDIT_ONLY |

服务器当前原位 RoboCasa/robosuite 的 **9/9** 个 generator 文件 SHA256 与随候选发布的固定公开 catalog 完全匹配；这足以继续做该服务器当前版本下的逐部件来源核对，**不能仅据此保证历史 episode 构造时候使用完全相同的 generator 版本和分支**。

角色候选还没有逐项填入；`role_assignments_written=false`，`generator_semantics_independently_reviewed=false`。未把 group1/名称/是否半透明当成自动定类证据，**590 个实际未知项保持待解决**。

## 4. 用户人眼检查的下一份产物

从本轮**正式 F1-C 实际源点云**生成 Layout10 frame0/200 四方向 PNG、有效颜色过滤图及可拖动旋转的单机离线 HTML。只在 data 服务器展示：

`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_f1c_aef1_roles_dcd8_gpt_accept_20261109/evidence/layout10_colorcloud_human_preview_20261109/`

仅 `127.0.0.1:8790` 本机预览，已验证 index/HTML/PNG 可读且 JS 语法通过。**HUMAN_PENDING**，尚不能标记通过。原用户已经接受的是 Layout1 **部分彩色点云**，不是 Layout10、整屋或 Room 的验收。

## 5. 后续负责人、任务、边界

**Codex 下一个实际开发工作：** 基于两场景已生成的逐部件表及真实 generator 源码，逐项填写 161+429 未知部件的来源证据；优先 Counter 整块 visual 与 collision chunks、window background、cabinet handle/panels、region/helper、独立物体。每个结论必须绑定原 XML/compiled body/尺寸材质/生成分支/引用行和严格源码 identity；不用 group 或名称猜测，不得将实际可见物体降成 auxiliary 来降低 unknown 数。可批量制定由生成器实际逻辑支撑、能逐条落地验证的规则，余项保留 unknown。交付独立分支、固定 SHA、两场景 0/200 报告和角色映射建议，不擅自变更 V3、nav_sg、训练/缓存。

**GPT 下一次负责：** 独立复审 Codex 的真实590项决定，导出已补齐角色的整屋点云，并接入**完整**固定 nav_sg 主程序的 native四帧，确认普通 Floor/Wall/Room/Object/Island、Room footprint 与关系。旧 P0 TEST_ONLY harness **不等于完整 native**。六图+Island 必须来自真实 nav_sg snapshot，再交用户人眼确认。PSS/Cosmos 训练在这些 Gate 之前不启动。

**用户本次待做：** 可看 Layout10 已生成的部分彩色点云预览，反馈视觉是否正常；不可由此升级整屋/SG 通过。

## 6. 证据与不变性

完整私有证据全部留在 data：
`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_f1c_aef1_roles_dcd8_gpt_accept_20261109/evidence/`

机器汇总 `gpt_f1c_roles_independent_acceptance.json` SHA256：
**`a60837027b0e71b93e7308e88c5078e485102707b7fb01d8ebe5ab0138a47168`**。
该机器文件索引了 13 个关键测试/真实四帧/角色审计/目录哈希证据的实际 SHA256。

未外传原服务器 MJCF、资产、原状态、RGB-D、PLY、点云、图片或逐项原始记录。仅发布此文本评审；未修改生产 V3、nav_sg、Gitlink、训练或 cache，未启动 GPU/model/rollout/训练，未创建或合并 PR。
