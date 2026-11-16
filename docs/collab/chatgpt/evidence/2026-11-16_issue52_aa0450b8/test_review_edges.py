"""Independent PR53 edge probes; no model weights, GPU, or production writes.

These tests express expected rejection and are deliberately RED on aa0450b8.
They are reviewer evidence, not changes to the candidate's test suite.
"""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys


SOURCE = Path(__file__).resolve().parents[1] / "source"


def test_foreign_cosmos_parent_must_be_rejected(tmp_path):
    # Use the real importer and its unchanged five-file binding inventory.
    # Only the temporary module bodies are synthetic; no Wan is instantiated.
    script = r'''
import importlib, json, pathlib, sys
from g2.latent_cache import encoding as e
root = pathlib.Path(sys.argv[1])
old, selected = root / 'old', root / 'selected'
for base, label in ((old, 'OLD_CHECKOUT'), (selected, 'SELECTED_CHECKOUT')):
    for parent in ('cosmos_framework', 'cosmos_framework/model',
                   'cosmos_framework/model/generator',
                   'cosmos_framework/model/generator/mot',
                   'cosmos_framework/model/generator/tokenizers',
                   'cosmos_framework/utils'):
        directory = base / parent
        directory.mkdir(parents=True, exist_ok=True)
        (directory / '__init__.py').write_text('')
    (base / 'cosmos_framework/utils/helper.py').write_text('SOURCE=' + repr(label) + '\n')
for relative in e._SOURCE_FILES:
    (selected / relative).write_text('# synthetic source, no model\n')
relative = 'cosmos_framework/model/generator/vision_encoder.py'
(selected / relative).write_text('from cosmos_framework.utils.helper import SOURCE\n')
weights = selected / 'identity_only.weights'
weights.write_bytes(b'CPU identity fixture, not model weights')
sys.path.insert(0, str(old))
parent = importlib.import_module('cosmos_framework')
sys.path.pop(0)
encoder = e.WanSingleFrameEncoder(weights, device='cpu', cosmos_root=selected)
encoder.descriptor()
name = 'cosmos_framework.model.generator.vision_encoder'
try:
    module = encoder._cosmos_module(name, relative)
except RuntimeError as exc:
    print(json.dumps({'rejected': True, 'error': str(exc)}))
else:
    print(json.dumps({'rejected': False,
                      'bound_leaf': module.__file__,
                      'parent_package': parent.__file__,
                      'helper_file': sys.modules['cosmos_framework.utils.helper'].__file__,
                      'helper_source': module.SOURCE,
                      'accepted_source_binding': name in e._IMPORTED_SOURCE}))
'''
    env = dict(os.environ, CUDA_VISIBLE_DEVICES="", PYTHONDONTWRITEBYTECODE="1")
    env["PYTHONPATH"] = str(SOURCE)
    result = subprocess.run(
        [sys.executable, "-c", script, str(tmp_path)],
        cwd=SOURCE, env=env, capture_output=True, text=True, check=True,
    )
    observed = json.loads(result.stdout)
    (Path(__file__).parent / "foreign_parent_observed.json").write_text(
        json.dumps(observed, indent=2) + "\n"
    )
    assert observed["rejected"], observed


def test_plan_must_reject_native_unsupported_canvas(tmp_path, capsys):
    from g2.latent_cache.encoding import _CONSTRUCTOR
    from g2.tests.test_view_vae_source import _fixture
    from tools.g2.build_spatial_view_vae_cache import main

    episode = tmp_path / "episode"
    _fixture(episode)
    weights = tmp_path / "identity_only.weights"
    weights.write_bytes(b'CPU planning fixture, not model weights')
    native_path = SOURCE / 'cosmos-framework/cosmos_framework/utils/generator/image_resize.py'
    spec = importlib.util.spec_from_file_location('pr53_native_resolution', native_path)
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    tier = native.get_vision_data_resolution((1024, 1024))
    assert tier == '768' and tier not in _CONSTRUCTOR['encode_chunk_frames']

    status = main([
        '--dataset-root', str(episode), '--weights', str(weights),
        '--device', 'cpu', '--dry-run', '--height', '1024', '--width', '1024',
    ])
    output = capsys.readouterr()
    observed = {
        'height': 1024, 'width': 1024, 'native_resolution_tier': tier,
        'constructor_tiers': list(_CONSTRUCTOR['encode_chunk_frames']),
        'cli_exit': status, 'cache_created': (episode / 'vae_cache').exists(),
        'plan_returned': status == 0,
    }
    if status == 0:
        observed['planned_canvas'] = json.loads(output.out)['results'][0]['recipe']['preprocessing']
    (Path(__file__).parent / 'unsupported_canvas_observed.json').write_text(
        json.dumps(observed, indent=2) + '\n'
    )
    assert status == 2, observed
