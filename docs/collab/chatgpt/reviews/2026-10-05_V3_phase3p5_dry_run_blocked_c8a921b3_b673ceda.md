# V3 Phase3.5 real cache parity dry-run — GPT execution evidence review

- 日期：2026-10-05
- Gate：`V3-REAL-CACHE-ONLINE-VAE-PARITY`
- implementation pair：`c8a921b38128ed7430577693e76c8f38d856599a / b673ceda5a9ff058abb31224b7006f2d87771ad2`
- source authorization：`docs/collab/chatgpt/reviews/2026-10-05_V3_phase3p5_source_review_r2_c8a921b3_b673ceda.md`
- ds Evidence：`/tmp/psm_wma_v3_phase3p5_ds_evidence_r1/`

## Verdict

`BLOCKED_ASSET_PATH`

这不是 source/code FAIL，也不是 parity FAIL。
当前唯一在线执行环境是编码服务器 `bitahub-a21313865965105152189478`，该环境没有显式提供 matching real assets，因此 dry-run 按授权要求在运行 probe 前安全停止。

## Exact-pair / execution discipline

ds 已按 fresh Evidence 目录开始：
- exact root/child pair lock；
- no code/test/gitlink edits；
- no observational / threshold / Phase4；
- no global filesystem search；
- no historical path guessing；
- no asset download/copy/rebuild。

## Asset check result

以下显式变量均未形成可执行 real-asset contract：
- `CACHE_ROOT`
- `SOURCE_ROOT`
- `WAN_VAE_PATH`
- `PARITY_OUT`

执行服务器与 source authorization 中的 current environment note一致，是编码服务器而非训练/资产服务器。

因此：
- 未执行 `verify_robocasa_exact_window_real_parity.py --dry-run`；
- 未生成 parity output JSON；
- 未加载 Wan VAE；
- 未访问真实视频/cache；
- 未使用 GPU。

这是正确的 fail-closed 行为。

## Evidence files

fresh directory：
`/tmp/psm_wma_v3_phase3p5_ds_evidence_r1/`

已保存 pair/env precheck raw outputs与 summary。

## Unblock condition

仅当 Owner/执行环境显式提供且本地存在：
1. exact-window cache directory；
2. matching flat LeRobot v3 source directory；
3. local Wan VAE file；
4. fresh parity output JSON path；

才允许重跑同一 dry-run-only Gate。

可通过：
- 将训练/资产服务器作为新的 Desktop Commander device连接；
- 或在当前 ds shell显式 export/mount上述路径。

禁止为了解除阻塞：
- 从历史 manifest absolute path猜测；
- 扫描整台机器寻找数据；
- 下载/复制/rebuild cache/source/VAE。

## Next boundary

在 real dry-run `DRY_RUN_PASS` 前：
- 不授权 observational real Wan encode；
- 不冻结 numerical threshold；
- 不运行 thresholded parity；
- 不启动 Phase4 Local-TTT integration；
- 不启动 GPU training/simulation。

Phase3.5 implementation本身保持可用；当前 blocker纯属执行资产/服务器可达性。