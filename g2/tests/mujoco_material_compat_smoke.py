"""Compare source-material samples with the stock MuJoCo EGL renderer.

Run once with each supported MuJoCo wheel. Tiny magnified textures keep the
comparison on the base level. The RGBA fixture uses a single additive draw
over black to measure texture/material alpha without a second transparent pass.
"""

import io
import json
import math
from hashlib import sha256

import mujoco
import numpy as np
from OpenGL import GL
from PIL import Image

from g2.sim.material_resolver import MaterialResolver

SIZE = 192
FOV = 32
BOX = np.array([0.55, 0.43, 0.20])
MESH = (
    '<mesh name="shape" vertex="-.5 -.45 0  .5 -.45 0  0 .55 0  0 0 -.45" '
    'face="0 1 2  1 0 3  2 1 3  0 2 3" '
    'texcoord=".15 .2  .93 .1  .49 .88  .5 .4"/>'
)


def _vector_text(values):
    return " ".join(map(str, values))


def _fixture(kind, texture_type, pixels, *, normal, right, up, uniform=False):
    encoded = io.BytesIO()
    Image.fromarray(pixels).save(encoded, format="PNG")
    alpha = pixels.shape[-1] == 4
    cube = 'gridsize="6 1" gridlayout="RLUDFB"' if texture_type == "cube" else ""
    mesh = MESH if kind == "mesh" else ""
    shape = 'type="mesh" mesh="shape"' if mesh else 'type="box" size=".55 .43 .2"'
    # 3.3.7 retains the archived F27 mesh UV convention. The 3.3.1
    # fixture deliberately passes non-unit repeat for native explicit UVs.
    repeat = "1 1" if mesh and mujoco.__version__ == "3.3.7" else "2 3"
    return mujoco.MjModel.from_xml_string(
        f"""
        <mujoco>
          <visual><global offwidth="{SIZE}" offheight="{SIZE}"/>
            <quality offsamples="0" shadowsize="0"/>
            <headlight ambient="0 0 0" diffuse="0 0 0" specular="0 0 0"/>
          </visual>
          <asset>
            <texture name="t" type="{texture_type}" file="texture.png"
              nchannel="{pixels.shape[-1]}" {cube}/>
            <material name="m" texture="t" rgba="1 1 1 {0.6 if alpha else 1}"
              emission="1" specular="0" texrepeat="{repeat}"
              texuniform="{str(uniform).lower()}"/>
            {mesh}
          </asset>
          <worldbody>
            <camera name="sample" pos="{_vector_text(3 * normal)}"
              xyaxes="{_vector_text(np.concatenate((right, up)))}" fovy="{FOV}"/>
            <geom name="subject" {shape} material="m"/>
          </worldbody>
        </mujoco>
        """,
        assets={"texture.png": encoded.getvalue()},
    )


def _samples(model, data, kind, normal, right, up, pixel_indices):
    columns, rows = pixel_indices.T
    plane = float(BOX[np.argmax(np.abs(normal))]) if kind == "box" else 0.0
    span = 2 * (3 - plane) * math.tan(math.radians(FOV) / 2)
    u = (columns + 0.5 - SIZE / 2) * span / SIZE
    v = -(rows + 0.5 - SIZE / 2) * span / SIZE
    points = plane * normal + u[:, None] * right + v[:, None] * up
    if kind != "mesh":
        return (
            points,
            np.zeros(len(points), np.int64),
            np.tile([1.0, 0, 0], (len(points), 1)),
            pixel_indices,
        )

    # Find the compiled top triangle in world coordinates, then interpolate
    # its original face UVs at exactly the native pixel centres.
    rotation = data.geom_xmat[0].reshape(3, 3)
    world = model.mesh_vert @ rotation.T + data.geom_xpos[0]
    triangles = world[model.mesh_face]
    top = np.flatnonzero(np.isclose(triangles[:, :, 2], plane, atol=1e-7).all(axis=1))
    (face,) = top.tolist()
    transform = np.vstack((triangles[face, :, :2].T, np.ones(3)))
    weights = np.linalg.solve(
        transform, np.vstack((points[:, :2].T, np.ones(len(points))))
    ).T
    inner = np.min(weights, axis=1) > 0.05
    return (
        (points[inner] - data.geom_xpos[0]) @ rotation,
        np.full(inner.sum(), face, dtype=np.int64),
        weights[inner],
        pixel_indices[inner],
    )


