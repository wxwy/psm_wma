"""PR53 R1 reviewer regression using the exact fixed Child package layout.

This imports only the real env_parsers namespace package, never its credential
modules, Torch, Wan, weights, or a GPU. The guard itself is unmodified candidate
code. Like the prior probes, reproduce with sibling source/ and evidence/ dirs.
"""

import json
import os
from pathlib import Path
import subprocess
import sys


SOURCE = Path(__file__).resolve().parents[1] / "source"


def test_selected_child_native_namespace_must_be_accepted():
    script = r'''
import importlib, json, pathlib, sys
from g2.latent_cache.encoding import _check_cosmos_origins
root = pathlib.Path(sys.argv[1])
expected = root / "cosmos_framework/utils/env_parsers"
assert expected.is_dir()
assert not (expected / "__init__.py").exists()
assert sorted(p.name for p in expected.iterdir()) == [
    "cred_env_parser.py", "customization_env_parser.py",
    "env_parser.py", "inference_env_parser.py",
]
sys.path.insert(0, str(root))
package = importlib.import_module("cosmos_framework.utils.env_parsers")
paths = list(package.__path__)
locations = list(package.__spec__.submodule_search_locations)
assert paths == locations == [str(expected)]
observed = {
    "package": package.__name__,
    "spec_origin": package.__spec__.origin,
    "file": getattr(package, "__file__", None),
    "loader": type(package.__loader__).__name__,
    "package_paths": paths,
    "spec_search_locations": locations,
    "all_paths_in_selected_child": paths == [str(expected)],
}
try:
    _check_cosmos_origins(root)
except RuntimeError as exc:
    observed.update(accepted=False, error=str(exc),
                    cause=type(exc.__cause__).__name__)
else:
    observed["accepted"] = True
observed["torch_loaded"] = "torch" in sys.modules
observed["wan_loaded"] = any("wan2pt2" in name for name in sys.modules)
print(json.dumps(observed))
'''
    result = subprocess.run(
        [sys.executable, "-c", script, str(SOURCE / "cosmos-framework")],
        cwd=SOURCE,
        env=dict(
            os.environ,
            CUDA_VISIBLE_DEVICES="",
            PYTHONDONTWRITEBYTECODE="1",
            PYTHONPATH=str(SOURCE),
        ),
        check=True,
        capture_output=True,
        text=True,
    )
    observed = json.loads(result.stdout)
    (Path(__file__).parent / "native_namespace_observed.json").write_text(
        json.dumps(observed, indent=2) + "\n"
    )
    assert observed["all_paths_in_selected_child"], observed
    assert not observed["torch_loaded"] and not observed["wan_loaded"], observed
    assert observed["accepted"], observed
