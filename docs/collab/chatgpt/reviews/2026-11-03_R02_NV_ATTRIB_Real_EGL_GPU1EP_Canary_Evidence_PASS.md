# PSM-WMA V3 — R02 NV_ATTRIB 真实 EGL GPU 1EP Canary 证据审核

**日期：2026-11-03｜Verdict：`R02_1EP_NV_ATTRIB_PASS`（DS_PRO 报告支持；未直接读取本次 GPU 原始产物）**

## 1. 版本身份与审核边界

- 当前正式 V3 基准 Root merge：`ff9110ce7ac3fe2438603a481ef720326e435c0a`；正式 Child/Gitlink `1069fe78841228cadbbfbe6afbd767eaed6225da`。此前 format-only Formal Root `46c08127b2a13155bb22204069a1456cb01424d7` / Child 同上已获 GPT `APPROVE_CODE`、DS 独立 CPU66 `DS_INDEPENDENT_PASS`。
- GPT 本轮直接从 GitHub 读取正式 V3 Root HEAD `01a376b1305c6ce3800de31c64816a88d24b665e`（较合并点仅增加审核文档）、Child HEAD/Gitlink 同上，以及 Child `render_devices.py`、Root `generated_media.py`、`robocasa_vendor.py`、EvalV2 CLI/Runtime。**这些源文件不等于本轮服务器运行原始证据被 GPT 读取。**
- 用户转交 DS_PRO 的《R02 1EP GPU Canary — PASS（NV_ATTRIB 真实 EGL）》（2026-11-03）是本轮实测验收的证据来源。服务器 Remote Desktop Commander 查询原始输出时再次断连；GPT 未读取本轮 `result.json`、`media_summary.json`、20个 MP4/receipts、进程清理日志或 `fresh2.log` 原始文件，**不能称为 GPT 直接复跑/逐条审计**。
- 服务器证据只保留本机；不上传或复制。正式目录 `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3` 中是否已拉取本次审核 docs-only 新 HEAD，不影响此前 Merge 生产代码验收。

## 2. 单 Episode 真实硬件报告

**Run 配置**：R02 Fresh；`CloseFridge` ×1EP，seed0；Phase B `local_memory_mode=required`，GPU6 Action Server、GPU4 EGL Renderer，M1/B1；Checkpoint `iter_000020000`；`save_generated_video=all`。独立新配置 `R02/eval_phase_b_nv_attrib_v2.yaml`（有 asset_manifest），`sg video`→`sg render` + NVIDIA EGL vendor环境；`PYTHONDONTWRITEBYTECODE=1`。

**正式输出**：
`/mnt/data1/data_v2_0617/robocasa_eval_runs/local_ttt_robocasa_raw15/packed128_droid_fresh_g1_20261019/R02_1ep_nv_attrib_v2/`

**本机日志**：`/tmp/r02_1ep_nv_attrib_v2/logs/fresh2.log`、`dry_run.log`。

| Gate | DS_PRO报告结果 | 本轮裁决 |
| --- | --- | --- |
| 物理 EGL | `egl_physical_pci_v1`；`physical_identity_verified=true`；`egl_device_index=4`；GPU4 PCI `0000:98:00.0` 与 expected==actual；Server GPU6 | Report-supported PASS |
| Context | `context_verified=true`；`context_device_handle_verified=true`，匹配枚举设备句柄 | Report-supported PASS |
| Core/SR | success latch，308 steps/20 replans/84.17s，environment_success=true，`summary.status=complete`，`success=1`、`failure/invalid/interrupted/pending=0`，`results_qualified=true`、`clean_execution=true`、`sr=1.0` | Report-supported PASS |
| 媒体 | 20 Replans =20 MP4非空=20 receipts=20 ACK；`media_summary.status=COMPLETE`，`expected=saved=acknowledged=20`，`errors=[]`；另有 rollout.mp4 | Report-supported PASS |
| 运行退出/清理 | `CLI exit=0`，无`last_failure.json`/`cleanup_failure.json`，无残留 owned Action/Simulator/Encoder | Report-supported PASS |

