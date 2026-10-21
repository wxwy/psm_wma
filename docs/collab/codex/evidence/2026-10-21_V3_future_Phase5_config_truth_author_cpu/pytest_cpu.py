"""Author-only minimal CPU bootstrap; bypass unrelated eager dataset registrations."""
import sys
from pathlib import Path
from types import ModuleType
import pytest
child=Path('/workspace/psm_wma/cosmos-framework')
sys.path.insert(0,str(child))
name='cosmos_framework.data.generator.action.datasets'
package=ModuleType(name)
package.__path__=[str(child/'cosmos_framework/data/generator/action/datasets')]
package.__package__=name
sys.modules[name]=package
if __name__ == '__main__':
    raise SystemExit(pytest.main(sys.argv[1:]))
