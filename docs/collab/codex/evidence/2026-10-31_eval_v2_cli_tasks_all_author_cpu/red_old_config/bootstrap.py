import importlib.util,sys,robocasa_eval_v2,pytest
spec=importlib.util.spec_from_file_location("robocasa_eval_v2.config",'/tmp/psm-eval-tasks-all-20261031/final/red_old_config/config.py')
module=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=module
spec.loader.exec_module(module)
robocasa_eval_v2.config=module
raise SystemExit(pytest.main(sys.argv[1:]))
