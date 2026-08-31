---
name: psm-execution-governance
description: 管理 PSM-WMA 的审核申请、三方批准门、执行者边界与监控节奏。凡任务涉及提交审核、等待审核、启动训练/评测/推理或监控已启动执行时使用；普通代码编辑不使用。
---

# PSM 执行治理

## 触发条件

出现以下任一情况时，先加载本技能：发起或处理审核申请、询问审核回复、请求启动或恢复训练/评测/推理、将任务交给 Execute 会话、或要求监控后台执行。

## 审核门

- 只有 ChatGPT Inbox 最新有效 verdict、Kimi、MM 针对同一实现 SHA 都批准，才可启动对应执行。
- 任一 `REQUEST_CHANGES`、SHA 不一致或未回复均不得执行；先处理意见并重新审核。
- 审核申请后每 30 秒轮询 Inbox/远端、Kimi pane、MM pane；记录送达、处理、verdict 与 file:line。

## 角色边界

- 构建者负责代码、冻结命令、证据汇总和审核申请。
- Kimi、MM 只审核，不执行。
- Execute 只接收构建者已冻结的命令、输入、输出、PASS/FAIL 与停止条件；不得读取或判断审核消息、Inbox 或 review 文件。

## 执行与监控

- 启动前向用户说明完整命令、资源、输入、输出、PASS/FAIL。
- 已启动执行后每 5 分钟监控 Execute 会话、GPU、日志和产物；不重复执行者的普通预检。
- 任一 FAIL、NaN、OOM、越界命令或缺失产物，立即停止并保留证据；不得自动扩大范围或重跑。
