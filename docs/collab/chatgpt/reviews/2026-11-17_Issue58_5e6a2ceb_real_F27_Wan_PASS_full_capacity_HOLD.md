# G2 Issue58 PR62 — 独立真实 F27＋Wan 验收、运行环境修复和全量容量 Gate

日期：2026-11-17。**技术结论：Issue58 P0 CODE PASS + TWO-EP REAL SUPERVISOR PASS；正式 9,126 生产仍需磁盘容量与多 worker 性能 Gate。**

## 1. 固定版本、协议与约束

- 正式生产源码 Root：`5e6a2ceb702acd724076692f42ca4fc60380192b`，Child/Gitlink：`d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`；nav_sg：`70eb7b447e65d793b0ebe18b258291ce46f057c1`。全程服务器工作树受管代码 clean。
- PR #62 后续 **test-only** 提交 `9b051d22259534cfff8c7f006cb26520966eb2fb` 和 `e36bc9468eb581685372257b297276cf221232ce`，修复三份独立审核脚本把运行中`dispatch_observed.json`写到仓库证据目录的做法。新脚本只写 pytest `tmp_path`。三份测试独立 **3/3 PASS**，Git 工作树前后干净；原历史 JSON 保留。它们不改变任何生产代码，所以本次真实运行固定仍为 `5e6a2ceb702acd724076692f42ca4fc60380192b`。
- 环境沿用 `psm_wma/cosmos-framework/.venv`：Python3.13.11、Torch2.10.0+cu128、NumPy2.2.5、真实 Wan T=1/B=1 FP32 256×256白底。`psm_wma_v3/.g2_runtime_deps_py313` 仅用于 GT/F27 渲染，提供 MuJoCo3.3.7；Noetic有原生环境。三者都是**被使用的运行组件，不得视为废弃而删除**。
- 运行 CPU Root/Child/nav与正式 V3 未修改、Git未从服务器commit/push、没有删原视图、没有新增Python环境或安装依赖、没有启动9,126全量和训练。

## 2. 生产版本修复

原 fixed `a3e0048b40e1392d0ff92d4fce8da4dc278447f6` 的真实样例在GT生成后被F27严格拒绝：GT worker使用MuJoCo3.3.1，F27子进程从已配置的额外依赖目录使用MuJoCo3.3.7，日志 `actual MuJoCo compiler version differs from source`。两次worker attempt同样失败。使用独立新 RED测试复现，修复正式路径 `g2/offline/full_production.py::Supervisor.worker`，将worker运行时改为 `isolated_env(self.cfg, renderer=True)`，VAE消费者仍严格 `isolated_env(cfg)`。新增`g2/tests/test_one_shot_renderer_environment.py`：**RED→GREEN**。

提交到PR62 Root `5e6a2ceb702acd724076692f42ca4fc60380192b`。隔离独立CPU：#53 **283 PASS**、Stage A **150 PASS**、producer/marker/viewer **45 PASS**、Issue58 one-shot含新回归 **23 PASS**，合计 **501/501 PASS，0fail/error/skip**；Ruff/format/Git diff PASS。无证据标记未通过的数值/资源Gate为PASS。

## 3. 官方仓库入口的真实样例执行（新监督器，不是旧临时脚本）

对固定Root在独立空目录检出，使用仓库自带 `bash g2/offline/build_native_raster.sh` 在该检出编译预构件，不从服务器提交。源码SHA `dec6adb711a7d200ec78cc7ee37956327d7eef68321bb2d483679dce5effef0e`，生成 `g2/bin/libfast_surface_cells.so` SHA `20784e6d5fba4538a963060e34babc54ac424625a4262f5c9af6b52db7a56255`。官方CLI `scripts/g2/run_stage_a_full.sh` `preflight` 校验 Root/Child/nav、native、mapping SHA `aa884820494a17f50b41a8a8c2bfa6b6fda11babbbef31c449c1c0ce850e09ed`、Wan recipe `3ee9c48399143866b2a0061f3cee01bff35842228f639380d60602d6402e2fc1`、原环境NumPy和GPU6/7 0foreign，**PASS**。

使用同一仓库CLI `run --manual-start`，两条真实RoboCasa target-atomic，全新隔离staging，不复用首轮失败工作目录：

