# Issue #54 / Draft PR #55 — Stage A A2 独立 CODE＋真实样例验收

日期：2026-11-17。**正式技术结论：APPROVE_CODE ＋ REAL_SAMPLE_FUNCTIONAL_PASS**，仅限固定 A2 实现、CPU 合同与下面明确的服务器小样例。**不是全量生产授权、配置冻结、V3 合并许可或训练准备完成。**

## 1. 版本、隔离执行与批准范围

- Formal Root：`4ad0fe7394cb62c4b5692fecaf6ce52963b8852c`。
- Cosmos Child/Gitlink：`d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`，未改。
- nav_sg G2：`70eb7b447e65d793b0ebe18b258291ce46f057c1`，未改。
- 预检正式 V3：`fe1089fb925d86697bebd9bef18608d9c9eae87b`；服务器既有正式工作树未切换或修改。
- PR #55 叠加未合并 #53；#53 已审核 VAE 核心 `778d1ed8a031429fd857c980fc872d4c85123cd1`。PR #55 保持 Draft、未合并。
- 服务器独立检出 `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_issue54_a2_review_4ad0fe73_20261117/source`，Root/Child 均精确匹配正式 SHA，验收结束 Git worktree clean。
- 只使用已存在的 `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin/python`（Python 3.13.11、Torch 2.10.0+cu128、PyArrow 21、MuJoCo 3.3.1、Ruff 0.12.7），**未创建/安装/升级环境、依赖或驱动**。仅原生 F27 必需时加载已有 Noetic/renderer runtime。其它 GPU/生产/训练进程未停用。
- 所有真实数据、图像、模型和原始日志留在授权服务器。服务器没有 commit/push；本 GitHub 记录只包含报告与派生汇总，无私有资产。

## 2. 独立 CPU、静态与故障反例 Gate

在固定工作树和现有 Python 下，执行作者冻结的 A2 命令：

```bash
cd /mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_issue54_a2_review_4ad0fe73_20261117/source
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD/cosmos-framework:$PWD"
ISSUE54_PYTHON=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin/python \
ISSUE54_RUFF=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin/ruff \
ISSUE54_A2_OUT=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_issue54_a2_review_4ad0fe73_20261117/evidence/independent_cpu \
bash docs/collab/codex/evidence/2026-11-17_issue54_a2/commands.sh
```

| 独立测试 | 结果 |
|---|---:|
| 原 #53 缓存回归 | **283 PASS，0 skip** |
| Stage A（含 A2） | **150 PASS，0 skip** |
| Producer/Marker/Viewer | **45 PASS，0 skip** |
| 合计 | **478 PASS、0 fail、0 error、0 skip** |
| 旧 A1 三个原始 RED→GREEN 反例 | **3 PASS**，单独计数 |
| 作者两项 P2 原始脚本 | **2 PASS**，单独计数 |
| 源码指纹 | **209/209** 与作者固定测试匹配，执行前后稳定 |
| Ruff/format/合成流式及补编码合同 | PASS |

两项 P2 原始脚本分别验证硬退出后未发布数值暂存不冒充完成、事后补编码先完成时消费者可接管，不产生重复编码。批准 #53 VAE 核心、A1 语言/任务规则以及 Child 均保持不变。

CPU 原始证据：`<gate>/evidence/independent_cpu/`、`<gate>/evidence/original_orphan_probe.log`、`original_posthoc_probe.log`、`a1_original_probes.log`。上述数据不把合成 CPU 当真实 GPU 证据。

## 3. 真正 Wan2.2 权重与合成最终图双入口

同一真实 Wan2.2 VAE 权重、单帧 T=1、256×256 等比白底 fit/pad、FP32 逐 View 缓存、H100 GPU6；合成最终图 5 个 owner 记录同时经过 A2 消费与事后 `build_profile`：**5/5 latent 逐元素一致，索引/元数据/最终完成标记一致，最大差异0**。只证明真实模型功能及两入口对照，不代表 native F27。

本轮样例 recipe：`3ee9c48399143866b2a0061f3cee01bff35842228f639380d60602d6402e2fc1`。不同 NumPy/PyTorch 运行版本不得暗中混用同一 sealed recipe。

## 4. 两条真实 RoboCasa native/F27 end-to-end 样例

固定源码经 native MuJoCo GT→nav_sg Room/SG→snapshots→F27→新 Stage-A profile 运行，输出在只属于本验收的 staging 根：

```text
/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_issue54_a2_review_4ad0fe73_20261117/
  real_f27/staging_output/tasks/CloseBlenderLid/episodes/episode_000000/
  real_f27/staging_output/tasks/CloseFridge/episodes/episode_000502/
```

| 独立观察 | CloseBlenderLid/000000 | CloseFridge/000502 |
|---|---:|---:|
| 当前 spatial states | 37/37 | 44/44 |
| 全流程秒数（包含 GT、F27、发布） | **346** | **462** |
| F27 render 秒数 | 165.42 | 215.94 |
| 实际 view 数（含新增 marked top） | **4** | **8**（含 Island 四方向） |
| 最终图片 owner 数 | **89** | **80** |
| 旧新版 RGB 全状态逐像素精确一致 | **111/111** | **308/308** |
| `SPATIAL_SOURCE_READY` | PASS | PASS |
| 未编码时退出 75、没有提前 COMPLETE | PASS | PASS |
| 两份 source 副本：流式补齐／事后补编码 | PASS | PASS |
| 两入口全部 latent `torch.equal` | **89/89** | **80/80** |
| 真实图重编码最大 abs | **0.0** | **0.0** |
| 两份 `vae_cache` 与 `profile COMPLETE` | PASS | PASS |
| 选中少量 View 读取 P95 | **0.526 ms** | **0.514 ms** |

