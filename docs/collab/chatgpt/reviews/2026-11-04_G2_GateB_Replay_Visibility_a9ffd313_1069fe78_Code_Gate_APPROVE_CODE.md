# GPT 独立增量 Code Gate — G2 Gate B Replay Visibility

- 日期：2026-11-04
- 正式结论：**APPROVE_CODE**，仅限本次 G2 Gate B 可见性/独立射线检测修正及只读 RGB 诊断代码 Gate。
- Formal Root implementation：`a9ffd313770c5344195f415425124a5075e62b2b`
- Child/Gitlink：`1069fe78841228cadbbfbe6afbd767eaed6225da`
- 隔离候选分支：`v3-g2-gateb-replay-fix-20261104`
- 基线报告 Root：`992cfc2adb3150c573d19206e176bd8a52574949`；既有 Stage-1 源码结论：`b67bc4ca9a2afb1ff26fac0846f8ee7042a589ab`
- 当前官方 V3：`083b36ac27ad43b6f5127d9a58aed4fac02eaaa7`；此处无 V3 合并。

## 审核范围与方法

独立读取 GitHub 上锁定的正式实现源码、父提交 Diff、旧 Gate B 失败报告、旧 Stage-1 Code Gate、G2 Gate B follow-up runbook、当前测试源码、原始作者 JUnit/summary 和范围绑定；没有依赖作者口头审批。正式增量 `992cfc2a...a9ffd313` 仅六个文件：一处生产代码 `tools/g2/rgbd_pose/replay.py`、新增软件渲染测试 `tools/g2/test_replay_render_visibility.py`、旧测试 fixture 的显式上下文元数据、runbook 和 SESSION/TODO。子模块未改，源码 blob `e8155a1850597e327e03578360188778de09fe12` 与作者绑定吻合。后续证据和 Inbox 仅是 bookkeeping，不是新的 Formal Root。

## Findings

1. **可见性筛选：未发现 code blocker。** `Replay.ray_check` 用原生 fresh depth 与 segmentation、场景 geom ID/opacity/visibility、同 ID 邻域和深度局部稳定性约束形成 eligible 集合；不以缓存深度数值或已观察到的 ray 误差选择通过样本。虽然使用传入 sample 的 valid mask，但完整版 verifier 另外要求缓存/当前 valid mask 完全一致，且 full-image cached/fresh depth 在原阈值内。未知渲染选项及低匹配数量返回 INCONCLUSIVE；可比较样本的错误仍可触发 FAIL。MSAA 筛选改变了可比样本范围，因此实际 RoboCasa 的覆盖率仍需专门检验，不得把筛选后的 PASS 当作全像素几何证明。
2. **front-face mesh 几何：未发现 code blocker。** 新 `_front_face_mesh_distance` 使用 live geom pose 和 MuJoCo compiled mesh 三角形，不重复施加 compiler mesh 变换；cull-face mesh 用正向三角相交，非 mesh / 关闭剔除仍用 native `mj_ray` 距离；近裁剪面起射并恢复光学 Z。合成正反面、旋转、缩放、同 geom 多层深度有测试。完整 RoboCasa mesh 的 CPU 开销和渲染后端行为尚未实测。
3. **RGB 诊断和原数值 Gate：未发现 code blocker。** 新增的同上下文 RGB-vs-RGBD、segmentation 前后 RGB 差异和材质/场景标量 fingerprint 只在 `ray_check` 内计算；`verify_robocasa_rgbd_pose.py` 未改，仍分别检查原始视频 RGB MAE ≤5、缓存/真实深度、valid mask、K/Pose 和独立 ray ≤0.01m、至少16条样本。没有用 RGB 诊断替换或绕过 RGB Gate。服务端实际 RGB 偏差的根因仍未确认。
4. **作者 Evidence 限定为 CPU。** 从原始 JUnit 独立核对：legacy83 为 83 tests / 0 failed / 0 errors / 0 skips；native software-render24 为 24/0/0/0；合计107 distinct。冻结的 old-source20 为9 failed/11 passed，新源20通过；legacy69个断言 AST 未变由作者提供绑定。Ruff/format/syntax 有落盘作者日志；本次 GPT 没有独立运行 CPU、GPU 或真实 RoboCasa，因此不将它称作 DS/GPT runtime parity。
5. **前轮 blocker 状态。** 先前6组实体复放中的独立 ray 误报风险，已有合成 CPU 复现和定向修正，但是否解释服务器的5/6几何 FAIL 尚未证实；服务端 RGB MAE 六组中5组超过5的既有失败仍 OPEN。旧失败报告不被新测试覆盖或改写。

## Gate 结论与严格边界

- **Code Gate：APPROVE_CODE**，针对精确 `a9ffd313770c5344195f415425124a5075e62b2b` + `1069fe78841228cadbbfbe6afbd767eaed6225da`。本轮未发现需要生产修复的 blocker；只批准下一阶段**另行授权**的隔离服务器 Gate B 重新验证，不意味着该真实 Gate 已获通过。
- **Physical Gate B：保持 FAIL / PHYSICAL_REPLAY_NOT_ACCEPTED**，不得进入 Gate C / N100 / 正式全量导出 / V3 合并 / 训练与 GPU 工作。
- 后续若获 Owner 单独授权，必须采用全新输出 namespace，对 `CloseFridge` local0/global502、帧0/214/428、left+eye_in_hand 进行同等真实回放；逐摄像头保留 RGB MAE≤5、0.01m/min16、全图深度/valid/K/Pose 与源绑定。RGB 未达标或有效 ray 样本不足仍 FAIL/INCONCLUSIVE，不能调阈值；必须单列可比样本数、mismatch、front-face mesh 样本数、执行耗时与 RGB 模式诊断。
- 服务端录制视频、RGB、Depth、数组、NPZ 或可逆编码不应离开服务器。此次审核没有修改生产代码、服务器工作树、训练/DCP、历史产物或官方 V3。

**Formal persistence：** 本 review 需要与 `docs/collab/chatgpt/CODEX_INBOX.md` 的 canonical append 同时存在才构成正式 verdict。