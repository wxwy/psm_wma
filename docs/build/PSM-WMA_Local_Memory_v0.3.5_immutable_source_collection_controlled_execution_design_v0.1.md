# PSM-WMA v0.3.5 Immutable Source Collection Controlled Execution 设计 v0.1

**日期**：2026-09-12
**状态**：docs-only；待三方审核。
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`

## 1. 范围

本 Gate 只冻结一次 future real collection/receipt execution 的受控 runbook，直接实现已批准 immutable collection execution/closure 设计；它不实际打开 source、创建 authority root、提交 collection/receipt、写 source-evidence、发布或运行 child/GPU/训练。获批后仍须以同一 Gate 的独立 execution approval 绑定真实 inputs，才可运行。

## 2. 审批输入与唯一命令形状

future execution approval 必须明示且三方绑定：execution-authority tuple、target lineage tuple `(target_ref, expected_base_root_revision, expected_child_gitlink, authority_approval_formal_root_revision)`、source-root absolute transport path、isolated work/index/temp roots、预期 collection/receipt fixed paths、日志和最小失败证据路径。不得接受 caller/env/default/working-tree discovery 的 authority、digest、target 或 config。

唯一 future command 形状为：

```text
python -I -S -B tools/psm_wma/immutable_source_collection.py execute \
  --authority-root-revision <reviewed> --selection-request <transport> \
  --source-root <absolute-directory> --target-ref <reviewed-ref> \
  --expected-base <reviewed-root> --expected-child <reviewed-gitlink> \
  --isolated-index <new-temp> --failure-evidence-dir <new-temp>
```

真实命令、所有 `<...>` 值、环境、workdir、CPU/GPU（必须 CPU-only）、网络（必须禁用）和 PASS/FAIL 判据必须在独立 execution approval 中回填；本设计不填事实常量。

## 3. 执行顺序与不可变边界

1. 在 source entry 打开前，从 Git lookup 验证 authority tuple、authority-root parent、target ref/base/Gitlink；任一 drift FAIL。
2. 只在同一 executor activation 从 root directory FD 安全打开 selection entries，在同一 regular-file FD 双读/双 hash 并构造 canonical candidates 与 single-use typed handoff；不得读取 checkpoint payload 或联网。
3. isolated preflight 从 handoff 复验 entry results、five artifacts、config byte equality、allowlist 和 candidate tree；不得改变 live ref/index/worktree。
4. preflight PASS 后再次复验 lineage，再提交 parent 精确等于 expected base 的五-path collection root；只从已提交 tree lookup 重算。
5. 生成并提交 parent 精确等于 collection root 的单-path receipt root；独立重算 receipt/tree/blob/digest。
6. 两 root 和 post-check 全部 PASS 前不得 push、publication 或 downstream consumption。成功只输出经 review 绑定的 receipt revision/path/blob OID，移交既有 source-evidence controlled-write execution。

任何失败先停止；preflight failure 保持 live 状态不变。live failure 必须恢复 snapshot ref/index/worktree，无法证明完整恢复即 `ROLLBACK_INCOMPLETE` fail-stop，禁止重试、下游、GPU 或训练。

## 4. 产物、验收与下游

成功产物仅为 collection root、receipt root、receipt binding 和不含 source bytes 的 execution report；失败产物仅为最小 stable failure code/evidence。PASS 要求 authority/lineage/handoff/tree/receipt/rollback contract 全部独立复验，且 staged delta 分别恰为五路径和一路径。FAIL 不产生 accepted authority。

本 Gate 不增加 provenance 子链：成功后按已有 source-evidence controlled-write → record/receipt → publication materializer/verifier → root audit 收口；闭环后下一设计固定为 `G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-DESIGN`。

请求唯一 verdict：

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CONTROLLED_EXECUTION
```

或 `REQUEST_CHANGES(file:line)`。批准不授权真实执行、source I/O、child、GPU 或训练；只允许申请其独立 execution approval。
