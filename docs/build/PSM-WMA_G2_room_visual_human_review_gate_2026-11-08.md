# PSM-WMA G2 — MuJoCo 原始场景 × nav_sg Room 分割：人工视觉验收 Gate

日期：2026-11-08；状态：**PENDING_HUMAN**。本 Gate 的裁决权属于用户人眼验收；原生 C++ 测试、Room 数量或 IoU 一律不能自动升级为分割正确。

## 原始产物（data 服务器本地）

**审图入口**：

`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.nav_sg_g2_gt_native_integration_candidate/results/human_review_v1/index.html`

在 data 服务器本机浏览器打开。静态 HTML 不连接服务器服务，支持人工选择「认可 / 不认可 / 需复查」、填写理由，并导出本地 `g2_room_human_verdict.json`。当前没有任何人工 PASS。

每个 Layout 单独保存：
- `original_mujoco_top_rgb.png`：从完整 MuJoCo MJCF **原始材质/纹理**加一个临时正交审图相机生成的真实场景 RGB。
- `original_mujoco_oblique_rgb.png`：同一场景自由相机斜视 RGB，用来判别柜体、墙和独立区域。
- `native_room_segmentation_only.png`：原生 C++ `RoomBuilder` 输出的 Room ID 二维网格；不是模拟划分。
- `original_with_native_room_overlay.png`：**同世界坐标**原场景顶视 RGB + 实际 Room ID + MuJoCo 实体墙黄色线；Room 分割验收的主要依据。
- `original_with_gt_floor_and_walls.png`：GT 地板与实际墙体几何。
- `original_with_errors.png`：在同一 RGB 上标出 Room 和 GT floor 的重叠、漏划（蓝）与多划（红）。
- `human_review_contact_sheet.jpg`：四宫格，前两张原图、原生分割叠图、GT 差异图。
- `mujoco_reference.json`：相机 XY 覆盖范围、每个真实墙段与地板体的中心/姿态/尺寸；`evidence_summary.json`：Room ID、计数、GT 来源和未完成的人工结论。

审图脚本（只位于隔离原型目录，不是正式 PR）：`render_mujoco_review_reference.py`（通过 Xvfb/GLFW **CPU 软件渲染**）、`build_room_visual_review.py`（原生 Room CSV/World XY → RGB 叠图），以及 `compare_native_footprint_gt.py`（指标及 GT floor 区域）。

## 实际原生 C++ 结果

来自隔离 Catkin 构建：`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.nav_sg_g2_gt_native_integration_candidate/workspace`，未改正式 nav_sg 生产代码。

| 样例 | 原生 Room 数 | Room 体素二维 footprint | GT floor overlap IoU | 人工裁决 |
|---|---:|---|---:|---|
| Layout 1: PickPlaceDrawerToCounter EP36，frame 0 | 1 | Room 0 = 1569 个 10cm XY 格 | 0.9509 | **PENDING_HUMAN** |
| Layout 10: CloseBlenderLid EP1，frame 0 | 2 | Room 0 = 2060 格；Room 1 = 152 格（1.52㎡，位于房间上侧狭长区） | 0.9105 | **PENDING_HUMAN** |

Layout 10 的 Room 1 是否应当独立，是关键人工判断。GT 的 Layout 10 有 **两块地板碰撞实体、五个真实墙段**，所以仅有 2 个 Room 不等于正确，也不必机械规定结果必须只有 1 个。用户需根据原场景视觉结构、开放边界和原生 Room 分割位置做裁决。

**测试状态与限制**：
- GT Occupancy 导入后 native 三态逐体素读回 parity PASS；禁止覆盖已导入/运行中地图的 guard PASS。
- 原生 C++ RoomBuilder 隔墙 BFS 回归：隔墙单元不可传播 Room 到另一侧，PASS；但其生产级语义、动态场景仍待正式 Codex PR 独立回归。
- 通过 GT labeled PLY 到内存实体引用的原型 PASS；并非最终完善的生产 SG 结构、逐关节关系系统。
- 当前认可的审图模式是 `source=esdf_grid`、geometry-only TopoCut；`source=gvd` 在某次 repeat 出现 Room 数降为 0 的不稳定现象，未作为人工审图主依据。
- G2 GT Occupancy 当前是**MuJoCo collision surface 点云体素 + Floor polygon 内自由空间的 P0 近似**，并非几何体内部/容器空腔的精确实体体素化。原场景 RGB 真实来自 MJCF 纹理，但 PLY 点云颜色是 `geom_rgba` 近似，不得混淆。
- 图像对齐脚本不会通过任务名、oracle 语义或人工修改来调整 Native Room 分割；仅将原生 Room ID world XY 绘制在相同世界轴的 MuJoCo 审图相机下。
- 静态文件一致性复核：HTML 所引用的 10 张图片均存在；RGB 各自 `880×660`，叠图像素变化非零；每 Layout 实际 Room 数符合 C++ CSV；`human_verdict=PENDING_HUMAN`；没有改正式 `wxwy/nav_sg` 代码仓。

## 人工确认需要判断什么？

1. Layout 1 是否确实只是一间完整 Kitchen？墙线是否沿真实外墙，Room 是否侵入外墙或严重漏掉可用区域？
2. Layout 10 的 Room 1 是否由真实空间/语义界面隔开（比如开放连接、台面造成的假通道瓶颈），还是**误切出一个 1.52㎡ 的假 Room**？
3. Layout 10 非矩形地板、第五墙段与分割图是否一致，尤其是凸包会错误填充的凹陷区域。
4. 矩形房间、非矩形房间是否出现跨实体墙的 Room 连通、墙体被归作自由空间、未知处被强行补完？
5. 如果分割形式有问题，给出图片中的位置/区域与预期 Room 数量，记录为 HUMAN_FAIL / REVIEW；该证据优先于静态 IoU。

## 本 Gate 后续工作

- **未获得用户人工裁决前，不应标记 Room Segmentation PASS，也不应冻结 Room 视图编码/缓存契约。**
- 若 Layout 10 误切分，先按真实图片和原生 TopoCut 参数/几何瓶颈定位原因，修改隔离 C++ 原型后重跑、重生成审图包，不用偏离到重训练一个墙体检测器。
- 人工视觉验收通过后，向 Codex 提交隔离原型的固定源码/测试/Gate 证据，正式开发独立 Draft PR；再由 GPT 用真实数据在独立环境中执行最终验证。
