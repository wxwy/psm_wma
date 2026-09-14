# Stage-1 authority-root materialization request v1.4

**Gate**：`G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-INSTANCE-CONSTRUCTION-AND-REVIEW`

**状态**：docs-only rebound-parent exact request；待独立三方审核，绝不执行。

## 1. Supersession 与唯一 authority

本文件与同名 canonical JSON 替代历史 v1.1--v1.3 request instance。它不复制旧 parent
`b3595395427114f73ff53a19a0c2b9180e39905f` 的任何 authority 数值；唯一 formal parent 是已关闭
config-grammar remediation 的 `08d5828cdb4c12afa3b798ff01826c91ceb8755a`，child/Gitlink 不变为
`93a89ba61306d840a008813f62f26a34d54850f4`。

## 2. 新 parent launcher binding

canonical JSON 冻结 new-parent formal tree 内
`docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py`：

- blob OID=`af19a9eb66ecaf8bd0b92a48ab1867f105026658`;
- raw SHA-256=`8b0fad39857fb72e3a3eb317f4acf6f2d6e94e196935f52f07d6170e79c678dd`;
- bytes=`18966`.

ordered replay 必须先只读并验证该 base，再解析其 `RAW[2]`，保留唯一
`--bootstrap-owner-root-fd,8`，完成 request 所列 transformations。path/blob/raw/length 任一不符、旧
`615d6b...` base、overlay fallback 或 mixed-parent reconstruction 均为
`BLOCKED_AUTHORITY_NOT_CLOSED`。

## 3. 已重算的 identity

- parser=`2336 / 1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333`;
- bootstrap=`9406 / ccd8ee2772d666707c919e6a20376c997771b9ff068fe0432fdaa96c686ab097`;
- bootstrap argv=`2341 / 85ac67c8a062399dfbface5f9c42867401ffab45320f802697c704061be8df9d`;
- contract=`182 / bec6a57aab61fd888ef0eedce37adce227a38a299a9faded53b252c8b5901702`;
- outer payload=`18875 / 658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8`.

JSON 同时冻结 four-module closure、FD3/4/5/8、freshness/absence、Git/Python identity、环境和 metadata。
任何 runtime drift 只能拒绝，不能构造替代 request。

## 4. 停止条件与审核范围

三方对本文件所属新 exact pair 全批准前不得执行。即使未来获批，Stage-1 PASS 也只允许产生
authority tuple 后硬停；不授权 materialization/retry、source/checkpoint/manifest/data/cache I/O、
collection/receipt/record/package/publication、child/runtime、GPU/CUDA/torchrun、训练、评测、推理或
LIBERO4IN1。

请求最终 verdict：`APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_STAGE1_AUTHORITY_ROOT` 或
`REQUEST_CHANGES(file:line)`。

