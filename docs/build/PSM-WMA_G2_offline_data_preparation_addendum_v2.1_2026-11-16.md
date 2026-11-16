# PSM-WMA G2 离线数据准备 v2.1：Owner 新决定、接管核查与分阶段执行合同

日期：2026-11-16。状态：**最新离线构建要求生效；新增 Stage A 生产实现尚未交付；语言模板与生产参数未冻结。**

本文件依据 Owner 在本会话指定并完整阅读的 `PSM-WMA_G2_Offline_Data_Preparation_Handoff_2026-11-16.md`（Library 702 行提取文本）整理，是仓库内的版本化执行补充，不声称与 Library 原文件字节一致。原 `PSM-WMA_G2_detailed_design_v2.0_2026-11-16.md` 保留不覆盖；冲突条款以下述最新决定为准。用户同意已讨论部分，不等于未展开的全部细节均已冻结。

## 1. 当前授权与严格顺序

1. **阶段 A：全局信息离线构建。** 完善既有生产链，输出 views、SG、投影/成员元数据、任务实体、增强语言与逐 view VAE cache。
2. **阶段 B：state15 单独处理。** 阶段 A 完成后，核实真实底盘 frame，构造 Pose5＋EEF10，独立确定归一化。
3. **阶段 C：全部离线数据对齐。** 最后联合 raw decision frame、action window、G1 latent、state15、空间状态、SG、所选 view、对应几何及文本。

代码/CPU、服务器真实小样例、候选文件生成在本次推进范围内。**不启动模型训练，不自动合并 PR，不覆盖或删除旧数据，不修改既有 G0/G1/Local 训练链、checkpoint 或 Cosmos Gitlink。** 全量执行以样例定稿及资源核算为前置，不能将授权推进解释为跳过这些条件。

GPT 负责设计、独立审核与授权服务器验证；Codex 负责生产代码、静态/CPU 测试和固定 SHA 候选。服务器不 commit/push。发布 Issue 或指令不等于 Codex 进程已启动；状态必须以实际回执为准。

## 2. 本轮核实的真实起点，防止重复开发

| 对象 | 2026-11-16 本轮实查结果 |
|---|---|
| GitHub V3 | `55cc5181abf8ca4b1e2a3a6b415699c457cc080b`，本补充提交前 |
| 服务器正式 root | `875ad79189a4aaa903849b6a5a4cea0eaf62e523`；已 fetch，远端仅多归档 v2.0 的文档提交；未 checkout/pull/reset |
| Cosmos Gitlink / 服务器 Child | `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`，一致 |
| nav_sg G2 远端 / 本地 | `70eb7b447e65d793b0ebe18b258291ce46f057c1`，GitHub connector 查询远端并与本地比对一致 |
| nav_sg 服务器 fetch | 认证失败，VSCode credential socket 不可达；不冒称 fetch 成功，也不修改凭据。远端身份由 GitHub connector 单独核实 |
| Issue #52 | 逐 view VAE 核心既有任务，不新建重复核心 |
| Draft PR #53 | open、Draft、未合并；固定实现 `778d1ed8a031429fd857c980fc872d4c85123cd1` |
| PR #53 核查时 HEAD | `d36caf0fc35f3a84b739dc8df58ab992eb9f6917`，审核/证据 HEAD，不替换固定实现身份 |
| PR #53 CPU 独立结论 | APPROVE_CODE，283/283；F1/F2/namespace 回归已关闭 |
| 真实 VAE | 原有 psm_wma 环境，2 episodes / 10 per-view 文件 / 202 记录构建与同环境严格重编码 PASS，max_abs=0 |

老 Draft PR #51/#41/#34 以及 nav_sg #10/#9 的页面状态不能反推正式分支缺少相应能力；现行 G2 生产已经包含部分文件级集成和后续 P3 实现。以当前树和固定源码为准，不盲目重开、重做或合并历史 Draft。

### 2.1 继续使用原有运行环境

```text
/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin/python
Python 3.13.11 / Torch 2.10.0+cu128 / CUDA 12.8
```

**不创建新环境，不安装新的依赖，不使用上轮临时依赖 overlay。** 环境和源码分离：用该解释器运行已提交、固定的 root/Child 隔离 checkout。不要因 `psm_wma` 与 `psm_wma_v3` 名称接近而选错解释器；后者现场 cu130 环境并非当前可用 CUDA 路线。

