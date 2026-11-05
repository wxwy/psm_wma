# GPT V3 集成合并核验 — Issue #17 Streaming + Action Encode/Decode

**日期**：2026-11-05  
**正式增量源码结论：`APPROVE_CODE`；发布核验：`PROMOTION_VERIFIED`**。仅对下述精确实现Pair和对象/来源相等性有效。  
**Root implementation**：`95f756584a925ad1eba2d2f20c478c56d4096ed2`（官方`V3`）。  
**Child / Gitlink**：`1ca308055fc41fb69efaeb9efaa23808f164a18e`（官方`v3-local-ttt`）。

## 1. 实际GitHub对象与来源核验

- Root merge父提交为当前V3 `8586b30cdfef802cff56d1463e989cb7b62559b8` 与 Issue17 正式实现 `551b03621507dde52303f54290d4fea89d66e8da`。本轮 Root Tree `5ebb9d4811f67605417f8d3e771a6ab8d90e23bc`。
- Child merge父提交为 Issue17 `82fa270e8cdb76b3e1a4e94adf0c7ce2b497884e` 与 Issue18 `b3098008375c275a36dd2f50cbaf757bedf493ea`。新Child Tree **`21b0e3987546e1f85511be760bca9ee9f7a1974f`**，与先前已经独立测试、真实H100/RoboCasa运行的本地Child `1fab59779c2f24178efdc2caa5021e277af70d74` Tree **完全一致**。
- Root合并从已审核的Issue17来源引入25项文件（包括相关设计/需求）：源代码和测试路径的Blob来自此前经过GPT独立CPU验收的Root `551b0362` 代码内容；唯一新增文件为本次合并记账 `docs/collab/chatgpt/merges/2026-11-05_R06_Issue17_Issue18_V3_integration.md`。
- Root相对合并前V3共变化27路径：25项Issue17来源、一个Gitlink和一个合并记账。未改`SESSION.md`、`TODO.md`、`CODEX_INBOX.md`，保留V3已有审核/状态文档。未引入G2生产改动。
- GitHub远端核验：官方Root`V3` HEAD精确为`95f75658`，Child`v3-local-ttt` HEAD精确为`1ca30805`，Root Gitlink精确指向其Child HEAD。均为`force=false`和`expected_sha`受保护的fast-forward更新。

## 2. Gate与Evidence对应关系

- 先前独立源码Gate：Issue17 Streaming`551b0362/82fa270e` `APPROVE_CODE`；Action Encode`c9fa60b7/4e9c8104` `APPROVE_CODE`；Issue18 Decode`f4871059/b3098008` `APPROVE_CODE`。
- 本地隔离集成正式测试源码：Root `3704ccee3cc2b2120d38922f2c89645e7390c0e4` / Child `1fab59779c2f24178efdc2caa5021e277af70d74`。GPT独立完整Streaming CPU **869/869 PASS**、Action CPU **77/77 PASS**；源码前后不变。完整CPU869使用已披露的Python3.13原生pidfd系统调用兼容层，未改生产源码与断言。
- R06真实RoboCasa：原`iter_000027700`八个model shards和metadata SHA256均与R04原始记录相同，18个真实任务×2 EP，M16/B8，Action真实`[16,15]`，Local-TTT required，EGL GPU4/5、Policy GPU6/7。**36/36有效Core**、29成功/7任务级失败、`invalid=0`、`pending=0`、`results_qualified=true`、`clean_execution=true`、进程回收34/34、零`FailOnRecompileLimitHit`，真实Native Batch覆盖B1–B8。运行exit0。
- 同一Child代码Tree已经完全一致。Root的业务源码/test Blob来自已审核正式Pair，其他变化是Git历史、账本与Gitlink。因此**不是未经证据支持地把两份通过报告相加**；结论基于内容对象级交叉校验。
- **说明**：未用本次远端`95f75658/1ca30805`重新启动一轮900EP或完整GPU测试；这里认可的是内容相等性与之前独立集成测试结果的对应关系，不虚称已经独立重跑远端SHA下的900EP。

## 3. 发布完成与停止条件

`APPROVE_CODE`：新的准确Root/Child集成Pair源码与已独立实机验收版本的生产内容相同，未发现本轮Git对象合并引入新阻断项。官方发布已完成且双远端回读通过。

**本次授权范围**：合并到V3；**未授权**自动启动正式900EP、修改R04（648有效Core）/R05（12有效Core）/R06（36有效Core）旧Run、对旧Run跨SHA普通Resume、更改`sims_per_gpu`/`max_infer_batch_size` Resume identity、合并G2或修改训练权重/数据。以后如有新生产diff应另建Exact Pair增量Gate。
