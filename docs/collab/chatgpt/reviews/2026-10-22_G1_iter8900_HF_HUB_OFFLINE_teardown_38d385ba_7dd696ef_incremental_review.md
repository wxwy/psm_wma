# PSM-WMA V3 — G1 iter8900 HF_HUB_OFFLINE 测试 teardown 定向修复增量审核

日期：2026-10-22
Scope：原已批准 G1 Owner cross-pair Resume **一行测试 fixture** 修复；不修改训练 Resume 生产算法、Checkpoint/Config/JobIdentity，也不触发GPU/torchrun。
**New formal implementation Root**：`38d385ba73ba991eddbfb99a74111fece744a7d3`
**New Child/Gitlink**：`7dd696efb4807e7338a5e420db2a1ede6cec67d0`
**Source branch**：`v3-g1-cross-pair-resume-20261022`（Root/Child各自隔离分支，未合并V3）。
Prior source-reviewed Candidate：Root `b910304dbf493eb5babe26cf1b055edc8477b386` / Child `61bfa94766d33d95a7fa9771857d0f2fb3f0b405`；其后已有docs-only author HEAD `5fe6a513baa870c06f3186903b99e9bba80bb084`。本轮Root 38d385ba 以这条 docs-only HEAD 为父提交，在该树上只修改 Gitlink，未重复修改训练生产源码。

## 1. Exact delta / contract

**GitHub Connector 独立精确回读验证**：
- Child `61bfa947...` → `7dd696ef...` compare **唯一** changed file：`examples/psm_wma_robocasa_g1_cross_pair_resume_test.py`，+1行/0删：
```python
def test_real_preflight_wires_historical_digest_to_report_and_snapshot_producer(job, monkeypatch):
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    args = job.args
```
- Root `5fe6a513...` → `38d385ba...` compare **唯一** changed entry：mode160000 `cosmos-framework` Gitlink `61bfa947...` → `7dd696ef...`。Root Branch HEAD、Child Branch HEAD 与 Root Gitlink均已远端回读完全一致。
- Training launcher `scripts/train_v3_packed128_staged.sh` 未变；`--expected-root`/ `--expected-child`当前仍为所**审核运行实现 Pair**的精确身份证明，而不是将运行新Pair强制等于旧Frozen G1 `e012.../2d128...`。使用新版本时必须采用当前 **Root 38d385ba / Child7dd696ef**，不能复用原 `b910.../61bf...` 或任意V3 HEAD。
- `examples/psm_wma_robocasa_corrected_phase5.py:934-1062` 原生产 `preflight()` 内 `os.environ["HF_HUB_OFFLINE"]="1"`未变；新的单行只给pytest测试建立一个可由monkeypatch在其fixture teardown还原的临时环境变量，消除`conftest.py:283` 的 `detect_env_modifications` teardown 误报。没有全局添加白名单、禁用检测fixture、忽略错误或放宽G1严格恢复条件。
- 原 frozen Job config/config_digest和8 rank Local sidecar、T16/B8/GA2/K4 world8、正式30k/500/100、checkpoint8900/Full-training optim+RNG+fast 真实恢复仍原样。

## 2. Evidence / Verdict

**直接源码改动和Gitlink绑定验证：`APPROVE`（静态一行test-only修复范围）。**
**新Formal Pair 的目标机独立 pytest/teardown Evidence：`REQUEST_CHANGES` — EVIDENCE-ONLY，尚无修复后真实 pytest 新日志。** 必须明示这不是新发现的生产代码 blocker，也不是宣布已经运行115+32测试。

本次GPT直接通过GitHub工具提交测试和更新Gitlink、逐个SHA验证差异（作者即GPT，不应冒充第三方独立作者测试）。目标机Remote Desktop Commander当前设备离线；工具容器的`git ls-remote github.com`因DNS不可达，未执行pytest。之前的DS汇报为37项真实G1只读检查PASS与115 methods+32 subtests中**1项teardown fixture caveat**，这些证据绑定**旧** formal Pair；不能自动当成新Pair已验收。

**最小证据闭合条件**（避免整套G1历史反复跑）：
1. DS_PRO 在隔离 clean Root `38d385ba73ba991eddbfb99a74111fece744a7d3` / Child `7dd696efb4807e7338a5e420db2a1ede6cec67d0`，`CUDA_VISIBLE_DEVICES=''`，外置pycache/pytest log下执行**原生pytest fixture**中的目标测试，不能使用`--noconftest`也不能手动禁用`detect_env_modifications`：
```bash
# cwd=<new exact Root>/cosmos-framework; VENV_PYTHON为已验证CPU测试解释器
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 CUDA_VISIBLE_DEVICES='' \
"$VENV_PYTHON" -m pytest -q \
  examples/psm_wma_robocasa_g1_cross_pair_resume_test.py::test_real_preflight_wires_historical_digest_to_report_and_snapshot_producer
```
   证据要求：真正完整pytest returncode=0、`1 passed`、**0 teardown errors**，留下准确Pair/Gitlink/版本、stdout/stderr；不能只检查测试body的断言。
2. G1真实read-only验收绑定新的执行Pair；若此前37项G1 immutable资产SHA见证仍可复用，需只读核对旧Asset Identity没有漂移，并在新Pair上单独完成真实`--preflight`，才允许进入8×H100 Resume；不可直接把一行fixture修复看作真实Restore已经成功。
3. 真正Resume仍由Owner本人手动执行、使用新Pair及 `--owner-authorized-g1-cross-pair-resume`。ChatGPT不得自动启动GPU/训练或影响运行中的任何Job；未来再次从9000/10000中断不在本次Owner8900例外内。

**本轮技术结论：测试修复已经落到精确隔离仓库、源代码Scope正确。新Pair修复后目标机teardown回归证据仍待DS报告；没有对真实G1预检与Owner启动做自动授权。**
