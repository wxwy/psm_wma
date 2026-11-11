# G2-F1-E：已审核的两场景角色输入封装

依据固定F1-D实现6b04d214和GPT正式报告f86ecef5（blob1fe9d18f），
Issue26/6732760420。只接受两个已封存场景及frame0/200；原371项功能不变。
本次新增独立scene_release模块/26个契约用例及固定公开profile，不触碰
采样、材质、身份、对象模型、nav_sg或V3/Gitlink。

固定profile为`g2/config/scene_role_profiles_2026-11-09.json`。只包含计数、
模型/状态/两帧原清单/角色映射/逐项证据/catalog/GPT机器ledger的SHA、
review/source commit和批准范围，不包含私有部件名称或原文件载荷。
模块代码内固定profile完整字节SHA，CLI不能自行重签profile或复用verdict文本。
TEST_ONLY自建夹具仅用pytest monkeypatch注入自己的临时authority。

`scene_release package`复制已批准的原始映射及证据字节到新服务器目录，
不执行生成器/MuJoCo，不采样、不改生产映射。两帧原XML/编译/官方身份合同、
每项新role assertion、候选及analysis输入闭合均检查；两帧全部原始asset/
metadata/ep_meta/state引用按canonical路径去重且冲突拒绝，整archive及0/200
实际row重新哈希。原先已分类项必须原样保留。源目录、既有输出不可覆盖。

产物：role_map.json、hypotheses.json、component_evidence.json、两帧inventory、
generator_catalog.json、GPT机器ledger、config.json、release.json，最后才写
`RELEASE_COMPLETE`（release.json SHA）。`verify`重读实际消费的固定文件名，
拒绝合法替身掩盖坏canonical文件，校验原位所有外部引用及实际state数据。
改变manifest/marker不能升级认证。原候选证据中的pending状态不改写；
独立批准由不可变review/profile表达。

```bash
CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python -m g2.sim.scene_release package \
  --profiles g2/config/scene_role_profiles_2026-11-09.json --layout 1 \
  --inputs "$SERVER_LOCAL_INPUTS_JSON" --output "$NEW_SERVER_LOCAL_RELEASE"
python -m g2.sim.scene_release verify \
  --profiles g2/config/scene_role_profiles_2026-11-09.json --output "$NEW_SERVER_LOCAL_RELEASE"
```

inputs JSON必须含roles/hypotheses/analysis/catalog/approval/frame0/frame200七个
本地文件路径，只留服务器。layout10同样使用独立新目录和固定profile。
原始MJCF/assets/states/图片/点云及全部逐部件文件不出服务器；只输出计数/hash。
封存仅需NumPy+stdlib及既有source解析逻辑，CPU，无网络/GPU/模型/训练。
PASS为所有不可变证据匹配且新目录完整可复读；缺证据、任何变更或越界均拒绝，
保留失败目录不覆盖原物。已有接受的点云不重复导出或验收。

配置状态固定`REVIEWED_SCENE_ROLE_INPUT_FOR_INTEGRATION_ONLY`；training_ready、
full_scene_source_certified、historical_generator_revision_certified、真实native
object observations、GT结构标签输入、生产应用和新点云生成全部false。
保留PARTIAL_COLOR的88,258/144,812无效颜色点，封存不补颜色。不是通用分类器。

作者完整397/397，原371保留、40个旧G2文件逐字节不变。26项新增包含输入
篡改/源资产/真实state/未知项范围/固定authority/替身路径/认证提升/schema/
第二帧独立archive/冲突/输出隔离等负控。初次夹具geomID错误日志原样保留，
不作为候选缺陷。另Agent只读复核的P1/P2均关闭；无私有数据独立验收。

固定发布SHA=`54541c315ad13077b5b4b7f3d81d01138b8931d8`，tree=`e0aec27feb101b41a4afa72dde752199f0cb3531`。服务器新隔离检出43/43 G2 blob精确一致，两套真实package+verify均通过，原角色映射字节未变。

私有封存根和日志位置仅在服务器原位记录，不向GitHub公开；role-map及所有逐部件证据仅原位存在；仓库只存`server_release_aggregate.json`的计数/哈希。Layout1 release SHA=`36feac43894214e2eae9cb82ed3df0e313f0a62044bca0dba67f5ebfe79ba0f7`，Layout10=`3620f92a7c755d489e65b21f09ec00c5a7294c8312e2bee809b55cadd4439f17`。原目录已存在，不得覆盖；GPT独立验证使用固定源或原位只读verify，完整397回归及所有外部来源/state均须再核，不重复已批准的点云/分类人眼验收。后续ledger回执不替代固定实现SHA。
本次只为独立集成生成配置，GPT仍须验收封装。随后继续nav_sg#8正常结构、
原生主程序和对象关系，六图/Island由GPT从真实snapshot生成后交用户。
不在PSM-WMA编写房间分割，不合并、不建PR、不启动Cosmos或GPU。
