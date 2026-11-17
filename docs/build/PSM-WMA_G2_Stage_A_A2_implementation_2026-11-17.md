# Issue #54 / PR #55 — Stage A A2：生产并行 View VAE

日期：2026-11-17（CST）。本文件为 Codex 实现合同和复验入口；作者 CPU 结果见自有 evidence，**不构成 GPT 原生 / Wan / GPU 验收**。

## 起点和边界

从 `d96d89313473bb7e398ac53ee079044b785c760d` 的审核资料继续；其中批准的 A1 实现仍是 `8e11f27bb8e6e8d29c353a56acd0e15da1ddb2a8`。其 431 项服务器回归及三条原始反例的既有批准保留，不改写原报告。A2 固定实现 SHA 由后续 handoff 标明，不能用该 A1 批准代替 A2 批准。

分支 `codex/g2-stage-a-offline-issue54`；继续原 Draft PR #55，stacked base 为 #53 分支的 `d36caf0fc35f3a84b739dc8df58ab992eb9f6917`。Cosmos Child/Gitlink `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`；观察 V3 `fe1089fb925d86697bebd9bef18608d9c9eae87b`、nav G2 `70eb7b447e65d793b0ebe18b258291ce46f057c1`，均不修改。不合并两个 Draft，不安装依赖/创建环境，不访问私有服务器，不运行 GPU、权重、真实 F27、全量生产、state15、联合对齐或训练。

语言字段/精度/预算、画布、dtype、GPU 分配和生产并发仍为候选。下面涉及真实 Wan 的命令仅供 GPT 固定版本独立验收，不是 Codex 本轮执行记录。

## 复用和实际文件职责

- `encoding.py` 的图像预处理、受控来源导入和原生单帧 B=1/T=1 Encode1 原样复用；`source.py` 旧 v1/v2/v3 completed-package scanner 原样保留。
- `builder.py` 将已有有限 FP32 CHW 检查/存储转换提取为 `encode_record()`，同时供旧补编码和事件消费者使用；新来源通过独立适配分派。增加内部 record provider 以重用已经 ACK 的数值，不复制 VAE。流式收尾的 `assembled_records` 与实际 `encoded_records` 分开。
- `sealed_source.py` 验证新 profile、空间 readiness 和最终 owner，生成 #53 相同的数值计划；不恢复/伪造旧 COMPLETE。
- `streaming.py` 提供进程间持久队列、有限容量、独立消费者、ACK、source offer/refill、compact owner 对齐及清理。只读训练侧不导入它。
- `storage.py` 仅增加明确 schema 下的来源文件对和 PNG-disabled 规范路径；原逐 View 文件格式、普通读取按需 mmap/LRU 不变。读索引不导入 renderer、VAE 或 producer。
- `production.py` 协调同目标锁、完整数值/来源核验、最终 profile 事务及 `_spatial_inputs` 安全清理。
- 原 `episode.py` 在 FULL 和 ARROW_ONLY 两条最终像素分支接线；`atomic_6views_run.py` 注册 job、传递 spool/job、封存来源。旧调用不指定 profile/spool，保留旧路线。
- 原 build/verify CLI 继续使用；新增薄 CLI `tools/g2/consume_spatial_view_vae_events.py` 常驻消费。没有在线 daemon/Policy/训练依赖。

## 生命周期与不循环的完成语义

```text
最终材质/背景 -> clean PNG（不可变） -> 可选独立副本 overlay -> _w_rbs PNG（不可变）
    -> final-pixel event -> bounded pending PNG BLOB -> B=1 Encode1
    -> fsync 数值 chunk + 完整数值/来源检查 -> SQLite FULL-sync ACK（释放 pending BLOB）

原 producer 完成 SG/投影/成员/任务/语言/owner -> spatial_source.json
    -> SPATIAL_SOURCE_READY.json -> source offer / 补齐缺失事件 -> strict seal
    -> 按最终 compact owner 组装每逻辑 View 一个 .pt -> cache manifest/COMPLETE
    -> 完整 cache/source 核验 -> profile 发布事务 -> episode COMPLETE
    -> 持久 release 记录 -> 仅清理自己的临时 PNG / chunks
```

`SPATIAL_SOURCE_READY.profile_complete=false` 恒为来源阶段含义，不会被改成最终完成。最终 manifest 与 cache 不互相哈希：cache 绑定不可变 `spatial_source.json` 和 readiness 的 SHA；profile 的 VAE receipt 绑定已完成 cache。#53 header 的历史字段 `manifest_sha256 / complete_sha256` 在新 source schema 内分别指这两个明确命名的来源文件，不能据此声称 episode COMPLETE 已提前存在。

完整 cache 验证必须核对全部 owner、state 映射、View 集合、recipe、tensor shape/dtype/有限值、文件和逐条 tensor hash。`verified=true` 自身不是批准依据。原 source、SG、图片、语言和成员证据不因 VAE 成功而重写。

