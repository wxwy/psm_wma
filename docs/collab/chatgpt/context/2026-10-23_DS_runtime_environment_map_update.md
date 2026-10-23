# DS目标机环境地图补充 — 2026-10-23

来源：Owner转交的 DS_PRO《Batch C r2 C01/C02 独立 CPU 定向验收报告（A报告）》。目标机路径与执行事实为DS现场取证，GPT未登录目标机。

本页补充而不删除 `docs/collab/chatgpt/context/2026-10-22_DS_runtime_environment_map.md`。旧地图“源码缺失/需离线bundle交付”和当时的本地HEAD只描述历史状态，已被以下事实取代；Owner最新要求始终由DS服务器自行拉取V3，不让Owner转运代码。

## 最新源码与目录

| 对象 | 本轮现场身份/位置 | 边界 |
|---|---|---|
| 同步后的完整clone | `/mnt/data1/data_v2_0617/dspro_batchC_r2_verify_20261022/sync_full` | DS自行完整clone，未用blob过滤；不属于活动G1工作树 |
| advertised / origin/V3 | `78305dbb7166da818cb3033e797ba35aaec1e664` | DS核对一致；GPT本轮独立远端读取也一致；不是永久固定最新HEAD |
| 验收worktree | `/mnt/data1/data_v2_0617/dspro_batchC_r2_verify_20261022/wt_accept` | 独立detached，测试前后Root/Child均clean |
| Formal Root | `a4b22b929175e462b6a8db57ad2abee7e220dd37` | 已拉取V3祖先，不能以任意docs HEAD替代本验收 |
| Child/Gitlink | `c9f21040f462a114d597fc83773cb9b6a9e96214` | mode160000，按Gitlink初始化，不用submodule --remote |
| Evidence | `/mnt/data1/data_v2_0617/dspro_batchC_r2_verify_20261022/evidence/` | 新日志/XML/所有缓存外置 |
| 本轮A报告 | `/mnt/data1/data_v2_0617/dspro_iter8900_eval_ba91ebb7/batchC_r2_CPU_acceptance_20261022.md` | 虽目录名含20261022，实际验收日为2026-10-23 |

## 解释器与实际imports

- CPU Python：`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin/python`。
- Python3.13.11；NumPy2.2.5、MuJoCo3.3.1来自site-packages。
- RoboCasa import origin：`/mnt/data1/data_v2_0617/robocasa_repo/robocasa/__init__.py`。
- robosuite import origin：`/mnt/data1/data_v2_0617/robosuite_repo/robosuite/__init__.py`。
- 两者仍是旧editable，不是正式Vendor1ac17458安装证明。此组是C01/C02合成CPU，不加载真实模型/Kitchen，不能把环境容许性推广为正式仿真已验收。
- Vendor `1ac174585293ed998ffc9cf73e47439798cf6f6c` 为版本化补丁可重建产物；此次未重建/重装。
- `CUDA_VISIBLE_DEVICES=''`；HF/Transformers offline；PYTHONPATH包含正式验收Root、scripts和Child；pycache/HF/MPL/Numba均在外置Evidence。无源码pycache污染。

## 当前验收结果

源码同步阻塞已关闭。第一组148 passed；第二组33 passed +72subtests、2 failed，重试两项仍失败；Ruff0.12.7、format、语法均通过。

失败为 `eval_robocasa_queue_identity_test.py` 中12秒健康worker等待先超时，目标mkdir/log_open OSError没有真正注入。不是全量PASS，也没有由此确认新的生产Queue缺陷。裁决与后续最小修复见：

- `docs/collab/chatgpt/reviews/2026-10-23_BatchC_r2_DS_CPU_acceptance_fixture_timeout_disposition.md`
- `docs/collab/chatgpt/requests/2026-10-23_Codex_BatchC_fixture_wait_budget_and_DS_delta_recheck.md`

源码同步可继续由DS自行拉取；固定旧库源码映射、训练输出目录不是Git仓、raw15/env12和状态布局说明见前页。两页都是带日期的环境索引，不是执行授权；不修改活动G1工作树或冻结Config/DCP。

代理凭据不写入本文。DS报告本次使用代理且临时关闭TLS校验只是事实记录，不应固化为默认Git全局设置；后续使用受信任证书链。