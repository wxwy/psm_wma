# R09-B2 P4-v4 Execution-Preflight 设计 v0.3

**状态**：draft。仅静态设计整改；不授权实现、真实 staging、candidate 生成、record/refreeze、P5 export/compose 或训练。

## 已解析上游与已关闭前置

本 Gate 固定 root P4 provenance design=`f362b824735807278b74ccc553fc8f556598a8d2`、approved static implementation=`3d990e6fb65c192f12e3c2b58ae49356d3eba1e7`、ChatGPT review=`4088920d96bfb63cb64e06fe4315e74f7fbe67aa`、Gitlink=`21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`。静态 tooling 必以该 source identity 的 Git blob/current bytes 独立绑定，并对任何不可解析 anchor 或 source drift FAIL。

P5 consumer Git authority 前置已关闭：implementation=`3e3a853c61dd32888932041e6afbfac466818e09`，ChatGPT closure=`507a343`、Kimi/MM 同 SHA approval。它默认无 authority 即 FAIL；未来真实 authority 只能在独立 record/refreeze closure 后以新 reviewed verifier revision 写入。

## 候选状态机与精确文件语法

candidate 位于非 Git trust root 的 `candidate_root/<attempt-id>/`，attempt-id 与 verifier-owned 64-hex run-token 必相等地出现在每个文件；candidate directory 禁止 symlink、额外 entry、重试或修复。

- PASS 的精确 regular-file 集合是 `{request.json,result.json,verification.json}`，三者 canonical JSON，`schema_version="r09_b2_p4_v4_candidate_v1"`、backend、attempt_id、run_token 一致；result/verification 均 `status="PASS"`，verification 精确绑定 request/result canonical SHA 和 all-true checks。
- FAIL 的精确 regular-file 集合是 `{request.json,failure.json}`；禁止 result/verification。failure 的精确键为 `schema_version,backend,attempt_id,run_token,status,stage,error_type,error`，其中 status 固定 `FAIL`，stage 只可为 `admission|materialize|final_verify`。任何失败 candidate 永远 poison，record/refreeze 必拒绝其目录及同 attempt-id/token/run-root 的后续文件。

preflight 仍以不存在的 run_root 与 `<run_root>/import_staging/<run-token>` 开始；首次 mkdir 消耗身份。仅一次 copy-only materialize，随后在 final canonical path 重算 manifest、Python/ELF closure 与 readonly roster。异常仅写 FAIL candidate，禁止 cleanup/repair/rename/retry；新尝试必须全新 attempt-id、token、run-root。

## 非循环 publication 合同

未来独立授权的 record/refreeze 工具只接受 exact PASS grammar，独立重算 source/run/staging/closure/roster 与三 P4 JSON 的 canonical bytes；将三文件提交到固定 evidence paths。三 P4 文件禁止承载该提交的 evidence commit、tree、Gitlink 或自身 Git-blob identity，因而不自证也不形成循环 SHA。

post-commit identity 只由后续独立 reviewed P5 verifier revision 的 `AUTHORIZED_P4_V4_EVIDENCE` out-of-band 常量冻结（exact commit、raw tree SHA256、Gitlink、六个 blob SHA）。P5 仅接受该 exact commit，不接受 descendant；record/refreeze 不能自行填充该常量。CPU fixtures必须覆盖不可解析 anchor、PASS/FAIL grammar、failure poison、共同替换 clean descendant、Gitlink/blob/current/symlink/untracked drift。

## 静态实现范围

若获批准，仅 root tooling 与 stdlib CPU tests。禁止真实 staging、candidate、record/refreeze、compose、torchrun/GPU、模型/数据/checkpoint、训练/评测/推理/B2-T。
