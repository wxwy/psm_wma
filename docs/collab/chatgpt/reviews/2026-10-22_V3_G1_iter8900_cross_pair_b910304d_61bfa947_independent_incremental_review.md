# PSM-WMA V3 — G1 iter8900 Owner cross-pair Resume：b910304d / 61bfa947 独立增量审核

日期：2026-10-22
Gate：G1 专用 Owner Override Resume *isolated candidate* 的生产增量 / 作者合成 CPU Evidence。
Verdict：**`APPROVE` — 此精确 Pair 的 scoped source/author-CPU implementation Gate**。
**未授权**合并 V3、部署训练服务器、真实 G1 CPU preflight、加载8×H100、torchrun、恢复写Checkpoint或迁移其他Job。目标机 DS 独立 CPU/read-only actual G1 acceptance 与 Owner 真实训练启动单独 Gate。

## 1. Formal pair与远端状态

- Candidate Implementation Root `b910304dbf493eb5babe26cf1b055edc8477b386` / Gitlink Child `61bfa94766d33d95a7fa9771857d0f2fb3f0b405`；经 GitHub tree 核对两者精确一致。
- Candidate branch：Root `v3-g1-cross-pair-resume-20261022`，Child对应独立分支；尚未合入 V3。Codex 文档/Evidence HEAD `5fe6a513baa870c06f3186903b99e9bba80bb084` 只是后续归档，不是新的 Formal Pair。
- Root从候选父 `1fc28effe9e33a2e6522f6ffe60c55c68f8b367c` 的生产差异只有 `scripts/train_v3_packed128_staged.sh`（+11/-3）与Child gitlink；SESSION/TODO为append非功能。Child相对`35b0ea1ccee9ee26653ed6589c484f0997d1c586`仅修改 `examples/psm_wma_robocasa_corrected_phase5.py` (+210/-23)及新增 `examples/psm_wma_robocasa_g1_cross_pair_resume_test.py`（693行）。通用Trainer/DCP/Local、Optimizer、Producer/Planner、ExactWindow Config Truth helper、评测Queue源码无变动。
- 原冻结 G1 Root `e0121d34592d10323ede480eb3409468a07371ba` 并未在本轮公开 GitHub API中被解析到；DS所述目标机当前Root前缀`8610ad88`也不是本候选完整SHA。**必须用本候选源 Pair 自己的完整SHA运行，不能把当前任意V3 HEAD与其混用**。
- Frozen design/Owner审批：`docs/collab/chatgpt/requests/2026-10-22_G1_iter8900_owner_authorized_cross_pair_resume_compatibility.md` / `docs/collab/chatgpt/reviews/2026-10-22_G1_iter8900_Owner_override_cross_pair_resume_design_APPROVE.md`。此处不重审早先技术Pair或Owner允许的设计。

## 2. 直接增量实现与 contract→behavior

1. **Explicit-only exception** — Child `examples/psm_wma_robocasa_corrected_phase5.py:141-162` 声明G1冻结Job名/旧Root+Child/SHA256 canonical YAML/起点`iter_000008900`常量，`_owner_g1_cross_pair_resume()` 只准 `phase=resume`、指定Job、T16/B8/GA2/K4/8rank、30k/warmup500/save100、无fresh bounded；正常其它Job不变。Root launcher第三可选flag只有此Job的Resume可用，原双参数调用合同保持。
2. **Frozen authority/source normalization** — :207-254 `check_job_namespace()` 在Owner flag下仍查旧record Root/Child/record.semantic SHA自校验、schema/namespace/layout/diagnostic/canonical YAML+PKL每个 hash/symlink；只排除*顶层* root/child后递归逐字段比较其余训练语义。Tokenizer/Model/Optimizer/Scheduler/Trainer/数据路径/manifest/RNG/Cache/index/T/B/GA/K/源权重等非来源漂移fail-closed，报出具体字段路径。没有放宽默认Same-job Resume。
3. **Local-TTT frozen digest continuity** — :256-343 `_g1_resume_compatibility()` 用本次从实际 Catalog/Config 计算的`phase5_digest` + **历史record.semantic**重算旧`config_digest`，必须与原fresh launch记录精确相等；验证原fresh launch snapshot等于canonical YAML/PKL、8个rank dataloader sidecar iteration==8900、格式/profile/cache/corpus/source/digest、所有SegmentProvenance.config_digest，形成逐rank SHA/size witness。:1038-1053 preflight将此旧 digest 注入`report["config_digest"]`；未变更的Producer/Trainer/Callback直接读取相同旧digest，原LocalT-TT `restore_grouped_local_state()` 对cursor/frontier/fast-state仍独立发挥作用。仅屏蔽Root/Child而不带旧digest的实现会在Sidecar restore失败；本候选已覆盖该依赖。
4. **Runtime source 与 all-rank** — :851-894 `verify_root_child_lock()` 依然要求当前Root HEAD==实际`--expected-root`、Child HEAD==`--expected-child`==Gitlink、Child clean、Root仅允许原白名单修改；Owner flag另外校验旧`35b0...`为当前Child祖先，记录新runtime source。:517-539 all-rank agreement将旧digest与完整runtime audit hash组合比较，防止同一个旧digest掩盖各rank不同的新source。
5. **冻结资产与写路径** — :442-516 `JobLifecycle.write_config()` 在独占lease下再次读取冻结authority及8 sidecar，只有所有 witness与preflight完全一致才可创建新Launch，新增launch-local Owner审计，不修改旧`v3_job_identity.json`、canonical config、已保存旧DCP。新overlay Config兼容字段由32镜像16仅出现在RAM/新launch；旧canonical哈希与record semantic不得回写。完整Optim/Scheduler/RNG/Local state的真实加载标为`PENDING_UNCHANGED_STRICT_RUNTIME_LOAD`，没有在证据里虚报成功。
6. **Full-training vs inference** — :794-820 `_resume_checkpoint()`保留全训练恢复所需model/optim/scheduler/trainer metadata和8rank dataloader sidecar及路径/symlink检查，Owner override强制latest恰为`iter_000008900`；之前model-only inference不依赖optim的判断不适用本训练恢复Gate。
7. **作用域控制**：原`training_identity()`、原`config_digest()`、`overlay_config()`、主 `main()` 中计算/训练路径及旧Local model/trainer没有改语义；本轮仅新G1边界。

