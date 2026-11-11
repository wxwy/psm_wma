"""Explicit source-bound 10 mm color input for the accepted G2 View recipe.

The numerical raster, ownership, and view membership rules are the F13/F21
implementation. This adapter replaces the isolated scripts' process-global
``load_dense_surfaces`` monkeypatch and their fixed server paths. It does not
create Rooms, semantic identities, occupancy, or native source certificates.
"""

import math
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

from g2.io import ContractError, digest, new_output, write_json


def validate_surface_data(surface_data, snapshot):
    """Validate the producer's explicit arrays and scene/frame/owner binding."""
    if not isinstance(surface_data, (tuple, list)) or len(surface_data) != 5:
        raise ContractError('direct surface data must contain XYZ, RGB, validity, owners, evidence')
    xyz, rgb, valid, owners, evidence = surface_data
    if not isinstance(evidence, dict):
        raise ContractError('direct surface evidence is missing')
    for key in ('scene_id', 'source_sha256', 'frame_id', 'world_frame'):
        if key not in snapshot or evidence.get(key) != snapshot[key]:
            raise ContractError('direct surface source identity differs: ' + key)
    if type(evidence['frame_id']) is not int or evidence['frame_id'] < 0:
        raise ContractError('direct surface frame must be a nonnegative integer')
    entity_ids = sorted(e['id'] for e in snapshot['entities'])
    if evidence.get('entity_index_to_native_id') != entity_ids:
        raise ContractError('direct surface owner index differs from native entities')
    for key in ('voxel_leaf_m', 'dense_sample_spacing_m', 'dense_small_sample_spacing_m'):
        value = evidence.get(key)
        if type(value) not in (int, float) or not math.isfinite(value) or value != .01:
            raise ContractError('direct surface input requires the accepted 10 mm grid: ' + key)
    opaque = evidence.get("opaque_ray_owner_indices")
    if opaque is not None:
        if (snapshot.get("source_mode") != "full_map_mujoco_source"
                or evidence.get("opaque_ray_cert_schema") != "g2_verified_compiled_gt_opaque_owner_v1"
                or not isinstance(opaque, list) or len(opaque) > len(entity_ids)
                or any(type(i) is not int or i < 0 or i >= len(entity_ids) for i in opaque)
                or opaque != sorted(set(opaque))
                or any(snapshot["entities"][next(
                    j for j, row in enumerate(snapshot["entities"]) if row["id"] == entity_ids[i]
                )]["kind"] != "object" for i in opaque)):
            raise ContractError("invalid compiled source opaque ray recovery certificate")
    xyz = np.asarray(xyz)
    rgb = np.asarray(rgb)
    valid = np.asarray(valid)
    owners = np.asarray(owners)
    n = len(xyz) if xyz.ndim else 0
    if (not 0 < n <= 10_000_000 or xyz.shape != (n, 3) or
            xyz.dtype.kind not in 'iuf' or not np.isfinite(xyz).all() or
            rgb.shape != (n, 3) or rgb.dtype != np.uint8 or
            valid.shape != (n,) or valid.dtype != np.bool_ or
            owners.shape != (n,) or owners.dtype.kind not in 'iu'):
        raise ContractError('invalid direct surface arrays')
    if np.any(owners < -1) or np.any(owners >= len(entity_ids)):
        raise ContractError('direct surface owner index is out of range')
    return (np.asarray(xyz, dtype=np.float64), rgb, valid,
            np.asarray(owners, dtype=np.int32), dict(evidence))


def close_gpu_renderers():
    """Release only contexts already opened; CPU callers need no GL imports."""
    for name, close in (('g2.views.gpu_color_select', 'close_projector'),
                        ('g2.views.exact_compute', 'close_engine')):
        module = sys.modules.get(name)
        if module is not None:
            getattr(module, close)()