最终 profile 更新有 `VAE_PROFILE_PUBLISH_PENDING.json` 事务证据，包含精确的下一版 manifest SHA、source ID 和已核验 cache receipt；先持久化此记录，再原子替换 manifest，最后发布 COMPLETE。仅有该匹配证据才能在不要求完成的恢复路径中接受“manifest 已准备、marker 尚未落盘”；要求完成时仍拒绝。正常完成后删除事务记录；之后丢失 COMPLETE 必须报损坏，保留 A1 既有负例。

## 事件、身份和 compact

事件含 episode key、完整逻辑 View ID、canonical View/variant、PNG SHA、最终 clean/marker phase、size、原始来源 fingerprint、profile ID 和 pixel record key。携带独立复制的最终 bytes；入队时校验 PNG、尺寸、身份和 phase。没有选择图或像素可见性过滤。

FULL 发布实际物理资产；ARROW_ONLY 只发布标识版；REUSE_ALL 不发布新像素。所有有效方向、所有 Room/Island、clean 和 `_w_rbs` 均纳入。无有效方向没有 payload。最终目录路径仍为 `vae_cache/<完整view>.pt`，每个文件保存该 view 的所有版本。内部临时数值 chunks 不属于最终数据格式。

pixel record key 是 View + PNG 内容；数值 chunk key 再绑定 recipe，不绑定语言/发布事务。共享 spool 内相同数值输入可跨 publication scope 复用；保留各 job 的独立来源 ACK。完成后可清理无其他未完成 job 引用的 chunks，不建立永久跨数据集检索系统，也不无条件跨旧 recipe 续写。

最终 row/record_index 由封存的 `views[view].owners` 和 `state_records` 决定，不使用到达顺序作为索引。每个 owner 必须找到对应的 descriptor 和 durable ACK；相同像素允许对应多个几何 owner 的数值记录。旧 clean 引用、ARROW 的新 marked owner、当前成员版本与历史图片 owner 独立保留。

## 容量、故障和 writer

候选默认：pending 事件 32，PNG BLOB 总计 256 MiB，数值 staging 4 GiB，事件/job ledger 各不超过 100,000 行；每条 descriptor/scope 限 16 KiB。SQLite 页、索引和事务 journal 另有开销，不能把 BLOB 计数当磁盘实测峰值。数值预算额外预留文件头，不无限增加 RAM 队列。最终组装沿用原 #53 每次一个 View 的方式；没有逐记录重写整个 View。

`--vae-source-max-bytes` 另行限制每 episode PNG-disabled 的封存临时输入，默认 256 MiB，与 pending 队列预算不同。超过此有限输出预算明确失败并保留原 renderer 输入；不能把该值宣称适合所有长 episode。生产参数须由真实样例和磁盘预算冻结。

消费者慢时 enqueue 等待容量，有限超时明确延期；不丢弃源图。VAE 失败、spool 不可用或容量超时不会把合法 RGB/SG 改成失败数据：producer 写 `VAE_DELIVERY_PENDING.json`，继续空间产物封存，offer 完整 source。消费者显式 retry 后，从不可变来源按有限容量补齐未入队事件，再 strict seal；不重渲染。像素/来源/phase 冲突仍拒绝，不能用“延期”掩盖几何或来源错误。

一进程一常驻 encoder，跨 episode 复用。CLI 对整个服务持有 consumer flock；同一个 spool 不启动多个模型副本竞争。已就绪的 episode 优先收尾和释放结果，不等待所有 renderer 的队列都空。queue/root、目标和路径拒绝 symlink、路径逃逸、不同 scope/recipe 冲突。

同目标 streaming finalizer 与新 posthoc 共用 `.stage-a-vae-lock-<episode>`，再复用原 `vae_cache/.build.lock`。竞争写入明确拒绝。失败后的合法逐 View 文件不覆盖；完整审计后 resume。编码后、ACK 前崩溃：输入 BLOB 尚在，已 fsync chunk 审计通过后重用并补 ACK；错误 chunk 拒绝，不覆盖。cache 完成、profile marker 前崩溃和 profile 完成、job ACK 前崩溃分别恢复，不重复数值编码。

清理要求 final profile 和数值完整核验通过。PNG-disabled 临时输入先生成 `VAE_INPUT_RELEASE.json`，绑定 source ID、cache manifest SHA 和每个临时路径/原 SHA；cache 内每个 owner 仍保留原始 PNG hash。删除中断可幂等继续，缺失输入仅在完整数值/owner 证明下视为合法释放。释放临时 PNG 后，普通 verify 仍检查封存 hash 与数值 owner；显式 reencode 必须另有相同真实输入，不能由 latent 反推替代原图。保留 PNG、SG、原生输入和源服务器文件不在清理集合中；原 renderer 工作目录沿用既有 keep_work 政策，异步 pending 时保留。

## 精确 CPU 复验

