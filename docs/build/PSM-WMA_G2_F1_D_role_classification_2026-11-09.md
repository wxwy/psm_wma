# G2-F1-D：真实部件来源分类候选

本轮目标为 Layout1 的161项、Layout10的429项原未知角色。已通过的aef1ec04彩色点云及两场景部分点云人工结论保留，不重复导出、渲染或验收。角色分析工具dcd8a93d已获GPT AUDIT_ONLY批准；本轮为独立分类实现。

复用 `role_review.analyze` 原两帧/原XML/编译签名/来源上下文校验，新增 `g2.sim.role_hypotheses`。输入原位留服务器。全部正式源码在代码仓开发发布，服务器仅检出固定副本做作者分析；不是GPT独立验收。

## 可复现的实例规则

| 规则 | 必须同时具备的来源实例证据 |
|---|---|
| Counter台面与collision chunks | 官方Counter实例和真实body祖先；原box size/pose与compiled一致；台面真实材质绑定；与工厂0.5m分块数量、逐块宽度/位置/父body完整一致；局部朝向为工厂identity，不能以一起旋转三块冒充覆盖 |
| 其余碰撞primitive | 官方实例祖先；原primitive type/size/pose与compiled一致；实际接触掩码、无表面材质、原碰撞显示RGB标记、求解参数；同实例有材质可见表示；冻结生成器contact registry合同。不按group或名字单独分类 |
| 顶层Fixture区域 | 真实官方Fixture.naming_prefix下明确reg_注册；原primitive/compiled一致；透明、无接触、无材质。普通子body名称中带reg不代表注册根 |
| 嵌套门板/把手对齐helper | 官方Cabinet/Drawer父实例；工厂允许的door/left_door/right_door及handle直系body链；原reg_main primitive；同一真实nested实例下的有材质可见mesh；mesh文件实际命中原asset闭包哈希与公开registry具体model.xml；仅模型实际发出的object子树；bbox与mesh的缩放/位置/朝向一致。缺任一保留unknown，不以“透明+名字”排除 |
| Window背景 | 官方Window与原region尺寸；薄box、真实材质/纹理；组合body的实际源文件/hash/XML位置、尺寸及变换。按include真实上下文展开，忽略被包含根wrapper，并检查compiled直接父链，不能使用假wrapper或省略有变换的未命名body |
| 原始透明Accessory visual | 官方Accessory构造来源、原primitive/compiled、真实noncontact visual registry。透明本身不使其成为auxiliary；不推断未证明的语义用途 |

代码引用及原始文件SHA：`G2_F1_D_generator_role_catalog_2026-11-09.json`。其中model registry由固定公开代码的literal字典提取，不按模糊目录关键字匹配。模型XML及mesh实例证据的原文件只在服务器核对。

真实作者首轮474项已得到来源绑定候选，余116项的模板helper均无inline RGBA、具有显式class并有透明geom默认值。本轮正确解析main/嵌套default继承、geom.class及body.childclass，保留effective模板透明条件；不是省略透明验证或将任意透明geom改辅助。新增透明default/childclass正控和不透明default负控；按原生MuJoCo对照保留合法顶层main合并，拒绝嵌套main、非法top rename与重复具名class。完整作者CPU371/371，原366/363及历史336案例全部保留。实际最新两场景覆盖与余项以固定SHA交接结果为准。

## 固定版本与真实作者结果

正式实现Root为`6b04d214608eafea1da5c0bdd6f072ecc926ebca`，tree=`160514c3a96b04571e0f921b45a47340b7430ca0`，分支`codex/g2-f1d-role-classification`。之后的交接提交仅含文档/汇总证据，不替代实现SHA。作者CPU371项通过；服务器作者run06和GitHub40个G2文件blob均匹配该SHA。

| 原未知部件 | 来源绑定候选 | collision | visual | auxiliary | 无候选 |
|---|---:|---:|---:|---:|---:|
| Layout1 | 161 | 120 | 8 | 33 | 0 |
| Layout10 | 429 | 333 | 13 | 83 | 0 |

33/83个辅助候选全部由具体注册模型的对齐helper规则产生，要求原资产hash、发出的object子树、实际父链、缩放/位置/方向、默认类透明值及非接触证据；未把不支持几何或可见部件改辅助。原先474条候选逐条一致。以上为作者建议计数，590项全部`role_certified=false`/待GPT；原库存unknown计数仍161/429。新建议映射仅改变这些占位项，原已分类项和其他元数据保持。逐部件证据/建议映射留在服务器，本仓只保留汇总、原库存及结果文件hash。

