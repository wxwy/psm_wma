# Issue #58 / Draft PR #62 — GPT 独立固定源码审核（2026-11-17）

**正式技术结论：CPU_CODE_GATE_PASS + REAL_CACHED_F27_A2_GC_PASS；新 PR #62 的真实 F27＋Wan 并行/资源 A/B Gate 为 BLOCKED_RESOURCE，暂不批准9,126全量启动。**

## 固定版本和范围

- Root 实现：`a3e0048b40e1392d0ff92d4fce8da4dc278447f6`；Child Gitlink：`d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`，实际隔离工作树一致。
- nav_sg 当前：`70eb7b447e65d793b0ebe18b258291ce46f057c1`；生产 V3 未修改。
- PR #62 叠加既有 Draft #55（base `29f9993d2543b8bb638f135aac9dd7172b71baf0`），#53/#55/Child原VAE B1核心未改；提交该文档不替代上述 Root。
- 现有 `psm_wma/cosmos-framework/.venv/bin/python`，Python3.13.11、Torch2.10.0+cu128、NumPy2.2.5、PyArrow21.0.0、MuJoCo3.3.1、Pandas2.2.3、Ruff0.12.7。未新建环境/安装依赖/停外部进程/启动训练/删除原视图。
- 源码独立检出：`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_issue58_review_a3e0048b_20261117/source`，Git Root/Child受版本管理的文件验收后保持 clean。

## 1. 全部 CPU+故障恢复回归：500/500通过，0skip

在上述固定Root/Child和已有解释器运行作者原样 `docs/collab/codex/evidence/2026-11-17_issue58/commands.sh`，结果：

| 独立组 | PASS | FAIL/ERROR/SKIP |
|---|---:|---|
| #53 原始 VAE 缓存 | 283 | 0 |
| Stage A 既有链路 | 150 | 0 |
| Producer/marker/viewer | 45 | 0 |
| Issue58 One-shot/ledger/work/Supervisor新增 | 22 | 0 |
| **合计** | **500** | **0** |

作者本地原13个因PyArrow/MuJoCo/Pandas依赖缺失的Skip均已在服务器真正通过。原478个测试身份保留（CPU gate标记true）；固定作用域222个源码指纹稳定。Ruff/format/bash/help检查全部通过。

既有GPT A1独立三条RED→GREEN反例及Codex peer的一条队列分发独立探针，另行执行**4/4PASS**，与500项不重复计数。

SQLite 101,101条**模拟ACK**／1,001 jobs同一次CPU测试确实执行，活动工作集上限128、峰值101个events／1个job；最终DB1,163,264 bytes。这只证明ledger归档/容量，不是GPU吞吐。

## 2. 实际完成的真实F27/Wan数据归档验证：2条、169个原始owner记录

为审计P0新 `g2_final_pixel_spool_v3` 完成回执/清理，在全新隔离目录复制**此前经真实Wan2.2 encode、完成严格B1数值验收的**两条真实F27 cache数据：

- `CloseBlenderLid/000000`：37状态，89条真实owner，源与VAE cache完整可校验。
- `CloseFridge/000502`：44状态、8视图（含Island4），80条真实owner，源与VAE cache完整可校验。

对复制体独立使用PR62自身 `EventSpool` 注册、`producer_work` managed lease、`offer_source`、`adopt_completed`、严格 `validate_profile_episode/verify_episode` 和最终cleanup；验证来源文件/完整VAE文件SHA在归档前后不变，真实copy未被修改、只删除独立测试work；每条归档后active_records=0，完结后completed_jobs=2/active_jobs=0/failed_jobs=0。相同来源注册幂等、修改source_fingerprint的跨源注册被拒绝。两条真实缓存169条记录均受到检查。

**严格范围：本项是“真实已完成F27/Wan缓存输入→新版P0回执/GC/受控临时清理”测试；本轮没有重新编码Wan、没有在PR62真实监督器下同步渲染，不能伪称已通过新F27+Wan GPU Gate。**

## 3. 新PR62真实GPU预检结果：BLOCKED_RESOURCE，未绕过

创建只属于验收的两episode sample配置（sample=true, IDs0/502，renderer物理GPU6×1，Wan消费者物理GPU7），固定映射SHA `aa884820494a17f50b41a8a8c2bfa6b6fda11babbbef31c449c1c0ce850e09ed`，校验Root/Child/nav、同模型B1 recipe与原NumPy。执行正式仓库 `tools.g2.run_stage_a_production preflight` 而非服务器自定义入口：