原有环境样例 recipe：`3ee9c48399143866b2a0061f3cee01bff35842228f639380d60602d6402e2fc1`。早先 Torch 2.7/cu126 的两份缓存 recipe 为 `fc0fb8c551f9abeca5541cac03b5d42a26e6fa9029aba5cb896760aaed1dd4dc`；它们是历史样例，不能与新环境产物混用或静默覆盖。上轮一个输入跨环境 max_abs=0.03125，只能说明不满足跨 runtime 位等；不能凭此认定算法错误，也不能假定所有输入相同误差。

参考：PR #53 原有环境回执 `https://github.com/wxwy/psm_wma/pull/53#issuecomment-6919489156`；固定 CODE/CPU 报告 `docs/collab/chatgpt/reviews/2026-11-16_Issue52_778d1ed8_d5c1ffc7_ViewVAE_R2_APPROVE_CODE.md`。

## 3. 替代 v2.0 中冲突建议的决定

| 主题 | 当前要求 |
|---|---|
| 仿真对象筛选 | **Full Map + GT task grounding**：初始化元数据/任务角色→source fixture/object/part→SG entity IDs |
| 不再做的前置工作 | 当前不做物品 embedding、SigLIP/YOLOE 召回、对象专用渲染、像素对象 mask；真机感知检索以后返回同一种 TaskEntitySet |
| 全局构建 | 升级原 producer 正式导出元数据并重新生产，不另造长期残缺产物修补系统 |
| 离线编码覆盖 | 所有有效 view、所有 Island、全部实际图片版本；不依赖任务选图裁剪 |
| latent 存储 | episode 内每个逻辑 view 一个文件，内部全部 owner 记录与状态引用；不改成整集大文件或每 PNG 一个文件 |
| 模型读取 | 必选俯视图＋当前任务实体关联图并集，过滤不存在方向，完整路径去重；选图不删除整图中的其他物体 |
| VAE 入口 | 生产并行与事后补编码共用核心，不能维护两个不同编码器/索引系统 |
| state15/联合对齐 | 分别属于 B/C，不能塞进 A 或提前修改训练 Dataset |

GT 绑定是明确实验条件，不冒充机器人已具备开放目标识别。允许初始化目标身份，不输入未来轨迹、成功标志、专家终点、仿真计算的导航目标 pose 或奖励状态。

## 4. 数据位置与旧资产保护

```text
原始 flat:
/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic

既有 depth:
/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic-depth

最终正式全局根（升级后仍保持该位置）:
/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic-6views

固定计划:
/mnt/data1/data_v2_0617/robocasa365_v3_flat/.g2_atomic_9126_plan_20261113

旧 G1 left+wrist cache（不重建、不改格式）:
/mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-left_wrist-exact_window
```

新全局 profile 写到明确 staging/new-version 根，旧目录继续可用。全profile验收后才安排发布切换；旧数据删除须 Owner 明确授权。原始局部 episode、模型、states 和 ep_meta 路径取自已有计划/flat mapping，不按全局编号猜。

## 5. 生产链数据流与代码落点

```text
原始 source / ep_meta / states / flat caption
       ↓ 既有 producer + native Room/Island/SG + F27
       ├─ 投影/成员/原始箭头位姿元数据
       ├─ 初始化 GT 任务角色 → TaskEntitySet
       │      ├─ 当前选图索引
       │      └─ 当前可信事实 → 增强文本库/状态索引
       └─ 材质/透明/背景/箭头全部完成的最终图
              ├─ 可选 PNG 永久落盘
              └─ 有界新图事件/稳定输入 → 独立 VAE consumer
                                            ↓
                     复用 #53 preprocess / Encode1 / per-view writer
       ↓ 空间输入 sealed，final owner 对齐，所有必需产物验收
       完整 profile 发布
```

继续复用 `g2/offline/atomic_6views_run.py`、`episode.py`、`atomic_6views_metadata.py`、`atomic_6views_snapshots.py`、`g2/views/render_connections.py`、`robot_pose_marker.py` 与现有 resolver。不得复制 renderer 或 Wan 网络，不改变材质、遮挡、1mm/1°更新、Room/Island语义来简化新功能。

推荐新增小型职责模块（名称允许在实现中合理调整）：

| 模块 | 职责 |
|---|---|
| `g2/offline/output_profile.py` | 输出开关、计算依赖、新profile校验、完成条件 |
| `g2/offline/spatial_metadata.py` | 原生投影和成员序列化、独立版本引用、反向索引 |
| `g2/offline/task_entities.py` | 18类任务角色适配、精确source→SG绑定、无歧义证据 |
| `g2/offline/language_context.py` | 原始caption、可信事实、可配置候选模板、文本去重 |
| `g2/latent_cache/streaming.py` | 生产事件消费、有限spool/恢复、调用现有编码/存储核心 |
| `tools/g2/` | 薄CLI和审计入口，不能承载全部业务或被未来Dataset反向导入 |

