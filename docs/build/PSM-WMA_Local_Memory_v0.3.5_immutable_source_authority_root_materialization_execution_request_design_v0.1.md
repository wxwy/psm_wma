# PSM-WMA v0.3.5 Authority Root Materialization Execution Request 设计 v0.1

**日期**：2026-09-12
**状态**：docs-only；待三方审核。
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST-DESIGN`

## 1. 目的与唯一范围

本文件冻结既有 source-evidence 闭环中唯一一次 authority-root materialization 的**审批请求格式**。它承接已关闭的 real-adapter CPU/static formal pair `ad9e0110494a582e707ed5f041610d4cc40a82df` / `93a89ba61306d840a008813f62f26a34d54850f4`，不新增 checkpoint authority、publication evidence 或同一 binding 的横向 Gate。

本 Gate 不创建 selection/config JSON、candidate commit、local/remote ref、temporary index、evidence 文件或 clean worktree；不打开八个 checkpoint source entry；不执行 collection/receipt/source-evidence/publication、child/runtime、CUDA/GPU、训练、评测、推理或 LIBERO4IN1。

三方批准本设计后，唯一允许的下一份文档是 one-shot execution request。该 request 必须在执行前冻结全部实际值并再次获得 `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT`；本设计本身不授予写入权限。

## 2. 不可变输入与 formal-tree identity

one-shot request 必须逐字冻结下列值，且每项均由 request 之外的只读 source 重算；request/ledger commit 不是 authority：

| 项目 | 固定值或规则 |
| --- | --- |
| materialization formal root | `ad9e0110494a582e707ed5f041610d4cc40a82df` |
| required Gitlink | `93a89ba61306d840a008813f62f26a34d54850f4` |
| adapter path/blob/raw SHA-256 | `tools/psm_wma/materialize_immutable_source_authority_root.py` / `ade7c872a8b702964d083ce1718aafde582f5156` / `ab8b50b826b5c022a781c2f8f96b12cafbb46f38197b779f65b21c992a42e68b` |
| authority module path/blob/raw SHA-256 | `tools/psm_wma/immutable_source_authority_root.py` / `9937f74c49b14d489823c731aa2856b00c1a3d06` / `4ebf9fb8b0605bc30c45800bdfa7d367444ff97daee69926eba9aa5c9817f5d0` |
| selection bytes | v0.1 real-adapter design §2 的 exact 516-byte `immutable_source_selection_request_v1`，SHA-256=`8fe4585f366cb69ad9181e30c25b5f4e99040c83d8ffe66426897bfa9d331edd` |
| config bytes | v0.1 real-adapter design §2 的 exact 508-byte resolved config，SHA-256=`43b3b77b5934107c54b8bee157b46d07cb17b85ca89305ad6fb7405237e42d1d` |
| fixed ref | `refs/heads/authority/r09-b-ttt-v035-immutable-source-v1`，local 与 remote 均 expected-zero |

selection/config 的 native blob OID 不预先从文档推断；one-shot request 必须以目标 repository 的 native object format 从 exact raw bytes 独立计算，并与 candidate tree 重算结果一致。两 raw bytes 只准经请求中写明的两个 regular、non-symlink FD 输入；不得使用 caller mapping、stdin、环境变量、PATH、当前 worktree 或 Git index。

## 3. 受控启动与完整 argv

实际审批 request 必须冻结：受控 clean worktree 的绝对路径与 `realpath`、其 `HEAD=materialization formal root`、只读 root tree witness、Python/Git executable 的 absolute path/raw SHA-256/`--version`、credential-free normalized remote identity digest、exact sanitized environment、commit metadata、FD input paths、temporary index、fresh absolute evidence destination和完整 argv 的 canonical JSON SHA-256。

为避免从调用者 cwd 或 `PYTHONPATH` 导入代码，启动必须使用受控 clean worktree，且仅可采用以下等价 bootstrap：

```text
<python> -I -S -B -c '<stdlib bootstrap: require clean-root realpath; prepend exactly that root; run module tools.psm_wma.materialize_immutable_source_authority_root as __main__>' -- <all frozen adapter arguments>
```

bootstrap 只能使用 Python 标准库；在把该 clean root 放入 `sys.path` 前不得导入项目模块。adapter 的既有 preflight 必须在任何 Git mutation 前重算 §2 的 formal-tree module bytes、Gitlink、interpreter/Git identity、input SHA、evidence freshness 和双端 expected-zero ref。任何 drift、import path 不一致、non-regular FD、remote/ref/evidence 已存在或 preflight error 都是 zero-mutation FAIL。

argv 的参数集合必须与 `materialize_immutable_source_authority_root._parser()` 完全相同，包含 `--selection-fd`、`--config-fd`、formal root/Gitlink、两 raw SHA、cwd/remote/index/evidence、Git/Python identity、两个 module identity、author/committer 六字段与 commit message。禁止通配符、shell expansion、ambient `GIT_*`、`PYTHON*`、credential、代理、网络配置或未冻结额外参数。

## 4. 单次事务、证据与停止条件

执行只允许在 fresh destination、fresh temporary index 和 fixed ref 双端缺失均经 preflight 证明后进行一次。PASS 必须同时产生：

1. single-parent detached authority candidate，其 parent 精确等于 formal root，tree delta 恰为固定 selection/config 两个 `100644 blob`；
2. independent verifier 重算的 exact seven-key `root_revision` binding；
3. fixed ref 的 local/remote expected-zero CAS 均精确指向 candidate；
4. canonical `immutable_source_authority_root_materialization_evidence_v1`，其中不含 raw bytes、source paths、URL 或 secret。

FAIL 在任何 source open 前停止；若尚未创建 ref，evidence 仅记录 preflight/failure 和 null authority values。若发生 candidate/ref mutation，必须按 adapter 的 ownership-aware rollback 证明双端复原；无法证明时结果唯一为 `ROLLBACK_INCOMPLETE`，保留最小诊断并停止，不重试、不换 parent/ref/路径、不进入 collection 或训练。

PASS 仍只授权把经三方 review 明示的 seven-key binding 交给后续 controlled collection execution approval；不授权 source read、collection/receipt、controlled write、record/receipt、publication、root audit、GPU smoke 或正式训练。

## 5. 审核与后续

请求唯一 verdict：

```text
APPROVE_TO_PREPARE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_EXECUTION_REQUEST
```

或 `REQUEST_CHANGES(file:line)`。全批准后仅可生成包含全部实际 identity、metadata、path、environment、argv、PASS/FAIL/rollback 判据的 one-shot request 并再次三方审核；不得直接执行。