1. 新固定检出未自带未提交的F27 C++预编译 `g2/bin/libfast_surface_cells.so`，首次preflight如设计拒绝。审核仅运行代码仓自带 `bash g2/offline/build_native_raster.sh` 编译生成隔离目录.so，记录源码SHA `dec6adb711a7d200ec78cc7ee37956327d7eef68321bb2d483679dce5effef0e`、二进制SHA `20784e6d5fba4538a963060e34babc54ac424625a4262f5c9af6b52db7a56255`，无新依赖/无源码修改。
2. 重新preflight，环境与source都通过，到GPU所有权处按合同报：`selected GPUs have unowned processes; stop them manually before launch: [3594807,3594808]`。核对nvidia-smi：GPU4/5/6/7均有非本轮常驻进程 `3594805..3594808`，每卡约36,968MiB。**它们仍各有约44GiB空闲，阻断是“禁止与未归属进程共用GPU”的显式策略，不是已证明显存不够。**没有停掉外部进程，更没有放宽检查、使用GPU或声称实际并行A/B PASS。

**因此新 one-shot Supervisor 的真实 F27+Wan 同步/停止/恢复/多renderer/资源峰值 A/B 仍是 NOT_RUN/BLOCKED_RESOURCE。**前轮Draft#55已测过B1同卡真实F27与Wan重叠（89/89 ACK/完整），但那不能替代本次修改了的监督器/GC实际GPU验收。

## 4. 源码审查与剩余Gate

本轮源码审阅确认：
- `EventSpool.enqueue` 仍有限max_events/max_spool_bytes/max_result_bytes与活动ledger max_records，而归档 `completed` 永久回执+SQL delete只作用于 source/profile/cache严格发布后的ACK。不会按累积100,000条拒绝整个9,126队列。
- `work_lifecycle.producer_work/cleanup_registered_work` 以同身份租约、renderer锁、target锁与带fsync的rename/deletion intent处理成功episode；中断/未封存/非法或跨根工作目录禁止清理。
- `full_production` 使用单个原计划、原统一生产队列；独立B1常驻Wan消费者；成功episode完成前不会记full COMPLETE，安全停止/恢复、监控/资源背压均有对应CPU测试。
- 只在仓库路径 `scripts/g2/run_stage_a_full.sh` 提供Owner手动生产入口，临时review scripts不属于生产依赖；P1 microbatch推迟、B1编解码及配方不变。

但完整生产许可**仍需要**：①确保审核源码的本地预编译二进制及其签名绑定，②在Owner批准的空闲或明确允许共存的GPU集合上，使用正式仓库 `preflight/run/resume` 做真实F27+Wan样例，尤其测producer完成、VAE ACK、managed work GC、长间隔、崩溃恢复、最终DRain，③相同输入及资源的render-only A/B量化工作目录和spool峰值、CPU/GPU负载、单集延迟，④所有候选生产参数/旧视图删除范围/保留数据冻结与全库磁盘容量计划。无法在严格GPU资源预检阻断下声称通过。

如果现有GPU4-7常驻进程必须继续运行（此前G2可与之共存），Owner/Codex应先定明确共存策略：带最低剩余显存、GPU编号和运行授权的显式sample/full配置，在不停止任一不相关进程的条件下再做真实Gate；否则Owner手动释放被选GPU，然后复验。请勿默认放宽权限或自行结束进程。

服务器独立原始证据目录：
`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_issue58_review_a3e0048b_20261117/evidence/`

- `cpu_original_command/{pr53,stage_a,related,one_shot}.{log,xml},gate.json,sqlite_stress.json`
- `independent_reviewer_probes.{log,xml}`
- `real_f27_cached_gc_probe.py/.log`，`genuine_F27_v3_gc/proof.json`
- `sample_config.json`,`sample_preflight_first.log`,`sample_preflight_native_ready.log`
- `native_build_hashes.txt`

Evidence hashes:
- `cpu_original_command/gate.json` SHA256 `bba379fde7e72f78db244a0e25cd09fa5217cd93e8648d97fa32f0483448ef98`
- `real_f27_cached_gc_probe.log` SHA256 `3f7641a599ab3f3abc710549c410fac1f7b83b8b30e96876700ca2360ba1a764`
- `sample_preflight_native_ready.log` SHA256 `d394a225dc799559176880226d8909134abce2e917aec5799a96d61bb5431137`

**P0代码与CPU/真实缓存回执可以保留；全面生产结论：暂不批准。** 旧6views 67GiB与flat/Depth/G1完全保留，PR62仍Draft、未合并，未运行9,126或训练。
