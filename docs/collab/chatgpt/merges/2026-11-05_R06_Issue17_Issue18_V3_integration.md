# R06 — Issue17 Streaming + Action Encode/Decode 合并到 V3

- 日期：2026-11-05；Owner 授权将已独立验收的集成版本合并到 V3。
- Root 父提交：最新 V3 `8586b30cdfef802cff56d1463e989cb7b62559b8` 和 Issue17 `551b03621507dde52303f54290d4fea89d66e8da`。
- Child merge commit：`1ca308055fc41fb69efaeb9efaa23808f164a18e`，父提交 `82fa270e8cdb76b3e1a4e94adf0c7ce2b497884e` + `b3098008375c275a36dd2f50cbaf757bedf493ea`。
- Child Git Tree `21b0e3987546e1f85511be760bca9ee9f7a1974f`，与 R06 真实H100验收的 Child Tree 完全一致。
- Root 从 Issue17 原正式Root继承全部25项源码、测试和设计/请求文档，保留当前V3 SESSION、TODO、CODEX_INBOX、所有历史review；不包含G2未审核增量。
- Source Gate：Issue17 Streaming `APPROVE_CODE`，Action Encode `APPROVE_CODE`，Issue18 Decode `APPROVE_CODE`。
- 集成版GPT独立CPU：Root `3704ccee3cc2b2120d38922f2c89645e7390c0e4` + Child `1fab59779c2f24178efdc2caa5021e277af70d74`：869/869完整CPU、77/77 Action CPU 均PASS；CPU使用隔离pidfd测试环境兼容层，未改生产源码。
- 实际R06 H100 RoboCasa：iter27700原权重逐shard SHA256与R04匹配；18 Task × 2 EP，M16/B8、Action H16/15D、Local-TTT required；36/36有效，成功29/失败7，零Invalid/Interrupted/Pending，`clean_execution=true`，34/34进程回收，零Dynamo重编译上限错误；原始证据保留服务器。
- 本次只合并代码，不自动启动新的900EP；不修改旧R04/R05/R06的任何Core；M/B Resume严格一致性不变。
