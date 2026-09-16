# Source-evidence closure request instance construction implementation design v0.1

**Gate**：`G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-REQUEST-INSTANCE-CONSTRUCTION-IMPLEMENTATION-DESIGN`

**状态**：docs-only；待 MM/DS/ChatGPT 审核；不创建 instance，不执行 source I/O。

本设计复用已批准 schema：`docs/build/PSM-WMA_Local_Memory_v0.3.5_source_evidence_closure_request_instance_schema_v0.1.md`，formal root=`771633764096d7d2af2ff12d828bebc174daa6d1`，child=`93a89ba61306d840a008813f62f26a34d54850f4`。

## 目的与输入

本 Gate 只定义如何依据已批准的 exact schema 构造一份 fresh request instance。唯一构造模块/入口为
`tools/psm_wma/build_source_evidence_closure_request_instance.py:build_request_instance`，implementation
白名单仅为该模块、`tools/psm_wma/test_build_source_evidence_closure_request_instance.py`、`TODO.md` 与
`SESSION.md`。输出路径固定为
`docs/build/PSM-WMA_Local_Memory_v0.3.5_source_evidence_closure_request_instance_v1.json` 与同名 `.md`。
构造器只能消费同一轮只读
observation 产生的 authority/source/executor/producer/record/receipt/publication/root_audit/preflight/execution
字段；不得从旧 JSON、SESSION、环境变量或本文固定值补字段。formal root 与 child 必须绑定本轮当前 root tree。

## 一次性构造序列

1. 由已批准的只读 `ObservationBundle` provider 注入并冻结当前 HEAD、canonical selection/config bytes 及其
   FD/stat/hash、authority fixed-ref 的 local 与
   remote absence；读取 root、index、cwd、evidence path、解释器、Git、executor/producer/audit module 的 tree blob
   与 raw identity；捕获 sanitized environment 和完整 argv。
2. 只在内存中按 schema 的 exact key 集合组装对象，拒绝未知键、缺键、重复语义键、非 canonical 类型和非
   lowercase identity。`record`/`receipt` 的 key 列表与四项 digest mapping 必须来自已关闭 producer/closure 合同。
3. 删除顶层 `sha256` 后用 canonical JSON（递归排序、紧凑分隔符、单 terminal LF）计算 SHA-256，再写入顶层
   `sha256`；重新序列化并逐字节验证 canonical round-trip 与 digest。
4. 仅在同一原子写操作中生成固定 JSON 与 detached Markdown sibling；写后立即逐字节读取验证路径、bytes、SHA，
   任一失败即保留明确 partial-residue 事实并终止，禁止 retry、补写或执行。
5. 构造成功后 hard stop，并以新 instance 的 exact formal root/child/SHA 申请三方审核；该审核不授权 source
   collection、record/publication 写入、receipt-root 生成、child 修改、GPU 或训练。

## 断言与失败边界

- preflight 必须证明 designated output/path/ref 均 absent、工作树/index snapshot 未变、zero mutation；否则
  `BLOCKED_AUTHORITY_NOT_CLOSED`。
- 构造阶段禁止打开 checkpoint/manifest/data/cache payload，禁止 subprocess、网络、Git mutation、torch/CUDA、
   source/record/publication I/O；所有 Git/远端查询由 provider 在构造器外完成，构造器不得自行 subprocess、网络或 Git 操作。
- 任何身份漂移、canonical mismatch、写后 readback mismatch 或 partial output 都是 terminal failure；不得把
  instance 当作 execution request 或训练输入。

## 审核请求

请求 verdict：
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_REQUEST_INSTANCE_CONSTRUCTION_CPU_STATIC`
或 `REQUEST_CHANGES(file:line)`。
