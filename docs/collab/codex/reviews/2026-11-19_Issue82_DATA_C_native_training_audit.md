# Issue #82 独立审查与修复交接

原始审查结论 **REQUEST_CHANGES**。固定位为 Root `ab3d466eea259795c539bdee50f714f48dc7c91b` 和 Child `9370c3858532b4d61630138431145c8360e86eb0`，覆盖自 `d43126f4127a352eb821354185e3a0a4fa797767` 起与 DATA_C、CAP2 和训练快照有关的实现，包含 PR #78–81。

修复候选为 Root `3aff85a702f5e3b05bc5cd94c4c86ad4685c1b9d` 和 Child/Gitlink `765a06b73c10c7fb4ccd30c38c96ceadec88385d`，分支 `codex/g2-data-c-certification-audit-82`。Child 使用原仓已合并的 PR #19，审查其三个文件的差异。原始训练快照的证据仍可用 `inspect_legacy_v2=True` 查看。候选正式 Provider 需要新 v3 认证收据，沿用 DATA_C v2 及 CAP2 recipe，由新 Data ID 固定认证内容。

## 按严重程度排序的发现

1. **P1 · 原生 Phase5 未应用 Train 名册。** 原版确实构造并验证分割，但 Phase5 直接让 rank planner 从不带过滤的 G1 catalog 取 Episode。若按这个固定版本训练，Val Episode 属于可训练集合。检查了实际 factory、预检和 rank planner 构造，CPU 验证只走计划与数据，未启动训练。候选 Gitlink 固定到 Child PR #19，复用已发布修复。G2 preflight 给 catalog 传入认证 Train key，过滤发生在原始 flat offsets 计算之后。现有 G1 调用仍使用全 catalog。 [原始 Phase5](https://github.com/wxwy/cosmos-framework/blob/9370c3858532b4d61630138431145c8360e86eb0/examples/psm_wma_robocasa_corrected_phase5.py#L1182) · [候选 Phase5](https://github.com/wxwy/cosmos-framework/blob/765a06b73c10c7fb4ccd30c38c96ceadec88385d/examples/psm_wma_robocasa_corrected_phase5.py#L1182) · [Child PR #19](https://github.com/wxwy/cosmos-framework/pull/19)
2. **P1 · 正式 Data ID 没有固定实际 CAP2。** 原版用语言 recipe、C 快照和划分计算 Data ID，逐 Episode 的语言数据与完成记录只在各自目录中自洽。使用同一 recipe 替换文本并重算 `text_id`、文件 SHA 和语言 `COMPLETE`，不会改变旧正式 ID。也复现了记录自称 frame 0、引用确有匹配 SHA 的后续 SG 时原版读取器接受。候选认证从 DATA_C 绑定的 View manifest 中取 frame 0，以发布的 SG、TaskEntitySet 和原 caption 复算完整 CAP2，封存每条文本及完成记录 SHA。修复后的运行时同字节校验加上四 Episode 缓存，不必在读取文本时重新访问 View。 [原始 Data ID](https://github.com/wxwy/psm_wma/blob/ab3d466eea259795c539bdee50f714f48dc7c91b/tools/g2/certify_training_snapshot.py#L272) · [原始语言读取](https://github.com/wxwy/psm_wma/blob/ab3d466eea259795c539bdee50f714f48dc7c91b/g2/language/initial_context.py#L633) · [候选认证](https://github.com/wxwy/psm_wma/blob/3aff85a702f5e3b05bc5cd94c4c86ad4685c1b9d/tools/g2/certify_training_snapshot.py#L39)
3. **P1 · 因果、完成与 View 几何检查不全。** 原版认证允许窗口的 `spatial_state_ordinal` 指向另一个时间点，只比较窗口自报 frame、ordinal 范围和少量窗口字段。原版 `read_common` 的同类反例复现。原版 R2 另有一次实际 state frame 对照，可能在读取时报错，未观察到模型读到未来帧。旧认证还有只比较 DATA_C 完成记录所载 SHA 的分支，未要求该记录为完整正确的同版本发布。旧运行时读取空间投影 JSON 未绑定到 View manifest 中的实际字节散列。候选共用严格的完成和时间线验证，每个 action 窗口都核对原始 20 Hz frame、16 个 action 和第 17 个 observation，按实际时间线找到最近因果状态；在全部状态验证双俯视图、owner 和目录，使用已认证的 manifest 校验投影字节。 [原始认证](https://github.com/wxwy/psm_wma/blob/ab3d466eea259795c539bdee50f714f48dc7c91b/tools/g2/certify_training_snapshot.py#L199) · [原始 Provider](https://github.com/wxwy/psm_wma/blob/ab3d466eea259795c539bdee50f714f48dc7c91b/g2/data/aligned_provider.py#L427) · [候选因果验证](https://github.com/wxwy/psm_wma/blob/3aff85a702f5e3b05bc5cd94c4c86ad4685c1b9d/g2/data/joint_index.py#L206)
4. **P2 · Provider 每个 rank 的 I/O 与保有资源随语料增长。** 原版认证入口扫一次全部 C，Provider 再常驻所有 C 窗口字典和 B tensor。每个已访问 Episode 也会保留自己的 reader 和 mmap 缓存。候选构造只读小索引，按需读取经过认证的 Episode，有界保留最近四集的 DATA_C/DATA_B、CAP2 和 ViewReader，淘汰 ViewReader 时主动关闭。当前窗口的投影文件只需一次读入，所选 latent 继续由已有 ViewReader 读取。原样本复核还发现 View-first Reader 每次冷读会重新解压并解析完整工作源。候选在索引 SHA 已固定时校验相同的工作文件、READY 和 gzip 回执，原有未固定索引的入口仍走完整验证。无旧版 RSS 对照实测。 [原始构造](https://github.com/wxwy/psm_wma/blob/ab3d466eea259795c539bdee50f714f48dc7c91b/g2/data/aligned_provider.py#L317) · [原始 Reader 持有](https://github.com/wxwy/psm_wma/blob/ab3d466eea259795c539bdee50f714f48dc7c91b/g2/data/aligned_provider.py#L527) · [候选按需索引](https://github.com/wxwy/psm_wma/blob/3aff85a702f5e3b05bc5cd94c4c86ad4685c1b9d/g2/data/aligned_provider.py#L269)

## 代码合理性

- **PASS · 双顶视图共用一个 joint。** C v2 每个 Episode 共享 action、state15、SG、文本、side views 和窗口时序，只新增两张俯视图各自的一份真实引用。两版共用投影、组成员与 VAE recipe，各自指向独立的 owner 和 record。选图只在 R2 请求时选择一个顶视图。不存在的方向明确拒绝，当前候选继续读取已发布 latent。 [DATA_C 构建](https://github.com/wxwy/psm_wma/blob/ab3d466eea259795c539bdee50f714f48dc7c91b/g2/data/joint_index.py#L288)
- **PASS · CAP2 构造和生效范围。** 候选沿用同类同标签同房间的分组、距绑定实体的距离后按 Entity ID 打破平局、每组最多两条。实体绑定留在事实来源，formatter 使用原指令、当前候选文字和固定输入几何。没有发现 inside/on 推断、专家动作或后续状态正例。原始文本审阅标记 `production_template_frozen=False` 与在线 Full Map parity 未认证由快照入场校验表达。 [CAP2 分组](https://github.com/wxwy/psm_wma/blob/ab3d466eea259795c539bdee50f714f48dc7c91b/g2/language/initial_context.py#L207) · [Child 静态文本](https://github.com/wxwy/cosmos-framework/blob/765a06b73c10c7fb4ccd30c38c96ceadec88385d/cosmos_framework/data/generator/action/utils/static_task_text.py)
- **FAIL · 原版生产和验收路径有不同强度的条件。** 候选让生产复核、认证和训练读取共享 DATA_C/DATA_B 校验，划分只调用原 G1 的 `split_episode_ids`。认证到独立目录，先封存并读回，再原子发布整个目录，出错可重新发布到仍未占用的路径。存量 v2 快照可显式审阅。完整离线认证负责覆盖全部索引，Provider 保留按需数值校验。依照这两个入口的执行成本分工，避免在多 rank 启动时重跑全量离线认证。
- **NOT_RUN · 真实 Phase5 运行门。** 实际模型 R1／R2 训练、DCP、FSDP2、训练断点恢复、Session cache、GPU 与在线 Full Map GT 不在本次证据范围。CPU fixture 和真实 read-only 计划验证只说明对应的数据接口。

## 独立复现与候选验证

| 检查 | 结果 |
| --- | --- |
| 候选 CPU 和静态检查 | **PASS**，Root 384/384，Child 48 通过、1 跳过（Phase4A 可选旧数据调试）。Ruff 与 11 文件格式通过。Root 有 27 个既有 fork 弃用警告 |
| 固定原版 CPU | **PASS**，35/35，零失败、零跳过。独立于 Issue 中用户报告的 31 项 |
| 原版两个反例 | **FAIL**，原语言 Reader 接受晚帧 SG，原 `read_common` 路径接受伪报 frame 0 的未来 ordinal。候选逐项拒绝 |
| 划分及原生 plan | **PASS**，实用 G1 catalog 的 9,126 条含 90 条 Val。Phase5 catalog 精确包含 9,036 Train、零 Val，9,036 条原始 flat offset 和 2,063,614 窗口匹配。8 个 rank 的 CPU plan 生成 64 个片段，均属于 Train |
| Frame 0 CAP2 和成品索引 | **PASS**，9,126 EP 共 2,085,331 个窗口。9036 Train / 90 Val 分别有 2,063,614 / 21,717 窗口。所有 CAP2 由固定 frame 0 来源复算，并与已发布文本完整匹配 |
| Source Reader 兼容和冷打开 | **PASS**，18 类各一条真实 Episode，两条路径的 cache manifest 和所有逻辑索引完全相同。完整解压 7.428 s、已固定索引 0.066 s，单次中位数 399.385 ms 和 3.575 ms。交替调用顺序，清除了进程内解码缓存，测量只覆盖索引打开 |
| 正式 Provider | **PASS**，真实 6 EP 含 Train 与 Val、各初／中／末共 18 窗口，R2 两种顶视图共 36 次通过。18 对保留各自实际图片内容身份，投影与 side views 一致。R1 给定不存在的 View 根仍有合法文本/state15、零 View 读 |
| Provider 有界资源 | **PASS**，全量索引打开后未预载 Episode。经过 6 个唯一 Episode 后保留 4 个 ViewReader。实测额外 4 个 FD，`close()` 后回到起点。完整快照重开 22.801 s 后的暖进程，Provider 构造 0.620 s。未做生产多 rank 训练吞吐或旧版 RSS 对照 |
| 原始结果与版本证明 | **PASS**，旧 v2 收据 SHA256 `4252e4b5e9dd6fab99b162fb571182ca309e8c8469445b6b5b43a5e37c717339`，正式 DATA_C manifest SHA256 `4283e518d5f8b75dd76cc4275a4463c1624f13a32972088f2fbf7965c0c5ed66`。隔离复核按原版本重开历史 v2 |

迭代中的真实读取发现候选曾以路径对象查询字符串键的 manifest，已改为规范 POSIX 字符串并补了真实入口回归。新增回归还证明固定 `projection_id` 而替换文件中的米制数值会被原始 SHA 拒绝。第一次 Child 集合运行用了关闭训练模块导入的开关，准确复验使用 `COSMOS_TRAINING=1` 加载 CPU 测试依赖，环境隐藏 CUDA 设备。

候选完整离线认证用时 120.46 秒，峰值 RSS 976,020 KiB。快照身份为 `8eaa187687feb91be56e9e2044797a3258a3d7c86b10f522a9071e056b1d869c`，训练数据身份为 `64e737a2bab7d3a053d0549cbe7981c2944a64ac08fd039aab03fbf151cc683e`，G1 划分身份为 `2949df28790d9254bb018ee0018c8a49aab5f718c9eb9f0e3ba7091ffb57105a`。两次隔离认证的收据和完成记录逐字节一致，收据 SHA256 为 `d464b41db8051a222d1864f5d6f6eea7123ab9e6b15e8f9ddb865653620570ed`。新证书只发布到服务器隔离目录。原始 log/XML、数据和测试输入留在服务器 `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_issue82_codex_20261119.VtZJAQ/`。仓库的辅助命令和摘要只含源码、来源身份、统计和复现命令。 [复现命令](../evidence/2026-11-19_issue82/commands.json) · [验证摘要](../evidence/2026-11-19_issue82/results.json)

## GPT 复审范围

请在 [Draft PR #83](https://github.com/wxwy/psm_wma/pull/83) 按固定 Root 和 Child 复审四项发现，重点检查旧证书显式审阅、新证书内容封存、双顶视图完整性和 Phase5 的 Train 名册。旧 v2 快照沿用历史审阅入口，采用修复后的正式 Provider 时使用独立认证的 v3 快照和它的 Data ID。当前项目处于 Draft 复审。
