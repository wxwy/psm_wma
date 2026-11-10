# Issue #35 — EGL 环境阻塞解除与真实输入补采：GPT 独立 Evidence 核验

**日期**：2026-11-10。**Formal implementation pair 未变**：Root `18be4a80a5ae4d97bc7d287034d24efab847c496` / Child+Gitlink `193627f42f4cd1ba6d563aefb8fa8f9428ecb56d`。
**Verdict**：`EGL_ENV_BLOCKER_CLOSED / REAL_INPUT_CAPTURE_PASS / NUMERICAL_REPLAY_PENDING`。这是新 Evidence 审核，不重复审核未改变的 Stage2 代码，也不授权V3合并。

## 1. 已独立复现并解决 EGL 阻塞

- Codex 原普通身份 uid1004/gid1004 访问GPU4 `/dev/dri/renderD132`（root:render、gid993、mode0660）被拒绝。原生EGL枚举8个device，但PCI可证实数0/8、`configure()` BLOCKED。
- 此账号本已列入 `getent group render`。GPT 使用 `sg render -c` 创建临时执行身份 gid993（不提权、不chmod、不改组、不绕过设备校验），原生 `egl_probe.py` 立即得到PCI可证实8/8、`MAPPING_PASS_NO_CONTEXT`、GPU4 EGL index4。
- 旧GPT成功的真实RoboCasa评测亦采用 `sg render`。按相同执行方式启动Codex现成的外部录制脚本，真实Policy/共享VAE/Sim/原生EGL皆成功运行。
- 原Codex报告的 BLOCKED 状态是当时真实情况，保留历史记录；此处只关闭**执行环境权限阻塞**。

## 2. 真实完整输入补采成功（短诊断，不是SR）

服务器私有目录：`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/issue35_render_group_capture_20261110/`。

- 运行原外部 `capture_driver.py`、`capture_entry.py` 与 `hooks/`，没有修改脚本或生产源码；保留原始Root/Child/Gitlink、DCP/mode、物理EGL Guard和startup-helper SHA验证。1Server×1Sim、Policy GPU6/Sim+VAE GPU4、CloseFridge seed4603。
- **K=1**：`capture_ready.json` 确认 source_step `[0,16,32]`，原本需要排查的32已冻结。
- **K=16**：确认source_step `[0,16,32,48,64]`，目标64已冻结。
- 每次请求均留有 `request_NNNN.pt`、`prepared_NNNN.pt`、`outputs_NNNN.pt`，**8组×3=24/24 PT 文件存在**。请求覆盖实际Batch、candidate/previous FastRecord、完整FastState、4×32 Prefix、四类RNG状态、输出动作；经服务器端独立读取确认K1 source32的前后FastRecord及Prefix张量真实存在。
- 录制到目标请求后主动对本诊断原生协调器发 SIGINT。因此原生Episode状态为partial/invalid、协调器exit1，**不能当作评测失败或成功**。外层采集驱动exit0、`capture_result.json` 状态 `CAPTURE_COMPLETE_NOT_SR`。
- K1和K16分别3/3个owned进程关闭回执；独立核查无残留Policy/Sim/VAE、GPU4–7显存全为0MiB，GPU0–3任务未动。无capture_error、无unsupported_parent。
- 完整24个PT的size+SHA256独立收据保留在**服务器本地** `independent_receipt.json`，收据SHA256：`bfacf5dbf329f5b3f11254629425b74772f6b94b2748c9cdb624fb26fb354574`。未向GitHub/ChatGPT外传真实输入、图像、FastState、Prefix或原始trace。

## 3. 原有Attention trace 独立计算

- 独立再次运行Codex `reduce_existing_trace.py`，读取Stage2的原始单次 H100 profiler；原数据及SHAs与作者一致。
- PackON：**causal Flash kernel28次（GPU sum0.277605ms）、GEN 840次（11.958062ms）、varlen prepare 868次（2.771284ms）**。
- 812是28层×29次的源码缓存命中路径，不等于812个额外causal GPU kernel；源分支可能被编译器消除。单次Profiler的CPU inclusive、GPU kernels和墙钟不能叠加，不能推导能省多少ms。**不批准盲目删dummy causal或重写Attention**。

## 4. 当前应执行的唯一下一步

真实快照已经可用：K1 request_0032、K16 request_0064。Codex应在同一Local iter15000 checkpoint、同一冻结完整Batch/Prefix/FastState/RNG/噪声步下，分开比较：

1. 原始Local Prefix推理：`use_prefix_text_kv_cache=False`、`use_prefix_pack_templates=False`。
2. Stage1文本KV：`True/False`。
3. Stage2文本KV+Pack：`True/True`。

分别确认完整Vision/Action输出是否精确或容差一致，以及首次不同张量/编译边界。之前真实Episode开始分叉（K1 replan2、K16 replan4）并不足以证明缓存Bug；相同RGB/FW范数也不足以证明完整输入相同。**仅当确定数值归因或性能瓶颈，才考虑新的最小生产补丁；不重跑No-TTT。**

## 5. 正式边界

**`CAPTURE_EVIDENCE_PASS`，但 `REAL_INPUT_NUMERICAL_PARITY_PENDING`。** Formal pair未变，不重新做代码审核；现有Draft不自动合并V3，不关闭Issue35，不宣布SR、生产SLA或Attention优化完成。