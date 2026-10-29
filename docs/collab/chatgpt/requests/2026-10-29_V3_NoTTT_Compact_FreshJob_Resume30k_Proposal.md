# 独立 Compact Fresh Job Resume 至总30k — 待 Owner 扩大执行范围的提案

- 日期：2026-10-29（Asia/Shanghai）。
- **状态：`PROPOSED_NOT_AUTHORIZED`。本文件准备可审核的命令与范围，不是执行许可。**
- 前序：[Fresh10 增量审核](../reviews/2026-10-29_V3_NoTTT_Compact_S2_Fresh10_Incremental_Review.md)，verdict `ACCEPT_S2_FRESH10_REPORT`。
- 当前批准范围已在 fresh total iter10 结束。只有 Owner 明确授权同一 Job 续训至总30000后，DS 才执行下述 payload；无需重新请求 CPU、严格Gradient Parity或iter20/100中间Gate。

## 1. 待批准的具体范围

同一 Job `no_ttt_compact1_corerun_fresh_20261029_world4_ga4`，从本 Job 最新合法训练 checkpoint 真实 Resume 至总 iter30000。当前报告最新为iter10，因此预期首个新增commit为11，剩余29990次；如果启动前合法进度已变，记录真实恢复点，不回滚、不重跑已完成部分。同Job存在活动进程时只观察已有运行，不重复启动；若已有总iter≥30000完成证据，只整理现有结果，不再次启动。

资源为物理GPU4–7、4卡FSDP2、No-TTT、Compact=1、GA4/B8/T16、workers0。max_iter30000、warmup500、save_iter100维持原值；旧正式Job `no_ttt_packed128_droid_fresh_30k_world4_ga4` 不受本动作改变。存储监控与checkpoint保留继续由Owner本地程序管理。

Owner 批准此范围意味着接受当前已明确的残余数值风险：历史严格Gradient Parity为FAIL、同模式参考重复性不满足原阈值、Compact特有缺陷归因INCONCLUSIVE、完整输入／输出见证未关闭。本次续训不把这些状态改成PASS。

## 2. 现场最小检查与恢复验收

执行前复用现有生产机制核对本Job的latest/complete marker、identity及必需资产；实际训练状态恢复必须包含model、optimizer、scheduler、trainer和既有生产数据frontier/sidecar。禁止缺checkpoint后静默fresh、改名或修改identity绕过恢复检查。

记录实际工作目录、Python/import来源和能取得的源码身份。不重新启用Owner已豁免的No-TTT Root/Child clean/HEAD/Gitlink硬门，不要求同步正在运行的训练工作树。

启动后在同一次续训里核对：加载的是本新Job训练checkpoint、恢复迭代与optimizer/scheduler/trainer一致；按iter10恢复时首个新增commit为11；现有健康字段正常。随后继续已批准总目标，不在11/20/100人为再设停止点。

## 3. 拟执行 payload（Owner 扩范围批准后使用）

工作目录与Python/OUTPUT_ROOT来自本轮DS报告；其余六个路径从**新Job自己的identity**读取，并验证存在。若现场环境迁移，保留同一Job/资产身份并记录真实路径；下面的历史路径不代表GPT已经现场验证。

由DS既有持久执行和监控入口运行，避免短时交互工具超时终止长训。日志保留到本Job独立evidence目录及既有monitor；checkpoint由原生产保存机制写入本Job。launcher使用本地模型与离线环境，不下载模型。

