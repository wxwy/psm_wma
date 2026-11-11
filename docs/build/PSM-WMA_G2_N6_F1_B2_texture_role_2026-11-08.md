# G2-N6-F1-B2：源角色证据与 primitive 材质候选

依据：[GPT F1-B 限定 APPROVE](https://github.com/wxwy/psm_wma/blob/gpt/review-g2-n6-f1b-02912226-20261108/docs/collab/chatgpt/reviews/2026-11-08_G2_N6_F1B_02912226_GPT_independent_review.md)，review commit `48f33dd36a0f79e98a9437d0c4e3eb145c1b1692` / file blob `5ab23b76b25eced9f19f3a8feb609d20e5daa700`；[Issue26 F1-B2 指令](https://github.com/wxwy/psm_wma/issues/26#issuecomment-6722340254)。

独立分支 `codex/g2-n6-f1b2-texture-role` 从 F1-B ledger `6bbd1e43ec1cab988af1c6aebf43cb60d8322b13` / runtime `029122268ea535d8b3c74c0b3fb2b0d0302a828f` 派生。新固定实现 SHA 见 canonical `CODEX_INBOX.md` 本批条目；后续 ledger 只改交接记录。所有新证据仅来自自建本地 CPU 夹具。没有读取、下载或传出 data 原始文件。

## 纹理规则与剩余边界

- 对 box/cylinder/sphere/ellipsoid 实现 MuJoCo **3.3.7** 的 object-linear 2D 投影和 cube 投影。使用实际 geom 局部坐标，先采样颜色再变换至世界系，旋转/运动不会把纹理锚定到世界坐标。
- 2D 使用 `s=.5*repeat_x*object_x-.5`、`t=-.5*repeat_y*object_y-.5`，`texuniform` 为真时按空间尺寸处理。它是 MuJoCo 的平面投影，不是自行设计的 box 每面展开。按编译像素顺序做 repeat/bilinear 基层纹理采样。
- Cube 遵循 GL 的 `+X,-X,+Y,-Y,+Z,-Z` 面方向、compiled 六面堆叠或同图重复、clamp-to-edge/bilinear；按 pinned renderer 忽略 2D texrepeat。多个 cube 面同为主方向且颜色不同的点保留无效 mask；不会任意挑一张图当真值。
- Pinned renderer 只绑定 **RGB 材质槽**。RGBA layer 不是其覆盖项；RGB 槽中的四通道图则必须应用 alpha。新 primitive 只用已验证 RGB 绑定；RGBA-only、独立 opacity、不支持变换/维度/版本保持未知。原 RGB mesh UV 数学保持；RGB 四通道 alpha 补为安全检查，未验证的 RGBA mesh layer 保守标无效。
- **显式 2D sRGB 暂不支持**，因为 GL 会解码后过滤，当前源输出按基层 asset bytes 定义。默认/linear 的已验证路径不冒充 sRGB 支持。Cube 的 pinned 上传使用 GL_RGB，按其实际规则处理。这里输出 asset albedo，不是带光照、遮挡或 mipmap LOD 的相机 RGB。
- Capsule 的复合 object transform、部分 mesh UV/opacity 等仍明确未支持。任何部分颜色需要显式 `--allow-partial-color`，不得把无效点中的值当真实颜色使用。

上游参考为 `google-deepmind/mujoco` tag `3.3.7`：`src/render/render_gl3.c`（blob `133e5d6a617606a51fca5a377be37716fdf5923b`，settexture/renderGeom），`render_context.c`（`4a47f1dfe26b5f627d653dc3add7fb32800c3bce`，uploadTexture），`engine_vis_visualize.c`（`c107b9ba32ff9e7121abdab7b40061bae53e2f1c`，mjv_initGeom）。这些是公开源码，未读取私有服务器模型。

## 角色表有证据，角色正确性仍需独验

`asset_inventory` 继续 `AUDIT_ONLY`、无点云/COMPLETE/自动分类。新增 `role_evidence` 将下列事实绑定到已有显式断言：

- 原始 source closure 的 XML 文件哈希、节点路径/属性/default 表引用、完整 include 链和原始 body 祖先。包括 `.xml`、`.inc`、`.mjcf` 及包含在具名 body 中的片段。XML 角色由实际 loader 记录，不按文件扩展名猜测。
- 编译 geom/body、原始数值类型 ID、局部位姿、尺寸、材质、group/contype/conaffinity 和 mesh 原始完整几何哈希的稳定签名。world pose 不进入角色签名，因此 frame0/200 身份不因运动变化。
- 未给角色仍 `UNCLASSIFIED`。原始 node 名称只用于对照原位置，不据 group/name/碰撞 bit 作语义判断；无来源、多个候选或缺失上下文保持缺口。
- `roles_template.json` 给出对应签名/node ID，未知 `role/source_kind/role_evidence.asserted_role` 仍为空。必须由审查人员依据真实来源填角色和理由；官方 ep_meta 绑定和类别/body 原合同不变。
- `--require-role-evidence` 严格核对角色断言、签名、原始节点和理由；robot 排除及官方 ep_meta 绑定还需实际原始 body 祖先证据。机器人名称本身不构成证明。证据的 `role_certified=false` 表示这是**有据的角色断言**，不是自动认证；既有独立 full-source role/material review 仍是唯一整屋来源 Gate。

当完整角色尚未确认，显式 `--allow-unclassified` 可导出已确认视觉部分，但所有未知/错误断言仍在完整 geom 表中，状态为 `PARTIAL_SOURCE`、无 COMPLETE、`training_ready=false`。不能为导出把未知表面改成 auxiliary，也不能借此隐藏已知 visual 的近退化失败。角色齐全且颜色可用的旧 `COMPLETE` 仍只指 `DECLARED_VISUAL_GEOMS_ONLY`；未经独立整屋审核，候选整体仍按未认证的部分来源处理，不授予 Full-GT 或训练资格。

冻结 `surface_sampling.py` SHA256 `763f945ae6f282abd7f69dbe7dbef9cb20d1990fa2a9f34159f6b63ae95cd967` 未改。非零近退化 paper-towel 不会静默删面或降阈值；真实机器人 mesh 只有在有据的角色排除后才不进入预扫描。已确认 visual 近退化仍中止并保留失败证据。真实 paper-towel 原资产未在此访问，source-specific triage 留给服务器。

## 逐点证据及封存

- `precolored.txt` 保持 native V1 七列/原始颜色有效位接口。`color_audit.npz` 按相同点顺序记录 `geom_id`、输入局部 `local_face_id`、`reason_code`、`input_triangle_area_weight_m2`。Mesh face ID 是原编译三角索引；primitive 则是确定性生成的采样输入三角索引，不能冒充源 OBJ 编号。
- 每个实际采样 visual 的 `color_coverage` 保留全部 sampled point 有效数/无效原因、保留面评估数/比例和面积加权样本估计。复用精确叉积消去保护以保持面积证据一致，不改变几何筛选。曲面使用三角近似面积；`continuous_surface_color_coverage_certified=false`，点/面积估计都不是连续颜色覆盖或整屋完整度。
- `source_scope` 汇总逐点有效数，部分 geom 中有效点不会全部被计成无效，也不会因为一次 probe 有效而全部计成有效。
- Hash 绑定的 `source_identity.color_evidence_protocol` 要求新的逐点附件存在。新 manifest 删除附件及 coverage 字段无法在相同 visual/source SHA 下伪装成旧协议。验证 hash/尺寸/有界数组、行数、原 cloud mask、geom/face/reason/面积及 coverage 自洽。
- 既有 reviewed bundle 条件封存第四份 source evidence `source_evidence/color_audit.npz` 并在复读时重新验证；真正旧 producer 无该 marker 时仍兼容原三份证据/七个 bundle 文件。`g2/nav_bridge/snapshot.py` 本批只扩展证据闭包，没有新增 native 结构、对象感知或视图算法。

## 作者 CPU 验证

Python3.12.14 / MuJoCo3.3.7 / NumPy2.3.5，复用现有环境，无依赖新增、GPU、checkpoint、模型或 rollout。

```bash
python -m pytest -q g2/tests --junitxml="$NEW_JUNIT"
# 259/259，0失败/错误/跳过，原207 testcase ID全部保留。
# 同一冻结13项新primitive测试在原029上13 FAIL -> 新13 PASS。
MUJOCO_GL=egl PYOPENGL_PLATFORM=egl LIBGL_ALWAYS_SOFTWARE=1 \
GALLIUM_DRIVER=llvmpipe MESA_LOADER_DRIVER_OVERRIDE=llvmpipe \
python docs/evidence/g2_n6_f1_b2_2026-11-08/software_projection_check.py --output "$NEW_OWN_REFERENCE_DIR"
```

强制 llvmpipe，54个自建盒体方向/material组合、864点，实际 MuJoCo 软件图像与新采样最大相差1个 RGB 字节；显式 sRGB 源128实测输出55，新路径仍明确无效。包含 RGB/RGBA 双槽、uniform/repeat 和六方向坐标对照。测试图仅用于验证，不进入对象感知或伪装真实观测。

自建旧有效6种几何的0/200各6244点与029数据行逐字节一致，状态/边界/原几何哈希相同。原207测试ID均保留；两项原负控将已支持的 textured box 换为仍未支持的 capsule，封存测试新增附件数改8；旧协议另有7文件兼容测试。代码复核发现的槽位/alpha、消去面积、include/body、plane 签名、附件封存/防降格和 sRGB 边界均已闭环。作者代码复核/自建证据不是 GPT 真实服务器验收。

## 服务器执行与 STOP

只在新的**固定 SHA 隔离副本**中执行，不改服务器正式代码仓；复用已在服务器的 Layout1/10 原始 source closure、ep_meta、状态及既有环境，全部私有输入、图片、点云、审计留在服务器。

```bash
# 先看完整原始证据表，不提供角色也能做全geom AUDIT_ONLY。
python -m g2.sim.asset_inventory --mjcf "$SOURCE_XML" --scene-id "$SCENE_ID" \
  --asset-root "$SOURCE_ASSETS" --output "$NEW_INVENTORY_DIR"
# 有既有角色/严格state_source时可按四帧复审；不得将模板空项改成假auxiliary。
python -m g2.sim.asset_inventory --mjcf "$SOURCE_XML" --metadata "$ROLE_MAP" --ep-meta "$EP_META" \
  --states "$STATES" --state-format mujoco_fullphysics --frame 200 \
  --asset-root "$SOURCE_ASSETS" --output "$NEW_FRAME_AUDIT_DIR"
# 审明角色、body、官方类别和来源后，保存已绑定证据的角色map。
python -m g2.sim.prescan --mjcf "$SOURCE_XML" --metadata "$BOUND_ROLE_MAP" --ep-meta "$EP_META" \
  --states "$STATES" --state-format mujoco_fullphysics --frame 200 --spacing "$SPACING" \
  --require-role-evidence --allow-unclassified --allow-partial-color \
  --asset-root "$SOURCE_ASSETS" --output "$NEW_CANDIDATE_DIR"
```

每个 frame 使用新目录，实际 qpos archive 则按原格式调用。先核验全部1020/2115 geom 的来源/角色/排除依据、纹理投影/mask与真实源画面、paper-towel 非零面及 robot 来源；统计真实完整颜色覆盖缺口，再用实际 native ColorCloudMap 复验四帧。原来通过的 accessory/obj/distr 数值及128零面的策略必须保持。标为 partial 的项不能因为有图或点数增加就改 PASS。

本批没有在 data 上跑四帧或 native ColorCloudMap，也没有获得整屋角色/材质 PASS。其后才是 nav_sg #8 普通 Floor/Wall/Room/Island、真实 YOLOE/SigLIP、native 快照与六图/Island 人工检查；source labels 仍只是 provenance。V3、native `2009fae35d86579bb22c273fb97ec1bf0835b533`、Gitlink `1ca308055fc41fb69efaeb9efaa23808f164a18e` 和原 PR/训练/缓存不改。无 GPU、PSS/Cosmos 或训练任务。

**发布本批固定 SHA、作者测试/源码证据及 Issue26 交接后 STOP，等待 GPT 独立服务器新 SHA 复验，不合并。**