现有 `g2/latent_cache/{contract,encoding,source,storage,builder}.py` 不重写；仅在确有新profile/来源契约需要时作最小增量。保留原事后 build/verify 入口和旧格式回归。reader 不依赖 VAE、ROS、MuJoCo、EGL 或 producer。

PSM 与 nav_sg 各有 `g2` 包，不得同时无区别加入 PYTHONPATH。原生 RGB-D/ROS 感知路径不能受本次仿真输出升级影响。

## 6. 输出 profile 与发布门槛

支持按配置保存 sixview RGB、Island RGB、SG、空间元数据、任务实体、增强文本、原始箭头pose、view VAE，及明确启用的点云/体素。最小身份、来源、版本、有效性与完成信息不可关闭。

| PNG | VAE | 必须行为 |
|---|---|---|
| on | off | 正常渲染/保存，不加载 VAE |
| on | on | PNG保存，同时事件驱动编码 |
| off | on | 图像仍生成，stable input 在 VAE durable receipt 前不能清理；完成后可不保留 PNG |
| off | off | 无 RGB 依赖时跳过无用渲染，仍保留声明的 SG/元数据 |

关闭保存不是“场景中不存在”。disabled / absent / reference / pending / failed 至少明确区分。unsupported 配置显式拒绝，不生成空文件冒充。

采用显式新 schema/profile；旧 compact v1/v2/v3 validator 严格保留。`profile_complete` 与 `training_ready` 分开；SG-only 可完成，但不是完整训练包。

**避免循环依赖：** #53 的旧补编码入口要求已完成旧package，而新全profile COMPLETE 要等 VAE。新的 producer 接口应先 seal 不可变空间来源 inventory/readiness，再让同一核心完成编码与发布；不得伪造旧 COMPLETE 让缓存开跑，也不能让两个阶段互等。新source inventory 与旧completed-package采用显式版本/适配，必要的source-provenance扩展不能静默削弱旧cache的PNG来源校验。

## 7. 空间元数据与对象—view索引

每个逻辑view正式保存：scene/episode/view ID、room/island、type/direction；world/scene稳定坐标与单位；Room→World或等价变换；right/up/forward、uv_min、投影范围、正交标识、像素中心/行翻转；原始W/H、mpp、真实画幅宽高；成员集合/反向索引/墙根方向依据；image-owner、geometry、membership各自版本；源状态/模型/renderer信息；箭头实际position/forward/frame/source_frame及投影证据。

- 物理画幅覆盖为 W_px×mpp、H_px×mpp；像素中心跨度另算，padding不算物理空间。
- Room origin当前定义是 `[center.x,center.y,0]`，轴由墙几何确定；不直接用3D center或单位轴冒充。
- 关联来自实际renderer `native_entity_ids`，不是像素可见性检测；Object–view是资产关系，不增加物理contains层级。
- 图片沿旧owner复用时使用owner投影；当前成员可以独立更新，不能用PNGhash替代所有版本。
- 同内容几何/成员表可存一次再引用。缺元数据显式缺失，不从最终图片猜世界原点。
- 正交RGB像素只有投影射线，不声称得到唯一XYZ；本轮不新增像素depth。
- 原有state_目录可完全不出现，必须按manifest所有逻辑状态处理。

## 8. TaskEntitySet：仿真初始化绑定

优先 `fixture_refs`，再结合 `object_cfgs` 和固定任务初始化源码，最后是可验证的唯一类别/规范名规则。保存 role、source_instance_id、source_part_id、全部匹配SG IDs、binding_status、依据和规则版本。不能跨episode写死 entity_N；一对多part不能仅取首个。

必须区别：全场景fixtures、干扰物cfg、初始化src_fixture、任务目标、参考物与可能非唯一目的地。`PickPlaceDrawerToCounter` 当前源码允许任意合法counter，登记counter只能作为相关参考，不能改写成唯一允许放置台面。`NavigateKitchen`使用target_fixture，排除仅用于机器人起点的src_fixture；不输出源码里的target_pos/target_ori。

初始化目标通常整集一次绑定；当前位置/成员/view关联从当前状态读取。空fixture_refs不是视觉检索的理由；多义/缺失必须明确报告，不能静默按列表首项选择。第一批需要18类task角色完整适配与CPU用例，再独立做真实覆盖检查。

## 9. 稀疏选图与语言