合计 **81 spatial states / 12个有效逻辑View文件 / 169个真实图像 owner 记录**；只编码实际 owner，未变化的逻辑帧使用索引引用。老版带底盘标识的 `floor_top.png` 与新版 `floor_top_w_rbs.png` 在全部状态下逐像素一致；新增 `floor_top.png` 为干净底图、单独维护 owner。Fridge 的四个 Island 方向均完成44状态精确图片对照。

GT TaskEntitySet、当前成员—View 双向索引、当前状态选择、语言原文和可信增强事实、投影/几何和独立状态身份均通过新 profile validator。Blender 本体与独立 BlenderLid 同时绑定。

实际图片人眼对照链接（本地 18765 服务；用户先前旧VAE重建人眼PASS不被重开）：

- http://127.0.0.1:18765/g2_a2_real_f27_4ad0fe73_20261117/index.html
- http://127.0.0.1:18765/g2_a2_real_fridge_4ad0fe73_20261117/index.html

## 5. 真实同步并行 F27＋独立 Wan 消费者

额外使用**原已生成的 Blender 原生 GT snapshots**，仅重跑一份新的 F27 渲染，同时在同一物理 GPU6 的独立 Python 进程上启动实际 `EventConsumer`。新版素材写新的源/render/spool/目标目录，不覆盖早先两份结果。

原生 F27 实际渲染阶段结束时，**89/89 个有效图像版本都已被消费者持久 ACK**：证明事件真正在渲染进行过程中被消费。随后 pack 并 seal source，消费者核验并发布 COMPLETE。

| 此单样例量测 | 结果 |
|---|---:|
| renderer 启动到结束（含启动消费者约3s） | **163.405s** |
| renderer 结束时 ACK | **89/89** |
| source pack + offer source | **17.726s** |
| 测试启动到 profile COMPLETE | **205.183s** |
| spool 最终 pending/unfinished/failed | **0/0/0** |
| 逐View记录与此前同配方补编码 | **89/89 latent完全一致** |
| 全部实际记录再次真 Wan reencode | **89/89 PASS，maxabs0** |
| 双方源身份 | **不同且各自正确绑定**；不能错误强求两个独立渲染的 `source_id` 相等 |

**测试历史与判据澄清：**

1. 首次尝试因 reviewer 为 VAE 消费者误加 V3 runtime 目录，使 NumPy2.2.5→2.5.4，正确触发 recipe mismatch 拒绝，未启动 renderer。保留原始 FAIL，随后使消费者仅使用原本 psm_wma 环境；renderer 使用其已验证的独立运行路径，R2 正常。
2. R2 自定义 reviewer 再额外强制两个独立渲染的 `metadata` 全部相等，因包含不同 `source_id` 而断言失败。检查已证明**所有 View 的 owner 记录、PNG hash、state_records 和全部 89 latent 完全相等**；两次独立封存的来源ID不同是正确 provenance。最终新独立检查要求各自来源验证通过而非跨运行ID相同，89个实际记录重新编码 maxabs0。保留两次 reviewer 错误日志，不作生产代码缺陷。
3. 旧无消费者 F27 单样本记录 165.42s；新163.405s 只作当前非独占GPU下的对照，不宣称统计显著加速，更不能直接外推 32 renderer 并发或全9126性能。额外模型加载、pack、读入等成本需要完整批量测算。

此项是真实 F27 与 Wan **同时间重叠**，不同于第4节“来源封存后 stream refill”；分别记账，不混称同一测试。

## 6. 证据、后续边界与 Verdict

服务器原始证据（私有资产留服务器）：

```text
/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_issue54_a2_review_4ad0fe73_20261117/
  evidence/independent_cpu/{pr53,stage_a,related}.{log,xml}
  evidence/real_wan_a2_parity.log
  evidence/real_f27_wan_a2_parity.log
  evidence/real_f27_fridge_wan_a2_parity.log
  evidence/real_concurrent_blender_master_r2.log
  evidence/real_concurrent_blender_master.log          # initial wrong-env reject
  evidence/real_concurrent_blender_correct_source_boundary.log
  evidence/aggregate_gate.json
  real_f27/evidence/real_f27_fridge_pixel_spatial_audit.json
  real_f27/evidence/real_f27_wan_a2_parity.json
  real_f27/evidence/real_f27_fridge_wan_a2_parity.json
  real_f27/evidence/concurrent_blender_gate_r2_final.json
```

`aggregate_gate.json` SHA256：`192cf9ef494f879228047412bccb002363eff5b38d22bdd758c182cee4c2b315`。全部验证进程已退出，正式 Root/Child/nav 和现有训练进程未改，未生成/安装环境。

**批准范围：A2 CODE、CPU 和两条真实生产样例＋真实编码数值/完成条件；一个真实重叠运行样例功能 PASS。**

**明确未完成：**其余指定两条样例 NavigateKitchen/002104 与 PickPlaceDrawerToCounter/005077 的新 profile F27；多任务/多消费者/多renderer及 H100资源争用的统计性能、长时间崩溃恢复和 spool ledger 轮换预算；9,126全集 source/GT角色/文本/view cache覆盖；增强语言模板与完整生产 image size/dtype/batch/硬盘预算冻结；新版本 staging 完成及发布；随后才是单独state15与联合对齐。A+B+C都未完成，不得宣称训练输入ready。

PR #55继续 Draft，PR #53仍未合并；**不修改 V3、Child/Gitlink、nav、不启动全量生产或训练**。本次审核报告/派生汇总提交不替代固定正式实现 `4ad0fe73`。
