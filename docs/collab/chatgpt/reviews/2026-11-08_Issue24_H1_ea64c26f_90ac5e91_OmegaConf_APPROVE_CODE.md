# Issue24 Stage3A H1 OmegaConf — GPT 独立整改复审

**正式技术结论：`APPROVE_CODE`（仅 H1 narrow CPU/static incremental Gate）**

**H1 HIGH = CLOSED**。上一份报告 `2026-11-08_Issue24_Stage3A_RealWanDCP_ListConfig_REQUEST_CHANGES.md` 所记录的、真实 H100 Policy DCP 加载后在 `worker_constructor_config` 遇到 OmegaConf `ListConfig` 而无法序列化的生产阻塞，已在新 Formal Pair 的代码和独立 CPU 行为证据中关闭。

本结论**不授权**真实 H100 重试、DCP/Wan/B1 数值等价测试、真实 RoboCasa/EGL 1×1、P0 A/B/C、Stage3B B4/B8 Action Path、SR、训练、900EP、V3/Gitlink 合并或切换现有运行/Resume。

审核日期：2026-11-08；角色：独立审核 GPT；实施：Codex。

## 1. 正式受审目标与实际代码增量

| Authority | 完整 SHA |
|---|---|
| 本轮 Root Formal implementation | `ea64c26f7738f2efba5c33c78f18eab475230a61` |
| 本轮 Child & Root Gitlink | `90ac5e91c5919cdb1d228aebd797e40327900981` |
| 上轮 Root CPU Code Gate | `ef82fe02ee73e3c804b83ffbd68c5123c1377fa2` |
| 上轮 Child | `6842b329f71fff8b9813b2d00b83edfc61e3e505` |
| 紧邻本轮 Root 技术提交的 bookkeeping parent | `1882959a9ba88a00f4914a4657c07dc203d573a2` |

- Root PR https://github.com/wxwy/psm_wma/pull/25 仍 Draft；Child PR https://github.com/wxwy/cosmos-framework/pull/7 仍 Draft。本轮 Root PR Head 随 review/evidence 文档增加而变化，**Formal Root 始终仅是 ea64c26f，不是后续 HEAD**。
- GitHub Git Tree `ea64c26f...` 的 Gitlink 真实为 `90ac5e91...`。在授权数据主机单独从 GitHub 重新 clone 并 detached checkout **精确双仓 Formal Pair**，两个 worktree `git status --porcelain` 空。
- **直接增量** Child old6842→new90ac：仅3文件，生产 `cosmos_framework/inference/robocasa_vae_daemon.py`（+40/−4），新增 `cosmos_framework/inference/robocasa_vae_daemon_test.py`，扩展 `cosmos_framework/scripts/robocasa_feature_http_test.py`。Root 以前一轮 ledger `1882959...`→`ea64c26...`：Child Gitlink、`tools/v3/eval_v2_batch_tests/shared_vae_test.py` 新负向/正向及 `SESSION.md`、`TODO.md`。无其它 Root 生产代码变更。
- 正式差异遵守上轮独立 CPU `APPROVE_CODE` 结果只作增量基线，不将旧 SHA 的 verdict 直接继承给新 SHA。

## 2. H1 生产根因与整改正确性

**旧症状** `robocasa_vae_daemon.py:47–66`：真实 `tokenizer.encode_exact_durations` 为 `omegaconf.ListConfig`，未经展开进入 `canonical_json` 抛 `ProtocolError: invalid canonical JSON`；前一轮真实 DCP on H100 GPU6 已复现。这使 C Policy 初始化入口 `loaded_vae_identity` 不可用。

**新代码核对：**

1. Child `robocasa_vae_daemon.py:47–57` 独立 `_plain_config_container`：仅对真实 `ListConfig / DictConfig` 调用 `OmegaConf.to_container(resolve=True,throw_on_missing=True,enum_to_str=False)`，在原 parent context 展开插值，未用 `str()`/忽略字段/自动编造默认值；缺失/不能解析时拒绝。
2. Child `worker_constructor_config:60–102`：先展开实际配置，chunk map 保留真实 str key/正整数且要求原 Wan chunk window 的 `%4==0`，精确 durations 保留顺序与重复/None vs empty，bool/float/str/嵌套非法值 fail closed；其他维度保持正整型，causal 保留 bool；最终仍通过 canonical JSON/strict JSON 原 64KiB 限制。无 VAE/Policy 模型计算修改。
3. Child `loaded_vae_identity:105–168`：`tokenizer_config` 中等价 OmegaConf 的有效参数比较和实际模型 `temporal_window` 都归一化，**模型 state_dict 真实 tensor hash、scale hash、模型 class、encoder dtype/backend/Config hash 仍来自实际 Loaded 模型**。不同配置/权重仍导致不同签名/拒绝。
4. Child 新 tests 实用真实 OmegaConf2.3.0 ListConfig/DictConfig，验证原生字节与 Identity 相等、父上下文插值、类型/缺失/超大/None/empty、变值哈希/拒绝、Worker loader 的 Python constructor kwargs 与 C Policy入口；Root 相关测试以真实 helper 增加 `omega_constructor` 变体。无再设计 Worker / 原有事务更改。

