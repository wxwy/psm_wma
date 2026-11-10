"""CPU tests for a diagnostic wrapper; no model/checkpoint or CUDA context."""

import gc
import io
import json
from pathlib import Path
import random
import sys
import types

import pytest
import torch

import latency_probe as probe


class Cuda:
    def __init__(self, *, initialized=True, ready=True):
        self.initialized, self.ready = initialized, ready
        self.recorded, self.events, self.queries = [], [], 0

    def is_initialized(self):
        return self.initialized

    def current_stream(self, device):
        assert self.initialized
        return ("unchanged_stream", device)

    def memory_stats(self, device):
        assert self.initialized
        return {"num_alloc_retries": 0, "allocated_bytes.all.current": 128}

    def Event(self, *, enable_timing):
        assert enable_timing and self.initialized
        parent = self

        class Event:
            def record(self, stream):
                parent.recorded.append(stream)

            def query(self):
                parent.queries += 1
                return parent.ready

            def elapsed_time(self, end):
                assert parent.ready
                return 1.25

        event = Event()
        self.events.append(event)
        return event

    def synchronize(self, *args, **kwargs):
        pytest.fail("observer must not add CUDA synchronization")


def rows(stream):
    return [json.loads(line) for line in stream.getvalue().splitlines()]


def model_for(fn):
    return type("Model", (), {probe.METHOD: fn})


def observe(model, stream=None, cuda=None, **kwargs):
    stream = io.StringIO() if stream is None else stream
    cuda = Cuda() if cuda is None else cuda
    return probe.GenerationProbe(model, types.SimpleNamespace(cuda=cuda), stream, **kwargs), stream, cuda


def test_same_inputs_outputs_rng_grad_and_single_native_call():
    calls, received = [], object()

    def native(self, arg, **kwargs):
        assert arg is received and kwargs["opaque"] is received
        calls.append((torch.is_grad_enabled(), torch.randn(5), random.random()))
        return received

    model = model_for(native)
    torch.manual_seed(42)
    random.seed(42)
    model().generate_samples_from_batch(received, opaque=received)
    expected, expected_rng, expected_python_rng = calls.pop(), torch.get_rng_state(), random.getstate()
    torch.manual_seed(42)
    random.seed(42)
    observer, stream, cuda = observe(model)
    with observer:
        assert model().generate_samples_from_batch(received, opaque=received) is received
    actual = calls.pop()
    assert len(calls) == 0 and expected[0] == actual[0] and torch.equal(expected[1], actual[1])
    assert expected[2] == actual[2] and torch.equal(expected_rng, torch.get_rng_state())
    assert expected_python_rng == random.getstate()
    assert len(cuda.events) == 2 and len(cuda.recorded) == 2
    assert [r["cuda_event_ms"] for r in rows(stream) if r["type"] == "cuda_span"] == [1.25]


@pytest.mark.parametrize("error", [RuntimeError("native"), SystemExit(7), KeyboardInterrupt()])
def test_preserves_original_exception_and_restores_method_gc(error):
    def native(self):
        raise error

    model = model_for(native)
    original, callbacks = getattr(model, probe.METHOD), gc.callbacks[:]
    observer, stream, _ = observe(model)
    with pytest.raises(type(error)) as caught:
        with observer:
            model().generate_samples_from_batch()
    assert caught.value is error
    assert getattr(model, probe.METHOD) is original and gc.callbacks == callbacks
    assert next(r for r in rows(stream) if r["type"] == "generation")["outcome"] == "raised"


def test_no_cuda_context_created_and_no_output_inspection():
    class Opaque:
        def __iter__(self):
            pytest.fail("output inspected")

        def __repr__(self):
            pytest.fail("output inspected")

    output = Opaque()
    model = model_for(lambda self: output)
    observer, stream, cuda = observe(model, cuda=Cuda(initialized=False))
    with observer:
        assert model().generate_samples_from_batch() is output
    assert not cuda.events and not cuda.recorded
    row = next(r for r in rows(stream) if r["type"] == "generation")
    assert row["cuda_before"] is None and row["cuda_after"] is None


def test_pending_cuda_never_synchronizes_or_discards_host_samples():
    model = model_for(lambda self: "ok")
    observer, stream, cuda = observe(model, cuda=Cuda(ready=False))
    with observer:
        assert model().generate_samples_from_batch() == "ok"
    data = rows(stream)
    assert len([r for r in data if r["type"] == "generation"]) == 1
    assert next(r for r in data if r["type"] == "cuda_span_unavailable")["reason"] == "not_ready_no_added_sync"
    assert not observer.pending and cuda.queries > 0


