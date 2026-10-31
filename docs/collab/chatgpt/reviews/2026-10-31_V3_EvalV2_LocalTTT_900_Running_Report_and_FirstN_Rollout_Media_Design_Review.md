# PSM-WMA V3 EvalV2 18×50 Local-TTT iter20000：DS_PRO运行中报告审核 + 每Task前N Rollout MP4最小设计

**日期2026-10-31。评审类型：DS_PRO报表逻辑/运行中Evidence报告核验与未来媒体Feature设计；**不是新Implementation Formal Code Gate，也不是900正式SR验收。**

- GPT审阅 GitHub现行V3（审核时Root `2655d23a6d2c6660110f6242b7cdb3465038435c`，Child formal `6c83596d6a259e89c4cd3e79424024983426ac3d`）；这不是对在训现场实际Run源码的独立校验。DS报告本机 `out2`、GPU、DCP、OSMesa、Sim与结果由Owner转交，无法从GitHub直接访问运行服务器；**所有真实性状态标为DS_REPORTED**。
- 运行状态暂定：`RUNNING / PRODUCING_RESULTS / INTERIM_METRICS_NOT_FROZEN`。既往V3 Code APPROVE继续有效，不做代码再审；真正900 Gate须在Run完成、缺口/错误和Session清理全部闭合后另行决定。报告中的实际`phase_b_native_batch_v1 + local_memory=required`不是No-TTT。

## 一、已报告的实际进展（只作为阶段性报告）

- 2026-10-31 15:22–15:25UTC（北京时间23:22–23:25）DS称迭代 `iter_000020000`、4 ActionServer GPU4–7、8 physical Sim slots（M2/B2）、CPU OSMesa无本次Segfault、源DCP完整、NoTTT训练与评测共享同四张GPU，71/900 Core归档，47成功24行为失败，阶段性47/71≈66.20%；尚未被GPT直接抽取`result.json`核实。报告均按Owner原话，不构造新的完整900SR。
- 基于DS 67分钟得到71集，实际≈1.06 EP/min；每Episode平均438.3 steps/297.8s≈1.47steps/s与所报告1.47–1.55steps/s内部相符，4轮左右/67min得约16–17分钟一轮；据此推算剩余829EP还需≈12.9h仅是线性粗预测，不可承诺完成时间。
- 数值更正：20Hz/1.5step/s≈13.3倍慢（非8倍）；450step/1.5≈300s≈5min（非3min），1050step/1.5≈700s≈11.7min（非10min）。推理每replan2.7–3.4s且chunk16，折合约0.17–0.21s/step，所以CPU Sim占比较大**合理但未严格测得完整瓶颈分解**；GPU与正式NoTTT训练并发，性能数据不是独占测试。

## 二、报告内部必须更正（无需重测、无需追加此前Owner已免除的旧Canary原始Evidence）

### RUN-R01 Medium — 逐Task列表遗漏，统计与总数不一致

- **位置：** DS报告§4成功Task清单及§3归档数。18个官方`ATOMIC_TASKS`中`PickPlaceToasterToCounter`不在报告列表（只列17 Task）；所列Success=5×4+6×3+1×2+3×1=**43**，而总体列47。遗漏任务如为4/4才可补齐，但这是猜测，不能替代DS查权威`result.json`。
- `TurnOffStove`报告仅归档3集，但Task表写`1/4`，应根据该时点真实文件给出`x/3`并注明ep索引，不能把未归档算作失败/成功。
- **验收：** DS仅从同一时间戳所见已提交的`result.json`/`summary.json`聚合一次Task→success/failure/valid/missing，必须满足18 Task与Success/Failure分别求和到总计47/24/71；不可为了报表修正重新运行任何EP或改写任何Result。

### RUN-R02 Medium（如真越屏障则High） — RoundBarrier和归档快照口径冲突

- **位置：** DS报告§3“71已归档，18Task×4减TurnOffStove1”和“4轮完成+第5轮运行中”；代码Child`cosmos_framework/evaluation/robocasa_v2/scheduler.py:91-141`的`RoundScheduler.dispatch()`在任何inflight未结束前不能发下一轮，且写`ROUND_BARRIER`事件；Root`runtime.py:813-865`屏幕显示`round=scheduler.round+1`。
- 71=72−1表示第四轮存在一条未归档（在其余17Task都是4时）；按严格屏障第五轮不能开始。多处状态可能来自不同采样时刻或口头轮次定义混淆；**不能仅凭这段报告推断实际调度出现Bug**。
- **验收：** DS只读核同一时间快照的当前`round`、inflight claim `(task, episode)`、最后一条`ROUND_BARRIER` Event及归档聚合；更正报告文字。如果确有`ROUND_BARRIER`跨越未完成第四轮则另开真实运行Finding，不在运行中即时改Code。

### RUN-R03 Medium — 真正LocalTTT的Fast状态证据未在报告中列出

- **位置：** DS报告§1/§5 仅给`local_memory=required`、Server和B1直方图。现行Child`action_policy_server_robocasa.py:904-946`要求Local capability、raw15/state15/H16/K4/local32，并以`robocasa_local_memory_policy.py`的状态机制执行Local更新；Simulation`eval_v2_adapter.py:149-180`将Local信息记录于各EP`predictions.jsonl`。
- **验收：** DS下次阶段性总结只需汇总真实`prefix_present`、`adapted_steps>0`、`inner_loss_mean`、`fast_state_norm`、每Session End ACK/cleanup（不用上传老Canary原始大包），以区分“模式已是required”和“实际完成在线Fast Update”的不同证据层次。

