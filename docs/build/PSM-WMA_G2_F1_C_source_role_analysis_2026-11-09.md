# G2-F1-C 第二阶段：整屋分类来源分析与服务器逐部件证据表

采样正式候选已独立发布为 `aef1ec04d631ef23c9b3f04dd2ab0f11344e2f21`，交接 [Issue26 / 6731022450](https://github.com/wxwy/psm_wma/issues/26#issuecomment-6731022450)。本阶段为另一分支 `codex/g2-f1c-role-analysis`，不改冻结的四个 producer 文件、采样行为、nav_sg、Gitlink 或视图。

**已完成的是公开生成代码追溯和服务器本地分析入口，尚未完成真实590项定类。** Layout1的161、Layout10的429个原始逐部件审计/资产都在data；本工作区没有读取或复制它们，不能填写不存在的geom身份或声称清零。公开代码版本也不能自动当作服务器生成该Episode的版本。

## 已核对的原始生成语义

公开参考固定 RoboCasa `3443cdf3dd20f9ae8ed41adba442059b506891d0`，robosuite `5ce6643f3092639d08f7b0f90ed1c6a84f50552c`；九个文件的完整bytes/SHA256/Git blob及十四个引用片段已逐项核对。机器目录：`G2_F1_C_generator_role_catalog_2026-11-09.json`。这是有条件的来源参考，不是已匹配服务器版本的结论。

| 待查部件族 | 原始代码证据 | 逐部件必须补齐的依据 |
|---|---|---|
| 完整台面visual | [Counter:311](https://github.com/robocasa/robocasa/blob/3443cdf3dd20f9ae8ed41adba442059b506891d0/robocasa/models/fixtures/counter.py#L311) 明确创建完整box、绑定台面材质、非接触，并登记 `_visual_geoms` | 原fixture/构造分支，w/d/h/th/half_top，body、原XML节点、编译size/pose和材质对应，不能仅认 `_visual` 名字 |
| 台面碰撞分块 | [Counter:280](https://github.com/robocasa/robocasa/blob/3443cdf3dd20f9ae8ed41adba442059b506891d0/robocasa/models/fixtures/counter.py#L280)、367：按0.5m宽度分块，单独登记 `_contact_geoms`；带开孔分支497–540同理 | 重现分块尺寸/位置与contact登记，确认原碰撞定义；不能把半透明碰撞调试色当真实表面材质 |
| 窗背景 | [Window:362](https://github.com/robocasa/robocasa/blob/3443cdf3dd20f9ae8ed41adba442059b506891d0/robocasa/models/fixtures/windows.py#L362) 使用有材质的 `BoxObject(obj_type="visual")`，组合进窗体 | 原Window构造分支、背景尺寸/相对变换、2D纹理和实际父body；背景不能因名称/位置而改作auxiliary |
| 区域定义geom | [Fixture:127](https://github.com/robocasa/robocasa/blob/3443cdf3dd20f9ae8ed41adba442059b506891d0/robocasa/models/fixtures/fixture.py#L127) 将相应geom登记到 `_regions` 并设透明 | 必须证明该实例确由region定义消费、实际非接触且透明；透明本身不能区分区域、玻璃和液体 |
| 门板/把手/连接件 | [CabinetPanel:191](https://github.com/robocasa/robocasa/blob/3443cdf3dd20f9ae8ed41adba442059b506891d0/robocasa/models/fixtures/cabinet_panels.py#L191)、[Handle:38](https://github.com/robocasa/robocasa/blob/3443cdf3dd20f9ae8ed41adba442059b506891d0/robocasa/models/fixtures/handles.py#L38)、[MujocoXMLObject:395](https://github.com/ARISE-Initiative/robosuite/blob/5ce6643f3092639d08f7b0f90ed1c6a84f50552c/robosuite/models/objects/objects.py#L395) | 追到被组合的原XML/复制visual分支、nested body变换和材质；不能仅用父fixture的旧顶层registry漏掉子对象 |
| 辅助生成fixture、透明液体、其他无法证明项 | [scene_builder:175](https://github.com/robocasa/robocasa/blob/3443cdf3dd20f9ae8ed41adba442059b506891d0/robocasa/models/scenes/scene_builder.py#L175) 的auxiliary是生成/放置关系，未给出“非场景表面”的语义 | 继续UNCLASSIFIED；逐项查真实生成定义和可见/碰撞用途。无本轮自动排除规则，不能为提高完成率将它们改auxiliary |

robosuite的 [visual/collision模板](https://github.com/ARISE-Initiative/robosuite/blob/5ce6643f3092639d08f7b0f90ed1c6a84f50552c/robosuite/models/objects/objects.py#L612) 与 [生成分支](https://github.com/ARISE-Initiative/robosuite/blob/5ce6643f3092639d08f7b0f90ed1c6a84f50552c/robosuite/models/objects/generated_objects.py#L736)说明group/接触标志的来源。这可用于核对已追踪的构造分支，不能反过来把所有group0/1一律定类。

## 逐部件工具与边界

复用 `g2.sim.asset_inventory` 的真实两帧AUDIT_ONLY输出；新增 `g2.sim.role_review` **只生成分析表**。不执行生成器，不恢复/重建环境，不上传文件，不写生产roles map、不写COMPLETE。

输入必须匹配：两帧scene与hashed metadata、完整model closure、source parsing/include上下文、严格frame/state archive、原始XML节点和compiled/body/geometry签名。原始XML由现有冻结 `source_geom_nodes` 原位重读/验hash，而非信任可自签的JSON片段；源文件根目录及generator目录不能成为输出位置。既有role必须通过hashed原声明和冻结 `source_binding()` 重算；不能靠同时篡改两帧role清空未知数。

输出逐geom保留原角色、几何/材质/采样状态、body、原XML与编译证据。未知项始终 `role=UNCLASSIFIED`。每个显式假设要求正确的node/compiled身份、生成代码原文件SHA/引用行、对应分支和每个条件的本部件解释；代码版本不同、缺证据/错条件均是 `EVIDENCE_REJECTED`，仍保留该项和其余未知项。候选只标 `EVIDENCE_BOUND_CANDIDATE_PENDING_GPT`；`remaining_unclassified_count` 仍包含它，`role_certified/training_ready/full_scene_source_certified=false`。

现有已声明项仅 `DECLARED_NOT_RE_REVIEWED`，也不被本工具提升为独立审核通过。输出 `hypotheses_template.json` 的null字段必须逐项填写；**不把公开reference规则命中当作自动语义认证**。修改生成器目录或版本应更新公开可审的catalog，不改哈希绕过校验。

## GPT服务器本地执行与Codex后续实现接口

所有路径用服务器既有输入替换；产物放新隔离目录。先按固定采样SHA完成四帧Gate，保留每帧新 `asset_inventory`（源码需来自该固定候选，另增加本工具即可；producer原文件必须相同）。

```bash
# 当前源码仓是实现来源；不在服务器生产checkout编辑。
CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
python -m g2.sim.role_review \
  --inventory "$LAYOUT_FRAME0_INVENTORY" \
  --inventory "$LAYOUT_FRAME200_INVENTORY" \
  --catalog docs/build/G2_F1_C_generator_role_catalog_2026-11-09.json \
  --output "$NEW_SERVER_LOCAL_ANALYSIS"
```

该命令先输出完整逐部件表与空的假设模板，不读取generator。分别在Layout1/10核对unknown确为161/429、全部geom为1020/2115；这些是既有review目标值，不是本工具硬编码的通过条件。若数量不同，保留实际表与原因，不删项补数。

逐项构造来源分析应依照上表：Codex在仓库补可复现的规则/解释，GPT对照本地实际生成器、XML/材质和compiled geometry独立核验。当前未获得私有逐项输入，**没有替590项预填结论**。若确认生成器版本与公开catalog完全一致，并已有本地逐项假设，可验证：

```bash
CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
python -m g2.sim.role_review \
  --inventory "$LAYOUT_FRAME0_INVENTORY" \
  --inventory "$LAYOUT_FRAME200_INVENTORY" \
  --catalog docs/build/G2_F1_C_generator_role_catalog_2026-11-09.json \
  --hypotheses "$SERVER_LOCAL_PER_COMPONENT_HYPOTHESES" \
  --generator-root "robocasa=$SERVER_ROBOCASA_REPO_ROOT" \
  --generator-root "robosuite=$SERVER_ROBOSUITE_REPO_ROOT" \
  --output "$ANOTHER_NEW_SERVER_LOCAL_ANALYSIS"
```

repo root需包含catalog里的 `robocasa/...` / `robosuite/...` 相对路径。版本不匹配时该候选保留拒绝理由，不能用当前public main冒充Episode的实际生成源码。公开版本号/哈希和聚合结论可以交接；私有逐部件文件、原资产、状态、图片、点云都留服务器，不需要向Codex上传。

**本阶段验收待完成**：真实590项逐部件假设与独立角色判定、未解决清单、全屋来源审核签字。工具/参考分析是已完成的可复核实现，不等于这些真实分类已完成。

## 完整房屋导出方案与执行顺序

1. 冻结F1-C采样候选由GPT关闭四帧几何/颜色/原face/UV/状态Gate；不能用服务器原型代替新SHA。
2. 分别保留全部源geom，逐项核对上述角色依据与未解决项。已批准角色再由正式代码/配置形成现有 `g2_sim_prescan_v1` 声明与source proof；本分析工具不自动写入。可见背景/家具/液体缺颜色时保留无效原因，不能伪装辅助角色删掉。
3. 使用现有 `g2.sim.prescan --require-role-evidence`；诊断阶段保留 `--allow-unclassified --allow-partial-color`，状态PARTIAL_SOURCE/PARTIAL_COLOR，training_ready=false。新输出namespace、新producer manifest/附件。全部角色与真实材质/整屋来源独立审定后才申请既有full-scene review，不能将声明子集COMPLETE升级成整屋通过。
4. 输入稳定后转nav_sg#8，使用固定完整原生主程序四帧构建普通Floor/Wall/Room/Object/Island和空间关系；PSM不实现第二套房间分割，也不以GT结构根冒充普通感知。RGB-D对象感知是独立未完成项。
5. G2仅从真实nav_sg快照生成六图/Island，对照MuJoCo原场景由GPT和用户分别验收。PSS/Cosmos在此前保持未启动，不训练、不合并。

作者CPU/代码复核的确切结果与固定分析提交见本批Inbox/evidence交接；它们不取代GPT服务器源审核。V3、nav_sg、Gitlink、训练/缓存和原PR均未改。

本批作者结果：完整336/336，0failure/error/skip；原291全部保留，新增45个来源/隔离/错误输入正反控。公开9文件/14片段已验原Git blob；自建真实两帧catalog匹配例只有1个候选，unknown仍4、实际角色写入0。另一个Agent确认五类P2已关闭、限定范围无开放P0/P1/P2；原36个冻结G2文件和adapter SHA逐一未变。原始日志/JUnit、保留索引、自建逐部件示例和代码复核位于 `docs/evidence/g2_f1_c_roles_2026-11-09/`。真实590项没有在这里完成分类。
