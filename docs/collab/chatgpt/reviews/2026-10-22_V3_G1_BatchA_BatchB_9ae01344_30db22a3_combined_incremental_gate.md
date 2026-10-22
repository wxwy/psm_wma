# PSM-WMA V3 — G1 Resume + RoboCasa Batch A/B 合并：精确新 Pair 增量 Gate

日期：2026-10-22
Owner 指令：“那就合并”（上一轮明确指向 Batch A 与 Batch B；已批准的 G1 Resume 必须保留）。
类型：合并操作的源码完整性/跨候选组合新 Formal Pair 审核；并非真实模型或第三方仿真安装验收。
**Formal new Root Implementation SHA：`9ae01344ffe82a3b403732aa61cce3dd7fb5055a`。**
**Formal new Child/Gitlink SHA：`30db22a3586c0270611753dc2ca0deb10ec27833`。**
**Pinned vendor patched local commit：`1ac174585293ed998ffc9cf73e47439798cf6f6c`，tree `195e30cfd5d37289d227a89234bd8bb069792905`；Root vendor.lock contains reconstruction data.**
**Merge/source integrity Verdict：`APPROVE` — 实际 V3 远端 Git 源码整合范围和对象绑定已完成并验证。**
**Combined implementation CPU/integration Evidence verdict：`REQUEST_CHANGES` — EVIDENCE-ONLY。** 组合后的精确Root/Child未在目标机以该Pair跑过 focused cross-regression；不能把此前 A 92+61、B 110、G1 115+32三份互不相同的Candidate CPU结果直接当作新Pair验收。真实Kitchen physics/benchmark Gate独立保持`REQUEST_CHANGES`；Batch C 仍未完成。

## 1. 受控合并及提交关系

1. 新 Child `30db22a3586c0270611753dc2ca0deb10ec27833` 为**真双父Merge commit**，第一父原已入Root-V3的G1 Child `7dd696efb4807e7338a5e420db2a1ede6cec67d0`，第二父Batch A Child `e42a2468672d3ef8fcba708fc19e70daec7c790e`；新Child树为G1父树上移植Batch A Child两个真实源Blob：
   - `cosmos_framework/simulation/robocasa/closed_loop_eval.py`：`e099c39c54b0157cda75af6313b5ca5eefac7012`；
   - `cosmos_framework/simulation/robocasa/closed_loop_eval_lifecycle_test.py`：`3a44d380c5333cfd30bddde480172bb7a485991e`。
   - 经GitHub compare确认新Child相对G1第一父**仅以上2文件**（+81/-41，新增119行）；G1的`examples/psm_wma_robocasa_corrected_phase5.py` Blob `6d78601c2fe99496e3b09cff2084f457a9644482`和测试`examples/psm_wma_robocasa_g1_cross_pair_resume_test.py` Blob `956c967b5f8b25eb2775c49624c365054c2b688e`均未修改。Child另建可访问独立合并ref `v3-integrated-g1-batch-a-b-20261022`，旧Owner训练隔离分支没挪动。

2. 新Root `9ae01344ffe82a3b403732aa61cce3dd7fb5055a` 为**三父Merge commit**：
   - 第一父：原 V3 HEAD `c3e108c720875c24ea028558594797d22b7b4b56`；
   - 第二父：Batch A Root `7646d41488a55d5a44ab193520a42c48cf5acc90`；
   - 第三父：Batch B r2 Root `891801bf44736e1eaf44b91377f98c5c5035edd0`。
   - GitHub远端 HEAD、提交父系、mode160000 Gitlink及完整`compare(first_parent,new_root)`均回读；Ref经`expected_sha`、`force=false`非强推更新，保留主线早已存在的全部审查/Inbox/docs历史。第一父到新Root仅15条路径发生变化（14个真实Root Batch A/B源码、Vendor、CPU tests +1 Gitlink）；没有意外覆盖G1 Launcher `scripts/train_v3_packed128_staged.sh` Blob `0514c1baab4a543c702f7033d765b810c038ab16`，也没有篡改旧G1根目录或Checkpoint。
   - Batch A Root移植：`scripts/eval_robocasa_18task_queue.py` blob`d063559077db1380bd7e0b9642cd99d5b380900c`，新`scripts/robocasa_processes.py`、原Queue identity tests及新Process tests均精确取自已审隔离候选Blob。
   - Batch B Root移植：`scripts/robocasa_vendor.py` blob `cea8e84aee0ae05c5fe3b5d7947a0200a9e6ed16`、`tools/v3/build_robocasa_vendor.py`、`tools/v3/robocasa_vendor_test.py`、`third_party/robosuite_patches/`的固定锁/补丁/Provenance/License/Runbook等全部10个Blob精确取自已审r2候选。
   - Vendor SHA是Patch基于robosuite tag`824ac14...`离线本地确定性构造产物，不是官方ARISE upstream已经有的分支提交；不能对公网GitHub误作可直接fetch SHA。

## 2. 本轮静态技术检查

