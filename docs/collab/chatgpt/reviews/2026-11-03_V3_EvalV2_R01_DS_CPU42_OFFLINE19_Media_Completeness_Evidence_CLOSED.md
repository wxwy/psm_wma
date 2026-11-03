# R01 DS CPU42 + OFFLINE19 Evidence 审核

日期：2026-11-03。审核身份：独立 Evidence Reviewer。

**Verdict：R01_MEDIA_COMPLETENESS_EVIDENCE = CLOSED。**
**历史 R01 Fresh Run = FAIL_RETAINED**：原始 exit=1、原 media_summary=MEDIA_INCOMPLETE，不得改写，也不得称修复版已重新完成 GPU Fresh Run。

Formal Root：2d1ad80f89ab4cc0e275ff4341f064954870abdd
Formal Child/Gitlink：c93f2abf4fb27d36176ff8db094379a853cec796
候选分支：v3-eval-v2-media-profile-20261103

本轮 Formal Pair 未变：此前 Root profile 字面量修正已获得 APPROVE_CODE，本次**只核对 DS 新增 Evidence，不重复源码审核**。任何后续审核文档提交 SHA 不是新的 Formal Pair。

## DS 新证据及审核判断

1. 独立 CPU42：DS报告新 clean checkout 的 Python3.13.11 运行42/42 PASS、0失败/错误/跳过，源码前后不变；冻结测试 SHA256 d5f32f29936bebedc94301e7f7a528b8abdcd26d96fa10d5d9b3aa28ca8fab8a 与原代码绑定。作者 CPU42 不替代 DS 独立结果。
2. 原始 R01 产物原/副本：DS报告复制前104/104文件哈希完全相同；副本独立核验后，原始104/104哈希不变；副本仅 media_summary.json 发生了预期更改（其余103/104不变）。
3. 副本在新 Formal Root 上执行真实 generated_media.publish(Store(...))，返回 COMPLETE，episodes=expected_episodes=1，expected=saved=acknowledged=19，errors=[]；并非手工编辑原始失败状态。
4. DS 报告 ffmpeg6.1.1 对19/19实际MP4运行全帧解码（-v error -xerror -i ... -f null -）均 exit0；19/19 Receipt status VIDEO_SAVED，Episode/Task/Generation/Attempt身份一致，实际文件哈希与 Receipt SHA 一致。原 GPU 运行 Core 1/1 valid/success、19 Replan、媒体零丢弃、owned进程清理成功的历史报告与此离线验证相互支持。
5. 可追溯原始证据：DS报告 r01_media_profile/DS_CPU42_OUT 的 gate/invocation/junit 与 R01_reconciliation/evidence 的 publish_report.json、receipt_binding_check.json、ffmpeg_decode.log、original_and_copy_integrity.json，以及 original_before.sha256 和 copy_after.sha256。本审核人**未直接连入 DS 服务器读取这些原始字节或运行 CPU/GPU**，因此 Evidence 结论基于 DS 的独立报告，而不是自称亲自做了复核。

## Gate 区分与后续边界

- Profile 修复 Code Gate：APPROVE_CODE（原有结论）。
- DS 独立 CPU42：PASS（DS报告支持）。
- 真实媒体 OFFLINE19：PASS（DS报告支持）。
- **R01 Media Completeness Evidence Gate：CLOSED**。原数据保存正确，Profile 汇总假阴性已由修复代码在真实19条数据上闭环验证。
- **历史 R01 Fresh GPU Execution Gate：FAIL_RETAINED**。旧进程 exit=1 的事实不更改；新代码从未进行新一次 Fresh GPU exit0 Run，不能把两个结论混为一谈。
- 不要求重复 GPU 只为确认已保存的19个视频；若后续 Gate 明确需要“新 Formal SHA 下 Fresh Run exit0”，应单独得到 Owner 授权。
- 本轮不授权正式 V3 合并、900 Episode、GPU重跑、实际B2压测，也不允许改动历史 R01、H2/H3、out2、No-TTT、训练/Checkpoint 或其它在跑任务。DS按原指令 STOP。

本次仅新增 review/Inbox 文档，Root implementation/Child/Gitlink 不变。