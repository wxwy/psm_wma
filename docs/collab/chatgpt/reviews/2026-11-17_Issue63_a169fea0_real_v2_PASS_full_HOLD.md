# PSM-WMA G2 — Issue #63 / Draft PR #64 独立审核（2026-11-17）

## 裁决

**APPROVE_CODE_AND_TWO_REAL_V2_SAMPLES_PASS；HOLD_FULL_9126_CAPACITY_STRATA_AND_32_WORKER_RESOURCE_GATE。**

正式新来源协议代码 Root **`a169fea07016b80b3639646cc9925ac70b6525a8`**，Child/Gitlink **`d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`**，nav_sg **`70eb7b447e65d793b0ebe18b258291ce46f057c1`**。这些在授权数据服务器隔离工作树核对，受管文件清洁，V3/Child/nav未修改。

PR #64 后续修正：
- `ffc18f52976c0dd7b363207788b63537771d59a5`：修复容量报告将未观测任务自动插入 defaultdict、导致 `measured_task_count` 由真实2误报18；测试新增断言仅真实分层计数。本次 **555/555 CPU 独立 PASS** 在此修正后的固定提交复跑（零fail、零skip、零error；所有原501身份保留），所有受管Git文件 clean。
- `83ce555a9bd2e5e064cac24056e64493cf30e25d`：修复生产模板的 canonical RoboCasa vendor asset root 和仓库runbook提示。此配置已由 `a169fea0` 正式CLI私有配置真实2集检验；此提交未改算法、VAE和训练读取器。本次报告仅审核资料，绝不能代替以上源码标识。

## 一、源码与独立CPU

- 固定 Root a169 实际服务器：PR53/VAE **283**、Stage A **150**、related **45**、One-shot **23**、Source capsule/retirement **54** → **555/555 PASS**，原作者本地13项依赖skip在此均实际通过。额外复播已发布Codex原独立peer安全探针 **5/5 PASS**（测试范围重叠，不叠加到555）。
- 新 `g2_spatial_source_index_v2` 保留视图owner/state_records、像素哈希和必要最小投影，移除重复 `stage_static/materials/shell` 等渲染审计；保留原始工作源身份但不伪称已删除文件可重新算哈希。源和完结指纹、SQL完整事务、持久recovery journal、reader/writer leases、v1/v2严格分支和有条件审计归档经静态审查和CPU故障点测试。
- 训练 `open_episode_index / ViewReader` 原v1严格读取不降级，新v2只读取签名小索引、按需访问对应 `.pt`，不加载renderer、ROS或Wan权重。所有生产PNG（clean/w_rbs Room/Island）、SG压缩包、每帧 `spatial_metadata`/投影/关系、任务和语言数据完整保留；B1 T1算法/recipe与Child均不变。
- 原始CPU/Gitlog证据分别位于服务器 `.../.g2_issue63_review_a169fea0_20261117/evidence/cpu_independent` 和修复提交 `.../.g2_issue63_review_ffc18f52_20261117/evidence/cpu_independent`。测试输出仅服务器隔离Evidence，受管源码Git clean。

## 二、实际原生F27 + H100 Wan B1 真实数据（非FakeEncoder）

运行官方仓库 `scripts/g2/run_stage_a_full.sh ... preflight/run --manual-start`，仅抽取真实 `CloseBlenderLid/000000` 与 `CloseFridge/000502`（相同raw mapping fingerprint与原录像），F27物理GPU6×1、独立常驻Wan消费者物理GPU7；样例仅两条，不启动9,126全量。

真实运行前遇到模板资产根问题：`/mnt/data1/data_v2_0617/robocasa_repo/robocasa/models/assets` 是指向 `robocasa_vendor_build_20261023` 的软链接，`g2.sim.source_geometry.load_model` 精确解析后**按设计拒绝** `asset escapes approved roots`（两次producer重试失败；原始失败日志保存）。按相同资产SHA/原始source fingerprint，在**另一个全新隔离配置**中显式把 `robocasa_repo` 改为 canonical `/mnt/data1/data_v2_0617/robocasa_vendor_build_20261023/robocasa`，严格Root/Child/nav/recipe/NumPy/GPU preflight PASS；没有放宽symlink安全边界，也未在服务器修改任何受Git管理源码。随后官方2ep Supervisor **exit0, phase DONE, complete=true, selected2, failed0**。

