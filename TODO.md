# PSM-WMA 任务队列

状态：`TODO`、`IN_PROGRESS`、`BLOCKED`、`REVIEW`、`DONE`。

| ID | 状态 | 负责人 | 前置条件 | 验收条件 |
|---|---|---|---|---|
| COLLAB-BOOTSTRAP | DONE | Codex | 无 | 根目录协作协议、会话状态、任务队列和长期决策文件可供所有 Agent 使用 |
| DOC-R01 | DONE | Codex | G0 Runtime Plan v0.6 | REVIEW-R01 的 H1/H2、M1-M3、L1/L2/L4 已修订并完成最小行为验证 |
| DOC-R02 | DONE | Codex | DOC-R01 完成 | Kimi 独立审查 APPROVE；MEDIUM-1 与 LOW-1/2/3/4 已关闭，Runbook 状态 `reviewed` |
| DOC-R03-R06 | TODO | 待认领 | 对应前序 Gate 完成 | 分别新增版本化 Runbook，不与其他 Gate 混入同一提交 |
| REVIEW-R01 | DONE | Kimi | DOC-R01 已重新进入 REVIEW | 二轮复审 APPROVE，首轮 8 项全部关闭，N1/N2/N3 已于收尾处理 |
| G0-R01 | DONE | Codex | REVIEW-R01 DONE；环境和 checkpoint 就绪 | Gate JSON PASS；用户批准 RoboLab 基础设施豁免，Reasoner/Policy/World smoke 与独立复核完成 |
| G0-R02 | DONE | Codex | G0-R01 PASS | metadata/config/index audit JSON PASS；有效索引 0 缺失、provenance 完整，warm-start 与 LIBERO 数据契约已冻结并通过独立审查 |
| G0-R03 | REVIEW | Codex | G0-R01 PASS | 真实 LIBERO 7→10→64 action pipeline、domain 5/8、shape/mask、projection smoke 与 1.423B trainable scope 已落盘；warm-start/行级更新保护决策待独立审查 |
| G0-R04 | TODO | 待认领 | G0-R02、G0-R03 完成 | 基于已确认的 Edge LIBERO config 与 warm-start contract，Edge-Policy-DROID x LIBERO forward/loss finite，最小差分和异常信息可复现 |
| G0-R05 | TODO | 待认领 | G0-R04 PASS | LIBERO tiny-overfit 达到 Runbook 阈值并保存曲线与 checkpoint 信息 |
| G0-R06 | TODO | 待认领 | G0-R05 PASS | LIBERO closed-loop baseline 可重复且 SR > 0 |
| G0-R07-R09 | BLOCKED | 待认领 | G0-R06 PASS | Local/Global packing 与 Local Memory Gate 分别满足 Runtime Plan |

## 新增任务规则

- 一个任务只对应一个可独立验证的结果。
- 编码前先认领并列出预计修改文件。
- 验证完成后先转 `REVIEW`，独立检查通过后才转 `DONE`。
- 阻塞必须写明缺少的资产、权限或上游结果，不使用笼统描述。
