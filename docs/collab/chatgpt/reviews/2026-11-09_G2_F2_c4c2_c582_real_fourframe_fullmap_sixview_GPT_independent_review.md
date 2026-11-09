# G2 F2 — GPT data 服务器真实 Layout1/10 四帧独立验收

日期：2026-11-09（CST）。被审固定实现：PSM-WMA `c4c2a36431478825b2f1db8b0fa7b74c11ac9b2d`（tree `352226ad1e6bc1133a890e6295290e58fce8e7e1`）及 nav_sg `c5825589cc748145819dfc17cfeb7a026aa08c46`；作者交接 [PSM #26](https://github.com/wxwy/psm_wma/issues/26#issuecomment-6738487245)、[nav_sg #8](https://github.com/wxwy/nav_sg/issues/8#issuecomment-6738486321)。

**结论：`APPROVE_F2_IMPLEMENTATION_COMPONENTS_AND_REAL_GT_FOURFRAME_PREVIEW_ONLY; NORMAL_LAYOUT10_AND_REBINDING_OPEN; H1_PENDING`。** 四帧原始 MuJoCo Full Map GT → native Room/SceneGraph → PSM严格封装→六视图确实跑通，已准备人工 H1；**普通传感器 Layout10 原生快照与正式历史模型 rebinding 仍阻塞**，并未获得历史源/全部材质/YOLOE/SigLIP/整屋/训练验收。此为无 PR 的 docs-only 独立评审分支，不表示已 APPROVE merge。

## 1. 独立固定源码、原生编译、全套测试

GPT 在 data 服务器新建隔离目录，PSM Git 从精准提交重新检出并核验 **55/55 个 G2 文件的 Git blob SHA、SHA256及 tree**。nav_sg 因隔离服务器 Git 凭据限制，使用已哈希核验 e15 基线+GitHub connector 固定 c582 的代码修改重新构造，**152/152 核心.h/.cpp SHA256 与 GitHub 作者固定 inventory 完全一致**，实际 native 运行指纹 `f07b7d5385aaba9fcf5a47cd5aa693a58f93fb3e3f741ac55f8d5ba9c3566da0` 一致；未拿旧二进制冒用新版本。

独立测试：
- PSM `517/517 PASS`；Noetic Python相关 `53/53 PASS`；隔离 MuJoCo Python GT `47/47 PASS`，合计作者所称 100；原生 Catkin **168/168 distinct C++ GTests PASS**，Catkin 输出 `336 tests` 是同一测试两次统计。零失败、错误、跳过。
- 原生 `mapping_only_node`、`gt_oracle_native`、共享库全新编译通过。服务器 ROS1 Noetic/Python3.12 与 MuJoCo/Python3.13 运行分环境，必要 GTest:: 兼容修复**仅限隔离构建目录自动生成文件**；固定 C++ 源码未修改。
- 完整 source inventory 和本人执行的 JUnit、Catkin raw logs 在服务器证据目录；没有外传源图、点云、原状态/资产。

## 2. 真正 RoboCasa 输入重建（双方两帧）

布局映射：Layout1 `PickPlaceDrawerToCounter` local episode_000036 → target-atomic global episode_005077（459帧）；Layout10 `CloseBlenderLid` local episode_000001 → global episode_000001（412帧）。在上一轮 GPT 已验证真实 RGB-D 201/201帧基础上，这轮使用**原始实际模型 MJCF、mesh/texture、ep_meta.json、states.npz**重新导出 0/200帧 GT grid/objects 及 F2 color source-bound 实物点。

关键：旧 native GT `auxiliary_sources.ep_meta` 缺失，本次用同一 MuJoCo **3.3.7** 重新导出、严格绑定原始官方 ep_meta，不能修改旧 manifest 字段。四帧每点 XYZRGB 与旧 F1-D 人眼接受的采样源数据**逐行完全一致**（只是新 native 绑定 identity SHA 自然变化），颜色无效原样保留，`PARTIAL_COLOR`，`training_ready=false`。

Layout1每帧 **1,113,611 点，其中1,025,353颜色有效、88,258颜色未知**；Layout10每帧 **2,149,469 点，其中2,004,657有效、144,812未知**。使用的是 `TEST_ONLY_PILOT_SELECTION_layout1/10` metadata/既有 `known_region_NOT_CERTIFIED.json`，这个预扫 FREE 先验**并没有独立全屋授权**，不能以此推断源模拟器历史生成器完整认证。

## 3. 四帧 Full Map 真正 native 与 PSM 密封成功

四个真正的 source-bound `g2.nav_bridge.full_map.prepare` 均 PASS，随后在新隔离 Noetic 真正执行固定 `g2/gt/native_gate.sh`，每个 frame0/200 均产出 `FULL_MAP_PREVIEW_COMPLETE` 和实际 native `spatial_snapshot/{snapshot.json,grid_states.raw,surfaces.csv,SNAPSHOT_COMPLETE}`，而非只生成 plan。再用新 PSM `g2.nav_bridge.full_map.capture` 对 4 帧重新审核真实各 geom、原始点 XYZRGB、颜色无效位、owner、sources/state 和原生 build fingerprint，均产出严格 `BUNDLE_COMPLETE`。

| 原生输出 | Layout1 frame0 & 200 | Layout10 frame0 & 200 |
|---|---:|---:|
| Native Room | 1 | 1 |
| Room footprint格 | **1,820** | **2,492** |
| 显式 Source GT Object | **39** | **92** |
| 当前 Room 可归属 | **39/39** | **76/92** |
| 未归属 Room | **0** | **16（UNKNOWN，未强制归最近Room）** |
| Source root实体（含几何分块/背板） | 2 Floor + 8 Wall | 4 Floor + 10 Wall |
| Native Object 经对象路径连 Floor | 39 YES | 76 YES，16 UNKNOWN |
| 已认证 Floor NO 物体 | 0 | 0 |
| Native Island | **0** | **0** |

这里的 2/8、4/10 是原生 **GT 根实体分块数量**，不是实际房间只有2块地板却有8面墙：上一轮原 MJCF 审计 Layout1 真正地板1主面/墙体4主段，Layout10地板2主面/墙体5主段，其他源 root 包含 backing、分块。Room 内对象连接中存在实际小于30cm的对象链，因此大量对象可共同归墙。**不能把 Island 0 解释为“实景全局没有孤岛”，需 Owner H1 确认具体物体连通是否合理。**

## 4. 用户最终六视图：四帧各六张，真实PNG共24张，H1 pending

使用 **`g2.views.render` 固定 F2 源码从四个真实 native bundle** 渲染 Layout1、Layout10 的 Frame0、200，每帧均输出6张及 `views.json`，均 `MUJOCO_FULL_MAP_GT_PENDING_HUMAN`、`training_ready=false`，当前4帧没有 Island 四图，因为 native 计算 Island=0：
- **BEV**：Floor-connected objects向地板正交投影；
- **UP**：仅在 native 明确 `floor_state=NO` 时投到从原实体 Wall 顶确定的Z≈3.0m 天花板**参考平面**；**不要求连 Ceiling、也不以机器人/相机高度做分层切片**。四帧UP几何有效像素=0（没有明确Floor NO；Layout10 16 UNKNOWN不可偷换成NO）。没有物理 Ceiling mesh，不能称已感知天花板。
- **+X/-X/+Y/-Y**：每方向只投真实 Source Wall root 经对象链可达对象，非真实实体Wall方向不由 Room边界造墙；Island如存在额外四方向独立输出，不混入四墙。
- 来源颜色仍有失效像素。为便于 Owner 审核，GPT只在服务器生成 **24张人工诊断叠图**：真实 `color_valid` 时显示源 RGB，`geometry_valid` 但颜色未知时灰色，无几何时近白色；未改任何正式 rgb.png/原 native cloud。
- 已在 data 本机启动限 `127.0.0.1:8792` HTTP预览、验证首页与24张叠图 HTTP 200。Owner 使用 `ssh -N -L 8792:127.0.0.1:8792 data` 打开
  `http://127.0.0.1:8792/real_f2_fourframe_sixview_H1_local_review_20261109/index.html`，核对原 MuJoCo真实源图 vs 每帧BEV/UP/四墙、对象归属、是否出现应当为Island的中央桌柜、是否因30cm链过度归墙。**人眼 H1 未请求确认、尚未通过**。不能上传任何私有图到 GitHub。

## 5. GPT 独立核对真实连接路径：不靠图像目测作代码结论

按四帧 `snapshot['connections']` 的逐源 `paths,nodes,distances_m`，自己重算每一跳两个真实 3D bbox 的最小欧氏间隔，均 **严格小于0.30m** 且与数值证据精确匹配；路径除终点 Floor/Wall 外 **全部是源对象节点**，没有 Wall/Floor/Ceiling/Room/机器人当中继；`roots_are_endpoints_only=true`，rejected structural relays 标注完整，SOURCE GT 与 normal 不混淆。

| 源场景/帧 | 经真实路径验证的root连通关系 | 对象链及到根的间距跳数 |
|---|---:|---:|
| Layout1 frame0 | 234 | 415 |
| Layout1 frame200 | 234 | 415 |
| Layout10 frame0 | 760 | 2345 |
| Layout10 frame200 | 760 | 2349 |

16个 Layout10 的 Room UNKNOWN 对象保留 `upper_member=false`、`floor_member=false`，没有冒称“确定不连地板”而投向 Ceiling；部分为 cabinet/drawer/counter/microwave/accessory，位置集中某片未被当前源Room划分覆盖的区域。当前 native `relation_status=NATIVE_HIERARCHY_ONLY_OBJECT_RELATIONS_NOT_OBSERVABLE`，真实语义 `on/inside/contains` 尚无 YOLOE/SigLIP 观测证明。

## 6. 尚未通过，必须分开跟进的两个实际 Blocker

**A. 正式原始模型 rebinding 来源证明：两场景都失败。** 独立运行 `g2.sim.model_rebinding.create`，源官方 `model.xml.gz` 的 mesh/texture 绝对路径是录制时 `/root/robocasa/...` 等，当前服务器无权读取；`model_rebinding.py:83` 在检测 `p.is_file()` 时抛真实 `PermissionError`，无法生成完整原历史路径→现资产闭包proof。**没有放宽 SHA/伪造 historic asset hash**。Codex下轮应明确对不可读取的历史旧路径保守 `BLOCKED`（并给出可审计缺失列表）或加入受控真实资产原始字节证明方案；切勿仅凭当前路径替代就自封历史版本认证。当前 FullMap source GT bundle不依赖此可选 rebinding proof。

**B. 普通 real RGB-D path 的 Layout10 native snapshot export 仍拒绝。** GPT 基于全新 `c5825589` binary 真正重放 Layout1/10 各前201帧，均 201/201真实 RGB-D ACK。Layout1 frame0 native输出2个局部 Floor patches /10个 Wall patches，frame200输出5/10，`PARTIAL_OBSERVED_AXIS_ALIGNED_PATCHES`；不伪称全屋。Layout10 frame0、frame200 snapshot API **拒绝 `native object identity/geometry/mode conflict`**，对应 `mapping_8_3/mapping/src/map_input/spatial_snapshot.cpp` ~lines293–295 的 ID冲突/GT mode/bbox综合防护，尚未定位是哪一个子条件，**不能标原生普通Layout10通过**；须由 Codex 加精确诊断并源修复，保持oracle与普通感知隔离、Room/Walls未观察不造假。

**其他 Gate：** 原用户已经人眼接受的是此前 Layout1/10的部分点云，不是本轮源 FullMap 六图。现有 `known_region_NOT_CERTIFIED`、未证历史 generator、未知颜色、16 unassigned、无真实同帧YOLOE/SigLIP+关系，均保持 `full_scene_source_certified=false`、`training_ready=false`。不运行 PSS/Cosmos 或合并。

## 7. 交付、负责人、后续顺序

**GPT 已执行**：固定源码证据、517/168/100 独立 CPU、四帧真 GT原生、严密4个bundle、24张真实六视图、4个connection源逐跳审计、2026-11-09 server-local H1 gallery。所有私有证据留 data：
`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_f2_c4c2_c582_gpt_real_accept_20261109/evidence/`
机器证据汇总 `gpt_f2_independent_fullmap_fourframe_verdict.json` SHA256：
**`59d3f19f183691ce7e4e961a3f0e8a2a386a9949ef5138e0cfcca95f22492b80`**。

**Owner 下一步**：在本地浏览器看真实四帧六图，对照原MuJoCo，明确 Room/墙面、GT Object、Island=0、Layout10 16 UNKNOWN是否合理。完成 H1后才能冻结空间图口径。

**Codex 下一轮**：保留源两仓，修复 Layout10 ordinary snapshot mode/ID 具体原因、historical rebinding路径权限/严格证明可用性或明确BLOCKED，针对Owner H1发现的空间归属问题最小改；不得重新开发 RoomSegmenter、不能为了六图好看篡改 Floor/Wall/颜色/模型观测。新固定SHA交 GPT独立复验；DS、V3、Gitlink、训练和原生产缓存继续不动。

本报告仅代码审核与实际 H1 候选，未创建PR、未合并，未经人眼不能用 FullMap 结果训练。