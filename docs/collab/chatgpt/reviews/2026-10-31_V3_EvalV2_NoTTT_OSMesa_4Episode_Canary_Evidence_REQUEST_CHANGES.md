# PSM-WMA V3 EvalV2 — No-TTT / CPU OSMesa 4-Episode Canary 新运行证据审核

- 日期：2026-10-31（CST）；角色：ChatGPT 独立 Evidence / Gate reviewer。
- **报告绑定的 Formal Root implementation：`d18b420c02cfc51a1b85e9f1d6ce5d26f7bd3163`**；
- **Formal Child/Gitlink：`2f7334c4ada6ace1d21185985aae90539052bf18`**，在 exact Root GitTree 重新验证；源代码 Pair 与先前双模式 `APPROVE_CODE` 相同，**不重复技术代码审核**。
- 当前远端 `origin/V3`（审核时 HEAD `1f79c41aa40a992a03631c8ff3c34ad1b04efd68`）的 child gitlink 是 `0ae313e329d290fc6b8a50fda1112820fb7ac485`，**不是本次候选的 exact child**；latest V3 / 本记录 HEAD 不是 Formal implementation，不能取代 DS formal checkout。
- 输入：Owner 直接粘贴的 DS_PRO 《EvalV2 Phase B GPU Canary 结果报告（CPU OSMesa 渲染 / No-TTT）》；DS本地目录 `/tmp/ds_pro_canary_dual_no_ttt_20261030/{out,evidence}/`、预热缓存 `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/caches/warmed_numba_osmesa/`。
- **真实 Evidence Gate verdict：`REQUEST_CHANGES`（仅新增运行证据和可重复运行条件；不撤回原双模式源码 Code Gate）**。
- **工作结论**：DS报告的 No-TTT OSMesa 4集机制指标“reported pass”，Owner已接受 `B2=2/244` 且选择 OSMesa；但本审核未取得原始输出、Numba注入脚本/缓存字节和生成视频文件，故**无法独立关闭正式 Evidence Gate，亦不能将此直接升级为正式900资格**。本结论不要求为提升 B2 命中率而重跑或调整合批窗口。

## 1. DS 报告可直接确认的内部一致性与验收范围

DS报告：`status=complete`、`results_qualified=true`、`clean_execution=true`、`fresh_EXIT=0`；2个任务各2 Episode，4/4 valid，**4个行为失败 / SR=0**（**不等于4/4策略成功**），4个rollout MP4，GPU7显存约10GB且无OOM，NoTTT checkpoint `iter_000011000`，`local_memory_mode=off`，2 Sim/1 Server、B2上限2、seed0/30 denoise steps。
- 报告中的 `244 batch`、`242×B1+2×B2` = **246个模型预测请求**，与两任务2集共约246次replan的量级相符；**B2实际命中率2/244≈0.82%**，Owner已明确接受该最小机制验收结果。只代表“合批机制至少生效过”，不代表Batch吞吐加速显著。
- DS报告 `render+compose` avg7.2ms、p95 8.7ms，`env.step` avg约468ms/p95约514ms；**这不能证明完整OSMesa渲染不是瓶颈**。Child `cosmos_framework/simulation/robocasa/closed_loop_eval.py:407` 的 `env.step` 本身可能触发物理/多相机渲染；外层 `compose` 的7ms并不覆盖内部成本。Owner已认可**实际评测吞吐**，这不是请求重跑的性能 blocker，报告需将“render不是瓶颈”收敛为“外部compose开销小、完整env.step较慢、分项归因未完成”。
- 本次 checkpoint 是 `iter_000011000`，不是先前Owner准备保存的 `iter_000012200`，因此测试仅证明iter11000在该配置的运行；不应把这次4EP记作iter12200验证。
- 报告未明确是否与训练在 GPU4–7 上同期运行。此前Owner已准备暂停训练空出4–7，因此不应自动把“GPU7 Server与Sim共用机器”提升为“**与GPU训练并行的压力测试PASS**”。
- **本轮真实事故材料均为 DS_REPORTED**：远程设备离线；GPT当前容器中上述`/tmp`及`/mnt/data/shenzhen`路径不存在，亦未在当前对话上传文件原件。报告内部一致性及精确源码逻辑不等于完整日志和文件哈希的独立复核。

## 2. 增量 Finding — E6-P1 HIGH（正式长跑复现/运行信任链）

