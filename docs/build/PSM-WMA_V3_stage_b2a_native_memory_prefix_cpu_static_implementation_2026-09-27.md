# PSM-WMA V3 Stage B2-A implementation record

- Gate: `V3-STAGE-B2A-NATIVE-MEMORY-PREFIX-CPU-STATIC`; status: `REVIEW`，未自授 closure。
- Design authority: root `d57ef855404cabceed9c4190b13d435a98a30206` 的 B2-A v0.1；资源口径取同提交 Stage B2 resource profiles v0.2。
- Baseline child: `1ecebf1ab2fa64bc1d5906959c4cb1fe1d1edc5a`；implementation child: `366501b3b4626f30f0739d2e5765139a52f2308f`。

实现把 B0 Local32 `[K=4,D=32]` 作为独立前缀附在已物化的原生 consumer 上。`GenerationDataClean`、`SequencePlan` 和 `PackedSequence` 仅携带 per-sample Local payload；packer 不增加原生 token、position、split 或 loss 索引。网络注册 `local_memory_runtime`、`local_memory2llm` 与 `local_memory_modality_embed`，逐 decoder layer 用生成侧 input norm、K projection/K norm 与 V projection 构造前缀；只有 two_way 生成查询可读，reasoner causal 查询和原生 mRoPE 不变。多样本 `[Local,native]` K/V 交错是张量化的，不在 CUDA 热路径读取 tensor 值到主机。私有训练 override 在原生数据物化后复制 carrier 并附加 Local，不允许 dataset `local_memory` 第二 authority。

FP32 master bridge 的 Local 投影显式对齐原生 `target_dtype`；bridge 使用非零 fan-in 初始化。完整 Local slow 参数清单：encoder 29,440 + TTT core 66,240 + bridge 67,584 + modality embedding 2,048 = **165,312**（Edge hidden 2048）。当前 optimizer `_build_params_with_metadata` 的 `keys_to_select=["local_memory"]` CPU fixture 验证全部入选，host 参数被冻结，fast state 不在 `named_parameters()`。

验证命令：在 `/disk/rl/worktrees/cosmos-framework-v3`，设置 `CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu LD_LIBRARY_PATH='' PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1`，用 `.venv/bin/python -m pytest -c /dev/null --noconftest -p no:cacheprovider -q` 运行 `memory_prefix_test.py` 与 B0/B1 五个 `*_test.py`：**153/153 PASS**。新增文件 Ruff check/format PASS；全部修改文件 Ruff 排除基线 I001 后 PASS；`packers.py` 与 `omni_mot_model.py` 的 format debt 在 HEAD 基线同样存在，未重排 upstream 整文件；child/root `git diff --check` PASS。

边界：未接 active driver、trainer、DCP、在线 inference 或 GPU；4090 S1 和 H100 profile 均留后续 Gate。需 fresh review，不能把本记录当作运行或 closure 证据。
