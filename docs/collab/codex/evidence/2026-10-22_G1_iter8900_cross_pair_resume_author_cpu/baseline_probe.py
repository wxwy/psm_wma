import importlib.util,sys
from pathlib import Path
import pytest
child=Path('/workspace/psm_wma/cosmos-framework');sys.path.insert(0,str(child))
from examples import psm_wma_robocasa_corrected_phase5 as current
import examples
spec=importlib.util.spec_from_file_location('g1_before',Path(__file__).with_name('phase5_before.py'))
old=importlib.util.module_from_spec(spec);sys.modules[spec.name]=old;spec.loader.exec_module(old)
for name in vars(current):
 if name.startswith('G1_'):setattr(old,name,getattr(current,name))
sys.modules['examples.psm_wma_robocasa_corrected_phase5']=old
examples.psm_wma_robocasa_corrected_phase5=old
if __name__=='__main__':raise SystemExit(pytest.main(sys.argv[1:]))