def test_async_completed_events_join_correct_request_without_extra_call():
    model = model_for(lambda self: 12)
    observer, stream, cuda = observe(model, cuda=Cuda(ready=False))
    with observer:
        assert model().generate_samples_from_batch() == 12
        cuda.ready = True
        assert model().generate_samples_from_batch() == 12
    assert [r["call"] for r in rows(stream) if r["type"] == "cuda_span"] == [1, 2]
    assert observer.calls == 2 and not observer.errors


def test_observer_errors_cannot_mask_native_result_or_failure():
    cuda = Cuda()
    cuda.memory_stats = lambda device: (_ for _ in ()).throw(OSError("unavailable"))
    model = model_for(lambda self: "native")
    observer, _, _ = observe(model, cuda=cuda)
    with observer:
        assert model().generate_samples_from_batch() == "native"
    assert {e["operation"] for e in observer.errors} == {"cuda_before", "cuda_after"}


def test_write_error_does_not_mask_original_exception():
    error = ValueError("original")

    class Broken(io.StringIO):
        def write(self, text):
            raise OSError("disk full")

    def native(self):
        raise error

    model = model_for(native)
    observer, _, _ = observe(model, stream=Broken())
    with pytest.raises(ValueError) as caught:
        with observer:
            model().generate_samples_from_batch()
    assert caught.value is error and any(e["operation"] == "write" for e in observer.errors)


def test_preserves_gc_settings_other_callbacks_and_records_native_gc():
    model = model_for(lambda self: gc.collect())
    original_callbacks, settings = gc.callbacks[:], (gc.isenabled(), gc.get_threshold())
    observer, stream, _ = observe(model)
    with observer:
        model().generate_samples_from_batch()
    assert gc.callbacks == original_callbacks and (gc.isenabled(), gc.get_threshold()) == settings
    row = next(r for r in rows(stream) if r["type"] == "generation")
    assert row["gc"] and all(g["start_ns"] <= g["end_ns"] for g in row["gc"])


def test_inherited_method_is_restored_without_adding_attribute():
    parent = model_for(lambda self: "inherited")
    child = type("Subclass", (parent,), {})
    observer, _, _ = observe(child)
    with observer:
        assert child().generate_samples_from_batch() == "inherited"
    assert probe.METHOD not in child.__dict__ and not observer.errors


def test_runner_replacing_method_is_not_overwritten():
    model = model_for(lambda self: 1)
    replacement = lambda self: 2
    observer, _, _ = observe(model)
    with observer:
        setattr(model, probe.METHOD, replacement)
    assert getattr(model, probe.METHOD) is replacement
    assert any(e["operation"] == "method_replaced_by_runner" for e in observer.errors)


def test_host_control_does_not_create_cuda_events_or_change_flags():
    model = model_for(lambda self, **kwargs: kwargs)
    observer, stream, cuda = observe(model, cuda_events=False)
    with observer:
        for enabled in (False, True):
            assert model().generate_samples_from_batch(use_prefix_projection_cache=enabled) == {
                "use_prefix_projection_cache": enabled
            }
    flags = [r["cache_flags"]["use_prefix_projection_cache"] for r in rows(stream) if r["type"] == "generation"]
    assert flags == [False, True] and not cuda.events


def test_compile_counts_read_only_without_importing_compiler(monkeypatch):
    monkeypatch.delitem(sys.modules, "torch._dynamo.utils", raising=False)
    assert probe.compile_counts(torch) is None
    counters = {"stats": {"unique_graphs": 8}}
    monkeypatch.setitem(sys.modules, "torch._dynamo.utils", types.SimpleNamespace(counters=counters))
    result = probe.compile_counts(torch)
    assert result == counters and result is not counters and counters == {"stats": {"unique_graphs": 8}}


def test_pending_buffer_bound_keeps_every_generation():
    model = model_for(lambda self: None)
    observer, stream, _ = observe(model, cuda=Cuda(ready=False))
    with observer:
        for _ in range(258):
            model().generate_samples_from_batch()
        assert len(observer.pending) <= 256
    assert len([r for r in rows(stream) if r["type"] == "generation"]) == 258
    assert any(e["operation"] == "pending_limit" for e in observer.errors)


