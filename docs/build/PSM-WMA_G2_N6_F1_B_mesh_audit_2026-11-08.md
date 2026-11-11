# G2-N6-F1-B：零面积面与完整资产预审

依据：[GPT F1-A2 限定范围 APPROVE](https://github.com/wxwy/psm_wma/blob/gpt/review-g2-n6-f1a2-e7308332-20261108/docs/collab/chatgpt/reviews/2026-11-08_G2_N6_F1A2_e7308332_GPT_independent_review.md)，review 文件 blob `a47215ef342a09fda01fc228965024486a0c1670`；[Issue26 F1-B 指令](https://github.com/wxwy/psm_wma/issues/26#issuecomment-6720997620)。

独立分支 `codex/g2-n6-f1b-mesh-audit` 基于 F1-A2 handoff `28926f6c64db37e9cc71e9cdf24e4f6ad42a4674` / runtime `e73083324055af459d2c6c65bb52bda142bb4833`。固定实现 SHA 以 canonical `CODEX_INBOX.md` 本批交接条目为准，后续 ledger 提交只更新文档。F1-A2 的四个身份/Pointer 函数源码逐字节不变。本批不改 native、Room 参数/过滤算法或 Gitlink。

## 采样规则

- 仅跳过输入坐标精确有理数叉积为零的三角面。float32 转 float64 不丢精度；疑似零面用 `Fraction` 精确验证。浮点叉积为零、面积很小或某个比例低，均不足以证明应丢弃。
- 保留原 dtype 的 `cross_norm > 1e-14` 正面积保护；对数值误差候选额外精确比较叉积平方范数。真非零极小面、非有限计算和全零网格拒绝。零面不消耗点数预算。
- 正常面的三角形顺序、分段数、重心坐标和矩阵乘法保持原算法。UV/材质规则不放宽，包括已丢弃面存在缺失 UV 时仍拒绝完整颜色导出。
- `face_id_basis=INPUT_LOCAL_TRIANGLE_INDEX`：面 ID 是**输入 MuJoCo 编译 mesh 的局部三角表索引**，不是未经验证的原始 OBJ face 编号。跳过后绝不重新编号。UV 仍查原 `mesh_facetexcoord[face_ids]`。
- 原始全量顶点/面参与 `local_geometry_sha256`，不会因跳过零面而重写资产。`sampling` 同时写入每个采样 visual 记录和 geom 审计，记录原面数、保留面数、丢弃原 ID/个数/比例、丢弃面积及面积比例、近退化拒绝 ID、输入精度、点数、spacing 和局部剩余预算。所有被丢弃面面积精确为 0；保留面积为数值近似，曲面 primitive 的该统计指其三角近似。
- 预算失败还记录触发原 face ID、此前分配点数、当前所需累计点数。导出器在新目录写 `sampling_failure.json`，绑定完整资产闭包、元数据/ep_meta 哈希、恢复状态及全局预算/此前 geom 点数，只保存到失败 geom 的审计前缀，不冒充完整 inventory；不写点云、manifest 或 COMPLETE。重试必须用新输出目录。

采样代码纳入 `adapter_source_sha256`。新源码导出的 visual/source identity 因代码哈希变化是预期行为，不能用旧 review 给新 manifest 盖章。原 asset closure、state/archive/row、native binding 校验与 `COMPLETE=DECLARED_VISUAL_GEOMS_ONLY`、`training_ready=false` 保持原合同。

## 全 geom 几何/材质预审入口

`python -m g2.sim.asset_inventory` 不采整屋点云、不写 COMPLETE，不生成 native 对象或结构标签。其 `inventory.json` 是 `AUDIT_ONLY`：

- 遍历全部编译 geom，包括 visual/collision/robot/auxiliary、透明体和未知项；保留 body 祖先、实际状态/位姿、geom 类型/尺寸、group/contype/conaffinity、材质名/RGBA、纹理角色/大小/编译像素哈希和原资产闭包。
- 可不提供角色 metadata（首次只做默认 frame 0），也可给不完整角色 map。未知角色保持 `UNCLASSIFIED`；错误官方身份、类别、body 或格式记为 INVALID，继续检查其他 geom。未知多余 geom 声明、场景冲突、错误 state closure/archive 仍拒绝整个来源。只读取显式声明，不按名字/碰撞 bit/group 自动判断角色。
- 所有支持的 finite surface 均执行完整三角几何预审，包括非 visual mesh。plane/hfield 等不支持项、近退化 mesh、全部零面均明确记录，不能被其后的好 geom 掩盖。
- 每个可用 geom 仅在**一个保留面的重心**探测材质接口。`PROBE_VALID` 只说明这一次探测可用，`surface_color_coverage_measured=false`，没有全表面颜色有效率。纹理投影、透明度及全 mesh UV 的已有保守检查仍生效。真实颜色有效率必须来自后续全表面实际导出。
- `roles_template.json` 对未知项写 `role/source_kind/classification_reason=null`，未填写时 exporter 会拒绝。已有合法声明保留；审查人员应依据服务器实际 ep_meta/body/视觉/碰撞来源逐项补齐理由。模板和 probe 都不是独立来源审核。

最初无需 metadata 的服务器本地命令（占位变量由执行者在服务器定义，不把原始路径/文件传出）：

```bash
python -m g2.sim.asset_inventory \
  --mjcf "$SOURCE_XML" --scene-id "$SCENE_ID" \
  --asset-root "$SOURCE_ASSETS" --output "$NEW_AUDIT_DIR"
```

带真实帧的严格来源/材质预审，复用 F1-A2 已有 states、ep_meta 和 metadata 的 `state_source`（完整模型闭包与 archive SHA）：

```bash
python -m g2.sim.asset_inventory \
  --mjcf "$SOURCE_XML" --metadata "$ROLE_MAP" --ep-meta "$EP_META" \
  --states "$STATES" --state-format mujoco_fullphysics --frame 200 \
  --asset-root "$SOURCE_ASSETS" --output "$NEW_FRAME_AUDIT_DIR"
python -m g2.sim.prescan \
  --mjcf "$SOURCE_XML" --metadata "$ROLE_MAP" --ep-meta "$EP_META" \
  --states "$STATES" --state-format mujoco_fullphysics --frame 200 \
  --spacing "$SPACING" --asset-root "$SOURCE_ASSETS" --output "$NEW_CLOUD_DIR"
```

实际 archive 若为 qpos 必须显式用相应格式。为四帧分别使用新目录；沿用既有模型环境及已验证状态，不重建整套 RoboCasa，不改服务器正式代码仓，所有资产、状态、图像、点云、审计文件留在服务器。

## 本地作者验证

本地 CPU、Python 3.12.14 / MuJoCo 3.3.7 / NumPy 2.3.5，无依赖新增。所有 MJCF、OBJ、纹理和 states 都是本地自建夹具，无机器人 rollout、图像模型或 GPU。

```bash
# 同一份冻结的24项采样测试：旧 e730 sampler 11 FAIL /13 PASS → 新24 PASS。
python -m pytest -q g2/tests/test_surface_sampling.py
# 完整 G2：207 PASS，0 failure/error/skip，保留原160项全部 testcase ID。
python -m pytest -q g2/tests
# 提供完整旧e730 g2包的独立目录；只生成自建正面积源并在两个源码根运行。
python docs/evidence/g2_n6_f1_b_2026-11-08/compare_own_positive_surfaces.py \
  --baseline-root "$OLD_E730_ROOT" --candidate-root "$NEW_SOURCE_ROOT" \
  --output "$NEW_PARITY_DIR"
```

另一个独立代码复核反例揭示 float32 消去误差：精确非零叉积约 `1.12e-44` 却有 rounded legacy norm 约 `7.63e-6`。候选版对此错误放行的 RED 已原样保留，精确平方范数修正后拒绝且不丢弃。预算失败证据也补全重放配置。相反，精确共线但 rounded cross 非零的面会被正确证明为零并跳过。

自建 MuJoCo 编译 mesh 的14个面中零面原 ID为1/13，UV红绿像素不串位；FULLPHYSICS frame0/200 +12cm 位移、来源和颜色身份保持；坏状态/角色/来源拒绝，unsupported 后的 geom 仍完整列出。原有效6种几何（mesh/box/sphere/ellipsoid/capsule/cylinder）的两帧各6244点，旧新版全部 XYZ/RGB/valid 数据行逐字节一致（源码身份 header 预期变化），原几何哈希/状态/边界也一致。

原始 RED/GREEN/JUnit、复核发现与闭环、源文件哈希和 own-fixture parity 记录见 `docs/evidence/g2_n6_f1_b_2026-11-08/`。作者与另一 Agent 的代码复核不是 GPT 真实服务器验收，未重跑/宣称 C++ native 验收。

## GPT 服务器新 SHA 验收 / STOP

请在固定新 SHA 的隔离源码副本中先复跑 G2 全套，再在**服务器原位**复用原 Layout1/10 source closure 与 frame0/200：

1. 复验实际 `obj_g0` 4048面零丢弃；`distr_g0` 7920面中的128个面须精确证明为零，保留7792面、丢弃总面积0，核验原 compiled face IDs、UV、原始全几何哈希。数值近零但非零的实际面应拒绝并报告，不能为通过而改变阈值或改面。
2. 默认/显式 info.cat、obj/distr 实际 body 祖先、动态身份、四帧原始 state/archive/row 与 asset closure 均须保持。此前墙面附件+obj 子集与相同参数旧有效面逐点比较，预期代码来源身份会变化；新增 distr 不能替代其他未覆盖视觉体。
3. 对两布局全部1020/2115个 geom 作角色和视觉资产/材质来源逐项审计，拒绝任意以 auxiliary 标记掩盖可见体的声明。分类须由真实来源证据审核，不能把 name/group/contype 自动推断当结论。检查 collision/robot/auxiliary、全状态变化、几何和贴图缺口。
4. 对已审明 visual 做实际完整表面采样，报告各 geom/点的真实颜色有效率及缺失原因。probe 有效、局部 COMPLETE 和声明角色齐全均不等于整屋通过。仍不支持的投影或 geometry 要单列为 F1-B 后续缺口。
5. 未获独立完整来源审核前不得设置 full_scene_source_certified/training_ready。全部服务器原始文件/审计/图片/点云留在服务器，由 GPT 提供限定结论，不外传报告文件。

本批源代码、固定 SHA、作者证据和 Issue26 交接发布后 **STOP 等待 GPT 独验**。F1-B 真实整屋 Gate、nav_sg 普通结构 #8、真实对象感知、六图/Island 人工、PSS/Cosmos/训练均保持 OPEN/未启动。本批不合并 V3、现有 PR 或 Gitlink，不创建生产任务。
