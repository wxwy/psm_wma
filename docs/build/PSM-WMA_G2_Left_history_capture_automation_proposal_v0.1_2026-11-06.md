# G2 Full-GT：Left 历史照片自动采集与维护方案 v0.1

日期：2026-11-06。状态：**PROPOSED，供讨论，不是代码/渲染/训练执行授权**。

继承 [G2 详细设计 v0.2](./PSM-WMA_G2_detailed_design_v0.2_2026-11-06.md)：只有独立、通常固定、相对较大的实体进入 SG 并拥有历史视觉索引；小物件只维护关系/必要状态，不建专属图库；所有图像必须来自原 robot0_agentview_left、合法整机配置、可达区域，记录拍摄机器人位姿并自然保留机械臂。

当前只考虑 Full Map + MuJoCo GT Update。四种初始化×两种更新的其他情况不在本稿实现范围。这里是 PSS 数据生产与维护的确定性程序，不是新训练的选图模型、Agent 或机器人任务策略。

## 1. 两个任务、同一个 Capture/Memory 索引

- 初始化：给定 S0 与大实体目录，自动生成机器人观察配置、验证可达性、拍摄并选择少量互补代表照片。
- Episode 内：按时间顺序处理原 Left 图像和 GT 变化，只增补缺失视角/状态、替换更好代表或刷新已经观察到的变化区域。
- 两者共用质量指标、共享 Capture、多实体引用、状态分桶与选择事件日志。初始参考图明确为 simulated prior；任务真实历史帧不提前可用。

## 2. 大实体目录：一次定义策略，批量自动实例化

用现有 RoboCasa metadata/fixture 类别、MJCF body/geom 所属和局部几何生成目录，不用 YOLOE 再决定 Full-GT 的节点身份。

可维护小型版本化 anchor policy：Counter、Fridge、Microwave、Stove、Cabinet 等是否入图，抽屉/门/层板是独立节点还是所属 anchor 的部件。规则按空间功能和独立性确定，不按统一体积阈值。小杯、瓶、碗、盘、打蛋器等只进入关系实体目录。

每个大实体生成：anchor_id、类别、世界/局部变换、边界、geom owner 映射、部件/关节、可观察区域（front、work_surface、drawer_opening 等）与状态类别。未知类别和模糊归属输出 NEEDS_SCHEMA_REVIEW，不自动把每个 geom/Accessory 作为一个大节点。人工工作是第一次确定类别/部件规则及少量异常，不是逐 Episode 画框选图。

几何实例 owner 需要唯一映射，机器人/辅助 marker 排除为环境节点，小物件仍保留物理遮挡/碰撞，不能从场景中删除。

## 3. 机器人观察配置的自动生成

### 3.1 复用已有候选位姿入口

公开 RoboCasa 当前源码 robocasa/utils/env_utils.py 已提供 compute_robot_base_placement_pose(env, ref_fixture, ref_object=None, offset=None)：根据设施及相邻支撑设施计算底盘放置位置。它适合作为候选种子，而不是完整安全/可达性证明。

按每个大实体生成少量中心/左右偏移、近/远距离、底盘 yaw 修正的候选；原 Left 相机随机器人运动学生成，不独立改相机位置、俯角或高度。第一轮可尝试 3 个横向位置×2 个距离作为可配置起点，不能视为已标定最优值。高柜/微波炉不允许为覆盖而额外设置机器人不具备的俯仰自由度。

全局合并相近的机器人配置：同一观察点可能同时拍到台面、炉具和微波炉。不要以每个大实体为单位重复完成相同拍照。

本次只查到公开上游接口，尚未核验 data 固定 vendor 版本。实施应复用固定版本中存在的对应逻辑或最小适配，不为了此方案升级仿真依赖。上游函数包含任务/设施相关分支，不能当作任务无关的完整可达性算法；遍历全部允许大实体，不用未来目标 ID 或示教未来状态挑选视角。

### 3.2 三层验证：粗筛、配置、路径

