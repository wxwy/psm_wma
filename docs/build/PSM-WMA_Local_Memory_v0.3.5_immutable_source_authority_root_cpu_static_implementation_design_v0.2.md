# PSM-WMA v0.3.5 Immutable Source Authority Root CPU/static Implementation 设计 v0.2

**日期**：2026-09-12
**状态**：docs-only；待三方复审。
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-CPU-STATIC-IMPLEMENTATION-DESIGN`

本文件针对 v0.1 的两项 HIGH 做显式 supersession；未冲突部分继续继承 v0.1。v0.2 仍只申请 synthetic CPU/static tooling 实现授权，不授权真实 JSON、commit、ref、source、remote、GPU 或训练。

## 1. 实现 allowlist 与现 executor 闭合

实现 allowlist 精确扩展为四个文件：

```text
tools/psm_wma/immutable_source_authority_root.py
tools/psm_wma/test_immutable_source_authority_root.py
tools/psm_wma/immutable_source_collection.py
tools/psm_wma/test_immutable_source_collection.py
```

现有 collection executor 必须原位增加 typed authority-ref observation，不能由 caller、wrapper 或 ledger adapter 代做。固定 ref 仍不可覆盖：

```text
refs/heads/authority/r09-b-ttt-v035-immutable-source-v1
```

`GitTransaction` 增加语义明确的 local fixed-ref 与 remote fixed-ref 只读观察；测试 transaction 只实现内存状态，不执行真实 Git/网络。`_bound_source_inputs()` 在已有 authority object、parent/tree/blob/raw-byte 和 collection lineage 校验全部通过后、任何 source open 之前，必须重新观察 local 与 remote fixed ref。二者都必须精确等于 `authority["root_revision"]`。任一 absent、wrong target、local/remote disagreement 或 observation error 均在 source-open sentinel 前 FAIL，并保持 ref/source mutation count 为零。

如需避免复制较弱 validator，可在 `immutable_source_collection.py` 内最小提取现有 selection validation，并同步调整其直接测试；不得改变既有接受/拒绝语义。实现送审必须列出这四个文件的实际 delta，并证明原有 collection tests 全部保持通过。

直接验收必须调用真实 `_bound_source_inputs()` / `collect_synthetic()` 路径，而非比较常量或测试 wrapper：exact seven-key mapping、local ref exact、remote ref exact 时到达 source-open sentinel；首键 alias/双键/缺额外键以及上述每个 ref 负例均在 sentinel 前拒绝且零 mutation。

## 2. Publication 与 ownership-aware rollback 状态机

`publish_candidate()` 的唯一顺序冻结如下：

1. 新鲜观察 local 与 remote fixed ref，二者必须 absent；
2. local 执行 expected-absent → exact-candidate CAS；仅 CAS 成功后记录本 activation 的 `local_created` witness；
3. remote 执行 expected-absent → exact-candidate CAS；仅 CAS 成功后记录本 activation 的 `remote_created` witness；
4. 新鲜重读 local、remote，二者都必须仍为 exact candidate，再复验 committed binding；
5. 任一步失败进入一次 fail-stop rollback，不自动重试 publication。

rollback 按 remote 后 local 的逆序处理。只有本 activation 持有对应 `*_created` witness 的 endpoint 才允许尝试修改，而且唯一允许的修改是 conditional exact-candidate → absent compare-and-delete。没有 witness、当前值是 foreign revision、观察不可读、compare-delete 失败或 ownership 无法证明时，绝不删除该 endpoint；记录 incomplete，并继续安全尝试清理另一个由本 activation 创建的 endpoint。

rollback 完成后必须重新独立观察 local 与 remote。只有二者都被证明 absent 才是 rollback success；否则统一返回 `ROLLBACK_INCOMPLETE`，不得把 foreign ref 删除、覆盖或自动重试。若 failure 前某 endpoint 本就由并发者创建，该 foreign endpoint 保留，因此最终必为 `ROLLBACK_INCOMPLETE`，即使本 activation 创建的另一个 endpoint已安全删除。

## 3. CPU/static 竞态验收增量

除 v0.1 全矩阵外，必须用 deterministic injected transaction 直接覆盖：

1. local CAS 成功后、remote CAS 前，remote 被并发创建：remote foreign 保留，local 仅以 candidate→absent 条件删除，最终 `ROLLBACK_INCOMPLETE`；
2. 两次 CAS 后、postcheck 前 local 或 remote 漂移为 foreign：漂移 endpoint 不删除，仍由本 activation 所有且保持 candidate 的另一 endpoint可条件清理，最终 `ROLLBACK_INCOMPLETE`；
3. rollback 期间 endpoint 从 candidate 漂移为 foreign：compare-delete 失败且 foreign 保留；
4. 一端创建成功、另一端 CAS conflict，以及两端不同 success/conflict 组合；
5. unreadable observation、缺 ownership witness、compare-delete failure均 fail-stop，且 foreign refs 从未被移除；
6. 无竞态的 postcheck failure 可对两端完成逆序条件回滚，并由 fresh observation 证明均 absent；
7. 当前 collection executor 的 fixed-ref PASS、local absent、remote absent、local wrong、remote wrong、两端不一致、local/remote observation error，均验证 source-open sentinel 顺序与零 mutation。

## 4. 授权边界与 verdict

本轮仍是 docs-only remediation。三方对同一新 root/child pair 全部批准后，才允许按四文件 allowlist 实现并运行 stdlib CPU/static tests。真实 adapter、JSON、authority commit/ref、source/remote I/O、collection、publication evidence、child、GPU、训练均继续禁止。

请求唯一 verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_CPU_STATIC
```

或 `REQUEST_CHANGES(file:line)`。
