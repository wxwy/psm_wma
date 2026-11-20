"""Read the selected nav_sg MuJoCo serializer and compiled source identity."""

import hashlib
import importlib.util
import sys
from pathlib import Path

from g2.io import ContractError, digest


def load_oracle_source(nav_repo):
    source = Path(nav_repo).resolve(strict=True) / "g2/gt/mujoco_scene.py"
    if not source.is_file():
        raise ContractError("nav_sg native GT source unavailable")
    name = "_g2_atomic_native_oracle_source"
    spec = importlib.util.spec_from_file_location(name, source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def native_build_source_sha256(nav_checkout):
    """Match the source inventory hashed by the native Catkin build."""
    mapping = Path(nav_checkout) / "mapping_8_3" / "mapping"
    sources = sorted(
        (*mapping.glob("include/**/*.h"), *mapping.glob("src/**/*.cpp")), key=str
    )
    if not sources:
        raise ContractError("selected nav_sg native source files are unavailable")
    inventory = "".join(
        f"{file.relative_to(mapping)}:{digest(file)}\n" for file in sources
    )
    return hashlib.sha256(inventory.encode()).hexdigest()