来源参考的限制：11份生成器源码中3份与服务器现有源码匹配，8份来自明确标记的固定公开参考快照。它们不是Episode历史生成器版本证明；不能把旧GPT确认9份当前源码或本轮公开源码hash一致当作历史构造分支认证。全部28个引用片段的真实行界/hash经预检查；`handles.py`的369..396旧引用越过394末行已修正，字节/hash不变。GPT需独立检查每个原始源节点、实例、资产及生成逻辑，而非接受公开参考即认定角色正确。

服务器隔离作者执行入口（固定仓库代码，只读原输入；需要NumPy，无MuJoCo/GPU/训练）：

```bash
cd /mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_f1d_author_roles_20261109/source02
CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python3 \
  docs/evidence/g2_f1_d_2026-11-09/run_server_local_author.py \
  --runtime-json ../runtime.json \
  --catalog docs/build/G2_F1_D_generator_role_catalog_2026-11-09.json \
  --public-reference-root ../public_reference_from_connector \
  --output ../author_run06
```

这是已经完成的作者命令；`author_run06`存在，不得覆盖/重跑。GPT复验请用新的隔离检出及不存在的输出目录，先核对40源文件blob及目录中11参考文件hash、28片段。命令运行不访问外网；参考快照提前从GitHub固定版本入站。`runtime.json`仅保存服务器本地输入/现有生成器根位置，不外传。此前local-clone/HTTPS证书失败的作者日志和后续引用范围拒绝结果均原位保留，没有关闭TLS校验或修改服务器源码；最终输入、proposal和证据以run06为准。

真实报告根：`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_f1d_author_roles_20261109/author_run06/`，下有`layout1/`、`layout10/`。详见仓库`docs/evidence/g2_f1_d_2026-11-09/server_author_aggregate.json`和`server_disk_integrity.json`中的各文件hash。初次落盘核验脚本错误要求未知占位值也不变，已更正为仅允许590占位项在新建议映射中变化，未改候选代码/结果，不计候选问题。

## 输出与审核边界

新目录保存 `hypotheses.json`、`candidate_evidence_analysis/role_analysis.json`、`proposed_roles.json`、`unresolved.json` 和 `summary.json`。这是建议映射，不写现有配置或生产角色。原始unknown计数保持，候选状态`AUTHOR_PROPOSED_PENDING_GPT`，`production_roles_changed=false`、`full_scene_source_certified=false`、`training_ready=false`。角色映射建议保留原声明、原state_source、官方ep_meta身份及源节点/compiled proof。失败或冲突不为凑590定类。

整个输出根必须不存在且避开原XML/assets/metadata/生成器目录；在任何写入前检查。只读生成器，绝不执行其Python代码。只有明确允许的公开参考源码下载能入站，且校验原SHA/bytes，来源标为公开快照，不冒充原位或历史Episode代码。此前GPT已核对9个文件是本轮历史证据，不意味着新增参考或每个历史构造分支自动通过。

```bash
CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
python -m g2.sim.role_hypotheses \
  --inventory "$FRAME0_INVENTORY" --inventory "$FRAME200_INVENTORY" \
  --catalog docs/build/G2_F1_D_generator_role_catalog_2026-11-09.json \
  --generator-root "robocasa=$ROBOCASA_SOURCE_ROOT" \
  --generator-root "robosuite=$ROBOSUITE_SOURCE_ROOT" \
  --output "$NEW_SERVER_LOCAL_ROLE_PROPOSAL"
```

输入为服务器已有1020/2115 geom的两帧inventory；无需新建云、相机、图像、GT结构根或训练。原位作者运行辅助入口为 `docs/evidence/g2_f1_d_2026-11-09/run_server_local_author.py`，runtime.json和所有逐部件输出都留服务器，只输出聚合计数/哈希/阻塞摘要。现存库与固定公开参考快照分别记入provenance。

## 本轮交付与后续顺序

先提交独立代码并原位生成实际两场景分类候选、来源证明及余项，再冻结SHA交GPT独立复验。作者CPU合成规则测试和真实作者计数都不等于GPT批准；确切结果以证据/Inbox固定交接为准。

GPT逐项核对原source/model/XML/material/geometry/body、规则分支和两帧一致性，保留无法确认项。来源分类批准后再推进nav_sg普通Floor/Wall/Room/Object/Island和空间关系，然后六视角/Island交用户人工。本仓不重复实现房间分割。不合并未验收代码，不启动GPU/Cosmos训练，不动V3、nav_sg、Gitlink或生产缓存。
