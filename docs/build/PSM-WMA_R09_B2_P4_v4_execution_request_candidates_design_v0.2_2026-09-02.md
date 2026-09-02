# R09-B2 P4-v4 Execution Request `candidates` 静态合同 v0.2

**状态**：draft；替代未获实现批准的 v0.1。仅设计/未来 root parser-validator 与 stdlib CPU fixture，禁止任何 candidate/run-root/staging 创建、preflight、P5、GPU 或训练。

`candidates` exact 为 `{root,attempt_id,recurrent,ttt_fast_weight,identity_sha256}`；outer digest 必为 lowercase 64-hex，且等于删除自身后全对象的 `canonical_sha256`。fixture 必覆盖 outer added/missing/retyped/digest drift，并在重算无关 inner identity 后仍 FAIL。

`root` exact `{root,resolved_root,kind,identity_sha256}`，kind=`candidate_root`，自身 canonical SHA；root lexical path 与每个随后派生 leaf 均复用 `_future_lexical_path`：absolute、normpath 不变、无 dot/dotdot/repeated/double separator，不创建、不 strict-resolve，所有既有 prefix `lstat` symlink FAIL。root 与 source/submodule 及**两侧** `run.<backend>.identity.root` 均无相等/祖先/后代重叠。

`attempt_id` 为 64 lowercase hex，且不等于 `run.recurrent.run_token` 或 `run.ttt_fast_weight.run_token`。

每 backend exact `{backend,candidate_root,run,identity_sha256}`；backend byte-exact为其 key，`candidate_root` exact `<root.root>/<attempt_id>/<backend>`、同一 lexical validator，且与两侧 run roots均无 overlap；`run` canonical-equal 对应 closed `run.<backend>`完整对象；record identity 为删除自身后的 canonical SHA。exact two backend，任何 third/missing/label/root/run/identity reuse FAIL。候选 payload、poison、atomicity仍由既有 static candidate contract 管理，不读取或创建目录。

若批准，仅修改 root `tools/g0/r09_b2_p4_v4_execution_preflight.py`及 stdlib CPU tests；覆盖上述 exact grammar、outer/inner identity、两向 root/leaf overlap、derived ancestor symlink、attempt/run-token inequality、ambient independence及无副作用。禁止 subprocess/project entry、真实执行、P5/GPU/训练。

请求 verdict：`APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_CANDIDATES_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 `file:line`）。