- **位置**：Root `scripts/eval_robocasa_18task_queue.py:271-280`（覆盖缓存环境）；Root `scripts/robocasa_eval_v2/identity.py:103-113`（每个新Run私有`NUMBA_CACHE_DIR`）；Child `cosmos_framework/evaluation/robocasa_v2/store.py:259-269`（`.run.lock`创建时序）。
- **根因**：为了规避DS报告的OSMesa/libLLVM与Numba JIT冲突，实际运行依赖第三方脚本在`store.create()`生成`_internal/.run.lock`后，**异步把`_internal/cache/numba`替换为外部持久预热缓存的symlink**；这份非正式代码/缓存是成功运行的关键条件，却没有作为已验证的Runtime身份或可复放的、启动前原子依赖记录。首次sim import与外部注入存在竞争；缓存因Numba/CPU能力/源码/环境变动失效，会重新触发JIT及潜在的原生崩溃。
- **额外安全约束**：Numba官方文档说明`.nbi/.nbc`从pickle反序列化；目录必须是可信且权限受控。DS只列出了8个`.nbc`文件（936K），没有公开完整`.nbi`目录索引和文件权限/哈希，不能证明下一次能命中缓存，也不能默认将logs备用目录视为可信。参阅`https://numba.readthedocs.io/en/latest/developer/caching.html`。
- **违反的验收边界**：4EP Gate可接受手动临时验证，但正式长跑要求`clean exact Source+Run`与所有运行关键依赖**确定、可核验、可复用**；不能把未登记外部cache+竞态注入当作已批准的生产运行机制。
- **验收条件**：保存原始`inject_numba_cache.sh`、`run_eval.sh`、完整`.nbi/.nbc`缓存、逐文件sha256、owner/permission、Numba/llvmlite/LLVM/libOSMesa版本与实际`LD_LIBRARY_PATH`/运行时cache-hit日志；确认下次实际需要的签名都命中，且无动态JIT；将缓存部署改为**启动Sim之前可验证、无后台race的确定性步骤**（最小runner/runtime改动即可，非全链重构）。如果需改生产源码，必须形成新Formal Pair并窄增量Code Gate；当前报告中一次成功并不足以批准900。

## 3. 增量 Finding — E6-P2 MEDIUM（后端/依赖未进入冻结评测身份）

- **位置**：Root `scripts/robocasa_eval_v2/config.py:10-43,77-80`（没有renderer/backend字段）；`scripts/eval_robocasa_18task_queue.py:271-275`（继承`MUJOCO_GL`）；`scripts/robocasa_eval_v2/identity.py:162-189`（runtime identity/manifest仅锁vendor/library/model/source等，未绑定`MUJOCO_GL`、libOSMesa具体构建与预热缓存标识）。
- **根因**：同一个checkpoint/config、同一Root/Child可用不同外部环境变量在OSMesa/EGL间切换，也可能改变`LD_LIBRARY_PATH`和所加载的OSMesa/LLVM而不触发Manifest/Resume身份失配。视觉观测和计算路径可能改变，属于科学协议的未记录变化。
- **验收条件**：在4EP归档补交实际选用backend/依赖版本与校验和、单独不可篡改Run环境记录；在正式900前，以最小范围将`render backend`及其关键二进制/依赖与缓存身份绑定到不可变运行配置/Manifest并使Resume模式漂移fail-closed（如改源码须新技术Gate）。不要求构造大型新资源框架。

## 4. 增量 Finding — E6-P3 HIGH Evidence-only（权威原件尚未交付）

- **位置**：DS报告 `/tmp/ds_pro_canary_dual_no_ttt_20261030/out/{summary.json,episodes.jsonl,manifest.json,logs/...}`、`evidence/{fresh.log,fresh_osmesa_launch.out,numba_inject.log}`、`canary_phase_b.yaml`、`run_eval.sh`、`inject_numba_cache.sh`，以及4个`result.json`和rollout MP4。
- **根因**：只收到转述，不存在可供GPT独立逐字节核对的summary/manifest/Batch Histogram/Session End与原生MP4，且上传的运行依赖与重启路径不可直接复核。
- **违反的验收边界**：独立Evidence Gate的`contract → behavior → original evidence`要求；不能以DS文字结论替代原始证明。
- **验收条件**：只读归档上列运行文件及SHA256清单，清楚绑定exact Formal Root/Child、`iter11000`模型hash、运行环境；视频至少附`ffprobe`时长/帧数和文件sha256；server Batch Histogram应来自实际成功提交的native model batch、两个Sim的真实Session/register/End/cleanup及 process registry/owned-only exits要可核验；确认结果码及4个valid Core没有伪造/遗漏。只要原件存在，**无需为了归档和复核而重跑4Episode**。

## 5. 额外说明 / Scope

- 公开同类缺陷旁证：`https://github.com/conda-forge/llvmlite-feedstock/issues/99`讨论动态链接不同LLVM构建导致llvmlite segfault；但不是本机`libLLVM20.1`与OSMesa冲突的独立根因证明。DS原生最小复现仍需带调用栈日志。
- **Code Gate**：此前双模式 `APPROVE_CODE` 保持，formal Pair未变，不重复Code review；此轮E6-P2系新的OSMesa使用情境暴露的协议风险，不能写成旧源码整个范围被拒。
- **Functional Canary**：据DS汇报，4有效/4行为失败、两个B2真实提交、MP4、exit0，操作层初步可认为`DS_REPORTED_PASS`；Owner对2/244的接受决定照办，不要求扩充合批窗口。
- **Formal Real Evidence Gate verdict**：`REQUEST_CHANGES`，当前唯一授权是补原始Evidence和冻结所需运行依赖；待独立复核后再判Gate closure。
- **Formal900/LocalTTT GPU**：均**未因此获批**；NoTTT模式4EP不能替代LocalTTT自己的真实 Canary，也不能替代与GPU训练并行的压力测试。
