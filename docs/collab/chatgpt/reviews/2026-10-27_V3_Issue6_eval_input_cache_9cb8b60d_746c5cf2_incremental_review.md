# GPT independent incremental review — V3 Issue #6 RoboCasa Eval persistent input-verification cache

- 日期：2026-10-27
- **Formal implementation Root:** `9cb8b60dccf4ac2520f8d862b723d7bc94fe3813`
- **Child/Gitlink:** `746c5cf2f2324104a62fb71510343aa40d3976c5`（无改动）
- Base production Root: `49df7f3c2e0ba8ef5871f9dd490e41fbc3dc5da9`；Codex branch base/docs Root `eafef76f324964cb400b12e73dea2b4241c2baf7`
- Candidate `v3-eval-input-cache-20261027` currently at `bef955c2001b32e4bdd437c9bb6103ece6b8f59c`（**仅后续 Evidence/Bookkeeping，不替代 implementation SHA**）
- 冻结合同：`docs/collab/chatgpt/requests/2026-10-27_Codex_V3_RoboCasa_eval_cached_input_verification.md` / Issue #6
- Author handoff：`docs/collab/codex/reviews/2026-10-27_V3_RoboCasa_eval_input_cache_author_handoff.md`
- **Formal verdict: `APPROVE` — 仅限本精确 pair 的增量实现代码 + 作者 synthetic CPU Evidence Gate；不是 DS_PRO 独立 CPU 或真实 DCP/GPU/RoboCasa Gate。**

## 1. 远端锁定 / Scope

直接读取 GitHub candidate Root、V3、Gitlink、实际五处 production diff、两个新测试文件和既有相关回归，非仅依赖 Codex 口头报告。Root `eafef76f.. → 9cb8b60d..` 为一个实现提交；Child/Gitlink 维持 `746c5cf2..`。Production scope:
- `scripts/robocasa_episode_resume/model_identity.py`
- `scripts/robocasa_input_verification.py`（新增）
- `scripts/robocasa_resume_store.py`
- `scripts/robocasa_resume_cli.py`
- `scripts/v3_evaluation_identity.py`

新增/调整仅直接相关 CPU tests + design/SESSION/TODO。受保护的 Child、模型/训练、Episode sampler、eval execution/error cancellation、GPU7、HTTP/server、media/local cleanup 和 No-TTT 未修改。

## 2. Contract → code behavior → evidence

| Contract | 直接源码核验 | Evidence/判定 |
|---|---|---|
| Cold 只完整哈希一次 | `RunStore._read_current_identity` Cold 调用原 `build_model_identity`；`locked:370-376` 锁内首先 `verify_model_observation`（stat/目录），仅真实变化才全哈希 | 生产路径正确；tiny DCP 188B Cold 读取一次，2 文件，author JUnit 支持 |
| Warm 原 Strong digest/0 Payload | `model_identity.reuse_verification_record:284-336` 严格 Cache schema/checksum/namespace/原 anchor 原始字节 SHA/30天/四参数/完整文件 stat；命中复用原 `parameters/digest`，遥测0 bytes | 生产路径正确；mock 禁止 `_read_hash` 的 Warm 直接测试 |
| Cache 失效/撤销/迁移/并发 | `RunStore._read_current_identity:233-255` miss 回到严格完整哈希与 `_admit`，不信任 Cache 作为独立锚；旧 `legacy_ingest`/relocation opt-in 未弱化；`.run.lock` 独占保留 | 作者负例覆盖损坏/过期/错误 SHA/目录/路径/参数/mtime/ctime/不同字节、共享锁和 race |
| 原子化/只读 dry-run | `_persist_verification:257-268` 只在已持有原 lease 且 `begin_invocation:599-623` 的原 strong anchor 存在时用既有 `_write(replace=True)` temp+fsync+replace+dir fsync；`preview` 无写 | fault injection/子进程 exit23 和 readonly tests 覆盖；Cache 是模型校验记录，不是 Episode 完成标志 |
| Config/Task 一次 Invocation 验真后 Batch 轻校验 | `snapshot_inputs` 在原 vendor/Config/Task 完整 bundle 前；`InvocationInputGuard.__init__` 后检 hash 绑定期间 stat 未变，三阶段 `verify` 只查 manifest+dev/ino/size/mtime/ctime；final 再校验 | 20 Batch×3 guard零内容读，原始 full bundle 每 Invocation 仍保留；Author mutation/CLI cases 直接覆盖 |
| ABI 与媒体/源 Resume 不回归 | `v3_evaluation_identity.build_evaluation_identity` 可复用已强验的 metadata SHA（预先确认参数+路径/stat），其余身份字段一致；`eval_robocasa_18task_queue.py`,`robocasa_resume_execution.py`,`scene_sampling.py`,`robocasa_eval_results.py` 未改 | 旧22/50 合成 reuse、原 strong manifest/完整性 guard 测试通过；真正机上22集未被本轮重新核验 |

