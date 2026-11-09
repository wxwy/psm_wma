"""Issue31 single teacher-forced diagnostic; no Gate or speed verdict."""
import json
import sys
from pathlib import Path
import torch
from cosmos_framework.scripts.action_policy_server_robocasa import ActionModelService
from cosmos_framework.model.generator.mot import inference_text_kv_memory as cache
from cosmos_framework.model.generator.mot.memory_prefix import attach_local_prefixes
from tools.v3 import benchmark_local_ttt_prefix_kv as bench

out = Path(sys.argv[sys.argv.index("--output-dir") + 1])
saved = {}
source_before = bench.identity(Path(sys.argv[sys.argv.index("--root-worktree")+1]))
original_init = ActionModelService.__init__
original_prep = ActionModelService._prep_policy_item
original_fixed = bench.fixed_history_prefix

class Captured(Exception):
    pass

def service_init(self, *args, **kwargs):
    original_init(self, *args, **kwargs)
    saved["service"] = self

def prep_item(self, *args, **kwargs):
    result = original_prep(self, *args, **kwargs)
    saved["prep"] = result
    return result

def err(x, y):
    d = (x-y).abs()
    return dict(max_abs=float(d.max()), mean_abs=float(d.mean()),
                equal=bool(torch.equal(x,y)))

def diagnostic(model):
    prefix, fw, visual, executed = original_fixed(model)
    service = saved["service"]
    with torch.inference_mode():
        plans, clean, cond, _, noise, reference, mask, noisy_action = model._prepare_inference_data(
            service._single_policy_batch(saved["prep"]), [31], False)
        plans, clean = attach_local_prefixes(plans, clean, (prefix,), k_local=4, local_dim=32)
        fixed_noise = [torch.where(m.bool(), r, n) for n,r,m in zip(noise, reference, mask, strict=True)]
        nvision = clean.x0_tokens_vision[0].numel()
        ashape = clean.x0_tokens_action[0].shape
        def forward(memory, tau):
            torch.compiler.cudagraph_mark_step_begin()
            values = model._get_velocity(net=None, noise_x=[n.clone() for n in fixed_noise],
                timestep=torch.tensor([[float(tau)]], device=model.tensor_kwargs["device"]),
                text_tokens=cond, sequence_plans=plans, gen_data_clean=clean, skip_text_tokens=False,
                packed_sequence_template=None, memory=memory, has_noisy_actions=noisy_action)
            torch.cuda.synchronize()
            return values[0].detach().float().cpu().clone()
        rows = []
        old_state_init = cache.InferenceTextKVMemoryState.init
        def state_init(self, hidden, device):
            old_state_init(self, hidden, device)
            if not rows:
                ci, gi = hidden["_causal_indices"].cpu(), hidden["_full_indices"].cpu()
                rows.append(dict(und_real=int(hidden["_num_causal_tokens"]), gen_real=int(hidden["_num_full_tokens"]),
                    und_padded=hidden["causal_seq"].shape[0], gen_padded=hidden["full_only_seq"].shape[0],
                    und_first=bool(torch.equal(ci, torch.arange(ci.numel()))),
                    causal_indices=ci.tolist(), full_indices=gi.tolist(),
                    causal_offsets=hidden["_causal_seq_offsets"].cpu().tolist(),
                    gen_offsets=hidden["_full_only_seq_offsets"].cpu().tolist(),
                    sample_offsets=hidden["sample_offsets"].cpu().tolist()))
        cache.InferenceTextKVMemoryState.init = state_init
        a = model._make_inference_text_kv_cache()
        b = model._make_inference_text_kv_cache()
        previous = None
        try:
            outputs = {"original_1000":forward(None,1000)}
            previous = cache.install_inference_memory_attention_dispatch(model.net)
            outputs["fill_1000"] = forward(cache.InferenceTextKVMemoryState(a,local_prefix_length=4),1000)
            outputs["hit_1000"] = forward(cache.InferenceTextKVMemoryState(a,local_prefix_length=4),1000)
            outputs["fill_500"] = forward(cache.InferenceTextKVMemoryState(b,local_prefix_length=4),500)
            outputs["hit_500_from_1000"] = forward(cache.InferenceTextKVMemoryState(a,local_prefix_length=4),500)
            changes = [dict(layer=i,k=err(x.get()[0].cpu(),y.get()[0].cpu()),
                            v=err(x.get()[1].cpu(),y.get()[1].cpu())) for i,(x,y) in enumerate(zip(a,b,strict=True))]
            cache.restore_inference_attention_dispatch(previous)
            previous = None
            outputs["original_500"] = forward(None,500)
            compare = {}
            for x,y in (("original_1000","fill_1000"),("fill_1000","hit_1000"),
                        ("original_500","fill_500"),("fill_500","hit_500_from_1000")):
                left,right = outputs[x],outputs[y]
                compare[x+"_vs_"+y] = dict(vision=err(left[:nvision],right[:nvision]),
                    action=err(left[nvision:].reshape(ashape)[:,:15], right[nvision:].reshape(ashape)[:,:15]))
            source_after = bench.identity(Path(sys.argv[sys.argv.index("--root-worktree")+1]))
            assert source_after == source_before
            report = dict(status="DIAGNOSTIC_ONLY", root=source_after, source_before=source_before,
                          layout=rows, velocity_errors=compare, und_kv_timestep_changes=changes,
                          source_unchanged=True,recompile_limit=torch._dynamo.config.recompile_limit)
            torch.save(outputs,out/"teacher_forced_outputs.pt")
            (out/"diagnostic.json").write_text(json.dumps(report,indent=2)+"\n")
            public = dict(status=report["status"], layout={k:v for k,v in rows[0].items() if not k.endswith("indices")},
                          velocity_errors=compare,
                          max_und_k_change=max(r["k"]["max_abs"] for r in changes),
                          max_und_v_change=max(r["v"]["max_abs"] for r in changes),
                          changed_und_layers=[r["layer"] for r in changes if not r["k"]["equal"] or not r["v"]["equal"]])
            print(json.dumps(public,indent=2),flush=True)
        finally:
            if previous is not None:
                cache.restore_inference_attention_dispatch(previous)
            cache.InferenceTextKVMemoryState.init = old_state_init
            for branch in (a,b):
                for value in branch:
                    value.clear()
    raise Captured("DIAGNOSTIC_CAPTURED_NO_GATE_VERDICT")

ActionModelService.__init__ = service_init
ActionModelService._prep_policy_item = prep_item
bench.fixed_history_prefix = diagnostic
try:
    bench.main()
except Captured:
    pass

