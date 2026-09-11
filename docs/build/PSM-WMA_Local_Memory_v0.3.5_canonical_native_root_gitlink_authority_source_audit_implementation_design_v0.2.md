# PSM-WMA v0.3.5 Root Gitlink Source-audit Implementation 设计 v0.2

**日期**：2026-09-12；**状态**：docs-only remediation；待三方审核。
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-ROOT-GITLINK-AUTHORITY-SOURCE-AUDIT-IMPLEMENTATION-DESIGN`

**supersedes**：v0.1 的 Git execution 与 machine-readable evidence 表述；其两文件白名单、禁止范围、raw-object 与 temporary-fixture 规则不变。

## 1. 隔离的 Git execution contract

implementation 的唯一 Git executable 是 absolute regular file `/usr/bin/git`；不存在、不可执行、`sha256(read_bytes())` 或 `git --version` 不能以严格 ASCII 单行取得时 operational FAIL。不得 `PATH` lookup、caller `--git`、shell、alias、hook 或 config lookup。每一次 subprocess 都必须 `shell=False`、`text=False`、`close_fds=True`，并只继承 exact environment：`LC_ALL=C`、`LANG=C`、`PATH=/usr/bin:/bin`、`GIT_CONFIG_NOSYSTEM=1`、`GIT_CONFIG_GLOBAL=/dev/null`、`GIT_NO_REPLACE_OBJECTS=1`、`GIT_OPTIONAL_LOCKS=0`；所有 caller env（尤其 `GIT_DIR/GIT_WORK_TREE/GIT_COMMON_DIR/GIT_OBJECT_DIRECTORY/GIT_ALTERNATE_OBJECT_DIRECTORIES/GIT_NAMESPACE/GIT_REPLACE_REF_BASE/GIT_CONFIG_*`）必须不存在。root 只能由 validated absolute `-C <root>` 选择，child 只能由 validated absolute `--git-dir <child-git-dir>` 选择。

command identity exact mapping=`root_gitlink_git_command_identity_v1`，keys=`schema,git_executable,git_executable_sha256,git_version,environment_sha256,command_whitelist_sha256`；后两 digest 分别由上述 exact environment mapping 和 v0.1 whitelist canonical JSON 计算。它必须进入每个结果。

## 2. exact evidence / failure contract

成功 artifact 是 exact `root_gitlink_source_audit_evidence_v1` object，keys=`schema,status,command_identity,checks,audit_record,audit_record_sha256,tool_source_sha256`，`status="PASS"`。`checks` 是按此固定顺序、不可删改的 array：`root_commit`、`root_tree`、`root_tree_record`、`gitlink`、`publication_blob`、`publication_json`、`canonical_model_config`、`checkpoint_source_descriptor`、`child_commit`、`child_tree`、`child_tree_record`、`audit_record`。每项 exact keys=`name,status,reason,observed`；`status` 只允许 `PASS/FAIL/SKIPPED`，`reason` 是 nonempty stable machine code，`observed` 只含已读取 object OID/type/byte_length/digest 或 nested canonical digest，绝不含 checkpoint bytes、env 或 worktree/HEAD data。PASS 不允许 FAIL/SKIPPED；首次 FAIL 后余项必须 SKIPPED，且不得生成 authority。

无论 validation 或 operational failure，都不写/截断/替换 `--output`；stdout 唯一输出 canonical `root_gitlink_source_audit_failure_v1`，keys=`schema,status,exit_code,command_identity,checks,tool_source_sha256`，`status="FAIL"`，checks 同上。exit 2=validation，3=operational。publication raw bytes 必须 exact canonical JSON bytes（解析后重新 canonical serialize 必须 byte-for-byte 相等），否则 `publication_json` FAIL。

## 3. 新增 witnesses 与 verdict

temporary-fixture tests 必须注入 hostile `GIT_DIR`、object/alternate directory、replace refs 与 config-injection env，并断言 sanitized execution仍只得到 fixture root/Gitlink/publication/child tree；同时断言 command identity、每步 PASS/FAIL/reason、failure stdout schema、pre-existing output byte-preservation及 noncanonical publication whitespace/key-order bytes reject。其余 v0.1 witnesses不变。

请求 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_NATIVE_ROOT_GITLINK_AUTHORITY_SOURCE_AUDIT` 或 `REQUEST_CHANGES(file:line)`；仍不授权代码、真实 audit、I/O、GPU 或训练。
