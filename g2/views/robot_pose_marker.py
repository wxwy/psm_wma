"""Simulation-only robot chassis pose stamp on the final G2 floor-top PNG.

Operates after the accepted pixel-exact raw View comparison, not inside the
surface renderer. Native RGB, geometry, camera paths and SG remain untouched.
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

from g2.io import ContractError, read_json, write_json


MARKER_STYLES = ("classic", "game_arrow")
DEFAULT_MARKER_STYLE = "game_arrow"


def chassis_pose(model, data):
    """Use the *actual* Omron wheel-base frame, not robot0_base (XML anchor)."""
    import mujoco

    body_id = mujoco.mj_name2id(
        model, mujoco.mjtObj.mjOBJ_BODY, "mobilebase0_wheeled_base")
    if body_id < 0:
        raise ContractError("robot pose marker requires mobilebase0_wheeled_base")
    position = [float(x) for x in data.xpos[body_id]]
    # RoboCasa PandaOmron's PHYSICAL FRONT points from the wheel chassis
    # toward the arm mount: body local +X (wheel body is mounted at x=-0.20).
    # Do NOT use joint_mobile_forward here: its axis is +Y in recorded MJCF,
    # and describes a translation DOF, not the front of the physical robot.
    rotation = data.xmat[body_id].reshape(3, 3)
    forward = [float(x) for x in rotation[:, 0]]
    if not all(math.isfinite(v) for v in position + forward):
        raise ContractError("non-finite chassis pose")
    if math.hypot(forward[0], forward[1]) < 1e-8:
        raise ContractError("chassis forward direction has no ground projection")
    return {
        "position_world": position,
        "forward_world": forward,
        "source_body": "mobilebase0_wheeled_base",
        "forward_axis": "body_local_positive_X",
    }


def project(meta, pose):
    """World pose -> exact floor_top image coordinates, including flipped row."""
    if meta.get("axis") != "floor_top" or meta.get("coordinate_frame") != "NATIVE_ROOM_REFERENCE":
        raise ContractError("robot marker requires native room floor_top projection")
    frame = meta["reference_frame"]
    origin = frame["origin_world"]
    right, up = meta["right_world"], meta["up_world"]
    uv_min = meta["uv_min_room"]
    mpp = float(meta["meters_per_pixel"])
    width, height = int(meta["width"]), int(meta["height"])
    p = [float(a) - float(b) for a, b in zip(pose["position_world"], origin)]
    direction = [float(x) for x in pose["forward_world"]]
    if (len(p) != 3 or len(direction) != 3 or len(right) != 3 or len(up) != 3
            or len(uv_min) != 2 or not 0 < mpp < 1 or width < 1 or height < 1
            or not all(math.isfinite(float(x)) for x in p + direction + list(uv_min))):
        raise ContractError("invalid pose or metric floor-top projection")
    dot = lambda a, b: sum(float(x) * float(y) for x, y in zip(a, b))
    col = (dot(p, right) - float(uv_min[0])) / mpp - .5
    row = height - .5 - (dot(p, up) - float(uv_min[1])) / mpp
    dx, dy = dot(direction, right), -dot(direction, up)
    size = math.hypot(dx, dy)
    if size < 1e-8 or not all(math.isfinite(x) for x in (col, row, dx, dy)):
        raise ContractError("invalid projected chassis direction")
    return col, row, dx / size, dy / size


def _stamp_classic(image, x, y, dx, dy):
    """Preserve the old engineering-style blue dot and heading arrow."""
    draw = ImageDraw.Draw(image)
    tip = (x + 23 * dx, y + 23 * dy)
    # Ground-facing map marker: white halo, blue arrow and blue center dot.
    draw.line([(x, y), tip], fill=(255, 255, 255), width=9)
    draw.line([(x, y), tip], fill=(22, 103, 217), width=5)
    side_x, side_y = -dy, dx
    wing_a = (tip[0] - 9 * dx + 6 * side_x, tip[1] - 9 * dy + 6 * side_y)
    wing_b = (tip[0] - 9 * dx - 6 * side_x, tip[1] - 9 * dy - 6 * side_y)
    draw.line([wing_a, tip, wing_b], fill=(255, 255, 255), width=8, joint="curve")
    draw.line([wing_a, tip, wing_b], fill=(22, 103, 217), width=4, joint="curve")
    draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=(255, 255, 255))
    draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(22, 103, 217))


def _stamp_game_arrow(image, x, y, dx, dy):
    """Antialiased red chevron with a notched tail, like a game minimap marker.

    Draw only a small local patch; the map image itself is never resampled.
    The image-space heading (dx, dy) remains the physical chassis +X axis.
    """
    scale = 4
    radius = 29
    center = radius * scale
    overlay = Image.new("RGBA", (2 * radius * scale, 2 * radius * scale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    # Coordinates are (along heading, perpendicular to heading). A recessed
    # rear notch makes the silhouette a concave game-style chevron, not a kite.
    shape = ((22, 0), (-16, -11), (-6, 0), (-16, 11))
    def points(offset_x=0, offset_y=0):
        return [((radius + along * dx - across * dy + offset_x) * scale,
                 (radius + along * dy + across * dx + offset_y) * scale)
                for along, across in shape]
    # Understated drop shadow and dark red outline are visible on white floors.
    draw.polygon(points(1.0, 1.5), fill=(50, 34, 32, 80))
    polygon = points()
    draw.polygon(polygon, fill=(232, 52, 39, 255))
    draw.line(polygon + [polygon[0]], fill=(151, 39, 33, 255),
              width=scale, joint="curve")
    patch = overlay.resize((2 * radius, 2 * radius), Image.Resampling.LANCZOS)
    image.paste(patch, (round(x) - radius, round(y) - radius), patch)


def _stamp(image, x, y, dx, dy, *, style=DEFAULT_MARKER_STYLE):
    if style == "classic":
        _stamp_classic(image, x, y, dx, dy)
    elif style == "game_arrow":
        _stamp_game_arrow(image, x, y, dx, dy)
    else:
        raise ContractError("unsupported robot pose marker style: " + str(style))


def overlay_final_top_views(stage, pose, *, style=DEFAULT_MARKER_STYLE):
    """Stamp only exported top RGBs; do not modify g2_original_gpu or masks."""
    from g2.offline.native_transport import sha_file

    if style not in MARKER_STYLES:
        raise ContractError("unsupported robot pose marker style: " + str(style))
    stage = Path(stage)
    report = read_json(stage / "direct_color_views.json")
    total, drawn, details = 0, 0, []
    for view in report["views"]:
        native = view["native_view"]
        if Path(native).name != "floor_top":
            continue
        total += 1
        meta = read_json(stage / "g2_original_gpu" / native / "view.json")
        rel = Path(view["rgb_file"])
        if rel.is_absolute() or ".." in rel.parts or rel.parts[0] != "sixview":
            raise ContractError("robot marker refuses unsafe top view path")
        target = stage / rel
        with Image.open(target) as loaded:
            image = loaded.convert("RGB")
        if image.size != (meta["width"], meta["height"]):
            raise ContractError("robot marker projection differs from final RGB dimensions")
        x, y, dx, dy = project(meta, pose)
        inside = 0 <= x < image.width and 0 <= y < image.height
        if inside:
            _stamp(image, x, y, dx, dy, style=style)
            image.save(target)
            view["sha256"] = sha_file(target)
            drawn += 1
        details.append({
            "native_view": native, "rgb_file": str(rel),
            "pixel_xy": [round(x, 3), round(y, 3)],
            "marker_drawn": inside,
        })
    if total == 0:
        raise ContractError("cannot stamp robot: no floor_top RGB was exported")
    if drawn == 0:
        raise ContractError("robot chassis is outside every exported floor_top view")
    marker = {
        "enabled": True, "style": style,
        "drawn_views": drawn, "eligible_views": total,
        "pose": pose, "views": details,
        "stage": "AFTER_RAW_PIXEL_EXACT_VALIDATION",
        "affects": "FINAL_FLOOR_TOP_RGB_PNG_ONLY",
    }
    report["robot_pose_marker"] = marker
    write_json(stage / "direct_color_views.json", report)
    return marker
