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
- 后台代码、训练、推理、评测必须由 Codex 原生每三分钟轮询；审核等待必须由 Codex 原生每三分钟轮询、至少连续三十轮；不得将 tmux 会话本身作为监控机制。
- 每完成一个最小步骤必须输出路线进度；每次审核请求发出后立即启动三分钟一次、至少连续三十轮的审核回复监控。
- 每次发起审核申请时，必须在用户可见消息中使用醒目的 `🚨 审核申请已发出` 标识，便于用户及时提醒 GPT。

### 审核申请发送与回复监控（强制）

1. 申请必须先 append 到 `docs/collab/chatgpt/CODEX_INBOX.md`；若预计 append 后超过 128 KiB，先按 Inbox rollover 规则归档/重建，再把申请 append 到新的 live Inbox。申请必须写清任务/Gate、根仓提交号、子模块提交号与 Gitlink、证据路径、验收条件、允许/禁止范围，以及明确的 verdict 请求。
2. 同一申请必须主动发送到 MM 和 Kimi 的指定 `tmux` pane。发送时先用 `tmux send-keys -l` 写入完整文本，再单独执行 `tmux send-keys Enter`；不得把“文本已显示在输入框”当作“已发送”。随后必须 `tmux capture-pane` 回读，确认申请已提交且会话进入处理或已回复状态。
   - 固定节奏：写入完整文本后与单独的 `Enter` 之间至少间隔 1 秒；Enter 后必须 capture-pane 回读确认。
3. 用户可见的申请标记固定为 `🚨 审核申请已发出（根仓 <hash>；子模块/Gitlink <hash>）`，两个提交号不得省略。
   - 每次新申请及其后的每次审核轮询用户可见首行必须使用完整固定格式：`Awaiting review — 🚨 审核申请已发出（根仓 <hash>；子模块/Gitlink <hash>）`；两个 SHA 必须为该审核 formal root 与 formal child/Gitlink，不得缩写、遗漏、换序或使用其他前缀。
4. 申请发出后，每三分钟由 Codex 原生轮询三路，至少连续三十轮：ChatGPT `docs/collab/chatgpt/reviews/`（按 formal SHA 查找新增正式 review，不将 Inbox 当作回复来源）、MM pane、Kimi pane；每次轮询记录申请是否送达、是否开始处理、最终 verdict 与 `file:line` 意见。普通轮询不得反复读取完整 Inbox archive。
   - 每次轮询或收到“已回复/拉取最新”提示时，必须先保存本地 `HEAD`、执行 `git fetch origin V2`、逐条输出本地旧 `HEAD..origin/V2` 的新增提交，并在可快进时先 `git merge --ff-only origin/V2`；之后才按 formal SHA 读取 ChatGPT `reviews/`、capture Kimi pane、capture MM pane。不得以未拉取的本地目录、输入框文本或旧 capture 断言“未回复”或“已齐”。
   - **即时远端锁定（防遗漏硬规则）**：用户问“是否已拉取最新”“是否有回复/更新”、提示审核者已回复，或 Agent 准备说“无新增/尚未回复/未发现 review”时，不得复用上一轮轮询结果；必须在本次回复内重新执行并按顺序记录：`before_head=$(git rev-parse HEAD)` → `git fetch origin V2` → `git ls-remote origin refs/heads/V2` → 输出 `before_head..origin/V2` 全部新增提交 → 可快进则 `git merge --ff-only origin/V2` → 按 exact formal root/child 扫描 `reviews/` → capture Kimi/MM。结论只能表述为“截至本次检查（本地 HEAD、远端 advertised V2 SHA）”；不得把一次检查外推到后续时刻，也不得仅因 revision range 为空而跳过 review 目录扫描。
   - 若 `fetch` 后发现远端相对检查开始已推进，必须先逐条呈现新增提交和 merge 结果，再读取 verdict；禁止先说“没有更新”后才拉取。任何先前基于旧 fetch 的否定性陈述，在新 fetch 前均视为过期，不得复述。
