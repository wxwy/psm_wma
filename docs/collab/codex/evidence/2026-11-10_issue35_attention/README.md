# Issue35 作者诊断证据（未完成真实输入 Gate）

实施 Pair 始终为 Root18be4a80a5ae4d97bc7d287034d24efab847c496 /
Child-Gitlink193627f42f4cd1ba6d563aefb8fa8f9428ecb56d。这里只有文档、
自有外部诊断代码、本地CPU日志/JUnit、派生统计/哈希；没有服务器原始文件。

详细状态见 `../../reviews/2026-11-10_Issue35_Attention_ExistingTrace_RealInputCapture_BLOCKED.md`。

- `diagnostic_status.json`：从服务器自有探针得到的派生状态，不是独立审核。
- `profile_statistics.json`：已有合成输入profile的分类统计，不是真实请求验收。
- `probe/`：当前格式整理后的自有诊断工具；不是EvalV2生产路径。
- `probe_before_format/`：CPU/启动测试执行时的工具版本及哈希，保留审计。
- `local_cpu/snapshot02.xml` / `.log`：最新4项CPU无损保存测试，Shell0；
  `snapshot.xml` / `.log`是此前3项初检，不能相加成7项独立项目验收。
- `local_cpu/static_initial.log`：初始工具静态问题；原样保留。
- `local_cpu/static_final.log`：当前probe Ruff检查成功。
- `local_cpu/formatting_equivalence.json`：关键snapshot/hook/bootstrap/reducer
  格式整理前后AST相同；driver lambda→def、egl_probe复合import拆分另列。

本地CPU命令（执行时工作目录 `/workspace/work/issue35-evidence`）：

```bash
env CUDA_VISIBLE_DEVICES='' LD_LIBRARY_PATH='' \
  OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  PYTHONPATH=/workspace/work/issue35-evidence:/workspace/work/psm-wma-attention-issue35/cosmos-framework \
  /workspace/.venvs/psm-wma-cpu/bin/python -m pytest \
  --noconftest -c /dev/null --rootdir=/workspace/work/issue35-evidence \
  -p no:cacheprovider -q snapshot_test.py --junitxml=snapshot02.xml \
  >snapshot02.log 2>&1
```

服务器自有目录 `_codex_issue35_attention_20261109` 中保留原始补采失败、
EGL检查、bootstrap02和75文件索引，地址与SHA见报告。`capture_driver.py`
是待原生EGL物理证明通过后才可使用的后续短补采工具；这次没有capture02，
没有成功模型请求。不能因help/CPU测试成功就宣称冻结输入录制已通过。

不重复No-TTT，不关闭K1/K16真实动作差异，不提交Attention生产补丁，
不请求对未变Stage2 Pair重新Code Gate，不合并V3。