## 3. 作者原始 Evidence（验证而非直接继承）

作者 handoff（Root docs-only successor `406175e3e3a688aeda2313697cbb2d8e24bff5fe`）：
`docs/collab/codex/reviews/2026-11-08_Issue24_H1_OmegaConf_ea64c26f_90ac5e91_Incremental_Code_Review_Request.md`。

证据：`docs/collab/codex/evidence/2026-11-08_issue24_stage3a_h1_omegaconf/`。

| author-02 JUnit suite | XML tests | actual <testcase> | errors/fail/skips |
|---|---:|---:|---:|
| Stage3 focused incl H1 | 607 | 400 | 0/0/0 |
| Root lifecycle/config | 153 | 153 | 0/0/0 |
| A/B legacy protection | 143 | 143 | 0/0/0 |
| **合计** | **903**（含207 subtests）| **696** | **0/0/0** |

原始 gate Shell0、Ruff changed 4 Python files PASS、`source_unchanged=true`；旧生产代码与新注入的相同 H1 tests RED 2 项（前一版正式源码未被更改，Red Worktree因测试注入不 clean）；作者首轮的日志解析器失败未运行 pytest、第二轮只修改外部 parser 并重跑。未误把失败轮次计作通过。原生配置字节/哈希的作者对照与我们独立结果一致。

## 4. GPT 独立复验（非作者环境、没有 GPU）

实际从 GitHub 分离检出 Root ea64 / Child90ac；在授权 `data` CPU-only `CUDA_VISIBLE_DEVICES=''`，Python3.13.11 / torch2.10.0+cu128（只用 CPU）/ Ruff0.12.7，使用独立清洁证据目录：

`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/issue24_h1_omegaconf_independent_cpu_20261108/independent_h1_cpu/`

- **真正执行**新 daemon、C Policy HTTP、旧 Worker、Root shared VAE 4 份聚焦 pytest 文件：独立 `231 passed`，JUnit `tests=231,failures=0,errors=0,skipped=0`；不是作者696项的伪独立复验。
- 新增 Reviewer-controlled **完全分离 old Child6842 native、old Child6842 OmegaConf、new Child90ac native、new Child90ac OmegaConf 4 个 Python 进程**，直接调用这些 SHA 的实际 `worker_constructor_config` 与 `loaded_vae_identity`，冻结同一 BF16 CPU tensor state：
  - old-native：PASS，旧合规 canonical bytes/hash；
  - old-Omega：预期 `ProtocolError: invalid canonical JSON` RED；
  - new-native：PASS 与 old-native `canonical_constructor bytes` **精确相同**、全部 VAE identity fields **精确相同**；
  - new-Omega：PASS 与 old-native / new-native **canonical bytes + VAE identity 全部逐字节相同**。
  - 独立 constructor SHA256：`3b18d66495ab097bc8960f2eedf874e76cb5e1a285da56177d4f874acc6d3f99`；该 CPU synthetic 模型的 config hash `5a3f01c683dbc9e3f6c07775456391ea4df807daf799538fecea0ee273911a7f`；这**不是实际生产 Wan checkpoint 的 hash**。
- 独立 Ruff check 四个 changed Python PASS + Ruff format --check PASS：4 files already formatted。
- Root/Child Git status clean；GPU4–7 `0MiB`，没有真实 Wan/DCP、EGL、Server/Sim、训练/评测/导出运行。
- Raw independent evidence：`h1_targeted.{xml,log,exit}`, `independent_identity_compatibility.py`, `old_native.json`, `old_omega_RED.json`, `new_native.json`, `new_omega.json`, `independent_ruff.log` 和 `independent_gate_summary.json`；本地 `independent_gate_summary.json` SHA256：`51aac7635b2f97394b8eef351ec7411da2afd4aec604e61f8579395c7e11913c`。

## 5. Verdict / Gate boundary

**`APPROVE_CODE`** for **H1 H100-real-model-startup BLOCKER 的代码/CPU 合同整改**，**H1 CLOSED at CPU Gate**。没有新的 prod high/medium blocker；本增量不扩大 Stage3A 15+1 / FastState 原子事务设计，C仍仅 B1/wait0，原 strict numerical acceptance 未放宽。

**下一轮（未运行，本 verdict 未授权）：**在另立的真实 H100 Gate 上，复跑实际 iter15000 DCP Policy 初始化并对照独立 Worker真实 Loaded Wan identity，然后同源RGB 的 B1 Visual96、T16 vs16×T1 FastState/Prefix/Action 数值 parity；任何不能完全等价之处单独记录真实误差，不隐式 Accept。再考虑单 Policy×单 Sim C 真实 post-step 行为/延迟与 A/B/C 配对 SR。Stage3B B8 Action 和 V3 merge 保持禁止。

> Formal Target 仅为 Root ea64c26f7738f2efba5c33c78f18eab475230a61 + Child90ac5e91c5919cdb1d228aebd797e40327900981。后续本 review 与 Inbox 的 bookkeeping commits **不改变 technical formal pair**。
