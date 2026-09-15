# Stage-1 v1.7 request-instance recovery design v1.8

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V18`。
**状态**：仅 docs-only pre-C closure remediation；不构造 v0.4，不消费 v1.7 的一次 C authority。

## 发现与前序不变事实

对 v1.7/v1.0/v0.5 和冻结 P0/P1 输入的复读表明，v1.7 要求把“designated candidate、record、receipt、publication 路径”逐项作 absence observation，却没有给出其 pathname、与 Stage-1 字段的映射或允许它们由何处派生。将任意路径补入 snapshot 会违反 v1.7 的“不得推断/不得混入额外路径”规则；在 C 后才发现该问题又会不可逆消耗 one-shot authority。

已完成的 P0/P1 纯内存身份核验不是 C：v1.0 的三对象、literal `ReplayBinding`、replayed parser/outer 及 `project_request_closure` 均匹配冻结 identity，未读取输出路径、环境、`.git`、ref 或 remote，未写入任何文件。v0.4 pair 仍不存在。

## 唯一可观察目标的闭合映射

若本版获同 pair 三方 `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`，未来 C 的 designated path absence 集合**只能**为下列四项，按本表顺序写入 JSON；不使用未定义的 candidate/record/receipt/publication 名称，也不增加任何 path：

| JSON key | frozen absolute path | Stage-1 role |
|---|---|---|
| `clean_root` | `/disk/rl/psm_wma/.authority-root-materialization-08d5828` | future authority-root clean worktree target |
| `index` | `/disk/rl/psm_wma/.authority-root-materialization-08d5828/.authority-root.index` | future temporary index target |
| `evidence` | `/disk/rl/psm_wma/artifacts/g0/r09/authority_root_materialization_evidence_v1.json` | future authority evidence target |
| `pending_evidence` | `/disk/rl/psm_wma/artifacts/g0/r09/authority_root_materialization_evidence_v1.json.pending` | future evidence pending target |

每项必须使用 `lexists=false` 的 raw observation，包含 path、predicate、boolean、无跟随 `lstat` 结果（仅在存在时才含 identity）和 observation record 的 canonical bytes length/SHA-256。固定 authority ref 的 local/remote absence 是独立 closure 字段，不能被其中任一路径替代。candidate、record、receipt、publication 是未来 Stage-2/collection 语义，当前 Stage-1 request 不定义、不读取、不创建也不为其伪造 absence record。

## Future v0.4 JSON 最小 schema 增补

v0.4 canonical JSON 顶层必须额外含且只含 `designated_path_absence`，其值为上述四个有序 record；并须保留 v1.7 要求的 `.git`/config/local V2、两条 remote query 和 extracted remote V2 raw identity、local/remote authority-ref absence、P0/P1 raw closure、six-key environment、owner-FD、cwd/index/evidence target 以及 one-shot boundary。每个 raw bytes field 以标准 base64 字符串、`byte_length` 和 `sha256` 三元组编码；text fields 不得替代 raw bytes。

本版不改变 v0.5 detached sidecar：JSON 仍为 UTF-8、recursive sorted keys、compact separators、恰一 terminal LF；Markdown 仍绑定 sibling JSON filename、raw length、SHA-256、canonicalization literal 和 prospective Git blob OID。`patch_raw → strict UTF-8 patch_text → exactly one apply_patch(patch_text)`、line encoder/inverse witness、pre/post byte equality及 partial residue terminal policy保持原样。

## 边界与审核

本版只解决 pre-C path/schema ambiguity。它不授权 v0.4 构造、materialization/retry、launcher/materializer、真实 source/checkpoint/manifest/data/cache I/O、collection/receipt/record/publication、child/runtime/config mutation、GPU/CUDA/torchrun、训练、评测、推理或 LIBERO4IN1。

Requested verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or `REQUEST_CHANGES(file:line)`.
