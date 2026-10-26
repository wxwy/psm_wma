import os,subprocess,sys,types
from pathlib import Path
import pytest
child=Path('/workspace/psm_wma/cosmos-framework')
sys.path[:0]=[str(child),str(child.parent/'scripts'),str(child.parent/'tools/v3')]
os.chdir(child)
import examples
name='examples.psm_wma_robocasa_corrected_phase5'
module=types.ModuleType(name)
module.__file__=str(child/'examples/psm_wma_robocasa_corrected_phase5.py')
sys.modules[name]=module
setattr(examples,'psm_wma_robocasa_corrected_phase5',module)
original=subprocess.check_output(['git','show','923d9c3fd392e6bafbdb1771a292c7b313e6b3dc:examples/psm_wma_robocasa_corrected_phase5.py'],cwd=child)
exec(compile(original,module.__file__,'exec'),module.__dict__)
raise SystemExit(pytest.main(['--noconftest','-c','/dev/null','-p','no:cacheprovider','-q',
 'cosmos_framework/trainer/matched_no_ttt_test.py::test_world4_ga4_four_rank_packed_consumer_budget_and_frontier',
 'examples/psm_wma_robocasa_matched_no_ttt_test.py::test_g1_owner_override_cannot_enable_no_ttt',
 'examples/psm_wma_robocasa_g1_cross_pair_resume_test.py::test_launcher_explicit_flag_only_reaches_named_resume_without_running_torch',
 '--junitxml=/tmp/psm-v3-nottt-mp-20261026/baseline_red.xml']))
