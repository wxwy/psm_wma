import ast
from pathlib import Path
from unittest.mock import Mock
import pytest
import numpy as np


def old_runner(env_error=None, media_error=None):
    path = Path(__file__).with_name('baseline_closed_loop_eval.py')
    node = next(n for n in ast.parse(path.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == 'run_policy')
    node.returns = None
    for arg in node.args.args + node.args.kwonlyargs:
        arg.annotation = None
    client = Mock()
    client.end.return_value = 'synthetic-session'
    reset = Mock(side_effect=RuntimeError('reset failed') if media_error else None)
    env = Mock()
    env.reset.side_effect = env_error
    scope = {'np':np, 'compose':lambda _:np.zeros((2,4,3),np.uint8),
             'save_partial_video':Mock(side_effect=media_error), 'reset_local_memory':reset}
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),scope)
    kwargs = dict(server_url='synthetic', image_size=256, action_horizon=16,max_steps=0,latch=1,timeout=0.1,local_memory_client=client)
    return scope['run_policy'], env, client, kwargs


def test_reset_error_still_cleans_episode():
    run,env,client,kwargs = old_runner(env_error=RuntimeError('env reset failed'))
    with pytest.raises(RuntimeError,match='env reset failed'):
        run(env,**kwargs)
    client.end.assert_called_once_with(0)


def test_encoder_primary_error_is_not_replaced_by_reset_error():
    run,env,client,kwargs = old_runner(media_error=RuntimeError('encoder failed'))
    with pytest.raises(RuntimeError,match='encoder failed'):
        run(env,**kwargs)