| 真实 episode | States | 有效 Views | VAE owners | 旧生产 View像素对照 | PR62 v1 总量 | Issue63 v2 总量 | 最终capsule |
|---|---:|---:|---:|---:|---:|---:|---:|
| CloseBlenderLid/000000 | 37 | 4 | 89 | 111/111 RGB相同 | 56,915,501B | **23,211,969B (22.137MiB)** | **162,482B (159KiB)** |
| CloseFridge/000502 | 44 | 8（含Island4） | 80 | 308/308 RGB相同 | 58,496,883B | **28,295,447B (26.984MiB)** | **157,666B (154KiB)** |
| **合计** | **81** | **12** | **169** | **419/419 exact** | **115,412,384B** | **51,507,416B** | — |

- 共缩小 **55.4%**。两集 `spatial_source.json` 和旧READY永久文件都**不存在于最终output**；新 `spatial_source_index.json`、`SPATIAL_SOURCE_FINAL_READY.json`、`SOURCE_RETIREMENT.json`、cache v2新manifest/COMPLETE、episode v2 COMPLETE以及SQL tombstone均已真实校验；每条native managed work已回收。
- 独立 private Reviewer 从PR62真实v1的 `ViewReader` 对比PR64 v2的对应 `ViewReader`，**169/169个Tensor逐条数值全相等**；不同source asset根会改变source_id，因而**跨运行 `.pt` 文件整体SHA不是相同（0个同SHA）**，不能说`.pt`文件SHA在两次独立运行间一致。新retirement在其同一v2任务完成前后保留PT payload hash，并成功做真实校验。
- **GPU7 H100上重新加载真实Wan2.2-VAE权重，对v2完成后的169个最终PNG owner独立真正再编码**，`verify_episode(check_source=True,reencoder=WanSingleFrameEncoder)`，**169/169 PASS，max_abs_error=0.0**。总22.921s，其中Blender18.321（含warmup）、Fridge4.599；Torch峰值分配 **5.308GiB**，recipe `3ee9c48399143866b2a0061f3cee01bff35842228f639380d60602d6402e2fc1`。
- 全链总体wall **914.431s**，最后spool `completed_jobs=2, active_jobs=0, active_records=0, pending=0, failed_jobs=0`；工作目录峰值 **1,406,680,845B (~1.31GiB)**；pending PNG峰值 **1,036,052B**；最终spool字节数1,640,571B。真实来源retirement分别耗 **7.211s Blender / 7.693s Fridge**。
- 新旧任务实体/语言文档逐内容相同；部分跨两次真实F27运行的SG和空间元数据文件SHA随 canonical vendor 资产路径引入的 `source_sha256/geometry_version/spatial_metadata_id` 不同，**不能冒称同一次跨源字节一致**。图像419 exact和latent169 exact在严格源哈希绑定下分别确认。
- 独立 official `tools.g2.verify_spatial_source_index`和`tools.g2.verify_spatial_view_vae_cache`在已退休v2 Blender通过。
- 独立 Reviewer 首版算job fingerprint漏target，修复仅在**服务器private evidence脚本**而非受管源码里更正，最终审计通过；原失败日志留存。

原始独立私有证据目录（只在授权服务器）：
`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_issue63_review_a169fea0_20261117/evidence/`

包含 `sample_vendor_assets_config.json`, `sample_vendor_assets_preflight.log`, `real_sample_vendor_assets_run.log`, `sample_vendor_assets/run/result.json`, `independent_v2_real_final_gate.json`, `independent_v2_wan_reencode_169.json`, `independent_v2_real_final_gate.log`, `independent_v2_wan_reencode_169.log`, `old_full_9126_capacity.json`, `stratified_capacity.json`, 初始资产根失败日志；不外传任何用户数据或模型。

