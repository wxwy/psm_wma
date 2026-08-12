# PSM-WMA 任务队列

状态：`TODO`、`IN_PROGRESS`、`BLOCKED`、`REVIEW`、`DONE`。

| ID | 状态 | 负责人 | 前置条件 | 验收条件 |
|---|---|---|---|---|
| COLLAB-BOOTSTRAP | DONE | Codex | 无 | 根目录协作协议、会话状态、任务队列和长期决策文件可供所有 Agent 使用 |
| DOC-R01-R06 | IN_PROGRESS | 其他 Agent | G0 Runtime Plan v0.6 | R01-R06 均具备可直接执行的前置资产、命令、断言、产物、PASS/FAIL 和失败分流 |
| REVIEW-R01-R06 | TODO | 待认领 | DOC-R01-R06 进入 REVIEW | 独立 Agent 完成一致性、可执行性和源码锚点审查，问题均有级别和行号 |
| G0-R01 | TODO | 待认领 | REVIEW-R01-R06 DONE；环境和 checkpoint 就绪 | 官方 Edge-Policy-DROID 能力 smoke 产生规范 JSON 和完整关键日志 |
| G0-R02 | TODO | 待认领 | G0-R01 PASS | 完成 Edge 与 Policy-DROID checkpoint/config 差异审计并产出 JSON |
| G0-R03 | TODO | 待认领 | G0-R01 PASS | DROID/LIBERO action pipeline、domain、shape、mask 和 trainable scope 有运行时证据 |
| G0-R04 | TODO | 待认领 | G0-R02、G0-R03 完成 | Edge x LIBERO forward/loss finite，最小差分和异常信息可复现 |
| G0-R05 | TODO | 待认领 | G0-R04 PASS | LIBERO tiny-overfit 达到 Runbook 阈值并保存曲线与 checkpoint 信息 |
| G0-R06 | TODO | 待认领 | G0-R05 PASS | LIBERO closed-loop baseline 可重复且 SR > 0 |
| G0-R07-R09 | BLOCKED | 待认领 | G0-R06 PASS | Local/Global packing 与 Local Memory Gate 分别满足 Runtime Plan |

## 新增任务规则

- 一个任务只对应一个可独立验证的结果。
- 编码前先认领并列出预计修改文件。
- 验证完成后先转 `REVIEW`，独立检查通过后才转 `DONE`。
- 阻塞必须写明缺少的资产、权限或上游结果，不使用笼统描述。