## 3. 作者 CPU Evidence 审核

已打开GitHub固定候选交接与直接源码，并读取实际 `gate.json` / `manifest.json` / `scope_proof.json` / `pytest.log` / `pytest.xml`；结果**115 passed +32 subtests passed，0 fail/error/skip**，JUnit计147包含subtests而非147个独立方法；Ruff0.12.7 check/format、语法、bash-n和diff-check据作者gate均RC0。
- 新68 case + 旧F0 28 methods + Config Truth19 case；测试用原未改`restore_grouped_local_state`的AST/CPU Tensor 直接验证旧digest能恢复每个rank连续frontier/4Fast值，错误new digest/损坏cursor/NaN/shape/provenance仍失败；源/非源字段损坏、Flag范围、旧fresh launch/SHA/sidecar rank/config/iteration、root clean/Gitlink/Child ancestry、新launch更改等负例覆盖。
- 用原函数body做合成 CPU 状态还原，比单纯helper/字符串断言更强；而重依赖、G1真实frozen YAML/PKL/实际8份DCP、全分布式FSDP、最终restore依旧未在GPT或作者机器上运行。
- 作者`manifest.json`明确`actual_g1_digest_known_to_author=false`、在tiny test fixture内替换原f87 SHA。GPT**没有独立拿到目标机真实G1文件**，不能把这个合成通过升级成现存G1的预检结果。

## 4. 当前发现与后续 Gate

**Scoped implementation blocker：无**。历史“禁止在新Root+Child恢复G1”的设计拒绝已被Owner对**此特定G1**的显式Override裁决替代；本候选完成所授权的有限实现，不授权普遍弱校验。

**Remaining execution/asset gate（non-code BLOCKED until DS evidence）**：DS_PRO须在隔离clean exact Root`b910...` / Child`61bf...`下，使用现存目标机真实G1身份与full checkpoint做**只读**核验：canonical旧YAML hash `f87e2e49c6931ce7dc32b467aa3f8026269f5ad255216e1cdd8fafb1d7e7374e`、identity semantic/launch完整digest一致、`iter_000008900` full training-state metadata和8个rank sidecars；运行本轮有限CPU tests，测试边界无显卡；随后**单独申请**真实同Job `--preflight`及 Owner授权的8×H100 Resume。任何目标环境真实非来源drift、旧digest或恢复组件不吻合必须fail-closed，不准为求绿而放开新字段。
- 此实现刻意限定起点**8900**：若未来在9000/10000等再次中断，当前Owner例外不会自动允许从新最新iteration重启；未来需另行明确设计/授权，不应把本次初始许可误解为永远跨Pair放行。
- 根仓V3主线未合并、真实训练未启动；不修改运行中或历史G1工作树/训练资产；不准混合Batch A另一个Child gitlink。

**Formal code/author-CPU Gate verdict `APPROVE` for exact `b910304d/61bfa947` ONLY。** 等待DS independent CPU/read-only asset evidence和Owner单独真实训练启动Gate。
