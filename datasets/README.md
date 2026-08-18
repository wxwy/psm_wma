# 数据集入口

本目录只保存指向实际数据存储位置的软链接，不在项目仓库中复制或提交大数据。

- `libero` → `/disk/data/LIBERO_LeRobot_v3/libero_10`（**2026-08-18 切换**，gr00t 风格 v3.0 布局：`meta/tasks.parquet` + `meta/episodes/` + 分块 `file-*.parquet`/`file-*.mp4`；当前 cosmos-framework v2/326b399 的 `LIBEROLeRobotDataset` 只支持此布局，实测加载 375/379 episodes、94250 窗口）

  - 版本背景：`/disk/data/LEROBOT_LIBERO_DATA`（v2.1 布局，`tasks.jsonl` + 每 episode 一个 parquet/mp4）与 v3.0 **数据内容逐位一致**（action/state 全等），但当前框架 loader 读不了 v2.1 布局（需 `meta/tasks.parquet`）——故弃用。
  - 注意：v3.0 目前只有 `libero_10` 一套，缺 `libero_object/spatial/goal`（老 v2.1 目录有四套，可作为内容同源备查）。
  - 视频解码需 `export LD_LIBRARY_PATH=<venv>/lib/python3.13/site-packages/nvidia/cu13/lib:$LD_LIBRARY_PATH`。
