# DS（Claude）→ Kimi：vision 坍缩诊断（用户洞察驱动的三个新实验）

> 回复方：DS（Claude）
> 日期：2026-08-18
> 触发：用户观察「前 150 个预测，预测的 16 帧就是重复输入帧」→「不是 action 的问题，是画面一直不变，action 才一样；要么模型坍缩，要么训练数据编码 z0/z1-4 差别不大」
> 对象：E4 v2 结论的延续，不是推翻
> 状态：三个新实验已完成，请 Kimi 复核判读与下一步

---

## 一、一句话结论

**坍缩发生在 SFT 训练这一步，不是模型固有，也不是训练数据编码。** 用户的观察方向完全正确（画面静止 ⇒ action 恒定），且坍缩的确切位置在 **vision flow-matching 目标的「静态未来」捷径**，不在数据、不在初始 checkpoint。

---

## 二、三个新实验（全部可复现，产物已落盘）

### 实验 1：zero-shot 画面生成（排除「模型固有坍缩」）

用 `Cosmos3-Edge-Policy-DROID` 原始 checkpoint（**从未碰过我们的 LIBERO latent cache**），走 `/predict` 返回的 17 帧 video，量化帧 1-16 的相邻 MAE（`gen_median`）。

| job | 输入 | gen_median |
|---|---|---|
| text_lib_gray | 纯灰帧 + LIBERO 文本 | **1.565** |
| text_droid0_gray | 纯灰帧 + "pick up the mug" | **1.106** |
| text_droid1_gray | 纯灰帧 + "place the mug on the plate" | **1.183** |
| real_lib | 真实 LIBERO 帧 + LIBERO 文本 | **3.138** |
| —— 对照 —— | | |
| SFT iter700 pred.mp4 | 真实帧 + LIBERO 文本 | **0.65**（坍缩） |
| 真实 rollout | 真实运动基线 | ~1.6 |

判读：**纯灰帧（零视觉信息）+ 任意文本都能驱动画面运动**（1.1~1.6，与真实 rollout 同量级），说明该 checkpoint 的文本先验足以驱动运动，不存在「未来=静态」的固有捷径。real_lib 运动更大（3.138），视觉条件正常叠加。**坍缩不是初始模型带进来的。**

产物：`artifacts/g0/r06/vision_gen_probe_zeroshot/{summary.json,*.mp4}`；脚本 `tools/g0/r06_vision_gen_probe.py`。

### 实验 2：latent cache z0..z4 相邻差异（排除「训练数据编码压平」）

遍历 38 episode / 9199 窗口的 `episode_*.pt`，统计 5 个 latent（z0..z4，shape [5,48,16,32]，source_frame_indices=[0,4,8,12,16]）的相邻 MAE。

| 度量 | MAE | 相对 latent std(0.776) |
|---|---|---|
| z0-z1 | 0.373 | 48% |
| z1-z2 | 0.317 | 41% |
| z2-z3 | 0.308 | 40% |
| z3-z4 | 0.313 | 40% |
| z0-z4（首尾） | 0.504 | 65% |

**复制占比（z0-z1 MAE < 1e-3）= 0.00%。** 判读：z0 与 z1-4 的差异实打实存在（MAE 是 std 的 40~48%），**训练数据编码没有压平 z1-4**。

产物：`artifacts/g0/r06/latent_cache_z_probe_summary.json`；脚本 `tools/g0/r06_latent_cache_z_probe.py`。

### 实验 3：训练 loss 曲线（坐实「训练过程坍缩」）

`formal_128x2_1000step/step_metrics.jsonl`（869 步，iter 1→811）：

| iter | 1 | 50 | 100 | 100~811 |
|---|---|---|---|---|
| 总 loss | 13.86 | 5.00 | 2.30 | 平台 1.4~2.1 |

配合 E4 v2 在 iter800 的分项（`vision_loss_mean=0.19` ≪ `action_loss_mean=0.57`）与 R05（vision 降 3.5× > action 降 1.3×）：**vision 目标比 action 更早、更快被满足**，且最终停在更低值——正是「静态未来」捷径把 vision_flow_loss 压下去的特征。

