"""Direct-episode filter probe using the exact formal function AST."""
import ast
import json
import subprocess
import tempfile
from pathlib import Path

from g2.offline.output_profile import OutputProfile
from g2.offline.stage_a import package_stage_a
from g2.tests.test_stage_a_package import stage_case


def main():
    text=subprocess.check_output(['git','show','29e4623e1875a2363a46ce210e2543aa1e08bffb:g2/latent_cache/batch_engine.py'],text=True)
    node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='discover_published')
    scope={'Path':Path,'__name__':'g2.latent_cache.formal29_probe','__package__':'g2.latent_cache'}
    exec(compile(ast.Module(body=[node],type_ignores=[]),'<formal29-discover>','exec'),scope)
    with tempfile.TemporaryDirectory(prefix='issue68-peer-filter-') as d:
        base=Path(d)
        kwargs,_=stage_case(base/'fixture',OutputProfile(selection_top_variant='clean',view_vae=False))
        root=base/'episode'
        package_stage_a(destination=root,compress_source=True,**kwargs)
        results={key:[p.name for p in scope['discover_published'](root,**selectors)] for key,selectors in [('wrong_task',dict(tasks=['DifferentTask'])),('wrong_episode',dict(episodes=[999]))]}
    Path(__file__).with_name('scope_observed.json').write_text(json.dumps(results,sort_keys=True,indent=2)+'\n')
    print(json.dumps(results,sort_keys=True))


if __name__=='__main__':main()