```bash
set -euo pipefail
cd /mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3

export PYTHON=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin/python
export OUTPUT_ROOT=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/outputs/no_ttt_robocasa_raw15
export JOB_NAME=no_ttt_compact1_corerun_fresh_20261029_world4_ga4
export PSM_V3_COMPACT_CACHED_VIDEO=1
export CUDA_VISIBLE_DEVICES=4,5,6,7

test -x "$PYTHON"
COMPACT30K_NAMESPACE="$OUTPUT_ROOT/psm_wma_v3/corrected_phase5/$JOB_NAME"
COMPACT30K_IDENTITY="$COMPACT30K_NAMESPACE/v3_job_identity.json"
test -f "$COMPACT30K_IDENTITY"

compact30k_source_path() {
    "$PYTHON" - "$COMPACT30K_IDENTITY" "$1" <<'PY'
import json
import sys
from pathlib import Path

with open(sys.argv[1], encoding="utf-8") as f:
    record = json.load(f)
value = record["semantic"]["source_paths"][sys.argv[2]]
if not isinstance(value, str) or not Path(value).is_absolute() or not Path(value).exists():
    raise SystemExit("Missing or invalid Compact Job source path: " + sys.argv[2])
print(value)
PY
}

SOURCE_ROOT="$(compact30k_source_path source_root)"
CACHE_ROOT="$(compact30k_source_path cache_root)"
DATASET_INDEX_ROOT="$(compact30k_source_path dataset_index_root)"
EDGE_POLICY_CHECKPOINT="$(compact30k_source_path edge)"
WAN_VAE_PATH="$(compact30k_source_path vae)"
BASE_CHECKPOINT_PATH="$(compact30k_source_path base_checkpoint)"
export SOURCE_ROOT CACHE_ROOT DATASET_INDEX_ROOT
export EDGE_POLICY_CHECKPOINT WAN_VAE_PATH BASE_CHECKPOINT_PATH

export NOTTT_LOADER_WORKERS=0
unset NOTTT_PREFETCH_FACTOR NOTTT_PERSISTENT_WORKERS NOTTT_LOADER_TIMEOUT_S

COMPACT30K_EVIDENCE_DIR="$COMPACT30K_NAMESPACE/evidence/resume_to_30000_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$COMPACT30K_NAMESPACE/evidence"
mkdir "$COMPACT30K_EVIDENCE_DIR"

bash scripts/train_v3_matched_no_ttt_4gpu.sh resume 30000 \
    2>&1 | tee "$COMPACT30K_EVIDENCE_DIR/launch.log"
```

`resume 30000`是恢复后到总30000，不是恢复点30000，也不是额外训练30000步。JOB_NAME必须显式为上述新Job；launcher默认名仍是旧正式Job，RUN_NAME不能替代。不要增加`--audit-missing-grads`，它与formal execution模式不兼容；使用既有telemetry。

## 4. 结果与停止条件

**恢复阶段成功：** 同Job模型及训练状态真实恢复，first new commit=restored_iter+1，已有梯度／loss／telemetry监测无新异常。记录该事实后继续已批准总目标；它不表示30k已完成。

**总目标完成：** total iter30000正常完成，报告last_completed_iteration与last_saved_checkpoint、实际完整checkpoint及正常退出。中途检查报告只能写进行中与实际进度。

**实际错误：** checkpoint/identity/生产恢复校验失败、错误fresh warm-start、缺失或非有限梯度、NaN/Inf、OOM/NCCL或训练异常时停止本次明确归属的新Job进程并保留证据；不自动重试、fresh重建或迁至GPU0–3，不用宽泛pkill触碰旧Job。共存资源问题单独归因，不直接判定Compact数值缺陷。

已有有效输入探针若发现本应相等的输入实际不同，按新实质问题停止并报告；输入见证仍OPEN或可选字段未测本身不触发新Gate。Loss不要求单调，每步不要求匹配Dense。

## 5. 一次启动回传与已有证据归档

回传实际恢复checkpoint/iter、optimizer/scheduler/trainer与数据恢复记录、首个新增commit、现有健康字段和新Job进程归属；如继续运行，明确实际进度，不提前宣称完成30k。旧Job仅记录观察事实，不声明零干扰。

在不重新训练的前提下，一并整理已有fresh10原始launch.log、train_rank0.jsonl、launch.json、identity、complete marker/latest，以及旧Resume的BLOCKED报告；澄清现成记录的时间时区和显存采样口径。无需全量上传模型checkpoint、重复17份v2附件或补造缺失指标。

本地4个evidence提交与origin/V3分叉的整合应独立处理，保留本地提交与远端新增文档；不把本提案当成强推、reset或改动活动训练工作树的授权。
