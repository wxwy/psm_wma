"""Non-invasive F27 robot marker: room-frame projection and final PNG only."""
import hashlib
import json

from PIL import Image
import pytest

from g2.io import ContractError
from g2.views.robot_pose_marker import chassis_pose, overlay_final_top_views, project


def _meta():
    # 90-degree room rotation: room X=world Y, room Y=-world X.
    return {
        "axis": "floor_top",
        "coordinate_frame": "NATIVE_ROOM_REFERENCE",
        "reference_frame": {"origin_world": [10, 20, 0],
                            "axes_world": [[0, 1, 0], [-1, 0, 0], [0, 0, 1]]},
        "right_world": [0, 1, 0], "up_world": [-1, 0, 0],
        "uv_min_room": [-2, -2],
        "width": 420, "height": 400, "meters_per_pixel": .01,
    }


def _pose():
    return {
        "position_world": [10.5, 21, 0],
        "forward_world": [-1, 0, 0],
        "source_body": "mobilebase0_wheeled_base",
        "forward_axis": "body_local_positive_X",
    }


def test_projection_uses_real_room_axis_origin_and_flipped_image_row():
    x, y, dx, dy = project(_meta(), _pose())
    assert x == pytest.approx(299.5)
    assert y == pytest.approx(249.5)
    assert dx == pytest.approx(0)
    assert dy == pytest.approx(-1)


def test_final_top_only_stamps_png_and_preserves_inner_raw_geometry_and_sides(tmp_path):
    stage = tmp_path / "state"
    top = stage / "sixview/floor_top.png"
    side = stage / "sixview/minus_X.png"
    raw = stage / "g2_original_gpu/rooms/0/floor_top"
    top.parent.mkdir(parents=True)
    raw.mkdir(parents=True)
    Image.new("RGB", (420, 400), "white").save(top)
    Image.new("RGB", (420, 400), (21, 31, 41)).save(side)
    Image.new("RGB", (420, 400), (63, 71, 82)).save(raw / "rgb.png")
    (raw / "view.json").write_text(json.dumps(_meta()))
    (raw / "geometry.npz").write_bytes(b"unmodified geometry evidence")
    data = {"views": [
        {"native_view": "rooms/0/floor_top", "rgb_file": "sixview/floor_top.png",
         "sha256": hashlib.sha256(top.read_bytes()).hexdigest()},
        {"native_view": "rooms/0/minus_X", "rgb_file": "sixview/minus_X.png",
         "sha256": hashlib.sha256(side.read_bytes()).hexdigest()},
    ]}
    (stage / "direct_color_views.json").write_text(json.dumps(data))
    raw_hash = hashlib.sha256((raw / "rgb.png").read_bytes()).hexdigest()
    side_hash = hashlib.sha256(side.read_bytes()).hexdigest()
    before_top = top.read_bytes()
    summary = overlay_final_top_views(stage, _pose())
    assert summary["drawn_views"] == 1
    assert summary["eligible_views"] == 1
    assert top.read_bytes() != before_top
    assert hashlib.sha256(side.read_bytes()).hexdigest() == side_hash
    assert hashlib.sha256((raw / "rgb.png").read_bytes()).hexdigest() == raw_hash
    assert (raw / "geometry.npz").read_bytes() == b"unmodified geometry evidence"
    after = json.loads((stage / "direct_color_views.json").read_text())
    assert after["views"][0]["sha256"] == hashlib.sha256(top.read_bytes()).hexdigest()
    assert after["views"][1]["sha256"] == side_hash
    with Image.open(top) as image:
        assert image.getpixel((300, 250))[2] > image.getpixel((300, 250))[0]
        assert image.getpixel((300, 230))[2] > image.getpixel((300, 230))[0]
        assert image.getpixel((80, 80)) == (255, 255, 255)


def test_missing_valid_floor_top_or_outside_pose_rejected(tmp_path):
    with pytest.raises(ContractError, match="invalid projected chassis direction"):
        project(_meta(), dict(_pose(), forward_world=[0, 0, 1]))
    with pytest.raises(ContractError, match="projection"):
        project(dict(_meta(), axis="minus_X"), _pose())
    with pytest.raises(ContractError, match="projection"):
        project(dict(_meta(), meters_per_pixel=0), _pose())


def test_default_on_cli_and_config_sensitive_f27_reuse(tmp_path):
    from g2.offline.atomic_6views_run import parser, stage, _stage_mark

    assert parser().parse_args(["plan"]).robot_pose_marker is True
    assert parser().parse_args(["plan", "--no-robot-pose-marker"]).robot_pose_marker is False
    row = {"source_fingerprint": "f" * 64, "task_class": "OpenDrawer", "episode_id": 0}
    work = tmp_path / "work"
    work.mkdir()
    calls = []

    def build(path):
        path.mkdir()
        (path / "episode_receipt.json").write_text("{}")
        calls.append(True)

    stage(work, "f27", row, build, required=("episode_receipt.json",),
          robot_pose_marker=True)
    assert _stage_mark(work / "f27", "f27", row, robot_pose_marker=True)
    stage(work, "f27", row, build, required=("episode_receipt.json",),
          robot_pose_marker=True)
    assert len(calls) == 1
    assert not _stage_mark(work / "f27", "f27", row, robot_pose_marker=False)
    stage(work, "f27", row, build, required=("episode_receipt.json",),
          robot_pose_marker=False)
    assert len(calls) == 2


def test_real_mujoco_chassis_frame_not_robot_root_anchor():
    mujoco = pytest.importorskip("mujoco")
    xml = """<mujoco><worldbody>
      <body name="robot0_base" pos="10 10 0">
        <body name="mobilebase0_support" pos="-2.5 3 .55">
          <geom type="sphere" size=".04"/>
        </body>
        <body name="mobilebase0_wheeled_base" pos="-2 3 .15" quat="0 0 0 1">
          <joint name="mobilebase0_joint_mobile_forward" type="slide" axis="0 1 0"/>
          <geom type="box" size=".1 .2 .1"/>
        </body>
      </body>
    </worldbody></mujoco>"""
    model = mujoco.MjModel.from_xml_string(xml)
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    pose = chassis_pose(model, data)
    assert pose["position_world"] == pytest.approx([8, 13, .15])
    assert pose["forward_world"][:2] == pytest.approx([-1, 0])
    assert pose["forward_axis"] == "body_local_positive_X"
    arm_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "mobilebase0_support")
    arm_xy = data.xpos[arm_id, :2]
    base_xy = pose["position_world"][:2]
    # Physical front (wheels -> arm mount) is NOT the named forward slide DOF.
    assert sum((arm_xy[i] - base_xy[i]) * pose["forward_world"][i]
               for i in range(2)) > 0
    joint_id = mujoco.mj_name2id(
        model, mujoco.mjtObj.mjOBJ_JOINT, "mobilebase0_joint_mobile_forward")
    assert model.jnt_axis[joint_id].tolist() == [0, 1, 0]