1. 从 S0 几何形成导航粗栅格，按机器人观察/移动姿态的高度占据与足迹做保守膨胀，取与合法起点连通的候选。不能把吊柜投影误当落地障碍，也不能忽略会撞到机械臂的突出物。
2. 在独立模拟副本中设置整台机器人配置，执行正向计算，检查关节限位、机器人-环境/自碰撞、相机挂载与支撑合法性。地面预期支撑接触与环境穿透分开处理。
3. 用现有导航规划入口优先；缺失时用小型 x/y/yaw 离散搜索作为离线采集工具。检查连接边/旋转扫掠与整机包络；只检查两个终点不构成可达性证明。底盘运动学约束以实际机器人模型为准，不假设任意平移。离散检查的分辨率与保守余量明确记录，不宣称连续碰撞的数学保证。

MuJoCo mj_forward 在不进行时间积分的情况下更新正向计算，可用于配置检查。其 contact 列表受 contype/conaffinity、排除规则等影响，故不能用 ncon==0 直接证明整机几何无碰撞；应审核碰撞覆盖并对必要几何做补充检查。mj_geomDistance 能提供 geom 间距离，但旧版本对部分大 distmax 查询存在精度限制，应以固定版本和小样本验证。

### 3.3 连续采集与批量加速

同一组候选可以输出可达巡视路线，通过既有底盘接口走位并记录真实 Left。第一条验收样本优先这样做，检查路径、机械臂和相机画面。

规模化时可对已经验证可达的观察配置，在独立 S0 副本中离散放置整台机器人后渲染，保留路径/可达性证据；这是 simulated prior，不伪称实际走过连续轨迹。禁止只移动相机、隐藏机器人或改变原图相机参数。

连续运动如碰动非机器人实体，不能把结果当静态 S0 巡视；应明确失败/恢复副本并重试，不能偷偷写回主场景。设置 qpos+forward 不会自动证明物理稳定、控制可达或门开状态合理。

## 4. 照片质量是可计算记录，不依赖 VLM 主观打分

每次候选在同一模拟状态由原 Left 渲染 RGB、Depth、geom/instance ID，合并为大实体和机器人 mask。robosuite 有这些输出接口，需与现有坐标系、Depth 单位、相机 K/T 契约一致。

先按低分辨率/稀疏检查淘汰明显不合格候选，最后以正式输出分辨率重检并保存。一次图片评价所有实际可见大实体，不只评价原目标。

建议最小指标：

| 字段 | 计算方式 | 用途 |
|---|---|---|
| visible_pixels / bbox / border_truncation | GT 实例像素和画面边界 | 判断过小、严重截断 |
| view_bin / distance | Left 与 anchor 相对位姿 | 判断新视角或近重复，不依赖机械臂图像变化 |
| state_bin | 大实体关节/部件状态分桶 | 保留有区别的开/关/中间状态，不为每一角度建图库 |
| relevant_region_visible | 工作面/开口等几何区域与 depth/seg 对应 | 判断照片能否证明需要刷新的内容区域 |
| robot_occlusion | 原相机视锥下实体/区域采样点与深度、robot ID 的遮挡判断 | 判断机械臂是否挡住目标，而非是否出现在整张图中 |
| quality_score / reason_codes | 上述指标的确定性组合 | 同槽替换与诊断 |

机器人 mask 与可见 anchor mask 在同一像素本来互斥，**不能通过二者交集估计遮挡**。可用目标/区域的几何表面样本投影并检查前方 depth/ID：目标表面在视野内且前方首先是 robot 才计为机器人遮挡；先区分目标自遮挡、其他环境遮挡。首版也可只采用可见像素/关键区域可见性，不强求完整表面积比例。

GT mask 让实体绑定可自动化，不意味着 RGB 一定清晰可辨；透明/反光/细杆等要记录质量标记。不要用图像面积占比冒充可见表面积。

先采用硬门槛 + 简单排序，不引入学习式评分：相机/姿态合法、目标像素够、截断可接受、关键区域可见，然后按有效覆盖/遮挡与质量选代表；面积评分饱和，避免把极近距离局部特写永远当最佳。

