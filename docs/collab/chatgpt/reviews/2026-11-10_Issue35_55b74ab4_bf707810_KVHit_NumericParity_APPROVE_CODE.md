# Issue #35 — Prefix-aware Text KV 首次命中数值修复：GPT 独立正式审核

**日期**：2026-11-10。**Verdict：`APPROVE_CODE`（仅本次数值修复，严格限域）。**

| 角色 | 固定 commit |
|---|---|
| Formal Root implementation | `55b74ab461fda27e4ff6490023c828db0abc0a9f` |
| Formal Child / Root Gitlink | `bf707810f573e885f0966d65c232dc2a610d6a93` |
| 前一正式 implementation | Root `18be4a80a5ae4d97bc7d287034d24efab847c496` / Child `193627f42f4cd1ba6d563aefb8fa8f9428ecb56d` |
| 当前 Draft PR | [Root #36](https://github.com/wxwy/psm_wma/pull/36) / [Child #12](https://github.com/wxwy/cosmos-framework/pull/12) |

Root PR #36 的证据/账本 HEAD `5658adab2c6acc6f30926d8457386619fd527593` **不是**本次受审 formal implementation SHA；后续 review/Inbox 提交也不变更上述 pair。

## 1. 冻结合同、前序阻断与修复范围

前序 GPT 直接从真实 RoboCasa K1/source32、K16/source64 完整冻结请求（Batch/FastState/Prefix/RNG）复现：原 Local (KV OFF/Pack OFF) 与启用 Stage1 Prefix-aware TextKV 的 raw15 Action 最大差分别 `0.0049707889556884766`、`0.007069587707519531`；仅 Stage2 Pack ON/OFF 没有额外差异。30步 velocity Step0 首次填充与旧路径相同，Step1 第一次缓存命中开始不同。详见历史正式 [Issue35 GPT real replay finding](https://github.com/wxwy/psm_wma/blob/v3-local-prefix-attention-issue35-20261109/docs/collab/chatgpt/reviews/2026-11-10_Issue35_RealInput_KVCacheHit_ParityFail_IndependentReplay.md)。

本次 formal pair 相对上一 pair 的 Child 生产改动严格集中于：`mot/attention.py`、`mot/inference_text_kv_memory.py`、`mot/unified_mot.py`；另一文件为 `mot/prefix_text_kv_memory_test.py`。Root 实现只变动 Gitlink、`SESSION.md`、`TODO.md`。没有修改本项目训练、TTT FastState 更新、Sim/Worker、checkpoint mode、NoTTT 接入、全局 BF16、DCP inventory 或原生 recompile limit8。

## 2. 生产源码独立审核

- `attention.py` 在 B1 Prefix-aware 填充路径捕获**原生已物化**的 Prefix K 归一化值和对应原始投影输入；以 `_PrefixTextKVToStore` 区分普通 GEN/UND tuple，避免影响其他 MemoryState 类型。
- `inference_text_kv_memory.py` 将两张参考张量 `detach().clone()` 到**本次请求内、每层**的 `UndKVCache`，并在 `clear()` 同时释放。命中时当前 Prefix K/V 仍实时投影；只有当前 Prefix K 投影输入与填充时记录的输入**逐元素精确相同**，才以 GPU `torch.where` 选择原生填充的 BF16 归一化值；改变输入时选择当次计算值，V始终使用当前值。None、shape、dtype、device及B1/layout有 fail-closed 校验。
- `unified_mot.py` 仅当显式 Prefix-aware InferenceTextKV 状态有效时把未归一化的当前 Prefix K 交给 dispatcher。NoTTT/no-Prefix、普通 TextKV 及非此路径不受新参数影响。
- 缓存生命周期仍受单次 generate 的 install/finally/clear 限制，slow weights 在该请求内冻结。无需假设跨请求 FastState 一样。未发现本次增量引入的生产级 contract violation。

## 3. 独立 CPU 与 Evidence 验证

GPT通过 Remote Desktop Commander 在授权服务器新的 **clean formal pair** 上执行，不复用作者原始通过命令的返回值：

- 独立新增 Prefix/Text-KV 定向测试：**37/37 PASS**。
- 独立执行整个作者公布的 frozen scoped CPU Gate（实际调用仓库既有 `cpu_gate.py`，重新产生我方 JUnit/静态/source 哈希）：**213/213 PASS，0 failures/errors/skipped**；9 个 scoped 静态文件检查通过；**1487** 个源文件指纹前后相同。历史 `test_model_owned_all_continuation_never_initializes_w0` 已在之前审核确认是原有失败，本轮依约 deselect，未冒充 PASS，不能称全仓测试全绿。
- 修改范围对比及 Root Gitlink 由 GPT 从 Git对象再次核对，Root55b/Childbf707 均 clean，正式 pair 有效。

## 4. H100 同一真实冻结请求：GPT 独立执行结果

使用 GPT 自己上一轮的 `replay_real.py` 和 `replay_velocity_probe.py`，仅在**隔离工具副本**中更新 formal SHA，并扩展第三模式的逐步记录；没有修改生产代码。GPU6 H100、同一 Local-TTT iter15000 DCP、B1/H16/raw15、30步UniPC、guidance1，严格恢复每次 Request 原始 CPU/CUDA/NumPy/Python RNG、FastRecord、4×32 Prefix。每个模式重新读取冻结请求，避免输入污染。

| 真实冻结请求 | 原Local KVoff/Packoff | 修复后 Stage1 KVon/Packoff | 修复后 Stage2 KVon/Packon |
|---|---|---|---|
| K1 / source32 的 raw15 Action / Action / Vision | **与前序原始Local逐元素一致** | **逐元素一致** | **逐元素一致** |
| K16 / source64 的 raw15 Action / Action / Vision | **逐元素一致** | **逐元素一致** | **逐元素一致** |
| 30步 velocity vs 原始Local | 基线 | **30/30 完全一致** | **30/30 完全一致** |

GPU模型回放在两组 K 各完成3条模式、**均 exit0**。GPT随后通过CPU读取所有新产出的 PT，并与前序独立原始 Local PT 逐元素使用 `torch.equal` 验证：两组×三模式的 raw15 Action、模型 Action、Vision 均 **max_abs=0，changed=0**；进一步读取30×每模式的 BF16 velocity 原张量并逐步比较，K1/K16的 Stage1与Stage2相对原 Local的**全部30/30步均为max_abs=0、changed=0**。没有“最后动作巧合相同、速度预测仍不同”的遗漏。

此前与旧码真实闭环 `K1=0.00497079/K16=0.00706959` 的数值阻断项现由该新正式 Pair 的真实请求回放直接关闭。旧 Stage2 采集的输出仍是历史不同值；修复后新输出对齐的是**原始 KVoff Local**，不能错误地要求等于错误缓存下采集的旧 Stage2 动作。

独立服务器证据（**不上传原始张量**）：

`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/issue35_kv_norm_fix_independent_20261110/`

包含 `cpu/pytest.log` (37 pass)、`cpu_213_gate/gate.json`、`k1/result.json`、`k16/result.json`、`k1_all3/result.json`、`k16_all3/result.json`、原始输出PT、完整速度PT和 `independent_final_verdict.json`。**最终派生核验文件SHA256：`bb0bce146d3e5132311bba31492dbae972576c41db9915b359ea26bd7647b50c`。** 所有数据留在服务器，GPU4–7最终0MiB，没有残留相关进程，GPU0–3其他任务未操作。

## 5. 剩余限制与正式 verdict

**阻断项 `REAL_INPUT_STRICT_NUMERICAL_PARITY_FAIL_AT_STAGE1_CACHE_HIT` → `CLOSED`**，本轮未发现其他直接相关的 production blocker。独立 **`APPROVE_CODE` 仅限 Issue35 Prefix-aware KV 首次命中 BF16 归一化数值修复及现有 B1/two_way/30-step 两组真实冻结输入的严格一致性 Gate**。

本 verdict **不**授权：RootPR36/ChildPR12及上游PR32/33自动合并V3、真实完整Episode/SR、NoTTT新测试、更多图像/场景/Batch/布局、跨Session大规模压力、GPU吞吐/P50/P99、生产部署或第三项 Attention 优化。数值修复**后**的生成性能、尾延迟可能变化，必须另行独立测量，不应预设加速百分比；此前 Step1 差异关闭不代表Attention剩余性能问题已解决。

Review/Inbox 文档提交仅是 bookkeeping，不变更 formal implementation SHAs。