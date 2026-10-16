# GPT → DS_PRO — V3 Packed128 DROID Fresh S0 CPU-only Readiness

**日期：2026-10-17**  
**状态：执行请求（READ-ONLY / NO GPU / NO TRAINING）**。不是 F1/旧B1 重新审核，不是 Model/DCP 数据 load，不是训练授权。  
**使用已经通过 F0/F1 CPU Gate 的精确隔离 formal pair：**
- Root `6ebf8998a7935f2ad690bb547c5db5e5a4322e6d`
- Child/Gitlink `2d128ed5a07601cdd424974f99b67832eafeeb41`
- 分支 `v3-f1-checkpoint-rng-20261016`；其 docs HEAD `ccfd900bc35fcd39ca9953aa7aa55b85398300ad` **不是**正式 implementation Root。 
- 代码必须用 clean detached Worktree，并如实锁 Root/Child/Gitlink。主线 `V3` 仍是旧生产 Gitlink；严禁用它冒充 F1 实现。
- 参考 F1 CPU Closeout：`docs/collab/chatgpt/reviews/2026-10-17_V3_F1_6ebf8998_2d128ed5_EVID03_EVID05_CPU_gate_closeout.md`，verdict `APPROVE_TO_CLOSE` (CPU ONLY)。

**DS权限：**只读核查现有文件/元数据、使用新隔离目录编写小型 Evidence。禁止源代码/测试/GitHub修改；禁止任何GPU/CUDA/torchrun、真实模型权重读入、真实DCP shard load、再hash大DCP、数据全集复检、仿真或训练。禁止清理/移动旧595GB B1 Evidence、原 iter1300 DCP、451GB缓存。已关闭的F0/F1/B0/旧B1实验不得重跑。任何阻塞请直接记录，无自动兜底。

## A. S0-STORE — 真实DCP大小、卷容量、保留方案（可立即开始）

1. **锁定真实旧正式 Index8 DCP 来源：**仅引用已确认 `iter_000001300` 实际 Save Directory + `latest_checkpoint.txt`，检查它指向iter1300，记录该目录所属mount和Path。不要通过全卷盲目搜索。只读取 `stat`/文件目录元数据，**不反序列化DCP、不读/hash shard body**。
2. 汇总原 `iter_000001300/{model,optim,scheduler,trainer,dataloader}`（如适用）各组件实际**文件数量、apparent bytes、allocated bytes、.metadata大小、每rank Local pkl大小**；给总计 `C_old`，明确哪些组件存在、哪些为分布式共享Shard，目录大小不是每rank“4.7GB×8”的默认假定。不要用B1 `rank*.pt` 数值捕获替代真实DCP。可使用 scoped `find ... -type f -printf '%p\t%s\n'` 和 `du -sb / du -sB1`，只枚举 **单个已知旧DCP目录**。
3. 在候选**新** `OUTPUT_ROOT` 的目标持久文件系统上只读 `df -B1` / `df -i`、`stat -f`、mount/fsid、当前可用容量、空间被共享进程使用的变化和目录写许可（仅新测试隔离目录，勿动正式Job）。分别报告`/mnt/data`、`/mnt/data1`、`/`的实际free，不把上次223GB当作当前真值。Quota不确定时标记未证实，不因缺工具就宣布无Quota。
4. 以 `C_old` 作为**旧作业测量值，而非新F1 Fresh DCP真实C**，给出预算：
   - 安全保有最新 + 上一个已完成 + 正在写的第三份，再加日志、评测视频和缓冲，即 `3 × C_est + W`（`W` 显式说明来源；若估值无根据，`STORAGE_UNCERTAIN`）。
   - `save_iter=100,max_iter=30000` 最大产生300个保存点，F1代码本身**没有自动滚动删除策略**；分别估算不清理与有界保留方案。
   - 提出**供Owner批准**的策略：只允许清理未来新Fresh Job中**已完成且非latest/previous/被评测引用/里程碑**的保存，必须在 `complete.v1.json` + latest新指针确认后；若必须移动或删除另行授权。**此轮不可实施任何清理/自动Retention**。
   - 失败的hidden staging和最终orphan也占空间，须计入应急预算；不得静默复用或覆盖。
5. 输出`S0_STORE_PASS/CONDITIONAL/BLOCKED`和**真实容量原始数字**。`STORAGE_PASS` 不能只凭一个旧DCP尺寸自动推断新C；初次正式Fresh100应测新C，再决定Resume500/长训Retention。

## B. S0-CONFIG — 正式Packed128命令和真实CPU预检（不启动）

