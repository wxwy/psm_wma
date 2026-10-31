# EvalV2 与当前 V3 训练优化的无源码改写组合候选

日期：2026-10-31（CST）。当前状态：**ISOLATED_CANDIDATE / 原精确Child目标待Owner确认**，尚未更新canonical V3/v3-local-ttt。

- 原Owner观察：V3 `2ee690b0` / Child `0ae313e3`，希望合入已批 EvalV2 Root `d18b420c02cfc51a1b85e9f1d6ce5d26f7bd3163`、保持 Child `2f7334c4ada6ace1d21185985aae90539052bf18` 并保留训练。
- 实际fresh canonical：Root `369f3f4d82b8694b7efee5d5b16589d82aa00547` / Child `baf1b5bf46853e9849a91518803b9738fc216235`。另一路NoTTT Issue12+13已先合入，直接pin2f会丢掉13项训练改动。
- **组合源码Root `4139ad245b73cc1c16c9d4954241cecb81478992` / 新Child `6c83596d6a259e89c4cd3e79424024983426ac3d`**。新Child两parent为baf和2f；Root保留369与d18历史（中间含任务docs claim2b4097a）。原2f只作为approved Eval parent，不能把新Child伪称为2f。
- 隔离分支：Root/Child `v3-eval-v2-integration-20261031`。证据/ledger后继HEAD不替换上述被测source Pair。

## 实际改动与来源

没有编辑生产代码、没有调整双模式/Batch/共享GPU/OSMesa。Child两侧路径各13，交集为空；全部1270个tree对象精确等于已批Eval与当前训练delta并集。Root全部12407个tree对象除三份bookkeeper及Gitlink外同样为原对象并集。当前V3所有已有源码（Eval变化路径除外）、训练launcher/console/tests及既有docs均保留。三个文档冲突按canonical原字节prefix+历史候选追加条目+本轮claim处理，原件与resolution记录在raw/merge-doc-originals，不替换历史Review。

实际读取的正式依据：

- DualMode d18/2f `APPROVE_CODE`：`docs/collab/chatgpt/reviews/2026-10-30_V3_EvalV2_DualMode_d18b420c_2f7334c4_Incremental_Code_Gate_APPROVE_CODE.md`。
- NoTTT OSMesa `PASS (DS_PRO_REPORTED / OWNER_ACCEPTED)`：`docs/collab/chatgpt/reviews/2026-10-31_V3_EvalV2_NoTTT_OSMesa_Owner_Accepted_Report_Gate_PASS.md`。本轮尊重Owner免收raw要求，不再索要DS旧原件、不重跑4EP、不重构OSMesa。
- 当前训练组合57e3/baf `APPROVE_CODE`：`docs/collab/chatgpt/reviews/2026-10-31_V3_NoTTT_Issue12_13_Integrated_57e36dec_baf1b5bf_Composition_Incremental_Code_Gate_APPROVE_CODE.md`。

这些旧审核是来源依据；不把新组合冒充旧exact Pair，也不自授新的GPT/DS verdict。当前Owner已授权合并+light CPU，唯一待确认点为真实canonical推进后不可同时满足的“原Child精确2f”与“保留新baf训练”。

## 轻量 CPU 结果

**84 unique PASS，0 fail/error/skip，Shell0；source_unchanged=true。** Pytest73.25s，harness76.85s；1个明确的real_OS用例被计划排除（deselected），不是skip或失败。未重跑旧324/435/合成900或真实OS/OSMesa/Canary。

选择为Eval config17 + entry15 + dual-mode Root11（排除OS）+ Child dual35 + 当前训练integrated-entry6。涵盖off|required配置/Manifest/Resume、公共Server构造与CPU小DCP能力错配、B1/B2/Session/replay/timeout/End/无Local/真实Local fast CPU、Core拒绝，以及真实Shell→console→profile→CPU Trainer/AsyncLoader绑定。训练torchrun/真实数据/worker pool为替身，未执行训练或读取真实Job/DCP。

Ruff check24Python；format23+legacyQueue已改函数范围；compile24、3shell bash-n、明确revision source diff-check、真实未mock verify_source/import-origin、真实`run_robocasa_eval_v2.sh --help`的`--local-memory-mode {off,required}`均PASS。两次外部静态脚本scope计数断言（误把历史Evidence.py计入）发生在项目执行前，保留为preflight记录；修改的只有外部检查器，无正式源码/断言修改。

## 产物

`object_audit.json`包括全部tree并集证明及祖先；`raw/light-cpu/`原始JUnit/日志/argv/env/指纹；`raw/static-and-entries/`检查与SourceGuard/import smoke；`raw/merge-doc-originals/`保留三方原始冲突内容。原始文件mapping与artifact SHA清单可逐项复算。仅复制小型证据，不复制pytest tmp/微型Git仓库/缓存。

## DS CPU 交接（待canonical目标确认后使用）

使用新的干净Root工作树检出被测source Root `4139ad245b73cc1c16c9d4954241cecb81478992` 与Gitlink `6c83596d6a259e89c4cd3e79424024983426ac3d`，不能用旧NoTTT worktree或旧editable import代替。工作树之外新建evidence目录，将本目录`instrumentation/run_light_cpu.py`和`object_audit.json`一起复制到该新目录，运行：

```bash
/workspace/.venvs/psm-wma-cpu/bin/python /absolute/new-evidence/run_light_cpu.py /absolute/clean-composed-worktree
```

记录脚本验证完整source Pair、clean/Gitlink、禁GPU/离线、命令/JUnit/log/source unchanged；不自动安装依赖或执行GPU/真实模型/仿真/DCP。实际DS Python环境按其可用CPU环境等价准备。PASS要求84/84/零fail,error,skip/shell0/source unchanged、Mode CLI与import来源正确。可先使用相同static checker/按其命令验证source guard（其中工作目录绝对路径需与实际DS路径对应）。这是可复现CPU交接，**本会话没有向DS进程发送执行命令，也没有宣称DS已跑**。

NoTTT先18×1筛查/成熟后900、LocalTTT四集Canary属于Owner后续执行路线；本次不启动这些工作，不停止训练、不访问真实checkpoint、不改变已接受OSMesa recipe。
