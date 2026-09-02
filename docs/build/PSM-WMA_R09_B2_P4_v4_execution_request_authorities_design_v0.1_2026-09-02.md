# R09-B2 P4-v4 Execution Request `authorities` 静态合同 v0.1

**状态**：draft；仅申请 root 静态 parser/validator tooling 与 stdlib CPU fixtures。前置：entry/source/interpreter/environment 静态 sections 已各自三方 closure；本文件不授权真实 preflight、staging/materialize/candidate、record/refreeze、P5 export/compose、torchrun、GPU 或训练。

`authorities` 精确为 `{d005_pair,identity_sha256}`。`d005_pair` 精确为 `{recurrent,ttt_fast_weight,verification,source,identity_sha256}`；前面三个 binding 都精确为 `{relative_path,sha256}`，`source` 精确为 `{root_revision,gitlink_revision,submodule_revision,identity_sha256}`。所有摘要为 64 位小写 hex，所有 revision 为 40 位小写 hex，所有 identity 都是删除自身字段后的 canonical JSON SHA256；额外、缺失、类型、顺序或摘要漂移均 FAIL。

三个 `relative_path` 必是 root-relative、非空、无 `..`、非绝对的 regular-file 路径，且三者两两不同。读取一律由 `O_RDONLY|O_NOFOLLOW|O_CLOEXEC` 打开、`fstat` 确认 regular file、单 fd 读取一次；同一 raw 同时用于 SHA256、canonical JSON 解码和后续 D005 verifier 输入，禁止 `Path.read_text/read_bytes` 或 pathname reopen。此 section 不创建目录、文件、记录或任何实际 staging 产物。

三个 raw 必是 canonical JSON（sorted keys、紧凑 separators、末尾单一换行）。`recurrent` raw 解为 backend=`recurrent` 的 D005 record，`ttt_fast_weight` raw 解为 backend=`ttt_fast_weight` 的 record；其 `d005_sha256` 必分别等于该 record 删除 `d005_sha256` 后 canonical JSON SHA256。`verification` raw 解为 D005 verifier JSON，要求其 `schema_version` 为冻结 D005 verifier schema、`status="PASS"`、其 recurrent/TTT checks（含 `record_digest`）逐项 true；validator 从各自 fd-bound raw 独立重算两个 record self digest，再调用既有 `verify_r09_b2_p4_d005.verify_pair(recurrent, ttt, root)`，返回 `status="PASS"` 才可接受。不得让 candidate 自报 PASS 代替 verifier。

`source` 必同时与两个 record 的 `source` 精确相等，并与 entry/source section 已验证的 root revision、Gitlink、submodule revision精确 cross-bind。换言之，authority records 不能来自不同 checkout、不同 Gitlink、descendant 或历史 source；未来完整 request 只能绑定同一个已验证 source tuple。两条 record 的除 P3 backend-owned 字段外的共同 source/inputs/budget 必由既有 D005 verifier复核，不在本 section维护第二套比较规则。

`authorities.d005_pair` 是 environment section 的唯一输入：validator 将该 pair 的 fd-bound decoded records 传给既有 `validate_environment_pair()`，并要求 request `environment.recurrent`/`ttt_fast_weight` 与对应 D005 record 的 `d005_projection`、effective/native object、P3 `PSM_R09_B1_TTT_ENABLED` 完全一致。没有该 named authority、任一 binding 缺失、任一 verifier FAIL 或 environment 交叉绑定不等均 FAIL。`IMAGINAIRE_OUTPUT_ROOT`、`PYTHONPATH` 的后续 run/runtime ownership不在本 section materialize。

CPU fixtures：临时 Git root 的正例；每个 binding path、sha、identity、symlink、FIFO/目录、TOCTOU pathname reopen；canonical JSON、record backend/self digest、verification status/check、record digest；pair verifier FAIL；source revision/Gitlink/submodule drift；三 binding duplicate/extra path；environment authority missing/record swap/projection/effective/native/P3 drift。每个 intended-branch mutation 必重算其他内外摘要；测试禁止 `os.environ`、subprocess execution、network、torch、GPU 和真实 staging。

本设计请求 `APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_AUTHORITIES_STATIC_TOOLS`。若三方同 SHA 批准，允许仅在 root validator/test 中实现上述静态合同并独立重新审核；run、candidates、backends 及真实 execution request 仍须分别设计、批准和验证。
