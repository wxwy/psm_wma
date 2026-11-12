# G2 Offline View 多 GPU、多 Worker 批处理调度

日期：2026-11-12。适用于已有 Source-MuJoCo Full Map、完整 10mm 颜色缓存和 nav_sg Native Dual Map 的 Episode。代码入口是 python -m g2.offline.batch_render。本阶段不负责原始 Episode 回放、Depth 导出和上游原生体素构建。

## 资源配置

现场参考配置：196 CPU、4 GPU × 80GB。调度器支持选择任意 1～8 张物理 GPU、每张 GPU 配置 1～8 个独立 EGL 渲染 Worker。最多支持 8×8=64 个可配置槽位。实际默认建议用 4,5,6,7 四卡做 A/B 测试，每卡从一个 Worker 开始，比较 4×1、4×2、4×4、4×8 的 Episode/hour，而不是假设同卡 8 个一定更快。

默认没有 CPU 配额限制，没有显存硬限额，没有单 Episode 的运行时长硬截止。可选参数：--min-free-mib N（默认 0 不检查）、--timeout-seconds N（默认 0 无超时）。显存/CPU 高占用时由用户调整并发，调度器不会改变训练进程或抢占其它 GPU 进程。

## Manifest 约定

绝对路径、明确源标识，示例：

    {
      "schema": "g2_gpu_batch_render_v1",
      "training_ready": false,
      "jobs": [
        {
          "id": "robocasa_episode_005077",
          "inputs": "/ABS/PATH/verified_005077_inputs.json",
          "prepared": "/ABS/PATH/verified_color_prepared",
          "native_output": "/ABS/PATH/nav_sg_native_005077"
        }
      ]
    }

输入必须已完成全部状态 Snapshot、10mm ColorManifest 和 Native F24 完成证明，Frame 数/索引一致，色缓存 Source SHA 与 Inputs 完全匹配。旧 Collision View 的 reference_views 不能移用于新 Visual Mesh 视图；应使用新输入绑定并保留独立人审 Gate。

## 典型命令

首先配置 V3、NAV_G2_RUNTIME_DEPS、G2_PYTHON、MANIFEST 和 OUT 的真实绝对路径，确保 Python 可以 import V3 和 nav_sg 已安装依赖。

    export PYTHONPATH="$V3:$NAV_G2_RUNTIME_DEPS"
    "$G2_PYTHON" -m g2.offline.batch_render plan \
      --repo-root "$V3" --manifest "$MANIFEST" --output-root "$OUT"

    "$G2_PYTHON" -m g2.offline.batch_render run \
      --repo-root "$V3" --manifest "$MANIFEST" --output-root "$OUT" \
      --gpus 4,5,6,7 --workers-per-gpu 1 --max-jobs 4 --allow-experimental

    # 扩大到 4 卡共 8 Worker：
    # --gpus 4,5,6,7 --workers-per-gpu 2 --max-jobs 8

    "$G2_PYTHON" -m g2.offline.batch_render report \
      --repo-root "$V3" --manifest "$MANIFEST" --output-root "$OUT"

真实启动必须明确给出 --allow-experimental 和 --max-jobs N，避免未通过 H1 时意外启动整套 9,126 Episode。运行每个槽位为独立 child process，使用其物理 MUJOCO_EGL_DEVICE_ID 和 CUDA_VISIBLE_DEVICES；CPU 调度进程不创建 EGL context。

## 断点与验收

调度器在同一 OUT 下写入不可覆盖的 job/attempt_0001、attempt_0002...；完整结果为每个 Episode 的 episode_receipt.json，必须与源 Inputs/Color/Native 的 SHA256、帧序列、每帧 Direct Color 和 Alpha 图层 PNG 的 SHA256 一致。仅进程返回码 0 不能视为成功。成功跳过、失败自动尝试后续任务，重试不覆盖旧输出。保存 _batch_plan.json（锁定源清单/代码 HEAD/Python）、_attempts、_logs、_receipts、_batch_run_report.json。锁阻止两个调度器同时写同一批次；SIGINT/SIGTERM 请求停止进程组。恢复时若 Git HEAD 或输入 HASH 已变化，则需要新输出根，不能混合前后版本。

H1、source Visual Geom/Material 颜色归属、未知背景、混合 Alpha 的待验收状态不因批处理成功而改变。所有结果仍为 training_ready=false。该调度器是 View-only；包含上游 RGBD/Color/Native 构建在内的全链路耗时不得用单独 View 导出 100 秒/Episode 冒充。

## 实测要求

先运行 CPU 模拟调度测试，包括 1～8 GPUs × 1～8 Worker、失败/超时/重试/信号/损坏回执/哈希/恢复；再做 4 卡、小批次实机验证，最后以实际吞吐评估 4×1/2/4/8 的性价比。用户提供的 196 CPU 与 4×80GB 是部署环境，不是代码里额外的限制。