`selected_views(t) = mandatory_floor_top(t) ∪ union(object_to_views_t[task_entity])`，按真实有效view过滤、确定性排序、去重。完整保留选中图上下文。多Room读实际目录，不把早期`2+4R+4I`概念式当硬合同。保底只处理真正语义不确定，缺文件/错身份/损坏不允许用fallback掩盖。

语言原文权威是原训练 `sample['task']`：当前flat可由frame.task_index→meta/tasks.parquet取得；ep_meta.lang只交叉核对。

增强文本保留完整原任务，附当前相关实体可信事实。禁止猜开闭/抓持/inside/on/成功、写行动步骤或专家控制提示。SG centroid只叫AABB中心；connections不升级成接触/支撑/inside。默认不写快速变化的机器人pose/最近/左前方。

原文、enhanced text分别保留；稳定排序、单位、template_version、文本hash、数字精度和长度策略可配置并记录；text bank＋state→text_id复用。不要按frame强制全部失效；不能离线缓存可训练AR hidden/KV。token IDs只有确定实际formatter/tokenizer后才可绑定。

**当前模板仍未冻结。** 本轮四任务、十二状态的review-only样例比较：A仅role/name/room/island；B再加world AABB center/size，三位小数仅演示精度。它们不是生产数据，也不证明模型已利用文本；不把whitespace word数伪称token数。需要用户检查后再冻结字段、精度、长度与回退。

## 10. 并行VAE与事后入口共享核心

事件发布点必须在最终材质/透明/背景及机器人箭头完成之后，覆盖FULL、ARROW_ONLY和REUSE_ALL；真正新图片编码，引用只更新索引。消费stable不可变内容，不引用会被清理/重写的临时缓冲区。

现有compact会进一步去重floor_top并重写owner，故先用稳定源/内容身份管理任务，最终发布时再归并owner/record映射，不用未定manifest SHA或record号当唯一key。

少量独立consumer复用模型，不随32renderer各加载模型。有界队列/内存/磁盘spool，消费者慢时允许背压，不丢图、不宣称永不阻塞。清理与durable ack关联；失败保留已合法RGB/SG，VAE pending/failed可独立恢复。

writer同目标互斥；有限内存或临时分块累积后按确定顺序一次发布per-view文件，不逐条重写整文件。不新增通用MQ平台、多存储后端或跨episode内容寻址系统。

B=1/T=1仍是参考；事件streaming不等于Wan temporal streaming。B>1仅在独立数值与隔离Gate通过后启用。两入口同最终像素、同recipe、同数值判据；不能静默放宽以追求吞吐。

## 11. 本轮实际诊断与文件

服务器独立诊断根：

```text
/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_offline_data_prep_takeover_20261116/evidence/
```

### 11.1 原有环境CPU基线

固定Root778d1ed8/Childd5c1ffc7，原有psm_wma解释器，CUDA_VISIBLE_DEVICES=''，10个已有相关测试文件：**283/283 PASS，8.86s**。原始日志 `baseline_cpu.log`、JUnit `baseline_cpu.xml`。这是已有实现回归，不计作新生产模块已完成。

执行形式：

```bash
cd /mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_view_vae_real_gate_20261116/source
PYTHONPATH="$PWD/cosmos-framework:$PWD" CUDA_VISIBLE_DEVICES='' \
PYTHONDONTWRITEBYTECODE=1 COSMOS_DEVICE=cpu COSMOS_TRAINING=0 COSMOS_INTERNAL=0 \
/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin/python \
-m pytest -q -p no:cacheprovider g2/tests/test_view_vae_*.py \
g2/tests/test_scene_view_event_index.py g2/tests/test_scene_view_index_package.py \
g2/tests/test_scene_graph_compact_v3.py --junitxml=<evidence>/baseline_cpu.xml
```

### 11.2 真实GT/语言诊断

`inspect_gt_language_samples.py`只读计划、原ep_meta、flat任务表及frame task_index、现有SG resolver；未加载模型、仿真或产生正式新schema数据。

- 18类各一条初始化元数据：12条fixture_refs非空、6条为空；不是全库role覆盖。
- 四条代表：CloseBlenderLid/0、CloseFridge/502、NavigateKitchen/2104、PickPlaceDrawerToCounter/5077。
- 共1,359条raw frame caption与ep_meta.lang一致；每集初/中/末3个空间状态，共12状态。
- exact source_instance→SG全部part匹配；对当前四例未出现缺失。Nav排除src；Drawer reference不收紧目标。
- 在三个采样状态中，A模板每任务1种；B模板前三类中Blender/Fridge各3种、Nav1种，Drawer3种。不能从三个采样点推断整集更新次数。
- 输出 `task_metadata_18_sample_audit.json`、`gt_language_review_samples.json`、`gt_language_review_samples.html`、`gt_language_review.log`。
- 用户可访问既有本地服务：`http://127.0.0.1:18765/g2_offline_prep_20261116/index.html`，已HTTP200回验。私有图像/原始源数据不上传GitHub。

