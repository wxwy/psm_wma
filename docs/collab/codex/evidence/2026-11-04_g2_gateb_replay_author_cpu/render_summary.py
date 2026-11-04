import json
import time
from pathlib import Path

import mujoco
from OpenGL import GL

from tools.g2.test_replay_render_visibility import software_scene

rows={}
driver=None
for case in ['plane','tilted_plane','transparent','inward','compound']:
    with software_scene(case) as sim:
        if driver is None:
            driver={name:GL.glGetString(token).decode() for name,token in (
                ('vendor',GL.GL_VENDOR),('renderer',GL.GL_RENDERER),('version',GL.GL_VERSION))}
        start=time.perf_counter()
        result=sim.check()
        rows[case]=dict(wall_s=time.perf_counter()-start,**result)
        assert result['status']=='PASS' and result['matching_geom_samples']>=16
assert 'llvmpipe' in driver['renderer'].lower()
report=dict(native_cpu_osmesa=True,mujoco_version=mujoco.__version__,
    gpu_or_server_data_used=False,driver=driver,cases=rows)
Path('/tmp/psm-g2-gateb-replay-20261104/native_render_summary.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(driver=driver,cases={k:dict(status=v['status'],
    matching=v['matching_geom_samples'],max_error_m=v['max_abs_z_error_m'],
    wall_s=v['wall_s']) for k,v in rows.items()}),indent=2))
