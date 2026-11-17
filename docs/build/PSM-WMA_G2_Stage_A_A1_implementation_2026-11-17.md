# Issue #54 Stage A：第一批实现与第二批接口

日期：2026-11-17（Asia/Shanghai）。作者代码/CPU 候选；不是 GPT 服务器独立验收报告。

权威：Owner 最新指令、Issue #54 及双 floor-top 变体补充、v2.1 addendum；本会话收到的《接手核对与增量构建交接》全文。Library 702 行原件未取得，不声称完成原件字节比对。旧 v2.0 中检索/embedding 等冲突建议不执行。既有审核及原始证据不改写。

## 基线和范围

- 独立分支 `codex/g2-stage-a-offline-issue54`，基于 #53 HEAD `d36caf0fc35f3a84b739dc8df58ab992eb9f6917`；已审核 VAE 核心 `778d1ed8a031429fd857c980fc872d4c85123cd1`。
- 最新 V3 `fe1089fb925d86697bebd9bef18608d9c9eae87b` 的 docs-only 增量并入本分支，merge `66583e16d75f7704bbafe6c429e97c9a0c9df9c2`；没有更新 V3 ref。
- Child/Gitlink `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`，nav G2 `70eb7b447e65d793b0ebe18b258291ce46f057c1`，不改动。
- 本批实现 A–F 及 A2 的不可变事件/来源封存接口。**没有实现 A2 常驻消费者、共享核心新 source adapter、持久 ACK、队列恢复、最终 VAE 收尾。** 没有新的 VAE 编码器；#53 原五个核心模块和两个 CLI 保持原样。
- 不创建环境/安装依赖，不运行 Wan/权重/GPU/真实数据/全量生产/训练，不修改 G1、Cosmos、nav、state15 或联合索引，不合并 PR。

## 原 producer 的接线

`atomic_6views_run.py --output-profile <JSON> --flat-root <原 flat 根>` 在原生产链中传递冻结配置；旧调用省略该参数，保持旧 compact v1/v2/v3 发布和校验。新配置使用新 work namespace 和独立输出根，禁止写默认旧正式根；已有输出只校验复用，不覆盖。

`episode.py` 仍调用原 F27、材质/透明/背景处理和原 marker compositor。FULL 完成最终 clean 图后派生 marked copy；ARROW_ONLY 引用 clean 与其他方向，仅重新盖章；REUSE_ALL 引用上一次实际 owner。原 1 mm/1° 规则未改。新版原始 receipt 是 `g2_stage_a_raw_episode_v1`，不送入旧 compactor 冒充旧产物。

当 PNG/VAE 均关闭，producer 在 native snapshots 后直接发布所声明的 SG/任务/文本/pose，不执行后续颜色融合或 F27。这个分支仍需要原 native Full Map 几何/SG 前置；不会凭空产生结构。CPU 接线测试使用明确合成的 native fixture，未运行实际 native 栈。

配置候选位于 `tools/g2/profiles/`：clean 选择示例、PNG−/VAE+ 来源示例、SG-only 示例。它们不是生产配置冻结。selection 启用时必须明确 `clean` / `w_rbs` / `both`；没有训练默认值。

## 新协议和完成条件

```text
episode/
  episode_manifest.json             g2_spatial_profile_episode_v1
  spatial_source.json               g2_sealed_spatial_source_v1
  SPATIAL_SOURCE_READY.json          来源封存；profile_complete=false
  task_entities.json                各精确 TaskEntitySet 的内容索引
  language.json                     唯一文本库 + 逐状态 caption/fact 索引
  state_000000_frame_000000/
    scene_graph.json.gz
    spatial_metadata.json
    sixview/[rooms/<uid>/]floor_top.png
    sixview/[rooms/<uid>/]floor_top_w_rbs.png
    sixview/.../plus_X.png           仅存在的方向
    islands/<native-id>/plus_X.png
  _spatial_inputs/...                仅 PNG−/VAE+ 的稳定输入
  COMPLETE.json                     仅全部声明产物合格后
```

原生几何快照、投影与源文件哈希在封存前复核；空间 source ID、profile ID、完整文件清单、当前状态和 owner 一起封存。新 validator 独立验证图像、投影、双向成员、任务映射、因果索引、可复现文本与完成条件。旧 scanner/validator 不接受新 schema，不能伪造旧 COMPLETE 绕行。

| 组合 | 本批行为 |
|---|---|
| PNG+/VAE− | 保存 PNG 与所声明的其他产物；可完成 declared profile |
| PNG+/VAE+ | 保存 PNG，封存来源，VAE pending，**无最终 COMPLETE** |
| PNG−/VAE+ | 仍实际渲染；稳定输入写有上限的 `_spatial_inputs/`，pending，不删除 |
| PNG−/VAE− | 无 RGB 依赖时跳过 F27；只完成所声明结构产物 |

