# Flexible Episode Resume — production HIGH-01 r2 作者交接

Implementation Root：`6151e0712f28ace5d92258a8feb31fa8f1ee81c1`；Child/Gitlink：`813a550dab5d6b5b5e3be90d38bb97527956b4dc`（未变）。基线 `6e10c8d461ecc5f49e05da932a2d925e9ad62ef3`，针对 GPT252d823c/813a550d REQUEST_CHANGES 的新 HIGH-01。已批准 Design1bf88fa6与Owner契约cc7820be不变，不重新打开旧设计finding。

只修改终态 Progress 补算与调用侧：流式二进制读取，64MiB总字节、4096字节每条、2×reserved episodes行数、100000 Episode/逻辑ID上界；UTF8严格解码，禁止重复字段/非有限数，要求换行提交及原digest/Attempt/按序start-end。读前后文件stat见证变化也拒绝。文件损坏不推测该来源已执行集数；按Job记录final_progress_read错误，保留其它来源计数，继续发布最终PARTIAL/非零状态。合法start但未闭合仍计执行/失败，尚未创建进度的Worker启动失败不伪造Episode。

新增9项真实默认CLI终态注入（UTF8、截断、文件超限、行超限、重复字段、错误身份、乱序、NaN、合法start）及1项打开前文件超限拒绝的直接证明。逐项验证最新摘要和不可变最终报告均PARTIAL、remaining=5、准确executed/failed、保留原Job错误及回收见证、损坏原文件字节不变。旧16项集成和其余四组保留。

CPU：旧CLI运行新用例8failed/1passed；修复后10passed；最终冻结五组 **164 passed, 72 subtests passed in 1155.14s (0:19:15)**，0failure/error/skip。JUnit声明tests=236，实际164个testcase元素，成功subtests不单列元素。Ruff0.12.7check/format及语法15文件通过，精确源码hash与提交Blob绑定。这里是作者Evidence，不是DS独立CPU/GPT正式验收。

Evidence：`docs/collab/codex/evidence/2026-10-24_flexible_episode_resume_progress_r2_author_cpu/`（原始日志/XML用gzip无损归档、命令、完整五组JUnit、静态检查、Diff、源码hash、远端回验、文件校验清单）。前一版本154+72证据保留原SHA，不叠加本次统计。新增测试采用已有CPU fake-model/Kitchen harness；默认CLI/Local客户端/进程及最终证据链保持真实调用。没有真实模型/GPU/Kitchen/DCP/训练操作。

请求GPT仅对新Pair的HIGH-01增量复审；通过后DS_PRO在clean detached worktree独立执行同一五组及静态检查。Child/Vendor、四参数模型身份、Seed/复用规划、Local-TTT、G1、iter12000历史20集及活动工作树均未修改。Codex提交后STOP；不授权仿真或训练。
