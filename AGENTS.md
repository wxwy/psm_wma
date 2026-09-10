# PSM-WMA Agent 协作约定

## 读取顺序

每次开始工作前依次读取：

1. `AGENTS.md`
2. `SESSION.md`
3. `docs/collab/chatgpt/CODEX_INBOX.md`（始终读取 canonical live Inbox；若有详细 review，按条目链接继续读；仅在 live Inbox 明确要求或需要历史上下文时读取 archive）
4. `TODO.md`
5. `MEMORY/DECISIONS.md`
6. 当前任务涉及的 `docs/build/` 文档
7. 进入 `cosmos-framework/` 后再读取其目录内的 `AGENTS.md`

## 文档职责

- `docs/build/`：版本化的正式方案、详细设计、Gate Runbook 和核验报告。已标记 `frozen` 或 `locked` 的文件不得静默改写，变更必须新建版本或显式记录 override。
- `docs/collab/chatgpt/CODEX_INBOX.md`：Codex → ChatGPT 的 **canonical live** 审核申请与交接 ledger；开始或继续当前任务前必须读取。Codex 的申请普通写入 append-only；达到 rollover 阈值时按下述规则归档并重建 live Inbox。ChatGPT 不在 Inbox 回写审核结论；其正式审核结果唯一存放于 `docs/collab/chatgpt/reviews/`，并以文件中声明的 formal root/child SHA 与 verdict 为准。
- `SESSION.md`：当前阶段的短期状态和 Agent 交接入口，只保留最新事实。
- `TODO.md`：唯一的待办队列。任务必须有 ID、状态、前置条件、负责人和验收条件。
- `MEMORY/DECISIONS.md`：跨会话长期有效的工程决策及依据，不记录临时过程。
- `artifacts/g0/`：R Gate 的机器可读结果；不得用文字结论替代 JSON 产物。

### ChatGPT Inbox 大小与 rollover（强制）

- live `docs/collab/chatgpt/CODEX_INBOX.md` 硬上限为 **131072 bytes（128 KiB）**。
- 每次准备 append 前先检查 `当前字节数 + 待追加字节数`。若将超过 128 KiB，必须先 rollover，不能继续把 live Inbox 无限增大。
- rollover 时把当前 live Inbox **byte-for-byte** 保存到 `docs/collab/chatgpt/archive/CODEX_INBOX_<timestamp>_<head7>.md`；archive 创建后不可改写、删除或截断。
- 然后在相同 canonical 路径重建精简 `CODEX_INBOX.md`，至少携带：立即前序 archive 路径与 blob SHA、pre-rollover head、当前 unresolved/latest Gate、formal target SHA、child/Gitlink、最新有效 verdict、详细 review 路径。重建后恢复 append-only。
- rollover 是 live Inbox 唯一允许的非 append-only replacement；archive 永远保持 append-only/immutable。
- Codex 始终先读 canonical live Inbox；除非 live 条目显式链接或确需历史信息，不得在普通审核轮询中反复读取完整 archive。
- rollover/ledger commit 只属于 bookkeeping，绝不能替代 design/implementation SHA 作为 verdict authority。

## 任务状态

统一使用：`TODO`、`IN_PROGRESS`、`BLOCKED`、`REVIEW`、`DONE`。

开始编码前，Agent 必须在 `TODO.md` 认领任务，并在 `SESSION.md` 写明预计修改的文件。若目标文件已被其他 Agent 标记为正在修改，不得并行编辑；先做检查、测试或选择不重叠任务。

## 每步记录

每个最小步骤都记录：

1. 目的与对应 Gate/任务 ID；
2. 阅读和复用的现有入口；
3. 实际修改的文件及行为变化；
4. 执行的命令和关键结果；
5. 未执行验证及原因；
6. 下一步和阻塞项；
7. 对应提交哈希；未提交时明确写 `未提交`。

完成一个步骤后先验证，再更新 `SESSION.md` 和 `TODO.md`，最后提交。不要把多个 Gate 混入同一提交。

## 代码执行告知

凡是执行代码、测试、训练、推理或评测，启动前必须先向用户显示并说明：

1. 目的及对应的任务/Gate；
2. 完整启动命令、工作目录和关键环境变量；
3. 是否需要 GPU、预计资源范围以及是否访问外网；
4. 输入的 checkpoint、数据集或配置；
5. 日志、JSON、checkpoint 等产物路径；
6. PASS、FAIL 和 BLOCKED 判据。

只有只读的文件查看、文本检索、Git 状态检查等不执行项目代码的命令，可以保持简短说明而不逐条展示完整命令。外网访问、配置/密钥修改及其他需确认操作仍必须先取得用户明确许可。

## 代码与审查

