# GPT → DS_PRO — V3 B1 P0 GPU Smoke 冻结 CFG 全局 RNG 单线程错误：修复代码 CPU Gate

**日期：** 2026-10-15  
**执行者：** DS_PRO：独立 READ-ONLY CPU 验证；可在 `/tmp` 构造附加测试脚本，但 **不得修改 GitHub 代码或冻结 Child/正式训练文件**。  
**当前阶段：** `B1_P0_THREADED_CFG_LOCAL_RNG_CPU_GATE`；**禁止 GPU / torchrun / 模型加载 / 真实 DCP 恢复 / 训练**，需新版本独立 CPU 验收并获 Owner 新 GPU 授权后再进行 P0 重跑。  
**精确候选 B1 Root SHA：** `a32395911c9913a5e02eb8a17e0bac11fe9ff4e0`（分支 `v3-gateb1-numeric-implementation-20261014`）  
**精确 Child/Gitlink：** `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`  
**旧 P0 GPU BLOCKED 的 Root：** `46e9cc0e5dc97a1f7f813b2a332b095aa1062a4a`。不得把旧 CPU PASS 或旧 GPU授权视为新 SHA 的批准。  
**差异审查：** `git diff --name-only 46e9cc0e..a3239591` 应 **恰好两个**路径：
- `tools/gates/v3_gateb1_producer_cfg.py`
- `tools/gates/test_v3_gateb1_producer_cfg.py`

**冻结对照（禁止改变）：**
- Source Index8 Root `b159f45906f7261d028aecc226ab7f2bb9807eb9` / Child `937066ffd90f2bf783ad4fbb4909e9c0b8922982`
- Target Packed128 Root `c4731bca1a590663db88bd6cd74dbcf9fd513a85` / Child `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`
- Owner frozen r2 policy SHA `bcb9f8d699c0ce6c79d54cf5bb213c157665798c38dae9daeb6b4a1607e63fda`
- 原始 iter1300 B0 DCP FP `2e409afe788f4faf2cc1f5db8d500638a219647dc90283f9687863212d77d999`
- 上述配置、数据/模型、B0、前轮144 CPU tests、4×合法 Prepare 证据已经完成，**不重复数据集全量扫描、B0 或全仓审计**。

## 1. 背景与问题定位

DS 的旧 SHA P0 GPU 报告证明 8×H100 分布式初始化、4B 模型构建、FusedAdam 和 **原始 iter1300 五组件 strict DCP 恢复成功**，但 SOURCE 的第1个原生训练步在 `v3_packed128_gateb_compare.scoped_python_cfg_rng` 因 `threading.active_count()==1` fail-close：真实 FSDP8 进程有 8–13 个无关框架后台线程。没有 1301/1302 训练完成数据、没有 TARGET 运行，也没有数值等价结论。首次 Nemotron 配置找不到源于 **CWD != 冻结 Child 根目录**，后续已靠正确 CWD 修正。

**GPT 改法并非简单放宽 `active_count`：**
- 原 B0 CPU helper `scoped_python_cfg_rng`（使用全局 `random.seed`）不改，已关闭的 B0 不再跑。
- 新 B1 `scoped_keyed_native_caption_transform` 验证真正的 `ActionTransformPipeline` + `TextTokenizerTransform`，使用 B0 原 `ConsumerKey` seed 和独立 `random.Random(seed).random()`，没有任何全局 `random.seed/getstate/setstate` 操作。
- **浅拷贝**当前原始 native Pipeline 与 Tokenizer，对副本禁用 CFG 随机抽样，随后在 native JSON prompt formatter **之后**，对原生 tokenizer 输入执行同样的 caption/drop 决定；仍调用冻结 Child **原生 Tokenizer** 处理文本。修改只存活在当前 Consumer 的 clone 中，原始 tokenizer/pipeline 对象和其它 Python 线程不会看到临时的 process-global seed。
- 仍要求 `threading.current_thread() is main_thread`、`num_workers=0`、真实冻结 class provenance、`cfg_dropout_rate=0.1`、`format_prompt_as_json=True`、未开启 IdleFrame 额外随机 dropout、ConsumerKey 正确，每 Consumer 必须恰好调用一次 TextTokenizer，否则 fail-closed。
- 已添加 5 个 synthetic 测试：64 Consumer 本地随机决策、后台线程共存下的 Native Producer 两次等价 replay、错误 CFG/接口阻断、缺失/重复 Tokenizer 调用、非主线程拒绝。

冻结 Source/Target 需要独立核实：
`cosmos_framework/data/generator/action/datasets/action_sft_dataset.py` 的 `ActionSFTDataset._transform` 为 `ActionTransformPipeline`；冻结 `TextTokenizerTransform.__call__` 中仅一处 Caption CFG `random.random()`；`ActionTransformPipeline.__call__` 先 JSON prompt 后 tokenizer；`format_prompt_as_json=True`、`idle_frames_augmentor is None`、Rate 0.1。确认 `ActionPromptJsonFormatter` 没有随机抽样。**不能自行改 Child 或 Mock 掉未覆盖的新随机站点**。

