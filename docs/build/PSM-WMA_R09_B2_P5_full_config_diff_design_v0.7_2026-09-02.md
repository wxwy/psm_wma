# R09-B2 P5 Full Resolved-Config Diff 静态设计 v0.7

**状态**：draft。本版替换 v0.6；只整改 ChatGPT review `2026-09-02_R09_B2_P5_v06_design_93d2f39_37bf7f6.md` 的三项 HIGH 与一项 MEDIUM。v0.2--v0.5 的完整 envelope/diff、P3 common-evidence/backend-contract、fresh failure-attempt 与 verified lexical loader 合同继续有效。

## 1. 目的、前置和永久禁止范围

P5 只比较 `recurrent` 和 `ttt_fast_weight` 的完整 resolved-config；它不构造 trainer、model、dataloader、optimizer 或 checkpoint，不调用 launch/validate/instantiate/`load_experiment_from_toml`，不触发 CUDA、torchrun、GPU、训练、评测或推理。

旧 P5 attempt、request SHA 和 output root 永久不可重试或复用。实现前置为新的、独立获批的 P4-v4 execution-preflight record/refreeze；历史 P4 v2 evidence 与 P4 static D005 template 都不能满足本版身份。P4 preflight/staging 的创建和 P5 export/compose 均仍需各自三方执行批准和用户明确授权。

### 1.1 与旧 P4 freshness 语义的显式关系

本版仅对**未来已获批的 P4-v4 preflight → P5 handoff** 覆盖 P4 interpreter-provenance v1.0/v1.3 中“旧 P5 child 前后 D005 run root absent”的旧 P5 路径语义：P5 现在只读核验已由 P4 parent 创建、已 PASS 的 `p4_run_root/p4_staging_root`，绝不创建、进入写模式、重命名或修改它们。没有该独立 P4-v4 PASS 时，仍按旧语义拒绝预存 run root。P5 自己的 failure/output staging 继续仅位于三根与 P4 run root 之外的独立 `.attempt-<uuid>`。

## 2. 四个互不混淆的路径身份

每 backend 的 authoritative preflight result 必须包含下列 canonical absolute paths，P5 parent 和 pair verifier 都独立以 `resolve(strict=True)`、无 symlink alias、非重叠规则复算：

| 身份 | 用途与约束 |
| --- | --- |
| `production_source_root` | Git production checkout。它提供已冻结 TOML bytes、child `cwd`（`production_source_root/cosmos-framework`）和 source revision/Gitlink。它与子模块均须 tracked+untracked full-clean。 |
| `p4_run_root` | P4 execution parent 创建的非 Git run-local root。它不得与任一 Git root 重叠。P5 只读检查其 post-preflight roster，不将其当作 source checkout。 |
| `p4_staging_root` | 唯一 `<p4_run_root>/import_staging/<run-token>` copy-only staging tree。它不是 Git root；必须由 exact staging manifest、readonly tree、final-path native closure 与 non-overlap 绑定。 |
| `evidence_root`、`exporter_root` | 独立 Git checkouts，分别保存批准 evidence 与 P5 tooling；两者及其子模块均 full-clean，并与前三者两两不重叠。 |

P5 child 的 TOML 只从 `production_source_root` 的已绑定 Git blob/current bytes 读取；child `cwd` 固定为上表 source 子目录。`PYTHONPATH` 必须缺席，不能成为 import authority。verified `-I -S -B -c` loader 在验证 request/argv SHA/bootstrap Git-current bytes 后，才将 `sys.path` 精确重写为已批准的 base stdlib、base lib-dynload、再加 preflight record 中按顺序列出的 canonical `p4_staging_root` payload paths；不得包含 cwd、source root、ambient site、`.pth` 或任何其他路径。

P5 parent/verifier 要分别证明 final staging manifest SHA、readonly mode、resolved path、ELF/native closure 中每个 canonical path 和 SHA 都与 preflight result 相同。source/staging substitution、staging relocation、任一 symlink alias，及相同 bytes 的 ELF 置于不同 `$ORIGIN` 路径，均必须在 child import 前 FAIL。

## 3. P4-v4 execution-preflight 的权威证据

P4-v4 preflight 必须在独立 Gate 中重新 record/refreeze；其每 backend 的三个 canonical JSON 文件固定发现于：

```text
<evidence_root>/artifacts/g0/r09/b2/p4_execution_preflight_v4/<backend>/
  request.json
  result.json
  verification.json
```

`backend` 只可为 `recurrent` 或 `ttt_fast_weight`；P5 caller 不得传入替代文件或目录。P5 verifier 从其自身绑定的 `evidence_root`、固定相对路径、backend 枚举和 Git blob/current bytes 取得三文件，再独立 canonical-JSON rehash，不信任 P5 request 内的路径、digest 或 allowlist。

三个文件的顶层 key 必须精确如下（无缺失、额外或重排语义）：

```text
request.json:
  schema_version, backend, production_source, p4_run, p4_staging,
  request_defaults, interpreter, loader_argv, effective_environment,
  native_loader_environment, payload_manifest, producer

result.json:
  schema_version, status, backend, request_sha256, production_source,
  p4_run, p4_staging, request_defaults, interpreter, loader_argv,
  effective_environment, native_loader_environment, payload_manifest,
  native_closure, pre_p5_run_root_roster, producer

verification.json:
  schema_version, status, backend, request_sha256, result_sha256,
  checks, verifier, verification_sha256
```

