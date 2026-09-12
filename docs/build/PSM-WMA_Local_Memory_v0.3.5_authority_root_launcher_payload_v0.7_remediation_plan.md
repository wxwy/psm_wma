# Authority-root launcher payload v0.7 remediation plan

本文件只落实 `80132197.../93a89ba...` 三方最终意见，不执行任何 launcher。

1. `worktree add` 改为显式 mutation-boundary helper：无论 native Git 返回非零或 post-check 失败，均先
   no-follow 检查 CLEAN 与 `worktree list --porcelain`；两者均证明 absent 才返回 ordinary FAIL，任一
   残留或无法证明 absence 均为 `ROLLBACK_INCOMPLETE`。成功路径立即 retain CLEAN directory FD/identity。
2. route snapshot 在普通 `.git` 目录下额外 no-follow 检查 `.git/commondir` **必须 absent**，并于每个
   native Git 前后重验 absence；插入、替换或读取失败一律 fail-closed。
3. handoff 在 writer close、reader open、dup2 后均重新 `lstat` backing path；path/reader/target
   `(dev,ino,size)` 必须相同，mode 必须严格 `0600`，raw digest 必须相同。删除 v0.6 中 inert 的错误
   actual-argv base64 副本，仅保留被 SHA 复算的 exact lexical bytes。
4. 新增 temporary-only witness 文件：同/异 FD、extra FD close-set、pathname same-bytes replacement、
   mode drift、commondir insertion/replacement、route/config replacement、nonzero/partial add、post-add
   drift、foreign clean root、cleanup success/failure。每个 fixture 使用临时 Git repo，禁止 `/disk/rl/psm_wma`
   root、source/checkpoint 与 production paths。

以上完成后才可生成新的 immutable v0.7 payload、annex/request，静态测试、提交并重新三方审核。
