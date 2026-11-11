"""Opt-in GPU/CPU parity smoke; never collected in ordinary CPU pytest.

Run: MUJOCO_GL=egl python -m g2.tests.gpu_view_parity_smoke --output <new.json>
Real source-bundle parity remains a separate integration Gate.
"""

import argparse
import json
from pathlib import Path

import numpy as np

from g2.views.direct_color import close_gpu_renderers
from g2.views.render import AXES, rasterize


def run(output):
    output = Path(output)
    if output.exists():
        raise ValueError('refuse to overwrite parity evidence')
    vertices = np.array([[x, y, z] for z in (0., .04) for y in (0., .04) for x in (0., .04)])
    faces = np.array([[0, 2, 1], [1, 2, 3], [4, 5, 6], [5, 7, 6],
                      [0, 1, 4], [1, 5, 4], [2, 6, 3], [3, 6, 7],
                      [0, 4, 2], [2, 4, 6], [1, 3, 5], [3, 7, 5]])
    keys = np.array([[x, y, z] for x in range(4) for y in range(4) for z in range(4)])
    xyz = (keys + .5) * .01
    rgb = ((keys * [17, 31, 53] + [15, 25, 35]) % 256).astype(np.uint8)
    owners = np.zeros(len(xyz), np.int32)
    valid = np.ones(len(xyz), bool)
    valid[::7] = False
    owners[::11] = -1
    records = []
    try:
        for axis in AXES:
            args = (xyz, rgb, valid, owners, {0}, [-.01] * 3, [.05] * 3, axis)
            kw = dict(meters_per_pixel=.01, meshes=[(0, vertices, faces)],
                      surface_tolerance=.01, asset_fill_radius_m=.015)
            cpu = rasterize(*args, renderer_backend='cpu', **kw)
            gpu = rasterize(*args, renderer_backend='gpu', **kw)
            for i in (0, 1, 2, 4):
                np.testing.assert_array_equal(cpu[i], gpu[i])
            np.testing.assert_allclose(cpu[3], gpu[3], rtol=0, atol=1e-9, equal_nan=True)
            records.append({'axis': axis, 'rgb_mask_geometry_owner_exact': True,
                            'depth_max_error_m': float(np.nanmax(np.abs(cpu[3] - gpu[3]))),
                            'valid_color_pixels': int(gpu[1].sum())})
    finally:
        close_gpu_renderers()
    result = {'schema': 'g2_gpu_view_synthetic_parity_v1', 'passed': True,
              'source': 'TEST_ONLY_SYNTHETIC_CUBE_NOT_REAL_SCENE_ACCEPTANCE', 'views': records}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    print(json.dumps(run(parser.parse_args().output), sort_keys=True))
