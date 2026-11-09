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
