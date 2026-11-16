"""Namespace provenance regressions without loading Wan, weights or Torch."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CHILD = ROOT / "cosmos-framework"


def _run(code, *arguments):
    result = subprocess.run(
        [sys.executable, "-c", code, *map(str, arguments)],
        cwd=ROOT,
        env=dict(
            os.environ,
            CUDA_VISIBLE_DEVICES="",
            PYTHONDONTWRITEBYTECODE="1",
            PYTHONPATH=str(ROOT),
        ),
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_real_selected_child_namespace_is_accepted_without_model_imports():
    observed = _run(
        """
import importlib,json,pathlib,sys
from importlib.machinery import NamespaceLoader
from g2.latent_cache.encoding import _check_cosmos_origins
root=pathlib.Path(sys.argv[1])
expected=root/'cosmos_framework/utils/env_parsers'
assert expected.is_dir() and not (expected/'__init__.py').exists()
sys.path.insert(0,str(root))
package=importlib.import_module('cosmos_framework.utils.env_parsers')
assert isinstance(package.__loader__,NamespaceLoader)
assert package.__spec__.loader is package.__loader__
assert package.__spec__.origin is None and package.__file__ is None
assert list(package.__path__)==list(package.__spec__.submodule_search_locations)==[str(expected)]
_check_cosmos_origins(root)
assert 'torch' not in sys.modules
assert not any('wan2pt2' in key for key in sys.modules)
print(json.dumps({'accepted':True,'loader':type(package.__loader__).__name__}))
""",
        CHILD,
    )
    assert observed == {"accepted": True, "loader": "NamespaceLoader"}


@pytest.fixture
def namespace_roots(tmp_path):
    from g2.latent_cache.encoding import _SOURCE_FILES

    for name in ("selected", "foreign"):
        root = tmp_path / name
        for parent in (
            "cosmos_framework",
            "cosmos_framework/model",
            "cosmos_framework/model/generator",
            "cosmos_framework/model/generator/mot",
            "cosmos_framework/model/generator/tokenizers",
            "cosmos_framework/utils",
        ):
            path = root / parent
            path.mkdir(parents=True, exist_ok=True)
            (path / "__init__.py").write_text("")
        namespace = root / "cosmos_framework/utils/native_namespace"
        namespace.mkdir()
        (namespace / "marker.py").write_text("VALUE=" + repr(name) + "\n")
        for relative in _SOURCE_FILES:
            (root / relative).write_text("# CPU source identity fixture\n")
        (root / _SOURCE_FILES[0]).write_text(
            "from cosmos_framework.utils.native_namespace.marker import VALUE\n"
        )
        (root / "identity_only.weights").write_bytes(b"not real VAE weights")
    return tmp_path


@pytest.mark.parametrize("preload", [False, True])
def test_controlled_import_accepts_selected_namespace_before_and_after_import(
    namespace_roots, preload
):
    observed = _run(
        """
import importlib,json,pathlib,sys
from g2.latent_cache import encoding as e
root=pathlib.Path(sys.argv[1])/'selected'
if sys.argv[2]=='True':
 sys.path.insert(0,str(root))
 importlib.import_module('cosmos_framework.utils.native_namespace')
 sys.path.pop(0)
name='cosmos_framework.model.generator.vision_encoder'
relative=e._SOURCE_FILES[0]
first=e.WanSingleFrameEncoder(root/'identity_only.weights',device='cpu',cosmos_root=root)
first.descriptor()
module=first._cosmos_module(name,relative)
assert module.VALUE=='selected' and name in e._IMPORTED_SOURCE
second=e.WanSingleFrameEncoder(root/'identity_only.weights',device='cpu',cosmos_root=root)
second.descriptor()
assert second._cosmos_module(name,relative) is module
e._check_cosmos_origins(root)
assert 'torch' not in sys.modules
print(json.dumps({'accepted':True,'reused':True}))
""",
        namespace_roots,
        preload,
    )
    assert observed == {"accepted": True, "reused": True}


@pytest.mark.parametrize(
    "case",
    [
        "foreign_namespace",
        "mixed_namespace",
        "empty_paths",
        "foreign_module_path",
        "foreign_spec_path",
        "unknown_loader",
        "mismatched_loader",
        "namespace_has_file",
        "namespace_has_origin",
        "namespace_has_location",
        "ordinary_missing_origin",
        "ordinary_missing_file",
        "symlink_directory",
        "missing_directory",
        "namespace_became_regular_package",
    ],
)
def test_namespace_origin_guard_keeps_unverifiable_sources_rejected(
    namespace_roots, case
):
    observed = _run(
        """
import importlib,importlib.machinery,importlib.util,json,pathlib,sys
from g2.latent_cache import encoding as e
base=pathlib.Path(sys.argv[1]);case=sys.argv[2]
root=base/'selected';foreign=base/'foreign'
name='cosmos_framework.utils.native_namespace'
expected=root/'cosmos_framework/utils/native_namespace'
other=foreign/'cosmos_framework/utils/native_namespace'
sys.path.insert(0,str(root))
importlib.import_module('cosmos_framework.utils')
def namespace_from(paths):
 spec=importlib.machinery.PathFinder.find_spec(name,[str(p) for p in paths])
 assert spec is not None and spec.origin is None
 return importlib.util.module_from_spec(spec)
if case=='symlink_directory':
 actual=expected.with_name('namespace_actual')
 expected.rename(actual)
 expected.symlink_to(actual,target_is_directory=True)
if case in ('foreign_namespace','mixed_namespace'):
 paths=[other.parent] if case=='foreign_namespace' else [expected.parent,other.parent]
 package=namespace_from(paths)
 sys.modules[name]=package
else:
 package=importlib.import_module(name)
assert isinstance(package.__loader__,importlib.machinery.NamespaceLoader)
if case=='empty_paths':
 package.__path__=[];package.__spec__.submodule_search_locations=[]
elif case=='foreign_module_path':package.__path__=[str(expected),str(other)]
elif case=='foreign_spec_path':package.__spec__.submodule_search_locations=[str(expected),str(other)]
elif case=='unknown_loader':package.__loader__=package.__spec__.loader=object()
elif case=='mismatched_loader':package.__loader__=namespace_from([expected.parent]).__loader__
elif case=='namespace_has_file':package.__file__=str(expected/'marker.py')
elif case=='namespace_has_origin':package.__spec__.origin=str(expected/'marker.py')
elif case=='namespace_has_location':package.__spec__.has_location=True
elif case.startswith('ordinary_missing_'):
 marker=importlib.import_module(name+'.marker')
 if case=='ordinary_missing_origin':marker.__spec__.origin=None
 marker.__file__=None
elif case=='missing_directory':expected.rename(expected.with_name('removed_namespace'))
elif case=='namespace_became_regular_package':(expected/'__init__.py').write_text('')
try:e._check_cosmos_origins(root)
except RuntimeError:pass
else:raise AssertionError('unverifiable namespace/module accepted: '+case)
assert sys.modules[name] is package
assert not e._IMPORTED_SOURCE
assert 'torch' not in sys.modules
print(json.dumps({'rejected':True,'module_preserved':True}))
""",
        namespace_roots,
        case,
    )
    assert observed == {"rejected": True, "module_preserved": True}
