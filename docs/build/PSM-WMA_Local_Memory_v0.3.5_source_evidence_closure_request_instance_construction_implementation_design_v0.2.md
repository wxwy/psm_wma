# Source-evidence closure request instance construction implementation design v0.2

**Gate**：`G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-REQUEST-INSTANCE-CONSTRUCTION-CPU-STATIC`

本 amendment 版本化覆盖 v0.1 的执行边界：本 CPU/static Gate 只验证内存 canonical bytes，不执行 JSON/Markdown
写入；原子写入、写后 readback 与 partial-residue policy 延后至独立 real-output execution Gate。v0.1 的
identity、exact schema、provider 注入、禁止 source payload/subprocess/network/GPU/训练条款继续有效。

实现必须 fail-closed 校验：全部十个嵌套 section 的 exact keys/types；lowercase 40/64-hex identity；有序
string arrays；固定 package/witness keys；固定 execution order；record 的四项 mapping 必须为
`RECORD_KEYS[2:]`（包含 `immutable_source_identifier`、`source_manifest_sha256`、`source_input_sha256`、
`checkpoint_source_descriptor_sha256`）。构造器只返回 canonical UTF-8 bytes，并以 self-excluding SHA-256
验证 round-trip。

实现范围白名单：`tools/psm_wma/build_source_evidence_closure_request_instance.py`、对应 stdlib test、
`TODO.md`、`SESSION.md` 与本 amendment。请求最终 verdict：
`APPROVE_TO_CLOSE_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_REQUEST_INSTANCE_CONSTRUCTION_CPU_STATIC`
或 `REQUEST_CHANGES(file:line)`。
