# ObservationBundle provider design v0.1

**Gate**：`G0-R09-B-TTT-V035-SOURCE-EVIDENCE-OBSERVATION-BUNDLE-PROVIDER-DESIGN`

本设计为 request-instance 构造提供同轮、只读、可复核的 `ObservationBundle`。provider 只采集身份和
状态元数据，不读取 source payload、checkpoint、manifest、data 或 latent cache 内容，不执行 Git mutation、
网络写入、child 修改、GPU/CUDA/torch 或训练。

## 唯一入口与输出

唯一入口：`tools/psm_wma/observe_source_evidence_bundle.py:observe_bundle`。输入为显式 root、目标 evidence
路径和固定 module/path allowlist；输出为内存 `Mapping`，不写文件。输出必须包含 request-instance constructor
所需的 authority/source/executor/producer/record/receipt/publication/root_audit/preflight/execution 字段，
并冻结：当前 root HEAD、index tree、formal root/child、固定 ref local/remote presence、目标路径
absence、cwd、uid/gid/mode、解释器/Git/module path/blob/raw SHA、sanitized environment SHA 和完整 argv。

## 机械约束

provider 对每个路径使用 no-follow `stat`/fd identity，所有 SHA 从已打开 fd 计算；目标路径和 staging path
只做不存在性检查。任何 symlink、identity drift、权限不符、缺字段、非 lowercase identity 或 snapshot 变化
返回 `BLOCKED_AUTHORITY_NOT_CLOSED`，不生成可消费 instance。provider 不读取旧 SESSION、旧 JSON、环境变量
或 review 文件补字段。

## 测试与边界

stdlib temporary fixture 覆盖 regular-file identity、symlink 拒绝、uid/gid/mode、target/staging absence、
snapshot drift 和 payload 不读取；测试不触碰真实固定路径。provider 设计审核不授权 request-instance 写入、
source-evidence publication、GPU 或训练。

请求 verdict：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_SOURCE_EVIDENCE_OBSERVATION_BUNDLE_PROVIDER` 或
`REQUEST_CHANGES(file:line)`。