1. 准备clean detached F1 Worktree。核 `scripts/train_v3_packed128_staged.sh` （已是规范入口）仅调用 `examples/psm_wma_robocasa_corrected_phase5.py`，不调用旧H3F，默认Packed128 `v2_a2_member_packed_slot_major_v1`，T16/B8/GA2/K4/world8，workers0，无full-prefetch，training schedule max30000/warmup500/save100。Index8 当前不能在此入口显式选择，记为**P1兼容事项，不阻塞Packed-only**，绝无OOM后隐式回退。
2. 对新鲜且**不存在**的 `JOB_NAME`+目标`OUTPUT_ROOT`，用**已验收 Index** 和已有DROID/Edge/VAE/source/cache路径做真实 Phase5 `--preflight --phase fresh --formal-execution-until 100 --world-size 8`（不启CUDA模型，**不** `config.validate()`）。**Preflight必须不创建新的Job目录，不读取生产模型/DCP shard，不重建/复验全索引**。已知接受过的Index实例路径为 `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-verified-index-r1`；路径若变化须找到正确已验收现存文件且注明。
3. 独立记录：全resolved配置/配置语义SHA、真正`Config`类型、SafeLocal类目标、`psm_v3_sync_local_v1`、DROID model-only warm start、strict`True`/async`False`/local storage、Layout、raw15/state15、H16/17帧、camera_set/Use_state、Action/Vision loss权重、aux存在的静态条件、precision、optimizer selected FQN规则、LR seed/deterministic/CFG RNG策略、数据身份。生成小型文本摘要/机器可读JSON，不存高敏路径以外的新模型内容。
4. 正式Fresh100及允许的same-job Resume500执行预算不得改变`30000/500/100`真实Scheduler、优化目标与 `training_identity`。Resume500如需不存在的真实DCP，只对**语义config身份**做非破坏性比较，不伪造同Job Checkpoint恢复通过。将此前2rank探针与这次world8 preflight **不同 config digest** 明确区分。
5. **禁止在CPU把 `Config.validate()` 标 PASS**：其实现需8GPU World Comm + `.cuda()`，放到未来有Owner授权的GPU Gate首个硬检查。

## C. S0-SEMANTIC — 复用既有证据的静态/CPU有限风险登记

**不要重审已通过的F1生产代码；只整理S0真值/待GPU证据。** 对以下合同建立 `evidence_ref / covered_by_CPU / requires_GPU / owner_decision`：
- 正确的目标是RoboCasa raw15/state15→action64 valid mask、horizon16、left_wrist和实际env12控制输出的transform/decoder（Simulator ABI要到未来1–2 task短rollout，不能用Loss下降代替）。
- Full128/128与Terminal Partial如 [122,128] 的真实 `n_member/n_window`，Action/Vision/Aux Native loss含有/无Aux和跨rank counts；不要将V2默认Aux/GA盲目改V3。只引用已有已闭CPU合成test/accepted DS B1 consumer witness；未覆盖处列到后续 GPU/CPU scoped gate，不运行全部旧套件。
- Local S0 No Prefix，continued consumer应有前一已提交Evidence/Prefix，Episode/Slot绝不可污染；Local Slow `encoder/core/local2llm/modality_embed` 与 Generation/Action 参数选中及`FSDP`本地shard eligibility，`numel=0` 属于合法空分片，不等于某参数断梯度；`rank0`遥测不是全部8rank。
- 真实 `Config.validate()/NCCL+Gloo`、DROID weights load、8rank Local/Action/Growth Params Grad & optimizer moment非零、CUDA RNG，同Job Save→Resume100→500及实际任务闭环都 **GPU pending**；不得以旧V2 LIBERO或旧B1 iter1300覆盖。

## D. 一个容易遗漏的**训练前GPU Gate选择**（本轮仅收集可行性，不执行）

已确认 F1源码 `corrected_phase5.py:_execution_stop_iteration()` 中：
- `--audit-missing-grads` **仅允许** `--phase fresh --stop-after-iter 3 --job-name bounded_*`。
- 正式 `--formal-execution-until 100` **拒绝与**`--audit-missing-grads`合用。
- 单纯Rank0正式遥测不能代替 **8rank pre-optimizer Local Slow 梯度**证据。

请给Owner一个二选一的准备意见：
- **推荐A：**另立精确授权的`bounded_3step` FSDP8短诊断 + allrank missing-grad报告，承认此诊断会写**独立**iter3 DCP并消耗其空间；其DCP绝不Resume进正式Job；再批准独立Fresh100/Resume500。无需新增代码SHA。
- **替代B：**若Owner坚决只希望两次GPU Job，则须Codex先新增生产正式首3步 allrank e2e hard witness，形成**新实现SHA +新CPU独立Gate**，不能假装目前已支持。
无论选哪个，当前 S0 **都不得启动 GPU**。

## E. 交付、停止

返回一份 `DS_PRO_V3_S0_Packed128_Fresh_readiness_2026-10-17.md` + 小型 `s0_readiness.json`，含：
- 精确Root/Child/Gitlink & clean checkout，所有命令/RC、源、C_old各组件大小和当前3卷容量
- 新Fresh建议Output路径/磁盘安全阈值/Capacity结论和有界Retention建议（**建议，不实施删除**）
- real world8 Phase5只读preflight结果/配置身份、所有必需资产检查、上述 S0 语义风险状态表
- G0 bounded3诊断所需额外DCP空间和下一阶段Gpu最小执行建议
- Blockers：列出 `P0 storage`、`P0 actual GPU validate/Native`，没有Evidence按`BLOCKED`真实归类，不可凭CPU默认为PASS。

禁止修改GitHub源代码/测试/旧证据、禁止 GPU、torchrun、DCP内容装载、Formal Fresh/Resume、旧B1数值实验或全量数据复扫。由GPT下一轮对S0报告做**独立的Readiness/Evidence Gate审核**；F0/F1同SHA技术/CPU verdict都不重审。
