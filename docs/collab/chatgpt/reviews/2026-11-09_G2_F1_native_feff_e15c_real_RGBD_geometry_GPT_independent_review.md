# G2 F1 Native — GPT 独立真实服务器验收与下一轮编码阻塞报告

2026-11-09（CST）｜独立审核来源：data 服务器真实 RoboCasa Layout1/10 和新 Noetic 隔离源码。

**最终结论：`COMPONENT_GATES_PASS_BUT_REAL_STRUCTURES_AND_SEMANTIC_OBJECTS_BLOCKED`。**

固定审核源码（不得用后来 Inbox/作者摘要代替）：
- PSM-WMA native bridge：`feff0d54b04a4c669198ec48493736bbc5dcaa81`，Git tree `91312da9c3971fa70491685a2061f5223a687fa3`。
- nav_sg native structures：`e15c4cc28a157526a53827f29aeb70f88c845a66`，Git tree `f9ea268257b2309931d449b827f86b08f0ab86c1`。
- 正式双场景 role release：`54541c315ad13077b5b4b7f3d81d01138b8931d8`，冻结角色分类依据 F1-D `6b04d214`。

## 1. 固定代码与测试独立复现

- PSM-WMA 全部 G2 **45/45 个 Git blob**、固定 tree 核验成功；本次服务器独立 `pytest` **446/446 PASS**，旧371 case ID 保留，新增75，零失败/跳过。
- nav_sg 因 data 服务器 GitHub 凭据不可用，GPT 以已固定基线**隔离复制**加 GitHub Connector 原位读取固定 `e15c4cc2` 中变化文件重构。**175/175 个实际源码/测试/构建文件的 SHA256 全匹配**冻结 GitHub `source_inventory.json`，原生真正 152 个 .h/.cpp 的运行来源指纹 **`a977dcd33eeb77a44acb2f9c6818583ab9a2b9d243b79b88b6e7c4398fb07c`** 全匹配。独立构建的 `mapping_only_node`、`libmapping.so`、`gt_oracle_native` 均成功。
- Noetic 独立 Catkin native **157/157 个不同 C++ gtest PASS**；Catkin 汇总314是同一157 case 重计数，零失败/错误/跳过；相关 Python **53/53 PASS**。完整主程序通过两组正式 opt-in 测试：`closed/esdf_grid` 输出 1 Room/1 Floor/4 Walls，`doorway/gvd` 输出1 Room/2 Floors/5 Walls，均重放4帧且 frame0/3真实 ROS 原生快照产生；这些自建场景**不等于 RoboCasa 真实验收**。
- 服务端环境 Noetic 不在 `/opt/ros/noetic`、CMake/GTest存在旧兼容问题。仅修复隔离 Catkin **生成的测试 make/link 文件**，未改 frozen nav_sg 源文件。原 PSM 30 个错误起因是稀疏 checkout 漏取固定 generator catalog，补齐后446 PASS；原 Python 5 个失败因缺隔离源码 Git HEAD metadata，已补本地**标注为合成、非 GitHub 正式 commit** 的 HEAD，53 PASS。这里不归咎候选生产代码。

## 2. 两套真正服务器场景配置复验

- 以固定 `feff0d54` 代码，重验作者 Layout1 / Layout10 role release，且在新的 GPT 独立目录重新 `scene_release package` + `verify`，均 PASS。前者161项、后者429项；角色 map SHA `e57070c4...` / `d7d4d23d...` 与先前 GPT F1-D 批准完全一致。
- GT Source 的颜色仍是 `PARTIAL_COLOR`，无效颜色点 Layout1 **88,258**、Layout10 **144,812**；`training_ready=false`、`full_scene_source_certified=false`，不因封存或预扫描自动提升全场景认证。
- 已对 `recorded.prepare` 逐项验收严格拒绝误称 `world` 的旧 `map` 预扫描；然后使用原始 MuJoCo exporter **重新以 `world` 真实坐标版本生成**两套 frame0 输入，原已批准每一行 XYZRGBvalid、原模型几何/状态/色审核完全一致，不是改字符串绕过。已审角色配置封存、原 RGBD和上次人工点云均未变。

## 3. 真正 nav_sg mapping_only_node × 真正 RoboCasa RGB-D 重放

查到官方 RoboCasa 原始状态与 RGBD 的真实全局 Episode：