服务器原始SHA256：
- `sample_vendor_assets/run/result.json`: `eefaa34388f29b0d09609ca8b09c33a7a5ad974accb519223f9c746a7b93c2a5`
- `independent_v2_real_final_gate.json`: `e991d980264b12be6066ccf65dc26aa6ab9865f3198fa7fe05ff6e0f0e116b68`
- `independent_v2_wan_reencode_169.json`: `7736a5708a318b0d014cb68ccce7f1aa2000c8efbdd644b3d6cc98f59b0dc3c1`
- `real_sample_vendor_assets_run.log`: `267509bdc4057ec5972be5d53ed3b0429b1cc7bf8abfd260852bc2facac0c375`

## 三、全库磁盘容量情景：**HOLD_CAPACITY**（已发现并修复P2报告计数）

官方只读工具确切扫描旧 `robocasa365-target-atomic-6views` **9,126 episodes，18任务，638,440个文件，64.02GiB逻辑字节/65.13GiB已分配块**；各任务平均分布极不均。已测两个新v2任务同ID增量约Blender 7,449,142B，Fridge4,910,631B。用官方容量工具作**假设未来Owner会删除旧View才可释放空间**的场景（实际未删除），`available_bytes=211,689,906,176 B=197.15GiB`，reserve8GiB，公式估算全库条件下界 **106.94GiB**、上界 **126.12GiB**。该数值不是16类缺样本任务的可信最坏情况界，故**不能批准全库**。

审计暴露了新的真实小缺陷：原 `source_capacity.py` 用 `defaultdict` 在构建18类报告时 `deltas[task]` 默默插入16个空任务，使 `measured_task_count=18`（错误），虽已正确标出16类缺失、`verdict=HOLD_CAPACITY`。通过官方GitHub在 **`ffc18f52976c0dd7b363207788b63537771d59a5`** 修复：`task_samples=deltas.get(task,())`，增补实际回归；**全555CPU独立重跑 PASS**。同样用已验真实v2样例、旧版全库做只读容量扫描，结果现在**`measured_task_count=2`、`missing_new_task_samples=16`、upper126.12GiB、candidate_fits=true、`verdict=HOLD_CAPACITY`、`full_production_authorized=false`**，正常 CLI退出75；证据只留 `.../.g2_issue63_review_ffc18f52_20261117/evidence/capacity_fixed.json`。

虽然条件上界在“删旧后197GiB”容量内，但不宜把上界作为真实最坏情况（仅两类有实际新增样例），还需18类均衡真实F27抽样/32worker资源与同条件render-only A/B，加之native/spool临时空间和reserve裕量。**不得以PR64两个真实样例功能PASS直接手动启动9126**。旧6views、raw/Depth、G1缓存均未删除，实际data1可用还只有约132–133GiB。

## 四、明确后续Gate与权限

1. Codex/Owner继续明确18类任务空间容量采样范围，至少要覆盖其他16类；按每类真实独立episode与实际PNG/owner/metadata比例，计算按任务分层的容量。不得暗示两条样例即全部代表。
2. GPT独立验证四卡GPU4–7×8 slots **32 worker**（已测GPU6×1和GPU7 B1实际样例，不代表32 render并发）；同资源render-only A/B，测 VAE backlog/背压、native work/CPU/GPU/输出峰值，验证停止/恢复。原SQL101101模拟ACK/1001job的CPU stress不是GPU吞吐压力证明。
3. 已验证首选的canonical vendor RoboCasa资产根路径已**正式写入PR64模板**，其余宿主机需明确授权自己的真实根路径。模板内Root与mapping仍为占位符，必须在Owner自己的绝对路径私有config里填固定源码SHA/map SHA，禁止使用已失败样例旧配置。
4. 整体Stage A数据准备不是训练READY；state15及G1/G2联合对齐仍未做。PR64仍Draft，未合并；**不删除旧View、运行环境、不启动9126、state15、训练**。

**技术审查裁决：Issue63代码与两例真实F27+Wan来源回收/读取数值全部PASS。全量部署许可：HOLD_CAPACITY_AND_32_WORKER_GATE。**
