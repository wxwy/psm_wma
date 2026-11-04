import numpy as np
from scipy.spatial.transform import Rotation

from tools.g2 import verify_robocasa_rgbd_pose as checker
from tools.g2.rgbd_pose import cache, source as src
from tools.g2.test_rgbd_pose_export import FakeReplay, bound


def test_static_float32_camera_rotation_is_not_reported_as_motion(tmp_path):
    raw, flat, source = bound(tmp_path)
    rotation = Rotation.from_euler('xyz', [-2.6178494833854566, 1.7480055403415324, 2.8816979303657675]).as_matrix().astype(np.float32)
    class Rotated(FakeReplay):
        def render(self, camera):
            sample = super().render(camera)
            sample['T_world_camera_gl'][:3, :3] = rotation
            sample['T_world_camera_cv'] = sample['T_world_camera_gl'] @ np.diag([1.,-1.,-1.,1.])
            return sample
    result = cache.export_episode(tmp_path/'out', source, [0,1,3], storage='uint16_mm', chunk_frames=2,
        recipe={'regression':'static_f32_pose'}, replay_factory=Rotated)
    report = checker.verify(result['directory'], replay=True, raw_root=raw, flat_root=flat,
        state_index_policy='frame_index', replay_factory=Rotated,
        rgb_reader=lambda ref, i: np.full((8,8,3), 7+i, dtype=np.uint8))
    motion = report['camera_pose_motion'][src.CAMERAS[0]]
    assert motion['changed'] is False
    assert motion['max_rotation_rad'] < 1e-7