@pytest.fixture
def native_runner(tmp_path, monkeypatch):
    root = tmp_path / "formal"
    root.mkdir()
    runner = tmp_path / "existing_k16.py"
    out = tmp_path / "out"
    identity = dict(
        root=probe.FORMAL_ROOT, child=probe.FORMAL_CHILD, gitlink=probe.FORMAL_CHILD, root_status="", child_status=""
    )
    monkeypatch.setattr(probe, "source_identity", lambda root: identity.copy())
    native_calls = []
    model = model_for(lambda self, *args, **kwargs: native_calls.append((args, kwargs)))
    module = types.ModuleType("cosmos_framework.model.generator.omni_mot_model")
    module.OmniMoTModel = model
    monkeypatch.setitem(sys.modules, module.__name__, module)
    monkeypatch.setitem(sys.modules, "torch", types.SimpleNamespace(cuda=Cuda()))
    args = ["--root", str(root), "--runner", str(runner), "--out", str(out), "--", "--k16-source64"]
    return types.SimpleNamespace(
        root=root, runner=runner, out=out, identity=identity, model=model, calls=native_calls, args=args
    )


def test_existing_runner_and_argv_reused_without_extra_generation(native_runner):
    f = native_runner
    f.runner.write_text("""from cosmos_framework.model.generator.omni_mot_model import OmniMoTModel
import sys
assert sys.argv[1:] == ["--k16-source64"]
for enabled in (False, True):
    OmniMoTModel().generate_samples_from_batch("original_input", use_prefix_projection_cache=enabled)
raise SystemExit(0)
""")
    original_argv, cwd, path = sys.argv, Path.cwd(), sys.path[:]
    assert probe.main(f.args) == 0
    assert sys.argv is original_argv and Path.cwd() == cwd and sys.path == path
    assert len(f.calls) == 2
    metadata = json.loads((f.out / "metadata.json").read_text())
    assert metadata["status"] == "RECORDED" and metadata["source_unchanged"] and metadata["runner_unchanged"]


def test_native_runner_exception_retained_with_cleanup(native_runner):
    f = native_runner
    f.runner.write_text(
        'from cosmos_framework.model.generator.omni_mot_model import OmniMoTModel\nOmniMoTModel().generate_samples_from_batch()\nraise RuntimeError("native runner")\n'
    )
    original, callbacks, argv, cwd = getattr(f.model, probe.METHOD), gc.callbacks[:], sys.argv, Path.cwd()
    with pytest.raises(RuntimeError, match="native runner"):
        probe.main(f.args)
    assert getattr(f.model, probe.METHOD) is original and gc.callbacks == callbacks
    assert sys.argv is argv and Path.cwd() == cwd
    assert json.loads((f.out / "metadata.json").read_text())["status"] == "RUNNER_RAISED"


@pytest.mark.parametrize(
    "field,value",
    [
        ("root", "wrong"),
        ("child", "wrong"),
        ("gitlink", "wrong"),
        ("root_status", " M script.py"),
        ("child_status", " M model.py"),
    ],
)
def test_identity_rejection_precedes_runner_and_output_creation(native_runner, field, value):
    f = native_runner
    f.identity[field] = value
    f.runner.write_text('raise AssertionError("must never start")')
    with pytest.raises(ValueError, match="exact clean"):
        probe.main(f.args)
    assert not f.out.exists() and not f.calls


def test_no_calls_or_source_change_cannot_be_reported_recorded(native_runner, monkeypatch):
    f = native_runner
    f.runner.write_text("pass\n")
    assert probe.main(f.args) == 2
    assert json.loads((f.out / "metadata.json").read_text())["status"] == "DIAGNOSTIC_INCOMPLETE"


def test_input_runner_modification_is_detected(native_runner):
    f = native_runner
    f.runner.write_text('from pathlib import Path\nPath(__file__).write_text("changed")\n')
    assert probe.main(f.args) == 2
    assert json.loads((f.out / "metadata.json").read_text())["status"] == "SOURCE_CHANGED"


def test_new_output_directory_is_required(native_runner):
    f = native_runner
    f.runner.write_text("pass\n")
    f.out.mkdir()
    with pytest.raises(FileExistsError):
        probe.main(f.args)
    assert not list(f.out.iterdir())


def test_post_run_source_change_and_nonzero_exit_are_preserved(native_runner, monkeypatch):
    f = native_runner
    f.runner.write_text("raise SystemExit(23)\n")
    count = []

    def identity(root):
        result = f.identity.copy()
        if count:
            result["child_status"] = " M actual_source.py"
        count.append(1)
        return result

    monkeypatch.setattr(probe, "source_identity", identity)
    with pytest.raises(SystemExit) as caught:
        probe.main(f.args)
    assert caught.value.code == 23
    assert json.loads((f.out / "metadata.json").read_text())["status"] == "SOURCE_CHECK_FAILED"