- **模块重叠/冲突判定**：G1 Child独自修改`examples/psm_wma_robocasa_corrected_phase5.py`和其测试；Batch A Child独自修改`simulation/robocasa/closed_loop_eval.py`和新增生命周期测试，路径无交叉。Root Batch A修改Queue/Process/test4文件、B新增Vendor+Manifest/test10文件，未覆盖G1 Launcher或当前主线Review/Inbox。
- Batch A `per_task` Action Server、`max_sessions=1` Local-TTT required、有限Task/Episode wall deadline、owned Linux process PGID终止/回收、失败 `INCOMPLETE` 错误保真与Client finally cleanup原逻辑保留。旧Queue `--no-guardrails`、`--action-chunk-size 16`均继承。
- Batch B独立Vendor patchset基于robosuite v1.5.2，修复Legacy Controller非普通别名、懒初始化继承链、MuJoCo3.3.1 CCD真实native flag、sleeping false/no unsupported true，并添加运行时版本/源码来源/metadata区分的只读校验Helper。**没有**在本Batch B候选把Helper接进Queue，合并时亦**没有**偷偷接入；这属于后续Batch C集成合同，不可把“源码合入”称为已自动验证真实Simulator依赖。
- G1 Child仍保留 Owner只针对冻结源 e012/2d128 和 iter8900的显式跨Pair Resume + strict semantic/历史digest/8sidecars保障，`monkeypatch.setenv("HF_HUB_OFFLINE","1")` teardown修复未丢。
- **正在运行的G1**由Owner在旧隔离工作树手动启动；此次GitHub merge不意味着训练服务器工作树更新或重启，不准为更新V3修改活跃进程的源路径或环境变量。新V3 Root SHA若将来手动运行应将`EXPECTED_ROOT`与实际HEAD精确匹配；本Owner跨Pair例外仍仅限iter8900，后续从iter9000/10000不自动继承。

## 3. Evidence现状与确切后续验收条件

以前各自Candidate Evidence：
- G1: 原Child`61bf...`由Codex合成115方法+32subtests；一行pytest teardown修复后的Child`7dd...`已审核，仅目标机独立测试闭合还缺原始新的pytest执行日志。
- Batch A: Root`7646d...`/Child`e42a...`作者72 focus+61subtests以及20回归（共92方法），合成PID/HTTP/Sim边界；没有与G1新Child组合的真实GPU测试。
- Batch B: Root`891801...`/Vendor`1ac174...`作者r2 110 CPU单项，真实Native MuJoCo3.3.1 tiny XML、Legacy数值/继承类体通过；真实Kitchen/渲染和`SIM_PYTHON`安装未验证。

**新 Formal Pair `9ae01344... / 30db22a3...` 的集成 Gate 仍为 EVIDENCE-ONLY BLOCKED until DS fresh CPU**。最低DS验收：
1. 在**独立clean detached**的新Root/Child exact commit（非运行中G1工作树）只读checkout；root/child HEAD及Gitlink和源码diff、Vendor锁哈希/补丁sha检查；不改任何冻结G1资产、不切训练工作树、不能启GPU。
2. CPU-only执行原G1专用测试+F0/Config Truth及teardown无遮蔽定向复验；原`HF_HUB_OFFLINE`应在目标pytest启动前刻意未设置，再让monkeypatch维护其值，以确保原teardown故障不会被环境预置遮蔽；确保0failed/teardown-error，证据报告准确methods/subtests。
3. CPU-only执行Batch A Process/Queue/Child生命周期/身份与media相关回归；观察1/2/8workers真实synthetic进程组隔离、SIGTERM/SIGKILL、工作目录信号和队列INCOMPLETE行为，0fail/error。
4. CPU-only从离线固定robosuite/RoboCasa Commit与Patch新Vendor checkout复构建，核对Vendor Commit `1ac174585293ed998ffc9cf73e47439798cf6f6c`、Tree `195e30cfd5d37289d227a89234bd8bb069792905`、Ruff/syntax、实际Native MuJoCo小XML与Legacy方向测试；缺依赖则`BLOCKED`，不可skip/fake PASS。
5. 检查当前G1恢复训练不因源码审查被修改、强退或用新的Gitlink和`expected-root/child`混用；DS不检查GPU inventory，不启动任何新模型/仿真/训练。
6. 独立真实Kitchen/PandaOmron`create/reset/step` + camera/state/raw15/controller/CCD/Target Split物理验证另由Owner单独授权，不因CPU测试变Green自动放行；不要把过去脏DS四行补丁下SR5%变为正式Bench。
7. Batch C统一Owner手动`--config YAML`/GPU、任务、episodes、MP4、generated video、timeout、dry-run/list-tasks/完整Task attempt resume仍**未实现**；必须后续新的实现Pair并经过独立Gate。当前Merge不应被表述成已可执行未来Batch C手动命令。

## 4. 最终结论

**Git merge SOURCE-INTEGRITY：`APPROVE`**：新版V3已包含G1 + Batch A + Batch B精确候选源码，GitHub远端核对无丢失/冲突、无非授权源码覆盖。

**Combined formal Pair source/CPU Gate：`REQUEST_CHANGES`（EVIDENCE-ONLY）**：新Pair未有独立组合CPU运行证据；此项不指示Codex重写生产代码，只需DS在隔离clean该SHA下完成定向组合CPU Gate，若揭露逻辑问题再报Production blocker。

**Batch B real Kitchen physics/benchmark Gate：仍 `REQUEST_CHANGES`（单独后续Gate）；G1当前Owner已手动Resume保持不动。**