### 11.3 全库完成标识核查与预算起点

`inventory_current_global_packages.py`按固定计划读取episode_manifest与COMPLETE，检查身份、manifest精确SHA、声明state数；**不等价于逐张PNG/SG内容验收**。

| 指标 | 本轮结果 |
|---|---:|
| planned / manifest-complete | 9,126 / 9,126 |
| 缺失/不合法manifest-completion组合 | 0 |
| schema | 全部compact_v3 |
| logical spatial states | 235,475 |
| 实体PNG owner记录 | 515,687 |
| 逻辑PNG引用 | 650,222 |
| 若全view编码的数值文件数 | 45,843 |
| 正式源目录已有cache COMPLETE | 2，历史样例，不代表全库编码 |
| 候选FP32 [48,16,16]纯tensor预算 | 约23.606 GiB，不含索引/文件头/临时spool/新PNG与SG |

输出 `current_global_manifest_inventory.json/.log`。现场data1可用约101GiB、data约274GiB；新全profile staging与旧资产共存还需精确预算，不能从latent单项较小推断总空间足够。

## 12. 实施顺序与验收交付

### A1：profile、投影/成员、GT实体与语言候选

先给实际改动文件表和简短ABI；实现新profile依赖、原renderer元数据正式导出、18任务TaskEntitySet、独立selection/text版本与候选配置；复用旧renderer/resolver。CPU验证新旧协议各自严格、同名跨Room/Island、无目录引用、动态absence、一对多part、distractor/src排除、确定性文本和无未来信息。

### A2：并行编码集成及完整发布

延续#52核心，新增不可变事件/有限spool、producer/补算统一来源适配、one-writer与resume、consumer失败/慢速/乱序/清理、完整profile发布。保留#53原283测试；B>1未经真实证明不用作默认。不要重复做已经关闭的importer边界审核。

### A3：固定源码真实样例与文件生成

在原有环境、隔离staging，至少覆盖上述四条及多Island/缺失方向/异尺寸；对相同renderer recipe核对旧新像素/状态引用，检查投影与箭头一致，真实审查任务角色和语言，比较两VAE入口像素与latent，核对恢复及保存组合。测量资源、吞吐、queue/spool峰值与读取分位数，不预设任意加速百分比。

每个阶段提交：固定Root/Child/nav版本、源码改动范围、精确命令、输入身份、输出路径、CPU/GPU/人审分别的PASS/FAIL、失败原证据和未完成项。新代码先固定SHA与Draft，再服务器验证；候选分支可以基于已审核#53并整合本V3文档补充，但不能自动把#53合入V3或重做缓存核心。

### A4：冻结配置后全量

只在模板/画布/dtype/batch/资源profile由样例确定后全量。新staging保留旧数据；逐task统计planned/complete/pending/failed及各类产物覆盖；不能跳过失败计DONE。所有声明输出校验通过才写全profileCOMPLETE，发布切换/旧清理仍独立处理。

### B/C：当前只保留合同，不实施

B固定方向raw15 action不变、state15为Pose5＋原EEF10、z保留；需实查mobilebase0_center site与mobilebase0_wheeled_base body，20Hz当前raw状态，不从2Hz箭头插值。禁止全局action归一化、未来轨迹minmax、验证集统计和偷偷清零前五维。

C联合task/global-local episode/rawframe/action window、G1 latent、state15、causal spatial state、SG、selected view的latent/几何/成员、text_id。训练cache miss不能隐式运行VAE/renderer/ROS/LLM。A+B+C未全过，不宣布G2训练输入全部准备完毕。

## 13. 当前状态边界

已完成：全文接收、最新决定归档、现场版本/Issue/PR核对、已有缓存CPU复跑、真实GT与语言候选诊断、全库manifest级盘点。

未完成：新增profile/metadata/18任务角色/语言正式模块、并行VAE与新profile发布实现及其新CPU测试、升级producer真实回放对照、多配置性能/质量Gate、模板/生产参数冻结、全量新版本生成、state15、联合对齐、模型接线/训练。

本文件是落实最新Owner方向的执行合同与本轮实查记录，不把诊断脚本冒充生产实现，不把历史真实VAE202样例外推为新producer集成已通过。
