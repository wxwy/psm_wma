# DS_PRO — V3 D1 GPU 前 J1 Launcher / J2 全梯度 Comparator 补证

**报告日期:** 2026-10-11
**固定 Formal Root:** `444c232b976e80ac68cde9e7370e73b9f6410f0e` / **Child+Gitlink:** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`
**Owner-relayed:** 本记录依据 owner 转交的完整 DS_PRO 130 行报告。GPT 未直接读取训练服务器 `/tmp` 脚本字节或现场 JSON。DS 宣称 J1/J2 CPU-only 验证完成且无 GPU、DCP Load、Trainer、Forward/Backward/Optimizer/Scheduler Step、DCP Save、生产源码改动或原 Formal30k Resume。

## J1：Launcher 修复（DS 报 PASS）

- 脚本：`/tmp/ds_pro_v3_d1_r1/h3/launcher.py`
- SHA256：`9b615b01e9025f6925da50d5f70bd4448dbb7020f364e3212e876ff8990e49cd`
- 将 positional training script 改为 `/tmp/ds_pro_v3_d1_r1/h1/no_step_harness.py` 本身；不再错误传入 `.../.venv/bin/python` 作为 torchrun positional；显式 `--max-restarts=0`。
- `free <25,000MiB`（任何一张卡）立即 `BLOCKED`；移除 20k–25k WARN 放行分支。需要 Owner GPU sharing approval、8×H100 可用、robotwin_server 稳定；不能杀掉外部进程。
- 保留外部按 `<mode>_attempt_<NN>` 独立拒绝覆盖的结果和首异常；Launcher 按 Reference OFF/OFF 然后 Optimized ON/ON 顺序执行，每模式最多一次；如果 Reference 错误，禁止启动 Optimized。
- CPU `--static-accept` + `j1_cpu_verify.py` 合计 21/21 PASS，进程 spawn 由 mock 替代，无实际 torchrun/GPU。
- 静态示例原始命令路径使用 `torchrun --nproc-per-node=8 --max-restarts=0 --rdzv-backend=c10d --rdzv-endpoint=localhost:0 /tmp/ds_pro_v3_d1_r1/h1/no_step_harness.py --mode <reference|optimized> --out-base /tmp/ds_pro_v3_d1_r1/gpu_run --attempt 1 --phase resume`，其余为 frozen Formal Pair、Shadow output、Source/Cache/Edge/VAE/DROID/index 参数；由 Guard-checked Launcher 统一启动而非手动两条独立命令。
- 报告称原 CUDA allocator env 没有额外注入；若运行时与 formal frozen env 不符须 fail closed，不能因「清理」而静默更改数值条件。

## J2：全梯度 Comparator 修复（DS 报 PASS）

- Comparator `/tmp/ds_pro_v3_d1_r1/h2/pre_step_comparator.py` SHA256：`3e84d2c676903bd471b38af6e04df3df4b18208f04c534cef91f19b2dcd06b60`
- Harness v2 `/tmp/ds_pro_v3_d1_r1/h1/no_step_harness.py` SHA256：`e854f7a4df27372863387b8706739601f16f44d1e68fb93e59755719815c50c5`
- CPU 正/负例 `/tmp/ds_pro_v3_d1_r1/h2/h2_positive_negative_cases.py` SHA256：`50d91e1de7413d07bc6d0a3e872eb63c9ea7ec92b4615be7b716ff1b99e53c23`，17/17 PASS；包括 index300 mismatch 而前 256 元素相同必 FAIL、全值缺失 UNVERIFIED、错误将 weight 充当 grad 时 BLOCKED。
- 数值 Comparator：全 local gradient tensor SHA256 相同才能判 `BIT_EXACT`；若 SHA 不同，必须读取可校验 SHA 的独立全量 `tensor_file` 或全量 values，按 (1<<20) 元素逐块比较；缺完整张量 `UNVERIFIED`，Evidence SHA 不匹配 `BLOCKED`；不允许以前256采样通过。真实 FSDP2 per-rank/FQN/shard/dtype/shape 一一对齐。
- `w0_fast_*` 从 `param.grad` 捕获并与 parameter weight hashes 区分；Candidate Local 逐 slot/identity/provenance、四 fast tensor（全量数值/持久化）和 committed members 进行对照，不止计数。
- 容差保持原冻结：FP32 Loss (atol=1e-6,rtol=1e-5)、FP32 Grad (1e-6,1e-4)、BF16 Loss/Grad (2e-2,2e-2)、near-zero both absmax<1e-7；非有限/shape/dtype/None-vs-zero 出现须 Fail。未执行 Optimizer Step/完整训练 throughput 标 NOT_TESTED。

## 原实物/边界

- Original formal Job `formal_verified_index_30k` STOPPED；source DCP 未改动（DS 声明）。
- 仅使用 C1 已验证的独立 Shadow Root `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/ds_pro_shadow_c1_r2/` 和 Job `formal_verified_index_30k_shadow`，每模式进程全新加载相同 iter800 same-job，`warm_start=False`、full Config Digest `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`。
- **DS 自评 J1_PASS / J2_PASS，申请 8×H100 Shadow-only 两模式各一次的 Pre-step numerical test**。本报告不声称真实 Loss/Gradient 已测。GPT Review 见 `docs/collab/chatgpt/reviews/2026-10-11_V3_D1_J1_J2_prelaunch_closure_444c232b_e9b8a41.md`。
