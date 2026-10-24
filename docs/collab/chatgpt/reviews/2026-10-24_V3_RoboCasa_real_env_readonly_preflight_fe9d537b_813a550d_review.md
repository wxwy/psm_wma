# V3 RoboCasa 真实环境 Preflight — 独立只读 Evidence Review

日期：2026-10-24（CST）。
**FORMAL VERDICT: `REQUEST_CHANGES` — ONLY GPU/real-run readiness (resource and pending evidence).**
静态资产盘点基本就绪；不是新的生产实现 blocker，不撤销 Design、Production、Fixture 或 DS 独立 CPU 已批准的 Gate。未授权、未执行 Dry-run、完整模型权重读取、Runtime Probe、GPU、RoboCasa reset/step、训练。

## 精确身份和证据来源

- Formal Root `fe9d537b4a5f82c8ea72a4f8ce182fdcefac6790`；Child/Gitlink `813a550dab5d6b5b5e3be90d38bb97527956b4dc`；Owner contract `cc7820bee1a73bd2bb2078cb7f00239944f66d37`。
- 先前 CPU Code/Evidence Gates 已关闭，本次 pair 未变，**不重复技术代码审核**。后续 reviews/inbox bookkeeping SHAs 不是新的 formal target。
- DS_PRO 于2026-10-24给出实际主机只读 Preflight 报告。GPT审核该详细报告并核对 GitHub 中的冻结 Store/CLI、Vendor锁、运行手册；**未直接登录服务器读取其 nvidia-smi、df、stat 或模型文件**。此结论按现场DS报告的证据边界判断。

## 已确认的资产库存（限只读）

- 独立 detached checkout和Child干净；iter_000012000检查点含 `.metadata` + 8个DCP model shards（每个约1.69GB）、trainer/scheduler等历史产物；模型config约15544字节。目录/mtime/size存在≠真实DCP payload SHA相同≠可加载。
- 模拟器venv可import robocasa1.0.1/mujoco3.3.1/PIL12.2.0/imageio2.37.2/imageio-ffmpeg0.6.0；server Python有PyYAML6.0.3；真实Vendor lock及21MB asset manifest存在但还没通过固定source/patch/hash/runtime核验。
- target/atomic恰有18个唯一底层Task metadata；现有4-task×5-run包含20个 `*_episode.json`，并记录原四硬参checkpoint=iter12000、num_steps=30、action_horizon=16、guidance=1.0；该“20”仅为文件数量，未进行真实 Episode/Local/Media/cleanup核验，**不得先声称reused=20**。
- DS报告base_port8900无监听，但端口不被预留；实际GPU使用8/8 util100%，每卡56–58GB/81.5GB已占；`/mnt/data1`约7TB，仅空闲132GB（使用率99%）。

## 当前资源/证据 findings

### HIGH-RES01 — GPU Canary 当前无已划拨空闲GPU
- **位置/证据**：DS 2026-10-24 `nvidia-smi` 资源报告；`docs/eval/robocasa_manual_runbook.md:39-52`，Owner contract首段。
- **根因**：8/8均util100%，没有Owner划拨的空闲卡；剩余约23–25GB显存不等于GPU可安全叠加真实Action Server，不能干扰G1与他人任务。
- **验收**：Owner明确划拨可用GPU并确认进程归属、显存/算力预算，canary前复查资源和端口；不得自行停止任何训练。

### MEDIUM-RES02 — 18×5扩展磁盘未证明足够
- **位置/证据**：DS `df` 空闲132GB；Owner contract§3/§4/§5、Runbook§媒体/浏览导出。
- **根因**：若旧20集均valid，本次90 episodes计划还需70集；`save_generated_video=all` 可能逐replan产生大量MP4，且partial日志、JSONL、导出浏览副本也占空间，当前没有旧20集 `du`/媒体文件分布与本次增长预算。
- **验收**：DS只读测量旧run原始媒体与视频浏览副本、各集大小分布/文件数并建本次媒体策略预算，Owner确认新输出可用空间、额外失败留量和保留缓冲；不删旧Evidence/G1产物。

### MEDIUM-PREFLIGHT03 — 同名历史run `.run.lock` 未核对
- **文件**：`scripts/robocasa_resume_store.py:201-212`。
- **根因**：报告未明确检查原目录 `.run.lock` 的存在/普通文件/symlink安全类型；源码 `_admit` 对已有输出目录缺失锁会 `MISSING_RUN_LOCK` fail-closed。当前不主张该锁实际缺失。
- **Owner contract§4**要求保留原锁的互斥。
- **验收**：DS仅只读核查原 `.run.lock` 类型、当前是否被锁占用（不可创建/替换/重置）；异常单独报告，禁止私自补锁。

## 后续独立 Gate，而非本轮失败项

- **真实DCP身份 / 20历史 Episode是否可复用** 未经验证：后续获得 Owner 单独授权，执行 `--dry-run` 的模型字节SHA+legacy bridge、原始episode/C01/Local/media全部核验。旧20个JSON不能直接计 completed。
- **Vendor/Runtime身份** 也未验证：`scripts/robocasa_vendor.py:135-231` 及 `third_party/robosuite_patches/vendor.lock.json` 还要求 robosuite==1.5.2、numpy==2.2.5、源码补丁、native MuJoCo库、registry horizon；import基础检查不足以通过。新增任务的Dry-run将运行CPU-only Runtime Probe。
- **示例YAML不能直接拿来执行：** `configs/eval/robocasa_g1_iter8900.example.yaml` 实际仍指向iter8900和其它run_name，必须由Owner在源码/训练checkout以外准备准确的iter12000 DCP、原run目录、`resume`、四硬参、tasks=all、media政策及 vendor/asset 路径。
- **CPU Dry-run不依赖空闲GPU**，但会实读约13.5GB DCP shards、审核旧媒体，并且在需新增 Task时CPU探测真实Runtime；应单独授权，不得因为本静态审核完成就自行执行。后续正式Resume admission需要锁外/内两次model payload读。
- 若当前18×5使用旧20+新70，若源/runtime/场景种子不同则仅为便利性合并，禁止称同条件benchmark。真正同条件18×5需另起新namespace。

## 结论和边界

**`REQUEST_CHANGES` 限真实运行资源准备：HIGH-RES01、MEDIUM-RES02、MEDIUM-PREFLIGHT03。**
接受DS只读Inventory阶段资产存在的报告，不认为生产Resume源存在新增 bug。下阶段最小流程：只读补查历史锁、磁盘大小与GPU占用归属；Owner单独授权CPU Dry-run；最后另行分配GPU/磁盘并由Owner手动启动1Task×1Episode新namespace Canary。禁止直接启动GPU/真实RoboCasa、修改训练、清理或覆盖历史、重跑已完成20 Episode。
