"""Expected-red upstream v1.5.2 contracts; explicitly invoked, not an auto-test filename."""
import ast
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock

ROOT = Path(os.environ['PSM_ROOT_WORKTREE'])
sys.path.insert(0,str(ROOT/'tools/v3'))
from robocasa_vendor_test import lifecycle_classes

BASE='824ac14cefcfb7ec125fe5eb2e0bad7364466154'
CACHE=os.environ['PSM_ROBOSUITE_CACHE']

def source(path):
    return subprocess.check_output(['git','-C',CACHE,'show',BASE+':'+path],text=True)

def chain(tmp_path):
    for file in ('base.py','robot_env.py','manipulation/manipulation_env.py'):
        p=tmp_path/'robosuite/robosuite/environments'/file;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(source('robosuite/environments/'+file))
    return lifecycle_classes(tmp_path)

def test_legacy_factory_should_construct_controller():
    node=next(n for n in ast.parse(source('robosuite/controllers/parts/controller_factory.py')).body if isinstance(n,ast.FunctionDef) and n.name=='mobile_base_controller_factory')
    scope={'mobile_base_controllers':SimpleNamespace(MobileBaseJointVelocityController=Mock(),LegacyMobileBaseJointVelocityController=Mock())}
    exec(compile(ast.Module(body=[node],type_ignores=[]),'upstream-factory','exec'),scope)
    assert scope['mobile_base_controller_factory']('JOINT_VELOCITY_LEGACY',{}) is not None

def test_deferred_constructor_should_reach_all_parent_layers(tmp_path):
    cls=chain(tmp_path)['ManipulationEnv'];obj=cls.__new__(cls)
    obj.__init__(robots='PandaOmron',load_model_on_init=False)

def test_destroy_before_sim_creation_should_be_safe(tmp_path):
    cls=chain(tmp_path)['MujocoEnv'];obj=cls.__new__(cls)
    obj._destroy_sim()

def test_task_should_accept_and_forward_physics_flags():
    tree=ast.parse(source('robosuite/models/tasks/task.py'))
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Task')
    init=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
    wrapper=ast.ClassDef(name='Task',bases=[ast.Name(id='World',ctx=ast.Load())],keywords=[],body=[init],decorator_list=[])
    scope={'World':type('World',(),{})}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[wrapper],type_ignores=[])),'upstream-task','exec'),scope)
    scope['Task'](mujoco_arena=None,mujoco_robots=[],enable_multiccd=True,enable_sleeping_islands=False)
