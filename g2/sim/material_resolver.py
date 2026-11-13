"""Source-bound base albedo and opacity, independent of semantic ownership.

The resolver returns linear source albedo. It does not perform illumination,
refraction, normal mapping, or classify a material from its object name. A
separate compatibility display value reproduces the historical G2 convention
for already supported opaque assets; that value is never called linear source
albedo. No old F24 byte array is assigned a color space by this module.
"""

from dataclasses import dataclass

import numpy as np

from g2.io import ContractError
from g2.sim.texture_projection import (
    _bilinear,
    _cube,
    linear_to_srgb,
    srgb_to_linear,
)



def _lazy_decode_texels(raw, srgb):
    """Exact float64/255 + sRGB decoding on only selected source bytes."""
    values=np.asarray(raw,dtype=np.float64)/255.0
    if srgb:
        values[...,:3]=srgb_to_linear(values[...,:3])
    return values


def _lazy_bilinear(raw, uv, repeat, srgb):
    """Preserve original four-neighbor order and floating-point arithmetic."""
    height,width=raw.shape[:2]
    xy=(uv%1 if repeat else np.clip(uv,0,1))*[width,height]-.5
    lower=np.floor(xy).astype(np.int64)
    fraction=xy-lower
    colors=np.zeros((len(uv),raw.shape[2]),dtype=np.float64)
    for dx,dy in ((0,0),(1,0),(0,1),(1,1)):
        x,y=lower[:,0]+dx,lower[:,1]+dy
        x=x%width if repeat else np.clip(x,0,width-1)
        y=y%height if repeat else np.clip(y,0,height-1)
        weight=(fraction[:,0] if dx else 1-fraction[:,0])*(fraction[:,1] if dy else 1-fraction[:,1])
        colors+=_lazy_decode_texels(raw[y,x],srgb)*weight[:,None]
    return colors


def _lazy_cube(raw, direction, srgb):
    """Six-face cube with exact same face priority, ambiguity and rounding."""
    magnitude=np.max(np.abs(direction),axis=1)
    usable=np.isfinite(direction).all(axis=1)&(magnitude>0)
    tied=np.isclose(np.abs(direction),magnitude[:,None],rtol=1e-12,atol=0)
    transforms=((2,-1,1,-1),(2,1,1,-1),(0,1,2,1),
                (0,1,2,-1),(0,1,1,-1),(0,-1,1,-1))
    colors=np.zeros((len(direction),3));assigned=np.zeros(len(direction),bool)
    uncertain=np.zeros(len(direction),bool)
    for face,(s_axis,s_sign,t_axis,t_sign) in enumerate(transforms):
        axis=face//2
        selected=usable&tied[:,axis]&((direction[:,axis]>=0) if face%2==0 else (direction[:,axis]<0))
        indices=np.flatnonzero(selected)
        if not len(indices):continue
        uv=np.column_stack([direction[indices,s_axis]*s_sign,direction[indices,t_axis]*t_sign])
        uv=.5*(uv/magnitude[indices,None]+1)
        panel=raw[face] if raw.ndim==4 else raw
        candidate=_lazy_bilinear(panel,uv,False,srgb)
        different=np.max(np.abs(colors[indices]-candidate),axis=1)>1e-12
        uncertain[indices]|=assigned[indices]&different
        new=~assigned[indices]
        colors[indices[new]]=candidate[new]
        assigned[indices]=True
    return colors,usable&~uncertain,uncertain


VALID = 0
UNSUPPORTED = 1
OPACITY_UNSUPPORTED = 2
INVALID_COORDINATES = 5
UNVERIFIED_VERSION = 6
CUBE_FACE_TIE = 4


@dataclass(frozen=True)
class MaterialSamples:
    """Arrays have one row per requested surface sample.

    ``rgb_linear`` is normalized source albedo; ``rgb_compat`` is an encoded
    display triplet matching old supported G2 assets. Historical non-sRGB
    assets were written to PNG without an output transfer, so these fields
    deliberately differ from a universally sRGB-encoded source albedo.
    ``appearance_linear`` decodes that display triplet for linear display-space
    compositing, preserving already accepted opaque appearance. It is not a
    claim of physical/camera color equivalence.
    """

    rgb_linear: np.ndarray
    alpha: np.ndarray
    color_valid: np.ndarray
    alpha_valid: np.ndarray
    material_id: int
    alpha_mode: np.ndarray
    reason_code: np.ndarray
    alpha_reason_code: np.ndarray
    evidence: dict
    rgb_compat: np.ndarray

    @property
    def appearance_linear(self):
        return srgb_to_linear(self.rgb_compat)


