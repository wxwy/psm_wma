"""Simulation-only robot chassis pose stamp on the final G2 floor-top PNG.

Operates after the accepted pixel-exact raw View comparison, not inside the
surface renderer. Native RGB, geometry, camera paths and SG remain untouched.
"""
from __future__ import annotations

import math
import hashlib
from dataclasses import dataclass, asdict
from pathlib import Path

from PIL import Image, ImageDraw

from g2.io import ContractError, canonical, read_json, write_json


MARKER_STYLES = ("classic", "game_arrow")
DEFAULT_MARKER_STYLE = "game_arrow"
# Appearance changes must invalidate existing F27 overlay stage receipts.
MARKER_RECIPE_VERSION = "g2_robot_marker_appearance_v3"


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




@dataclass(frozen=True)
class MarkerAppearance:
    """One appearance contract for BOTH classic and game_arrow markers.

    Changing length scales the whole silhouette, including its width and notch;
    stroke width remains independently adjustable in final-image pixels.
    """
    outline_enabled: bool = True
    outline_width_px: float = 1.0
    outline_color: str = "#E1E5EA"  # gray-white
    fill_color: str = "#454B53"     # dark gray
    length_px: float = 26.6         # accepted game-arrow silhouette (70/80)
    relief: str = "raised"          # flat | raised (2.5D illusion)

    def __post_init__(self):
        if type(self.outline_enabled) is not bool:
            raise ContractError("marker outline flag must be boolean")
        for name, lower, upper in (("outline_width_px", 0, 8),
                                   ("length_px", 8, 128)):
            val = getattr(self, name)
            if type(val) not in (int, float) or not math.isfinite(val) or not lower <= val <= upper:
                raise ContractError("invalid robot marker "+name)
        import re
        for name in ("outline_color", "fill_color"):
            if not isinstance(getattr(self, name), str) or not re.fullmatch(
                    r"#[0-9a-fA-F]{6}",getattr(self, name)):
                raise ContractError("invalid robot marker "+name+"; expected #RRGGBB")
        if self.relief not in ("flat", "raised"):
            raise ContractError("robot marker relief must be flat or raised")

    def to_dict(self):
        return asdict(self)


def add_appearance_args(parser):
    """Use the SAME CLI contract in direct F27 and batch F27."""
    import argparse
    parser.add_argument("--robot-pose-marker-outline", action=argparse.BooleanOptionalAction,
                        default=True, help="enable gray-white marker outline (default: on)")
    parser.add_argument("--robot-pose-marker-outline-width", type=float, default=1.0,
                        help="marker outline thickness in final PNG pixels")
    parser.add_argument("--robot-pose-marker-outline-color", default="#E1E5EA",
                        help="marker outline color #RRGGBB")
    parser.add_argument("--robot-pose-marker-fill-color", default="#454B53",
                        help="marker fill color #RRGGBB")
    parser.add_argument("--robot-pose-marker-length-px", type=float, default=26.6,
                        help="marker front-to-rear size in pixels; all other dimensions scale with it")
    parser.add_argument("--robot-pose-marker-relief", choices=("flat","raised"), default="raised",
                        help="2D flat or subtle raised/2.5D shading")


def appearance_from_args(args):
    return MarkerAppearance(
        outline_enabled=args.robot_pose_marker_outline,
        outline_width_px=args.robot_pose_marker_outline_width,
        outline_color=args.robot_pose_marker_outline_color,
        fill_color=args.robot_pose_marker_fill_color,
        length_px=args.robot_pose_marker_length_px,
        relief=args.robot_pose_marker_relief)


def appearance_cli_args(appearance):
    a=appearance
    return [
        "--robot-pose-marker-outline" if a.outline_enabled else "--no-robot-pose-marker-outline",
        "--robot-pose-marker-outline-width",str(a.outline_width_px),
        "--robot-pose-marker-outline-color",a.outline_color,
        "--robot-pose-marker-fill-color",a.fill_color,
        "--robot-pose-marker-length-px",str(a.length_px),
        "--robot-pose-marker-relief",a.relief,
    ]


def marker_cache_key(style, appearance):
    if style not in MARKER_STYLES or not isinstance(appearance, MarkerAppearance):
        raise ContractError("invalid robot marker style/appearance")
    return hashlib.sha256(canonical(dict(
        recipe=MARKER_RECIPE_VERSION, style=style, appearance=appearance.to_dict()))).hexdigest()


def _rgb(hex_color):
    return tuple(bytes.fromhex(hex_color[1:]))


def _lighter(rgb, ratio=0.55):
    return tuple(round(c*(1-ratio)+255*ratio) for c in rgb)


def _darker(rgb, ratio=0.65):
    return tuple(round(c*(1-ratio)) for c in rgb)