def _case(name, kind, texture_type, pixels, normal, *, uniform=False):
    up = np.array([0, 1, 0]) if normal[2] else np.array([0, 0, 1])
    right = np.cross(up, normal)
    model = _fixture(
        kind, texture_type, pixels, normal=normal, right=right, up=up, uniform=uniform
    )
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    alpha = pixels.shape[-1] == 4
    with mujoco.Renderer(model, height=SIZE, width=SIZE) as renderer:
        renderer.update_scene(data, camera="sample")
        renderer.scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW] = 0
        renderer.scene.flags[mujoco.mjtRndFlag.mjRND_ADDITIVE] = int(alpha)
        reference = renderer.render().copy()
        renderer_name = GL.glGetString(GL.GL_RENDERER).decode("ascii")
    radius = 13 if texture_type == "cube" else 40
    grid = np.arange(SIZE // 2 - radius, SIZE // 2 + radius, 4)
    pixel_indices = np.column_stack([v.ravel() for v in np.meshgrid(grid, grid)])
    points, faces, weights, indices = _samples(
        model, data, kind, normal, right, up, pixel_indices
    )
    sampled, lazy = [
        MaterialResolver(model, lazy_texel_decode=mode).sample(
            0, kind, faces, weights, local_points=points
        )
        for mode in (False, True)
    ]
    np.testing.assert_array_equal(sampled.rgb_linear, lazy.rgb_linear)
    np.testing.assert_array_equal(sampled.alpha, lazy.alpha)
    assert len(indices) > 20 and sampled.color_valid.all() and sampled.alpha_valid.all()
    expected = np.rint(sampled.rgb_linear * sampled.alpha[:, None] * 255).astype(int)
    reference_pixels = reference[indices[:, 1], indices[:, 0]]
    delta = int(np.max(np.abs(reference_pixels.astype(int) - expected)))
    assert len(np.unique(reference_pixels, axis=0)) > 1, name
    assert delta <= 2, (name, delta)
    assert (
        sampled.evidence["colorspace_reference"]
        == f"MUJOCO_{mujoco.__version__.replace('.', '_')}_TEXTURE_UPLOAD"
    )
    return {
        "fixture": name,
        "renderer": renderer_name,
        "compared_pixels": len(indices),
        "max_rgb_byte_delta": delta,
        "reference_pixels_sha256": sha256(reference_pixels.tobytes()).hexdigest(),
        "sampled_pixels_sha256": sha256(
            expected.astype(np.uint8).tobytes()
        ).hexdigest(),
    }


def main():
    y, x = np.indices((4, 4))
    rgb = np.stack([32 + x * 50, 24 + y * 53, 12 + (x + y) * 30], axis=-1).astype(
        np.uint8
    )
    rgba = np.concatenate(
        [np.full_like(rgb, 255), (26 + x * 50 + y * 17)[..., None].astype(np.uint8)],
        axis=-1,
    )
    top = np.array([0, 0, 1])
    results = [
        _case("primitive_2d_repeat", "box", "2d", rgb, top),
        _case("primitive_2d_uniform", "box", "2d", rgb, top, uniform=True),
        _case("primitive_2d_rgba_alpha", "box", "2d", rgba, top),
        _case("mesh_2d_uv", "mesh", "2d", rgb, top),
    ]
    cube = np.concatenate([np.roll(rgb, i, axis=2) + i * 3 for i in range(6)])
    for axis in range(3):
        for sign in (1, -1):
            normal = np.eye(3, dtype=int)[axis] * sign
            results.append(
                _case(f"cube_axis_{axis}_{sign}", "box", "cube", cube, normal)
            )
    print(
        json.dumps({"mujoco": mujoco.__version__, "results": results}, sort_keys=True)
    )


if __name__ == "__main__":
    main()