class MaterialResolver:
    """Cache decoded textures for one immutable compiled source model.

    Geometry poses may change freely. Material tint and mapping parameters are
    read on every sample call, because different geoms can override the same
    material. If texture bytes/metadata change, call ``invalidate(texture_id)``
    (or use a fresh resolver) before sampling. The caller owns the source/model
    provenance check; ``source_sha256`` is copied into the evidence, not treated
    as proof that an arbitrary supplied model matches that digest.
    """

    def __init__(self, model, *, source_sha256=None, lazy_texel_decode=False):
        # Experimental opt-in only; original eager path remains the default.
        if type(lazy_texel_decode) is not bool:
            raise ContractError("lazy_texel_decode must be boolean")
        self.lazy_texel_decode=lazy_texel_decode
        self._raw_textures={}
        self.raw_texture_load_count=0
        self.raw_texture_cache_hits=0
        self.model = model
        self.source_sha256 = source_sha256
        self._textures = {}
        self.texture_decode_count = 0
        self.texture_cache_hits = 0

    def invalidate(self, texture_id=None):
        if texture_id is None:
            self._textures.clear()
            self._raw_textures.clear()
        else:
            self._textures.pop(int(texture_id), None)
            self._raw_textures.pop(int(texture_id), None)

    def _base(self, geom_id):
        from g2.sim.source_geometry import effective_rgba

        if (not isinstance(geom_id, (int, np.integer)) or isinstance(geom_id, bool)
                or geom_id < 0 or geom_id >= len(self.model.geom_matid)):
            raise ContractError("invalid material geom identity")
        g = int(geom_id)
        material = int(self.model.geom_matid[g])
        base = np.asarray(effective_rgba(self.model, g), dtype=np.float64)
        if (base.shape != (4,) or not np.isfinite(base).all()
                or np.any((base < 0) | (base > 1))):
            raise ContractError("unsupported compiled material color/alpha range")
        return g, material, base

    def descriptor(self, geom_id, kind=None):
        """Conservative whole-geom opacity classification before rasterization.

        No semantic owner participates. A varying alpha texture goes through
        the layer path; unknown opacity never becomes an opaque occluder.
        ``alpha_valid`` means opacity is spatially constant and known here;
        nonconstant texel alpha still needs coordinate-specific sampling.
        """
        g, material, base = self._base(geom_id)
        description = dict(geom_id=g, material_id=material, kind=kind,
                           texture_id=-1, effective_rgba=base.tolist(),
                           alpha_valid=True, alpha_min=float(base[3]),
                           alpha_max=float(base[3]), alpha_mode="OPAQUE",
                           guaranteed_opaque=bool(base[3] == 1.0),
                           reason="COMPILED_CONSTANT_ALPHA")
        if base[3] < 1.0:
            description["alpha_mode"] = "BLEND"

        def unknown(reason):
            description.update(alpha_valid=False, alpha_min=None, alpha_max=None,
                               alpha_mode="UNKNOWN", guaranteed_opaque=False,
                               reason=reason)
            return description

        if material < 0:
            return description
        import mujoco

        slots = self.model.mat_texid[material]
        rgb_role = int(mujoco.mjtTextureRole.mjTEXROLE_RGB)
        rgba_role = int(mujoco.mjtTextureRole.mjTEXROLE_RGBA)
        opacity_role = int(mujoco.mjtTextureRole.mjTEXROLE_OPACITY)
        if int(slots[opacity_role]) >= 0:
            return unknown("SEPARATE_OPACITY_TEXTURE_UNVERIFIED")
        texture = int(slots[rgb_role])
        description["texture_id"] = texture
        if texture < 0:
            if int(slots[rgba_role]) >= 0:
                return unknown("RGBA_TEXTURE_ROLE_UNVERIFIED")
            return description
        if mujoco.__version__ != "3.3.7":
            return unknown("UNVERIFIED_MUJOCO_TEXTURE_VERSION")
        try:
            if self.lazy_texel_decode:
                values, _, _, bounds = self._raw_texture_info(texture,mujoco)
            else:
                values, _, _ = self._texture(texture, mujoco)
        except (IndexError, ValueError) as exc:
            return unknown(str(exc))
        if values.shape[2] == 4:
            if self.lazy_texel_decode:
                low,high=float(bounds[0]*base[3]),float(bounds[1]*base[3])
            else:
                low,high=float(values[...,3].min()*base[3]),float(values[...,3].max()*base[3])
            description.update(alpha_min=low, alpha_max=high,
                               alpha_valid=bool(low == high),
                               guaranteed_opaque=bool(low == 1.0),
                               alpha_mode="OPAQUE" if low == 1.0 else "BLEND",
                               reason="COMPILED_TEXTURE_ALPHA_RANGE")
        return description

    def is_guaranteed_opaque(self, geom_id):
        return self.descriptor(geom_id)["guaranteed_opaque"]

    def _raw_texture_info(self, texture, mujoco):
        """Raw uint8 source snapshot and source-exact opacity statistics.

        No eager float64 allocation or whole-image sRGB transfer. The original
        expensive _texture method is unchanged and remains the default.
        """
        if texture in self._raw_textures:
            self.raw_texture_cache_hits+=1
            return self._raw_textures[texture]
        model=self.model
        width,height,channels,address=(
            int(getattr(model,key)[texture])
            for key in ("tex_width","tex_height","tex_nchannel","tex_adr"))
        if min(width,height)<=0 or channels not in (3,4) or address<0:
            raise ValueError("unsupported texture dimensions/channels")
        raw=np.asarray(model.tex_data)[address:address+width*height*channels]
        if raw.size != width*height*channels:
            raise ValueError("truncated compiled texture")
        if raw.dtype!=np.uint8:
            raise ValueError("compiled texture bytes must be uint8")
        if not hasattr(model,"tex_colorspace"):
            raise ValueError("compiled texture colorspace is unavailable")
        space_id=int(model.tex_colorspace[texture])
        srgb=int(mujoco.mjtColorSpace.mjCOLORSPACE_SRGB)
        linear=int(mujoco.mjtColorSpace.mjCOLORSPACE_LINEAR)
        auto=int(mujoco.mjtColorSpace.mjCOLORSPACE_AUTO)
        if space_id not in (srgb,linear,auto):
            raise ValueError("unsupported texture colorspace")
        raw=raw.reshape(height,width,channels).copy()
        raw.setflags(write=False)
        constant=bool(np.all(raw==raw[0,0]))
        alpha_bounds=None
        if channels==4:
            # Float64 conversion/multiplication follows original order.
            alpha=raw[...,3]
            alpha_bounds=(float(alpha.min())/255.0,float(alpha.max())/255.0)
        info=(raw,"sRGB" if space_id==srgb else "LINEAR",constant,alpha_bounds)
        self._raw_textures[texture]=info
        self.raw_texture_load_count+=1
        return info

    def _texture(self, texture, mujoco):
        if texture in self._textures:
            self.texture_cache_hits += 1
            return self._textures[texture]
        model = self.model
        width, height, channels, address = (
            int(getattr(model, key)[texture])
            for key in ("tex_width", "tex_height", "tex_nchannel", "tex_adr")
        )
        if min(width, height) <= 0 or channels not in (3, 4) or address < 0:
            raise ValueError("unsupported texture dimensions/channels")
        raw = np.asarray(model.tex_data)[address:address + width * height * channels]
        if raw.size != width * height * channels:
            raise ValueError("truncated compiled texture")
        values = raw.reshape(height, width, channels).astype(np.float64) / 255.0
        if not np.isfinite(values).all() or np.any((values < 0) | (values > 1)):
            raise ValueError("invalid compiled texture values")
        if not hasattr(model, "tex_colorspace"):
            raise ValueError("compiled texture colorspace is unavailable")
        space = int(model.tex_colorspace[texture])
        srgb = int(mujoco.mjtColorSpace.mjCOLORSPACE_SRGB)
        linear = int(mujoco.mjtColorSpace.mjCOLORSPACE_LINEAR)
        auto = int(mujoco.mjtColorSpace.mjCOLORSPACE_AUTO)
        # The pinned 3.3.7 GL upload applies sRGB decoding only for SRGB.
        # AUTO is the compiled non-sRGB/default-linear mode, not permission
        # to guess a texture's encoding from its file name or color values.
        if space not in (srgb, linear, auto):
            raise ValueError("unsupported texture colorspace")
        if space == srgb:
            values[..., :3] = srgb_to_linear(values[..., :3])
        values.setflags(write=False)
        constant = bool(np.all(values == values[0, 0]))
        result = (values, "sRGB" if space == srgb else "LINEAR", constant)
        self._textures[texture] = result
        self.texture_decode_count += 1
        return result

    def sample(self, geom_id, kind, face_ids, barycentric, *, local_points=None):
        """Resolve pure color, mesh UV, or pinned primitive 2D/cube albedo.

        Missing/unsupported color evidence yields zero RGB with validity false.
        Known black has validity true. Opacity is independent: an unsupported
        RGB projection can still have a known constant alpha. MuJoCo has no
        verified alpha-mask cutoff in this adapter, so fractional/zero opacity
        is BLEND; MASK is never inferred from a name or a few alpha samples.
        """
        model = self.model
        faces = np.asarray(face_ids)
        weights = np.asarray(barycentric, dtype=np.float64)
        if (faces.ndim != 1 or faces.dtype.kind not in "iu"
                or np.any(faces < 0) or weights.shape != (len(faces), 3)
                or not np.isfinite(weights).all()
                or np.any(weights < -1e-7)
                or not np.allclose(weights.sum(axis=1), 1.0, rtol=0, atol=1e-6)):
            raise ContractError("invalid material surface sample coordinates")
        g, material, base = self._base(geom_id)
        n = len(faces)
        rgb = np.repeat(base[None, :3], n, axis=0)
        compat = rgb.copy()
        alpha = np.full(n, base[3], dtype=np.float64)
        color_valid = np.ones(n, dtype=bool)
        alpha_valid = np.ones(n, dtype=bool)
        reasons = np.zeros(n, dtype=np.uint8)
        alpha_reasons = np.zeros(n, dtype=np.uint8)
        texture_alpha_known = False
        evidence = dict(
            mode="COMPILED_CONSTANT_SOURCE_ALBEDO", geom_id=g,
            material_id=material, texture_id=-1, texture_sampled=False,
            source_sha256=self.source_sha256,
            source_color_space="LINEAR_SOURCE_ALBEDO",
            display_compatibility="LEGACY_G2_ASSET_DISPLAY_VALUES",
            compatibility_is_physical_color=False,
            effective_rgba=base.tolist(), camera_observation=False,
            illumination_refraction_normal_mapping=False,
            alpha_mask_cutoff_inferred=False,
        )

        def result():
            rgb[~color_valid] = 0
            compat[~color_valid] = 0
            modes = np.full(n, "UNKNOWN", dtype="<U7")
            modes[alpha_valid & (alpha == 1.0)] = "OPAQUE"
            modes[alpha_valid & (alpha < 1.0)] = "BLEND"
            return MaterialSamples(rgb, alpha, color_valid, alpha_valid,
                                   material, modes, reasons, alpha_reasons,
                                   evidence, compat)

        def reject(reason, code=UNSUPPORTED, *, opacity_unknown=False):
            color_valid[:] = False
            reasons[:] = code
            evidence.update(mode="UNKNOWN_SOURCE_ALBEDO", reason=reason)
            if opacity_unknown and not texture_alpha_known:
                alpha_valid[:] = False
                alpha_reasons[:] = code
            return result()

        if material < 0:
            return result()
        import mujoco

        texids = np.asarray(model.mat_texid[material])
        rgb_role = int(mujoco.mjtTextureRole.mjTEXROLE_RGB)
        rgba_role = int(mujoco.mjtTextureRole.mjTEXROLE_RGBA)
        opacity_role = int(mujoco.mjtTextureRole.mjTEXROLE_OPACITY)
        texture = int(texids[rgb_role])
        opacity = int(texids[opacity_role])
        if opacity >= 0:
            alpha_valid[:] = False
            alpha_reasons[:] = OPACITY_UNSUPPORTED
            evidence["alpha_reason"] = "SEPARATE_OPACITY_TEXTURE_UNVERIFIED"
        evidence["unmodeled_shading_texture_roles"] = [
            int(i) for i, value in enumerate(texids)
            if int(value) >= 0 and i not in (rgb_role, rgba_role, opacity_role)
        ]
        if texture < 0:
            if int(texids[rgba_role]) >= 0:
                return reject("RGBA texture role is not verified by this renderer",
                              opacity_unknown=True)
            return result()
        evidence["texture_id"] = texture
        if mujoco.__version__ != "3.3.7":
            return reject("unverified MuJoCo texture projection version",
                          UNVERIFIED_VERSION, opacity_unknown=True)
        try:
            if self.lazy_texel_decode:
                pixels,space,constant,alpha_bounds=self._raw_texture_info(texture,mujoco)
            else:
                pixels,space,constant=self._texture(texture,mujoco)
        except (IndexError, ValueError) as exc:
            return reject(str(exc), opacity_unknown=True)
        channels = pixels.shape[2]
        texture_alpha_known = channels==3 or (
            alpha_bounds[0]==alpha_bounds[1] if self.lazy_texel_decode else
            bool(np.all(pixels[...,3]==pixels[0,0,3])))
        if channels == 4 and texture_alpha_known:
            alpha[:] = base[3] * (alpha_bounds[0] if self.lazy_texel_decode else pixels[0,0,3])
        texture_type = int(model.tex_type[texture])
        texture2d = int(mujoco.mjtTexture.mjTEXTURE_2D)
        texturecube = int(mujoco.mjtTexture.mjTEXTURE_CUBE)
        evidence.update(texture_colorspace=space, texture_sampled=True,
                        texture_decode_before_filter=True, texture_mip_level=0,
                        alpha_channel_is_linear=True,
                        compiled_colorspace_id=int(model.tex_colorspace[texture]),
                        colorspace_reference="MUJOCO_3_3_7_TEXTURE_UPLOAD",
                        rgba_role_ignored_by_pinned_rgb_binding=bool(int(texids[rgba_role]) >= 0))
        if texture_type not in (texture2d, texturecube):
            return reject("unsupported surface texture type",
                          opacity_unknown=(channels == 4))
        sampled = np.zeros((n, channels), dtype=np.float64)
        coordinates_valid = np.ones(n, dtype=bool)
        if constant:
            # A uniform texture is exactly independent of UVs and projection.
            # This includes (but does not special-case) white glass textures.
            sampled[:] = (_lazy_decode_texels(pixels[0,0],space=="sRGB")
                          if self.lazy_texel_decode else pixels[0,0])
            evidence["mode"] = "UNIFORM_TEXTURE_SOURCE_ALBEDO"
        elif kind == "mesh":
            if texture_type != texture2d or bool(model.mat_texuniform[material]):
                return reject("unsupported mesh texture projection",
                              opacity_unknown=(channels == 4))
            mid = int(model.geom_dataid[g])
            start, count = int(model.mesh_faceadr[mid]), int(model.mesh_facenum[mid])
            if np.any(faces >= count):
                raise ContractError("material sample face exceeds source mesh")
            uvfaces = np.asarray(model.mesh_facetexcoord[start:start + count])[faces]
            uvstart = int(model.mesh_texcoordadr[mid])
            uvcount = int(model.mesh_texcoordnum[mid])
            values = np.asarray(model.mesh_texcoord[uvstart:uvstart + uvcount])
            if uvfaces.shape != (n, 3) or values.shape != (uvcount, 2):
                return reject("invalid compiled mesh UV layout",
                              opacity_unknown=(channels == 4))
            coordinates_valid = np.all((uvfaces >= 0) & (uvfaces < uvcount), axis=1)
            ids = np.flatnonzero(coordinates_valid)
            if len(ids):
                uv = np.einsum("bi,bij->bj", weights[ids], values[uvfaces[ids]])
                uv *= np.asarray(model.mat_texrepeat[material])
                finite = np.isfinite(uv).all(axis=1)
                coordinates_valid[ids[~finite]] = False
                sampled[ids[finite]] = (
                    _lazy_bilinear(pixels,uv[finite],True,space=="sRGB")
                    if self.lazy_texel_decode else _bilinear(pixels,uv[finite],True))
            evidence.update(mode="MESH_UV_SOURCE_ALBEDO", filter="repeat_bilinear")
        else:
            if kind not in ("box", "cylinder", "sphere", "ellipsoid"):
                return reject("unsupported primitive texture mapping",
                              opacity_unknown=(channels == 4))
            points = np.asarray(local_points, dtype=np.float64)
            if points.shape != (n, 3):
                return reject("local primitive coordinates required",
                              INVALID_COORDINATES, opacity_unknown=(channels == 4))
            coordinates_valid = np.isfinite(points).all(axis=1)
            size = np.asarray(model.geom_size[g], dtype=np.float64).copy()
            if kind == "sphere":
                size[:] = size[0]
            elif kind == "cylinder":
                size = np.asarray([size[0], size[0], size[1]])
            if not np.isfinite(size).all() or np.any(size <= 0):
                return reject("invalid primitive extents", INVALID_COORDINATES,
                              opacity_unknown=(channels == 4))
            uniform = bool(model.mat_texuniform[material])
            ids = np.flatnonzero(coordinates_valid)
            local = points[ids]
            object_points = local / size
            if texture_type == texture2d:
                xy = local[:, :2] if uniform else object_points[:, :2]
                uv = xy * [0.5, -0.5] * np.asarray(model.mat_texrepeat[material]) - 0.5
                finite = np.isfinite(uv).all(axis=1)
                coordinates_valid[ids[~finite]] = False
                sampled[ids[finite]] = (
                    _lazy_bilinear(pixels,uv[finite],True,space=="sRGB")
                    if self.lazy_texel_decode else _bilinear(pixels,uv[finite],True))
                evidence.update(mode="PRIMITIVE_2D_SOURCE_ALBEDO", filter="repeat_bilinear")
            else:
                height, width = pixels.shape[:2]
                if channels != 3 or height not in (width, 6 * width):
                    return reject("unsupported cube channel/layout",
                                  opacity_unknown=(channels == 4))
                if self.lazy_texel_decode:
                    cubefaces=(pixels if height==width else
                               pixels.reshape(6,width,width,3))
                else:
                    cubefaces=(np.repeat(pixels[None],6,axis=0) if height==width
                               else pixels.reshape(6,width,width,3))
                samples,ok,uncertain=(
                    _lazy_cube(cubefaces,local if uniform else object_points,space=="sRGB")
                    if self.lazy_texel_decode else
                    _cube(cubefaces,local if uniform else object_points))
                sampled[ids] = samples
                coordinates_valid[ids] = ok
                reasons[ids[uncertain]] = CUBE_FACE_TIE
                evidence.update(mode="PRIMITIVE_CUBE_SOURCE_ALBEDO",
                                filter="clamp_to_edge_bilinear",
                                texrepeat_applied=False,
                                cube_face_order=["+X", "-X", "+Y", "-Y", "+Z", "-Z"])
            evidence["texuniform"] = uniform
        color_valid[:] = coordinates_valid
        reasons[~coordinates_valid & (reasons == VALID)] = INVALID_COORDINATES
        rgb[:] = sampled[:, :3] * base[:3]
        np.clip(rgb, 0.0, 1.0, out=rgb)
        compat[:] = linear_to_srgb(rgb) if space == "sRGB" else rgb
        if channels == 4 and not texture_alpha_known:
            alpha[:] = base[3] * sampled[:, 3]
            np.clip(alpha, 0.0, 1.0, out=alpha)
            alpha_valid &= coordinates_valid
            alpha_reasons[~coordinates_valid] = INVALID_COORDINATES
        evidence["texrepeat"] = np.asarray(model.mat_texrepeat[material]).tolist()
        return result()