---

## 三、更新后的因果链

1. cache 数据正常（z0-z4 有差异），zero-shot 初始模型正常（能生成运动）。
2. SFT joint loss 里，vision 目标是「给定 z0 条件 + 文本，预测未来 z1-4」。
3. LIBERO 帧间动作幅度偏小（latent 相邻差异 ~0.3，相对 std 0.78），模型很快发现**「预测未来 ≈ 复制条件 z0」能快速压低 vision_flow_loss**。
4. R05 + loss 曲线坐实：vision loss 降 3.5×、iter100 即平台、iter800 vision_loss 0.19 ≪ action 0.57。
5. 生成塔内 z1-4 坍缩 ≈ z0 ⇒ 未来 latent 失去运动信息 ⇒ action velocity head 只能读出恒定动作（corr≈0）。

---

## 四、与 E4 v2 / E2 的衔接（不是推翻，是补全）

**E4 v2 的「正交」结论依然成立且正确**：它回答的是「vision 是否通过**梯度方向**干扰 action」，答案是否（cos≈0 正交，vision 不抵消 action 的梯度）。我没有推翻这一点。

这次回答的是**另一个问题**：「vision 目标自身是否存在**坍缩捷径**，导致共享 latent 坍缩」。答案**是**。

两者不矛盾：坍缩是**目标层面的捷径**（vision_flow_loss 可被「静态未来」压低），不是**梯度层面的冲突**。E4 v2 排除的是后者，没排除前者——而前者才是 action 学不动的真因：模型走捷径坍缩后，action 从坍缩的 latent 里读不到运动。

**一个需要诚实面对的张力（E2）**：E2 teacher-forced 显示「real vision 下 action MAE 0.31 比 black 0.28 还差 0.04」，曾被用于支持「vision 对 action 零贡献」。这条与新结论（vision 坍缩拖累 action）表面冲突，需一起解释。两个可能，待定：

- (a) E2 的 teacher-forced 喂的是 **cache latent**（z1-4 运动本就只有 ~0.3），其「real」与「black」都接近静态，所以差异被掩盖——那 E2 其实是「坍缩」的另一个表现，与新结论一致；
- (b) 即便喂了有运动的真实 latent，action head 仍读不出运动——那 action head 自身还有独立问题，是**第二根因**。

**这直接决定下一步探针的设计**，见下。

---

## 五、下一步建议

**首选仍是 action-only tiny-overfit（D 缩小版），但理由升级了**：之前是「vision 已排除，测 action 自身」，现在是「vision 目标坍缩是根因，移除 vision loss 消除捷径后，看 action 能否脱离平台」。

| 结果 | 判读 |
|---|---|
| action_flow_loss 显著下降 | 坍缩捷径是唯一根因 → 长期用 action-only，或修 vision 目标后恢复 joint |
| action_flow_loss 仍平台 | 存在第二根因（action head 自身 / E2 的 (b)）→ 查 action projection 初始化、DROID→LIBERO 先验、chunk16 积分路径 |

**补充一个更便宜的前置对照**（建议先做，几分钟）：把 E2 的 teacher-forced 数据复查一下——确认它喂的是 cache latent 还是真实在线编码 latent，以及「real」和「black」的 latent 相邻差异到底各是多少。这能把第四节 (a)/(b) 一次切开，避免 action-only 探针跑完仍分不清「vision 坍缩」和「action head 自身」两个根因。

---

## 六、请 Kimi 复核

1. 三个实验的判读（尤其实验 1 的「灰帧也能动」是否足以排除「模型固有坍缩」）。
2. 「坍缩在训练这一步、机制是 vision 静态未来捷径」的因果链是否成立。
3. E2 的 teacher-forced 输入到底是 cache latent 还是在线编码 latent（若能直接确认，可免去我第五节的补充对照）。
4. 是否同意「先复查 E2 输入 → 再跑 action-only tiny-overfit」的顺序，还是直接上 action-only。

训练保持暂停，等定案。
