"""Bounded CPU witnesses against the exact checked source; no simulator/model."""
from __future__ import annotations

import ast
import hashlib
import json
import os
import threading
from pathlib import Path
from unittest.mock import Mock

import numpy as np

from cosmos_framework.simulation.robocasa import closed_loop_eval as module
from cosmos_framework.utils.rollout_evidence import run_recorded_episode
from cosmos_framework.utils.rollout_evidence import atomic_json
from robocasa_eval_results import finish_attempt, find_completed_attempt, start_attempt

ROOT = Path(os.environ.get('PSM_AUDIT_ROOT', '/workspace/psm_wma'))
OUT = Path(os.environ.get('PSM_AUDIT_OUTPUT', '/tmp/v3-audit-20261023'))
OUT.mkdir(parents=True, exist_ok=True)


class Env:
    def __init__(self, mode):
        self.mode = mode
        self.steps = self.checks = 0

    def reset(self):
        return {'step': 0}

    def get_ep_meta(self):
        if self.mode == 'metadata_exception':
            raise RuntimeError('synthetic task metadata error')
        if self.mode == 'missing_instruction':
            return {}
        return {'lang': 'close fridge'}

    def step(self, _):
        self.steps += 1
        # Real Kitchen.reward() also calls this oracle in env.step(). Model that
        # first call, then inject failure only in the evaluator's second check.
        self._check_success()
        return {'step': self.steps}, 0.0, False, {}

    def _check_success(self):
        self.checks += 1
        if self.mode == 'oracle_exception' and self.checks % 2 == 0:
            raise RuntimeError('synthetic success oracle error')
        return False


class Client:
    def begin(self, *args, **kwargs):
        pass

    def payload(self, *_):
        return {'synthetic': True}

    def acknowledge(self, *_):
        pass

    def record_completed(self, *_):
        pass

    def end(self, *_):
        return 'a' * 32 + ':0:' + 'b' * 32


def rollout_case(mode):
    env, calls, cleanup = Env(mode), [], []
    digest, attempt_id = 'c' * 64, 'CloseFridge/attempt_0001'
    task_root = OUT / 'complete_attempts' / mode / 'CloseFridge'
    directory = start_attempt(task_root, digest=digest, resume=False)
    action = [0.0] * 15
    action[4] = -1.0
    action[8:14] = [1, 0, 0, 0, 1, 0]

    def predict(*args, **kwargs):
        calls.append(args[2])
        return {'action': [action], 'local_memory': {'prefix_present': False}}

    module.compose = lambda _: np.zeros((16, 32, 3), dtype=np.uint8)
    module.predict = predict
    module.reset_local_memory = Mock()
    module.USE_BASE_ACTION, module.BASE_ENCODING = True, 'raw'
    result = run_recorded_episode(
        module.run_policy, env, output_dir=directory, episode=0,
        run_digest=digest, attempt_id=attempt_id,
        server_url='unused', image_size=256, action_horizon=1, max_steps=2,
        latch=1, timeout=1, generated_video_mode='none',
        local_memory_client=Client(), on_cleanup=cleanup.append,
    )
    assert result['outcome'] == 'behavioral_failure' and result['error'] is None
    assert env.steps == 2 and len(calls) == 2
    assert cleanup[0]['rollout_error'] is None and cleanup[0]['reset_ok'] is True
    if mode != 'oracle_exception':
        assert calls == ['', ''] and result['prompt'] == ''
    result['generated_videos'] = []
    atomic_json(directory / 'rollout00_episode.json', result)
    atomic_json(directory / 'results.json', [result])
    atomic_json(directory / 'rollout00_cleanup.json', cleanup[0])
    atomic_json(directory / 'process_cleanup.json', {
        name: {'pid': pid, 'pgid': pid, 'live_group': False, 'remaining_pids': []}
        for name, pid in [('server', 12301), ('simulator', 12302)]
    })
    progress = [dict(schema='psm_episode_progress_v1', evaluation_run_digest=digest,
                     evaluation_attempt_id=attempt_id, episode=0, event=event) for event in ('start', 'end')]
    (directory / 'episode_progress.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in progress))
    runtime = {'schema': 'synthetic CPU runtime fixture'}
    runtime_digest = hashlib.sha256(json.dumps(runtime, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
    atomic_json(directory / 'runtime_attestation.json', dict(runtime, digest=runtime_digest))
    validation = dict(digest=digest, runtime_digest=runtime_digest, expected_trials=1, video_mode='none',
                      rollout_enabled=False, init_png_enabled=False, sim_python=Path('/unused'))
    finish_attempt(directory, **validation)
    assert find_completed_attempt(task_root, **validation) == directory
    return {
        'reproduced': True, 'outcome': result['outcome'], 'error': result['error'],
        'prompt_sent': calls, 'action_count': env.steps, 'oracle_calls': env.checks,
        'cleanup': cleanup[0],
        'actual_attempt_validator_status': json.loads((directory / 'attempt.json').read_text())['status'],
        'actual_resume_validator_skips': True,
    }


def thread_case():
    path = ROOT / 'scripts/eval_robocasa_18task_queue.py'
    tree = ast.parse(path.read_text())
    execute = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'execute')
    block = next(n for n in execute.body if isinstance(n, ast.Try) and n.lineno == 795)
    stop, ready = threading.Event(), threading.Event()

    def work():
        ready.set()
        stop.wait(5)

    first = threading.Thread(target=work, daemon=False)

    class FailedThread:
        def start(self):
            assert ready.wait(1)
            raise RuntimeError("can't start new thread (injected)")

    namespace = {'threads': [first, FailedThread()], 'previous_handlers': {}, 'stop': stop}
    try:
        try:
            exec(compile(ast.Module(body=[block], type_ignores=[]), str(path), 'exec'), namespace)
        except RuntimeError as error:
            result = {
                'reproduced': first.is_alive() and not stop.is_set(),
                'startup_error': str(error), 'already_started_worker_alive': first.is_alive(),
                'stop_set_by_queue': stop.is_set(), 'source_block_first_line': block.lineno,
            }
            assert result['reproduced']
            return result
        raise AssertionError('injected startup error was lost')
    finally:
        # The probe, not the production block, releases its synthetic worker.
        stop.set()
        first.join(2)
        assert not first.is_alive()


if __name__ == '__main__':
    records = {mode: rollout_case(mode) for mode in ('oracle_exception', 'metadata_exception', 'missing_instruction')}
    records['partial_thread_start'] = thread_case()
    records['scope'] = 'actual rollout/attempt/resume functions with synthetic env/client/runtime/process boundaries; AST-selected actual thread-launch block'
    records['source_sha256'] = {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (
            ROOT / 'cosmos-framework/cosmos_framework/simulation/robocasa/closed_loop_eval.py',
            ROOT / 'cosmos-framework/cosmos_framework/utils/rollout_evidence.py',
            ROOT / 'scripts/eval_robocasa_18task_queue.py',
        )
    }
    (OUT / 'behavior.json').write_text(json.dumps(records, indent=2) + '\n')
    print(json.dumps({'reproduced_cases': list(records)[:4], 'synthetic_worker_reaped': True}))