5. 审核等待期间任务状态保持 `REVIEW`，禁止越过该 Gate。收到全部所需审核结论后，先处理 `REQUEST_CHANGES`；全部批准后才更新 `SESSION.md`、`TODO.md` 并提交。ChatGPT 未在 Inbox 回复不构成缺件；若 `reviews/` 中没有匹配 formal SHA 的正式 review，则视为尚未回复。MM/Kimi 会话不存在、发送失败或未提交时，立即重发并在 `SESSION.md` 记录，不能声称申请已发出。
6. 同一审核申请的 ChatGPT、Kimi、MM 三方最终 verdict 必须全部收到后，才合并意见并启动“评估 → 最小整改 → 验证 → 提交/推送 → 新 SHA 重新申请审核”闭环；不得依据单一审核者意见提前修改或使其他同 SHA 审核失效。整改必须严格限于已批准范围；若意见要求扩大权限、真实执行或改变 Gate，仍须先取得对应独立批准。新申请发出后重新开始三路三分钟、至少三十轮的原生轮询。

### 审核事实防遗漏协议（强制，覆盖任何相冲突的旧表述）

1. **唯一节奏与触发**：审核等待的固定轮询间隔为三分钟；用户提示“已回复”“已提交”“拉取最新”或 Agent 准备作任何审核状态判断时，必须立即执行一轮完整检查，不能等待下一定时轮询。项目 `AGENTS.md` 与项目治理技能必须保持该同一节奏；发现冲突时先修正规范再继续，不得自行择一执行。
2. **单轮观察记录**：每一轮都必须在 `SESSION.md` 的当前 Gate 记录可复核字段：检查时间（CST）、`before_head`、`origin/V2` advertised SHA、`fetch`/`merge --ff-only` 结果、完整新增提交范围、formal root/child pair、ChatGPT exact-match review 文件或“未找到”的检索命令和结果、MM/Kimi pane 名称与 capture 摘要、三方各自状态。记录只描述本轮事实，不能复制旧轮次的否定结论。
3. **否定结论的证据门槛**：只有本轮 `git fetch origin V2`、`git ls-remote`、必要的 fast-forward、exact formal-pair review 扫描，以及两个 pane 的成功 capture 全部完成，才可写“尚未回复”“无新增”或“未发现 review”。任一步失败、pane 不存在、远端不可达、formal pair 不明确或检索异常时，唯一允许的结论是“本轮检查失败/状态未知”，并列出失败步骤；不得把失败解释成未回复。
4. **回执与送达不可推断**：审核者口头提示、远端新增提交、Inbox 条目、tmux 输入框已有文本，均只是线索，不是最终审核事实。ChatGPT 只有 `reviews/` 内 exact formal root/child 且含正式 verdict 的文件才算回复；MM/Kimi 只有 capture 中已提交的、锚定 exact pair 的最终 verdict 才算回复。任何一个 SHA 不同、仅中间意见、或没有明确 verdict，均为“处理中”，不得计为批准或拒绝。
5. **推进互锁**：汇总/整改/实施/关闭 Gate 前，必须在同一轮观察记录中显式列出三方 exact pair 与 verdict；缺任一项即保持 `REVIEW`，不得以“之前已经看过”“应该已回复”补足。若收到 `REQUEST_CHANGES`，同样先等同 SHA 的三方 final verdict 全部到齐后才合并处理。
6. **可追责表达**：用户可见的审核进度必须逐方写为 `已送达 / 处理中 / 已回复(<verdict>, 证据路径或 pane) / 检查失败`，并带“截至本轮检查”的本地 HEAD 与远端 advertised SHA。禁止使用无证据的“都齐了”“没有新的”“应该”“似乎”等概括性表述。

### 审核状态原子互锁（强制，防止陈旧状态、漏发与误报）

