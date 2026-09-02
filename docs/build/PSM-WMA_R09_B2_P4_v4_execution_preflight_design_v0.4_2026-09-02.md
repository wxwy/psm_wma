# R09-B2 P4-v4 Execution-Preflight 设计 v0.4

**状态**：draft。仅静态设计整改；不授权实现、真实 staging、candidate、record/refreeze、P5 export/compose 或训练。

## 固定前置

沿用可解析 P4 design=`f362b824735807278b74ccc553fc8f556598a8d2`、static implementation=`3d990e6fb65c192f12e3c2b58ae49356d3eba1e7`、review=`4088920d96bfb63cb64e06fe4315e74f7fbe67aa`、Gitlink=`21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`；P5 authority prerequisite 已由 `3e3a853`/`507a343` 关闭。静态 tooling 必对不可解析 anchor/source drift FAIL。

## 候选与最终证据的字节合同

每 backend 的 candidate 位于非 Git trust root `candidate_root/<attempt-id>/<backend>/`，禁止 symlink、额外 entry、重试或修复。PASS 的精确 regular-file 集合是 `{request.json,result.json,verification.json,candidate_link.json}`：前三者必须已经是既有 P5 `load_p4_v4_preflight()` 所接受的最终 canonical evidence bytes，禁止 candidate-only top-level key、包装或重序列化；其既有 nested `p4_run.run_token` 绑定 token。`candidate_link.json` 不发布，精确键为 `schema_version,backend,attempt_id,run_token,payload_sha256`，其中 schema 为 `r09_b2_p4_v4_candidate_link_v1`，payload_sha256 精确映射三份 payload canonical SHA；link backend/token 必与三 payload 的既有 binding 相等。

FAIL 的精确集合是 `{request.json,failure.json}`，禁止 result/verification/link；failure 精确键为 `schema_version,backend,attempt_id,run_token,status,stage,error_type,error`，status 固定 `FAIL`，stage 只可为 `admission|materialize|final_verify`。失败 candidate 永久 poison，拒绝其及同 attempt-id/token/run-root 的后续文件。

run_root 与 `<run_root>/import_staging/<run-token>` 必从不存在开始；首次 mkdir 消耗身份。仅一次 copy-only materialize，最终路径重算 manifest、Python/ELF closure 与 readonly roster；异常仅写 FAIL candidate，禁止 cleanup/repair/rename/retry。

## 双 backend 原子 publication 与非循环 authority

record/refreeze 仅接受 exact backend ordered set `["recurrent","ttt_fast_weight"]`：每个恰一 PASS candidate，独立复验 link、payload bytes、existing P4 schema/source/run/staging/closure/roster，且 pair-level shared-source 与既有 cross-backend invariants必须成立。缺失/FAIL/poison/重复 backend 任一项均禁止发布和 authority freezing。

record/refreeze 必将两 candidate 的六份 payload 原字节（不 parse/rewrite/re-serialize）同时写入固定 P5 evidence paths，并以一个 commit-or-none Git commit 发布；该提交含全六文件，禁止 partial commit。三 P4 payload 不嵌入 containing commit/tree/Gitlink/blob identity。仅随后的独立 reviewed P5 verifier revision 将 exact commit、raw tree SHA256、Gitlink、六 blob SHA 写入 `AUTHORIZED_P4_V4_EVIDENCE`；P5 仅接受 exact commit，record/refreeze 无权写该常量。

CPU fixtures永久覆盖 candidate-only top-level key、任意 payload byte transformation、PASS/FAIL grammar、failure poison、缺失/FAIL backend、partial commit、共同替换 clean descendant、Gitlink/blob/current/symlink/untracked drift。

## 静态实现范围

若获批准，仅 root tooling 与 stdlib CPU tests；禁止真实 staging/candidate/record/refreeze、P5 export/compose、torchrun/GPU、模型/数据/checkpoint、训练/评测/推理/B2-T。
