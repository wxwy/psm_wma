# PSM-WMA Authority Root One-shot Materialization Execution Request v0.1

**日期**：2026-09-12
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`
**状态**：待三方执行批准；本文件本身就是前轮所要求的实际 one-shot request，不是额外 design Gate。

## 批准对象与范围

请求只允许一次 authority-root materialization：创建两个 canonical JSON、一个 detached candidate、fixed ref 的 expected-zero local/remote CAS，以及一个 canonical materialization evidence。它不打开 checkpoint source、不会进入 collection/receipt/controlled write/publication/root audit、不会修改 child、不会使用 GPU 或启动训练。

formal parent=`ad9e0110494a582e707ed5f041610d4cc40a82df`，Gitlink=`93a89ba61306d840a008813f62f26a34d54850f4`；candidate parent 只能是该 formal parent，不能是本 request、review 或 ledger commit。fixed ref 只能是 `refs/heads/authority/r09-b-ttt-v035-immutable-source-v1`，开始与结束均须以 `git show-ref` 和 `git ls-remote origin` 逐端证明 exact expected-zero/CAS result。

## 冻结输入、工具与受控路径

| 项目 | 固定值 |
| --- | --- |
| selection | 516-byte canonical `immutable_source_selection_request_v1`；SHA-256 `8fe4585f366cb69ad9181e30c25b5f4e99040c83d8ffe66426897bfa9d331edd` |
| config | 508-byte canonical resolved config；SHA-256 `43b3b77b5934107c54b8bee157b46d07cb17b85ca89305ad6fb7405237e42d1d` |
| Python | `/opt/conda/bin/python3.11` / SHA-256 `f3e3f561b473976be55d937616915d6c507dedcb3950c3ca72df786b28e8efdc` / `Python 3.11.9` |
| Git | `/usr/bin/git` / SHA-256 `587ef21868c948b883993e23209b86a72a6ddc06aab1545c697ffc31075acd4a` / `git version 2.34.1` |
| clean worktree | `/disk/rl/psm_wma/.authority-root-materialization-1eb08dea`，开始前必须不存在；由本次批准命令以 detached `ad9e011...` 创建 |
| temporary index | clean worktree 下 `.authority-root.index`，开始前必须不存在 |
| evidence | `/disk/rl/psm_wma/artifacts/g0/r09/authority_root_materialization_evidence_v1.json`，及 `.pending`，开始前均必须不存在 |

pre-import closure 精确为下表四个可执行 project module；`tools`、`tools.psm_wma`、`tools.g0` 均为无 `__init__.py` 的 namespace package。bootstrap 必须在把 clean root 放进 `sys.path` 前，对每项以 `lstat` regular/non-symlink、raw SHA-256，以及 `git -C <clean-root> ls-tree <formal-root> -- <path>` 的 `100644 blob <oid>` 三重检查；任一失败在 import/Git mutation/evidence write 前退出。

| path | blob OID | raw SHA-256 |
| --- | --- | --- |
| `tools/psm_wma/materialize_immutable_source_authority_root.py` | `ade7c872a8b702964d083ce1718aafde582f5156` | `ab8b50b826b5c022a781c2f8f96b12cafbb46f38197b779f65b21c992a42e68b` |
| `tools/psm_wma/immutable_source_authority_root.py` | `9937f74c49b14d489823c731aa2856b00c1a3d06` | `4ebf9fb8b0605bc30c45800bdfa7d367444ff97daee69926eba9aa5c9817f5d0` |
| `tools/psm_wma/immutable_source_collection.py` | `eefde4e5b5a0965bbdcaa5390b9286a4c77f2665` | `1b3353b0bd1342f1685062f962a7cbc1ba0dbf699bdc72c099ca470cb09cc340` |
| `tools/g0/audit_r09_b_ttt_root_gitlink_authority.py` | `d0020f067badfe591152fafa6336e20b485eb5ba` | `3db6376b35141d8ca5dc72c1bb38359943961db92545a88f320603121db4c39e` |

## 启动协议、判据与停止条件

批准执行时，先用固定 `/usr/bin/git` 创建/核验 clean worktree，再在该 worktree 内写入上述两项 raw bytes到 fresh regular non-symlink input files；写后以同一 FD 复读、canonical parse 和 SHA-256 核验。唯一 Python 启动形态为 `/opt/conda/bin/python3.11 -I -S -B -c <frozen-stdlib-bootstrap> -- <all parser arguments>`：bootstrap 只用标准库，先核验 Python/Git bytes/version、四模块三重 identity 和 clean root `HEAD`，再 `sys.path.insert(0, clean_root)` 并 `runpy.run_module("tools.psm_wma.materialize_immutable_source_authority_root", run_name="__main__")`。bootstrap raw UTF-8 bytes与完整 argv canonical JSON SHA-256必须写入执行 evidence；任何未冻结参数、`PYTHON*`/`GIT_*`、proxy、credential、shell glob 或 source import 都 FAIL。

adapter argv 必须覆盖 `_parser()` 的全部字段：两个 FD、formal root/Gitlink、两 raw SHA、cwd=`clean root`、remote=`origin`、index/evidence、Git/Python identity、四个冻结 module identity、author/committer metadata与固定 message。执行前的 one-shot review 必须补入 metadata、sanitized-env canonical bytes SHA、bootstrap raw SHA、argv SHA、remote credential-free identity SHA及精确 input/index/evidence paths；这些值不可在批准后替换。

PASS 仅当：single-parent two-path candidate、independent seven-key `root_revision` binding、双端 CAS 都精确指向 candidate，且 `immutable_source_authority_root_materialization_evidence_v1` 不含 raw bytes/source path/URL/secret。任一失败在 source open 前停止；已发生 mutation 时必须验证 ownership rollback，不能证明则写 `ROLLBACK_INCOMPLETE` 并停止，不重试。

请求唯一 verdict：`APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT` 或 `REQUEST_CHANGES(file:line)`。未获三方同 pair 批准不得执行上述命令。