- **Layout1**：`PickPlaceDrawerToCounter` local036 → target-atomic global**episode_005077**，完整459帧；GPT 本轮真实视频/Depth/K/pose **201/201** 校验，实际 ROS `mapping_only_node` **201/201** frame ACK、frame0和200 snapshot 导出。
- **Layout10**：`CloseBlenderLid` local001 → global**episode_000001**，完整412帧；同样真实RGBD验证201/201，原生ROS replay 201/201、frame0/200导出。
- 源 C++ 指纹准确、`world` 坐标及原 geometry SHA/状态/颜色证据存在。**但实际主程序仍然 Floor/Wall/Object=0**；每场景都产生1个原生 Room：

| 实测真实结果（frame0/200均同） | Layout1 | Layout10 |
|---|---:|---:|
| Native Room footprint（格） | 1,806 | 2,480 |
| Native Floor patch | **0** | **0** |
| Native Wall patch | **0** | **0** |
| Native Object | **0** | **0** |
| 原生结构状态 | `NO_OBSERVED_STRUCTURAL_SUPPORT` | 同左 |
| `affiliations_complete` | false | false |

实际底图来自已绑定原始 MJCF/mesh 的 `PRESCAN_PREBUILT` GT geometry 加真实 RGBD 更新；快照 `source_mode=perception` 是代码使用的路径名，**不能把 GT 预扫描自动误称 Cold Start 从相机直接感知全部地图**。缺少同帧真实 YOLOE/SigLIP sidecar，`object_frontend_status=BLOCKED_CURRENT_FRAME_RGBD_OBSERVATIONS`，`completed_rgbd_observations=0`。PSM `snapshot.capture` 对四帧实际 **4/4 正确拒绝 `BLOCKED_REAL_RGBD_OBSERVATIONS`**，无 bundle、无伪造对象标签。

## 4. Floor/Wall 真正原因及已知可靠 Full Map 证据

在固定 `e15c4cc2` `mapping_8_3/mapping/src/map_input/native_structures.cpp` lines234–249，算法要求任何一间 Room 的所有自由内部列，从地图最底直到观测地板高度都连续 `occupied`；任一列不满足便拒绝整间 Room 的 Floor，随后 Wall 因不存在 `floor_z` 也无法生成。RoboCasa Floor 是有限厚度几何，**其下方 UNKNOWN，绝不可擅自转成 occupied**。

独立逐帧占据诊断：
- Layout1 室内 known-free 1622列；**0列**从底部到Floor连续occupied；frame0/200有4/17个仅局部表面 Top occupied+Above free。
- Layout10 2308列，同样**0列**连续；frame0/200仅2/3个局部顶面证据。
- 原生传感器高度 probe `verified=true`，但这**不能用于六视图上下空间分割**，也不能凭一处探针宣布整屋墙地板已感知。
- 另读取**真实原始 MuJoCo MJCF + 编译geom world 8角点**，排除 backing、collision proxy：Layout1 **1块真正地板、4段真实墙**；Layout10 **2块真正地板、5段真实墙**。原生 native Room 的**全部1622/2308个 known-free 内部格**分别落在对应真实地板几何区域内，说明 **Full Map GT 真实地板源确实存在**，但普通传感器地板置信证据不足以宣称全域观测。
- Native Room perimeter：Layout1 170格均距真实 Wall ≤0.15m，Layout10 **205格中有63格距任何实体 Wall >0.30m**（开放式边界/缺口），强烈支持**Room footprint 不等于真 Wall**，禁止造四面闭合墙。两场景均无单独 Ceiling mesh；源墙最高 Z≈**3.0m**，可将其作为**注明来源的平行天花板参考面**，不表示检测到物理 Ceiling。
- 既有旧 GT native pilot Layout1 footprint1820/ Layout10 2492 与本轮1806/2480 不完全相同，来源不同，勿夸大 exact parity。

## 5. 正式 recorded source identity 的另一阻塞

原真实 episode 的 `model.xml.gz` SHA Layout1 `b13a3696...`、Layout10 `02584e28...`；地图来自经过 mesh path rebasing 的 `scene_rebased.xml` SHA分别 `bfa37c64...` / `0ff7d261...`。即使 gzip 解压原始 XML 后 SHA 也不等于 rebased SHA（路径变换的预期结果），而当前 `g2.nav_bridge.recorded.prepare` 将原 gzip SHA 和 rebased root SHA 直接比较，**必然拒绝严格正式记录**。原 `states.npz`、`ep_meta.json` 哈希均准确匹配。后续需实现可复算 gzip解压→受控path rebase→root和asset闭包SHA的严格来源绑定，不得删除比较或改文件头冒充通过。

