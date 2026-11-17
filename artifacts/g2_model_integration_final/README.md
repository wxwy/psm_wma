# G2 final source / CPU integration evidence

Fixed Child **9370c3858532b4d61630138431145c8360e86eb0**，Root本提交唯一绑定该Gitlink。
最终来源 A4209b151 / C26243dae / D6991142，含B C0/core及集成修正；不是独立批准或真实执行结论。

唯一最终完整运行 `pytest.log` / `junit.xml`：**636 PASS，1 SKIP，0fail/error，30模块，37.98s**。
skip为旧 `examples.psm_wma_robocasa_corrected_phase5_test::test_optional_real_strict_snapshot10_preflight`，
原原因“未提供真实 exact-window cache/source/Edge/base/VAE 路径”，未改skip/断言。42 warnings来自旧markers、
CPU禁用native CUDA autocast及CPU DCP等。重复/各作者运行不相加，上一442证据只属于历史部分集成pair。

本轮统一包括：C最终v2静态初始上下文/一次dropout、DATA_C薄adapter、严格G1 model-only、原生optimizer/阶段时钟、
实际grouped/Local/GA/sidecar、单进程CPU DCP、2-rank Gloo、旧Phase5/No-TTT及D Session/Batch/cache。
13项B-owned组合使用实际Reader/native MoT和vision-action头：all-layer independent G/L、B1/mixed隔离、
冻结GEN反传Global、全Global缺席零图依赖、Qwen/Nemotron FP32/BF16、两个Session三轮replan cache-on/off条件进动作头、
C严格加载实际小模型无Global G1状态、A→B后模型/optimizer/阶段/RNG恢复与连续运行逐项相等、Local权重不变。
实际grouped Local事务与直接native-head/controller是分别明确的CPU组合，不能称真实训练端到端或FSDP通过。

生产attention只走项目dispatcher；测试仅在kernel边界替换CPU SDPA。未加载真实Edge/G1/Wan资产或真实DATA_B/C，
没有GPU/正式训练/900EP。主模型参数inventory/FSDP注册有源码/CPU证据，真实所有rank阶段切换/恢复仍NOT_RUN。

复现（Root cwd，已检出固定Gitlink）：

```bash
G2_CPU_PYTHON=/workspace/.venvs/psm-wma-cpu/bin/python \
 bash artifacts/g2_model_integration_final/run_cpu.sh
```

runner列明30文件、空CUDA、CPU、单线程和原始断言。无需联网、checkpoint或数据；真实资产preflight会保留一个skip。
小型13项组合可按handoff的Child cwd pytest命令复现。真实运行使用C既有Phase5 --g2-recipe和D原server，
详见各作者runbook；smoke必须recipe.grad_accum_steps=1，未填null/缺verified provider/权重版本factory则BLOCKED。

`c_stage.log/xml` 为C32项单独复核；`native_stage_fixed.log/xml` 为追加真实动作头/controller恢复检查。
`native_composition.log` 初轮漏import，`native_stage.log` fixture选fused=False被原生factory明确拒绝；
修fixture沿用原有fused=True后通过，未修改生产optimizer。所有原失败保留，不累计到最终结果。

`sources.json` / `source_proof.log`：36个A/C/D唯一归属blob与固定来源相同、所有来源为祖先、tracked Child与固定HEAD相同。
scope diffstat、static和skip详情同时归档。历史C0旧源码输出/梯度/RNG逐位对照在上一目录，后继未改Global-off生产路径。
完整A/C/D原始证据经普通Root merge保留，不拿作者CPU数量替代本轮统一结果。
