"""Expected-red canonical compatibility on the actual first committed B source."""
from pathlib import Path
import importlib.util
import json

def test_unicode_bytes_must_match_existing_identity_contract():
    spec=importlib.util.spec_from_file_location('vendor_r1',Path(__file__).with_name('vendor_source_r1.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    value={'path':'厨房/评测输出'}
    expected=json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
    assert module.canonical(value)==expected