def _stamp_game_arrow(draw, xy, unit, appearance, scale):
    """Notched chevron. Kept at accepted 26.6 px length and 17.6 px width."""
    dx,dy=unit
    length_factor=appearance.length_px/26.6
    base=((15.4,0),(-11.2,-8.8),(-4.2,0),(-11.2,8.8))
    def pt(t, shift=(0.,0.)):
        along, across = t
        return ((xy[0] + along*length_factor*dx - across*length_factor*dy + shift[0])*scale,
                (xy[1] + along*length_factor*dy + across*length_factor*dx + shift[1])*scale)
    poly=[pt(v) for v in base]
    fill=_rgb(appearance.fill_color)
    if appearance.relief=="raised":
        draw.polygon([pt(v,(1.1*length_factor,1.45*length_factor)) for v in base],
                     fill=(28,31,36,80))
    draw.polygon(poly, fill=(*fill,255))
    if appearance.relief=="raised":
        # Inner bevel: illuminated leading/upper edge and a dark opposite edge.
        glow=_lighter(fill, .54); shade=_darker(fill, .53)
        draw.line([poly[1],poly[0]], fill=(*glow,190),
                  width=max(1,round(1.75*length_factor*scale)), joint="curve")
        draw.line([poly[0],poly[3]], fill=(*shade,180),
                  width=max(1,round(1.75*length_factor*scale)), joint="curve")
        draw.line([poly[3],poly[2]], fill=(*shade,155),
                  width=max(1,round(1.30*length_factor*scale)), joint="curve")
    if appearance.outline_enabled and appearance.outline_width_px>0:
        draw.line(poly+[poly[0]], fill=(*_rgb(appearance.outline_color),255),
                  width=max(1,round(appearance.outline_width_px*scale)), joint="curve")


def _stamp_classic(draw, xy, unit, appearance, scale):
    """Dot-and-arrow classic silhouette sharing EXACTLY the same styling knobs."""
    dx,dy=unit
    factor=appearance.length_px/30.0
    x,y=xy
    def pt(along, across=0, shift=(0.,0.)):
        return ((x+(along*dx-across*dy)*factor+shift[0])*scale,
                (y+(along*dy+across*dx)*factor+shift[1])*scale)
    p0,p1=pt(0),pt(23)
    a,b=pt(14,6),pt(14,-6)
    fill=_rgb(appearance.fill_color)
    w=max(1,round(4*factor*scale))
    radius=5*factor*scale
    ox,oy=appearance.outline_width_px*scale,appearance.outline_width_px*scale
    if appearance.relief=="raised":
        shift=(1.1*factor,1.5*factor)
        s=[pt(0,shift=shift),pt(23,shift=shift)]
        draw.line(s,fill=(28,31,36,80),width=w+round(2*scale))
        sh=pt(0,shift=shift)
        draw.ellipse((sh[0]-radius,sh[1]-radius,
                      sh[0]+radius,sh[1]+radius),fill=(28,31,36,80))
    if appearance.outline_enabled and appearance.outline_width_px>0:
        border=(*_rgb(appearance.outline_color),255)
        draw.line([p0,p1], fill=border, width=w+round(2*ox))
        draw.line([a,p1,b],fill=border,width=w+round(2*ox),joint="curve")
        draw.ellipse((p0[0]-radius-ox,p0[1]-radius-oy,
                      p0[0]+radius+ox,p0[1]+radius+oy),fill=border)
    draw.line([p0,p1],fill=(*fill,255),width=w)
    draw.line([a,p1,b],fill=(*fill,255),width=w,joint="curve")
    draw.ellipse((p0[0]-radius,p0[1]-radius,p0[0]+radius,p0[1]+radius),
                 fill=(*fill,255))
    if appearance.relief=="raised":
        bright=_lighter(fill,.55)
        draw.line([pt(1,1.0),pt(17,1.0)], fill=(*bright,200),
                  width=max(1,round(scale*factor)))


def _stamp(image, x, y, dx, dy, *, style=DEFAULT_MARKER_STYLE,
           appearance=MarkerAppearance()):
    """Draw antialiased marker on a cropped RGBA layer; never resample the map."""
    if style not in MARKER_STYLES or not isinstance(appearance, MarkerAppearance):
        raise ContractError("unsupported robot marker style or appearance")
    if not all(math.isfinite(v) for v in (x,y,dx,dy)):
        raise ContractError("non-finite marker projection")
    norm=math.hypot(dx,dy)
    if norm < 1e-8:
        raise ContractError("zero marker heading")
    unit=(dx/norm,dy/norm)
    scale=4
    radius=math.ceil(appearance.length_px*1.55+appearance.outline_width_px+8)
    patch=Image.new("RGBA",(radius*scale*2,radius*scale*2),(0,0,0,0))
    draw=ImageDraw.Draw(patch,"RGBA")
    xy=(float(radius),float(radius))
    if style=="game_arrow":
        _stamp_game_arrow(draw,xy,unit,appearance,scale)
    else:
        _stamp_classic(draw,xy,unit,appearance,scale)
    patch=patch.resize((radius*2,radius*2),Image.Resampling.LANCZOS)
    image.paste(patch,(round(x)-radius,round(y)-radius),patch)

def overlay_final_top_views(stage, pose, *, style=DEFAULT_MARKER_STYLE,
                            appearance=MarkerAppearance()):
    """Stamp only exported top RGBs; do not modify g2_original_gpu or masks."""
    from g2.offline.native_transport import sha_file

    appearance_key=marker_cache_key(style, appearance)
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
            _stamp(image, x, y, dx, dy, style=style, appearance=appearance)
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
        "recipe_version": MARKER_RECIPE_VERSION,
        "appearance": appearance.to_dict(), "appearance_sha256": appearance_key,
        "drawn_views": drawn, "eligible_views": total,
        "pose": pose, "views": details,
        "stage": "AFTER_RAW_PIXEL_EXACT_VALIDATION",
        "affects": "FINAL_FLOOR_TOP_RGB_PNG_ONLY",
    }
    report["robot_pose_marker"] = marker
    write_json(stage / "direct_color_views.json", report)
    return marker