产物状态 `disabled/absent/reference/pending/ready/failed` 分开。只有图像类允许 scene-absent；SG/任务/文本不能用 absent 充数。每方向 catalog 保留 disabled/absent 的原因、成员与 room/Island，不创建空白有效 payload。读取损坏属于拒绝；失败 staging 保留 `FAILED.json`，不会发布 COMPLETE。

`profile_complete` 仅表示声明 profile 完整，`training_ready` 一律 false。VAE=true 的新 profile 在本批只能到 SOURCE_READY；任何伪造 COMPLETE 都被拒绝。CLI 与调度对 pending 返回 **75**，失败为 **2**，完成为 **0**。pending 不计 DONE，也不作为需要反复重渲染的失败重试。

## 空间元数据和双向成员

`render_connections.renderer_member_sets()` 是 renderer 与 metadata 共用的实际成员规划。emit 直接使用同一个集合，来自 native connection/Room/Wall/Island 证据；不做像素对象检测、遮挡筛图或新房间算法。

每个有效完整逻辑 View ID 保留 room/Island、当前成员/物品集合、反向 entity→view 与 object→view，独立 `membership_version`、当前 `geometry_version` 和 image owner。引用图片的投影仍属于其 owner；当前成员来自当前 native snapshot，不能从旧图或 image owner 推断。

投影保留真实 world frame、Room origin/axes、right/up/forward、uv_min、原始 W/H、mpp、米制 W×mpp/H×mpp、另列像素中心跨度 `(W−1)×mpp`、半像素和行翻转公式。无 VAE padding；标记为正交射线，不能从 RGB 二维坐标断言唯一三维点。原始 x/y/z 和实际 chassis +X/源 body/frame 保存，不做 Pose5/yaw/归一化。

owner 另保留实际 scene keyframe 状态、帧、snapshot SHA 和投影 SHA。ARROW_ONLY 的图片 owner 可以是当前状态，但其底图几何仍来自先前 FULL。REUSE_ALL 的 marked owner 可以是上一次 ARROW_ONLY，不能用 FULL 旧箭头哈希顶替。

clean `floor_top` 与 `floor_top_w_rbs` 使用独立 owner/事件身份；多 Room 路径完整保留。marker disabled 是 disabled；一个 Room 外部时 marked 图仍存在且 marker_drawn=false；所有 top 外部仍遵守原拒绝规则。viewer 支持两个变体、多 Room 路径，按 canonical direction 做 1–6 过滤计数；marked 不是第七方向。

## 18 类初始化 GT 角色

规则参考公开 RoboCasa 固定 revision `425684d332f135f5b30a40b321f52d15a0fe9250`。逐文件 SHA256/Git blob、任务类继承链和初始化方法行号在 `PSM-WMA_G2_Stage_A_task_rule_sources_2026-11-17.json`。这不是历史 Episode 生成器版本认证；正式 TaskEntitySet 明示该限制。

| 任务 | 绑定依据与角色 |
|---|---|
| CloseBlenderLid | 唯一官方 Blender fixture，保留全部 parts/SG IDs |
| CloseFridge / OpenCabinet | `fixture_refs.fxtr`；空 refs 仅接受唯一合法 class |
| CloseToasterOvenDoor | `toaster_oven` |
| CoffeeSetupMug | 任务 `obj` + coffee_machine；不取 distr |
| NavigateKitchen | `target_fixture`；排除初始化 `src_fixture`，不输出 target pose |
| OpenDrawer | drawer；drawer_obj/distr_counter 不是操作目标 |
| OpenStandMixerHead | 唯一 StandMixer |
| PickPlaceCounterToCabinet | obj、cab、counter source reference |
| PickPlaceCounterToStove | obj、目标容器 container、stove destination reference |
| PickPlaceDrawerToCounter | obj、drawer source、counter related reference；**不是唯一允许目的地** |
| PickPlaceSinkToCounter | obj、container、sink source |
| PickPlaceToasterToCounter | obj、plate、toaster source |
| SlideDishwasherRack | dishwasher；不据 should_pull 推断当前开闭/成功 |
| TurnOffStove | stove + 原始 knob 语义；不伪造 knob part→SG 的精确绑定 |
| TurnOnElectricKettle | electric_kettle |
| TurnOnMicrowave | microwave；内容 obj 不冒充操作目标 |
| TurnOnSinkFaucet | sink；不取随机干扰物 |

每角色记录原字段/规则依据、exact source instance、全部 part→全部 SG IDs、binding_status。全图映射保留一对多。缺失/歧义输出 UNRESOLVED 和原因，producer 不静默选第一个，也不进入视觉检索；失败保存诊断。

