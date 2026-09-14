# Stage-1 authority-parent rebind design v0.1

**Gate**：`G0-R09-B-TTT-V035-STAGE1-AUTHORITY-PARENT-REBIND-DESIGN`

**状态**：docs-only，待独立三方审核；不构造 request，不执行 materialization。

## 1. 触发事实

已关闭的 config-grammar remediation formal root
`08d5828cdb4c12afa3b798ff01826c91ceb8755a` 是原 Stage-1 parent
`b3595395427114f73ff53a19a0c2b9180e39905f` 的后继。二者的 child Gitlink 均为
`93a89ba61306d840a008813f62f26a34d54850f4`，但 authority adapter blob 已由
`70b29267ea23dc4ca9d82d98ecd2b19423a9fc5e` 变为
`4a51bddd15ec9a88883e3071cc550de85721599b`。

旧 parent 内的 bootstrap parser 不含已关闭的 exact 14-tuple config grammar。因此继续将
`b359...` 写入新的 Stage-1 request，会在 clean authority tree 中重新执行旧 parser，不能消费
`08d...` 的 CPU/static closure。该差异不是可通过 overlay 或 request JSON 修复的 byte drift。

## 2. 最小 override

本设计只替代 v0.3 Stage-1 contract 中的 formal parent 绑定：下一份 Stage-1 request 必须绑定
`08d5828cdb4c12afa3b798ff01826c91ceb8755a` 与上述不变 Gitlink，而不得绑定 `b359...`。

request 构造时必须重新、同轮冻结所有依赖 parent 的字段：formal-tree 四模块 closure、adapter
blob/raw SHA，以及`docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py`
在`08d...` formal tree的精确`payload.base_path`、blob OID、raw SHA-256及字节长度；ordered replay
只能消费这组新-parent base bytes，任何path/blob/raw不符必须fail-close，禁止旧`615d6b.../3a5b4cd...`
base、overlay fallback或混合-parent重建。其后重新计算bootstrap raw/argv/contract、outer payload
bytes/SHA、clean-root basename、fixed ref freshness、selection/config FD/raw bytes、Git/Python identity、
sanitized environment、metadata 与whole-request canonical SHA。旧v1.1--v1.3数值仅作历史证据，不能复制。

## 3. 保持不变的约束

- fixed ref 仍为 `refs/heads/authority/r09-b-ttt-v035-immutable-source-v1`；构造前双端必须 absent；
- Stage-1 PASS 仍只允许产生 authority tuple 后硬停；
- 不授权 collection、receipt、record、publication、child/runtime、GPU/CUDA/torchrun、训练、评测、推理或 LIBERO4IN1；
- request 构造前不执行 materializer，不创建 clean root/index/ref/evidence，不读取 checkpoint、manifest、数据或 latent cache。

## 4. 审核请求

请求最终 verdict：

```text
APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_REBOUND_STAGE1_AUTHORITY_ROOT_REQUEST
```

或 `REQUEST_CHANGES(file:line)`。批准仅允许按 §2 生成一份新的 docs-only、fully fresh-bound
request instance 并重新三方审核；不授权该 request 的执行。
