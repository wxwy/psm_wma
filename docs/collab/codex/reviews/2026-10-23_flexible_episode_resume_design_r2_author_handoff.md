# Flexible Episode Resume r2 — 作者交接与增量设计审核申请

本次只整改 GPT 对第一阶段 Design/Isolated Prototype 的三个 blocker，尚未接入生产 Resume。

| 对象 | 精确身份 |
| --- | --- |
| 新 Formal Design/Prototype Root | `1bf88fa624e58e521caa2213f2b1a44bf2f2871d` |
| Child / Gitlink，未变 | `813a550dab5d6b5b5e3be90d38bb97527956b4dc` |
| 开发基线 / 上次 verdict handoff | `50ed1fdc87d1380be6b95219ea12b9d379f7edc7` |
| Owner 冻结契约 | `cc7820bee1a73bd2bb2078cb7f00239944f66d37` |
| 旧 r1 Design，被本次增量替代 | `44f0953ac75591d7e60394df6337a6ed133f3f08` |
| 最后生产源码 Root，未变 | `e6a970caba4bdc77f7d9b56a6a8fbcdafe57f1e0` |
| Vendor，未变 | `1ac174585293ed998ffc9cf73e47439798cf6f6c` |

隔离分支：`v3-flexible-episode-resume-design-r2-20261023`；已非 force 发布 V3，Root 与 Gitlink 远端回读一致。
后续 Evidence/Inbox 文档提交不代替上述 Formal Design SHA。

## 三项差异

| Finding | r2 行为 | CPU 证据 |
| --- | --- | --- |
| HIGH-01 | Parent按Task有效历史选模式。全新/新增Task保留 literal Seed、一个环境、连续reset；只对真正补缺使用派生Seed。execution_batches显式保存环境批次与physical/logical映射 | fresh5 fake trace等同原协议；4→18新增14Task不派生；partial3→5、seed变更、隐式模式拒绝；Parent混合旧/新Task组合 |
| MEDIUM-02 | COMPLETE先按原trials/runtime/media跑原完整validator，再buffer所有Episode core；矛盾整Attempt隔离，direct API同guard。RUNNING/FAILED闭合前缀保留 | COMPLETE2/5、坏/缺清理、末集Local ack错均无前缀泄漏；合法5/5及FAILED前缀；原文件不改 |
| MEDIUM-03 | 从已验来源的连续ID缺口、只读持久reservation/progress重建pending；可选内存hint不能造槽，当前缩小不丢pending | 无pending参数的disk/独立OS进程重建、{0,1,3,4}补2、尾部start、shrink-expand、多次失败新Attempt、映射冲突 |

新增 `reservation_recovery.py` 只读投影格式尚不是生产目录/旧JSONL发现器。
持久completed声明仅证明槽分配，不能代替Episode verifier。原型没有自动信任外部 `verified:true` 的生产入口。
Task级process_cleanup共享观测与Episode稳定身份分开，但COMPLETE每次仍重验完整清理。

## 实际作者 CPU 结果

本次只运行四组变更测试，一次合并运行：**185 passed，0 failure/error/skip，2.93秒**。

| 模块 | 本次通过 |
| --- | ---: |
| scene_sampling_test.py | 53 |
| episode_evidence_test.py | 53 |
| reservation_recovery_test.py | 34 |
| plan_test.py | 45 |

Ruff0.12.7 check、format --check及11个Python文件语法检查通过。
生产scripts/configs/Child/Gitlink/Vendor、model_identity及旧r1设计/Evidence无差异；Child clean。
JUnit因隔离`-c /dev/null`的classname为空，Evidence检查器按唯一test函数名映射四个源码文件计数，无二次运行或补造测试。
原r1的161项记录保留其旧SHA；未变的identity45本次未重跑，不能将两轮计数拼成新版本全量通过。
内部只读作者团队复核未发现本次三项的新阻断；不替代GPT正式verdict或DS独立验收。

完整日志、JUnit、命令、差异、静态检查器、源码哈希、远端回读与内部复核：
`docs/collab/codex/evidence/2026-10-23_flexible_episode_resume_design_r2_author_cpu/`。
新设计：`docs/collab/codex/designs/2026-10-23_V3_RoboCasa_flexible_episode_resume_design_r2.md`。

## 请求与停止边界

请求GPT只对本次新Design/Prototype Pair做fresh incremental review，裁决三项是否闭合，以及是否批准后续最小生产接线设计。
生产 admission/旧JSONL自动发现/原子持久分配/Worker调度与最终summary的完整CPU管线仍是下一阶段独立实现Gate。
模型完整哈希的真实I/O成本与最新invocation发现也留待该Gate，不在本批扩大整改。

本次没有启动GPU、Action Server、模型或仿真，没有访问真实DCP或改动活动评测/G1。
不重新训练iter12000，不重跑已完成20集。提交Evidence与canonical申请后停止，等待GPT；不自行进入第二阶段。
