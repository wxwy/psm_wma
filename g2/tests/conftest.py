"""TEST_ONLY protocol fixtures, never evidence of genuine model execution."""
import json
from pathlib import Path
import pytest
from g2.io import write_json


def box(lo,hi):
    vertices=[[x,y,z] for x in (lo[0],hi[0]) for y in (lo[1],hi[1]) for z in (lo[2],hi[2])]
    faces=[[0,1,3],[0,3,2],[4,6,7],[4,7,5],[0,4,5],[0,5,1],
           [2,3,7],[2,7,6],[0,2,6],[0,6,4],[1,5,7],[1,7,3]]
    return vertices,faces


@pytest.fixture
def native_factory(tmp_path):
    def make(name="native",mode="oracle_diagnostic"):
        root=tmp_path/name;root.mkdir()
        def entity(i,kind,lo,hi,*,roots=(),floor=False,island=None):
            vertices,triangles=box(lo,hi)
            return {"id":"entity_"+str(i),"native_id":i,"room_uid":0 if kind=="object" else -1,
                    "kind":kind,"label":"unknown","source_instance_id":"","bbox_min":lo,"bbox_max":hi,
                    "vertices":vertices,"triangles":triangles,"root_affiliations":list(roots),
                    "floor_member":floor,"upper_member":not floor and kind=="object","island_id":island,
                    "adjacent_room_uids":[0],"wall_axis":"x" if kind=="wall" else None}
        entities=[entity(0,"floor",[-1,-1,-.2],[2,2,0],floor=True),
                  entity(1,"object",[1.5,.4,0],[1.7,.6,.3],roots=("entity_0","entity_2"),floor=True),
                  entity(2,"wall",[1.9,-1,0],[2,2,2]),
                  entity(3,"object",[.4,.4,0],[.6,.6,.2],roots=("entity_0",),floor=True,island="island_0_entity_3")]
        if mode=="perception":
            entities=[entities[1]];entities[0].update(root_affiliations=[],floor_member=False,
                upper_member=False,island_id=None)
        s={"schema":"nav_sg_spatial_snapshot_v1","scene_id":"TEST_ONLY_contract","source_sha256":"a"*64,
           "frame_id":0,"timestamp_ns":100,"world_frame":"map","native_build_source_sha256":"b"*64,
           "source_mode":mode,"geometry_source_mode":"ORACLE_GRID" if mode=="oracle_diagnostic" else "SENSOR_INCREMENTAL","completed_rgbd_observations":1 if mode=="perception" else 0,
           "object_frontend_status":"OBSERVED" if mode=="perception" else "ORACLE_ONLY",
           "bounds_min":[-1,-1,-.2],"bounds_max":[2,2,2],"color_voxel_leaf":.05,
           "grid":{"origin":[-1,-1,-.2],"resolution":.1,"dimensions":[30,30,22],"state_file":"grid_states.raw",
                   "state_order":"xyz_z_fastest","states":{"unknown":0,"free":1,"occupied":2}},
           "connection_distance":.3,"affiliations_complete":mode=="oracle_diagnostic",
           "surface_file":"surfaces.csv","rooms":[{"uid":0,"local_id":0,"center":[.5,.5,1],
                 "frame_axes":"world_axes","label":"unknown","footprint":[[1,1]]}],
           "entities":entities,"relations":[{"source":"room_0","target":"entity_1","type":"contains",
                                           "evidence":"native_room_query"}],
           "relation_status":"OBJECT_RELATIONS_NOT_OBSERVABLE"}
        (root/"grid_states.raw").write_bytes(bytes([0,1,2])*(30*30*22//3))
        write_json(root/"snapshot.json",s)
        rows=[(-.5,-.5,0,120,120,120,1,"entity_0"),
              (1.6,.5,.3,20,180,30,1,"entity_1"),
              (1.95,1,1,220,220,220,1,"entity_2"),
              (.5,.5,.2,200,20,30,1,"entity_3")]
        if mode=="perception":rows=[rows[1]]
        (root/"surfaces.csv").write_text("x,y,z,red,green,blue,color_valid,entity_id\n"+
            "".join(",".join(map(str,row))+"\n" for row in rows))
        (root/"SNAPSHOT_COMPLETE").write_text("nav_sg_spatial_snapshot_v1\n")
        return root,s
    return make
