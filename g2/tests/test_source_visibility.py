"""Shared F27 display-only derivative tests, independent of B1K source."""
import unittest

import numpy as np
from g2.views import source_visibility as source


class SharedSourceVisibilityTests(unittest.TestCase):
    def setUp(self):
        self.rgb=np.full((11,11,3),200,dtype=np.uint8)
        self.geometry=np.zeros((11,11),dtype=bool)
        self.geometry[2:9,2:9]=True
        self.depth=np.full((11,11),np.nan,dtype=float)
        self.depth[self.geometry]=.4
    def test_actual_source_depth_step_edge_without_editing_rgb(self):
        old=self.rgb.copy()
        self.depth[3:9,5:9]=.8
        out,e=source.source_depth_outline(self.rgb,self.depth,self.geometry)
        self.assertTrue(np.any(out[3:8,5]<old[3:8,5]))
        np.testing.assert_array_equal(self.rgb,old)
        self.assertGreater(e["source_depth_or_silhouette_edge_pixels"],0)
        self.assertFalse(e["geometry_semantics_modified"])
    def test_flat_surface_keeps_interior_unchanged(self):
        out,e=source.source_depth_outline(self.rgb,self.depth,self.geometry)
        np.testing.assert_array_equal(out[4:7,4:7],self.rgb[4:7,4:7])
        self.assertTrue(e["display_only"])
    def test_source_door_original_mesh_even_behind_wall_drawn(self):
        x=[.31,.61,.61,.31]
        y=[.31,.31,.35,.35]
        verts=np.asarray([[a,b,.7] for a,b in zip(x,y)],float)
        old=self.rgb.copy()
        out,e=source.source_part_silhouettes(
            self.rgb,[{"kind":"door","vertices_world":verts}],
            axis="floor_top",frame_origin_world=[0,0,0],
            frame_axes_world=np.eye(3),low_room=[0,0,0],
            high_room=[1,1,1],mpp=.1)
        self.assertEqual(e["source_part_silhouettes_drawn"]["door"],1)
        self.assertGreater(int(np.sum(np.any(out!=old,axis=-1))),3)
        np.testing.assert_array_equal(self.rgb,old)
    def test_window_alternate_class_source(self):
        verts=np.asarray([[.2,.2,.2],[.8,.2,.2],[.8,.2,.7],[.2,.2,.7]])
        out,e=source.source_part_silhouettes(
            self.rgb,[{"kind":"window","vertices_world":verts}],
            axis="+Y",frame_origin_world=[0,0,0],frame_axes_world=np.eye(3),
            low_room=[0,0,0],high_room=[1,1,1],mpp=.1)
        self.assertEqual(e["source_part_silhouettes_drawn"]["window"],1)
    def test_geometry_nonfinite_fail_closed(self):
        d=self.depth.copy();d[2,2]=np.nan
        with self.assertRaises(source.SourceVisibilityError):
            source.source_depth_outline(self.rgb,d,self.geometry)
    def test_untrusted_source_geometry_rejected(self):
        with self.assertRaises(source.SourceVisibilityError):
            source.source_part_silhouettes(
                self.rgb,[{"kind":"door","vertices_world":[[float("nan"),0,0],[1,0,0]]}],
                axis="floor_top",frame_origin_world=[0,0,0],
                frame_axes_world=np.eye(3),low_room=[0,0,0],
                high_room=[1,1,1],mpp=.1)

if __name__=="__main__":
    unittest.main()
