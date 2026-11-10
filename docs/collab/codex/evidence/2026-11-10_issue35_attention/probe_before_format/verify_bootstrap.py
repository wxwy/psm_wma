"""CPU-only native launcher/helper precedence check; no checkpoint or scene."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    base = Path(__file__).resolve().parent
    root = base.parent / '_codex_issue31_prefix_pack_20261109/root2'
    output = base / 'bootstrap02'
    output.mkdir(exist_ok=False)
    helper = root / 'cosmos-framework/sitecustomize.py'
    digest = hashlib.sha256(helper.read_bytes()).hexdigest()
    expected = 'b80f9d0a2f876a4a66bd02dcc097ba7a7efb1ac46321a0cecb4fbffee3dbdf74'
    assert digest == expected, 'original helper changed; stop before delegation'
    paths = [str(root/'cosmos-framework'), str(base), str(root), str(root/'scripts')]
    os.environ['PYTHONPATH'] = os.pathsep.join(paths)
    sys.path[:0] = paths
    from capture_entry import prepend_probe
    from robocasa_eval_v2.identity import launch_environment

    native = launch_environment(output / 'cache')
    environment = prepend_probe(native)
    assert {k: v for k, v in native.items() if k != 'PYTHONPATH'} == {
        k: v for k, v in environment.items() if k != 'PYTHONPATH'
    }
    assert environment['PYTHONPATH'].split(os.pathsep)[0] == str(base/'hooks')
    environment.update(
        CUDA_VISIBLE_DEVICES='', LD_LIBRARY_PATH='',
        PYTHONDONTWRITEBYTECODE='1',
        ISSUE35_CAPTURE_DIR=str(output/'hook'), ISSUE35_TARGET_SOURCE_STEP='32',
        ISSUE35_ORIGINAL_STARTUP=str(helper), ISSUE35_ORIGINAL_STARTUP_SHA256=digest,
    )
    cases = [
        ('cli', [sys.executable, str(base/'capture_entry.py'), '--help']),
        ('policy', [sys.executable, '-m', 'cosmos_framework.scripts.action_policy_server_robocasa', '--help']),
    ]
    status = dict(original_helper_sha256=digest, native_environment_preserved_except_probe_precedence=True)
    for name, argv in cases:
        with (output/(name+'.log')).open('x') as log:
            result = subprocess.run(argv, cwd=root, env=environment,
                                    stdout=log, stderr=subprocess.STDOUT, timeout=120)
        status[name+'_exit'] = result.returncode
        assert result.returncode == 0, name+' help failed; retain log'
    status.update(hook_loaded=(output/'hook/hook_loaded.json').exists(),
                  class_instrumented=(output/'hook/class_instrumented.json').exists(),
                  model_initialized=(output/'hook/installed.json').exists())
    assert status['hook_loaded'] and status['class_instrumented'] and not status['model_initialized']
    status['status'] = 'BOOTSTRAP_ONLY_PASS_NOT_MODEL_GATE'
    (output/'result.json').write_text(json.dumps(status,indent=2)+'\n')
    print(json.dumps(status))


if __name__ == '__main__':
    main()
