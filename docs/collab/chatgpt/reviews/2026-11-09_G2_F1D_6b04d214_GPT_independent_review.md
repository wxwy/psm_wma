# G2-F1-D — GPT data 服务器独立审核：590 项来源角色候选

- 日期：2026-11-09（CST）。
- 固定候选：`6b04d214608eafea1da5c0bdd6f072ecc926ebca`；源码 tree：`160514c3a96b04571e0f921b45a47340b7430ca0`。
- 开发交接：[PSM-WMA Issue #26 / 6732441556](https://github.com/wxwy/psm_wma/issues/26#issuecomment-6732441556)。原 G2 F1-C 和角色分析工具的 GPT 限域通过见 [Issue #26 / 6731502313](https://github.com/wxwy/psm_wma/issues/26#issuecomment-6731502313)。
- 结论：**`APPROVE_SCENE_BOUND_ROLE_CANDIDATES_LAYOUT1_LAYOUT10_ONLY`**。接受本轮两个固定场景的来源角色分类建议进入独立集成测试；**未批准整屋材质/连续表面覆盖、历史 Episode 生成器修订、完整 nav_sg 正常感知和训练**。

## 1. 真正独立的来源和 CPU 检查

GPT 在 data 服务器开辟全新隔离目录，从 GitHub 获取固定 SHA，并直接对比 Git tree 与工作区 `git hash-object`：**40/40 G2 源码、配置、测试 blob 完全一致**；其中旧 `dcd8a93d` 的 **38/38 文件逐字节没有改变**。原版 F1-C 精确零面积、全部正面积保留、原 face ID/UV/状态/颜色审计仍冻结。

独立 CPU 运行 **371/371 PASS、0 failed/error/skip**。核对 JUnit 的 testcase ID：旧336项全部保留，新增加35项。测试不是作者日志复述。

参考原生成器的 **11/11 个文件**在 data 服务器现有 RoboCasa/robosuite 源码目录的字节 SHA256 全部与本次固定 catalog 一致；规则引用的 **28/28 个源代码片段**，其行界和片段 hash 亦直接校验通过。作者原报告仅 3 个 current-source match，是其 `runtime.json` 只配置了缓存中的 robosuite generator root，其他文件使用公开快照；GPT 这次直接检查了服务器完整 `/mnt/data1/data_v2_0617/robocasa_repo` 和 `robosuite_repo`。但两个工作树实际 HEAD 与 catalog 所引固定 commit 不同，且找不到足以证实原 Episode 录制当时完整生成器修订的记录，故**不得声称历史 git commit 已被认证**。此项不妨碍依据已封存原始 MJCF、asset、compiled geometry 直接核实当前特定场景的物理与渲染角色。

## 2. 真正重新生成，而不是接受作者 590 行文件

GPT 使用新固定代码、上一轮 GPT 独立产生的原始 Layout1/10 frame0/200 全几何 inventory，结合**服务器原位真实生成器源码**重新生成两场景候选。不是复制或修改作者 `author_run06`。两个场景的 `hypotheses.json`、`proposed_roles.json`、`unresolved.json` 与作者固定的 SHA256 **逐字节一致**。

| 逐部件来源分类 | Layout1 | Layout10 | 合计 |
|---|---:|---:|---:|
| 原未知项目 | 161 | 429 | **590** |
| 可碰撞几何 | 120 | 333 | **453** |
| 新视觉几何 | 8 | 13 | **21** |
| 非渲染/非碰撞辅助几何 | 33 | 83 | **116** |
| 无来源绑定候选 | 0 | 0 | **0** |

全部590项逐个绑定原始 XML 源节点与 hash、编译几何签名、官方 ep_meta fixture/body、帧0和200及原色/接触属性；**原先已经分类的859/1686项声明保持逐项不变**。分析工具中590项的 `review_state=EVIDENCE_BOUND_CANDIDATE_PENDING_GPT` 是作者未晋升时的源记录，不以手改标志制造通过。

### 116 项辅助部件的额外复核

对 **33+83=116 个**嵌套门板/把手 helper，GPT 自写独立 XML 与几何校验，不调用作者判别函数进行结论判定。每项均验证：

- 真实原始 `CabinetDoorPanel...` / `CabinetHandle...` model.xml 内容 hash，与其嵌套 `reg_main` 继承 default 的 **alpha=0**；
- 实际编译几何无物理接触、group=1、无真实可见材质，父 body/source 绑定一致；
- 同一 body 下真实可见 mesh sibling 存在，且物体体积框大小、缩放、位置、四元数与原始 template 逐项吻合；
- 原始 scene mesh 资产 hash 匹配，不能将真实可见门板/把手一起丢弃。

所有 **116/116 PASS**，涉及5个实际模型 XML。它们适合从**彩色可见表面采样**排除，但应保留源几何与关系/region 证据，不代表从场景状态删除。

### 其余候选

- 柜台台面：**17** 块有真实材质的 visual 与 **42** 块碰撞分块，GPT 按真实原 size/position 与生成器的0.5m分段公式逐块独立复算，**59/59 对应关系一致**。
- 其余 **411** 个已有原始接触/求解参数、无可见材质且有同实例视觉表示的 primitive 标记为 collision。检查了原XML的接触位、形状、几何、原始颜色标记及官方fixture身份，不凭 group/name 单独归类。
- Layout1 的3个透明液体/玻璃杯视觉组成部分**仍归 visual**，未为了减少 unknown 错归辅助；它们因透明度0不产生彩色表面点。
- Layout10 的1个 Window background 有原始纹理、材质、体尺寸与组合 body 变换对应，归入 visual。

## 3. 真正用候选映射重新导出四帧（隔离诊断，不改生产）

GPT 使用固定生产源码原始 MuJoCo model/state/ep_meta、`proposed_roles.json`、`--require-role-evidence` 严格来源检查，四帧重新写入**新的 data 隔离证据目录**。每帧磁盘级 `precolored.txt`、`color_audit.npz`、manifest 经 `verify_color_evidence` 复核。新数据和此前已验证 F1-C 数据逐 geom 对比，确认**原来已采样的每个 XYZRGB、有效位、原 face ID、逐点面积权重完全一致**。

| 场景 | 原已采样点 | 角色候选应用后采样点 | 新增点 | 新增点颜色 |
|---|---:|---:|---:|---|
| Layout1 frame0/200（每帧） | 1,110,591 | **1,113,611** | **3,020** | 全部有效 |
| Layout10 frame0/200（每帧） | 2,135,041 | **2,149,469** | **14,428** | 全部有效 |

实际采样新增的可见几何：Layout1 **5** 个、Layout10 **13** 个；另外3个已证实为透明 visual 的部件没有彩色采样点。最终角色声明覆盖所有 1,020/2,115 个编译 geom，`unclassified_geom_count=0`。源模型 closure、原状态 hash、可见几何/颜色审计不变，视觉来源 producer SHA 按新的角色输入正确变化。

**四帧仍然是 `PARTIAL_COLOR`**，Layout1 每帧 **88,258 个**颜色无效点、Layout10 每帧 **144,812 个**颜色无效点必须保留；不能用未认证颜色冒充原资产外观。四帧 `training_ready=false`、`full_scene_source_certified=false`，未生成训练就绪的认证。它们是场景特定的角色映射**独立诊断结果**，不是已合并生产映射。现有 Layout1/10 用户人眼通过仅针对之前的部分彩色点云，不代表本轮正常 nav_sg Room/SceneGraph 人工通过。

## 4. 限制、下一步谁做

**本轮认可的是对这两个固定场景的“几何角色候选映射”**，有原始模型、生成器字节、资产 hash、实编译接触/材质和两帧数据支持。未完整证明历史 Episode 的生成器 Git 修订；没有验证真实模型输出的每个颜色像素、连续表面覆盖，更未验证普通 nav_sg/YOLOE/SigLIP。不可将它升级为通用 RoboCasa365 全场景语义分类器；不可直接合并生产或启动 Cosmos。

**下一步 Codex**：将这一固定 SHA/场景范围下的被认可建议角色与原始逐部件证据做版本化、可追溯的独立发布与正式候选输入配置（确保 role-map 对应不可变证据 SHA，仍不改 V3/Gitlink）；同时优先实现 [nav_sg Issue #8](https://github.com/wxwy/nav_sg/issues/8) 的正常 Floor/Wall/Room/Object/Island 与关系图，不要在 PSM-WMA 里重新编写房间分割。不能用 MuJoCo oracle Floor/Wall/Room 标签伪装 native perception。**下一步 GPT** 对完整原生主程序在 Layout1/10 frame0/200 的 Room/footprint/Wall/Island/Object 结果做独立验收；六图+Island 必须来自 nav_sg 真实 snapshot，再交用户人眼检查。PSS/Cosmos 延后。

## 5. 原始证据留 data

隔离服务器工作区：

`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_f1d_6b04d214_gpt_independent_20261109/evidence/`

机器总报告 `gpt_f1d_independent_acceptance.json` SHA256：

**`8412b731787f2b686357d1ac4731729547da457f3906e35f407542755815bce5`**。

其中列有19份关键原始测试/来源/116模型/59柜台分块/真实四帧/逐 geom 精确无回归对照证据的文件 SHA256。原始数据、逐部件几何、状态、彩色点云、图片全部留在 data 服务器，未外传。仅此审核文本发布到 GitHub 独立评审分支；原 V3、nav_sg、Gitlink、原 PR、缓存、模型、训练与 GPU 均未改动，未合并、未建 Draft PR。