- 只做当前任务所需的最小修改，优先新增项目模块，集中修改 Cosmos 核心扩展点。
- 不覆盖、不回滚来源不明的工作区修改。
- 代码作者不得把“自测通过”等同于审查完成；任务进入 `REVIEW` 后，由另一 Agent 对照验收条件检查代码、测试和产物。
- 审查意见按严重级别记录，并附 `file:line`；修复后由审查者确认关闭。
- R01-R06 未通过前，不开始 Memory 算法实验实现。

## 正式实现文档格式

每个 R Gate 的 Runbook 至少包含：前置资产、精确命令、复用入口、最小代码改动、输入输出 Schema、断言、产物、PASS/FAIL、失败分流、回填字段。运行得到的事实不得提前写成固定常量。

## 持续执行与监控

- 触发 `提交审核`、`审核回复`、`启动/恢复训练、评测或推理`、`交给 Execute`、`监控执行` 时，必须先读取 `.codex/skills/psm-execution-governance/SKILL.md`；该技能定义三方审核门、角色边界及监控节奏。

- Agent 只能在发起审核、任务全部完成，或确实需要用户作出明确决策/授权时结束当前工作；普通阶段结果、可自行修复的错误和后台任务启动后都必须继续执行。
- 后台代码、训练、推理、评测必须由 Codex 原生每六十分钟轮询；审核等待必须由 Codex 原生每六十分钟轮询、至少连续三十轮；不得将 tmux 会话本身作为监控机制。
- 每完成一个最小步骤必须输出路线进度；每次审核请求发出后立即启动六十分钟一次、至少连续三十轮的审核回复监控。
- 每次发起审核申请时，必须在用户可见消息中使用醒目的 `🚨 审核申请已发出` 标识，便于用户及时提醒 GPT。

### 审核申请发送与回复监控（强制）

1. 申请必须先 append 到 `docs/collab/chatgpt/CODEX_INBOX.md`；若预计 append 后超过 128 KiB，先按 Inbox rollover 规则归档/重建，再把申请 append 到新的 live Inbox。申请必须写清任务/Gate、根仓提交号、子模块提交号与 Gitlink、证据路径、验收条件、允许/禁止范围，以及明确的 verdict 请求。
2. 同一申请必须主动发送到 MM 和 Kimi 的指定 `tmux` pane。发送时先用 `tmux send-keys -l` 写入完整文本，再单独执行 `tmux send-keys Enter`；不得把“文本已显示在输入框”当作“已发送”。随后必须 `tmux capture-pane` 回读，确认申请已提交且会话进入处理或已回复状态。
   - 固定节奏：写入完整文本后与单独的 `Enter` 之间至少间隔 1 秒；Enter 后必须 capture-pane 回读确认。
3. 用户可见的申请标记固定为 `🚨 审核申请已发出（根仓 <hash>；子模块/Gitlink <hash>）`，两个提交号不得省略。
   - 每次新申请及其后的每次审核轮询用户可见首行必须使用完整固定格式：`Awaiting review — 🚨 审核申请已发出（根仓 <hash>；子模块/Gitlink <hash>）`；两个 SHA 必须为该审核 formal root 与 formal child/Gitlink，不得缩写、遗漏、换序或使用其他前缀。
4. 申请发出后，每六十分钟由 Codex 原生轮询三路，至少连续三十轮：ChatGPT `docs/collab/chatgpt/reviews/`（按 formal SHA 查找新增正式 review，不将 Inbox 当作回复来源）、MM pane、Kimi pane；每次轮询记录申请是否送达、是否开始处理、最终 verdict 与 `file:line` 意见。普通轮询不得反复读取完整 Inbox archive。
   - 每次轮询或收到“已回复/拉取最新”提示时，必须先保存本地 `HEAD`、执行 `git fetch origin V2`、逐条输出本地旧 `HEAD..origin/V2` 的新增提交，并在可快进时先 `git merge --ff-only origin/V2`；之后才按 formal SHA 读取 ChatGPT `reviews/`、capture Kimi pane、capture MM pane。不得以未拉取的本地目录、输入框文本或旧 capture 断言“未回复”或“已齐”。
5. 审核等待期间任务状态保持 `REVIEW`，禁止越过该 Gate。收到全部所需审核结论后，先处理 `REQUEST_CHANGES`；全部批准后才更新 `SESSION.md`、`TODO.md` 并提交。ChatGPT 未在 Inbox 回复不构成缺件；若 `reviews/` 中没有匹配 formal SHA 的正式 review，则视为尚未回复。MM/Kimi 会话不存在、发送失败或未提交时，立即重发并在 `SESSION.md` 记录，不能声称申请已发出。
6. 同一审核申请的 ChatGPT、Kimi、MM 三方最终 verdict 必须全部收到后，才合并意见并启动“评估 → 最小整改 → 验证 → 提交/推送 → 新 SHA 重新申请审核”闭环；不得依据单一审核者意见提前修改或使其他同 SHA 审核失效。整改必须严格限于已批准范围；若意见要求扩大权限、真实执行或改变 Gate，仍须先取得对应独立批准。新申请发出后重新开始三路六十分钟、至少三十轮的原生轮询。
