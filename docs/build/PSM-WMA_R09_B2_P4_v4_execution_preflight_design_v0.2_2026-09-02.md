# R09-B2 P4-v4 Execution-Preflight 设计 v0.2

**状态**：draft。仅设计整改；不授权实现、staging、record/refreeze、P5 export/compose 或训练。

## 固定上游与 P5 消费前置

本 Gate 固定 P4 provenance design=`f362b827dc9b4c9c21d2af4f54f17e0ccba20278`、P5 v0.9 implementation=`49e6ccf52227fc362ff010e097561bb31694444f`、Gitlink=`21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`。builder/verifier 的 root revision、Git blob SHA 与 current-byte SHA 必须记录；任一 grammar/tool 变更另起设计。

在本 Gate 实现/执行前，P5 consumer 必先经独立静态整改审核：`evidence_root` 和其 submodule 必 full-clean Git checkout；固定三文件必须 tracked regular files，`git show HEAD:<path>` bytes 必逐一等于 current bytes；root revision/Gitlink 与 record binding 必相等。非 Git、mutable copy 或共同重算内部 SHA chain 均 FAIL。

## 两阶段候选→冻结 handoff

one-shot preflight 仅向不属于任何 Git trust root 的 `candidate_root/<attempt-id>/` 写 candidate `{request,result,verification,failure}.json`。P5 永不读取 candidate。独立、后续审核授权的 record/refreeze 工具从 full-clean evidence checkout 外读取 candidate 与最终 run/staging，独立复算所有 identity/manifest/closure/roster；仅 canonical PASS candidate 可 copy 到固定 Git 路径、单独提交，并记录 evidence revision/Gitlink/三文件 blob+current SHA。FAIL candidate 永不 refreeze 为 PASS。

## one-shot 生命周期

`p4_run_root` 和 `<run_root>/import_staging/<verifier-owned-token>` 在开始前必须不存在；token 为 64-hex、attempt-id 唯一并写入 request。首次 mkdir 消耗该 identity。parent 仅一次 copy-only materialize，然后在最终 canonical path 重算 manifest、Python universe、ELF closure、roster；成功才写 candidate PASS 并 chmod final roster readonly。任一异常只写 candidate failure，保留部分树为不可重用失败证据；不得 cleanup、repair、rename、同 token/run-root retry 或将其 refreeze 为 PASS。新尝试必须使用全新 run-root/token。

## 静态实现范围

仅 root tooling 与 stdlib CPU tests：验证 Git-evidence authority、candidate/refreeze schema、fresh/unique token、failure poison、Git/current-byte drift、hidden Python/ELF second site、loader/bootstrap/env/sys.path/roster drift。禁止真实 staging、record/refreeze、compose、torchrun/GPU、模型数据/checkpoint、训练评测推理/B2-T。