每张图输出 REJECT_UNREACHABLE、REJECT_COLLISION、REJECT_TOO_SMALL、REJECT_TRUNCATED、REJECT_REGION_OCCLUDED、KEEP_NEW_VIEW、REPLACE_BETTER 等可解释原因。门槛保存在 versioned recipe，通过单 Episode 图像审核标定，不声称当前阈值已适用所有资产。

## 5. 初始化多角度与共享：有界覆盖选择

为每个大实体定义可实现的槽 (anchor_id, own_state_bin, reachable_view_bin, distance_band)。仅从合法候选产生的槽中选择，不要求环物体 360°、不要求隐藏背面可见。

每个 Capture 覆盖多个槽。最小选择可用确定性贪心：每次选择补齐最多“当前没有合格图”的大实体/槽的照片，同分选质量较高、冗余较少者；达到预算或没有新覆盖后停止。优先让更多实体至少有一张可用图，再考虑第二/第三个互补视角，避免一个大台面凭面积占满预算。

可表达为 G(c)=sum_{u in slots}[max(Q_existing(u), Q(c,u))-Q_existing(u)]，先对“尚无任何图的大实体”设优先级。Q 只由当前配置可计算指标决定。无复杂整数优化、无新模型。第一版甚至可先每槽选一张，再按共享 capture_id 去重；只有确实冗余太多才加全局贪心。

实例：C1 同时清晰覆盖台面和微波炉，C2 只比 C1 略好但只覆盖台面，C3 覆盖此前没有的柜体。覆盖优先应先考虑 C1+C3；不是每个实体独立选最佳后再存重复图。

图库共享底层 RGB/blob。每个实体独立维护引用和质量；一个实体换图不能删除另一个实体或早期训练样本仍引用的 Capture。

## 6. 增量维护：两个小索引 + 一个事件日志

建议最小内存结构：

```text
representative[(anchor_id, own_state_bin, view_bin)] -> capture_id, quality
latest_context[(anchor_id, region_id)] -> capture_id, content_version_seen
pending_refresh[(anchor_id, region_id)] -> earliest_dirty_time, affected_extent
selection_events -> time, old_ref, new_ref, reason
```

结构参考照片不因为小物件位置变化全部重拍。关系/物件状态更新仅影响所属大实体的区域上下文。

### 6.1 内容变化不能只看关系拓扑

盘子从台面左边移到右边，on(plate,counter) 未变化，但该区域内容已变。Full-GT 的变化输入因此必须同时包含：

- 小物件相关关系变化；
- 同一父区域内的局部位姿变化超过容差；
- 大实体关节/自身位姿变化。

小物件不新增图库；只把受影响台面区域标 dirty。旧、新所属区域都需要更新；在同一台面移动也应记录受影响空间范围。与上次记录状态比较，防止每帧小位移累计漏记。

### 6.2 每帧便宜判断，事件后有限候选检查

- GT 状态增量按原训练时序维护。
- 没有新视角、没有待补状态、没有 dirty 区域时，只保留必要时间索引，不落新图。
- 存在 pending_refresh 时，即使底盘没动，也要持续按受控频率检查后续 Left：机械臂移开可能使目标区域重新可见。
- 物品持续运动时合并 dirty 事件，可用仅过去窗口的低速度/稳定条件减少频繁刷新。地图仍逐帧维护；图库不必同步每个运动帧。
- 只在已可见的受影响区域满足质量门槛时更新 latest_context，并清掉对应 dirty；看到台面右边不能清掉左边未观测变化。
- 结构参考替换要求同槽新图较旧图改善超过 hysteresis；不同内容版本的 latest_context 只需合格且更近，不强求胜过旧内容版本的画质。否则一张更清楚但内容错误的旧图会永远阻止刷新。
- 不让机械臂摆动本身产生新 view_bin；RGB 保留机械臂，筛选不把纯自运动当环境增益。

伪代码（接口草图，非已实现程序）：

