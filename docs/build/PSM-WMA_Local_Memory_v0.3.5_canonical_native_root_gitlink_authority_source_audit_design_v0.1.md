# PSM-WMA v0.3.5 Root Gitlink Authority Source-audit 设计 v0.1

**日期**：2026-09-12
**状态**：docs-only；待三方审核。
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-ROOT-GITLINK-AUTHORITY-SOURCE-AUDIT-DESIGN`

## 1. 前置与边界

前置是 synthetic CPU/static checkpoint remediation formal `69f028b2395d2f5dc6f36ac27803eb262b537e3c` / child `93a89ba61306d840a008813f62f26a34d54850f4` 的三方 closure。该 closure 只证明 synthetic fixture identity，不能代表生产 lineage。

本 Gate 仅设计未来**只读** source audit，目标是审计 root tree 中 `cosmos-framework` Gitlink 的可验证权威链。不得修改 child 或 root 运行时代码；不得读取真实 checkpoint/data/cache，不得 DCP、CUDA/GPU、torchrun、forward/backward、step、sidecar、训练、评测、推理或 LIBERO4IN1。

## 2. Frozen audit input 与 authority predicate

未来 audit 必须锁定一个 formal root revision，并只读取得：

```text
root_git_revision
root_tree_sha256
submodule_path = "cosmos-framework"
child_git_revision = root tree Gitlink(submodule_path)
child_tree_sha256
canonical_model_config_sha256
checkpoint_source_descriptor_sha256
```

权威 predicate 是：root revision/tree 与 Gitlink 在同一不可变 root tree 中一致；Gitlink 指向可达 child commit；该 child commit 指向可达 child tree；path 精确为 `cosmos-framework`；config/source descriptor 是 versioned canonical mapping 的 SHA-256。任何 detached child HEAD、工作树、环境变量、payload 字段、相对路径、时间戳或 child-source hard-coded SHA 都不能替代该 predicate。

## 3. Audit evidence 与 fail-closed 规则

未来只读 audit 的机器可读产物必须包含上述每个 field、root tree lookup record、Gitlink lookup record、child commit/tree reachability record、canonical descriptor bytes SHA-256 及 audit command/version digest；没有真实 checkpoint 内容。每个 record 要有 exact PASS/FAIL 与 failure reason。

缺失 root/tree/Gitlink、path drift、child 不可达、tree mismatch、unknown/duplicate descriptor key、digest mismatch 或任何 source 未能证明时，audit 必须 FAIL，禁止生成 production authority mapping，也禁止进入 runtime integration。成功只代表 source-audit predicate PASS，不代表 checkpoint restore、GPU 或训练授权。

## 4. 后续序列

本 design 三方 `APPROVE_TO_DESIGN` 后，才允许独立只读 source-audit implementation design；其后仍需 implementation closure、独立 root-owned authority runtime-integration design/implementation、真实-I/O preflight 和 GPU Gate 分别审核。不得把本 Gate 或 synthetic closure 当作其中任一授权。

## 5. Verdict

请求唯一 verdict：

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_ROOT_GITLINK_AUTHORITY_SOURCE_AUDIT
```

或 `REQUEST_CHANGES(file:line)`。批准仅允许下一份 docs-only source-audit implementation design；不授权代码修改、真实 I/O、GPU 或训练。
