"""CPU-only check of compile_fx observer dispatch, no project/model imports."""
import functools
import json

import torch
from torch._inductor.compile_fx import compile_fx


def check(use_wraps):
    torch._dynamo.reset()
    record = dict(use_wraps=use_wraps, calls=0)

    def backend(graph, example):
        output = next(n for n in graph.graph.nodes if n.op == "output")
        original = output.args[0]
        first_input = next(n for n in graph.graph.nodes if n.op == "placeholder")
        output.args = (tuple(original) + (first_input,),)
        graph.recompile()
        compiled = compile_fx(graph, example)
        record["native_metadata_keys"] = sorted(compiled.__dict__)

        def observed(*args, **kwargs):
            record["calls"] += 1
            values = compiled(*args, **kwargs)
            assert len(values) == len(original) + 1
            return values[: len(original)]

        if use_wraps:
            observed = functools.wraps(compiled)(observed)
        elif hasattr(compiled, "_boxed_call"):
            observed._boxed_call = compiled._boxed_call
        return observed

    def function(x):
        return x + x

    data = torch.arange(16, dtype=torch.float32)
    actual = torch.compile(function, backend=backend, fullgraph=True)(data)
    record["output_exact"] = torch.equal(actual, function(data))
    return record


if __name__ == "__main__":
    result = dict(torch=torch.__version__, records=[check(True), check(False)])
    with open("observer_cpu01.json", "x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps(result))
