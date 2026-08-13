# PSM-WMA 任务队列

状态：`TODO`、`IN_PROGRESS`、`BLOCKED`、`REVIEW`、`DONE`。

| ID | 状态 | 负责人 | 前置条件 | 验收条件 |
|---|---|---|---|---|
| COLLAB-BOOTSTRAP | DONE | Codex | 无 | 根目录协作协议、会话状态、任务队列和长期决策文件可供所有 Agent 使用 |
| DOC-R01 | IN_PROGRESS | Codex | G0 Runtime Plan v0.6 | R01 具备可直接执行的前置资产、命令、断言、产物、PASS/FAIL 和失败分流 |
| DOC-R02-R06 | TODO | 待认领 | DOC-R01 完成 | R02-R06 分别形成可独立执行和审查的版本化 Runbook；R02/R03 必须落实 D006 的 metadata-first 与 warm-start 决策边界 |
| REVIEW-R01 | BLOCKED | 待认领 | DOC-R01 进入 REVIEW | 独立 Agent 完成一致性、可执行性和源码锚点审查，问题均有级别和行号 |
| G0-R01 | TODO | 待认领 | REVIEW-R01 DONE；环境和 checkpoint 就绪 | 官方 Edge-Policy-DROID 能力 smoke 产生规范 JSON 和完整关键日志 |
| G0-R02 | TODO | 待认领 | G0-R01 PASS | 先完成 Nano LIBERO recipe / Nano config / Edge config / Edge-Policy-DROID config-index 的 metadata/config audit 并产出 JSON；仅当关键未决问题会改变 R04 初始化策略时，才按需做 bare Edge selected-shard tensor diff |
| G0-R03 | TODO | 待认领 | G0-R01 PASS | DROID/LIBERO action pipeline、domain、shape、mask 和 trainable scope 有运行时证据，并明确 `action2llm` / `llm2action` / `action_modality_embed` / embodiment domain 的 inherit-vs-new-domain-vs-reinit 决策 |
| G0-R04 | TODO | 待认领 | G0-R02、G0-R03 完成 | 基于已确认的 Edge LIBERO config 与 warm-start contract，Edge-Policy-DROID x LIBERO forward/loss finite，最小差分和异常信息可复现 |
| G0-R05 | TODO | 待认领 | G0-R04 PASS | LIBERO tiny-overfit 达到 Runbook 阈值并保存曲线与 checkpoint 信息 |
| G0-R06 | TODO | 待认领 | G0-R05 PASS | LIBERO closed-loop baseline 可重复且 SR > 0 |
| G0-R07-R09 | BLOCKED | 待认领 | G0-R06 PASS | Local/Global packing 与 Local Memory Gate 分别满足 Runtime Plan |

## 新增任务规则

- 一个任务只对应一个可独立验证的结果。
- 编码前先认领并列出预计修改文件。
- 验证完成后先转 `REVIEW`，独立检查通过后才转 `DONE`。
- 阻塞必须写明缺少的资产、权限或上游结果，不使用笼统描述。
