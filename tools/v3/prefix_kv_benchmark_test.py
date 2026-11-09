"""Real CPU Local scan checks for the model-only GPU benchmark's input setup."""

from types import MethodType, SimpleNamespace

import torch
from cosmos_framework.model.generator.mot.cosmos3_vfm_network import Cosmos3VFMNetwork
from cosmos_framework.model.generator.mot.memory_prefix import LocalMemoryRuntime

from tools.v3.benchmark_local_ttt_prefix_kv import PrefixProjectionCounter, fixed_history_prefix


def _model():
    runtime = LocalMemoryRuntime().requires_grad_(False)
    net = SimpleNamespace(config=SimpleNamespace(local_memory_enabled=True), local_memory_runtime=runtime)
    net.scan_local_memory = MethodType(Cosmos3VFMNetwork.scan_local_memory, net)
    return SimpleNamespace(net=net)


def test_benchmark_prefix_uses_real_fresh_scan_after_global_no_grad():
    torch.manual_seed(31)
    model = _model()
    before = {name: parameter.detach().clone() for name, parameter in model.net.local_memory_runtime.named_parameters()}
    with torch.no_grad():
        prefix, state, visual, actions = fixed_history_prefix(model)
        assert not torch.is_grad_enabled()
    assert prefix.shape == (4, 32) and not prefix.requires_grad and not prefix.is_inference()
    assert visual.shape == (1, 16, 96) and actions.shape == (1, 16, 15)
    assert len(state) == 4 and all(torch.isfinite(t).all() for t in (*state, prefix))
    assert len(model.net.local_memory_runtime.core._telemetry["inner_loss"]) == 16
    for name, parameter in model.net.local_memory_runtime.named_parameters():
        torch.testing.assert_close(before[name], parameter, rtol=0, atol=0)


def test_benchmark_repeated_input_seed_reproduces_prefix_and_fast_state():
    torch.manual_seed(31)
    model = _model()
    torch.manual_seed(32)
    left = fixed_history_prefix(model)
    torch.manual_seed(32)
    right = fixed_history_prefix(model)
    for x, y in zip((left[0], *left[1], *left[2:]), (right[0], *right[1], *right[2:]), strict=True):
        torch.testing.assert_close(x, y, rtol=0, atol=0)


def test_projection_audit_count_does_not_recompile_when_counter_advances():
    """The former Python integer hook exhausted the real limit of eight."""
    counter = PrefixProjectionCounter(4, "cpu")
    net = torch.nn.Linear(8, 8)
    handle = net.register_forward_pre_hook(counter)
    graphs = []

    def backend(graph, inputs):
        graphs.append(graph)
        return graph.forward

    compiled = torch.compile(net, backend=backend, fullgraph=True, dynamic=False)
    with torch.no_grad(), torch._dynamo.config.patch(recompile_limit=8):
        for _ in range(20):
            compiled(torch.ones(4, 8))
            compiled(torch.ones(8, 8))
        assert counter.count.item() == 20
        assert len(graphs) == 2
        counter.count.zero_()
        compiled(torch.ones(4, 8))
        assert counter.count.item() == 1 and len(graphs) == 2
    handle.remove()
