"""Slot-0 receptive-field probe: does the clean condition latent slot 0
depend only on frame 0 (causal claim) or on frames 0..3 (DS leakage claim)?

Encodes with the exact training online path (uint8 -> fp32 /127.5-1 -> encode,
encode_exact_durations=[17]) and compares latent slot 0 across constructions.
"""
import json, sys
import numpy as np
import torch
sys.path.insert(0, "/gemini/code/psm_wma/cosmos-framework")
from cosmos_framework.data.generator.action.datasets.libero_lerobot_dataset import LIBEROLeRobotDataset
from cosmos_framework.model.generator.tokenizers.wan2pt2_vae_4x16x16 import Wan2pt2VAEInterface

VAE = "/gemini/code/models/Wan2.2-TI2V-5B/Wan2.2_VAE.pth"
device = torch.device("cuda")
dataset = LIBEROLeRobotDataset(
    root="/gemini/code/data/libero/libero_10_no_noops_1.0.0_lerobot",
    split="full", fps=20, chunk_length=16, camera_mode="concat_view",
    image_size=256, action_normalization=None)
tok = Wan2pt2VAEInterface(vae_path=VAE, encode_exact_durations=[17])
tok.model.model.to(device)

ep = dataset._episodes[0]
rows = np.flatnonzero(dataset._row_episode == 0)
start = 100
ts = [float(dataset._row_timestamp[i]) for i in rows[start:start+17]]
video = dataset._load_video(ep, ts)          # [C,17,H,W] float 0..1
video = (video*255.0).clamp(0,255).to(torch.uint8).permute(1, 0, 2, 3)

def enc(v_uint8):  # [C,T,H,W] uint8 -> [T_lat,C,h,w] fp32 cpu
    px = v_uint8.to(device=device, dtype=torch.float32).div_(127.5).sub_(1.0)
    with torch.inference_mode():
        lat = tok.encode(px.unsqueeze(0)).squeeze(0).float()
    return lat.permute(1, 0, 2, 3).cpu()

real = enc(video)                                   # 17 real frames
static = enc(video[:, 0:1].repeat(1, 17, 1, 1))     # frame0 repeated x17
alt = video.clone(); alt[:, 1:] = video[:, -1:]     # frame0 real, 1-16 = last frame
altlat = enc(alt)
ts2 = [float(dataset._row_timestamp[i]) for i in rows[200:217]]
video2 = (dataset._load_video(ep, ts2)*255.0).clamp(0,255).to(torch.uint8).permute(1, 0, 2, 3)
mix = video.clone(); mix[:, 0:1] = video2[:, 0:1]   # frame0 swapped, 1-16 real
mixlat = enc(mix)

def d(a, b, s): return float((a[s]-b[s]).abs().max())
out = {
  "latent_shape": list(real.shape),
  "slot0_real_vs_staticrepeat_maxdiff": d(real, static, 0),
  "slot0_real_vs_frames1to16_swapped_maxdiff": d(real, altlat, 0),
  "slot0_frame0_swapped_maxdiff": d(real, mixlat, 0),
  "slot1_real_vs_staticrepeat_maxdiff": d(real, static, 1),
  "slot1_frames1to16_swapped_maxdiff": d(real, altlat, 1),
  "slot1_frame0_swapped_maxdiff": d(real, mixlat, 1),
}
print(json.dumps(out, indent=2))
json.dump(out, open("/gemini/code/psm_wma/artifacts/g0/r06/slot0_probe/result.json", "w"), indent=2)
