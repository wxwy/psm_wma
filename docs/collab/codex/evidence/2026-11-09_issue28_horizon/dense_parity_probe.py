"""Same probe runs unchanged in two independent CPU processes/worktrees.

Actual CPU Local encoder/core; signed synthetic Visual96 and synthetic actions,
not Wan/DCP/diffusion numerical or hardware equivalence evidence.
"""
import hashlib
import json
import sys
from pathlib import Path

import torch
from cosmos_framework.inference.local_memory_state import CachedMemoryResponse
from cosmos_framework.inference.robocasa_local_memory_policy_test import _feature_adapter, _prepare_feature, _commit_feature_cold
from cosmos_framework.inference.robocasa_vae_protocol import canonical_json

torch.manual_seed(28)
torch.set_num_threads(1)
h, adapter, model = _feature_adapter()
_commit_feature_cold(adapter, h)
results = []
def tensor_digest(value):
    return hashlib.sha256(value.detach().cpu().contiguous().numpy().tobytes()).hexdigest()
for start in (0,16):
    rows = h.rows(start)
    update = _prepare_feature(adapter,h,start+16,rows)
    prefix = adapter.prefixes(update)[0]
    flat = prefix.detach().reshape(-1)
    matrix = torch.arange(flat.numel()*15,dtype=flat.dtype).reshape(flat.numel(),15)/100
    synthetic_action = flat @ matrix
    adapter.stage_boundary(update,h.boundary(start+16))
    results.append(dict(source_steps=list(update.visual_replacement.last_source_steps),
        feature_wire_sha256=hashlib.sha256(canonical_json(rows)).hexdigest(),
        cached_boundary_sha256=hashlib.sha256(canonical_json(h.boundary(start).record())).hexdigest(),
        fast_state_sha256=[tensor_digest(t) for t in update.memory.replacement.state],
        prefix_sha256=tensor_digest(prefix), synthetic_action_sha256=tensor_digest(synthetic_action),
        adapted_steps=adapter.status(update)['adapted_steps'], encoded_steps=adapter.status(update)['encoded_steps']))
    adapter.commit(update,CachedMemoryResponse(f'request-{start+16}','f'*64,b'{}'))
    h.commit_chunk(start+16)
Path(sys.argv[1]).write_text(json.dumps(dict(rows=results,scan_calls=model.scan_calls),indent=2)+'\n')
