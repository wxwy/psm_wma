# G2 integration CPU evidence — partial candidate

Code Child **6d72d4d252c287fc8060bdc5a8db7f6cf959af1e**，Root本提交绑定此Gitlink。
这是当前可审核候选，**不是完整训练集成/独立批准/GPU结论**。

最终 `pytest.log` / `junit.xml`：**442 PASS，0fail/error/skip，22文件，21.62s**。
重复迭代不累计。36 warnings 是 --noconftest 的旧marker、native CUDA autocast在CPU关闭等。
生产代码仍使用项目attention dispatcher；仅测试kernel边界替换CPU SDPA。无真实checkpoint/数据/GPU。

`g2_integration_test.py` 的12项组合证据覆盖：实际A Reader/projector、B三层MoT和native pack/
vision-action输入输出头，TRAIN_A冻结GEN后动作loss反传Global、真实CPU Local core.step_many，
none/Local-only/Global-only/both合批与单跑和缓存一致，全Global缺席无Reader/prefix却有零梯度，
C共享native specials/dropout与实际UND输入，Nemotron家族FP32/BF16原生/前置对照，D真实runtime/
hooks两个Session三轮replan cache-on/off的KV进入native动作头（含正常/空文本混批）。
这些不是完整训练步、真实数据对齐、实际FSDP或真实GPU服务闭环。

其他模块测试包含既有Session/Batch/Local事务、异常释放/重试和新mask内容绑定。D的多rank
Session cache明确拒绝；B FSDP准备方法/零图依赖只有CPU接口证据，执行侧仍需实测。

小型组合复现（Child cwd）：

```bash
CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu LD_LIBRARY_PATH='' PYTHONPATH=. OMP_NUM_THREADS=1 \
 /workspace/.venvs/psm-wma-cpu/bin/python -m pytest --noconftest -o addopts='' \
 cosmos_framework/model/generator/mot/g2_integration_test.py -q
bash ../artifacts/g2_model_integration/run_cpu.sh
mkdir -p work
CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu LD_LIBRARY_PATH='' PYTHONPATH=. OMP_NUM_THREADS=1 \
 /workspace/.venvs/psm-wma-cpu/bin/python ../artifacts/g2_model_b_core/check_disabled.py
```

Python路径可用G2_CPU_PYTHON替换。依赖满足时上述均无需GPU、checkpoint或离线数据。
完整suite命令与最终日志一致；runner不加入动态发现的GPU tests。
`disabled_c0_exact.log` 为C0原始Git对象四组输出/梯度/构造及forward RNG逐位相等；
后继保留旧native QKV/normalization执行顺序以减少编译BF16缓存物化变化，GPU仍NOT_RUN。
`ab_initial.log` 初轮失败来自测试把A真实Linear projector误写成Sequential参数名，未改A；
`ab_corrected/ab_anchor/first_composition/b_followup/nemotron/d_hooks/d_native_action` 为中间证据。

固定来源、无损blob/祖先关系与范围：sources.json、source_proof.log、child_scope.diffstat、root_scope.diffstat。
C的训练控制器/optimizer/warm-start/checkpoint后继与C最终Root handoff尚未到达；A/D Root证据已普通合入。不得据442项
关闭M05/M07或开启正式训练。DATA_B/C、真实GPU/FSDP/恢复/服务执行参数仍待固定来源与实测。
