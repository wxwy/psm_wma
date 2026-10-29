# DS_PRO — 独立 Compact=1 S2 Resume 至总 iter10

- 日期：2026-10-29；Owner已回复“好，继续”。
- **授权：一次独立S2真实Resume／连续Optimizer Commit，截止总iter10；关键入口输入见证允许并行补证。**
- 正式授权 Review：[`2026-10-29_V3_NoTTT_Compact_Parity_Disposition_and_S2_Resume10_Authorization.md`](../reviews/2026-10-29_V3_NoTTT_Compact_Parity_Disposition_and_S2_Resume10_Authorization.md)。
- 历史No-TTT Root `49df7f3c2e0ba8ef5871f9dd490e41fbc3dc5da9` / Child `746c5cf2f2324104a62fb71510343aa40d3976c5`。本轮GPT取证V3 HEAD `66a5b99c0a23312525ccbdc0fadb4655bc7d0b19`。记录现场真实身份；不把文档HEAD变更当成新训练实现，也不恢复已被Owner取消的源码clean/HEAD硬门。
- 不需要重交17份附件：四Rank完整v2 JSON已在V3并完成哈希核验；CPU Gate、三套Fresh1和旧paired实验均不重跑。

## 1. 执行目的与范围

独立Job `no_ttt_compact1_corerun_20261028_world4_ga4`，仅物理GPU4–7，真实4卡FSDP2、No-TTT、Compact=1、T16/B8/GA4。复用S1的Python、真实source/cache/index/模型路径和训练语义。

`resume 10` 表示从该Job现有latest恢复到总committed iter10。原报告latest为iter1，因此预期新增9次提交。若现场有新的同Job合法恢复点，在不回滚的前提下继续至10，按真实start报告提交数；若已有运行达到10，整理已有证据，不再重复启动。若该Job仍有活动进程，不重复启动第二份同Job。

`max_iter=30000 / warmup=500 / save_iter=100`固定，使用执行上限截到10，不改调度horizon。旧正式No-TTT、GPU0–3、G1、Cleaner和Checkpoint保留策略不动。

## 2. 启动前最小核对

1. 只读记录root/child、实际Python与import来源；只处理本次相关路径，不对活动旧Job执行pull/checkout/reset/submodule update。
2. 核对目标namespace、最新checkpoint、complete marker、4Rank sidecar及Job identity；复用已有严格Resume机制，不额外全量扫描／重哈希24GB模型。
3. 记录实际模型／optimizer／scheduler／trainer恢复路径，防止模型权重加载后fresh start。数据恢复依已有生产frontier/sidecar机制。
4. 核对物理GPU4–7和本次新Job进程归属，允许与旧Job共存；不设与已有证据无关的新空卡或磁盘阈值。
5. 下列命令的数据路径从本Job现有 `v3_job_identity.json` 读取。若文件缺失、字段不是完整绝对路径、实际源不可用或生产Resume校验失败，停止并报告；不得改用猜测路径或修改identity绕过验证。
6. 本轮loader workers固定为现有报告采用的默认0，禁止继承其它shell的worker优化参数。如现场原始S1启动记录明确是其它值，复用该已验证S1值并记录，不能悄悄改变传输配置。

这些检查不需要再次请求本轮执行许可。检查失败保留证据，不自动重跑。

## 3. 冻结命令（由DS在训练服务器执行）

**仅在§2已确认没有同Job活动进程、没有已有iter≥10完成证据后执行下列命令。**

以下根目录、Python和OUTPUT_ROOT来自既有DS报告；由DS现场核对存在性。其余六个数据／模型路径直接从同Job已保存的原始identity读取，避免使用报告中省略号路径。若执行环境已迁移，记录实际对应路径并保持原Job与资产身份，不能把本代码块中的历史路径当成现场已验证事实。

```bash
set -euo pipefail
cd /mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3

export PYTHON=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin/python
export OUTPUT_ROOT=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/outputs/no_ttt_robocasa_raw15
export JOB_NAME=no_ttt_compact1_corerun_20261028_world4_ga4
export PSM_V3_COMPACT_CACHED_VIDEO=1
export CUDA_VISIBLE_DEVICES=4,5,6,7

test -x "$PYTHON"
S2_NAMESPACE="$OUTPUT_ROOT/psm_wma_v3/corrected_phase5/$JOB_NAME"
S2_IDENTITY="$S2_NAMESPACE/v3_job_identity.json"
test -f "$S2_IDENTITY"

s2_source_path() {
    "$PYTHON" - "$S2_IDENTITY" "$1" <<'PY'
import json
import sys
from pathlib import Path

with open(sys.argv[1], encoding="utf-8") as f:
    record = json.load(f)
value = record["semantic"]["source_paths"][sys.argv[2]]
if not isinstance(value, str) or not Path(value).is_absolute() or not Path(value).exists():
    raise SystemExit("Missing or invalid S1 source path: " + sys.argv[2])
print(value)
PY
}

SOURCE_ROOT="$(s2_source_path source_root)"
CACHE_ROOT="$(s2_source_path cache_root)"
DATASET_INDEX_ROOT="$(s2_source_path dataset_index_root)"
EDGE_POLICY_CHECKPOINT="$(s2_source_path edge)"
WAN_VAE_PATH="$(s2_source_path vae)"
BASE_CHECKPOINT_PATH="$(s2_source_path base_checkpoint)"
export SOURCE_ROOT CACHE_ROOT DATASET_INDEX_ROOT
export EDGE_POLICY_CHECKPOINT WAN_VAE_PATH BASE_CHECKPOINT_PATH

export NOTTT_LOADER_WORKERS=0
unset NOTTT_PREFETCH_FACTOR NOTTT_PERSISTENT_WORKERS NOTTT_LOADER_TIMEOUT_S

S2_EVIDENCE_DIR="$S2_NAMESPACE/evidence/s2_resume_to_iter10_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$S2_NAMESPACE/evidence"
mkdir "$S2_EVIDENCE_DIR"

bash scripts/train_v3_matched_no_ttt_4gpu.sh resume 10 \
    2>&1 | tee "$S2_EVIDENCE_DIR/launch.log"
```

