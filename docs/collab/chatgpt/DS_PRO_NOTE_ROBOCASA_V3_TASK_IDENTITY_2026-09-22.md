# DS_PRO Note — RoboCasa365 v3 task identity

Date: 2026-09-22

RoboCasa365 v3 的 task / phrasing / episode 语义已经落盘，不要从聊天转述重新推断。

请直接读取并按此执行：

`docs/build/PSM-WMA_RoboCasa365_v3_only_migration_2026-09-22.md`

尤其注意其中 **Critical task identity rule**：

- LeRobot v3 `task_index` 是 natural-language phrasing index，不是 underlying RoboCasa task class。
- underlying `task_class` 由 `annotation.human.task_name` 作为 global task-table index，经 `meta/tasks.parquet` 解析得到。
- atomic / composite-seen / composite-unseen 的 underlying class 数分别应为 18 / 16 / 16。
- deterministic episode limit 按 underlying `task_class` 计算，不按 phrasing / `task_index` 计算。
- 当前 first conversion 仍是 N=10 / underlying task class，`camera_set=left_wrist`。

无需再另建一套解释或映射；以该 build 文档和当前 production loader/builder 为准。
