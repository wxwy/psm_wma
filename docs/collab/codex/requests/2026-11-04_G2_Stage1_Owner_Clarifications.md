# Owner Stage-1 clarifications received 2026-11-04

This is user-provided task/provenance text, not a server-file read or data audit.

- DS local prototypes are `/tmp/g3_full.py`, `/tmp/g3_diag.py`,
  `/tmp/g3_official_render.py`; outputs `/tmp/g3_out/`. They are not Git files.
  No server script, image, depth or cache has been downloaded into cloud.
- DS's actual replay interface is
  `robocasa.scripts.dataset_scripts.playback_dataset_hdf5.reset_to`.
- `flat_v3_mapping.parquet` contains **episode-level** rows (9126 records), with
  columns task_class, task_slot, local_episode_index, global_episode_index,
  local_row_from, local_row_to, global_row_from, global_row_to, local_annotation,
  global_annotation, resolved_task_class, tasks_phrasing, length. Adjacent
  `flat_v3_mapping_tasks.parquet` exists. Row/frame/state semantics still require
  explicit checks against real data; do not infer a state shift from timestamps.
- Existing g0 `_episode_selection_score`, `_select_episode_ids`,
  `_selection_digest`, `_build_episode_task_catalog` own deterministic selection.
  Stage-1 must not copy their sampler. Consume actual accepted cache manifests or
  an external exact global-ID list bound to the mapping. No confirmed current
  N100 ID list exists; `--episode-limit100/seed42` is not proof of training use.
- DS can compare the new tool with those temporary prototypes later. Codex need
  not wait for the prototypes to implement coordinates/codec/atomic cache/CPU
  tests. Do not claim source-state physical alignment or whole-dataset validation.
- Owner additionally permits server-side read/validation through available
  remote access, but **no server files or reversible sensor data may leave the
  server, including transfer into the author cloud workspace**. Return only
  necessary non-sensitive text statistics and verdicts.
- Production code maintenance must flow local author -> Git -> isolated server
  checkout. First read the server's
  `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/.codex/skills/github-fetch-proxy/SKILL.md`
  before any server fetch and use its actual route. Temporary server validation
  code is allowed; any final fix is made/committed locally then pulled again.
- Current tool discovery exposes no Remote Desktop Commander or other remote
  execution method, and no server credentials/host have been supplied. Server
  validation has therefore not been performed or fabricated. Author Gate A can
  proceed; actual replay Gate B/C and exact training membership remain pending.
