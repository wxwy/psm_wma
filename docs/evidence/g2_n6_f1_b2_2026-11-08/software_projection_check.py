"""Own sources and forced llvmpipe only; no GPU or external scene inputs."""
import argparse
import json
import os
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",required=True)
    args=parser.parse_args()
    for key,value in {"MUJOCO_GL":"egl","LIBGL_ALWAYS_SOFTWARE":"1","GALLIUM_DRIVER":"llvmpipe"}.items():
        if os.environ.get(key)!=value:raise RuntimeError("Required CPU software renderer environment: "+key+"="+value)
    root=Path(args.output).resolve();root.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
    import mujoco
    import numpy as np
    from PIL import Image
    from OpenGL import GL
    from g2.sim.source_geometry import surface_colors
    if mujoco.__version__!="3.3.7":raise RuntimeError("Unverified MuJoCo reference version")
    grid=np.asarray([[[20+x*25,30+y*23,15+(x+y)*12] for x in range(8)] for y in range(8)],np.uint8)
    Image.fromarray(grid).save(root/"grid.png")
    faces=np.asarray([np.clip(grid.astype(int)+[face*8,face*5,face*9],0,255).astype(np.uint8) for face in range(6)])
    Image.fromarray(np.concatenate(faces)).save(root/"cube.png")
    Image.fromarray(np.tile([0,0,255],(8,8,1)).astype(np.uint8)).save(root/"other.png")
    Image.fromarray(np.tile([255,0,0,0],(8,8,1)).astype(np.uint8)).save(root/"alpha.png")
    axes=[("+Z",[0,0,1],[1,0,0],[0,1,0]),("-Z",[0,0,-1],[-1,0,0],[0,1,0]),
          ("+X",[1,0,0],[0,1,0],[0,0,1]),("-X",[-1,0,0],[0,-1,0],[0,0,1]),
          ("+Y",[0,1,0],[-1,0,0],[0,0,1]),("-Y",[0,-1,0],[1,0,0],[0,0,1])]
    def numbers(values):return " ".join(str(value) for value in values)
    cameras="".join('<camera name="c%d" pos="%s" xyaxes="%s" fovy="45"/>'%
        (i,numbers(np.asarray(normal)*3),numbers([*right,*up])) for i,(_,normal,right,up) in enumerate(axes))
    variants=[("2d",uniform,repeat,False) for uniform in (False,True) for repeat in ("1 1","2 3")]
    variants += [("cube",uniform,repeat,False) for uniform in (False,True) for repeat in ("1 1","7 11")]
    variants += [("2d",False,"1 1",True)]
    report=[];renderer_name=None;size=np.asarray([.8,.7,.25]);height=width=128
    pixel_indices=np.asarray([(u,v) for v in (58,62,66,70) for u in (58,62,66,70)])
    for number,(texture,uniform,repeat,dual_role) in enumerate(variants):
        texture_file='file="grid.png" colorspace="linear"' if texture=="2d" else 'file="cube.png" gridsize="6 1" gridlayout="RLUDFB"'
        material=('texture="t"' if not dual_role else '')
        layers='<layer role="rgb" texture="t"/><layer role="rgba" texture="other"/>' if dual_role else ''
        xml=f'''<mujoco><visual><headlight ambient="0 0 0" diffuse="0 0 0" specular="0 0 0"/></visual>
          <asset><texture name="t" type="{texture}" {texture_file}/><texture name="other" type="2d" file="other.png"/>
          <material name="m" {material} rgba="1 1 1 1" emission="1" specular="0" reflectance="0"
            texuniform="{str(uniform).lower()}" texrepeat="{repeat}">{layers}</material></asset><worldbody>
          <geom name="g" type="box" size=".8 .7 .25" material="m"/>{cameras}</worldbody></mujoco>'''
        path=root/('model_%d.xml'%number);path.write_text(xml)
        model=mujoco.MjModel.from_xml_path(str(path));data=mujoco.MjData(model);mujoco.mj_forward(model,data)
        with mujoco.Renderer(model,height=height,width=width) as renderer:
            renderer_name=GL.glGetString(GL.GL_RENDERER).decode()
            if "llvmpipe" not in renderer_name.lower():raise RuntimeError("Not the required CPU llvmpipe renderer")
            for camera,(label,normal,right,up) in enumerate(axes):
                renderer.update_scene(data,camera='c%d'%camera)
                renderer.scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW]=0
                GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT,[0,0,0,1])
                image=renderer.render()
                normal=np.asarray(normal);right=np.asarray(right);up=np.asarray(up)
                extent=float(np.abs(normal)@size);distance=3-extent
                focal=.5*height/np.tan(np.deg2rad(float(model.cam_fovy[camera]))/2)
                horizontal=(pixel_indices[:,0]+.5-width/2)*distance/focal
                vertical=(height/2-pixel_indices[:,1]-.5)*distance/focal
                points=normal[None]*extent+horizontal[:,None]*right+vertical[:,None]*up
                colors,valid,_,reasons=surface_colors(model,0,"box",np.zeros(len(points),int),
                    np.tile([1.,0.,0.],(len(points),1)),local_points=points,with_diagnostics=True)
                if not np.all(valid):raise RuntimeError("Unexpected unknown reference point: "+str(reasons))
                observed=image[pixel_indices[:,1],pixel_indices[:,0]].astype(int)
                expected=np.rint(np.clip(colors[:,:3],0,1)*255).astype(int)
                error=int(np.max(np.abs(observed-expected)))
                report.append({"texture":texture,"texuniform":uniform,"texrepeat":repeat,"dual_rgb_rgba_roles":dual_role,
                    "face":label,"points":len(points),"max_rgb_byte_error":error})
                if error>2:
                    (root/'failed_comparison.json').write_text(json.dumps({"case":report[-1],"observed":observed.tolist(),"expected":expected.tolist(),"points":points.tolist()},indent=2))
                    raise AssertionError("Software renderer texture mismatch: "+str(report[-1]))
    # Explicit sRGB is deliberately a partial-color boundary, not silently
    # accepted by the raw compiled-byte filtering path.
    Image.fromarray(np.full((8,8,3),128,np.uint8)).save(root/"srgb.png")
    srgb=root/"srgb.xml";srgb.write_text('''<mujoco><visual><headlight ambient="0 0 0" diffuse="0 0 0" specular="0 0 0"/></visual>
      <asset><texture name="t" type="2d" file="srgb.png" colorspace="sRGB"/>
      <material name="m" texture="t" rgba="1 1 1 1" emission="1" specular="0"/></asset>
      <worldbody><geom name="g" type="box" size=".8 .7 .25" material="m"/>
      <camera name="top" pos="0 0 3" fovy="45"/></worldbody></mujoco>''')
    model=mujoco.MjModel.from_xml_path(str(srgb));data=mujoco.MjData(model);mujoco.mj_forward(model,data)
    with mujoco.Renderer(model,height=height,width=width) as renderer:
        renderer.update_scene(data,camera="top");renderer.scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW]=0
        GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT,[0,0,0,1]);image=renderer.render()
        _,valid,appearance,_=surface_colors(model,0,"box",np.asarray([0]),np.asarray([[1.,0,0]]),
            local_points=np.asarray([[0.,0,.25]]),with_diagnostics=True)
        assert not valid[0] and "sRGB" in appearance["reason"]
        assert abs(int(image[64,64,0])-128)>8
        srgb_boundary={"unsupported_mask_preserved":True,"rendered_rgb":image[64,64].tolist(),"raw_asset_rgb":[128,128,128]}
    result={"scope":"OWN_FIXTURES_CPU_SOFTWARE_OPENGL_NOT_REAL_LAYOUT_ACCEPTANCE","status":"PASS",
        "renderer":renderer_name,"mujoco":mujoco.__version__,"numpy":np.__version__,"cases":report,
        "rendered_faces":len(report),"compared_surface_points":sum(row["points"] for row in report),
        "max_rgb_byte_error":max(row["max_rgb_byte_error"] for row in report),"explicit_srgb_boundary":srgb_boundary,"training_ready":False}
    (root/'software_reference.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:value for key,value in result.items() if key!="cases"},sort_keys=True))


if __name__=="__main__":main()
