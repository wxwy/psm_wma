# Issue #14 — 每 Task 前 N 个逻辑 Episode 保存 Rollout MP4

状态：**REVIEW；作者定向 CPU Gate PASS**。尚未合入 V3。

| 身份 | 精确版本 |
| --- | --- |
| Formal Root | `fd183f9e8fddfaef93b6ec9484184f071062ae41` |
| Formal Child / Gitlink | `8664267704da3206e719f3c7eef2b5ed86e2a417` |
| Root 基线 | `9ba1dd110a4e3e99e717937c2f8d044fa077cdbf` |
| Child 基线 | `6c83596d6a259e89c4cd3e79424024983426ac3d` |
| Root/Child 独立候选分支 | `v3-eval-v2-rollout-first-n-20261101` |

后续 Evidence、Inbox 和回执提交不替代以上 Formal Pair。
已读取并确认 Issue #14 全文及 canonical 最小设计。Owner 当前只授权独立候选、
定向合成 CPU、自测证据及提交审核；不授权 V3 提升或真实执行。

## 实现及边界

```yaml
save_rollout_mp4: true
rollout_mp4_first_n_per_task: 3
save_generated_video: first
```

- Root `scripts/robocasa_eval_v2/config.py:23`、`:174`：新字段默认 null，
  保留旧 bool 行为。非 null 必须为 exact int、0..实际 episodes_per_task；
  拒绝 bool/float/string、负值/超界及 false+非 null（含 N=0）。
- Root `scripts/robocasa_eval_v2/runtime.py:54`、`:325`：向所有 Actor 原样透传
  上限，每次执行再决定录像。复用现有 CLI 的不可变调用记录，以 Fresh 配置固定 N；
  Resume 的 N 不同会在进程设置前拒绝。被拒 Resume 的记录不会替代 Fresh。
  旧记录缺少此键表示 null；不能给旧 Run 加非 null 上限。null 时原 bool 和
  generated 选项的既有行为保留。未改 Manifest、配置科学身份或 Source 校验。
- Child `cosmos_framework/simulation/robocasa/eval_v2_adapter.py:109`：每次
  NativeEpisode.execute 使用本次 attempt 的逻辑 episode index，传入现有
  MediaSink 的 rollout bool；没有在复用 Actor 中缓存首集结果。N=3 包含每 Task
  的 ep0/1/2，包含正常行为失败，不按成功数或先完成的顺序。重试同索引选择稳定。
  media_diagnostics 记录上限和本集实际 rollout_requested。
- Generated 的 none/first/all 独立；N=0 时仍可请求每 Episode 的首段预测视频。
  没有改 MediaSink、SR/Core、Store/Scheduler、Local-TTT、模型/Server、训练或 DCP。
  没有删旧媒体，也不声称该功能解决 OSMesa 渲染或获得性能收益。

## CPU Evidence

`docs/collab/codex/evidence/2026-11-01_eval_v2_issue14_rollout_first_n_author_cpu/`

- 最终 `final/gate.json`、原始 JUnit：**69 passed，0 failure/error/skip**，
  耗时约 13 秒。50 新用例 + 17 未改配置回归 + 2 未改媒体/Core 聚焦回归。
- Root/Child scoped Ruff **0.12.7 check、format --check、AST4 PASS**。
  Gate 前后精确 Pair 干净、源码未变；42 份产物哈希、11 份 Formal 源码绑定。
- 覆盖实际 CPU dry-run；cap 类型/边界/CLI episodes override；Fresh/Resume 配置
  记录及坏 Resume 不污染锚点；生产 Actor config 创建；同一 NativeEpisode 跨
  两 Task、ep0/1/2/3/49 与重复索引，包含 Success/Behavioral Failure、独立预测媒体。
  注入媒体构造/回调异常仍有合法 Core Commit 和 Local reset。
- Native 原始循环、HTTP codec/Local client 运行于 loopback 模型替身和 Fake Env；
  实际 MediaSink 筛选代码保留，但编码器被替身代替。没有真实 RoboCasa、模型、
  GPU、DCP、FFmpeg、MP4 编码或真实 Batch 性能验收。

两次早期 Gate 因新增夹具先后停在 20 pass/1 fail、27 pass/1 fail：分别是
调用记录未使用生产 save() 摘要封装，以及 Actor 夹具未持有生产 Store.locked lease。
只修夹具及 SESSION，生产代码、断言、预算都未放宽。原始失败日志/JUnit/Pair/Diff
完整保存在 attempts/；不可把部分通过数累加为最终统计或写成所有尝试均通过。

## 交接与停止条件

请求 GPT 对本次三文件增量及作者证据做 fresh Code Gate；不重复既有大范围审核。
准备发布 Child 候选，再发布 Root 候选，远端回读确认后停止。作者 PASS 不替代
GPT 或 DS 独立验收。实际录像、GPU、Canary 与正式评测另需授权。

当前 out2 Local-TTT 900 集、NoTTT 正式训练及其共享工作树、YAML、结果、媒体、
DCP、日志与进程均未访问或修改。V3 与正式 Child 分支保持原值；没有 DS 派发。
源码身份保护不因字段默认兼容而放开，不授权旧 Run 跨 Root/Child 恢复。
