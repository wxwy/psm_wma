# DS_PRO — Formal30k 原同模式续训 Step1 CPU Preflight 及资源阻塞：用户转交证据

**日期:** 2026-10-12
**Formal Root:** `444c232b976e80ac68cde9e7370e73b9f6410f0e`
**Child/Gitlink:** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`
**原始 Job:** `formal_verified_index_30k`, `--phase resume` from `iter_000000800`
**来源限制:** 本文忠实记录 Owner 转交的 DS_PRO 完整报告。GPT 未直接读取 DS 主机 `/tmp/ds_pro_v3_formal30k_preflight_20261012.json`、nvidia-smi 输出、源码状态或原始 DCP 文件；原始实物 SHA 和资源快照须由 DS 现场见证。本证据记录不构成 GPU 正式启动或训练结果。

## CPU-only Preflight（DS 报告 PASS）

- 使用 venv Python，令 `PYTHONPATH=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/cosmos-framework`，两个开关 `PSM_V3_COMPACT_CACHED_VIDEO=0` 和 `PSM_V3_SHARED_EPISODE_CACHE=0`，完整 `examples/psm_wma_robocasa_corrected_phase5.py --phase resume --preflight ... --num-workers 0 --t 16 --b 8 --ga 2 --k 4 --world-size 8 --max-iter 30000 --save-iter 100 --warmup 500`。
- 原始 CPU JSON：`/tmp/ds_pro_v3_formal30k_preflight_20261012.json`，exit=0。
- `lock.root=444c232b976e80ac68cde9e7370e73b9f6410f0e`、`lock.child=lock.gitlink=e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c` 一致。
- 完整配置 SHA256 digest `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`。
- `execution_scope=full_formal`, `execution_stop_after_iter=30000`, original Job `checkpoint_load_path=.../formal_verified_index_30k/checkpoints/iter_000000800`, `verified_index_hit=true`, `episodes=9126`, `allowed_root_noncode_changes=73`（报告称全部符合允许列表）。
- 报告称 model Edge config witness `a9381d094679851e1465c6f8236ddc672ba15b54ba93daf8c07115cb93a35553`, DROID base checkpoint model metadata `cf0c23404efb0bf78c163a85d3800d6163cbbcd5478401feb6cc93f5715a88fa`，Cache/Source digests 与原约定一致。
- 8rank原正式迭代800 DCP五个组件全在，44文件清单/0 symlink，`latest_checkpoint.txt→iter_000000800`；报告根据 mtime/既有 G0 来源判断本轮没有改写原 Job。训练仍 STOPPED，无 Checkpointer load/torchrun/optimizer step/原DCP写入。
- CPU Preflight 初始化耗时约198.3s（源 Reader 约195.9s），不构成 GPU/训练执行。

## 必须保留的运行时 PYTHONPATH 发现

- 当前 venv 的 editable 安装关联的是**父仓** `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework`（DS 报该父仓 HEAD `e3dc9ec`），父仓缺少当前 V3 Child 的 `robocasa_exact_window_cache`/corrected phase5 代码。若只使用 venv 而未设置 `PYTHONPATH`，导致 `ModuleNotFoundError`。
- 显式 `PYTHONPATH=<V3 Child checkout>` 时，`--preflight` exit0 且校验正确 Formal SHA。**Owner 的 torchrun 必须继承同一 PYTHONPATH**；不能让 import 落回父仓。该环境路径修正不修改任何生产代码/Model 配置。
- 正式授权文档位于 GitHub `V3` docs-only bookkeeping HEAD，而训练服务器 Root 固定在 `444c232b976e80ac68cde9e7370e73b9f6410f0e`；因此本地找不到文档并非 GitHub 未提交，不应通过移动训练工作树 HEAD 来读审核文件。

## GPU共享资源（DS 报告 2026-10-12 09:1x 快照）

冻结阈值：8张卡全部 free >=25000MiB，且外部 robotwin_server 稳定、Owner共享许可明确。

| GPU | free MiB | util% | guard |
|---:|---:|---:|---|
|0|24213|59|BLOCKED|
|1|24296|34|BLOCKED|
|2|24295|100|BLOCKED|
|3|34895|0|PASS|
|4|34895|5|PASS|
|5|35511|0|PASS|
|6|35511|0|PASS|
|7|24293|100|BLOCKED|

**4/8 低于25,000MiB，所以本次 GPU Gate FAIL/RESOURCE_BLOCKED；正式训练未启动。** 历史/瞬时显存不得当成下一次启动时实时资源，亦不得擅自降低阈值、抢占/kill他人进程或改变卡数/训练形态。

## 现场报告的其它边界

- DS 曾在非生产 `.codex/skills/psm-execution-governance/SKILL.md` 试写流程提示，触发 `verify_root_child_lock()/_audit_root_noncode_changes` Gate；报告称已通过 checkout 还原且最终 Preflight PASS。此为**尝试性越界后恢复**，不是授权修改固定 Root；后续流程文档由 GPT 写 GitHub V3 docs，不要求训练工作树本地写文件。
- 当前未有新正式GPU Resume/任何iter801更新；上次原 Job latest 保存800、旧日志最远805，后续必重放801–805、正常首保存点900。
- 用户/DS报告的六项前置条件中前五项 PASS、最后 GPU 资源条件 FAIL；无需重复前五项完整 Gate，除非源/环境/作业身份有改变。

**GPT裁决:** `docs/collab/chatgpt/reviews/2026-10-12_V3_formal30k_preflight_PASS_resource_hold_444c232b_e9b8a41.md`；资源解除后续守卫在 `docs/collab/chatgpt/reviews/2026-10-12_V3_formal30k_resource_hold_release_PYTHONPATH_launch_addendum_444c232b_e9b8a41.md`。