def export_white_views(rendered, rendered_root, output):
    """Export RGB PNGs with the F21 white background, retaining Room/Island IDs.

    One Room keeps F21's flat ``sixview/<axis>.png`` layout. Multiple Rooms
    use ``sixview/rooms/<uid>/<axis>.png``. Islands always remain separate
    under ``islands/<native-id>/<axis>.png`` and are never flattened into
    Room wall views. Missing directions remain absent and recorded upstream.
    """
    rendered_root = Path(rendered_root)
    output = Path(output)
    rooms = rendered.get('room_six_refs', {})
    exported = []
    for name, row in rendered['views'].items():
        if not row['image_generated']:
            continue
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ContractError('unsafe generated View path')
        folder = rendered_root / relative
        image = np.asarray(Image.open(folder / 'rgb.png').convert('RGB')).copy()
        geometry = np.asarray(Image.open(folder / 'geometry_valid.png')) > 0
        valid = np.asarray(Image.open(folder / 'color_valid.png')) > 0
        if image.shape[:2] != geometry.shape or valid.shape != geometry.shape or np.any(valid & ~geometry):
            raise ContractError('generated View mask dimensions or geometry binding differ')
        image[~geometry] = 255
        parts = relative.parts
        if 'islands' in parts:
            i = parts.index('islands')
            if len(parts) != i + 3:
                raise ContractError('invalid native Island View path')
            target = output / 'islands' / parts[i + 1] / (parts[i + 2] + '.png')
        elif len(rooms) == 1:
            target = output / 'sixview' / (parts[-1] + '.png')
        else:
            target = output / 'sixview' / relative.with_suffix('.png')
        if target.exists():
            raise ContractError('View export would overwrite an existing direction')
        target.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(image).save(target)
        exported.append({'native_view': name, 'rgb_file': str(target.relative_to(output)),
                         'size_wh': [image.shape[1], image.shape[0]],
                         'geometry_pixels': int(geometry.sum()),
                         'valid_color_pixels': int(valid.sum()),
                         'white_background_pixels': int((~geometry).sum()),
                         'sha256': digest(target)})
    if not exported:
        raise ContractError('no projectable G2 View PNG was generated')
    return exported


def save_direct_color_views(bundle, manifest, snapshot, surface_data, output, *,
                            meters_per_pixel=.01, renderer_backend='gpu'):
    """Render explicit native 10 mm color through the accepted G2 View path.

    ``manifest`` and ``snapshot`` must already come from the caller's verified
    source bundle or source-bound dynamic state. The producer supplies those
    objects directly so dynamic states never borrow a frame-zero identity.
    """
    if type(meters_per_pixel) not in (int, float) or meters_per_pixel != .01:
        raise ContractError('direct color Views require the accepted 1 cm/pixel recipe')
    if renderer_backend not in ('cpu', 'gpu'):
        raise ContractError('unsupported G2 rasterizer backend')
    if (snapshot.get('source_mode') != 'full_map_mujoco_source' or
            snapshot.get('surface_color_source') != 'MUJOCO_SOURCE_SURFACES_WITH_ORIGINAL_INVALID_MASK'):
        raise ContractError('direct color Views require explicit MuJoCo Full Map source')
    checked = validate_surface_data(surface_data, snapshot)
    bundle = Path(bundle).resolve()
    output = new_output(output, [bundle])
    started = time.perf_counter()
    from .render_connections import render_v2
    try:
        rendered = render_v2(bundle, manifest, snapshot, output / 'g2_original_gpu',
                             meters_per_pixel=meters_per_pixel, surface_data=checked,
                             renderer_backend=renderer_backend)
        exported = export_white_views(rendered, output / 'g2_original_gpu', output)
    finally:
        close_gpu_renderers()
    report = {'schema': 'g2_direct_color_view_export_v1',
              'scene_id': snapshot['scene_id'], 'source_sha256': snapshot['source_sha256'],
              'frame_id': snapshot['frame_id'], 'voxel_leaf_m': .01,
              'view_resolution_mpp': meters_per_pixel, 'renderer_backend': renderer_backend,
              'background_hex': '#FFFFFF', 'training_ready': False,
              'source_scene_graph_unchanged': True, 'view_count': len(exported),
              'gpu_render_and_export_s': round(time.perf_counter() - started, 5),
              'views': exported, 'room_six_refs': rendered['room_six_refs'],
              'islands': rendered['islands']}
    write_json(output / 'direct_color_views.json', report)
    return report
