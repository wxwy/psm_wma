# G2-F3 `abcc87ca` + `72b22349` — GPT data 独立复验（2026-11-10）

**正式结论：`APPROVE_LIMITED_REAL_RGBD_COLOR_AB_AND_EMPTY_DIRECTION`；1 Hz 六视图未通过、Layout10 普通地图未通过、实际画质 H1 仍待用户审核。**

固定审核代码（不是后续 Docs HEAD）：
- [nav_sg #9](https://github.com/wxwy/nav_sg/pull/9)：`abcc87ca636c81455f397e8b0813522c70874c00`；
- [PSM-WMA #34](https://github.com/wxwy/psm_wma/pull/34)：`72b223499ae6fd080a337dafe0bb60f9f879c953`。
两份 PR 均为 Draft，没有合并。请不要将本审查解释为合并许可或真实机器人模型语义通过。

## 1. 固定代码和隔离运行环境

GPT 使用 GitHub 完整 Git tree 的**实际 Git blob SHA**与服务器隔离源码逐文件比对：nav_sg **308/308**，PSM **60/60** 一致。作者已发布的服务器 PSM 源包包含一个较晚提交的 CMake 测试辅助文件；GPT 在**新建的只读审查副本**中恢复为固定 GitHub 提交的原 blob，并对60份源码全部重新核验。这没有触碰原作者目录、PSM V3、nav_sg原工作树、Gitlink或产线。

独立复跑：
- PSM Python **553/553 PASS**；原 F2 517 case ID逐个留存，新增36；
- nav_sg 正式 Python **121/121 PASS**（GT47、offline dataset34、offline replay+color AB40）；另外额外运行的 ROS/semantic package 测试28/28 PASS；
- 全新 Catkin/Noetic C++ **173/173 distinct GTest PASS**，Catkin346是统计包装的重复；无失败/错误/跳过；
- 所用 PSM Cu? 无 GPU/模型训练、无真实模型推理。

## 2. GPT 真正重新执行6组×201帧实际RGB-D

在 `data` 创建新审查目录、用固定源码新编译的真正 `mapping_only_node`，从 Layout1 `PickPlaceDrawerToCounter/episode_005077` 与 Layout10 `CloseBlenderLid/episode_000001` 的相同 Left RGB-D、K、Pose重放，完全不使用作者六组生成文件替代执行。分别测试 **5/2/1 cm**，六组均重新处理 **201/201**，合计 **1,206帧**，`skipped=overwritten_pending=rejected_enqueue=0`，无残留待处理。检查点为各场景帧0,20,…,200共**66份**原生颜色快照；所有330份实际快照文件逐字节 SHA256 校验通过。

尤其重要：GPT **66/66份新产生的 `observed_colors.txt` 与作者此前私有原产物的 SHA256逐字节相同**；11个相同时间点导航几何网格与原生 SG摘要在5/2/1 cm间也完全相等。这项事实既经过原产物独立重哈希，也经过**第二次实际执行**，不只是作者日志回放。仍属于 ACK-paced 逐帧回执控制，不是无限速真实相机的丢帧担保。

独立GPT执行指标（绝对时延受本次主机调度影响，不能冒称作者原始数值）：

| 场景 | 色彩体素 | 终点已融合彩色 voxel | 原生节点峰值 RSS MiB | 融合 CPU p50 ms | 普通快照 RPC p50 ms |
|---|---:|---:|---:|---:|---:|
| Layout1 | 5 cm | 4,010 | 194.52 | 11.67 | 88.37 |
| Layout1 | 2 cm | 25,301 | 200.52 | 12.92 | 129.02 |
| Layout1 | 1 cm | 101,252 | 226.01 | 13.50 | 271.28 |
| Layout10 | 5 cm | 2,041 | 202.02 | 13.25 | 拒绝 |
| Layout10 | 2 cm | 12,732 | 208.02 | 13.85 | 拒绝 |
| Layout10 | 1 cm | 57,644 | 218.57 | 14.44 | 拒绝 |

Layout1普通快照的1cm延时为5cm的约**3.1倍**（本次），作者独立时序为约5.1倍。共同结论是**不能称“提精度没有运行代价”**。Layout10的普通快照全部仍报 `native object identity/geometry/mode conflict`，不得以拒绝RPC耗时冒充成功快照延时，更不得用 FullMap GT正常渲染掩盖这一现存故障。

## 3. 独立12组/36张真实 RGB-D 颜色六视图

四帧 (Layout1、Layout10的0/200) × 5/2/1cm共**12组真正重新渲染**，每组3个含可投影物体方向+3个不含物体方向。固定 PSM源码产生的**36张 RGB PNG及其 `geometry_valid/color_valid` 掩码与作者 PNG 像素矩阵逐像素完全相同**；其有效RGB像素的颜色值均能在该帧对应 native RGB-D cloud中找到。**36个空方向没有 PNG**，原方向在 `views.json` 中标为 `SKIPPED_NO_PROJECTABLE_OBJECT` 并保留 Missing-view。未使用 MuJoCo Mesh/UV/Asset Texture去补颜色或遮挡后的背面。

独立渲染时前一次第200帧在 Python3.13/NumPy2.2.5 环境中因严格来源 hash/姿态值不一致正确拒绝。GPT 改用与保存录制证据一致的 **Python3.12 / NumPy2.5.4 / MuJoCo3.3.7**，第200帧全部严格审核通过。**没有修改生产代码、资产、manifest、散列或降低门槛**。不同Pillow版本可能使PNG二进制编码哈希不同，但像素、颜色valid、几何valid完全相同。

独立实际核心 render wall time仍分别约 **Layout1 12秒/帧，Layout10 23秒/帧**，对5→1cm变化不大，**即使低精度也达不到1 Hz**；说明主要阻塞在现有可视化/投影/逐源解析，而非仅彩色体素数量。须按源码 profiling优化，而不是靠再次降低颜色分辨率或仅缩小 PNG。颜色观测有效像素由5cm到1cm显著增多，但**可辨认外观是否过关需要Owner人工 H1，不得以像素数代替人眼**。

其中12组均未出现 native Island，因此本轮**没有真实 Island 质量验收**；Source GT结构与对象来自MuJoCo而颜色全部来自nav_sg RGB-D，也不能称已验证YOLOE/SigLIP对象识别。Floor UNKNOWN 不自动进入 UP，Room/Wall结构根不可充当对象连接传递中继；未观测背面不补色。

## 4. 供Owner检查的服务器内网页

GPT 在服务器原位从**真实左相机RGB**重读 Layout1/10 frame0/200并对照各原始 sourceRGB SHA，生成四张原相机参考图，再与新独立渲染的12组按三档精度编成H1对照。

仅 data 私有回环：`http://127.0.0.1:8793/evidence/gpt_f3_h1_actual_rgbd_comparison_20261110/index.html`。

Owner Windows: `ssh -N -L 8793:127.0.0.1:8793 data`。网页首页、全部36张三视图和4张原始相机图 **41/41 本地HTTP200**。用户必须核对实际物体外观是否可辨、观测孔洞与遮挡、Wall投影选择和Island真实缺失，才能给H1。

## 5. 尚未关闭的Gate及下一动作

**通过（限域）**：固定代码/回归；相同201真实RGBD原生6组×201融合无pending覆盖；66次源码带hash彩云；5→1cm颜色体素/观测像素确有提高；36色PNG和36空方向跳过的因果来源与数学/文件输出。

**阻塞**：正常导航 Layout10 原生snapshot的 identity/geometry/mode冲突；1Hz核心view renderer远未达标；无限速live相机压力未测；用户H1画质未验；真实Island方向投影未验；非GT的对象语义未验；历史全量源认证和训练均未通过。

**推荐下一轮 Codex**：保留现有 ColorCloudMap 的**5cm默认**，把1cm作为可配置选择；优先对本来12/23秒的 `g2.views.render_connections` 做投影/静态几何复用、缓存和CPU profiler分解（区分 source严格复验与实际投影，不跳过来源 Gate）、对原生 Layout10普通快照冲突输出具体ID/来源并最小修复；如果真实H1认为1cm外观仍不清晰，继续分析观测视角/RGB-D密度，而不是采用GT全知纹理美化或增第二份地图。用户 H1 反馈后再决定是否引入更复杂缓存或并行工作队列。

私有审查根（**全部数据仅留服务器**）：
`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_f3_color_ab_gpt_independent_20261110/evidence/`，机器报告 `gpt_f3_independent_review_machine_verdict.json` SHA256：

**`43be7d5e489e41f4e2c8bf2bb89390857c841f920c2250d847b9cf121ebacf5b`**。

本报告只有独立review文本发布GitHub，未复制私有图片/点云/RGBD/资产；未修改作者目录、V3/Gitlink/旧PR、未合并、未训练、未启用GPU/模型。