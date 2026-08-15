# PSM-WMA 任务队列

状态：`TODO`、`IN_PROGRESS`、`BLOCKED`、`REVIEW`、`DONE`。

| ID | 状态 | 负责人 | 前置条件 | 验收条件 |
|---|---|---|---|---|
| COLLAB-BOOTSTRAP | DONE | Codex | 无 | 根目录协作协议、会话状态、任务队列和长期决策文件可供所有 Agent 使用 |
| DOC-R01 | DONE | Codex | G0 Runtime Plan v0.6 | REVIEW-R01 的 H1/H2、M1-M3、L1/L2/L4 已修订并完成最小行为验证 |
| DOC-R02 | DONE | Codex | DOC-R01 完成 | Kimi 独立审查 APPROVE；MEDIUM-1 与 LOW-1/2/3/4 已关闭，Runbook 状态 `reviewed` |
| DOC-R03 | DONE | Codex | DOC-R02 完成 | Kimi 独立审查 APPROVE；2 MEDIUM + 3 LOW 已关闭或按范围转交，Runbook 状态 `reviewed` |
| DOC-R04 | IN_PROGRESS | Codex | DOC-R03 完成 | 建立 Edge-Policy-DROID × LIBERO forward/loss 独立 Runbook，覆盖精确命令、资产、Schema、断言、判据与失败分流 |
| DOC-R05 | DONE | Codex | G0-R04 PASS | R05 Runbook 已升为 `reviewed`，stats、tiny subset、loss/reload/checkpoint 判据已通过实执验收 |
| DOC-R06 | TODO | 待认领 | G0-R05 PASS | 新增版本化 closed-loop baseline Runbook |
| REVIEW-R01 | DONE | Kimi | DOC-R01 已重新进入 REVIEW | 二轮复审 APPROVE，首轮 8 项全部关闭，N1/N2/N3 已于收尾处理 |
| G0-R01 | DONE | Codex | REVIEW-R01 DONE；环境和 checkpoint 就绪 | Gate JSON PASS；用户批准 RoboLab 基础设施豁免，Reasoner/Policy/World smoke 与独立复核完成 |
| G0-R02 | DONE | Codex | G0-R01 PASS | metadata/config/index audit JSON PASS；有效索引 0 缺失、provenance 完整，warm-start 与 LIBERO 数据契约已冻结并通过独立审查 |
| G0-R03 | DONE | Codex | G0-R01 PASS | 真实 LIBERO 7→10→64 action pipeline、domain 5/8、shape/mask、projection smoke、参数拆分与 stats provenance 已落盘并通过独立审查 |
| G0-R04 | DONE | Codex/Kimi | G0-R02、G0-R03 完成；40GB GPU 与非 fused AdamW 路径可用 | 连续 20 步 PASS：loss/grad 全 finite、domain 行保护 PASS、末次 checkpoint 四件齐全、无 OOM/SIGKILL；机器可读 Gate JSON 已落盘 |
| G0-R04-ADAMW | DONE | Codex/Kimi | G0-R04 单步诊断；框架当前硬编码拒绝 `fused=False` | 标准 Adam/AdamW 的非 fused 优化器路径已通过单步验证和 Kimi 独立 APPROVE；FusedAdam 行为不变 |
| G0-R05 | DONE | Codex/Kimi | G0-R04 PASS | Gate JSON `PASS`；100/100 步、两次 reload 逐位一致、checkpoint 四件齐全；HIGH-1/2 复审 APPROVE |
| DCP-MULTIRANK-RELOAD | TODO | 待认领 | R06 或任何正式多卡训练启动前；不阻塞单卡 R05 | CPU optimizer 叶子在 NCCL 多 rank DCP reload 中可正确广播；至少 2 rank 恢复真实 AdamW 状态与定向单测 PASS |
| G0-R06 | TODO | 待认领 | G0-R05 PASS | LIBERO closed-loop baseline 可重复且 SR > 0 |
| G0-R07-R09 | BLOCKED | 待认领 | G0-R06 PASS | Local/Global packing 与 Local Memory Gate 分别满足 Runtime Plan |
| G0-R12-CACHE | DONE | Codex/Kimi | Cosmos RGB 编码契约已确认；本地 Wan2.2_VAE.pth | 379/379 episode 全量编码成功、零错误；manifest、finite 抽查和全量时序映射校验通过 |

## 新增任务规则

- 一个任务只对应一个可独立验证的结果。
- 编码前先认领并列出预计修改文件。
- 验证完成后先转 `REVIEW`，独立检查通过后才转 `DONE`。
- 阻塞必须写明缺少的资产、权限或上游结果，不使用笼统描述。
