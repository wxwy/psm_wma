# Stage-1 v1.7 launcher freeze design v0.4

v0.4 完整继承 v0.3 的 Gate、范围、两个精确 future implementation paths、公开 API、flag-aware parser table、失败合同与禁止项；仅补齐 v0.3 ChatGPT HIGH 所指的 outer-source 自校验 literals。v0.3 仅作历史设计，正式实现与审核以本文件为准。

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`。
**请求的正向 verdict**：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_LAUNCHER_FREEZE_CPU_STATIC`。

## v0.3 source table 的完整追加

v0.3 的 source table 保留原有四项且在 parser splice 后继续按“有序、精确一处、失败即
`BLOCKED_AUTHORITY_NOT_CLOSED:source_target`”执行。其后必须追加下列四项，均只匹配一处：

```text
(7538, 9406)
(7e1c0ecc2161984a88ea0d0eae82f9f7ced709ca919f0302f74a3a068e08c9b8, ccd8ee2772d666707c919e6a20376c997771b9ff068fe0432fdaa96c686ab097)
(2427, 2336)
(72777bd7305c760c48c069eafd068f1a538383a6fdb8d40258acf3d8fc3b7ae2, 1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333)
```

前两项只绑定 `boot(s)` 的 bootstrap raw length/SHA guard，后两项只绑定 `main()` 的
`RAW[2]` parser length/SHA guard；实现必须以精确 surrounding literal 定位，而非对任意
数字串全局替换。canonical direct witness 必须消费完整 v0.3 parser table 与完整八项 source
table，证明最终 outer=`18875` bytes / `658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8`，并为新增四项逐项加入 drift negative。

不新增任何实现授权：仍不得调用 main、Git/path/FD/exec I/O、request construction、Stage-1
retry/materialization、child/runtime、GPU/CUDA/torchrun、训练、评测、推理或 LIBERO4IN1。
