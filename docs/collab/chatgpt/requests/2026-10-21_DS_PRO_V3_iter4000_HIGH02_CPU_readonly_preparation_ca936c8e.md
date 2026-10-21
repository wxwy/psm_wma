# DS_PRO — iter4000 HIGH-02 新Pair CPU独立验证与只读准备

日期：2026-10-21。**只读源码/元数据、CPU合成测试和新外部Evidence。当前不授权GPU、真实Action Server/Simulator、训练、DCP写入、修改源代码或清理旧结果。** 下面GPU命令仅供后续GPT验收和Owner单独批准，全部NOT EXECUTED。

## 精确版本

- Implementation Root：`ca936c8eecd593133b1e6c61ba5691331958c592`。
- Child / Gitlink：`2d128ed5a07601cdd424974f99b67832eafeeb41`（不变）。
- Queue Blob：`eec2702d5382358e131928db60ce75c93c0c55d5`。
- Root V3及 `v3-iter4000-server-identity-20261021` 可达；后续docs HEAD不是Implementation。
- 作者报告：`docs/collab/codex/reviews/2026-10-21_V3_iter4000_server_identity_HIGH02_author_handoff.md`；Evidence：`docs/collab/codex/evidence/2026-10-21_V3_iter4000_HIGH02_author_cpu/`。
- HIGH-01已正式撤销，禁止改锁；只验证HIGH-02及其拒绝结果的错误保全，不重开训练Gate。

安全使用clean detached精确Root/Child，保留原工作区和所有未提交内容；不得reset/clean/force。不能锁版本则BLOCKED。创建新的外部Evidence/临时fixture目录，可写HF/MPL/pycache，`CUDA_VISIBLE_DEVICES=''`、offline；不安装或替换依赖。记录Python/Ruff/pytest、Root/Child/Gitlink、Blob和before/after clean状态。

## 1. CPU复验

工作目录为Root，使用现有CPU Python；下面是CPU测试命令（不是仿真）。外部ini仅包含 `[pytest]`。设置PYTHONPATH为本次Root、Root/scripts和Root/cosmos-framework，禁止误用旧工作区源码：

```bash
python -m pytest --noconftest -c "$EVIDENCE/pytest.ini" -q -s -p no:cacheprovider \
  tools/v3/eval_robocasa_queue_identity_test.py tools/v3/remaining_optimizations_test.py \
  -k 'queue or identity or screening or evaluation or resume' \
  --junitxml="$EVIDENCE/pytest.xml"
ruff check --config cosmos-framework/.ruff.toml \
  scripts/eval_robocasa_18task_queue.py tools/v3/eval_robocasa_queue_identity_test.py
ruff format --check --config cosmos-framework/.ruff.toml \
  scripts/eval_robocasa_18task_queue.py tools/v3/eval_robocasa_queue_identity_test.py
python -m py_compile scripts/eval_robocasa_18task_queue.py tools/v3/eval_robocasa_queue_identity_test.py
```

Ruff0.12.7。若既有回归的Torch CPU依赖不可用，先独立运行 `python tools/v3/eval_robocasa_queue_identity_test.py -v`（stdlib-only），如实标扩展回归BLOCKED，不能宣布整个Gate通过或删除选项。预期新13方法、既有15case；作者pytest9实际28 passed +41subtests、55无关deselected、0skip/fail/error。Runner计数可不同，按方法/子测试区分，不把JUnit69当69个独立方法。

核对12个QUEUE_WITNESS、无hang/残留线程和本次拥有进程均退出：1/2/4 Worker各4Task×5结果；非首端口占用零Popen/无输出claim；错checkpoint/config/mode、Config中途变化零sim调用；同路径/采样完全匹配但属于旧进程的监听端口拒绝且旧进程未被Queue终止；20条结果已齐时另Worker启动失败/Server死亡仍有worker_errors、INCOMPLETE/sr=None/RC1。合成视频不是实际MP4验收。

在目标Linux环境特别验证 `/proc/<pid>/fd` 与 `net/tcp` 的同用户访问和HTTP stand-in监听归属。Child真实HTTP是在Popen主进程中，非多层server wrapper。若现场通过launcher fork到不同监听PID或/proc不可读，报告BLOCKED，不绕过验证或扩大权限。

确认scope_proof：Lock仍threading.Lock、publish仍锁外；server/sim command、身份模块、Child不变。不存在HIGH-01整改需求。源码不能为通过测试而改动。

## 2. 真实四任务与iter4000：仅元数据预检

请先填现存的服务器真实路径，**不从本文猜测/创建资产**：ROOT_WORKTREE、CHECKPOINT、CONFIG_FILE、DATASET_ROOT、SERVER_PYTHON、SIM_PYTHON、BASE_PORT、GPUS、OUTPUT_DIR。GPUS必须现场空闲，未来最多4张；推荐两张，但不能把例子2,3当当前资源已空闲。OUTPUT_DIR必须全新，Evidence外置，不写Checkpoint/源工作区。

下例是DS在已批准只读准备范围内可使用的CPU核对模板；不启动模型或Simulator。环境变量需真实填好，读取小型complete JSON和metadata/stat，不反序列化或hash模型shard body：

