# PSM-WMA v0.3.5 Root Publication Freeze 设计 v0.1

**日期**：2026-09-12
**状态**：docs-only；待三方审核。
**Gate**：`G0-R09-B-TTT-V035-ROOT-PUBLICATION-FREEZE-DESIGN`

## 1. 目的与严格边界

本 Gate 只冻结未来将 root-owned authority publication 写入 Git 前的输入、提交边界和 fail-closed 验证顺序。唯一 future publication 路径仍是：

```text
docs/build/PSM-WMA_root_gitlink_authority_publication_v1.json
```

本文件复用并不改写
`PSM-WMA_Local_Memory_v0.3.5_canonical_native_root_gitlink_authority_source_audit_design_v0.3.md`
第 3--6 节的 publication schema、canonical JSON、tree/blob 与 authority 语义。

本 Gate 不创建 publication，不修改 child 或 root runtime，不读取 checkpoint、模型、数据或 cache，不运行 source audit、DCP、CUDA/GPU、torchrun、forward/loss/backward、optimizer/scheduler step、训练、评测、推理或 LIBERO4IN1。

## 2. 必须先冻结的 publication 输入

未来 materialization Gate 开始前，必须由独立、已批准的来源证明产生一个只含下列两个 nested object 的**输入包**；输入包本身不是 publication，也不得写入 publication target path：

```text
canonical_model_config
checkpoint_source_descriptor
```

两 object 的 exact key/type/value 规则完全继承 source-audit design v0.3 §4--§5。特别是：

- `canonical_model_config` 必须是 exact 15-key
  `canonical_native_local_ttt_config_v2`；resolved `ttt_tbptt_steps`、`ttt_inner_lr` 与 `k_local`
  必须是实际将被训练配置消费的值，不能在 publication 时猜测、补默认值或从环境读取。
- `checkpoint_source_descriptor` 必须是 exact 5-key
  `root_gitlink_checkpoint_source_descriptor_v1`；三个 identifier/digest 都必须来自已批准的 immutable source evidence，不能填路径、URL、分支名、时间戳、环境变量或人工标签。
- future materializer 必须对两 object 分别重新 canonicalize、计算 SHA-256，并要求其结果与输入包预声明的独立 witness 一致；任何 unknown、重复语义、非有限值、bool masquerading、key/type/value/digest drift 均 FAIL。

输入包的来源证据及其收集程序是另一项 future Gate；本 Gate 不授权收集或读取真实来源。这样 publication 写入时不会把“当前工作树可见内容”误当作 checkpoint provenance。

## 3. future materialization 的单次提交合同

获独立批准后，materializer 只可在一个新的 root commit 中新增或替换上述唯一 publication path。该提交的暂存区必须满足：

1. `git diff --cached --name-only` 只包含 publication path，或包含该 Gate 明确列出的同次 verifier/测试/运行记录文件；不得夹带 `cosmos-framework` Gitlink、训练产物、cache、checkpoint、Inbox rollover 或无关文档。
2. 实际 root Gitlink 必须在写入前从 index 读取，并以 full 40-hex child revision 记录到独立的 future audit invocation input；publication payload 不得声明 child SHA、root SHA、tree/blob OID 或任何 self-derived digest。
3. target path 的父目录必须已存在且为 root-tracked normal directory；拒绝 symlink、相对路径、路径别名、工作树外路径和 caller 选择的替代输出路径。
4. bytes 必须由唯一 canonical JSON encoder 一次性产生，严格 UTF-8、递归 key sort、`separators=(',', ':')`、`ensure_ascii=false`、`allow_nan=false`；写入后立即从 index blob 重新读取并逐 byte 对比，不能只比较 Python object。
5. 提交完成后才允许以该新 formal root revision 为输入申请 future read-only source audit；不得用 parent、working-tree HEAD 或预提交 blob SHA 代替 formal root tree lookup。

提交前的任何验证失败必须不创建或替换 target，不暂存 target，不创建 root commit，也不生成 authority。失败日志不得包含 checkpoint bytes、数据、密钥或环境变量内容。

## 4. future CPU/static implementation 的最小范围

下一份 implementation-design 可以且只能授权 root-owned、stdlib-only temporary-fixture tooling：

- `build_publication_bytes(input_package)`：拒绝所有不合法输入，返回 canonical publication bytes 和两项 nested digest；无文件、Git、child、checkpoint 或环境读取。
- `verify_publication_bytes(raw_bytes, expected_witness)`：严格 parse/canonical round-trip、exact three-key outer schema、nested schema 与 digest witness；不接受 caller supplied root/tree/blob binding。
- temporary Git fixture tests：证明 only-target staged-file contract、path/symlink/alias 拒绝、index blob byte equality，以及 root/child SHA 与 audit bindings 必须留给 materialization/audit Gate。

该 implementation 不得创建真实 target path，不得对真实 root 或 child 调用 audit，也不得读取任何真实 checkpoint/data/cache。测试输入只可为临时目录中人工构造的非真实字符串与 bytes。

## 5. 逐级 Gate 序列

```text
本 docs-only freeze design
  -> 三方 APPROVE_TO_DESIGN
  -> docs-only publication materializer/verifier implementation design
  -> 三方 APPROVE_TO_IMPLEMENT
  -> root CPU/static temporary-fixture implementation + closure review
  -> 独立真实 publication materialization execution design
  -> 三方 APPROVE_TO_WRITE_PUBLICATION
  -> 一次受控 root publication 写入/提交
  -> 独立 read-only root Gitlink source audit Gate
  -> 后续 runtime / real-I/O preflight / GPU / training Gates
```

任何后续 Gate 都不得由本 Gate 的批准自动获得。尤其是 publication 写入成功不是 checkpoint restore、LIBERO4IN1 cache 使用、GPU 或训练授权。

## 6. 本 Gate 的验收与 verdict

本 Gate 只验收本设计是否：

1. 没有实际 publication 或真实 source I/O；
2. 唯一 target path、nested schema 来源及 self-reference 禁令明确；
3. 将输入来源证明、bytes、index、formal root 和 audit 分成不可替代的阶段；
4. 对失败规定零 target/index/commit/authority mutation；
5. 没有放宽任何 v0.3 source-audit contract。

请求唯一 verdict：

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_ROOT_PUBLICATION_FREEZE
```

或 `REQUEST_CHANGES(file:line)`。本文件不授权 publication 写入、真实 audit、child 修改、真实 I/O、GPU 或训练。