1. **观察凭证先于结论**：每一次关于审核状态的肯定或否定陈述，都必须先产生一条同轮“观察凭证”。凭证必须包含轮次号、CST 时间、formal root/child pair、`before_head`、远端 advertised SHA、fetch/merge 结果、review 精确检索命令及结果、两个 pane 的 capture 结果。凭证未完整写入 `SESSION.md` 前，Agent 不得向用户作出“已送达、处理中、已回复、未回复、无新增、已齐”任一结论。
2. **单次观察不可复用**：一次凭证只对其记录的 formal pair、远端 SHA 和检查时间有效。任何新用户消息、任何新审核申请、任何远端 HEAD 变化、或任何准备启动整改/实施的动作，都会使旧凭证失效；必须重新完整观察。不得从历史对话、旧 `SESSION.md`、旧 capture 或审阅者口头提示复制状态。
3. **送达双回执**：向每位 tmux 审核者发送申请时，必须保存“消息摘要/目标 pane/发送时间/Enter 后 capture”四项回执。capture 必须能证明消息已离开输入框并进入会话；否则状态只能是“发送失败”，立即重发。ChatGPT 申请仅以 live Inbox 的已提交内容为送达回执，正式结果仍只以 exact-pair `reviews/` verdict 为准。
4. **失败即闭锁**：fetch、ls-remote、fast-forward、review 扫描、pane capture、Inbox 容量检查或送达回执任一环节失败、超时或输出不完整时，本轮状态一律为“检查失败/状态未知”。该闭锁禁止后续汇总、整改、实现、训练或关闭 Gate；只能先修复检查链路并重做完整观察。
5. **实施前机械复核**：在任何整改、编码、提交、训练或执行命令前，必须重新核验当前 `TODO.md` Gate 和最近一条完整观察凭证。若该动作需要三方结论，凭证中必须逐方列出同一 exact pair 的 final verdict；任一缺失、pair 不同、仅中间意见或任一 `REQUEST_CHANGES`，命令不得启动。此项不接受“审核者说已经看过”作为替代。
6. **汇报与记录同源**：用户可见的轮询进度只能由刚写入的观察凭证逐字段生成；不得手工概述或预测。若本轮没有新事实，仍须明确写“第 N 轮、截至本轮检查”及三方状态，禁止为了显得持续推进而重复旧结论。
7. **提交前自检**：涉及审核的每个提交前执行一次只读规范自检：确认本节未被后续文字弱化、当前 Gate 未越权、`SESSION.md` 中没有缺失观察凭证的审核结论。自检失败时不得提交与审核/执行有关的状态更新。

### 审核推进令牌与审核者名册（强制，杜绝跨轮拼接结论）