### RUN-R04 Note — M2/B2配置不等于B2模型路径已验证

- DS报告Native Histogram至今全为B1。多Sim和required Local真实工作，可视为Runtime持续生产中；**没有B2真实命中的证据，不能宣称Native B2/加速已实测PASS**。不同步/20ms等待窗口下全B1不一定是Bug；本轮不要调wait或重新启动900长跑追求B2。
- GPU4–7与NoTTT训练共存，DS称45.5–47GiB与100%util；需监控GPU内存实际峰值、HostRSS、NoTTT Step wall/timeout和Eval Session/进程风险，避免后续混淆“运行健康”与“完全不影响训练”。不自动抢占、不暂停/重启两作业。

## 三、媒体需求审核：`APPROVE_MINIMAL_DESIGN_FOR_ISOLATED_CANDIDATE`

**设计结论：建议Codex用最小增量实现‘每任务前N个逻辑Episode保存Rollout MP4’；批准的是实现候选范围，不是新Formal Implementation APPROVE_CODE。**

### 实际数据路径与代码

- Root `scripts/robocasa_eval_v2/config.py:22,168-172`：现有`save_rollout_mp4`仅bool、`save_generated_video`分别有`none/first/all`。Root`runtime.py:293-305`在**创建可复用Sim Actor时**设置media policy，不能在这里把本次EP是否录像计算成一个永久bool。
- Child `cosmos_framework/simulation/robocasa/eval_v2_adapter.py:76-125`：`NativeEpisode.execute`已经收到绑定的`attempt["task"]`/`attempt["episode"]`，每Episode新建`MediaSink`时传入`rollout=...`。Child`cosmos_framework/evaluation/robocasa_v2/media.py:71-120`已有`rollout=False`完全跳过frame enqueue/rollout encoding，生成视频独立。`model/LocalTTT/Server/Scheduler/Store/MediaSink`均不需改动。

### 推荐单一YAML ABI与语义

```yaml
save_rollout_mp4: true
rollout_mp4_first_n_per_task: 3  # optional; null=legacy bool behavior
save_generated_video: first  # unchanged/independent
```

- 新字段默认`null`；当`save_rollout_mp4==true`时，`N=0..episodes_per_task`（type必须是**exact int、bool不接受**）仅令 `attempt["episode"] < N` 的本Task逻辑EP产生rollout。N=3即每Task的`ep_000..ep_002`，**不按最早完成/成功/重试次数**选择。N=0零视频，N=50全部；无新字段时旧`true`所有、旧`false`全无。禁止`save_rollout_mp4=false`和非null N的模糊组合（配置期拒绝）。
- Root `config.py`加字段、校验；Root`runtime.py`只透传该数值到所有Worker settings；Child `eval_v2_adapter.py:122-125`在每次EP执行时依据合法attempt index计算真正的`rollout_enabled`。不改Server、Local Memory、Scheduler、Core Result、SR、已有MediaSink。生成的 `save_generated_video: first`**每Episode仍可保存首个Replan诊断媒体**（可能因Optional spool资源限制而drop），和Rollout N独立。
- 必须保持`media independent of SR`（Child`contract.py:95`，Owner D1–D5媒体合同）：未录像/视频写入失败不触发重试、不改变valid/success/failure、无需ffmpeg严格解码。不得删除旧MP4或重写已有Episode有效Core结果；Resume对同一个逻辑index与固定新配置应给出一致的录像选择。新media配置必须在可用的运行配置/Diagnostics中可追溯；如果现有Resume允许新字段静默漂移，应以**轻量本Run核对**防止未来无法重建缺失媒体，不能为此引入新框架或重新定义SR。
- 当前正在运行的`out2`使用已冻结原代码和Config，**绝对不热更新/原位改YAML、不修剪/迁移out2媒体、不自动重启/继续执行它的任何新版本**；实现只针对后续独立新Run，在共享训练/仿真进程安全结束前也不得同步在线Worktree。

### 有界验收样例

1. config：旧bool true/false与缺省null语义不变；N=0/3/50、N<=actualEpisodes；负数/超上限/布尔/浮点/字符串/矛盾组合拒绝。
2. 两Task含跨轮次EP0/1/2与EP3/49，复用Actor下每次执行使用实际`attempt["episode"]`而非首集设定、global counter；失败/Retry/Resume重复同一index不漂移。
3. 注入Fake MediaSink证实`rollout`bool按期望，`save_generated_video`独立且生成视频不被新N意外抑制；媒体失败不会影响Core/SR与Local Session清理。
4. 新候选Formal Root/Child SHA +狭窄源码Diff+CPU JUnit/Ruff/Evidence提交GPT Code Gate；不要复跑84/324/旧GPU、不启动真实Run、不自动合并V3。原旧媒体功能保留（兼容之前Run）。

Codex隔离实施任务已提交[GitHub Issue #14](https://github.com/wxwy/psm_wma/issues/14)；本设计Review不因运行中阶段性SR或DS报告自证而宣布900 Gate PASS。

## 四、后续独立事项

- 当前900继续运行；DS在下一份状态报告按上面Task/round/Local fast evidence修正，记录实际同一时间点源Manifest Root/Child、状态快照及真实Batch Histogram；不要求向ChatGPT交付此前已被Owner豁免的旧NoTTT OSMesa 4EP原始证据。
- 整体900结束后另审正式SR（`valid_success` + `valid_failure`覆盖900，Missing/Invalid/Skipped/Process Error分类与Clean qualification）、Local Fast State路径、证据和Owner决定；当前尚未达到冻结条件。