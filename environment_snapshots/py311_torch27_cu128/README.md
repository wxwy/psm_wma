# Python 3.11 / Torch 2.7 / CUDA 12.8 环境快照

该环境于 2026-08-14 停止作为 PSM-WMA 主环境。项目继续使用上游匹配度更高的 Python 3.13、Torch 2.10、CUDA 13.0。

已确认事实：

- Python 3.11.8、Torch 2.7.0+cu128、Torchvision 0.22.0、Triton 3.3.0 和 TorchCodec 0.5+cu128 可导入，40GB GPU 最小 CUDA 张量通过。
- 上游当前 `cu128` 依赖组实际面向 Torch 2.10；TorchCodec 0.10 与 Torch 2.7 ABI 不兼容。
- R04 使用原始 `FusedAdam` 时缺少匹配 Torch 2.7 ABI 的 Transformer Engine；临时切换 PyTorch AdamW 后可完成 optimizer 初始化。
- 既有 DCP 由 Python 3.13 写入，元数据引用 `pathlib._local.PosixPath`；Python 3.11 读取失败。内存兼容映射可读取全部 549 条 metadata，但相关源码适配已按用户要求撤回。
- Torch 2.7 缺少转换脚本依赖的 `torch.distributed.checkpoint.hf_storage`，因此不能直接用当前上游转换入口重新生成 DCP。

相关失败运行配置保存在：

- `artifacts/g0/r04/run_py311_torch27/`
- `artifacts/g0/r04/run_py311_torch27_adamw/`

源码中的 Python 3.11 专用 `typing.override`、DCP metadata 和 AdamW override 均已撤回，不应从该快照反向覆盖当前主线。