```python
for t, gt_state, left_frame, robot_config in causal_stream:
    changes = scene_state.update(gt_state)
    pending.mark(affected_anchor_regions(changes))

    if not should_check(robot_config, pending, missing_slots):
        continue

    evidence = evaluate_original_left(left_frame, gt_state, robot_config)
    for anchor in evidence.visible_anchors:
        update_representatives_if_new_or_better(anchor, evidence, t)
        refresh_only_observed_dirty_regions(anchor, evidence, pending, t)

    commit_reference_events(t)   # 不修改旧照片，不回填未来图
```

第一次保存原图前，先确认至少一个大实体引用该图；若多个实体接纳，Capture 只写一次。新版本有效时间为此刻或实际可用时刻，非回溯到物体开始变化的时刻。

## 7. 状态参考图的自动化边界

用大实体类型的关节/区域配方（例如 closed/open）枚举必要参考状态，不遍历所有关节组合。照片仍归大实体，不为了内部每只杯/瓶补近景。

在独立副本构造历史状态时必须验证关节限位、内容物/容器相对位置、非机器人碰撞与合法 Left 可见性。不能仅改抽屉 qpos 就声称内部物品会自动随动，也不能凭历史时序动作标签创建参考状态。

未知资产或状态不可物理自洽就输出 UNSUPPORTED_REFERENCE_STATE / NO_VALID_LEFT_VIEW，保留 Full-GT 关系记录，不造柜内相机。可先支持当前 S0，以及经过验收的少量 fixture 关节配方，再扩展；Full Map 并不要求每个隐藏表面都有照片。

## 8. 最小实施范围与验收（尚未执行）

沿现有 tools/g2 场景恢复/数据绑定入口新增小适配，不改 Cosmos Action Policy、不重写 nav_sg、不升级生产仿真依赖。职责建议：

1. anchor/config catalogue + robot-pose candidate adapter；
2. original Left render/visibility evaluator；
3. shared causal keyframe bank + event log。

第一轮仅一个 Episode，先自动生成 S0 参考库并保留全部候选决策摘要，再只读顺序处理原 Episode 的 Left/GT 状态演示替换记录。不运行新模型训练、不用 YOLOE、不给小物件建图库。

验收不能只有“图片生成了”：输出合法机器人位置/路径、每张 Left+实例/区域覆盖、每个大实体选中图、未覆盖/拒绝原因、一图多实体引用、GT 改变与 dirty/刷新时间对应、图库容量与变化曲线。人工检查一次规则后，批处理无需逐帧人工打分。

因果性测试：给流水线 Episode 前 N 帧，结果应等于全 Episode 运行时 t<=N 的已保存历史索引；截断未来不能改变早期选图。静止相机纯手臂运动不能让图库无限增长；盘子同台面移动必须产生 dirty；遮挡持续时不能清除 dirty；其他实体仍引用的图不能因局部替换而删除。

自动化应理解为“已定义资产/机器人范围内自动运行，并把未知案例明确分流”，不是任意资产绝对全自动、无缺件、100% 全视角。

## 9. 核查资料与未验证范围

- RoboCasa 上游 env_utils.py（本次读取的 blob d5d3daaa075cdc0d1fbf99b6d397db1a289720d3）：https://github.com/robocasa/robocasa/blob/main/robocasa/utils/env_utils.py
- MuJoCo 3.2.3 camera：https://mujoco.readthedocs.io/en/3.2.3/XMLreference.html#body-camera
- MuJoCo 正向计算/几何距离：https://mujoco.readthedocs.io/en/3.2.3/APIreference/APIfunctions.html
- MuJoCo 碰撞过滤：https://mujoco.readthedocs.io/en/stable/computation/
- robosuite 渲染/分割：https://robosuite.ai/docs/modules/renderers.html

本轮核验为文档/公开源码读取。没有连接 data 执行配置采样、碰撞/路径检查、RGB 渲染或帧选择，以上全为待实现的程序设计。公开上游函数存在不代表固定 vendor 版本或完整自动采集流程已经验证。