逐状态 selection = 声明变体的全部有效 top + 当前任务实体反向关联的有效 View，并集排序去重。选图有 reasons、membership IDs 和未关联任务 ID；不裁剪离线编码范围，不把不存在方向当 payload。

## 文本候选

原 caption 通过 flat frame.task_index→meta/tasks.parquet 解析，逐帧精确绑定、与 ep_meta.lang 交叉核对；不回退为 task class 或默认句子。PyArrow 只在真实读取入口延迟导入，不增加安装要求。只读相关 Parquet row groups 并核对其文件哈希。

增强文本只用当前已绑定角色、真实 SG 名称/room/Island 和可选的米制 world AABB center/size。原文逐字符保留；不输出调试文件路径、成功变量、专家动作、导航终点、未来状态，也不把 connection 当 inside/on 或开闭证据。

字段、3 位精度、4096 Unicode 字符预算均是候选；默认不追加数字 AABB。预算按完整事实截断，不截断原文；原文超限、遗漏事实都有标记。文本库按实际文本/recipe 唯一存储，状态单独保留当前完整事实 hash、纳入事实 hash 与 caption 来源，所以未显示事实变化不会重复存同一文本。语言 recipe 不属于 VAE recipe。

## 第二批接口及尚未实现项

`FinalPixelEvent` 携带复制的不可变最终 PNG bytes、SHA、完整 view ID、canonical/variant、episode/source/profile scope、final phase。数值 `pixel_record_key` 独立于文本/发布 scope；最终 compact 的 owner/record index 不属于入队身份。`package_stage_a(...event_sink=...)` 是同步可失败 hook，本批未把它冒称常驻并行系统。

`ConsumerLimits` 明确有限 event/spool 合同；本批实际执行的是 PNG−/VAE+ episode spool 上限和失败保留。`max_events` 是消费者接口参数，**尚无运行中的队列实现**。事件只在 final clean/marked pixels 后产生，不从 raw material/背景之前采样。新 source seal 无需旧 COMPLETE，最终 source 中的 state_records 是 compact 后 owner 的权威对照。

下一批仍需实现并验证：少量共享模型消费者/有限队列背压、事件乱序/崩溃恢复和持久 ACK、同目标流式/事后 writer 互斥、新 sealed-source adapter 调用 #53 同一 Encode1/逐 view writer、所有有效 view/variant 覆盖、owner reconciliation、缓存核验后最终发布，以及 durable receipt 后安全清理。现有旧 build/verify 继续只处理旧 completed packages；新 profile 不能通过它们编码。本批不宣称任何 VAE、ACK、恢复或消费吞吐 PASS。

## 本地复验和 GPT 下一门

现有 CPU interpreter `/workspace/.venvs/g2-view-vae-52/bin/python`；不创建环境。完整命令和原始日志/JUnit 在 `docs/collab/codex/evidence/2026-11-17_issue54_a1/`，以最终 gate.json 为计数权威。早期开发失败原样保留，不累计为独立通过项。

```bash
cd /workspace/psm_wma_issue52
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD/cosmos-framework:$PWD"
PY=/workspace/.venvs/g2-view-vae-52/bin/python
OUT=docs/collab/codex/evidence/2026-11-17_issue54_a1
bash "$OUT/commands.sh"

# 全部合成；输出必须是新的独立目录，不代表真实场景验收。
"$PY" -m tools.g2.inspect_stage_a_example --output /tmp/issue54_a1_example_new
"$PY" -m tools.g2.verify_spatial_profile \
  --episode-root /tmp/issue54_a1_example_new/example_episode
```

GPT 按固定实现 SHA 在原有服务器环境独立复验：CloseBlenderLid/000000、CloseFridge/000502、NavigateKitchen/002104、PickPlaceDrawerToCounter/005077。先读原 source/flat mapping 核实身份、磁盘/进程与现有环境，不照搬旧 GPU 编号，不复制私有资产。指定独立 plan/work/staging，使用原 producer `--output-profile tools/g2/profiles/stage_a_candidate_clean.json --flat-root <真实flat>`，保留原 direct-geometry/material/scene-event 参数；不能把所有任务的“第一个 Episode”当作上述固定编号。测试链路和 18 角色、四条真实 caption/绑定/SG事实/增强文本/selection 对照未验收前，不冻结语言或启动全量。

NOT_RUN：真实 PyArrow caption/原始 RoboCasa/native/F27 四样例、真实 Wan/GPU、新协议流式/事后数值一致、性能/磁盘/队列吞吐、全量生产、state15、联合对齐、训练、合并。已接受的 #53 202 记录旧真实样例仅作为既有基础，不覆盖上述新增范围。
