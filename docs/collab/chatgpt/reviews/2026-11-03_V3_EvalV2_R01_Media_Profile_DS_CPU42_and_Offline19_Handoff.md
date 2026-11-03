# GPT → DS_PRO — R01 Media Profile 修复后 CPU42 + 原 R01 19视频离线核验

**状态：待 DS 执行；只授权隔离 CPU/文件核对，禁止启动新 GPU、模型、仿真或正式 V3 合并。**

## A. 严格身份

- 已批准最小 Root 实现 `2d1ad80f89ab4cc0e275ff4341f064954870abdd`，保持原 Child/Gitlink `c93f2abf4fb27d36176ff8db094379a853cec796`。候选 `v3-eval-v2-media-profile-20261103` 文档HEAD仅提供作者Evidence；**不要用 docs HEAD 取代 Formal Root**。
- GPT Source Code Gate `APPROVE_CODE`：`docs/collab/chatgpt/reviews/2026-11-03_V3_EvalV2_R01_Media_Profile_2d1ad80f_c93f2abf_Incremental_Code_Gate_APPROVE_CODE.md`。
- 当前旧 R01 的 `R01_FRESH_EXIT=1`、`media_summary=MEDIA_INCOMPLETE` 是历史不可变事实；DS 原报告的19 MP4/19回执/19 ACK、Core/SR1/1成功只属运行时 evidence，不能人为把旧 Run 改为Exit0。

## B. DS 独立 CPU42（不可照抄作者状态）

取候选 Evidence（仅读）：`docs/collab/codex/evidence/2026-11-03_eval_v2_media_profile_author_cpu/run_cpu.py` 和 `red/frozen_test.py`、`final/invocation.json`。
在**新的、与生产/旧证据不重叠的** detached clean Root+Child checkout 上，将 Evidence 驱动和 frozen test 复制到新外部目录。冻结测试 SHA256 为 `d5f32f29936bebedc94301e7f7a528b8abdcd26d96fa10d5d9b3aa28ca8fab8a`；不要修改测试/源码/fixture 或共享解释器环境。

作者提供的 CPU driver 实际用法（本机真实绝对路径由 DS 填入，不能照抄占位符）：
```bash
# 假设已确认独立 detached clean ROOT、Child/Gitlink，
# 已复制官方候选 read-only Evidence run_cpu.py / frozen_test.py 至外部 EVID/tools/
export PSM_PROFILE_ROOT=/ABS/INDEPENDENT_ROOT_AT_2d1ad80f
export PSM_PROFILE_FROZEN_TEST=/ABS/INDEPENDENT_EVID/tools/frozen_test.py
CPU_PYTHON /ABS/INDEPENDENT_EVID/tools/run_cpu.py green \
  /ABS/NEW_EMPTY_DS_CPU42_OUTPUT \
  2d1ad80f89ab4cc0e275ff4341f064954870abdd
```
要求：Root HEAD/Gitlink `2d1ad80f89ab4cc0e275ff4341f064954870abdd`/`c93f2abf4fb27d36176ff8db094379a853cec796`；运行前后工作树 clean；Python 3.13 环境满足合成 ffmpeg/Store 依赖，`CUDA_VISIBLE_DEVICES=""`；42/42 PASS、0 fail/error/skip，Ruff check/format、py_compile、source-only diff --check PASS，保存原始 JUnit、invocation、gate、pytest log及真实运行环境路径/版本/hash。失败则 `FAIL`，缺依赖 `BLOCKED_ENV`；不要自行重跑旧379/122或 GPU。原作者的旧 RED2 已保存，无需 DS 再跑。

## C. 原 R01 19真实媒体离线 Reconciliation（同样禁止 GPU）

