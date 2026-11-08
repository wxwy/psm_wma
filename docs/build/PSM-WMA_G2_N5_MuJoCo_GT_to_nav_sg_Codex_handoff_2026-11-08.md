# G2-N5：MuJoCo GT 带标签点云 → nav_sg 原生 SDF / Room / SG 验证及 Codex 正式 PR 交接

日期：2026-11-08。结论：**GPT 服务器独立原型通过关键 C++ Gate，但不是正式产品实现；Codex PR 与 GPT 最终 PR 验收尚未执行。**

## 0. 用户确认的分工
**GPT 服务器隔离 POC + 真实原生测试 → Codex 在 GitHub 提交正式独立 Draft PR → GPT 拉取 PR 在同一服务器按固定 Gate 最终验收。** 不在 data 服务器运行 Codex，不修改训练数据、长期运行服务或原始 nav_sg 主目录。原有 RGB-D 感知路径不被 GT 代替或污染。

版本：GitHub `wxwy/nav_sg:G2` 在审计时 HEAD `bcbc46a53bee66b5820b793dd35acbe44c348a5c`；PR #2 是 RoboCasa RGB-D/Pose replay Draft，PR #4 是堆叠语义/关系 Draft。服务器源码干净工作树 HEAD `1a23b16`；隔离 POC 基于 `mapping_8_3/mapping` 复制版本（不要混淆真机启动 `ObjectNav-mapping-only/src/mapping`）。建议新 Codex 分支从 PR #4 head 派生、独立 Draft PR，保持 #2/#4 原样。

## 1. 已生成的隔离 POC（只存在 data 服务器，**尚未提交仓库生产代码**）

Python Oracle 导出目录：`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.nav_sg_g2_gt_labeled_cloud_candidate/`。
包含 `g2/gt/mujoco_scene.py`，以及 `episode_000036_frame0_native`、`episode_000036_frame200_check`、`episode_layout10_frame0_native` 的 `manifest.json`、`gt_labeled_surface.ply`、`gt_occupancy.raw`。
PLY 的每个点有 XYZ、RGB（仅 MuJoCo `geom_rgba` 近似！非真纹理）、整数 `instance_id`、`geom_id`，Oracle Manifest 保存类别、实体 ID、关联 geom/body、bbox、source SHA256。三态 Occupancy raw 为 x-major `uint8`：UNKNOWN=0, FREE=1, OCCUPIED=2。源为真实 MJCF 编译及 `states.npz`，跳过 robot，剔除 9 个 z≈10m 虚拟占位几何；完整点云不能伪装成传感器从假原点 raycast。

C++ 隔离原型：`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.nav_sg_g2_gt_native_integration_candidate/`。
重要文件：`workspace/src/mapping/include/mapping/sdf_map3d.h`、`src/sdf_map3d.cpp`（新 GT 三态导入）、`src/room_pipeline/room_pipeline_room.cpp`（FREE-only 2D BFS 阻断穿墙）、`test/gt_oracle_native_smoke.cpp`（原生 Grid/Room/SceneGraph/标签绑定/隔墙 Smoke）、`run_native_gate.sh`（私有 ROS Master 11375）、`compare_native_footprint_gt.py`、`results/`（日志、footprint CSV、图、指标 JSON）。无 GPU 训练和生产进程改动。

## 2. 已执行 Gate 与原始数据

| 指标 | RoboCasa Layout 1 / EP000036 frame0 | Layout 10 / CloseBlenderLid EP000001 frame0 |
|---|---:|---:|
| Native libmapping + GT smoke 二进制编译 | PASS | PASS |
| 三态体素数量 | 310,800 | 454,656 |
| OCCUPIED / FREE / UNKNOWN | 24,902 / 40,850 / 245,048 | 34,103 / 58,182 / 362,371 |
| SDFMap3D 逐体素读回 Parity | PASS | PASS |
| 原生 RoomPipeline，geometry-only esdf_grid | 1 Room | 2 Rooms |
| Room 图 nodes/edges | ≈140/339–341 | 208/488 |
| RoomBuilder 恢复的 XY footprint cells | 1,569 | 2,060 + 152 |
| MuJoCo 真实 floor cells（10cm） | 1,650 | 2,335 |
| Room footprint Precision / Recall | **1.0000 / 0.9509** | **0.9797 / 0.9281** |
| Room footprint IoU | **0.9509** | **0.9105** |
| GT Object 直接传给原生 SceneGraphManager | 39 个 | 92 个 |
| Object → Room 实际赋值 | 33 个 | 67 个 |
| 原生 C++ occupied wall barrier 2D BFS 回归 | PASS | PASS |

原生实现证明：`SDFMap3D::importOracleGrid` 严格检查三态、尺寸、坐标，再以原生 log-odds 写入，调用 nav_sg 自身 Inflation/ESDF；拒绝二次写入已有地图，绕开 `inputPointCloud(sensor_pos)` raycast 逻辑。Native `SceneGraphManager` 读取 Oracle PLY 的 object/fixture instance，构造带真实 ID 和几何的 Confirmed ObjectClusters，调用既有 `SceneGraphManager::update`；标签／类别仍经 GT Manifest sidecar 绑定，**不假装 SceneGraphObject 已原生支持 category，也不伪造 SigLIP embedding**。