`production_source` 精确含 `root, revision, gitlink, submodule_revision`；`p4_run` 含 `root, run_token`；`p4_staging` 含 `root, readonly, manifest_sha256, payload_paths`；`request_defaults` 含 `toml_path, toml_git_blob_sha256, toml_current_sha256, ordered_overrides, canonical_sha256`；`interpreter` 含 lexical launcher、base executable、stdlib、lib-dynload 与其 identity；`loader_argv` 含 exact argv、loader literal SHA、bootstrap Git/current bytes SHA；两个 environment object 均含 `set, unset, inherit_allowlist, canonical_sha256`；`payload_manifest` 含 path roster/SHA；`native_closure` 含 final canonical path、SHA、ELF interpreter、RPATH/RUNPATH/$ORIGIN resolution；`producer`/`verifier` 均含 root revision、tool path、Git blob/current bytes SHA 与 identity SHA。`checks` 必须枚举上述每一绑定和 roster verdict。`status` 只能为 `PASS` 才可被 P5 接受，且 `verification_sha256` 是 verifier 对除自身该字段外对象的 canonical SHA256。

P5 parent 与 pair verifier 分别重新读取 current source、staging、run-root 和 evidence bytes，重新计算 request/result/verification SHA、manifest、native closure、readonly state、path relation与状态；recorded `PASS` 不替代这些检查。共享伪造负例（同时替换 P5 request 和三份 preflight JSON）必须因固定 evidence discovery、Git/current-byte binding 或独立再推导而 FAIL。

## 4. verifier-owned P5 空环境语法

`p5_effective_environment` 必须从空 mapping 构造，绝不继承 parent `os.environ`。它精确为两个 P4 preflight `effective_environment.set` 中相同的 production-common key/value，加本次比较允许的、各 backend 已声明的 backend-specific key/value，以及唯一启动 locale `LC_CTYPE=C.UTF-8`；其它 key 一律拒绝。两个 backend 不同的键只能是 P3 backend-contract 已列明的差异，pair verifier 对该差异表独立复算。

以下键在 P5 child 前必须 absent：`RANK`、`WORLD_SIZE`、`LOCAL_RANK`、`MASTER_ADDR`、`MASTER_PORT`、`PYTHONPATH`，以及 `LD_AUDIT`、`LD_ASSUME_KERNEL`、`LD_BIND_NOT`、`LD_DEBUG`、`LD_DEBUG_OUTPUT`、`LD_LIBRARY_PATH`、`LD_ORIGIN_PATH`、`LD_PRELOAD`、`LD_PROFILE`、`LD_SHOW_AUXV`、`LD_TRACE_LOADED_OBJECTS`、`LD_USE_LOAD_BIAS`、`GLIBC_TUNABLES`。`native_loader_environment` 的同一 absence grammar 还必须在 parent resolve closure 与 `subprocess(..., env=p5_effective_environment)` 时逐项适用。

parent、pair verifier 与 child 分别重建该 mapping；child bootstrap 在首次项目/第三方 import 前断言实际环境逐键相等。环境中存在未知继承键、任一 loader injection/search 键、rank key，或 `LC_CTYPE` 缺失/非 `C.UTF-8`，均 FAIL；这些负例永久覆盖。

## 5. pre-training run-root roster

`pre_p5_run_root_roster` 是 preflight result 的 verifier-owned exact tree manifest。`p4_run_root` 仅允许两个顶层成员：`import_staging/` 和 `preflight.json`；前者仅允许唯一 `<run-token>/`，其全部 regular-file path、mode、SHA 与 `payload_manifest` 精确相同，后者只含三个 canonical evidence file 的相对路径与 SHA。所有 staging 文件为 readonly regular file；目录不可为 symlink。

任何 checkpoints、weights、stdout/stderr/capture、training/evaluation/inference artifact、模型/数据文件、额外 staging tree、未知文件、可写 staging 或 roster drift 都是 pre-spawn FAIL。P5 verifier 在接受 preflight 前重新 walk 该 tree 并与 `pre_p5_run_root_roster`、`payload_manifest`、`native_closure` 交叉验证；永久负例包含 partial-training artifact 与额外 staging。

## 6. P5 child、输出、测试与停止条件

每 backend P5 request 按 v0.6 的 canonical JSON 和 out-of-band request SHA 规则，额外绑定本版三份 P4 evidence SHA、四路径身份、runtime `sys.path` roster、`p5_effective_environment`、run-root roster 与 P3 contract。唯一 child launch 保持：

```text
<lexical-python> -I -S -B -c <FROZEN_STDLIB_LOADER> <p5-request-abs> <p5-request-sha> <exporter-root-abs> tools/g0/export_r09_b2_p5_resolved_config.py <bootstrap-sha>
```

direct exporter script、`-m`、缺任意 `-I/-S/-B/-c` 或 SHA token 永久 FAIL。parent 只在全部 Git roots、P4 evidence、staging、environment 和 roster 已 pre-spawn PASS 后，才可在所有根之外创建唯一 `.attempt-<uuid>`；两 child 与 pair verifier PASS 后才可原子 promote。失败只可写该 attempt 的 `failure.json`，canonical output 必须 absent。

CPU-only 标准库测试至少新增本版所有 substitution/relocation/symlink/$ORIGIN、historical-v2 rejection、fixed-discovery/shared-forgery、evidence nested-key/digest drift、ambient-loader/rank/unknown/locale、partial-training/extra-staging/readonly-roster drift 负例；不得调用 compose。任何不一致、非 PASS、child 非零、CUDA/torchrun/模型/数据/checkpoint I/O 都立即停止、保留失败 attempt、不得重跑且不得进入 B2-T/Local Memory 训练。

## 7. 审核请求

本版只请求 `APPROVE_TO_IMPLEMENT_P5_V07_STATIC_TOOLS` 或 `REQUEST_CHANGES`。批准后仅可实现 root P5 exporter/verifier 与 CPU 标准库测试；P4-v4 record/refreeze/preflight、P5 export/compose、GPU、训练和 B2-T都仍须独立审核与授权。
