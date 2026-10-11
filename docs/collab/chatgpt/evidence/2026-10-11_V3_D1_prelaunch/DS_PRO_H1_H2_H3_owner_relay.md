# DS_PRO D1 Final CPU Prelaunch — H1/H2/H3 owner-relayed report
Date: 2026-10-11. Formal Root `444c232b976e80ac68cde9e7370e73b9f6410f0e`, Child/Gitlink `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`. The DS report was directly pasted to GPT; raw `/tmp` scripts/JSON are not accessible here and have **not** been directly audited.

**DS self-reported H1/H2/H3 PASS.** No GPU/torchrun/model load, forward/backward/optimizer/scheduler step, DCP save or original formal resume; Formal30k STOPPED.

H1: `/tmp/ds_pro_v3_d1_r1/h1/no_step_harness.py` (381 lines, SHA256 `007747e06a9081f6b5184dab01ed532d0a073a0ec8211bb0ab67ae5634be669f`), production full iter800 Shadow 5-component strict load and same-job; `window.begin→run_member(GA0)→run_member(GA1)→capture→abort`; reports py_compile, AST, signature and OFF/OFF vs ON/ON static preflight PASS. 

H2: `/tmp/ds_pro_v3_d1_r1/h2/pre_step_comparator.py` (SHA256 `4c49ba0e831ca59b8c3f69e15b6861cabda19fed8679630ab12e8bb313e1711c`). Frozen fp32 Loss (atol 1e-6, rtol 1e-5); fp32 Grad (atol 1e-6, rtol 1e-4); bf16 Loss/Grad (atol/rtol 2e-2); near-zero both absmax<1e-7; 14/14 CPU test cases. Full w0_fast_* values; other selected gradient markers use full tensor SHA256 and **256 sampled elements for tolerant numeric comparison**. Explicitly does NOT claim optimizer step parity.

H3: `/tmp/ds_pro_v3_d1_r1/h3/launcher.py` SHA256 `fd5b8616c6ea73e5717fe85b00bc349bd18b942af7d7fd958b1519f40b0ca299`; plans sequential ref→optimized launches, GPU sharing guard, no automatic retry. Generated displayed launch commands use `torchrun --nproc-per-node=8 ... /.../.venv/bin/python /tmp/.../no_step_harness.py` (no `--no-python`), and this appears to misplace the executable as the training script. Also suggested free>=25,000MiB; 8 H100 each still share external robotwin_server according to last resource report.

The real original `formal_verified_index_30k` is not a valid test output; the C1 independent Shadow Root is `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/ds_pro_shadow_c1_r2/` and job name `formal_verified_index_30k_shadow`. C1 remains PASS; the requested paired GPU experiment has not yet run.