1. **冻结名册**：每个审核申请在送达前，必须在 `SESSION.md` 写明该申请的三位审核者身份与 tmux pane（ChatGPT、MM、Kimi；经用户明确替换时记录替换人及 pane）。同一 formal root/child pair 的名册不得因“下班/重置/有人回复”静默切换；替换审核者只能由用户明确指定，并使已有观察凭证失效，必须重新送达和完整观察。
2. **单轮推进令牌**：只有最新一条完整观察凭证同时列出冻结名册三方对完全相同 formal root/child pair 的最终 verdict，才构成该 pair 的“推进令牌”。`APPROVE` 令牌只允许推进该申请明确授权的下一动作；含任一 `REQUEST_CHANGES` 的令牌只允许汇总意见；缺件、pair 不同、处理中或检查失败均无令牌。
3. **禁止线索升级**：审核者口头消息、用户转述、远端有新 commit、文件名相似、旧 review、tmux 历史行、输入框文本都只能触发重新检查，永远不能直接生成观察凭证、送达回执、最终 verdict 或推进令牌。
4. **先写后做**：任何会改变工作树、提交、发送新的审核申请、执行代码或更新 Gate 状态的动作前，必须在当前会话重新读取最近观察凭证及冻结名册，并在操作记录中引用该凭证。没有推进令牌时，唯一允许的写操作是修复审核链路、记录失败或撰写不依赖审核结论的新 docs-only 设计；不得整改既有 review 意见。
5. **状态词保留**：`已送达`、`处理中`、`已回复`、`未回复`、`无新增`、`三方齐全`、`可以推进` 均为受控状态词，只能逐字从已写入的同轮观察凭证或推进令牌导出。无法导出时只能写“未检查”或“检查失败/状态未知”。
6. **快进方向机械判定**：fetch 后只可用 `git merge-base --is-ancestor "$before_head" origin/V2` 判断远端是否可从本轮开始 HEAD 快进；返回 0 时必须执行 `git merge --ff-only origin/V2`，而不是反向测试 `origin/V2` 是否为本地祖先。若两端分叉或 merge 失败，本轮为“检查失败/状态未知”，不得跳过远端 review、手工 merge 或把远端提交当作已合并。
7. **formal commit 范围隔离**：审核 formal commit 的变更范围只能用 `git diff-tree --no-commit-id --name-only -r <formal-root>`（必要时对其 parent tree 作 `git diff-tree`）和 `git ls-tree <formal-root> <submodule>` 得出；禁止用未指定 commit 的 `git diff <parent>`，因为它会把共享工作树的未提交 child/训练遗留混入结果。工作树状态只能单独作为 dirty-residue 事实，绝不能作为 formal diff 或 Gitlink drift 结论。

### 审核证据完整性与失效语义（强制，杜绝“检查过但没拿到结果”）

1. **工具输出截断即失败**：任何用于审核状态、远端同步、tmux 送达/回复或 formal-pair 结论的命令，只要工具报告 `truncated`、输出缺页、命令超时、退出码非零，或结果无法逐字段读取，本步骤即失败。不得从已显示的片段、上一轮结果或命令意图补推结果；本轮只能记录“检查失败/状态未知”，随后将缺失检查拆成更小的独立只读命令重做。
2. **一项证据一条命令**：审核观察不得把读取会话、fetch/merge、review 检索、两个 pane capture 与大段文档输出混在单个命令中。每项证据必须有独立、可见且未截断的命令结果；先取得并记录 Git 同步结果，再检索 ChatGPT review，最后分别 capture MM/Kimi。禁止因前一项输出过大而跳过后项或沿用旧结果。
3. **结论与凭证原子写入**：同轮观察凭证必须在所有独立命令成功后一次性写入 `SESSION.md`；任一证据尚未取得时不得先写部分“已回复/未回复/已送达”状态，也不得向用户输出这些受控状态词。凭证提交前必须复读写入后的相关段，确认 formal root、child、三方 verdict 与本轮远端 SHA 均逐字一致。
4. **远端新提交的强制消费**：`origin/V2` advertised SHA 与 `before_head` 不同时，必须先逐条读取 `before_head..origin/V2` 的提交主题，并在可快进时完成并核验 `merge --ff-only`；在此之前禁止扫描 review 后作任何否定性或完整性结论。用户提示的 SHA/文件名只作为本轮精确检索输入，不能替代此同步步骤。
5. **发送回执不可省略**：tmux 申请的“已送达”必须来自同一次 `send-keys -l`、至少一秒后独立 Enter、随后独立且未截断 capture 的三联回执；少任一项即是发送失败，不能进入轮询名册，更不能称已送达。ChatGPT 则必须先确认 Inbox append 的字节数、内容和提交已存在于当前 `HEAD`。
6. **无凭证不得继续**：在当前 Gate 没有最新完整观察凭证或推进令牌时，Agent 不得为了“持续工作”而猜测审核状态、提交状态更新、修改既有审核对象或启动后续 Gate；只可重做缺失检查、修复送达链路，或执行不依赖该 Gate 的只读检查。持续目标不构成绕过此闭锁的理由。