## 6. 用户最终六视图与连接（Codex 正式约束）

1. 俯视（BEV）：Floor-connected物体向地板正交投影。
2. **仰视（UP）：全部 Non-Floor-connected 物体向天花板平行参考面正交上投影；不做 Ceiling connection 判断、不用 Camera-Z/机器人附近地面高度做切片、不要求 Ceiling mesh 存在。**
3. +X/-X/+Y/-Y 四墙侧图：**与对应真实 Wall** 直接或经物体-物体传递连接的对象；开放墙方向不造假Wall，Room边界不是Wall。
4. 连通阈值为物体真实3D bbox最小欧氏距离严格 `<0.30m`（可配置），不按单轴投影距离。Floor/Wall/Ceiling/Room/机器人是边界/根，不可作为联通传递的超节点；否者墙→地板会把吊柜错误归 Floor。
5. Floor连接、但不连接任何真实墙的中央桌/柜等，组成 Room→Island，**每个 Island 单独生成四个正交侧视**，不混入房间四墙。吊柜可同时在仰视和所属墙侧图；UNKNOWN仍明确保留。
6. 全部可视化应从真实 `nav_sg` Scene Graph/当前帧结构和原始已审核材质输入产生。不得让静态 Source oracle 标注冒充 Cold Start 物体语义。六图/Island真实 H1 尚未完成。

## 7. 执行分工与边界

**Codex 下一项（已正式发布）**：
- [nav_sg #8 GPT 实施单](https://github.com/wxwy/nav_sg/issues/8#issuecomment-6736440426)；[量化来源补充](https://github.com/wxwy/nav_sg/issues/8#issuecomment-6736688140)。
- [PSM-WMA #26 跨仓接收单](https://github.com/wxwy/psm_wma/issues/26#issuecomment-6736467892)。
- 两仓分别从上述固定 SHA 创建独立候选，最小修复局部真实薄地板证据；支持**明确标记的 Full Map MuJoCo GT** 初始化（不同于 normal perception）；按用户终版6图/Island连接语义实现并标出来源；修正 strict recorded 原 gzip/rebased闭包身份，补 tests 负控。发布固定提交和真实两场景0/200调试报告，**不合并、不训练、不改V3/Gitlink**。
- 任务已经 GitHub 发布；本次 ChatGPT 工具**不能自动启动另一个 Codex 编码会话**，因此“已交接”不等于“Codex 已开工”。不制造虚假运行状态。

**GPT 本轮自己完成**：源码/CPU/原生真实201帧×2/四帧快照、源/地面/墙/开放边界与身份核验；用 CPU MuJoCo renderer 从原始模型和状态生成 Layout1/10 frame0/200 **真实原始场景俯视图（4张）**，并与 native Room、真实源Floor/Wall 叠图（4张）组成**诊断预览**。后者只是后续 H1 对照证据，不等于正式6图完成。全部图只在 data 本地 `127.0.0.1:8791/index.html`，需要 SSH loopback 转发。图片、点云、逐geom/source、RGBD 未外传。

**最终 Gate：** 代码及隔离封存与真实RGBD原生重放**限域 PASS**；真实 Wall/Floor/对象及空间关系 **BLOCKED**；六视图/Island **NOT_RUN**；Owner H1 **PENDING**；PSS/Cosmos **NOT_RUN**；`training_ready=false`，不允许升级完整来源或模型语义认证。

### 私有完整证据

全部仅存服务器：
`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_f1_native_feff_e15c_gpt_accept_20261109/evidence/`

机器汇总 `gpt_e15_feff_real_native_independent_gate.json` 的 SHA256：
**`f7da397befa1ca5b802decd172fe9be13f4010cdd2a2d4c2f652c4f072e04543`**。

机器文件记录了本轮重要日志、JUnit、真实 state/Room、Floor/Wall来源几何、ROS快照、拒绝负控、可重放预览的 hash 索引。未向外部发送私有原数据/图/点云，未修改 V3、原始nav_sg/Gitlink、训练/模型/生产缓存、未建PR、未合并。