# V3 Stage B0 CPU Core Gate

- 状态：REVIEW；cx 实现；ChatGPT 设计/审核；用户 owner/最终裁决；ds 后续执行/测试。
- 基线：root `8596d7cf48c252870c0c194eed388f223ba402a1`；child `196b93b70b579023ef008030b0c18a6fde353c82`。
- 用户要求继续实施；ChatGPT 冻结本轮 B0 设计。按本轮 root 范围限制，本文件同时承载任务认领、设计与状态，不修改历史 TODO/SESSION。
- 实际文件：child 仅新增 `cosmos_framework/model/generator/mot/local_evidence.py`、`local_memory_segment.py`、`local_memory_segment_adapter.py` 和三个对应 `_test.py`，共6文件、1048行；root 仅新增本文件并更新 Gitlink。child 源码只在 `/disk/rl/worktrees/cosmos-framework-v3` 实现；root 内嵌 checkout 仅同步最终已提交 Gitlink。
- 参考 V2 `22acb13c1fdb4f146e51e3c26f1759c73e6d0d7e` 的同名 core/segment/adapter；逐项精简重写，不 cherry-pick。V2/v2 不改。

## 冻结合同

- visual96 + executed_action15；state/dt/age 禁用；policy 的 raw15/64D heads 不属于本层。
- evidence256、TTT64、fast hidden256、Local32、K4、inner_lr0.1、TBPTT16。
- S0 无 Local；t>0 严格使用 t−1 evidence。core scan 返回 `[B,T,4,32]`；沿 T 串行，各 row 独立更新，inner loss 对每 row 的32维取均值、再对 row 求和，不除 B。
- fast state 是 fp32 普通 tensor，candidate 更新不原位修改输入；W0、slot_queries 与 projections 为 registered slow 参数。
- B0 adapter 每次处理一个 slot segment；core 支持 B>1。后续 B_stream8、active_GA2 仅以 plan fixture 表达 N_window=256，不实现 grouped driver。
- scan/backward 成功标记不发布 live sidecar。精确 identity/transaction/result capability 校验通过后，commit 才 detach+clone；失败、discard、skip 不写 pending candidate。跨段继承 committed state，仅 episode end 或显式 reset 清除。
- 本层仅提供 CPU transaction 成功通知接口，不验证真实 trainer backward。测试使用合成 outer 标量证明梯度；不接 Cosmos objective，不附加 inner/reconstruction loss。
- 不接 SequencePlan/PackedSequence/OmniMoT/trainer/config/optimizer/checkpoint/producer/launcher，不加载模型/数据、不跑 GPU。

## 验证与交付

- V3 `.venv/bin/python` CPU pytest：32/32 PASS，无跳过，14.85秒；V3 Ruff check、format check 及双仓 diff-check PASS，child staged diff-check PASS。日志 `/tmp/cx_v3_b0_cpu.log`；JUnit `/tmp/cx_v3_b0_cpu.xml`，不纳入仓库。
- 测试覆盖精确维度、K4、因果时序、S0/PAD、fp32/参数归属、独立row学习率、事务成功/失败/skip、continuation、GA fixture无二次缩放。
- GPU gate：不适用本轮；训练接线及真实模型证据留后续 Gate。
- child 提交：`4fa4f35c102433bb007d2a3fd4a9fc7fe0b5149f`。先 child commit/push，再 root Gitlink+本文件 commit/push；root implementation SHA 为包含本记录的提交，交付时回报 exact pair；待 ChatGPT fresh review，不自授关闭。

### 可复现命令

工作目录 `/disk/rl/worktrees/cosmos-framework-v3`；只使用合成 CPU tensors，不加载 checkpoint/数据，不访问外网，不运行 GPU。

```bash
CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu LD_LIBRARY_PATH='' \
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
.venv/bin/python -m pytest -c /dev/null --noconftest -p no:cacheprovider -q \
cosmos_framework/model/generator/mot/local_evidence_test.py \
cosmos_framework/model/generator/mot/local_memory_segment_test.py \
cosmos_framework/model/generator/mot/local_memory_segment_adapter_test.py \
--junitxml=/tmp/cx_v3_b0_cpu.xml > /tmp/cx_v3_b0_cpu.log 2>&1

.venv/bin/ruff check --no-cache \
cosmos_framework/model/generator/mot/local_evidence{,_test}.py \
cosmos_framework/model/generator/mot/local_memory_segment{,_test}.py \
cosmos_framework/model/generator/mot/local_memory_segment_adapter{,_test}.py
.venv/bin/ruff format --no-cache --check \
cosmos_framework/model/generator/mot/local_evidence{,_test}.py \
cosmos_framework/model/generator/mot/local_memory_segment{,_test}.py \
cosmos_framework/model/generator/mot/local_memory_segment_adapter{,_test}.py
git diff --check
git diff --cached --check
```

pytest 禁用上游 inference conftest 和插件自动加载，避免其 GPU 环境设置介入本层。只对六个新增文件执行 Ruff format。成功判据为32项测试无失败/跳过、Ruff/format/diff-check退出0；任一失败则不推进交付。测试证明失败/skip不发布 pending candidate，continuation从committed state继续；不把 CPU 成功表述为生产训练或 GPU 通过。下一步仅为新 pair 的 fresh review；B1/B2 未实施，artifacts/v3/ 未触碰。
