"""Expected RED against exact fac029c8 symbolic source, never a production module."""

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

import pytest

path = Path(__file__).with_name('frozen_r1_protocol_model.py')
spec = importlib.util.spec_from_file_location('frozen_phase_b_r1', path)
old = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = old
spec.loader.exec_module(old)


def test_b_d1_no_positive_ack_before_batch_quiescence():
    model = old.ProtocolModel(2)
    leases = tuple(old.Lease(model.epoch, f'slot{i}', 1, f'session{i}', f'ep{i}') for i in range(2))
    for lease in leases:
        model.open(lease)
    requests = tuple(old.Request(lease, 0) for lease in leases)
    witness = {}

    def before_publish():
        witness['end_ack_while_batch_owned'] = model.reset(leases[0])
        new = replace(leases[0], generation=2, session='new-session', episode='new-ep')
        try:
            model.open(new)
            witness['slot_reused_before_abort'] = True
        except ValueError:
            witness['slot_reused_before_abort'] = False

    def generate(prepared):
        return tuple(old.Response(p.request.key, (0.0,)) for p in prepared)

    with pytest.raises(ValueError):
        model.execute(requests, generate, before_publish)
    assert witness == {'end_ack_while_batch_owned': False, 'slot_reused_before_abort': False}


@pytest.mark.parametrize('kind', ['duplicate', 'new_frontier'])
def test_b_d2_pop_must_retain_inflight_slot_ticket(kind):
    lease = old.Lease('server-1', 'slot0', 1, 'session0', 'ep0')
    request = old.Request(lease, 0)
    queue = old.BatchQueue(slots=1, batch=1)
    assert queue.add(request, 0, 1, size=2)
    assert queue.pop(0) == (request,)
    if kind == 'duplicate':
        assert queue.add(request, 0.01, 1, size=2) is False
    else:
        with pytest.raises(ValueError, match='one pending'):
            queue.add(replace(request, frontier=1, evidence=(1,)), 0.01, 1, size=2)
