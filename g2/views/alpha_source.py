"""GT-source alpha sidecars for transparent-only entities.

Native 10mm color remains *opaque RGB*; translucent surfaces are never marked
color-valid, nor inferred from nearest opaque voxels. The independent RGBA
layer can be composited when a background is actually known; checkerboard
previews are explicitly NOT training-ready scene RGB.
"""
from pathlib import Path

import numpy as np
from PIL import Image

from g2.io import ContractError, write_json


def compiled_translucent_only_owner_proof(model, specs, snapshot, source_model_sha256):
    """Derive alpha from compiled, source-verified MuJoCo visual geoms only."""
    import mujoco
    from g2.sim.source_geometry import effective_rgba
    identities = sorted(e['id'] for e in snapshot['entities'])
    by_id = {e['id']: e for e in snapshot['entities']}
    groups = {}
    for spec in specs:
        owner = spec['owner']
        if owner < 0 or owner >= len(identities) or by_id[identities[owner]]['kind'] != 'object':
            continue
        rgba = np.asarray(effective_rgba(model, spec['g']), dtype=np.float64)
        if rgba.shape != (4,) or not np.isfinite(rgba).all() or (rgba < 0).any() or (rgba > 1).any():
            raise ContractError('unsupported compiled source alpha')
        # Color textures with alpha need UV-proven per-pixel opacity, and are
        # excluded from the constant-alpha sidecar.
        mat = int(model.geom_matid[spec['g']])
        textured = mat >= 0 and bool(np.any(model.mat_texid[mat] >= 0))
        appearance = 'COMPILED_CONSTANT_COLOR_NO_TEXTURE'
        if textured:
            rgb_tex = int(model.mat_texid[mat, int(mujoco.mjtTextureRole.mjTEXROLE_RGB)])
            other_textures = [int(t) for k, t in enumerate(model.mat_texid[mat]) if
                              k != int(mujoco.mjtTextureRole.mjTEXROLE_RGB) and int(t) >= 0]
            if rgb_tex >= 0 and not other_textures:
                cols = [int(getattr(model, key)[rgb_tex]) for key in
                        ('tex_width', 'tex_height', 'tex_nchannel', 'tex_adr')]
                tw, th, channels, offset = cols
                if channels in (3,4) and tw > 0 and th > 0:
                    pixels = np.asarray(model.tex_data[offset:offset+tw*th*channels])
                    # All-white texture is invariant to sRGB decoding and UVs.
                    if pixels.size == tw*th*channels and np.all(pixels == 255):
                        textured = False
                        appearance = 'COMPILED_UNIFORM_WHITE_RGB_TEXTURE_UV_INDEPENDENT'
        groups.setdefault(owner, []).append((rgba, spec['name'], textured, appearance))
    supported = {}
    skipped = {}
    for owner, geoms in groups.items():
        alpha = [float(row[0][3]) for row in geoms]
        if all(0 < x < 1 - 1.e-7 for x in alpha) and len(geoms) == 1 and not geoms[0][2]:
            rgba = geoms[0][0]
            supported[identities[owner]] = {
                'owner_index': int(owner),
                'rgba': rgba.tolist(),
                'geom_name': geoms[0][1],
                'source_model_sha256': source_model_sha256,
                'material_kind': 'COMPILED_CONSTANT_MUJOCO_TRANSLUCENT_GEOM',
                'source_color_appearance_proof': geoms[0][3],
            }
        elif any(x < 1 - 1.e-7 for x in alpha):
            skipped[identities[owner]] = 'MIXED_ALPHA_OR_TEXTURING_REQUIRES_GEOM_LAYER'
    return {
        'schema': 'g2_compiled_gt_alpha_only_source_v1',
        'scene_id': snapshot['scene_id'],
        'source_sha256': snapshot['source_sha256'],
        'model_source_sha256': source_model_sha256,
        'supported_owner_materials': supported,
        'skipped_mixed_or_textured_owners': skipped,
        'training_ready': False,
    }


def _verify_proof(proof, snapshot):
    if proof.get('schema') != 'g2_compiled_gt_alpha_only_source_v1':
        raise ContractError('invalid source-derived alpha proof')
    if proof.get('scene_id') != snapshot['scene_id'] or proof.get('source_sha256') != snapshot['source_sha256']:
        raise ContractError('alpha proof source mismatch')
    entity = {e['id']:e for e in snapshot['entities']}
    ordered = sorted(entity)
    materials = proof.get('supported_owner_materials')
    if not isinstance(materials, dict):
        raise ContractError('missing compiled transparent material proof')
    for eid, m in materials.items():
        if eid not in entity or entity[eid]['kind'] != 'object':
            raise ContractError('alpha mask cannot name non-objects')
        if m.get('owner_index') != ordered.index(eid):
            raise ContractError('alpha owner/ID mismatch')
        rgba = np.asarray(m.get('rgba'), dtype=float)
        if (rgba.shape != (4,) or not np.isfinite(rgba).all() or
                (rgba < 0).any() or (rgba > 1).any() or not 0 < rgba[3] < 1):
            raise ContractError('invalid alpha material values')
        if m.get('source_model_sha256') != proof.get('model_source_sha256'):
            raise ContractError('alpha material not bound to model')
    return materials


