# PSM-WMA V3 — Formal30k 原同模式 Resume Step1 CPU Preflight 证据审核：资源阻塞

**日期：** 2026-10-12
**Formal Implementation Root:** `444c232b976e80ac68cde9e7370e73b9f6410f0e` / **Child+Gitlink:** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`（远端 V3 对应 formal pair 未改变）。
**Gate verdict:** **`RESOURCE_BLOCKED`**。`FORMAL_CPU_PREFLIGHT_PASS`（依据DS原报告）、`FORMAL_GPU_NOT_LAUNCHED`。
**Prior authority:** `docs/collab/chatgpt/reviews/2026-10-12_V3_formal30k_iter800_owner_manual_same_mode_resume_execution_authorization_444c232b_e9b8a41.md`。
**新 evidence:** `docs/collab/chatgpt/evidence/2026-10-12_V3_formal30k/DS_PRO_2026-10-12_formal_CPU_preflight_PASS_GPU_resource_BLOCKED_owner_relay.md`。DS服务器原始文件未被GPT直接读取，实时资源也未由GPT远程获取；本次只对现场证据和冻结授权做增量审核，不重新做 C1/D1/生产技术审核。

## 1. Verdict分离

### CPU Preflight — 通过（给定真实来源报告）

DS 使用正确当前Child代码的完整 CPU `--preflight`，返回 EXIT0，报告核对：
- 原正式 Root/Child/Gitlink `444c232b976e80ac68cde9e7370e73b9f6410f0e`/`e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`；71e03c8历史代码仅用于说明Dense历史，不当作当前运行Child。
- 原 Job本身 `latest→iter_000000800`，model/optim/scheduler/trainer/dataloader五组件含8Rank sidecars；这不是 C1 Shadow 的独立路径。完整 `config_digest=70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`。
- `execution_scope=full_formal`, max30000 / warmup500 / save100 / T16 B8 GA2 K4 world8, `--num-workers0`；`verified_index_hit=true`, episodes9126, Source/Cache/Edge/DROID Identity正确。Root有73项准许非代码改动，无child工作树未授权变化。
- Preflight在Trainer构造之前返回，没有写原 Job；所述 Original Job 44文件/0 symlink无修改。此项只证实**preflight准备**，没有GPU Restore或iter801 Commit。

### 启动资源 Gate — `BLOCKED`（明确硬阻断）

**Severity HIGH / Operational resource blocker, NOT production bug.**
- **证据位置：** 用户转交 DS_PRO 报告 §3/上方 `docs/collab/chatgpt/evidence/2026-10-12_V3_formal30k/DS_PRO_2026-10-12_formal_CPU_preflight_PASS_GPU_resource_BLOCKED_owner_relay.md` GPU free表；Gate源 `docs/collab/chatgpt/reviews/2026-10-12_V3_formal30k_iter800_owner_manual_same_mode_resume_execution_authorization_444c232b_e9b8a41.md`, CPU Guard条款。
- **Root cause:** GPU0=24213、GPU1=24296、GPU2=24295、GPU7=24293MiB free，均**低于**冻结 >=25000MiB/卡门槛，GPU2/7 util100% 且存在非本任务活跃负载。
- **合同冲突:** 原正式 Job 8×H100 同时有效，CPU+GPU Guard全绿且Owner共享许可时才允许手动 Resume；低于阈值不得 launch。不允许把历史 GPU 峰值≈11.4GiB/rank推定为本次可安全共存，更不能将阈值从25,000降低到24,000或只用部分卡。
- **验收解除条件:** 由GPU owner/外部任务负责人协调资源。重新读取实时 8卡 `nvidia-smi memory.free`、进程PID/显存/稳定性，**全部>=25000MiB** 且获得共享许可、外部工作不抖动，确认Formal原DCP仍不变/没有其它 writer，再由Owner手动启动。若任一失败，继续`RESOURCE_BLOCKED`。无需重复已经PASS的昂贵完整CPU preflight，除非输入/代码/env/DCP/Index改变；可只做轻量现场identity、配置/路径/环境 guard。

## 2. New RUNTIME ENV finding — `PYTHONPATH` MUST be included in owner's launch environment

**Severity HIGH / Execution path requirement (found and resolved in CPU preflight).**
- **场景：** DS报告 venv editable installs parent cosmos-framework `.../psm_wma/cosmos-framework` HEAD `e3dc9ec`, and parent path lacks V3-only modules. Current V3 Child pinned `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c` is `.../psm_wma_v3/cosmos-framework`. Preflight without `PYTHONPATH` would hit wrong package import/ModuleNotFoundError.
- **Fix solely at runtime:** set `PYTHONPATH=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/cosmos-framework` **before** both `$VENV/python` CPU preflight and `$VENV/torchrun` GPU launch. The latter inherits exported environment into all8 rank workers. Keep existing `ENTRY/ARGS/CWD`, `PSM_V3_COMPACT_CACHED_VIDEO=0`, `PSM_V3_SHARED_EPISODE_CACHE=0`; no module symlinks, package reinstall, production edit or alternate Child checkout permitted. Guard should record runtime imported package paths where supported.
- **State:** `PYTHONPATH_RESOLVED_FOR_PREFLIGHT` / `PYTHONPATH_REQUIRED_AT_LAUNCH`.

## 3. Documentation not visible on pinned training checkout: expected, not blocker

- Remote GitHub `V3` has newer docs-only commits compared with the immutable training-server Root `444c232b976e80ac68cde9e7370e73b9f6410f0e`. Missing local `docs/collab/chatgpt/reviews/2026-10-12_V3_formal30k_iter800_owner_manual_same_mode_resume_execution_authorization_444c232b_e9b8a41.md` is not proof GitHub lacks it.
- **Do not `git pull` V3** onto this Formal Job checkout to view docs: that would move Root HEAD away from the frozen implementation SHA and break `verify_root_child_lock`. Passing the exact scoped user instruction or reading remote V3 doc out-of-band is enough.
- DS attempted writing `.codex/skills/psm-execution-governance/SKILL.md` but reports checkout reverted it and final Preflight passed. Record as transient out-of-scope workflow but **do not** promote a production code change to "fix" this. Keep tracked Root only in the allowlisted noncode state.

## 4. Status / next action

- **`CPU_PREFLIGHT_PASS / RESOURCE_BLOCKED / FORMAL30K_STOPPED`.**
- Previously authorized **owner-manual original Dense0/0 Resume** remains conditional and narrow, but is NOT currently executable because live resources failed. Stop; no torchrun or optimizer launched.
- New exact `PYTHONPATH` export and resource-unblock Owner handoff at `docs/collab/chatgpt/reviews/2026-10-12_V3_formal30k_resource_hold_release_PYTHONPATH_launch_addendum_444c232b_e9b8a41.md`; no separate long-running monitor automation asserted. DS may inspect resources only when asked, not auto-start.
- Once resource Gate is green and Owner launches manually: iter800 snapshot rollback replays801–805; iter801 first committed update monitoring; iter900 next valid new DCP, check all8 rank components without damaging original 800. No standalone D1-S GPU task or Formal Pair change.

**C1 remains CLOSED; D1 strict frozen gradient parity remains FAILED; optional D1-S design not approved and does not block old Dense continuation under the separate execution gate.**