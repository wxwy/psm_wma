# PSM-WMA V3 Stage B2-B 单段梯度接力 CPU/static 实现记录

- Gate：`V3-STAGE-B2B-SINGLE-SEGMENT-GRADIENT-RELAY-CPU-STATIC`；状态 `REVIEW`，本记录不授予 closure。
- 设计 authority：root `bf5c8d134014d0023a03c25f95d8e971922f40fd` 的 B2-B design v0.1 与 resource profiles v0.3。B2-A 已关闭 formal pair：root `21f20f2c436e9627a938148afca039da6023d145` / child `366501b3b4626f30f0739d2e5765139a52f2308f`。
- 实现 child：`bf6c80e679812b7d2881d6a54aa0b518299e3869`，已推送 `v3-local-ttt`。root Gitlink 指向该提交；root SHA 以本记录所在提交为准。

## 范围与行为

child 仅新增 `cosmos_framework/model/generator/mot/local_memory_native_segment.py` 和 `local_memory_native_segment_test.py`。单段 runner 从 `model.net.local_memory_runtime` 复用同一 encoder/core；核对 optimizer 精确选择所有 `local_memory` 慢参数（CPU fixture 为 165,312），host 参数冻结。只接受单 slot、T=16、单 GA member、精确 valid count 和 pending capability。S0 仅计入均值，其他 consumer 用 detached leaf 串行执行 `loss/N_valid` backward；回收每个 leaf 梯度后对原 B0 prefix 接力反传。成功顺序为慢参数梯度核验、事务成功标记、Local-only optimizer step、参数 finite 核验、B0 sidecar/调度 frontier commit。

失败时清空梯度并 discard pending，已提交的 sidecar/frontier 不变；optimizer step 已开始后若失败，runner 标记为不可重试，要求重启。callback 输出仅保留脱图 metadata；sample-coupled auxiliary loss 被拒绝。未修改 B0/B1/B2-A production、trainer、launcher、DCP、inference、GPU 配置或正式 Edge recipe。

## CPU/static 证据

- 工作目录：`/disk/rl/worktrees/cosmos-framework-v3`；解释器：该目录 `.venv/bin/python`。关键环境：`CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu LD_LIBRARY_PATH='' PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1`。不访问外网；无 checkpoint/真实数据集；B1 producer 使用 pytest 临时 H5 fixture；pytest 缓存禁用。
- 定向命令：`.venv/bin/python -m pytest -c /dev/null --noconftest -p no:cacheprovider -q cosmos_framework/model/generator/mot/local_memory_native_segment_test.py`；22/22 PASS。
- 合并命令：同一 pytest 前缀与参数，传入 `local_evidence_test.py`、`local_memory_segment_test.py`、`local_memory_segment_adapter_test.py`、`robocasa_latent_evidence_test.py`、`robocasa_segment_producer_test.py`、`memory_prefix_test.py`、`local_memory_native_segment_test.py`；175/175 PASS（3 条第三方 torchao deprecation warning）。
- 定向覆盖：S0/Local mapping、T16 stream order、真实 B1 producer 交接、monolithic 与 serial 梯度等价、完整 Local optimizer inventory、host 冻结、step 后才 commit、continuation、forward/loss/leaf/relay/optimizer 失败与 stale capability、多 member/count 拒绝。
- `.venv/bin/ruff check` 与 `ruff format --check` 检查上述新增两文件均 PASS；child staged diff-check 与 root diff-check PASS。未运行 GPU/4090 smoke、真实 OmniMoT callback 或正式训练；这些属于后续 Gate。

下一步：对本 fresh child/root pair 做独立审核；本记录不代替审核结论。
