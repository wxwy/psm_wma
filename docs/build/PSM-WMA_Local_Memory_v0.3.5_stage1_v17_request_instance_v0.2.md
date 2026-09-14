# Stage-1 v1.7 exact request instance v0.2

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-CONSTRUCTION-AND-REVIEW`。

本版本 supersede v0.1；v1.6 authority 不可复用。批准前禁止执行。批准后仅此 exact request 获得一次 Stage-1 materialization attempt：任何pre-mutation drift零写入拒绝；成功仅产authority tuple后硬停；失败或已消耗即永久禁止retry，须新建request并重新批准。

## Freshness semantics

remote `V2` 仅为construction provenance：其值必须是formal request root的祖先，不作runtime equality freshness。runtime freshness仅要求fixed local/remote authority ref及designated paths保持absence。

## Complete closure

同名JSON绑定 observation timestamp、formal/base/replay identities、replay module/test blob/raw、local V2与两remote observation、selection/config/bootstrap/contract raw、canonical parser argv、six key/value environment、owner-FD insertion、cwd/index/evidence targets及canonicalization规则。两个remote query均绑定command、timeout、returncode、stdout/stderr bytes/sha；authority absence=success+zero stdout/lines+zero stderr。

JSON whole identity不自嵌：以canonical UTF-8 JSON（sorted keys、separators `,`/`:`、末尾换行）得到sidecar identity；Markdown绑定该identity，runtime先重算再检查freshness。

当前 sibling JSON=`2496 bytes / 32d0543b32a2449b1dd3efd487b2afc0099fa2ca9a2310d3a875148061cc4fc5`；`json.tool`与`git diff --check`通过。

请求 verdict：`APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_STAGE1_V17_AUTHORITY_ROOT` 或 `REQUEST_CHANGES(file:line)`。
