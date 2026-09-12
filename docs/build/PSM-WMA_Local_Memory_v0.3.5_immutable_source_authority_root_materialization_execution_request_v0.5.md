# Authority-root one-shot materialization execution request v0.5

**日期**：2026-09-13
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`
**状态**：docs-only replacement request；待同一新 formal pair 三方审核。

本 request 完全替代 v0.4。唯一 runtime authority 是 annex v0.5：其 formal parent/Gitlink、输入、
bootstrap、actual argv、env、FD、fixed ref 与禁止项继承 v0.2/v0.3；v0.5 另外冻结 launcher artifact
`docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.5.py` 的 raw length=8542 和
SHA-256=`cfbb67dc1583eaab433176ad44c16635c09907efda17bdf6167b23a37540461b`。

实际启动只能使用 annex v0.5 §2 的 exact `python -I -S -B -c <artifact raw UTF-8> --` argv；payload
在首次 Git worktree add 前后绑定/revalidate parent routing/config，且 final `execve` 只可按 annex
v0.5 §3 的唯一 derivation。不得以 v0.4 descriptor、symbolic argv、shell、PATH、ambient environment、
remote alias 或额外 FD 替换任何 bytes。任何 identity、freshness、route/config、expected-zero 或 cleanup
proof 失败均为 FAIL/`ROLLBACK_INCOMPLETE`，不得 retry、换路径、进入 collection 或训练。

本文件不执行命令；不授权 source/checkpoint I/O、collection/receipt/publication/root audit、child、GPU、
训练、评测、推理或 LIBERO4IN1。请求唯一 verdict：

```text
APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT
```

或 `REQUEST_CHANGES(file:line)`。
