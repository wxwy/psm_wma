# Issue #63 / PR #64 — 18 类任务、32 并发槽位的独立生产验收

2026-11-17，GPT 独立服务器验收。**结论：Stage A 资源与容量 Gate 务实通过，可以在完成正式代码合并、旧 View 精确清理和最终 preflight 后，由 Owner 手动启动 9,126 条统一队列生产。** 本轮没有自动合并、删除旧数据、运行全库或训练。

## 已验收的固定实现

- PR #64 capsule 正式实现 Root a169fea07016b80b3639646cc9925ac70b6525a8；本次压力/容量核验固定 Root ffc18f52976c0dd7b363207788b63537771d59a5，后者仅增加已验的容量任务计数修复，不改变 Wan/F27 核心。
- Child/Gitlink d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2，nav_sg 70eb7b447e65d793b0ebe18b258291ce46f057c1。
- Canonical RoboCasa vendor asset root 模板修复：83ce555a9bd2e5e064cac24056e64493cf30e25d。服务器 private config 使用此前真实验证的 vendor 根，严格资源、模型配方、源码SHA和数据 mapping preflight 全通过。
- 新固定代码 CPU 回归 555/555 PASS、零失败、零跳过。正式源代码与子模块 Git 受管文件在服务器全程 clean。

## 一、真实并发 Gate：36/36 PASS

- 正式仓库脚本 scripts/g2/run_stage_a_full.sh，sample_mode=true，RoboCasa target-atomic 18 类、每类头两集，共36条真实episode，所有F27原生MuJoCo GT/SG/Room/View/Language+独立Wan2.2 B1、T1、FP32；真正32个不同的 GPU+slot 对均使用过：GPU4/5/6/7各8个槽位。
- 一次启动，原统一生产队列，max_active_jobs=32，GPU7独立常驻Wan B1消费者；所有渲染和 VAE 完结后，官方 run/result.json 确认 phase=DONE、complete=true、selected=36、exit0、wall 1186.159885 秒（19.77分钟）。
- 终态 spool completed_jobs=36、active_jobs=0、active_records=0、pending=0、failed_jobs=0。出现 max_events=32 满队列时保持有限背压、持续ACK与完成/GC；没有重试失败、VAE退出、资源拒绝或数据丢失。
- 峰值 native work 21,370,436,833B=19.9GiB，峰值待消费PNG 8,107,324B=7.73MiB，最终已完成 work 回收。GPU0–3既有训练未停止，GPU4–7结束后归零，程序未安装运行环境，也未改变源码。

## 二、跨18类逐集独立数据 Gate：36/36 PASS

36条都实际生成 v2 source capsule，原体积大的 spatial_source.json 在最终episode内不存在。严格核验 v2 source READY、cache manifest/COMPLETE、SOURCE_RETIREMENT和SQL tombstone、SG、spatial_metadata、task_entities、language、图片/latent来源hash、完成后work清理。

- 18/18任务类别，36/36episode、890个 spatial state、1695条真实 VAE owner（均经缓存/hash/owner映射校验）。
- 旧版同episode View逐像素 RGB 严格对照 4,137/4,137 PASS，旧floor_top对新floor_top_w_rbs。
- 最大 capsule 210,935B <1MiB，36条新v2总逻辑字节 478,865,143B；旧版同36条 268,602,101B。新版包含新增clean Top、语言、空间元数据与真实Wan latent，不再包含重复的native审计JSON。
- 36条本轮未另做1695次真正GPU重复编码；此前同正式B1 recipe的Blender/Fridge 169条真实Wan独立重编码已达到169/169 maxabs0。不能把本轮数值存储验收误写成1695条GPU二次Encode1。

## 三、全库容量 Gate：条件性工程 PASS，runtime监控不能撤销

官方 tools.g2.audit_spatial_capacity 只读旧9,126条全库及新36条完整v2来源：原全库18类、638,440个文件、64.02GiB逻辑/65.13GiB分配；18个类别均有2个同ID新版样例，measured_task_count=18、missing_new_task_samples=[]、all_task_sample_coverage=true。

- 条件性全库下界111,044,338,363B（约103.42GiB），条件性上界132,699,262,302B（约123.59GiB）。
- 真实/data1当前尚有约133GiB空间；**仅当Owner按许可删除旧6views（已分配65.13GiB）后**，估算 available=211,689,906,176B（约197.15GiB），预留8GiB后仍有约65.56GiB额外空间。此评估本轮没有删除原View。
- 程序只读报告返回 STRATIFIED_CANDIDATE_REQUIRES_GPT_APPROVAL、candidate_bound_fits=true、full_production_authorized=false，这是故意不自动授权全库。此项是独立审查方考虑18类2样例+充足余量+disk backpressure/停续机制后的**条件性人工 GO**，不能宣称两样例每类形成所有10种layout与9,126集的数学严格最坏情况上界。

## 四、剩余优化项（不再作为释放阻断）

严格同资源 render-only A/B = NOT_RUN。它是测算性能提升的可选工作；通过真实32槽整条F27/VAE/来源回收闭环与资源证据，我们将它从硬阻断降为后续性能优化，不谎称已通过这个A/B。

用户正式手动生成前，应：
1. 将PR62和PR64中已审查源码、容量计数修复及canonical vendor asset root模板正确纳入正式V3，冻结准确 root/child/nav/mapping SHA；不要使用之前错误的临时脚本。
2. 用代码仓官方脚本先运行 preflight，确认GPU4-7资源所有权、VAE B1/NumPy2.2.5、源路径、work/output/spool容量、32slots配置。
3. Owner精确确认并删除被许可的旧6views目录，再检查data1实际空闲量；**不得删除flat/Depth/G1/checkpoint或其他环境**。
4. Owner亲自 run --manual-start 启动9,126；持续监测output可用空间、VAE待消费、work/spool、completed的真实COMPLETE和失败重试；若原始变体更大导致容量紧张，应让安全阈值拒绝新作业，保留恢复状态，扩容后resume，不直接覆盖旧数据。

PR64仍Draft，不自动merge；本报告不改变正式产品实现源码、VAE数值或旧数据。

## 服务器独立原始证据（仅路径及哈希，未外传原图/模型）

私有 Evidence 根：
/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_issue63_18task_32slot_gate_20261117/

- run/result.json SHA256 93e53e5160e43276ad84753d631473427ba9384daeeaefbfc8bffbfd14c715aa
- evidence/independent_36ep_gate.json SHA256 d06b3e21f23e3f2a02dfcbcff366be536594da11c35550373ffd2db34b7abc30
- evidence/stratified_capacity_36ep.json SHA256 df7056a6fecce0e12163a46843c116ad3b3565e14a62b4ee54515ce20329c116
- evidence/pressure_run.log SHA256 03dc8654ba5bf648a379f5a75e31d4b940f7d08c00e1d9da6c687dbd7eb8da08

**审查结论：工程/容量两项阶段性Gate已务实关闭，推荐用户按顺序手动发布正式Stage A大生产。**
