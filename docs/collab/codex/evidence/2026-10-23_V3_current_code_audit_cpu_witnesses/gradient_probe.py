"""Run the exact gradient guard methods on two CPU Gloo ranks, no model/DCP."""
from __future__ import annotations

import ast
import hashlib
import json
import os
from datetime import timedelta
from pathlib import Path
from typing import Any

import torch
import torch.distributed as dist
import torch.multiprocessing as mp
from torch.distributed.tensor import DTensor

OUT = Path(os.environ.get('PSM_AUDIT_OUTPUT', '/tmp/v3-audit-20261023'))
OUT.mkdir(parents=True, exist_ok=True)
SOURCE = Path(os.environ.get('PSM_AUDIT_ROOT', '/workspace/psm_wma')) / 'cosmos-framework/cosmos_framework/trainer/local_memory_grouped.py'


def get_guard():
    tree = ast.parse(SOURCE.read_text())
    base = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'GroupedLocalMemoryTrainer')
    names = {'_optimizer_parameters', '_require_finite_gradients'}
    selected = [n for n in base.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert len(selected) == 2
    cls = ast.ClassDef(name=base.name, bases=[], keywords=[], body=selected, decorator_list=[])
    program = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0), cls], type_ignores=[])
    ast.fix_missing_locations(program)
    namespace = {'torch': torch, 'dist': dist, 'DTensor': DTensor, 'Any': Any, 'OptimizersContainer': type('UnusedContainer', (), {})}
    exec(compile(program, str(SOURCE), 'exec'), namespace)
    return namespace['GroupedLocalMemoryTrainer']._require_finite_gradients


def worker(rank, rendezvous):
    torch.set_num_threads(1)
    dist.init_process_group('gloo', init_method=rendezvous, rank=rank, world_size=2, timeout=timedelta(seconds=15))
    rows = []
    try:
        guard = get_guard()
        # First case is a real nonempty parameter with ALL grads missing on rank1.
        # Second is a legitimate empty local parameter on rank1 (control).
        for label, empty_rank1 in [
            ('nonempty_rank_missing_all_grads', False),
            ('callback_clears_rank1_after_first_guard', False),
            ('some_selected_grads_none_each_rank_active', False),
            ('legitimate_empty_rank', True),
            ('all_ranks_missing', False),
            ('rank1_inf', False),
        ]:
            parameter = torch.nn.Parameter(torch.empty(0) if rank == 1 and empty_rank1 else torch.tensor([1.0]))
            unused = torch.nn.Parameter(torch.empty(0) if rank == 1 and empty_rank1 else torch.tensor([2.0]))
            optimizer = torch.optim.SGD([parameter, unused], lr=0.1)
            if rank == 0 and label != 'all_ranks_missing':
                parameter.grad = torch.ones_like(parameter)
            if rank == 1 and label in {'callback_clears_rank1_after_first_guard', 'some_selected_grads_none_each_rank_active', 'rank1_inf'}:
                parameter.grad = torch.full_like(parameter, float('inf') if label == 'rank1_inf' else 1.0)
            if label == 'callback_clears_rank1_after_first_guard':
                guard(optimizer)
                if rank == 1:
                    parameter.grad = None
            before = parameter.detach().tolist()
            error = None
            try:
                guard(optimizer)
            except Exception as exc:
                error = f'{type(exc).__name__}: {exc}'
            if error is None:
                optimizer.step()
            rows.append({'case': label, 'rank': rank, 'local_numel': parameter.numel(), 'guard_error': error,
                         'grad_present': parameter.grad is not None, 'before': before, 'after': parameter.detach().tolist()})
            dist.barrier()
        (OUT / f'gradient_rank{rank}.json').write_text(json.dumps(rows, indent=2) + '\n')
    finally:
        dist.destroy_process_group()


if __name__ == '__main__':
    mp.spawn(worker, args=((OUT / 'gloo_rendezvous').as_uri(),), nprocs=2, join=True)
    rows = [row for rank in range(2) for row in json.loads((OUT / f'gradient_rank{rank}.json').read_text())]
    problematic = [row for row in rows if row['case'] == 'nonempty_rank_missing_all_grads']
    assert all(row['guard_error'] is None for row in problematic)
    assert problematic[0]['after'] != problematic[0]['before'] and problematic[1]['after'] == problematic[1]['before']
    for row in rows:
        if row['case'] in {'all_ranks_missing', 'rank1_inf'}:
            assert row['guard_error'] is not None
        else:
            assert row['guard_error'] is None
    report = {'reproduced_missing_rank_guard_gap': True, 'scope': 'AST-selected exact guard, CPU SGD + actual two-rank Gloo; no FSDP/native training',
              'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(), 'rows': rows}
    (OUT / 'gradient.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'reproduced_missing_rank_guard_gap': True, 'ranks': 2, 'scenarios': 6, 'empty_rank_control_retained': True}))
