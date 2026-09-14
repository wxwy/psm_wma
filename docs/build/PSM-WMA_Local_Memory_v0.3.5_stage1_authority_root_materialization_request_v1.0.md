# Stage-1 authority-root materialization request v1.0

**Gate**：`G0-R09-B-TTT-V035-STAGE1-AUTHORITY-ROOT-MATERIALIZATION-REQUEST`
**Status**：exact request draft；待三方审核，不执行。

## Exact binding

- design authority=`5a668ad8871798a0c252ce9c05dbf167c36ba839`；candidate parent=`b3595395427114f73ff53a19a0c2b9180e39905f`；child=`93a89ba61306d840a008813f62f26a34d54850f4`。
- request content base 与完整 launcher/FD8/four-module/argv payload 定义逐字继承
  `...immutable_source_authority_root_materialization_execution_request_v0.9.md` §§2--3；仅本文件的 fresh snapshot 覆盖其旧 runtime predicate。
- selection SHA=`8fe4585f366cb69ad9181e30c25b5f4e99040c83d8ffe66426897bfa9d331edd`；config SHA=`43b3b77b5934107c54b8bee157b46d07cb17b85ca89305ad6fb7405237e42d1d`；Git/Python SHA 分别为`587ef21868c948b883993e23209b86a72a6ddc06aab1545c697ffc31075acd4a`/`f3e3f561b473976be55d937616915d6c507dedcb3950c3ca72df786b28e8efdc`。
- same-round snapshot（2026-09-14 CST）：local fixed ref `refs/heads/authority/r09-b-ttt-v035-immutable-source-v1` absent（`show-ref --verify` rc=1）；remote exact `ls-remote` output empty；clean root、evidence、pending absent。

## Required pre-exec binding

执行前的独立 launcher 必须把 canonical selection/config raw bytes 以 FD3/4、canonical bootstrap contract 以 FD5、clean owner 以 FD8 绑定；完整 argv、六键 sanitized env、metadata、tool closure、overlay SHA 与双端 absent snapshot 都写入 canonical request JSON，再计算 whole-request SHA。任何当前观测过期、FD/path identity mismatch、missing field 或 SHA mismatch 均 `BLOCKED_AUTHORITY_NOT_CLOSED`，零 mutation。

审批仅允许一次 Stage-1 materialization；PASS 只产生 authority tuple 并硬停。禁止 collection/receipt/source-evidence/publication、child、GPU、训练、评测、推理和 LIBERO4IN1。

Verdict requested: `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_STAGE1_AUTHORITY_ROOT` or `REQUEST_CHANGES(file:line)`.