只用既有环境，单 CPU / FakeEncoder / 合成输入，无网络、权重或 GPU：

```bash
cd /path/to/fixed/psm_wma
ISSUE54_PYTHON=/path/to/existing/python \
ISSUE54_RUFF=/path/to/existing/ruff \
ISSUE54_A2_OUT=/path/to/fresh/cpu-evidence \
bash docs/collab/codex/evidence/2026-11-17_issue54_a2/commands.sh
```

脚本冻结 CUDA_VISIBLE_DEVICES 空、COSMOS_DEVICE=cpu、Root/Child PYTHONPATH；分别执行原 283、全 Stage A、关联 45 项，记录原始 log/JUnit、源码运行前后 SHA、431 个基线测试身份、静态与 CLI 结果及协议示例。缺原有依赖则记 skip，不安装、不以替身冒充 PyArrow/MuJoCo/Pandas。

协议示例脚本 `docs/collab/codex/evidence/2026-11-17_issue54_a2/protocol_probe.py` 复制完全相同的合成封存来源，构建流式/事后两套缓存，比较逻辑 index、metadata 和 tensor，输出 `protocol_example.json`。其中 FakeEncoder 的 shape 和数值不是 Wan 实证。

PASS：零 failure/error；旧测试身份不丢失；所有需执行的故障路径拒绝/恢复正确；源码前后指纹一致；保留的缺依赖项及尚未运行项单列。FAIL：遗漏 owner/View、混源/混 recipe、丢输入、无 ACK 清理、提前 COMPLETE、来源或 tensor 损坏被接受。运行结果见自有 evidence `final/gate.json`；GPT 的真实 Gate 仍 PENDING。

## GPT 独立服务器样例入口（本轮 NOT_RUN）

先固定新 Root SHA、未改 Child，使用原 PSM 解释器，检查资源和固定 Root/Child import origins。先做新版 producer 的四条既定样例及双变体/元数据检查，再进行获准的真实 VAE 数值/性能实验。不得借用旧缓存 recipe 或旧带标识 floor_top 来通过新语义。

已有旧 completed-package 补编码命令不变。新 profile 补算沿用同一 build CLI，要求原 profile 已声明 view_vae=true 及 SPATIAL_SOURCE_READY，无需 episode COMPLETE；关闭 VAE 的 profile 不在补算时被隐式升级：

```bash
# 需另行授权真实 VAE；下面变量由 GPT 实查后指定。
"$PY" -m tools.g2.build_spatial_view_vae_cache \
  --dataset-root "$STAGING/tasks/$TASK/episodes/$EPISODE" \
  --weights "$WEIGHTS" --cosmos-root "$FIXED_ROOT/cosmos-framework" \
  --device cuda:0 --height 256 --width 256 --storage-dtype float32 --execute --resume
"$PY" -m tools.g2.verify_spatial_view_vae_cache \
  --dataset-root "$STAGING/tasks/$TASK/episodes/$EPISODE" --recipe-id "$ACTUAL_RECIPE_ID"
```

独立 consumer 先初始化固定 recipe/spool（descriptor only），再显式 execute；两次 flags/环境应一致。原 producer 原有人工启动、GT/F27、immutable plan 参数保持，额外传 `--vae-spool "$SPOOL" --vae-source-max-bytes 268435456`，episode 子进程接收注册 job。无 spool 时仍可来源封存后事后补编码。

```bash
"$PY" -m tools.g2.consume_spatial_view_vae_events \
  --spool-root "$SPOOL" --weights "$WEIGHTS" --cosmos-root "$FIXED_ROOT/cosmos-framework" \
  --device cuda:0 --height 256 --width 256 --storage-dtype float32 --initialize
# 独立执行端，复用同一有限 spool/recipe；此行会真正加载模型。
"$PY" -m tools.g2.consume_spatial_view_vae_events \
  --spool-root "$SPOOL" --weights "$WEIGHTS" --cosmos-root "$FIXED_ROOT/cosmos-framework" \
  --device cuda:0 --height 256 --width 256 --storage-dtype float32 --execute
# 明确重试保留的失败 job：上条 execute 命令再加 --retry-job "$JOB_ID"
```

consumer idle 后退出：0=没有未完成/失败 job，75=仍有未完成来源/事件，2=执行/来源错误或失败 job；initialize 的 0 仅代表初始化，不代表数据完成。producer 75=空间来源就绪、全 profile 尚未验毕；dispatcher 允许 consumer 在读取75之前已完整核验完成，但仅有 prepared manifest 不算 DONE。

真实验收需记录相同 renderer 配置下 PNG/尺寸/集合、两变体独立 owner、成员/任务/selection、同输入 bytes/recipe 的实际 latent 对照、终端恢复、队列/磁盘峰值、吞吐/耗时与读取 P50/P95。上述 GPU 数值和性能目前均 NOT_RUN，不由 CPU 的 max_abs_error=0 替代。两 Draft 保持未合并，training_ready=false。
