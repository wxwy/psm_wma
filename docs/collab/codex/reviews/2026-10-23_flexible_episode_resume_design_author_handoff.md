# Flexible Episode Resume — 第一阶段设计与 CPU Gate 交接

日期：2026-10-23（Asia/Shanghai）。**REVIEW：提交 GPT 设计审核；生产 Resume 尚未修改。**

| 项目 | 精确版本 |
| --- | --- |
| 设计 / 隔离 Prototype Root | `44f0953ac75591d7e60394df6337a6ed133f3f08` |
| Child / Gitlink（未改） | `813a550dab5d6b5b5e3be90d38bb97527956b4dc` |
| Owner 需求基线 | `cc7820bee1a73bd2bb2078cb7f00239944f66d37` |
| 既有生产实现 Root（未改） | `e6a970caba4bdc77f7d9b56a6a8fbcdafe57f1e0` |

本轮遵循需求契约的“两步交付”建议，完成技术设计、非破坏性 legacy 摄入方案、fake-data CPU 原型及复核。仅新增 `tools/v3/episode_resume_prototype/` 与设计/交接文档、SESSION/TODO。生产 scripts、Child、配置与 Vendor 相对基线差异为空；没有实现新的生产调度入口，也没有启动真实模型、Action Server、仿真、GPU 或访问真实 DCP。运行中的18任务与 G1 工作树均未同步或更改。

## 设计交付

完整方案：`docs/collab/codex/designs/2026-10-23_V3_RoboCasa_flexible_episode_resume_design_r1.md`。

- 四参 model_identity 与每次 invocation_plan、原始 EpisodeRef 分层；不把旧文件换贴新 digest。
- 旧完整 Episode 按原身份/Seed/runtime/媒体策略验证；支持 FAILED/RUNNING Task 内的闭合前缀，runtime_error、半成品、坏核心证据不复用。
- 原始来源 locator 与证据快照分离；跨 attempt / logical slot 稳定去重，不按成功择优。Scanner 诊断进入启动和结束记录。
- 当前任务集合与请求集数决定统计；3→5只补2、8→5排除3，旧结果保留。当前 Worker/cleanup 错误即使覆盖已满仍不 COMPLETE。
- 当前媒体 coverage 从原 availability/实际预测数重算，旧 none/first→all不强制重跑，all→none不沿用旧 missing缓存。
- 请求 Seed family 与实际 effective seed 都记录；混合/未知环境与来源显式标识，不把旧 Seed结果说成新 Seed执行。

两项需要 GPT 审阅后才能接生产的技术选择：

1. **Checkpoint 新强基线与 legacy 弱桥接。** 新基线流式读完整模型权重并计算 SHA；旧历史只核 metadata SHA+完整 shard stat，保留 historical_payload_sha256=null，不事后伪造旧权重哈希。完整读取有存储 I/O成本；结构头/哈希均非 DCP load通过。本轮只对微型合成文件验证。
2. **新增 Episode 独立派生环境 Seed。** 固定 sampler_version、requested_seed、Task、logical_slot决定实际 Seed；重试/GPU/顺序无关，单集 fresh environment +1次 public reset，原 source physical ep0单独映射 logical3等。明确不是旧随机流连续恢复，也不保证物理场景永不重复。该候选的 Seed family标签不等于传给环境的 literal数字，完整实际值必须可见。

## 作者 CPU 与源码检查

完整 Evidence：`docs/collab/codex/evidence/2026-10-23_flexible_episode_resume_design_author_cpu/`。

最终全目录一次 CPU Gate：**161 passed，0 failure/error/skip**，无 subtests。四组：模型身份45、Episode核心/legacy45、场景采样34、当前计划/统计/lease37。Ruff0.12.7 check、format --check（9个 Python）、compileall 通过；源文件哈希与 exact commit绑定；生产路径 diff为空。

输入为临时 tiny Git/DCP/JSONL/MP4/PNG、fake env及 validated-record替身；复用了真实未改 legacy identity helper、原始审计/Local cleanup/media validator与 owned-process helper。验证实际核验的2个旧schema Episode→计划补3→假结果汇总，**不等于新 Queue已经执行了3个 Episode**；模型桥、锁与计划还不是正式入口全链，后续实现必须补 CLI/调度/源引用完整接线的 CPU Gate。

命令与 JUnit/日志、内部只读复核、source_checks、设计/prototype diff及 SHA256 在 Evidence。可在独立 CPU 环境复现：

```bash
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 \
python -m pytest --noconftest -c /dev/null -p no:cacheprovider -q \
  tools/v3/episode_resume_prototype
```

内部复核曾发现同 source快照 / 同logical slot双计和旧媒体覆盖缓存问题，已增加负例并修复；其意见不冒充 GPT/DS独立裁决。旧进度/视频交付的256项与本轮161项分别绑定各自目标，不合并成新的全仓生产CPU通过数。

## 请求与停止边界

请求 GPT 对本次**设计+非生产 Prototype Root44f0953a / unchangedChild813a550d**审核，明确上述模型桥接、Seed采样、逻辑/物理引用与迁移顺序。审核后再开始最小生产实现，随后独立 DS CPU Gate与新的 exact Implementation Pair审核。

Codex 在提交/非 force推送/回读及 canonical Inbox交接后停止。不更新当前运行中的评测或 G1，不要求 Owner暂停；本阶段不授权 GPU、新仿真或实际训练恢复。