- `CloseBlenderLid/000000`，37 spatial states、4有效view、89真实PNG owner、旧图对新版标识/侧图 **111/111 RGB严格像素一致**；89条真实Wan输入全部ACK并发布，受管理stage work清理成功，completed tombstone存在。
- `CloseFridge/000502`，44 spatial states、8有效view（含Island四方向）、80 owner、旧图对新版标识/侧图 **308/308 RGB严格像素一致**；80条真实Wan全部ACK并发布，stage work清理成功。
- 两者都先返回 SOURCE_READY/VAE_PENDING，待独立GPU7消费者结束后才发布正式 COMPLETE；统一队列自动从Blender转到Fridge，没有人工切批。
- 真实跑完 Supervisor **exit0 / phase DONE / complete=true / selected2**，总wall **914.671 s**，最终spool **completed_jobs2、active_jobs0、active_records0、pending0、failed0**。工作目录峰值 `1,406,645,096 bytes`（约1.31GiB），最终工作残留仅393B guard/locks；峰值pending PNG **1,022,125 bytes**，最终spool **1,320,435 bytes**（单两条）。G2 F27阶段 Blender **184.24s**、Fridge **230.67s**。
- 独立 `validate_profile_episode + verify_episode(check_source=True)` 全部PASS，仓库源及旧生产数据 unchanged，两个managed work已回收，归档receipt包含正确 `source_id`。
- **独立第二次真实Wan GPU7**针对最终输出全部169实际PNG owner执行 `verify_episode(check_source=True,reencoder=encoder)`：**169/169 PASS，两个episode最大绝对误差均为0**。两条reencode验证 18.005/4.554 秒（含首次加载差异），CUDA峰值分配5.308GiB。本轮没有启用B>1或改变配方。

审核脚本第一版因为 reviewer 错算job fingerprint（漏了target）而FAIL。保留错误日志；仅在**仓库外证据目录**复制并更正reviewer脚本，第二版 PASS。生产job/完成回执/数据库从未因此改动。

服务器完整原始证据：

```text
/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_issue58_review_5e6a2ceb_20261117/evidence/
  sample_config.json
  preflight.log
  real_sample_run.log
  sample/run/{result.json,progress.json,progress.jsonl,vae_consumer.log}
  sample/spool/completed/*/*.json
  pr62_real_sample_final_gate.json
  real_production_final_audit_r2.log
  real_wan_reencode_169.json
  real_wan_reencode_169.log
```

关键服务器SHA256：

- `sample/run/result.json` `0b4cea4c4d9bf8eca05bef1d2a2d005866e62bb6b1e38b7532e3407bc74cfb8b`
- `pr62_real_sample_final_gate.json` `833467c3650dae7054a5df6020bdd32dc51bd6a4a4320ab19ad9fff93a14f7b7`
- `real_wan_reencode_169.json` `593898dda2287afa3a79c9836c5d5e3d528fb21d22b3fc73d86702464038d913`
- `real_sample_run.log` `60965592c0c83b98d43e5ddae41b33225f2952d7212d01643fa0ed635063529c`

所有真实assets、weight、image和raw日志仅留在授权服务器；仓库记录为汇总而非私有数据复制。

## 4. 全量数据盘容量 Gate（新增明确阻断）

当前服务器空间：`/mnt/data1` 空闲约101GB（约101GiB原表述按df取整），`/mnt/data`约273GB，旧 `robocasa365-target-atomic-6views`约67GB。即使Owner自行删除旧目录，`/mnt/data1`估计仅剩约168GB可用。未经批准不能删除其他资产或自动将输出移到OS根分区（虽然root有额外640GB闲置，OS系统容量不应默认用于长期数据生产）。

真实新样例：Blender最终约56.9 MB、Fridge约58.5 MB，即每ep约55–57 MiB；简单外推9,126可达**约500 GB**，不代表全库真实准确均值，但目前不能以168GB全量运行。**单个`spatial_source.json`**已达Blender **32.302MiB**、Fridge **28.958MiB**，是最大空间成本。

只在内存中试算（**没有改写任何已签名JSON或缓存**）对每个episode的所有JSON做gzip一级压缩：`spatial_source.json`从约29–32MiB→约1.5–1.6MiB，包含所有JSON后两episode分别从56.9/58.5MB降至**约22.9/26.5MB**，约省55–60%。这证明有明显的无损序列化压缩机会；**但现有spatial_source.json路径、SHA和消费者契约仍依赖原明文JSON**，不可生产中直接改压缩格式而不配套源ID/reader/verifier/producer/训练数据加载逻辑并重新验收。按样例压缩后的粗略外推也可能仍超出168GB，需结合旧全量PNG owner分布和有效View统计做容量计划。

**因此阻断剩余正式9,126全量：在得到足够真实持久空间或完成可验证压缩存储并跑容量Gate之前，不建议Owner启动。**这与代码样例Gate通过并不矛盾。

## 5. 尚未完成与批准结论

本轮未进行与此新监督器**严格同资源、同条件**的render-only A/B，未跑GPU4–7×8=32 worker的负载和峰值，未证明整库总时长/IO；旧版与本轮F27单次耗时只能作为参考，不是统计性能结论。旧 View 67GB未经Owner再次主动删除（用户授权可删除但仍需特定清单/操作）；V3/Child/nav未合并或修改，未从本会话启动全库、state15、对齐或训练。

**APPROVE_CODE_AND_TWO_REAL_F27_WAN_SAMPLES**；全量部署 **HOLD_CAPACITY_AND_32_WORKER_RESOURCE_GATE**。P1 Batch>1仍按Owner决定延后，保持B1 exact0。启动脚本已在PR62仓库，非服务器临时launcher。生产代码固定Root`5e6a2ceb702acd724076692f42ca4fc60380192b`；同PR后续测试纯净修正Head`e36bc9468eb581685372257b297276cf221232ce`。正式根版本从未被服务器修改。
