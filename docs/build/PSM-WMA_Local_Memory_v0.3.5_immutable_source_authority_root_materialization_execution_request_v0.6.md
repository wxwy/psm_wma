# Authority-root one-shot materialization execution request v0.6

**日期**：2026-09-13
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`
**状态**：docs-only replacement request；待同一新 formal pair 三方审核。

本 request 完全替代 v0.5。唯一 runtime authority 是 annex v0.6 及其同提交的 immutable payload v0.6。
它只落实 v0.5 三方意见：后置 annex 输入改为内联受 SHA 约束的历史 bytes；FD=3/4/5 同号安全 handoff 和
exact close-set；transactional add/ownership cleanup/`ROLLBACK_INCOMPLETE`；以及 retained no-follow ordinary
parent route/config authority。候选 parent、Gitlink、actual argv、bootstrap、环境和禁止范围均未改变。

在三方对新 exact root/child 全部给出
`APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT` 前，禁止运行 payload 或任何
materialization、source/checkpoint I/O、JSON/worktree/index/candidate/ref/evidence、collection/receipt/
publication、child、GPU、训练、评测、推理及 LIBERO4IN1；否则唯一 verdict 为`REQUEST_CHANGES(file:line)`。