1. **先唯一确定 DS 2026-11-03 R01 原始 `out/R01` 完整目录**（以本机先前运行 evidence/Manifest 的实际绝对路径为准），只读检查/核对 Root/Child SHA/Manifest digest；记录原 `R01_fresh.exit=1`、原 `media_summary.json.status=MEDIA_INCOMPLETE` 与它们的路径/hash。**不能修改、重命名、覆盖、删除旧 R01 任何文件，不能修改旧 FAIL 记录**。
2. 将 R01 **必需的完整 Run 数据**（`manifest.json`、`tasks/`下的 Episode、`_internal/` Store 账本/锁、Core summary、`episodes.jsonl`、19个真实 MP4+Receipt 等）拷贝到**一个全新隔离 CPU 校验目录**，严格检查文件/目录安全与克隆的原始字节hash。可用安全文件系统拷贝；禁止在原目录里运行会写 `media_summary.json` 的 `publish()`，也不允许将孤儿文件“修成匹配”。
3. 在 Formal Root `2d1ad80f89ab4cc0e275ff4341f064954870abdd` / Child `c93f2abf4fb27d36176ff8db094379a853cec796` 的独立 CPU Python 环境中，**只对副本**调用真实代码：`Store(copy_root, read(copy_root / "manifest.json"))`，`with store.locked(): report=robocasa_eval_v2.generated_media.publish(store)`，所有入口与依赖必须来自正式干净 checkout。此方法会写副本的 `media_summary.json`，**原目录保持未写**。必须让真实 `publish` 检查 Episode Completion、19条 MP4 inventory、全部19条 receipt Episode/generation/attempt/index/hash 绑定，不能模拟或跳过校验。
4. 对副本中的 19 个实际 MP4 再做**CPU-only 全帧**解码验收（`ffmpeg -v error -xerror -i <file.mp4> -f null -`，每文件exit code=0）；不要把原先 `ffprobe` 仅元数据探测算作完整帧解码。
5. Gate 期望：`report.status=COMPLETE`、`episodes=expected_episodes=1`、`expected=saved=acknowledged=19`、`errors=[]`、19/19视频全帧解码成功；`summary.json` Core/SR仍1/1 valid/success，进程/媒体收据不变；副本以外的原旧 out/R01 原始字节/hash 未变。若存在任何 receipt/identity/hash mismatch 或其它异常，明确 `OFFLINE_RECON_FAIL`，给出精确首个文件/源码栈/错误内容，不得为闭 Gate 人工更改视频或 summary。
6. 新 DS 证据保存 `R01_reconciliation/evidence/`（严格新路径），包括 Formal pair、Python版本、完整执行命令、copy root、源文件hash、原失败状态与副本新 `media_summary.json`、完整19条验收CSV/JSON（每文件大小、帧数、SHA、收据绑定、ffmpeg exit）、stderr、原目录只读未变声明。**离线重算成功≠原 R01 运行退出码变为0**，必须并列展示。

注意：`publish` 用 Store 的安全锁和路径方法，若复制遗漏 `_internal/.run.lock` 等文件会无法合法调用；应复制足够完整的原始 Store 结构，**不可为测试伪造账本或绕过校验**。

## D. DS 交付与 STOP

以 `DS_PRO — R01-MEDIA-PROFILE-01 independent CPU42 + offline actual19 acceptance` 回答，分别报告 `CPU42 PASS/FAIL/BLOCKED_ENV` 和 `OFFLINE19 PASS/FAIL/BLOCKED_ENV`，两者不可混为一个 Gate。提交真实绝对证据路径、CPU原始JUnit与离线19清单/汇总及校验前后字节身份，**完成后即STOP**，由 GPT/Owner 审阅决定后续硬件 Gate/是否合并，不自行重跑1EP GPU或开启900EP。

不可访问/查询管理其他 GPU 任务或训练，不碰 GPU0–3/在跑训练、NoTTT、out2、历史 H2/H3、正式 V3、Checkpoint/DCP。DS只可访问原 R01 out 的**只读副本制作所必需文件**，禁止触碰其它历史项目成果。