**源码交叉核对**：Child `configure()` 对唯一 PCI 匹配后写入 `egl_physical_pci_v1` 与真实 `MUJOCO_EGL_DEVICE_ID`；`verify_current()` 检查当前 Context 及可用的 handle/PCI/CUDA字段。Root `generated_media.publish()` 检查 Phase B ack-required authority、每 Episode completion 计数、MP4 inventory 与 receipt 文件SHA/identity，生成 `COMPLETE` 才不阻止 CLI exit0。因此报告中的观测与当前代码的主要接受条件一致。

**保留的证据边界**：报告记载 `device_node=/dev/dri/renderD132`，但此前一次独立 probe 曾报告同机 DRM 查询返回 NULL。两次进程/环境/探针不同，不能仅凭文字判断是否矛盾；目前真实 PCI 和 Context proof 的关键字段独立于该可选 node 字符串，**本轮不因此否定 Canary**。如后续查看真实原始 proof，可以只读确认字段来源，不另起全面 GPU 映射工程。

## 3. 首次 vendor probe 失败与缓存风险

- DS报告首次 Fresh 在 **vendor preflight** 因共享 `robocasa_vendor_build_20261023/robosuite` 树内新增 Python3.13 Numba `.nbc/.nbi` 缓存而失败；这些文件据报告由外部进程写入，且与本 Eval 进程树无关。DS清理非 `.pyc` 缓存，并在本次 Run 使用 `PYTHONDONTWRITEBYTECODE=1` 后复验 probe RC0；旧 R02 和历史结果未改。
- 实码证据：Root `scripts/robocasa_vendor.py:audit_source()` 使用 `git ls-files --others` 且**审计 ignored files**；明确只允许有完整源一致性校验的 `__pycache__/*.pyc`，其它未跟踪非approved asset会触发 `untrusted untracked/ignored source`。Numba `.nbc/.nbi` 不在现有安全例外中。该一次失败是真实环境/缓存工况，并非 NV_ATTRIB 生产代码功能失败。
- **非本次 Canary blocker，后续需要窄范围单独排查**：长测前应确保共享 vendor 源树不再被其它进程写入 Numba cache，优先将运行时缓存导向源树外的独立目录；若确需改审计，只允许严格限定生成缓存的位置/格式/对应源，不能简单 blanket-ignore 所有 `.nbc/.nbi`（会降低 vendor 可信源审计约束）。`PYTHONDONTWRITEBYTECODE` 本身只针对 Python bytecode，不能推断必然抑制 Numba cache。
- 不授权 GPT/DS 在生产/共享 vendor tree 中批量删除缓存，也不要求为此重跑已通过的1EP。建议长测 dry-run/预检时关注是否复发，若复发，再安排 Codex最小整改和独立CPU回验。

## 4. Gate 裁决与下一步

- **`R02_1EP_NV_ATTRIB_PASS` / `R02_NV_ATTRIB_REAL_GPU_EVIDENCE=CLOSED_REPORT_SUPPORTED`**：本次正式 GPU1EP 真实 EGL 选卡、Context、Episode、Media 和退出路径，均有 DS 完整报告支持，达到约定验收标准。
- 历史最早 R01 `Fresh exit1/MEDIA_INCOMPLETE` 和旧 R02 `environment_initialization` 失败仍保留，不能改写；它们与新的成功运行分别成证据。
- 不因1EP成功推导18×50任务SR、900EP资源安全、M8/B2真实 Batch或长时间稳定性已证明。**未启动900EP、B2或额外训练。**
- 建议下一动作：由 Owner 决定是否在已验证的 M1/B1、双GPU Server/Renderer 组合下推进900EP；启动前只做独立新输出 namespace、空闲资源、同配置与 vendor 缓存不再污染的有限预检，避免无关架构扩张。900EP 需要另行授权，本审核不代替该授权。

**最终 Verdict：1EP Gate PASS（DS原始报告支持；GPT已核对对应生产源码，但未直接读取服务器运行产物）。**
