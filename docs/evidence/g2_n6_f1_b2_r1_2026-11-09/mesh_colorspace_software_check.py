"""Three own mesh material cases under forced CPU llvmpipe, no house inputs."""
import argparse
import json
import os
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",required=True)
    args=parser.parse_args()
    for key,value in {"MUJOCO_GL":"egl","LIBGL_ALWAYS_SOFTWARE":"1","GALLIUM_DRIVER":"llvmpipe"}.items():
        if os.environ.get(key)!=value:raise RuntimeError("Required CPU environment: "+key+"="+value)
    sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
    import mujoco
    import numpy as np
    from PIL import Image
    from OpenGL import GL
    from g2.io import ContractError,write_json
    from g2.sim.prescan import export
    from g2.sim.source_geometry import load_model,primitive_mesh,surface_colors
    if mujoco.__version__!="3.3.7":raise RuntimeError("Reference requires MuJoCo3.3.7")
    root=Path(args.output).resolve();root.mkdir(parents=True,exist_ok=False)
    source=root/"own_source";source.mkdir()
    Image.fromarray(np.full((8,8,3),128,np.uint8)).save(source/"albedo.png")
    vertices,faces=primitive_mesh("box",np.asarray([.4,.4,.4]))
    (source/"mesh.obj").write_text(''.join('v %.17g %.17g %.17g\n'%tuple(v) for v in vertices)+
        'vt .5 .5\n'+''.join('f %d/1 %d/1 %d/1\n'%tuple(face+1) for face in faces))
    metadata=source/"roles.json"
    write_json(metadata,{"schema":"g2_sim_prescan_v1","scene_id":"TEST_ONLY_R1_SRGB_MESH",
        "geoms":{"g":{"role":"visual","source_kind":"mjcf","geom_name":"g",
        "classification_reason":"Own authored software reference mesh"}}})
    results=[];renderer_name=None
    for colorspace in ("sRGB","linear","default"):
        extra='' if colorspace=="default" else ' colorspace="'+colorspace+'"'
        xml=source/(colorspace+'.xml')
        xml.write_text('''<mujoco><visual><headlight ambient="0 0 0" diffuse="0 0 0" specular="0 0 0"/></visual>
          <asset><mesh name="mesh" file="mesh.obj"/><texture name="t" type="2d" file="albedo.png"'''+extra+'''/>
          <material name="m" texture="t" rgba="1 1 1 1" emission="1" specular="0"/></asset>
          <worldbody><geom name="g" type="mesh" mesh="mesh" material="m"/>
          <camera name="top" pos="0 0 3" fovy="45"/></worldbody></mujoco>''')
        model,_=load_model(xml);data=mujoco.MjData(model);mujoco.mj_forward(model,data)
        with mujoco.Renderer(model,height=128,width=128) as renderer:
            renderer_name=GL.glGetString(GL.GL_RENDERER).decode()
            if 'llvmpipe' not in renderer_name.lower():raise RuntimeError("Not CPU llvmpipe")
            renderer.update_scene(data,camera="top");renderer.scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW]=0
            GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT,[0,0,0,1])
            observed=renderer.render()[64,64].tolist()
        colors,valid,appearance,reasons=surface_colors(model,0,"mesh",np.asarray([0]),
            np.asarray([[.2,.3,.5]]),with_diagnostics=True)
        if colorspace=="sRGB":
            assert not valid[0] and reasons[0]!=0 and "sRGB" in appearance["reason"]
            assert max(abs(value-55) for value in observed)<=1
            try:export(xml,metadata,root/(colorspace+"_strict"),spacing=.3)
            except ContractError:pass
            else:raise AssertionError("Strict sRGB mesh export did not reject")
            candidate=export(xml,metadata,root/(colorspace+"_partial"),spacing=.3,allow_partial_color=True)
            assert candidate["status"]=="PARTIAL_COLOR" and candidate["source_audit"]["color_valid_points"]==0
        else:
            assert valid[0] and reasons[0]==0
            np.testing.assert_array_equal(np.rint(colors[0,:3]*255),[128,128,128])
            assert max(abs(value-128) for value in observed)<=1
            candidate=export(xml,metadata,root/(colorspace+"_strict"),spacing=.3)
            assert candidate["status"]=="COMPLETE"
        results.append({"colorspace":colorspace,"rendered_rgb":observed,"sample_valid":bool(valid[0]),
            "sample_rgb_when_valid":np.rint(colors[0,:3]*255).astype(int).tolist() if valid[0] else None,
            "reason_code":int(reasons[0]),"export_status":candidate["status"],
            "training_ready":candidate["training_ready"]})
    report={"status":"PASS","scope":"THREE_OWN_MESH_CASES_NOT_REAL_LAYOUT_OR_OTHER_PRIMITIVES",
        "renderer":renderer_name,"mujoco":mujoco.__version__,"cases":results,"GPU_or_private_inputs":False}
    write_json(root/"mesh_software_reference.json",report)
    print(json.dumps(report,sort_keys=True))


if __name__=="__main__":main()
