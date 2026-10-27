# CODEX IMPLEMENTATION REQUEST — V3 RoboCasa Evaluation 检验结果持久化与 Warm Resume 快速复用

- Owner 日期：2026-10-27
- GitHub Issue：[#6](https://github.com/wxwy/psm_wma/issues/6)
- 当前 formal implementation/design 基准：Root **`49df7f3c2e0ba8ef5871f9dd490e41fbc3dc5da9`**；Child/Gitlink **`746c5cf2f2324104a62fb71510343aa40d3976c5`**。
- 目标分支：`wxwy/psm_wma:V3`；**只在独立 candidate branch/worktree 编码，不直接并入 V3**。若子仓没有必要变化，保持 Child/Gitlink 原 SHA。
- 本文档是 **Owner 交给 Codex 的实现任务**，不是 Gate verdict。仅允许代码、合成 CPU fixture、静态检查和 Codex 作者 evidence；未授权真实模型 DCP 哈希、GPU、真实 RoboCasa 仿真、训练、服务器启动、历史结果回写。

## 1. Owner 冻结目标

现在 G1 `iter_000012000` RoboCasa 评测在固定 `--run-name` 下按 Episode Resume；未来可扩展18Task×50Episode（900），当前已经完成、已验证的 Episode 必须原封不动继续复用。

**只要固定 Checkpoint、配置及数据元信息确实没有变化，首次成功完整校验之后，后续 Resume 就复用持久化验证证据，不再反复全量读取模型 Payload。** 用户不希望每次评测启动都对同一约13GB+ DCP 做两次完整 SHA256，也不希望每个 Batch 对相同 Config/18Task metadata 做三次内容哈希。

必须明确保留的语义：Cache 命中是**基于可信只读文件存储 + 文件指纹的变更检测**，并非文件内容重新完成密码学证明。相同 stat 的恶意篡改不在该快速路径能证明的范围内。禁止在缺乏这些前提时向用户宣称“已重新做完整 SHA256 验证”。

## 2. 生产源码定位（实际 V3）

- `scripts/robocasa_episode_resume/model_identity.py:133-220` — `build_model_identity()` 全量读取 `model/.metadata` 和每个 `*.distcp`，生成 strong digest 与 `observed_model_files`，其 stat witness 为 `(st_dev,st_ino,st_size,st_mtime_ns,st_ctime_ns)`；`:223-262` 的 `verify_model_observation()` 是零模型 Payload 读取的快速检查。
- `scripts/robocasa_resume_store.py:269-310` — `preview` 做一次 `current_identity_reader()`；正式 `locked()` 先在锁外算完整 Identity，然后在 `.run.lock` 内再调用一次 `current_identity_reader()` 完整哈希，并做一致性校验。旧 `_resume_v2/model_identity.json` 已存 strong identity。
- `scripts/robocasa_resume_cli.py:304-318` — `read_model()` 与 RunStore 的接口；`:347-360` runtime/vendor 与 Dataset provenance 构造；`:460-467` `verify_inputs` 于 `pre_model_load`、`post_model_load`、`pre_commit` 反复检查 stat / config SHA / Task metadata SHA，每个 Task Batch 都重复。
- `scripts/eval_robocasa_18task_queue.py:92-122` — Action Server `/info` 真实配置验证；`scripts/robocasa_eval_results.py` — Episode/media/cleanup 真实性检查；`scripts/robocasa_episode_resume/scene_sampling.py` — scene Seed + Episode/Batch identity 与 Pending Resume authority。

## 3. 实现契约

1. **Cold Run / 首次可信证据**：执行一次完整模型 Payload SHA256，校验 headers、合法文件集、统计见证、`num_steps/action_horizon/guidance` 与已有 Manifest / Legacy bridge；首次拿到的强 Identity 不得被另一次无意义的全量哈希覆盖，锁内进行新的 stat / 文件清单一致性检查。只允许在完成安全 admission、获得原 `.run.lock` 后原子持久化带 version/schema 的验证记录，并使用 atomic replace + fsync；不能覆盖原始历史 Manifest、Episode/source、Checkpoint 或 Log。Cold 模式如果检查失败，不保存“成功”缓存。
2. **Warm Run / fast path**：每次 Resume 在原 `.run.lock` 内或调用入口采用可信持久验证记录，核对 checkpoint 规范化绝对路径、模型文件名清单、类型（ordinary，非 symlink）、`st_dev/st_ino/st_size/st_mtime_ns/st_ctime_ns`、缓存 schema/integrity、强 Identity digest、持久化 `_resume_v2/model_identity.json` 以及 `num_steps/action_horizon/guidance`。全部匹配才可跳过所有 Model Payload 哈希，并继续当前的零字节 stat guard；**被接受的强模型 identity digest 必须与 Cold Run 完全相同**，不得凭 stat 生成一个新的“伪完整哈希”。必须记录本次 cache_hit、model_payload_bytes_read=0 和耗时。
3. **失效或无可信缓存**：首次/老 Run、路径变化/迁移、名称/大小/inode/mtime/ctime 变化、模型参数变动、损坏/缺失/过期缓存、损坏目录、并发写入、中断事务：完整重新哈希与旧强 Identity 作严格比较或显式拒绝；不能把新 Checkpoint 暗中作为旧的模型接受，不能仅清空 Cache 后无条件 Resume。合法同字节 rehash 后可在持锁条件下更新 witness。路径迁移时既有 `--allow-relocated-legacy-checkpoint` **仅保持原旧 Manifest 限定范围**，Cache 不得替代迁移授权或削弱强身份比较。
4. **Readonly dry-run**：不得创建/修改 Run namespace、`.run.lock`、Verification Cache 或历史文件；如 Cache 命中可快速只读验证，如 Cache 缺失可只读全哈希，但不能持久化新信任。Cache 写入必须符合 `RunStore` lock，故障安全且幂等；明确复用或拒绝的 error code。
5. **Config / Task 元信息重复哈希**：对一次 Invocation 中实际已经强验证且有稳定原始 hash+file stat witness 的配置与任务 Metadata，允许后续 Batch 的 `pre_model_load/post_model_load/pre_commit` 仅做轻量 stat 检查，避免每 Batch 三次内容哈希；如果变动则重新内容校验/拒绝，绝不忽略模型 ABI、Task 来源或失败边界。跨 Invocation 持久缓存可选，但若采用，必须具备与模型同级的完整失效/命名空间隔离规则。未审计的 Vendor/Simulator Runtime Probe 不得直接被文件 stat 冒充完整运行时验证，可明确保持现有 probe 逻辑不优化。
6. **运行期与结果真值**：完整保留 `require_free_ports`、`/info` Model/参数/LocalTTT 检查、listener ownership、`verify_inputs` 的变化拒绝语义、`EpisodeProgress` / Local-TTT session cleanup / model provenance / source manifest / rollout/video frame decoding / result validation、final source revalidation、Pending Recovery。不能为了“更快”让失败 Runtime Episode 变为 COMPLETE 或新 Old Source 出现假复用。
7. **代码范围最小**：优先只修改 Root `scripts/robocasa_episode_resume/model_identity.py`、`scripts/robocasa_resume_store.py`、`scripts/robocasa_resume_cli.py` 及它们直接相关合成 CPU tests、runbook。必要时只调整与 Config / Task witness 相关的 Root helper。不得修改 Child Native Model/DCP、训练器、G1 Local 代码、No-TTT 训练、Episode-major 调度、Gpu7 SIGABRT 处理或 on-infrastructure-error policy；如需越界，先提交设计阻塞并停止扩大范围。

## 4. Acceptance matrix：contract → behavior → evidence

| Case | 期望 |
|---|---|
| Fresh / 无 strong anchor，无 Cache | 一次完整 SHA 模型 Payload，产生原有相同 strong digest；持锁持久 Cache（非 dry-run） |
| 正常原位置 Warm Resume | 零模型 Payload 读取 / 无 `_read_hash`，验证同一强 digest，恢复原 Run/22 completed Evidence |
| Fresh→锁内第二次身份检查 | 一次 SHA+第二次 stat，无第二次大文件哈希，锁竞态能拒绝 |
| 同一 Invocation 的多个 Batch | Config/Task metadata 不每次重新完整读取，变更检查不能丢 |
| 缺失/损坏/旧 Cache；旧 `_resume_v2/model_identity.json` | 必须保守 fallback 完整哈希，旧 Resume 路径仍工作；旧 strong anchor 未被篡改 |
| 改一个 shard 字节、同大小且恢复原 mtime（ctime 更新） | Cache 不命中；完整重哈希后强 Identity mismatch / FAIL，绝不假绿 |
| shard inode/path/ctime/mtime/size/目录清单改变 | Cache 不命中；按严格身份/Legacy relocation 规则处理 |
| `guidance`、`num_steps`、`action_horizon` / Config/Task metadata 改变 | 禁止静默复用原结果 |
| 同时两 Invocation；锁/Cache 半写/损坏/进程 kill | 没有跨进程污染、部分缓存、双 Runner 执行或已完成证据破坏 |
| `--dry-run` | 缓存存在走纯读取，缓存不存在也不创建目录、锁或缓存 |
| Media / Episode Evidence / Local cleanup 负例 | 原有 fail-closed 不回归；失败不能进入分母的 COMPLETE |

测试全部可用 tiny synthetic `.metadata` / ZIP shard、合成 RunStore/invocation、可追踪 `_read_hash` 调用计数，不访问真实 DCP、显卡或 simulator。运行直接相关 pytest + ruff/format/syntax；Author 保存实际 JUnit、命令、配置、源码 SHA 和计时/读取字节证据。不得把 CPU 性能数字写成真实 H100 速度提升。

## 5. 交付与 Gate

在**独立 Root candidate branch** 实现并提交；如果动 Child，必须在独立 Child candidate branch 更新 exact Gitlink。输出：

- Root formal implementation SHA + Child/Gitlink exact SHA、Root/Child diff 与文件范围；
- Cache schema、lock/atomicity、trust boundary、失效流程说明，Cold/Warm 指标；
- 合成 CPU pytest/JUnit / Ruff Evidence、旧 Run Resume 兼容性和所有负例；
- 新的最小启动参数（理想为 **不改变现有正式 Resume 命令**，自动安全命中缓存）；
- 只交给 GPT 独立 Implementation Gate 与 DS_PRO CPU Gate。**STOP**，不得直接合并 V3、不得触碰训练服务器真实 Checkpoint、既有 22 个历史 Episode、GPU 4–7 / Runtime、仿真进程或任何生产输出。

重要：Issue 创建和规范文件持久化，只构成 Codex 可读取的任务交接；不会自动运行 Codex。
