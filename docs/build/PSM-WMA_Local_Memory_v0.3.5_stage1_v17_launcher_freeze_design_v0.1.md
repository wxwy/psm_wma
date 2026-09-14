# Stage-1 v1.7 launcher freeze design v0.1（已被 v0.2 supersede）

> 历史设计。Gate/API 不完整，正式实现与后续审核必须以
> `PSM-WMA_Local_Memory_v0.3.5_stage1_v17_launcher_freeze_design_v0.2.md` 为准。

**Gate**：`G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-INSTANCE-CONSTRUCTION-AND-REVIEW`

## 目的

v1.6 的一次 Stage-1 authority 在外层临时 wrapper 的 payload SHA 重演失败时零 mutation 退出；不得重试。
v1.7 先新增一个 root-only、stdlib-only、可审计的 launcher-replay module 及 direct CPU/static tests，随后才可
构造新的 exact request。该 module 必须从 formal parent 的 Git blob 读取 base、机械解析 `RAW[2]`、拒绝任何既存
owner-FD flag、唯一插入相邻 owner-FD pair，并重演 outer payload；任何 declared bytes/SHA 不匹配均在
`os.execve` 前以 `BLOCKED_AUTHORITY_NOT_CLOSED` 返回。

## 最小范围与验收

- 仅新增 root `tools/psm_wma/` launcher-replay module、其 direct temporary CPU/static test、设计/记录文件；child
  Gitlink 不变。
- 测试固定 v1.6 base/parser/outer identities，并覆盖错误 adapter SHA、旧 owner flag、错误插入位置和所有
  source-level drift；不得调用 `main()`、创建 project clean root/index/ref/evidence、访问 source/checkpoint/data/cache。
- `py_compile`、direct unittest、`git diff --check` 必须通过。
- 本设计不授权 v1.7 request construction、任何 Stage-1 重试或真实 I/O、child、GPU、训练。

## 后续边界

只有该 implementation 获独立三方同 SHA `APPROVE_TO_IMPLEMENT`、实现闭环再获独立 close approval后，才可由
其 frozen executable bytes 构造并审核 v1.7 exact request。该 request 仍是一轮新的 one-shot authority，且必须重做
freshness observation；不得从 v1.6 的失败推断可重试。
