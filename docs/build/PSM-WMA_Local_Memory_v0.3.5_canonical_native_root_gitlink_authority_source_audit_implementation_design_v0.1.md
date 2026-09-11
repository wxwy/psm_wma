# PSM-WMA v0.3.5 Root Gitlink Authority Source-audit Implementation 设计 v0.1

**日期**：2026-09-12
**状态**：docs-only；待三方审核。
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-ROOT-GITLINK-AUTHORITY-SOURCE-AUDIT-IMPLEMENTATION-DESIGN`

## 1. 前置、目标与严格范围

前置是 source-audit design formal `7d5580b34e9f27ecf5dbbfde863bacd15a03e67c` / child `93a89ba61306d840a008813f62f26a34d54850f4` 的 ChatGPT/MM/Kimi 同 pair `APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_ROOT_GITLINK_AUTHORITY_SOURCE_AUDIT`。该批准只授权本文件，不授权实现。

下一 implementation 只允许新增根仓两个文件：

```text
tools/g0/audit_r09_b_ttt_root_gitlink_authority.py
tools/g0/test_audit_r09_b_ttt_root_gitlink_authority.py
```

前者是 Python 标准库 only 的只读 Git object/source-audit tool；后者只用 `unittest`、`tempfile` 建立临时 Git repositories 的 CPU/static witness。不得改 child/Gitlink、训练/运行时代码、TOML、真实 publication、checkpoint/data/cache、DCP、CUDA/GPU、torchrun、forward/loss/backward、optimizer/scheduler step、sidecar、训练、评测、推理或 LIBERO4IN1。implementation closure 前不得对本根仓实际运行该 audit；单测只允许临时 fixture Git objects。

## 2. Tool interface 与可信输入边界

CLI 必须 exact 提供：

```text
--repo-root <absolute root repository path>
--formal-root-revision <40 lowercase Git SHA-1>
--child-git-dir <absolute Git object directory>
--output <absolute JSON artifact path>
```

`--formal-root-revision` 只是待验证的审计目标，不能因 caller 给出即被信任；tool 必须先用 root object database 验证它是 commit，再只从该 commit 的 tree 取得 tree/Gitlink/publication。`--child-git-dir` 只是 child object transport location，必须以 `git --git-dir <child-git-dir>` 使用；tool 禁止读取 child HEAD、working tree、环境变量、Git config alias 或任何 child source 文件；只允许对从 root Gitlink 派生的 exact child commit/tree OID 执行 object lookup。任何相对路径、非绝对路径、symlink escape、非 40-hex revision、不可达 object、非零 command、stderr-only 成功或额外 stdout 均为 FAIL。

工具可调用的 Git 子命令白名单只有：

```text
git -C <root> cat-file -e <formal>^{commit}
git -C <root> rev-parse <formal>^{tree}
git -C <root> cat-file -t/-s <root-tree-oid>
git -C <root> cat-file tree <root-tree-oid>
git -C <root> ls-tree <root-tree-oid> -- cosmos-framework
git -C <root> ls-tree <root-tree-oid> -- docs/build/PSM-WMA_root_gitlink_authority_publication_v1.json
git -C <root> cat-file blob <publication-blob-oid>
git --git-dir <child-git-dir> cat-file -e <gitlink>^{commit}
git --git-dir <child-git-dir> rev-parse <gitlink>^{tree}
git --git-dir <child-git-dir> cat-file -t/-s <child-tree-oid>
git --git-dir <child-git-dir> cat-file tree <child-tree-oid>
```

`cat-file tree` 与 `cat-file blob` 的 stdout bytes 必须以 `text=False` 原样读取；tree raw bytes 和 publication blob raw bytes 禁止 text decoding 后再 hash。固定 path 与 `160000 commit <gitlink>\tcosmos-framework` Gitlink entry 必须 exact，不接受 glob、prefix、alias、普通 blob/tree entry 或额外同 path entry。

## 3. 实现的 pure validators 与 artifact

tool 必须把 canonical JSON encoder、lower-hex validator、tree-record builder、publication decoder、nested config validator、source-descriptor validator 与 audit-record builder 拆为 pure functions；全部拒绝 `bool` 伪装整数、NaN/Infinity、未知/缺失/重复语义 key、非 exact schema/value。它们必须直接实现已批准 v0.3 §2--§6：

1. `root_gitlink_tree_record_v1` 的 native OID/raw tree bytes SHA-256/object type/byte length/canonical record SHA-256；
2. 三键 `root_gitlink_authority_publication_v1` publication，绝不接受 publication 内 root/tree/blob/verifier 派生字段；
3. exact 15-key `canonical_native_local_ttt_config_v2` 与 exact five-key `root_gitlink_checkpoint_source_descriptor_v1`；
4. exact 14-key `root_gitlink_source_audit_record_v1`，所有 root/child/tree/blob/source digest 都由本次 object lookup/recompute 得出。

`--output` 只能在**全部**验证成功后，用一次 atomic sibling-temp-file + `os.replace` 写出 canonical artifact；失败时不得创建、截断或替换 output，stdout 只打印一行 canonical summary JSON，exit `0`=PASS、`2`=validation FAIL、`3`=operational/unsupported invocation FAIL。artifact 必须附 tool source SHA-256、command schema/version、`status="PASS"`、audit record 与其 canonical SHA-256；不得写 checkpoint bytes、环境变量、working-tree/HEAD 结论或 runtime authority object。

## 4. CPU/static direct witnesses

unit test 必须以独立临时 root/child Git repos 写入 fixture objects，且只运行上述 tool 的 stdout/JSON contract；不得调用当前工程/child Git、网络、GPU 或任何 Cosmos import。至少覆盖：

1. valid fixture：root tree 的 `cosmos-framework` Gitlink、child commit/tree、fixed publication blob 与两 nested mapping 完整生成 PASS artifact；独立重算 tree/blob/config/source/record digests，确认 publication 不含 self-reference 字段；
2. formal revision、root/child object type、Gitlink mode/path/object、child reachability/tree、fixed publication path/blob type 任一 drift/missing/extra-entry均 FAIL 且 output 不存在或字节不变；
3. raw tree/blob byte、length、SHA-256、canonical-record digest drift 分别 FAIL；证明 hash 输入是原始 `cat-file tree`/`cat-file blob` bytes，而非 JSON/text reserialization；
4. publication outer key/schema/self-reference injection，以及 config 15-key/source five-key的 missing/unknown/type/value/hex/canonical digest drift 全部 FAIL，不能产出 authority record；
5. relative/symlink-escape/invalid revision、child HEAD/working-tree substitution、git command failure 或 unexpected output 均 FAIL；失败前后 pre-existing output bytes 不变，成功才可替换一次。

目标执行命令只在 implementation Gate 获批准后运行：

```text
python -m unittest tools/g0/test_audit_r09_b_ttt_root_gitlink_authority.py
python -m py_compile tools/g0/audit_r09_b_ttt_root_gitlink_authority.py tools/g0/test_audit_r09_b_ttt_root_gitlink_authority.py
```

还必须运行 target Ruff 与 root `git diff --check`。这些都是 CPU/static temporary-fixture tests；不是 source-audit execution，不证明当前 V2 publication 真实存在。

## 5. 后续与 verdict

只有本 design 三方 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_NATIVE_ROOT_GITLINK_AUTHORITY_SOURCE_AUDIT` 后，才可实现上述两文件与 CPU/static witnesses。implementation closure 后，仍须独立批准真实 root publication 的冻结、只读 source-audit execution、root-owned authority runtime integration、真实-I/O preflight 和 GPU Gate；任何一个成功均不得被解释为训练授权。

请求唯一 verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_NATIVE_ROOT_GITLINK_AUTHORITY_SOURCE_AUDIT
```

或 `REQUEST_CHANGES(file:line)`。
