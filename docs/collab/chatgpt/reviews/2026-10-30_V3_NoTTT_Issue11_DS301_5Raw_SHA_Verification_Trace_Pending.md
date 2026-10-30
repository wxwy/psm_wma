# No-TTT Issue #11 — DS_PRO 301 CPU Gate 五份原始证据字节级复核（增量）

- 日期：2026-10-30（Asia/Shanghai）；类型：**已提交 DS 独立 CPU 证据的增量审核，不是源码 Code Gate 复审**。
- **Frozen Formal Root：`e0fe911dfb9fd34957234828195cf051713f6c3d`；Child/Gitlink：`f6a92d47b6dac7998ddc58b3da26ef93f8068dc7`**；已有 `APPROVE_CODE` 保持。
- Evidence 来源：用户在当前会话上传的 DS_PRO 原始证据 copy-paste package，文件标题 `DS_PRO Issue#11 NoTTT Async 301 CPU Gate — frozen raw evidence submission (copy-paste package)`。这是用户提供的原件正文，不是 GPT 通过服务器连接直接读取的文件；DS 执行现场仍仅有其报告/路径见证。
- 旧 Review `docs/collab/chatgpt/reviews/2026-10-29_V3_NoTTT_AsyncOverlap_Issue11_DS301_Independent_CPU_Evidence_Review.md` 的“raw bytes 尚未审阅”状态**在本增量更新为5份完整文件已可复核；不回写篡改原审阅时间点**。

## 直接可复核的结果

GPT 从上传文本提取了五个完整 fenced raw sections，按原始换行方式形成逐字节文件并用 SHA-256 重新计算；与 DS 提供的6项清单中对应5项 **5/5 完全匹配**：

| 文件 | 计算 SHA-256（匹配DS清单） |
| --- | --- |
| `gate.json` | `bef86e20e36687c92ad7982be69652a3d0ed753ee5f852f6ead2d6f4d78afa7c` |
| `async.xml` | `85468232f2c7dc9f9ae6921a32cfa13b5be0489440bf7e4572377b1fcfa101bb` |
| `regression.xml` | `159d813edf4b119c0796d038973ca28a6945f291c43af02bc1d63b6d2e5fbfe8` |
| `environment.json` | `b4f1a20ba7c9977eaa89658a99a0a7f38611bcb1394e562b0430ab6c2b116e70` |
| `source_sha256.json` | `69ff4b476d694b12da32eb7173cfc3dc2d961fa829c24fa8a85cba5fda622d60` |

1. 直接解析 `gate.json`：`status=PASS`，实际5个 stage（import_origin / ruff_check / ruff_format / async / regression）exit0；Root/Child/Gitlink与上面精确 Pair 匹配，`syntax_files=13`，`source_unchanged=true`，`real_gpu=false`，`real_dcp_resume=false`。
2. 直接 XML parse：`async.xml` 72个独立 testcase，其中 loader29、recipe19、trainer24；`regression.xml` 229个独立 testcase（52+13+29+15+11+40+20+49），合计301，**301个classname+name无重复**，两个 suite 均为0 errors/0 failures/0 skipped；与 Gate 总计完全一致。原 `test_optional_real_data_debug_smoke` 未收录，符合禁止真实数据的冻结 CPU Gate。
3. `environment.json` 显示 Python3.13.11、torch2.10.0+cu128、pytest9.0.2、Ruff0.12.7、`CUDA_VISIBLE_DEVICES=""`、CPU/offline环境；CUDA软件依赖存在不等于运行了GPU。
4. `source_sha256.json` 18条，与独立候选先前绑定的 Formal Source Hash 列表逐项比对 **18/18相同**；该源码内容与先前 GPT 核对的正式Git Blob对应。`source_unchanged=true` 是生产CPU Runner结论，此粘贴未单独提供两次独立 before/after source dump。
5. 原 `no_ttt_async_loader_test.py::test_actual_source_transform_next_member_and_next_window_overlap` 的实际 JUnit testcase **PASS**；此前源码核查确认该测试必须真实计算后续Member、下一Window的 Source/Transform与 CPU fake-compute 的正时间交集；从而有直接**测试行为PASS证据**，不是仅仅相信DS文字或Worker PID出现。

## 尚需一份原件方可完成6/6直接审计

`timelines/overlap_trace.json` 第六项清单 SHA-256 为 `27357f1034a0b2ea91e887240c6566c1aac2630f37bd5f983123a332e3396c11`。**上传文本仅有结构头部、四个aggregate overlap数、2个Worker PID×3Window×4Member的事件计数清单，没有完整约92KB含 monotonic start/end 的 `async_trace`。** 因而该SHA无法重算，本轮DS计时毫秒交集无法被GPT直接逐事件复核。

- DS给出的摘要为：later-Member Source87.798ms/Transform128.965ms，next-Window Source20.455ms/Transform32.393ms；这些正值被成功Junit断言间接支持，**具体数值仍属于DS派生/粘贴证据**，不是GPT从本轮原始事件重算。
- 同一摘要还给出 CPU fake-only cold-start `async_window_wall=12142.119ms`、`sync=3452.383ms`、`main_wait=10376.207ms`，所以绝不据此宣称GPU加速。
- 可见XML时间带 `+00:00`：async starting UTC 15:13:59、regression starting UTC 15:22:15，对应北京时间约23:13–23:32；上传正文末尾写“15:13–15:32 CST”存在**8小时标签差异**。属非阻断元数据更正，不影响JUnit及哈希验收；请DS后续注明UTC/北京时间口径。
- 全目录 `evidence_manifest_sha256.txt` 663项仅给了路径；不属于当前冻结的最小6项 raw Gate，**不要求上传全部663项或重跑301项CPU测试**。

## 最终状态与下一动作

- **`DS_CPU_TEST_EXECUTION=PASS_VERIFIED_FROM_PASTED_RAW`**：5份完整raw byte哈希一致，301个XML唯一用例全过；源未变及精确身份有Gate记录，作者的原始实现 Gate `APPROVE_CODE` 不变。
- **`DIRECT_TRACE_RAW_HASH_AND_MS_RECOMPUTE=PENDING_ONE_FILE`**：只缺已生成的完整 `timelines/overlap_trace.json`，故完整6项 raw Evidence Archive 审核维持 **PARTIAL / Evidence-only OPEN**。这**不是**新生产代码blocker，不需要任何CPU重跑或代码修改。
- 仅请DS以**隔离Evidence-only路径或仓库分支**提交这1个92KB原始trace（不修改内容），提供其现有SHA与路径。GPT只对这一文件做1次Hash+事件交集增量核验后可关闭最后的raw审计。
- `REAL_GPU_PERFORMANCE=NOT_RUN`、`REAL_DCP_RESUME=NOT_RUN`，此前Compact严格GPU梯度Parity历史 `FAIL_PARITY` 仍不变。正式NoTTT Job仍使用旧RAW Loader `nw8`、GPU4–7活跃；Owner未授权GPU/停训/同Job并发Resume/正式Job切换，既有GPU资格验证提案仍为 `PROPOSED_NOT_AUTHORIZED`。
