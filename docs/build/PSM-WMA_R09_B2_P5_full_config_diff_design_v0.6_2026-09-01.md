# R09-B2 P5 Full Resolved-Config Diff 静态设计 v0.6

**状态**：draft。本版替换 v0.5 中以 P4 v2 direct D005 和固定 child-request SHA 作为 future execution identity 的部分；保留 v0.4/v0.5 已批准的三根隔离、失败 attempt 保留、完整 envelope/diff 与 CPU-only 边界。

## 1. 目的、前置和禁止范围

P5 只证明 recurrent 与 `ttt_fast_weight` 的完整 resolved-config 在已定义 backend 差异外一致。它不构造 trainer/model/dataloader/optimizer/checkpoint，不调用 launch/validate/instantiate，不触发 CUDA、torchrun、GPU、训练、评测或推理。

本版不能授权任何 P5 export/compose。真正一次性 export 前必须另获三方 `APPROVE_TO_RUN_P5_STATIC_EXPORT` 和用户明确执行授权；旧 attempt、旧 v2 request SHA 与旧 output root 永不重试或复用。

P5 的前置不再是静态 D005 本身：必须有独立获批的 P4 execution preflight，且该 preflight 已在最终 canonical path 完成 copy-only staging、full-clean、payload manifest、ELF closure 与 verified loader request binding。缺少该 request、任何 preflight FAIL/BLOCKED、production/evidence/exporter 任一根不 clean，均为 P5 pre-spawn FAIL。

## 2. 三根与 P4 v4 request 链

`production_root` 是 P4 execution preflight 记录的最终 canonical staging/source root；`evidence_root` 是只读的 P1/P3/P4 committed evidence；`exporter_root` 是已审核的 root exporter/verifier checkout。三根必须 canonical、两两不同、无祖先/子孙重叠及 symlink alias，并各自满足 `git status --porcelain=v1 --untracked-files=all` 空。

每个 backend 由 parent 从 P4 preflight 的 verifier-owned request defaults（TOML 与 ordered 100-update overrides）及 production source/budget/environment 派生一个 P5 child request。request 必含 backend、P4 request/preflight identity、P4 record/verification file SHA、P1/P3 binding、canonical cwd、lexical interpreter、精确 effective environment、fresh child-output path；parent canonical-JSON SHA256 后将该 SHA 作为 out-of-band token。

P5 child 唯一启动形态为：

```text
<lexical-python> -I -S -B -c <FROZEN_STDLIB_LOADER> <p5-request-abs> <p5-request-sha> <exporter-root-abs> tools/g0/export_r09_b2_p5_resolved_config.py <bootstrap-sha>
```

loader 在打开 exporter bootstrap 前，必须一次读取 request、比对 argv SHA、比对 exporter bootstrap 的 Git blob/current bytes SHA，并只 `compile/exec` 已验证 bytes。任何 direct `[python, exporter.py]`、`-m`、缺任意 `-I/-S/-B/-c` 或 SHA token 都永久 FAIL。bootstrap 仅接受 loader namespace 内的 P5 request，不能接受 CLI child request。

## 3. 输出、验证与停止条件

parent 只可在三根之外创建唯一 `.attempt-<uuid>`；canonical output 必须预先不存在。两 child 与 pair verifier 全部 PASS 后才原子 rename。任一 child、parse、binding 或 verifier 异常必须在 attempt 内写 `failure.json`，canonical output 必须仍 absent。

pair verifier 继续使用 v0.3 的 P3 common-evidence/backend-contract 精确拆分，以及 v0.4/v0.5 的 nested exact schema、environment equality、production/exporter source identity。它必须独立重算 P4 v4 request/defaults、P4 preflight identity、child request SHA、loader argv grammar 和 bootstrap bytes binding；caller 不得提供可自证的 allowlist、tool SHA 或 request digest。

永久 CPU tests 至少覆盖：P4 v4 request/defaults drift、P5 request same-path replacement、bootstrap Git/current bytes drift、direct exporter script、non-loader argv、production/evidence/exporter root overlap、untracked shadow、P3 contract swap、failure attempt 与 canonical absence。所有测试仅临时目录和标准库 mock；不得调用 `load_experiment_from_toml`。

任何 full-clean 不成立、request/bootstrap/manifest/closure drift、非零 child、`FAIL`/`BLOCKED` verifier、canonical output 已存在、出现 CUDA/torchrun/模型数据 checkpoint I/O，都是立即停止条件：保留 attempt 与 failure evidence，不重跑、不进入 B2-T 或 Local Memory 训练。

## 4. 审核请求

本设计只请求 `APPROVE_TO_IMPLEMENT_P5_V06_STATIC_TOOLS` 或 `REQUEST_CHANGES`。批准后仅可修改 root P5 exporter/verifier 和 CPU 标准库测试；P4 record/preflight、P5 export/compose、GPU、训练及 B2-T仍须独立审核与授权。