- 本代码块采用S1报告中的默认workers=0；如现场原始S1记录明确是其它值，执行前将对应worker/prefetch/persistent/timeout行替换为该S1原始配置，并记录，不能一边声明复用一边被代码块覆盖成0。
- 必须设置JOB_NAME，RUN_NAME无效。未设置JOB_NAME时launcher默认旧正式Job。
- launcher固定实际参数为 `--phase resume --formal-execution-until 10 --no-ttt --world-size 4 --t 16 --b 8 --ga 4 --max-iter 30000 --warmup 500 --save-iter 100`。
- 不加 `--audit-missing-grads`，该诊断参数与formal execution模式不兼容；直接使用现有telemetry／训练审计。
- 外网：launcher设置HF_HUB_OFFLINE=1和TRANSFORMERS_OFFLINE=1，复用本地资产，不下载模型。是否取得最新审核文档与实际训练联网分开记录。
- 日志保留在新建S2_EVIDENCE_DIR及既有Job telemetry目录；Checkpoint只由既有训练保存逻辑写入本Job。无需在iter10强制额外保存，实际保存结果据实报告。

## 4. 关键输入见证：并行补证，不是新的启动前置Gate

原v2顶层类型字符串不能证明列表内Tensor值相同。允许DS制作 `/tmp` 测试探针，复用真实cached-latent构造／搬运seam及一个固定rank-local GA member，比较Dense0和Compact1路径汇合处、进入training_step前的有效输入：

- 递归dict/list/tuple/Tensor与标量，记录字段路径、序列顺序、真实dtype/shape/device和实际值比较结果。
- 覆盖video_latent、action、文本token、mask、序列／consumer元数据及实际分支参数；相同有效逻辑输入按精确比较，原始视频占位表示允许Dense零张量与Compact零代理的已知表示差异。
- 不用仅shape／abs_sum／截断repr冒充数值证明；必要的值摘要保留原始dtype字节语义。未知对象不能退化为“类型一样即通过”，应标NOT_MEASURED并说明是否被模型消费。
- 恢复每侧所需RNG，记录模型入口前的真实有效随机输入；尚未进入模型内部的noising／输出不宣称已验证。
- 探针可只做数据准备／搬运与比较，不额外运行新的model forward/backward或Optimizer，不修改生产文件，不把探针放进正式Job的训练路径。
- 若无法利用已有入口低成本取得，回传精确缺口，输入见证保持OPEN；继续按本授权完成S2，不新增一轮严格GPU Parity。
- 若查到本应相同的有效输入确实不同，则属于新实质问题：暂停本次Compact Job并报告，不触碰旧Job。

此项即使完成，也只关闭对应入口输入子项，不自动关闭原F3完整输出、F4完整模型状态／有限性或F5执行脚本原始字节provenance。

## 5. PASS / FAIL / BLOCKED 与停止边界

**PASS_S2：**
- 从预期同Job恢复点真实恢复，新增提交从恢复迭代+1开始，连续到总iter10。
- optimizer／scheduler与训练迭代一致，数据frontier／sidecar按已有生产机制继续；已有健康监测无新异常、缺失或非有限梯度，无NaN/Inf/OOM/NCCL错误。
- 进程正常退出于执行上限，没有继续到100／30000。
- 本次没有改动或终止旧Job；记录旧Job在观察期的实际推进情况，不把它解读为零性能干扰。

**FAIL_S2：** 真实恢复或运行错误、实际状态／配置错配、非有限数值、未到10而异常退出、超过执行上限。OOM／共存资源冲突单独标因，不能直接归因Compact数值问题。只停止本次明确识别的新Job进程，不使用宽泛pkill，不动其它Job。

**BLOCKED_BEFORE_RUN：** 资产／checkpoint缺失、同Job已有活动进程、身份不匹配或现场无法安全启动。记录实况，不fresh重建、不回滚或改名、不迁到GPU0–3。

不要求Loss单调下降，不要求每步匹配Dense，不要求iter10必有Checkpoint。缺少某项旧telemetry指标就标NOT_MEASURED，不为补可选指标修改训练或重跑。生产检查实际报错不能忽略。

## 6. 一次性回传

提交一份短报告，引用既有原始日志／JSONL，至少列明：

- 实际root/child、工作目录、Python/import来源和上述实际环境变量。
- Job/namespace、恢复checkpoint与迭代、四卡world4/B8/T16/GA4/Compact=1/No-TTT/save_iter100。
- 首个新增commit、最终completed iteration、实际新增commit数；optimizer/scheduler/data恢复证据。
- 每步已有loss、wall/data_prepare/stall、显存与梯度健康字段；保留原日志，不补造未测Rank峰值。
- `last_completed_iteration` 与 `last_saved_checkpoint` 分开报告。
- 旧Job观测事实、输入见证状态及未测字段。
- S2=PASS/FAIL/BLOCKED与原因；历史严格Gradient Gate始终FAIL_PARITY，Compact归因仍INCONCLUSIVE。

短程耗时只能作为此次共存运行观察，不能据9步宣布稳态1.87倍。完成本次后停止，不自动进入100／30k，后续范围依据本轮证据再决定。