## 2. 一批独立 CPU 验证指令（必须真实记录退出码）

使用此前 DS 通过的 Python 3.13/torch/pytest/Ruff 环境，在新的 **clean detached** B1 Root/Child 精确 SHA：

```bash
set -euo pipefail
export CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
mapfile -t B1_IMPL < <(find tools/gates -maxdepth 1 -type f -name 'v3_gateb1_*.py' | sort)
mapfile -t B1_TEST < <(find tools/gates -maxdepth 1 -type f -name 'test_v3_gateb1_*.py' | sort)
test "${#B1_IMPL[@]}" -eq 12
test "${#B1_TEST[@]}" -eq 11
python -m py_compile "${B1_IMPL[@]}" "${B1_TEST[@]}"
ruff check --no-cache "${B1_IMPL[@]}" "${B1_TEST[@]}"
python -m pytest -q tools/gates/test_v3_gateb1_*.py
```

**预期：23/23 编译 PASS；23/23 Ruff 0 findings；原144 + 新5 = 149测试 PASS（报告真实计数，不得假定）。** 如果失败，STOP 并报确切报错、文件行、stdout/stderr；DS 不修改仓库。

## 3. 安全和数值精度的专门验收

1. **线程：** 在 CPU synthetic/可安全构建的 native-lite 环境启动至少一个活跃 Python background thread，调用 B1 真 `b0_consumer_cfg_scope`，要求不再 `active_count == 1` 拦截，也不允许将真正的数据 Transform 放在非主线程；`num_workers>0` 必须依然拒绝。
2. **局部 RNG：** 真 B1 路径不得调用 Python-global `random.seed`、`setstate` 或替换 `random.random`。在背景线程存在时，多次 Consumer-keyed replay 必须相同；没有外部 RNG 消耗时前后 `random.getstate()` 完全一致。与同一 seed 的原始单线程 Python CFG 一次 `random.random()` 应逐 Consumer 相符。
3. **原生语义：** JSON prompt formatter + 冻结 native TextTokenizerTransform 的输入/输出结构、caption blanking、token payload 完整 hash 不可改变。Transformer/Tokenizer 副本的 `cfg_dropout_rate=0` 仅禁用**重复抽签**，其余原生代码照常执行；原始实例属性不被写入。
4. **Fail-close：** 错 class provenance、非 ConsumerKey、rate 不是0.1、独立 per-view/tokenize_separately、额外 IdleFrame dropout、Tokenizer 0次或2次、非主线程与并行 num_workers，必须拒绝；异常后 producer 原来的实例方法恢复。
5. **冻结边界：** Full/Terminal、P0/P1、GA2 与原 B0 Fingerprint/Owner r2 policy 未改；`v3_gateb1_run._owner_receipt` 对旧 `implementation_sha=46e9cc0e...` 的原 Owner 授权必须在新 `a3239591...` 下拒绝，**绝不复制、改写或自动重签旧授权文件**。
6. **真正 GPU 仍未验证：** 测试不能假装有真实 FSDP8 Gradient/Optimizer/Local Fast State 等价证据。没有新 Owner 授权不得执行 torchrun、真正 DCP、SOURCE/TARGET 模型、Gate M 或 Formal30k。

## 4. 仅供未来获授权 GPU 重跑参考（本次严禁执行）

- 所有8张 H100 可与其他用户进程共存，只有当经 Owner 再次批准、预设最小可用显存与禁止干涉其它任务条件满足后才允许；重跑 **先 Source Index8 P0 repeat0 的1301/1302，人工审后 Target**。
- **工作目录 MUST 是各自冻结 Child 根目录** `cd "$LEG_ROOT/cosmos-framework"`，因为冻结 Nemotron JSON 模型路径相对 CWD；绝不修改冻结 Child 作修复。
- 真实原 DCP/latest 只读、独立 /tmp evidence、不允许自动重试；没有 P0 GPU 数值数据之前不扩展 P1/第二次重跑。

## 5. 验收报告

仅交一份：
`DS_PRO_V3_B1_CFG_LocalRNG_CPU_Verification_a3239591_2026-10-15.md`

包含 exact Code/Child SHA + 2文件 diff、23+23 lint/syntax、**实际测试数量**、真实冻结 Child 字节/源码 ABI 确认、后台线程+局部 RNG+token hash witness、所有负例、安全停机与剩余 GPU_UNVERIFIED。DS 仍不修改 GitHub。GPT 收到后做**新 exact SHA 的增量 Code/Evidence/Gate 审核**，届时再由 Owner 单独批准新实现的有界 P0 GPU smoke；**旧 `46e9cc0e` 的 GPU授权不能自动延续到 `a3239591`**。
