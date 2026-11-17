# B core CPU evidence

Child 7e888f217dfcddc35ed73782f65c6e0890c72c3a，C0直接后继。最终 pytest.log / junit.xml 为
198 PASS/0fail/error/skip，28项 B-core 合成CPU检查。不是多轮累计，不是GPU/FSDP/端到端批准。
`core_initial/iteration2` 保留实现期间占位/空输入错误；`bf16_kv.log` 是fixture不当转换FP32 rotary
buffer，修正后的 `bf16_kv_corrected.log` 及最终 pytest.log 通过。其他 iteration logs 为中间迭代。
`disabled_c0_exact.log` 从Git对象加载C0原生源，对照输出/梯度/初始化及forward RNG逐位相等。

Child cwd：

```bash
CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu LD_LIBRARY_PATH='' PYTHONPATH=. OMP_NUM_THREADS=1 \
 /workspace/.venvs/psm-wma-cpu/bin/python -m pytest --noconftest -o addopts='' \
 cosmos_framework/model/generator/mot/g2_contracts_test.py \
 cosmos_framework/model/generator/mot/g2_core_test.py \
 cosmos_framework/model/generator/mot/memory_prefix_test.py \
 cosmos_framework/model/generator/mot/inference_text_kv_memory_test.py \
 cosmos_framework/model/generator/mot/local_memory_fsdp_scan_test.py \
 cosmos_framework/model/generator/mot/parallelize_unified_mot_test.py \
 cosmos_framework/data/generator/sequence_packing/runtime_test.py \
 cosmos_framework/data/generator/sequence_packing/packers_test.py -q \
 --junitxml=../artifacts/g2_model_b_core/junit.xml
CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu LD_LIBRARY_PATH='' PYTHONPATH=. OMP_NUM_THREADS=1 \
 /workspace/.venvs/psm-wma-cpu/bin/python ../artifacts/g2_model_b_core/check_disabled.py
```

CPU参考kernel只在test边界替换，生产代码仍走项目attention。10条warnings来自--noconftest下
旧L0/CPU marker未注册，不是skip。9文件strict Ruff在static.log；其余旧文件只免基线I001，
baseline_import_sort.log记录C0同样存在的I001。未关闭已有优化，未访问真实私有数据/GPU。
