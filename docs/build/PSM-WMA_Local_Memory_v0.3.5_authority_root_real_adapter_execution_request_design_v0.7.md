# PSM-WMA v0.3.5 Authority Root PASS 线性化设计 v0.7

**日期**：2026-09-12  
**状态**：docs-only；待三方设计复审。  
**Gate**：`G0-R09-B-TTT-V035-PASS-LINEARIZATION-DESIGN`

本文件 supersede v0.4--v0.6 中将“public `<evidence>.pending` pathname 缺失”单独作为跨进程 PASS 线性化信号的表述。v0.3 的四文件 allowlist、opaque capability、exact raw bytes/OID、fixed-ref exact-old lease、Evidence-v1 ABI、CPU/static 限制及全部禁止范围不变；本文件不授权实现或真实操作。

## 问题与结论

`1440fd33` review 证明：只要 verifier 通过可替换 pathname 重新打开协调对象，writer 最后的 namespace identity proof 与 `.pending` 消失之间仍可发生替换；verifier 可锁到不同 inode 并在 authority 尚可 rollback 时接受 PASS。增加 sidecar、parking 或再次 lstat 都不能机械消除该窗口。

因此下列旧等式不能再作为无前提的实现合同：

```text
pending pathname absent <=> accepted PASS <=> committed <=> refs preserved
```

新设计必须使“可被 verifier 接受”经由 authority-owned、identity-bound capability，而不是仅由可替换 filesystem pathname 推断。

## 冻结选择：同进程 sealed-FD acceptance capability

选择**方案 1**，拒绝 verifier service。writer 在同一 authority transaction 内保留 sealed final evidence 的只读 FD；authority 从该 FD 读取、验证 Evidence-v1 bytes、核对 sealed `(dev,ino,digest)`、重观测双端 candidate refs，并在 guard transition 成功后签发不可复制、不可重放的 `AcceptedPass` capability。只有该 capability 是“accepted PASS”的权威；文件 pathname 只用于事后展示、审计和 independent bytes validation，绝不能单独授权 candidate refs 或 PASS。

`verify_evidence_path(path)`保留为**观察 API**：它只能回答“当前 pathname bytes 是否是有效 Evidence-v1 且当前 guard 是否缺失”，返回值不得被当作 authority acceptance token。需要执行/关闭 Gate 的调用方必须消费同一 transaction 直接返回的 `AcceptedPass`，不能通过重新打开任何 pathname 伪造。

因此不引入 socket、服务、端口、后台守护进程、持久 lock 或新远程依赖。任何仅使用 evidence 输出目录内新建或重开 pathname 的 lock、link、rename、marker、sidecar、目录扫描或一轮额外 lstat 都被明确拒绝，不得作为 implementation 修复。

## 必须冻结的合同

后续 implementation 必须冻结：

- `AcceptedPass`仅由 exact issued `EvidenceCommit` 创建；它绑定 activation、candidate revision、binding digest、sealed evidence FD identity/digest 与双端 ref witness，禁止构造、复制、pickle、replay；activation结束即失效；
- authority verifier 的唯一入口及顺序：sealed FD bytes/digest/identity → fixed refs exact candidate → authority-owned guard transition → mark `EvidenceCommit.committed` → issue `AcceptedPass` → preserve refs。任一前置失败均 guard 可见、无 capability、可 rollback；
- 线性化点：`AcceptedPass` issuance，`committed=True`及 refs preserve 必须在同一不可回滚 authority dispatch 内；文件 guard 缺失不是线性化点；
- `verify_evidence_path()`不可返回或构造 capability，且其成功/失败不改变 refs、commit 或 rollback；
- namespace replacement、FD replacement、verifier 并发、writer failure、post-commit exception 的 fail-stop 行为；
- Evidence-v1 bytes ABI保持不变；其“independent verifier”降格为内容审计而非 authority acceptance。任何需要旧“pathname verifier success 即 authorization”语义的 consumer 必须显式迁移到 capability API；
- CPU/static adversarial matrix：替换发生于 sealed FD 后、identity proof 后、guard transition 前后、`verify_evidence_path`并发前后；证明无 `AcceptedPass` 时绝不 preserve refs，capability发出后绝不 rollback。另测 pathname 可被替换而 observation 变化不影响既有 capability/ref终态。

## 范围与后续

本 Gate 只产出设计选择与验收矩阵。三方同 SHA `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PASS_LINEARIZATION_CPU_STATIC` 前，禁止修改 authority/adapter/test、禁止真实 source/candidate/ref/evidence 操作、child/runtime、CUDA/GPU、训练、评测、推理或 LIBERO4IN1。
