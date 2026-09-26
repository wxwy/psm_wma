# V3 Stage B1-Latent Producer 实施记录

- Gate：V3-STAGE-B1-LATENT-PRODUCER；状态 REVIEW；cx 实现，ChatGPT 设计/审核，用户 owner/最终裁决，ds 数据/执行取证。
- 设计 authority：root `f0d020dd8c06ab734bd6d8b8d915c937fd57b94a` 的 `PSM-WMA_V3_stage_b1_latent_producer_gate_design_v0.1_2026-09-26.md`，保持原文不变。
- 实现基线 formal pair：root `ddca6b239697ac83a9c09157de060dbe9e91ac59` / child `4fa4f35c102433bb007d2a3fd4a9fc7fe0b5149f`。root 已快进合入指定设计提交；child 基线未变。
- 本文件承载本轮实施认领及交付状态；root 范围仅本记录及最终 Gitlink，未修改历史 TODO/SESSION。
- 实际 child 仅新增 `cosmos_framework/model/generator/mot/robocasa_latent_evidence.py`、`robocasa_segment_producer.py` 及对应两个 `_test.py`；只在 `/disk/rl/worktrees/cosmos-framework-v3` 写源码，使用该目录 `.venv/bin/python`。
- B0 不改；不接 trainer/主 policy forward/在线 VAE/optimizer/checkpoint；不运行 GPU，不新增依赖，不迁 V2 patch，不改 chunk32/33帧。
- 缓存 reader fail-closed；visual96=fp32 mean48+sqrt(mean(square)+1e-6)48；source step=t−1，visual endpoint<=source step，action精确raw15[t−1]；T16连续slot段，末段尾PAD。
- CPU/static：98/98 PASS，无跳过，15.56秒（B1新增66项，B0回归32项）；四个新增文件 Ruff check/format check PASS。child 提交及最终双仓 diff-check 见下方交付记录。新 formal pair 待 fresh review，本记录不自授 closure。

## 实现映射与接口约束

- `robocasa_latent_evidence.py:causal_endpoint_index` 只接受从0开始、间距4的 endpoint，使用右侧二分查找后减1；不采用 nearest、ceil、插值或时间平均。
- `latent_to_visual96` 拒绝非CPU、非fp16、非 `[48,16,16]` 或非有限输入；转fp32后计算 mean48 与 RMS48（eps=1e-6）；无参数且不保留输入梯度。
- `RoboCasaLatentReader` 要求调用者显式指定 H5 `latent_key`、`endpoint_key`、`metadata_group`，不猜物理布局。metadata 从指定 group 的 attrs 读取：`episode_id`、`source_video_frames`、`temporal_compression_factor`、`source_frame_to_latent_policy`；必须与源 episode/视频帧数及冻结4/causal_endpoint一致。endpoint 必须完整覆盖 `range(0,source_frames,4)`；逐帧校验整个episode，包含当前未选中的缓存帧。内存只保留visual96副本，不输出可注入policy的cached video latent。
- 设计未指定 H5 物理键名；本轮未收到真实缓存 schema，未宣称该 reader 已通过真实数据验证。CPU fixtures 使用 `latents/rgb`、`indices/source_frame_indices`、根group attrs；这些是显式测试布局，不是对真实缓存的事实断言。若真实cache缺少冻结必需metadata或布局不同，应由ds记录并回报，不静默合成metadata或fallback。
- `RoboCasaSegmentProducer` 绑定一个episode的已转换raw15、cache reader及既有native RGB `payload_at(step)`回调。验证raw15与源视频等长，拒绝64维、非有限或不匹配输入。它不负责读取/转换LeRobot或执行policy，不改变callback返回的payload，也不捕获失败后随机重采样。
- 有效consumer数为 `max(0,source_frames-32)`，与 upstream33帧窗口边界一致。cursor按16个consumer递增；末段1..16有效行后尾PAD。返回B0原有SegmentBatch，`validate(16)`通过；B0三文件零语义修改。
- `consumer_visual_summary` 是当前consumer frame可得到的最新因果缓存摘要（endpoint<=t）；它不是逐帧在线VAE的等价声明。previous evidence独立按source=t−1选择endpoint；例如t=4时current endpoint4而previous endpoint0。该carrier字段从未用来替代previous-evidence authority。
- episode/category/source/terminal请求必须与producer绑定信息一致；slot/cursor/segment_id通过原有SegmentIdentity及provenance传递。raw15复制绑定，外部后续原位修改不污染已绑定episode。

## 可复现 CPU/static 验证

工作目录 `/disk/rl/worktrees/cosmos-framework-v3`。使用临时合成H5和CPU tensors；不加载真实数据、checkpoint/VAE，不联网、不运行GPU。日志 `/tmp/cx_v3_b1_cpu.log`；JUnit `/tmp/cx_v3_b1_cpu.xml`；不纳入Git。

```bash
CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu LD_LIBRARY_PATH='' \
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
.venv/bin/python -m pytest -c /dev/null --noconftest -p no:cacheprovider -q \
cosmos_framework/model/generator/mot/robocasa_latent_evidence_test.py \
cosmos_framework/model/generator/mot/robocasa_segment_producer_test.py \
cosmos_framework/model/generator/mot/local_evidence_test.py \
cosmos_framework/model/generator/mot/local_memory_segment_test.py \
cosmos_framework/model/generator/mot/local_memory_segment_adapter_test.py \
--junitxml=/tmp/cx_v3_b1_cpu.xml > /tmp/cx_v3_b1_cpu.log 2>&1

.venv/bin/ruff check --no-cache \
cosmos_framework/model/generator/mot/robocasa_latent_evidence{,_test}.py \
cosmos_framework/model/generator/mot/robocasa_segment_producer{,_test}.py
.venv/bin/ruff format --no-cache --check \
cosmos_framework/model/generator/mot/robocasa_latent_evidence{,_test}.py \
cosmos_framework/model/generator/mot/robocasa_segment_producer{,_test}.py
git diff --check
git diff --cached --check
```

PASS依据是98项无失败/跳过，Ruff/format/diff-check退出0。验证包含s={0,1,3,4,5,7,8,15,16}、future-sensitive H5、fp32累积及epsilon、缺失/错误metadata、shape/dtype/非有限/index次序/越界/长度/身份不匹配、cursor0/1/末段、raw15精确t−1、policy payload不变和B0回归。未运行真实缓存取证及GPU；ds后续必须按设计§8验证至少3任务×2episode、源视频/action长度、各边界段，并生成compact JSON evidence。

## 交付记录

- child `5f9c39464761665843b0f08c5e1d578f72114b33`，4个新增文件、580行，已先推送 `v3-local-ttt`；B0三文件相对formal baseline无diff，其他child production/config/trainer均未修改。
- root 仅本implementation record与Gitlink；root formal SHA为包含本记录的提交，推送后在交付报告核对完整pair。内嵌child只同步已提交SHA，不在其中编辑源码。
- 两仓工作树及staged diff-check PASS；不纳入已有未跟踪 `artifacts/v3/`。root按 `V3` 推送；状态保持REVIEW，CPU结果不替代fresh review或ds真实缓存取证。
