"""MuJoCo3.3.7 object-linear primitives and OpenGL cube base-level lookup.

Reference: google-deepmind/mujoco 3.3.7, render_gl3.c:settexture/renderGeom,
render_context.c:mjr_uploadTexture; cube orientation is the OpenGL cube table.
Asset albedo bytes only: no lighting, camera, mipmap LOD or house certification.
"""
import numpy as np

REASONS = {0: "VALID", 1: "UNSUPPORTED_APPEARANCE", 2: "SEPARATE_OPACITY_TEXTURE",
           3: "TRANSLUCENT_SAMPLE", 4: "CUBE_FACE_TIE_DIFFERENT_COLOR",
           5: "INVALID_LOCAL_TEXTURE_COORDINATES", 6: "UNVERIFIED_MUJOCO_PROJECTION_VERSION"}


def _bilinear(pixels, uv, repeat):
    height, width = pixels.shape[:2]
    xy = (uv % 1 if repeat else np.clip(uv, 0, 1)) * [width, height] - .5
    lower = np.floor(xy).astype(np.int64); fraction = xy - lower
    colors = np.zeros((len(uv), pixels.shape[2]))
    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        x, y = lower[:, 0] + dx, lower[:, 1] + dy
        x = x % width if repeat else np.clip(x, 0, width - 1)
        y = y % height if repeat else np.clip(y, 0, height - 1)
        weight = (fraction[:, 0] if dx else 1 - fraction[:, 0]) * (fraction[:, 1] if dy else 1 - fraction[:, 1])
        colors += pixels[y, x] * weight[:, None]
    return colors


def _cube(pixels, direction):
    magnitude = np.max(np.abs(direction), axis=1)
    usable = np.isfinite(direction).all(axis=1) & (magnitude > 0)
    tied = np.isclose(np.abs(direction), magnitude[:, None], rtol=1e-12, atol=0)
    # +X,-X,+Y,-Y,+Z,-Z; sc,tc each divided by positive major magnitude.
    transforms = ((2, -1, 1, -1), (2, 1, 1, -1), (0, 1, 2, 1),
                  (0, 1, 2, -1), (0, 1, 1, -1), (0, -1, 1, -1))
    colors = np.zeros((len(direction), 3)); assigned = np.zeros(len(direction), bool)
    uncertain = np.zeros(len(direction), bool)
    for face, (s_axis, s_sign, t_axis, t_sign) in enumerate(transforms):
        axis = face // 2
        selected = usable & tied[:, axis] & ((direction[:, axis] >= 0) if face % 2 == 0 else (direction[:, axis] < 0))
        indices = np.flatnonzero(selected)
        if not len(indices):
            continue
        uv = np.column_stack([direction[indices, s_axis] * s_sign, direction[indices, t_axis] * t_sign])
        uv = .5 * (uv / magnitude[indices, None] + 1)
        candidate = _bilinear(pixels[face], uv, False)
        different = np.max(np.abs(colors[indices] - candidate), axis=1) > 1e-12
        uncertain[indices] |= assigned[indices] & different
        new = ~assigned[indices]
        colors[indices[new]] = candidate[new]
        assigned[indices] = True
    return colors, usable & ~uncertain, uncertain


