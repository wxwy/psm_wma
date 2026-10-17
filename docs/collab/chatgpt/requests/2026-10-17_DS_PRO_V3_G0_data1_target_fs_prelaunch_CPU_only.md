# GPT → DS_PRO — V3 Packed128 G0 /mnt/data1 目标存储的最小 CPU-only Prelaunch Gate

**日期：2026-10-17**  
**状态：只读核查 + tiny synthetic FS probe；不是GPU/训练/模型/DCP运行授权。**  
**前序正式S0结论**：`docs/collab/chatgpt/reviews/2026-10-17_V3_Packed128_DROID_Fresh_S0_DS_Codex_readiness_evidence_review.md`。S0 READ-ONLY EVIDENCE `APPROVE_TO_CLOSE`；**G0 GPU Release BLOCKED**。只填这里的target FS/容量缺口，不重跑F0/F1、旧B1或全451GB索引。
**Frozen implementation Root：**`6ebf8998a7935f2ad690bb547c5db5e5a4322e6d`  
**Frozen Child/Gitlink：**`2d128ed5a07601cdd424974f99b67832eafeeb41`  
**候选正式输出卷：**`/mnt/data1`，已知用户可写父目录 `/mnt/data1/data_v2_0617/`；**Owner尚未确认此OUTPUT_ROOT，不得替Owner创建新正式Job**。

## 最小执行内容（仅无GPU的filesystem操作）

1. 确认上面Pair未变；`origin/V3`只是文档HEAD且生产gitlink仍是旧Child，未来GPU必须从原始formal Pair clean detached checkout运行。不要调整Worktree或Git历史。
2. **针对真实目的卷而非旧`/mnt/data`：**只读采集最新`df -B1`/`df -i`/`stat -f`/`findmnt`、用户写权限/潜在quota；记录当前空闲 bytes、mount/fsid、inodes、目录权限/祖先symlink检查。未发现quota标志时仅标`QUOTA_UNCONFIRMED`。
3. 在 **新隔离 tiny FS test directory**（比如`/mnt/data1/data_v2_0617/.psm_g0_fs_probe_20261017_<unique>`）模拟: 两个CPU进程同名`mkdir(exist_ok=False)`恰有一个成功；`fcntl.flock(LOCK_EX|LOCK_NB)`首进程持锁第二进程EWOULDBLOCK、释放后可重获；同FS file temp→flush/fsync→os.replace→dir fsync；小文件hash、pointer旧字节不被失败案例修改；外部只读检查文件真实存在。测试仅KB级/临时独立内容，不创建 `psm_wma_v3/corrected_phase5/<JOB_NAME>` 命名空间，不读旧DCP/body，**不得改动历史文件**。
4. 记录未来建议`OUTPUT_ROOT=/mnt/data1/data_v2_0617/psm_wma_v3_packed128_runs_<unique>`是否经过任何symlink祖先；`JOB_NAME`建议两种**尚不存在**且互不冲突的标识：`bounded_<g0_unique>`与`packed128_droid_fresh_<unique>`。**仅建议具体字符串/路径，不实际创建/锁定任何正式namespace**。
5. 将容量以旧C=**24,897,732,763B =23.188GiB**作为provisional估算：若Owner采用**三次启动 G0(1诊断DCP) + G1/G2(5正式DCP)**，按`6*C_old + W50GiB + R2*C_old ≈235.50GiB`预算；若未来G2在101安全硬停分为两次，则`7*C_old +W50GiB +R2*C_old ≈258.69GiB`。两者均须再加可能的其它共享写入风险，容量阈值不可把旧C当成新C的实测。该次目标卷报告时337.33GiB free；**本轮必须复测，不继承旧值**。建议初步停止线为 **current free <260GiB** 时不安排G0→500的完整四启动路线；如只授权G0，其实时时点容量门需由Owner单独规定，不能把本报告当GPU Release。
6. 留存本次FS探针的命令/RC/小JSON、随机写入前后hash/测试外部路径与`df`，并说明测试结束后小Evidence是否保留；**不自动删除任何旧证据**。不补做GPU`Config.validate`，不触发`torchrun`或CUDA Python。

## 输出、继续门

交一份`DS_PRO_V3_G0_target_data1_fs_prelaunch_CPU_only_2026-10-17.md`和small JSON，明确 `DATA1_TARGET_FS_PASS/FAIL/BLOCKED`、`SPACE_PROVISIONAL_OK/NOT_OK`，及未来新G0/G1运行时将使用的实际Output Root和建议Job名字（若Owner未批准，标注 PROPOSED）。如已有足够完整的、**相同`/mnt/data1`目标卷**tiny原子/锁/fsync成功日志，可直接引用并提供身份/命令/RC，不盲目重跑。

停止待GPT审核和Owner另行单次GPU授权。**不实施 G0/G1/G2，不清理未来或历史DCP，不修改代码和GitHub。**
