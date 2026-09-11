---
name: psm-execution-governance
description: 管理 PSM-WMA 的审核申请、三方批准门、执行者边界与监控节奏。凡任务涉及提交审核、等待审核、启动训练/评测/推理或监控已启动执行时使用；普通代码编辑不使用。
---

# PSM 执行治理

## 触发条件

出现以下任一情况时，先加载本技能：发起或处理审核申请、询问审核回复、请求启动或恢复训练/评测/推理、将任务交给 Execute 会话、或要求监控后台执行。

## 审核门

- 只有 canonical live ChatGPT Inbox 的最新有效 verdict、Kimi、MM 针对同一实现 SHA 都批准，才可启动对应执行。
- 任一 `REQUEST_CHANGES`、SHA 不一致或未回复均不得执行；先处理意见并重新审核。
- 审核申请后每 5 分钟轮询；用户提示“已回复”“已提交”“拉取最新”或准备作审核状态判断时立即额外执行一轮。每轮固定顺序为：保存 `before_head=$(git rev-parse HEAD)` → `git fetch origin V2` → `git ls-remote origin refs/heads/V2` → 先输出 `git log --oneline "$before_head"..origin/V2` 的每个新提交 → 如可快进则 `git merge --ff-only origin/V2` → 无论 revision range 是否为空都按 exact formal root/child 扫描 `docs/collab/chatgpt/reviews/` → capture Kimi pane → capture MM pane。只有这些步骤均成功且精确检索未命中时才可报告“无新增/尚未回复”；任一步失败必须报告“检查失败/状态未知”，不得把失败或旧结果解释成未回复。
- 审核等待、远端暂未回复、tmux 暂无新行都不是 `blocked`。任务保持 `REVIEW` 并持续轮询；只有同一外部阻塞已连续三轮且没有任何安全的本地检查或修复可做时，才可标记 `blocked`。
- 每次向用户显示审核申请时，首行固定为：`Awaiting review — 🚨 审核申请已发出（根仓 <hash>；子模块/Gitlink <hash>）`；不得省略 `Awaiting review`。

## Inbox rollover

- canonical live Inbox 固定为 `docs/collab/chatgpt/CODEX_INBOX.md`；Codex 始终先读这个路径。
- live Inbox 硬上限为 **131072 bytes（128 KiB）**。任何 append 前先检查 `current_bytes + append_bytes`。
- 若预计超过阈值，必须在 append 前执行 rollover：把当前 live Inbox byte-for-byte 保存为 `docs/collab/chatgpt/archive/CODEX_INBOX_<timestamp>_<head7>.md`，archive 一经创建即 immutable；然后在相同 canonical 路径建立精简 live Inbox。
- 精简 live Inbox 至少保留：immediate archive 路径 + blob SHA、pre-rollover head、当前 unresolved/latest Gate、formal target SHA、child/Gitlink、最新有效 verdict、详细 review 路径。完成后再 append 新条目。
- rollover 是 live Inbox 唯一允许的 replacement；普通操作仍严格 append-only。
- rollover/Inbox commit 永远是 ledger/bookkeeping SHA，不能替代 design/implementation target SHA。
- 普通审核轮询只读 live Inbox 尾部及其明确链接的 review；除非追溯历史事实，不要读取完整 archive，从而避免 Inbox 历史持续拖慢审核。

## 角色边界

- 构建者负责代码、冻结命令、证据汇总和审核申请。
- Kimi、MM 只审核，不执行。
- Execute 只接收构建者已冻结的命令、输入、输出、PASS/FAIL 与停止条件；不得读取或判断审核消息、Inbox 或 review 文件。

## 执行与监控

- 启动前向用户说明完整命令、资源、输入、输出、PASS/FAIL。
- 已启动执行后每 5 分钟监控 Execute 会话、GPU、日志和产物；不重复执行者的普通预检。
- 任一 FAIL、NaN、OOM、越界命令或缺失产物，立即停止并保留证据；不得自动扩大范围或重跑。

## 原生持续目标

- 收到“继续构建”“不要停”“监控”等持续性指令时，先检查原生 goal 状态。若不存在 active goal，按用户指令新建；若为 active，保持它直到真实 Gate 结束、需要明确授权或用户明确停止。
- 不得因为等待审核、一次轮询无变化、上下文压缩或单个工具调用结束而标记 goal 为 `blocked` 或结束回合。
- 若平台已存在错误的 unfinished `blocked` goal 且拒绝新建目标，必须立即向用户说明该平台状态和所需的“新建持续目标”明确指令；不得假称后台监控仍会自动唤醒当前回合。