def primitive_colors(model, g, kind, local_points, count, rgba):
    import mujoco
    rgba = rgba.copy()
    rgba[:, :3] = 0  # unknown texture is never replaced by a proxy geom color
    valid = np.zeros(count, bool); reasons = np.ones(count, np.uint8)
    appearance = {"mode": "UNSUPPORTED_TEXTURE_PROJECTION", "texture_sampled": False,
                  "camera_observation": False, "projection_reference": "MuJoCo3.3.7_render_gl3_settexture",
                  "color_encoding": "COMPILED_BASE_LEVEL_ASSET_BYTES_NO_LIGHTING_OR_MIPMAP_LOD"}

    def reject(reason, code=1):
        appearance["reason"] = reason; reasons[:] = code
        return rgba, valid, appearance, reasons

    if mujoco.__version__ != "3.3.7":
        return reject("unverified MuJoCo primitive projection version", 6)
    if kind not in ("box", "cylinder", "sphere", "ellipsoid"):
        return reject("unsupported primitive object-coordinate transform")
    if (not isinstance(local_points, np.ndarray) or local_points.shape != (count, 3)
            or not np.isfinite(local_points).all()):
        return reject("local surface coordinates required", 5)
    mat = int(model.geom_matid[g]); texids = model.mat_texid[mat]
    rgb = int(texids[int(mujoco.mjtTextureRole.mjTEXROLE_RGB)])
    # The pinned GL renderer binds RGB role only; RGBA role is a different
    # material layer, not an override of that binding.
    texture = rgb
    appearance["texture_id"] = texture
    if texture < 0:
        return reject("no RGB texture role bound by the pinned renderer")
    if int(texids[int(mujoco.mjtTextureRole.mjTEXROLE_OPACITY)]) >= 0:
        return reject("separate opacity texture", 2)
    width, height, channels, address = [int(getattr(model, key)[texture])
        for key in ("tex_width", "tex_height", "tex_nchannel", "tex_adr")]
    if channels not in (3, 4) or min(width, height) <= 0:
        return reject("unsupported texture dimensions/channel count")
    pixels = model.tex_data[address:address + width * height * channels].reshape(height, width, channels).astype(float) / 255
    size = model.geom_size[g].astype(float).copy()
    if kind == "sphere": size[:] = size[0]
    elif kind == "cylinder": size = np.asarray([size[0], size[0], size[1]])
    if np.any(size <= 0) or not np.isfinite(size).all():
        return reject("invalid primitive extents", 5)
    object_points = local_points / size
    uniform = bool(model.mat_texuniform[mat])
    texture_type = int(model.tex_type[texture])
    appearance["colorspace_id"]=int(model.tex_colorspace[texture])
    if texture_type == int(mujoco.mjtTexture.mjTEXTURE_2D):
        if int(model.tex_colorspace[texture])==int(mujoco.mjtColorSpace.mjCOLORSPACE_SRGB):
            return reject("sRGB decode/filter/output encoding is outside the verified base-byte projection path")
        xy = local_points[:, :2] if uniform else object_points[:, :2]
        uv = xy * [.5, -.5] * model.mat_texrepeat[mat] - .5
        if not np.isfinite(uv).all():
            return reject("nonfinite planar texture coordinates", 5)
        sampled = _bilinear(pixels, uv, True)
        valid[:] = True
        appearance.update(mode="primitive_2d_object_linear_asset_albedo", filter="repeat_bilinear",
                          texrepeat=model.mat_texrepeat[mat].tolist())
    elif texture_type == int(mujoco.mjtTexture.mjTEXTURE_CUBE):
        if channels != 3 or height not in (width, 6 * width):
            return reject("unsupported cube dimensions/channel layout")
        faces = np.repeat(pixels[None], 6, axis=0) if height == width else pixels.reshape(6, width, width, 3)
        # Cube texrepeat is ignored in the pinned renderer. texuniform scales
        # its object-linear directions by geom extents instead.
        sampled, valid, uncertain = _cube(faces, local_points if uniform else object_points)
        reasons[:] = 5; reasons[uncertain] = 4
        appearance.update(mode="primitive_cube_object_linear_asset_albedo", filter="clamp_to_edge_bilinear",
                          cube_face_order=["+X", "-X", "+Y", "-Y", "+Z", "-Z"], texrepeat_applied=False)
    else:
        return reject("skybox/other texture is not a supported surface texture")
    # Material modulation is real source albedo; excluded collision proxies do
    # not enter this path. Unknown points keep mask false and RGB zero.
    rgba[:, :3] = sampled[:, :3] * model_color(model, g)[:3]
    if channels == 4:
        rgba[:, 3] *= sampled[:, 3]
    reasons[valid] = 0
    rgba[~valid, :3] = 0
    appearance.update(texture_sampled=True, texuniform=uniform)
    if np.any(~valid): appearance["reason"] = "ambiguous or invalid cube direction"
    return rgba, valid, appearance, reasons


def model_color(model, g):
    from .source_geometry import effective_rgba
    return effective_rgba(model, g)