```bash
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 "$SERVER_PYTHON" - <<'PY'
import json, os, subprocess, sys
from pathlib import Path
root = Path(os.environ['ROOT_WORKTREE']).resolve()
def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True).strip()
assert git(root, 'rev-parse', 'HEAD') == 'ca936c8eecd593133b1e6c61ba5691331958c592'
assert git(root / 'cosmos-framework', 'rev-parse', 'HEAD') == '2d128ed5a07601cdd424974f99b67832eafeeb41'
assert git(root, 'ls-tree', 'HEAD', 'cosmos-framework').split()[2] == '2d128ed5a07601cdd424974f99b67832eafeeb41'
assert not git(root, 'status', '--porcelain')
assert not git(root / 'cosmos-framework', 'status', '--porcelain')
sys.path.insert(0, str(root / 'scripts'))
import eval_robocasa_18task_queue as q
tasks = q.discover_task_datasets(Path(os.environ['DATASET_ROOT']).resolve(), 4)
assert {name for name, _ in tasks} == {'CloseFridge', 'TurnOnSinkFaucet', 'PickPlaceSinkToCounter', 'NavigateKitchen'}
cp = Path(os.environ['CHECKPOINT']).resolve()
assert cp.name == 'iter_000004000'
complete = json.loads((cp / 'complete.v1.json').read_text())
assert complete['complete'] is True and complete['iteration'] == 4000 and complete['world_size'] == 8
for name in ('model', 'optim', 'scheduler', 'trainer'):
    assert (cp / name / '.metadata').stat().st_size > 0
for rank in range(8):
    assert (cp / 'dataloader' / f'rank_{rank}.pkl').stat().st_size > 0
assert Path(os.environ['CONFIG_FILE']).is_file()
assert not Path(os.environ['OUTPUT_DIR']).exists()
gpus = [item.strip() for item in os.environ['GPUS'].split(',') if item.strip()]
assert 1 <= len(gpus) <= 4 and len(gpus) == len(set(gpus))
q.require_free_ports([int(os.environ['BASE_PORT']) + i for i in range(len(gpus))])
print(json.dumps({'tasks': [(name, str(path)) for name, path in tasks], 'checkpoint': str(cp), 'ports_free': True}))
PY
```

还应登记真实Config SHA、训练/推理合同（raw15/state、H16/17帧、camera/state/base）、Checkpoint完整标记与模型stat身份，保持与现有不可变训练资产一致。此模板的小文件存在检查不冒充完整GPU模型载入/Save→Resume验收，也不替代原已关闭Gate。没有读取到服务器真实目录就报告未测，不能用作者合成目录代替M03。

若真实Config会被现有Server解析成action_chunk_size32、state=False或别的协议，提前报告BLOCKED。新Queue只接受16/64/raw15/state/required/fps20，不会改命令参数去覆盖原Config，也不授权DS增加override。实际 `/info` 检验要到之后获批的GPU Server阶段完成；本轮不启动Server来补它。

## 3. 仅未来授权后手工运行的模板：NOT EXECUTED

必须先取得新Pair GPT增量验收、Owner单独GPU/仿真许可，且目标GPU显存/磁盘空间/端口现场检查通过。不能抢占或共享仍被训练作业占用的卡；本轮不操作任何训练进程。

```bash
cd "$ROOT_WORKTREE"
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  "$SERVER_PYTHON" scripts/eval_robocasa_18task_queue.py \
  --checkpoint-path "$CHECKPOINT" --config-file "$CONFIG_FILE" \
  --dataset-root "$DATASET_ROOT" --output-dir "$OUTPUT_DIR" \
  --server-python "$SERVER_PYTHON" --sim-python "$SIM_PYTHON" \
  --gpus "$GPUS" --base-port "$BASE_PORT" \
  --expected-tasks 4 --num-test-episodes 5 --action-horizon 16 \
  --seed 0 --num-steps 30 --guidance 1.0 --timeout 600
```

显式GPUS，不用默认8卡；1/2/4张卡分别1/2/4个Worker，每个一个Server、一个串行Simulator、max_sessions=1、client slot0。同Task5个Episode顺序reset，20个Episode总量不随卡数变化；不是训练B8 Slot，也不是5个独立显式seed。Server policy sampler seed保持0，Queue `--seed 0`为环境主seed。

每Worker保留action_server.log、验证通过的server_info.json、server_process.json；每Task保留eval.log、results.json、逐动作/失败Evidence和5个实际非空可解码rollout MP4；保留全局evaluation_manifest.json、screening_summary.json和退出码。真实验收须4Task×5=20、无runtime_error/worker_error、每Task身份校验PASS，不能把CPU占位视频或行为失败/基础设施失败混同。生产native sim整体deadline问题没有在本次新增watchdog，具体运行仍须经审查的终止与清理方案，不能因本次CPU无hang就宣称任何sim卡死都已解决。

`--resume`：仅同exact Root/Child/config/checkpoint/protocol/task-set下的完整Task结果可复用；partial1–4条拒绝，actions/视频独占文件不能覆写。此Root改变了digest，旧Root结果不能导入。本入口不支持Episode边界继续；保留旧partial namespace，在批准的新隔离namespace从task/queue初始协议重跑，不跨Attempt拼接。同身份已完成Task复用也不意味着入口完全不启动Server。

## 4. 交付并停止

返回小型gate.json、完整命令/cwd/env/版本/RC、JUnit/日志、负例Witness、before/after source/Child洁净证明、四Task真实metadata集合/唯一性、真实Config/Checkpoint小文件身份、端口/proc兼容性、GPU/容量只读准备结论。任何测试失败停止，环境/资产/权限不足BLOCKED；不修改源代码修复，不删除原Evidence。

交GPT对上述新Formal Pair增量验收。**当前GPU_RELEASE仍未授权；不要直接执行第3节。**