## 3. Author Evidence 独立核实

直接读取 GitHub Evidence 目录 `docs/collab/codex/evidence/2026-10-27_eval_input_cache_author_cpu/` 中保存的 `junit.xml`、`pytest.log`、`command.json`、`STATUS.json`、`CACHE_IO_WITNESS.json`、`committed_source_binding.json` 和静态日志：
- **JUnit 实际包含227个 testcase，tests=227, failures=0, errors=0, skipped=0, time=4.049s**；5个测试模块依次46+7+35+41+98，新增两模块合计53例；不是仅接受作者的汇总数字。
- `committed_source_binding.json` 的 **10/10 Git blob SHA** 用 formal Root `9cb8b60d` 逐文件重新 fetch 对照一致。
- 作者报告 Ruff 0.12.7 `All checks passed!`、`9 files already formatted`；测试命令带 `--noconftest -c /dev/null`、CPU/无 CUDA 环境。
- 显式区别：我未亲自执行 CPU pytest、未访问真实13GB DCP、GPU、Server 或 RoboCasa；作者 tiny fixture 188B 和无原生服务器执行不能当作真实负载/实地验证。

## 4. Findings、限制与判定

**本 Code + Author Synthetic CPU Gate 未发现要求修改的生产 blocker，`APPROVE`。** 已审计源身份/Cache 写入和失效条件，未发现使原模型、旧 Episode 成果或 DCP 发生写入的代码。本轮不存在待关闭的 Issue #6 旧 formal blocker。

必须透明告知的合同内限制（非 blocker）：
1. 只有在 Owner 可信只读存储、可靠 Linux stat 见证假设成立时 Cache Hit 才能代表沿用之前完整的 SHA；**不是重新执行 SHA**，不抵御恶意 same-stat 覆盖或缓存/anchor 被同时伪造。
2. Config/Task 元数据**每个新 Invocation 首次仍全文校验**，只取消该 Invocation 内 per-Batch 三次全文哈希；跨 Invocation metadata cache 是 frozen scope 的 optional，不作为未实现 blocker。
3. Warm 快路径不会免除真正 Native DCP 模型加载、Vendor Runtime Probe、Server /info、Episode/media/Local cleanup 原始证据校验；真实启动加速幅度尚无现场量化。
4. 此 Review 的 approval **不授权** V3 合并、DS 以外的改代码、运行中的 G1/No-TTT 干预、Checkpoint/Run 改写、真实900 Episode/模型加载/GPU/仿真。

## 5. Next separate Gate

- **DS_PRO** 使用 clean detached Root `9cb8b60dccf4ac2520f8d862b723d7bc94fe3813` + Child `746c5cf2f2324104a62fb71510343aa40d3976c5` 独立跑冻结的5个合成 CPU modules、Ruff 及原 SHA/Blob/检查锁负例；验收当前 pair 与 Evidence 的再现，不重做其他无关 Gate。
- 通过后由 Owner 单独决定是否合并 V3、部署与读取真实 immutably pinned iter12000 DCP 的 cold/warm、是否授权 Resume 既有22个 Episode及其后续训练/仿真。
- 若 DS 更强 fixture 发现 production 回归，按新独立 blocker 重开，不得把此 code-only APPROVE 冒充全流程 PASS。

**Persistence:** 本文为 detailed review；正式 verdict 须在 `docs/collab/chatgpt/CODEX_INBOX.md` 同步 append-only 登记后方成立。