def save_source_alpha_sidecars(native_render_root, rendered, snapshot, proof, output,
                               *, visual_mesh_by_room=None):
    """Retain Alpha/validity as an independent diagnostic, never RGB replacement."""
    from g2.io import digest
    materials = _verify_proof(proof, snapshot)
    native_render_root = Path(native_render_root)
    output = Path(output)
    if output.exists():
        raise ContractError('alpha sidecar output must not overwrite')
    output.mkdir(parents=True)
    results = []
    for key, view in rendered['views'].items():
        if not view['image_generated']:
            continue
        parent = native_render_root / key
        with np.load(parent / 'geometry.npz', allow_pickle=False) as data:
            owner = data['native_entity_index']
        geometry = np.asarray(Image.open(parent / 'geometry_valid.png')) > 0
        valid = np.asarray(Image.open(parent / 'color_valid.png')) > 0
        original = np.asarray(Image.open(parent / 'rgb.png').convert('RGB'))
        if not (owner.shape == geometry.shape == valid.shape == original.shape[:2]):
            raise ContractError('source alpha view dimensions differ')
        with np.load(parent / 'geometry.npz',allow_pickle=False) as result_geom:
            depth_opaque=np.asarray(result_geom['depth'],float)
        if depth_opaque.shape!=geometry.shape:
            raise ContractError('source opaque geometry depth mismatch')
        if np.any(valid & ~geometry):
            raise ContractError('invalid source alpha mask domain')
        layer = np.zeros((*geometry.shape, 4), np.uint8)
        preview = original.copy()
        preview[~geometry] = 255
        by_entity = {}
        known_background_px=0
        unknown_background_px=0
        visible_alpha=np.zeros_like(geometry)
        visual_alpha_geom_indices=np.full(geometry.shape,-2,np.int32)
        visual_alpha_depth=np.full(geometry.shape,np.nan)
        if visual_mesh_by_room is not None:
            # Actual Alpha source geometry, not the old collision snapshot:
            # independently project compiled transparent MuJoCo Visual Geoms.
            from g2.views.exact_compute import get_engine
            room_key=key.split('/')
            if (len(room_key)<3 or room_key[0]!='rooms'):
                raise ContractError('alpha source view lacks explicit native room')
            try:
                room_uid=int(room_key[1])
            except ValueError as exc:
                raise ContractError('invalid native alpha room uid') from exc
            source_geom=visual_mesh_by_room.get(room_uid)
            if source_geom is None:
                raise ContractError('source alpha visual mesh unavailable for room')
            allowed_native_members=set(rendered['views'][key]['native_entity_ids'])
            specids={j for j,a in source_geom['attributes'].items()
                     if a['native_id'] in allowed_native_members and
                     a['native_id'] in materials and
                     a['geom_name']==materials[a['native_id']]['geom_name']}
            mesh=[row for row in source_geom['translucent'] if row[0] in specids]
            if mesh:
                from g2.views.render import AXES
                meta=rendered['views'][key]
                axis=meta['axis']
                if axis not in AXES:
                    raise ContractError('unsupported source alpha axis')
                lo=np.asarray(meta['room_bounds_min'],float)
                hi=np.asarray(meta['room_bounds_max'],float)
                visible_alpha,visual_alpha_depth,visual_alpha_geom_indices,dims,_=get_engine().draw(
                    mesh,specids,lo,hi,axis,.01)
                if visible_alpha.shape!=geometry.shape:
                    raise ContractError('source alpha mesh/view dimensions differ')
            else:
                visible_alpha=np.zeros_like(geometry)
        else:
            # Legacy separate-alpha diagnostic remains available for old
            # collision-based source Views; never pass as a visual GT proof.
            visible_alpha=geometry & ~valid
        for eid, m in sorted(materials.items()):
            if visual_mesh_by_room is not None:
                matching_source_spec={
                    j for j,a in source_geom['attributes'].items()
                    if a['native_id']==eid and
                    a['geom_name']==m['geom_name']}
                candidates=visible_alpha & np.isin(
                    visual_alpha_geom_indices, list(matching_source_spec))
                # Correct occlusion: the transparent surface is visible if
                # there is no opaque surface in front of it.
                alpha_front=candidates & (~geometry | (visual_alpha_depth < depth_opaque-1.e-8))
                opaque_unknown=alpha_front
            else:
                opaque_unknown = geometry & ~valid & (owner == m['owner_index'])
            if not np.any(opaque_unknown):
                continue
            rgba = np.asarray(m['rgba'], dtype=float)
            source_rgb = np.rint(rgba[:3] * 255).astype(np.uint8)
            material_alpha = float(rgba[3])
            layer[opaque_unknown, :3] = source_rgb
            layer[opaque_unknown, 3] = round(material_alpha * 255)
            rr, cc = np.nonzero(opaque_unknown)
            # Checkerboard is visibly UNOBSERVED background, never a claimed
            # source-color replacement. Alpha layer is preserved losslessly.
            checker = np.where((rr // 8 + cc // 8) % 2 == 0, 216, 244)
            bg = np.repeat(checker[:,None], 3, axis=1)
            if visual_mesh_by_room is not None:
                # Use existing source RGB when opaque background is known.
                # Otherwise the checkerboard is an explicit UNKNOWN, not GT.
                bg_is_proven=valid[rr,cc]
                bg[bg_is_proven]=original[rr[bg_is_proven],cc[bg_is_proven]]
                known_background_px+=int(bg_is_proven.sum())
                unknown_background_px+=int((~bg_is_proven).sum())
            preview[rr,cc] = np.rint(source_rgb * material_alpha + bg * (1 - material_alpha)).astype(np.uint8)
            by_entity[eid] = int(opaque_unknown.sum())
        if visual_mesh_by_room is None:
            assert not np.any((layer[:,:,3] > 0) & valid)
        relative = Path(key)
        if relative.is_absolute() or '..' in relative.parts:
            raise ContractError('unsafe alpha sidecar direction')
        target = output / relative
        target.mkdir(parents=True)
        Image.fromarray(layer, 'RGBA').save(target / 'source_rgba.png')
        Image.fromarray(preview, 'RGB').save(target / 'checkerboard_unknown_preview.png')
        results.append({
            'view': key, 'frame_id': snapshot['frame_id'],
            'material_alpha_from_actual_compiled_source': True,
            'alpha_pixel_count': int((layer[:,:,3] > 0).sum()),
            'by_entity': by_entity,
            'source_rgba_sha256': digest(target / 'source_rgba.png'),
            'checkerboard_preview_sha256': digest(target / 'checkerboard_unknown_preview.png'),
            'source_rgba_file': str((relative / 'source_rgba.png')),
            'checkerboard_preview_file': str((relative / 'checkerboard_unknown_preview.png')),
            'background_known': bool(known_background_px and not unknown_background_px),
            'full_transparency_compositor_complete': False,
        })
        if visual_mesh_by_room is not None:
            results[-1].update(
                source_alpha_on_known_opaque_background_pixels=known_background_px,
                source_alpha_on_unknown_background_pixels=unknown_background_px,
                source_alpha_mesh_geometry=True,
                source_alpha_opaque_depth_aware=True,
                source_alpha_no_refraction_or_multiple_layers=True)
    report = {
        'schema': 'g2_source_opaque_separate_alpha_view_sidecar_v1',
        'scene_id': snapshot['scene_id'], 'source_sha256': snapshot['source_sha256'],
        'frame_id': snapshot['frame_id'],
        'source_model_sha256': proof['model_source_sha256'],
        'compilation_provenance': 'ACTUAL_SOURCE_MUJOCO_MODEL_CONSTANT_ALPHA_ONLY',
        'view_count': len(results), 'supported_owners': sorted(materials),
        'skipped_mixed_alpha_owner_ids': proof['skipped_mixed_or_textured_owners'],
        'training_ready': False, 'human_gate': 'PENDING_HUMAN',
        'background_compositing_status': ('ACTUAL_OPAQUE_RGB_IF_PROVEN_ELSE_CHECKERBOARD_UNKNOWN'
                                         if visual_mesh_by_room is not None else
                                         'UNKNOWN_BACKGROUND_NOT_YET_RENDERED'),
        'view_alpha_layers': results,
    }
    if visual_mesh_by_room is not None:
        report['source_visual_mesh_for_transparency']=True
    write_json(output / 'alpha_sidecar_manifest.json', report)
    if visual_mesh_by_room is not None:
        # The actual Visual-Alpha GPU Z-buffer opened an EGL context. Release
        # it explicitly so long-lived episode workers do not leak contexts
        # and CLI shutdown does not rely on unsafe Python __del__ teardown.
        from g2.views.exact_compute import close_engine
        close_engine()
    return report
