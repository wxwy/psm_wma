# PSM-WMA v0.3.5 Immutable Source Authority Root CPU/static Implementation 设计 v0.1

**日期**：2026-09-12
**状态**：docs-only；待三方审核。
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-CPU-STATIC-IMPLEMENTATION-DESIGN`

## 1. 范围、allowlist 与复用

本 Gate 仅把已批准 authority-root materialization/binding v0.1+v0.2 冻结为下一步 root CPU/static implementation。唯一允许新增的 production/tool文件与直接测试为：

```text
tools/psm_wma/immutable_source_authority_root.py
tools/psm_wma/test_immutable_source_authority_root.py
```

实现必须复用现有 `tools/psm_wma/immutable_source_collection.py` 的 canonical JSON、Git full-entry `(mode,type,OID)`、40/64 lowercase hex 与 exact authority seven-key validation语义，不复制一套较弱规则。为避免私有函数成为跨模块接口，仅允许把上述已存在纯validator做最小同文件公开别名/重命名并保持现有executor与32个测试行为不变；若无需改动则不得修改旧文件。任何实现commit的最终allowlist必须在送审时逐文件列出。

本 Gate不创建两个正式JSON、authority commit/ref，不连接真实Git remote，不读取/选择/hash真实source，不执行collection/receipt/source-evidence/publication、child、checkpoint/data/cache、网络、GPU或训练。

## 2. Typed DI 与唯一生产算法

`immutable_source_authority_root.py` 定义不可序列化的typed request/candidate/result，以及一个显式注入的 `AuthorityGitTransaction` protocol。protocol只暴露算法所需的只读object lookup、detached single-parent commit creation、local/remote ref observation、expected-zero CAS和exact rollback witness；不得在模块内调用bare `git`、`PATH` lookup、shell、环境变量、cwd discovery或全局singleton。

唯一生产算法分三步，temporary fixture与future real adapter必须走同一代码：

1. `prepare_candidate(request, git) -> AuthorityCandidate`：request exact包含materialization formal root、expected child Gitlink、selection/config raw bytes及固定ref；先验证raw bytes canonical schema，再从formal root lookup完整tree和Gitlink；将两个fixed `100644/blob`加入temporary tree，要求full tree changed set恰为两path且所有继承entry全等；创建detached single-parent candidate。任何错误都在ref mutation前FAIL。
2. `verify_candidate(request, candidate, git) -> AuthorityBinding`：不信任candidate自报tree/blob/binding，仅以candidate revision重新lookup single parent、full tree、两个blob raw bytes及formal-root Gitlink；重算canonical schema、native OID、raw SHA、exact delta，输出exact seven-key mapping，首键唯一为`root_revision`。输出对象内部保存mapping的deep immutable copy，不允许caller mutation。
3. `publish_candidate(request, verified, git) -> PublicationWitness`：只接受同activation由`verify_candidate`产生且绑定同一request/candidate object identity的一次性capability；再次核验local/remote固定ref均不存在，再执行expected-zero CAS。随后local与remote relookup必须都精确指向candidate revision且committed binding复验一致。任何CAS/lookup/postcheck失败都停止；若ref已变更，调用exact rollback并验证恢复为absent，失败返回唯一`ROLLBACK_INCOMPLETE`。capability重复消费、跨request/实例、pickle/copy/reconstruct均FAIL。

固定path与ref不得由caller覆盖：

```text
docs/build/PSM-WMA_immutable_source_selection_request_v1.json
docs/build/PSM-WMA_immutable_source_canonical_model_config_v1.json
refs/heads/authority/r09-b-ttt-v035-immutable-source-v1
```

## 3. Schema、commit identity 与 ABI

selection/config exact schema与canonical bytes继承binding design v0.1 §2。authority commit必须精确一个parent=`materialization_formal_root`；不得使用ambient HEAD/index/worktree。commit metadata不得包含路径、secret、caller label或运行事实；CPU/static接口由injected transaction返回nativecandidate revision并由verifier以object lookup验证内容，不把可重复SHA或固定timestamp作为安全属性。future real execution request必须另行冻结commit author/committer/message/timestamp和exact interpreter/tool identity，CPU fixture的synthetic metadata不得冒充真实值。

`AuthorityBinding.as_mapping()`唯一返回：

```text
root_revision,
selection_path,
selection_blob_native_oid,
selection_raw_sha256,
config_path,
config_blob_native_oid,
config_raw_sha256
```

禁止`authority_root_revision` alias、双键、tuple positional transport、unknown/missing key或caller adapter。direct compatibility test必须将该mapping交给现有collection executor的authority seam：exact mapping通过authority phase并到达synthetic source-open sentinel；任一首键rename/双键/缺额外键必须在sentinel前拒绝且零Git/ref mutation。不得只比较key set常量来声称兼容。

## 4. CPU/static evidence matrix

标准库tests只使用temporary/in-memory Git transaction，不接触项目live refs或remote，至少直接覆盖：

1. selection/config unknown/missing/type/order/path/noncanonical/semantic-equal-byte-drift拒绝；
2. formal root不可达、child Gitlink missing/mode/type/OID drift、parent预置fixed path；
3. candidate zero/multi/错误parent、额外delta、fixed entry非`100644/blob`、任一继承path/mode/type/OID漂移；
4. candidate自报revision/tree/blob/binding篡改不影响独立lookup结论，lookup drift必须拒绝；
5.固定ref caller override拒绝，local/remote pre-existing、CAS竞争、wrong-target、post-CAS drift拒绝；
6. pre-CAS失败零ref mutation；post-CAS失败exact rollback成功；rollback或absent恢复无法证明时`ROLLBACK_INCOMPLETE`且不自动重试；
7. verify capability同activation identity、single-use、copy/pickle/reconstruct/cross-request拒绝；
8. exact seven-key mapping到现executor真实authority seam的正例，以及alias/双键/缺额外键pre-source负例；
9. ambient HEAD/index/worktree/locale/env改变不影响相同request结果，fixture source bytes全为测试内小型合成bytes。

测试验收为全部stdlib unittest PASS、两文件临时目录`py_compile` PASS、`git diff --check` PASS。CPU/static PASS只证明算法与DI contract，不证明real Git adapter、remote CAS、解释器、真实selection/config或source存在。

## 5. 后续与授权边界

实现完成后必须提交新的exact root/child pair三方复审。三方closure后下一步是独立真实materialization execution request：冻结两个正式raw-byte inputs、两工具Git blob/raw SHA、解释器path/raw SHA/version、sanitized env、cwd、commit metadata、fixed ref expected-zero remote state、完整argv、evidence/rollback判据。没有该独立批准不得创建JSON/candidate/ref。

真实authority tuple获三方binding后进入既有controlled collection execution approval；source-evidence/publication闭环完成后直接进入`G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-DESIGN`，不新增横向provenance Gate。

请求唯一verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_CPU_STATIC
```

或`REQUEST_CHANGES(file:line)`。本申请不授权真实materialization/source I/O/collection/receipt/source-evidence/publication、child、GPU或训练。