动态初步证据：Layout 1 frame0 vs frame200，49 个 Oracle 实体 ID 保持一致，抽屉与物体位移约 12cm；frame200 的 native Occupancy/Room/SG 可独立通过，**但尚未实现同一进程内的局部增量更新**。

### 非绿色项必须保留
- Layout 10 的物理结构是一个非凸厨房（两块 Floor、五段实体墙），但 geometry-only RoomPipeline 当前得到 2 个 Room；有 45 个 footprint cells 位于 GT Floor 外、168 个 GT Floor cells 未被 native Room 覆盖。不要仅看 Room 数量宣布分割正确。UI 的 ±X/±Y 四槽不应强行创造四堵墙。
- `room_pipeline/source=gvd` 在 Layout 1 上虽得到 1 Room（约 14,904 nodes、150,691 edges），但重复执行后 native GT Object→Room 查询 0/39，`labels_present=0, query_present=0`；相比 `esdf_grid` 33/39 是明确差异，GVD re-entry/label cache 需查因及原生回归，不能报全模式 PASS。
- `FloorSegmenter` 的直方图检测两场景均出现 peaks-too-close，回退 floor=0m、ceil=3m、slice=1.6m。当前 Room 指标使用了这个已知 fallback，不是自动地板检测 PASS。
- `SDFMap3D` 使用浮点 `ceil(map_size/resolution)`，Layout 10 触发维度误差。隔离 C++ smoke 只以 `map_size=dims*resolution-1e-7` 绕过；正式代码需要稳健地绑定整数 grid dimensions，不要保留魔数。
- RoomBuilder 2D recovery 原代码允许 BFS 穿过 `traversable=2`（OCCUPIED-only），隔离原型改成仅允许 FREE=1。正式实现需要补测试，明确若给墙面单元贴 Room 标签，只能作为无传播的邻接赋值；另检查声明的 `max_dist_cells` 未被 BFS 真正使用。
- **Full GT 语义不可夸大**：POC 以 Collision Surface Points 作为 OCCUPIED、以 Floor 范围内的高度层推断 FREE；未精确体素化所有实体内部、抽屉空腔、未知空间，也未使用贴图真实 RGB。因此 POC 仅可作为接口／Room footprint Smoke，不是最终 Full Solid GT，也不是 Cosmos 可用的最终真实 Colored Orthographic View。

## 3. Codex 正式实现任务（建议一个独立 stacked Draft PR）

**A — GT Scene Extractor**：正式化 MJCF+mesh+ep_meta+states 输入；资产路径可配置、文件哈希/坐标/时间可验证；实例 ID+类别+部件/joint 与完整可复现几何版本。保留小物件，排除机器人与辅助占位，区分 collision vs visual 和真实纹理颜色，不以 geom_rgba 冒充相机观测。

**B — GT Occupancy Adapter**：原生 SDFMap3D 专用 Oracle 模式，不 fake-raycast；输入独立三态 voxel map，精确 solid/known-free/unknown，原生 ESDF/GVD 可复用；严格 hash、维度、origin、分辨率、重复导入、场景切换校验；保证真实 RGB-D 路径 off-regression。

**C — GT SG & Relations**：Oracle 实例可直接入 Scene Graph（无需 YOLOE、SigLIP、DBSCAN、伪 embedding）；显式稳定 instance/category/part 及 room_uid，保留真实 Object → Room 直挂；Island 只是派生的 Room 下分组／资产索引。Root Floor/Wall 独立，Wall 有真实有限 3D 几何。首轮不做 Agent 或 Cosmos 训练。

**D — 正式原生测试**：用 catkin_add_gtest/ROS 隔离 Smoke 覆盖三态 parity、错误尺寸与原点、错误来源、重复导入、穿墙反例、Room 2D 标签稳定；Layout 1 + Layout 10 的实际 MJCF footprint IoU，`esdf_grid` + `gvd` 各自逐项返回，至少验证 frame0/frame200 ID 稳定和 sparse update 的重新读出。固定代码版本，不改 PR #2/#4，不用多张隐式样例掩盖失败。

## 4. 后续 GPT 独立验收的门槛

`NATIVE_IMPORT_PARITY=PASS`, `NO_FAKE_RAYCAST=PASS`, `ROOM_BARRIER_NATIVE=PASS`, `ESDF_GRID_ROOM/SG=PASS`, `GVD_REPEAT_ROOM_LOOKUP=PASS`, `GT_ENTITY_CATEGORY_BINDING=PASS`, `LAYOUT1_&_LAYOUT10_FOOTPRINT_EVIDENCE=MEASURED`, `DYNAMIC_CROSS_FRAME_ID=PASS`, `TRUE_SOLID_GT/UNKNOWN=PASS`, `REALISTIC_VISUAL_COLOR_PROVENANCE=PASS`；若后两项尚未完成，只能进入 GT 几何 Smoke 阶段，不能将其作为最终视觉缓存生产输入。

**截至本文件提交：正式 Codex PR 未创建，GPT 最终复验未运行。所有已测服务器原型代码仍在隔离目录，原仓库 nav_sg:G2 没有被此轮修改。**