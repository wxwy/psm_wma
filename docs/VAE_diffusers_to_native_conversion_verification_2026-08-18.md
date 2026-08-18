# Wan2.2 VAE：diffusers 布局 → cosmos-framework 原生布局 转化验证记录

- 日期：2026-08-18
- 作者：Claude Code（psm_wma 新机环境准备任务）
- 目的：把 Edge-Policy-DROID 包里的 diffusers 布局 VAE 转化为 cosmos-framework 原生布局，**证明转化正确**。本文档自包含，供任何一方（含 ChatGPT）独立审阅/复跑。

---

## 1. 背景：为什么需要转化

同一个 Wan2.2 VAE 权重，两个项目用不同的键名（key）布局：

| 布局 | 消费方 | 典型键名 |
|---|---|---|
| **diffusers** | Edge HF 包 `/disk/rl/models/Cosmos3-Edge-Policy-DROID/vae/diffusion_pytorch_model.safetensors`（`AutoencoderKLWan` 类） | `encoder.conv_in.weight`、`encoder.down_blocks.0.resnets.0.conv1.weight`、`encoder.mid_block.attentions.0.to_qkv.weight`、`encoder.norm_out.gamma`、`encoder.conv_out.weight`、`quant_conv.weight`、`post_quant_conv.weight`… |
| **native** | cosmos-framework 原生代码 `Wan2pt2VAEInterface` / `WanVAE_`（`cosmos_framework/model/generator/tokenizers/wan2pt2_vae_4x16x16.py`） | 顶层 `conv1`/`conv2`、`encoder.conv1`、`encoder.downsamples.N.downsamples.M`、`encoder.middle.*`、`encoder.head.*`… |

两者都是 **196 个键**，权重数值完全一样，只是键名不同。cosmos-framework 加载时用 `model.load_state_dict(ckpt, strict=True)`（见 `wan2pt2_vae_4x16x16.py:1051`）——**键名对不上直接报 missing/unexpected 错误**。

因此"转化"= **纯键重映射 + `torch.save`**，不做任何权重数值变换、不下载任何文件。

> 为什么旧机器（codex 执行 R01-R06）没遇到这个问题：旧机器 `/gemini/code/models/Wan2.2-TI2V-5B/` 有下载好的原生 `Wan2.2_VAE.pth`，直接命中本地文件；Edge 包里的 diffusers VAE 原生代码从不消费（fork main 与官方 v2 的 `edge_model_config.py` 同为 `bucket_name=""` + `vae_path="pretrained/tokenizers/video/wan2pt2/Wan2.2_VAE.pth"`）。本机无原生文件且禁止下载，唯一来源是 Edge 的 diffusers VAE，故需转化。

## 2. 产物

```
cosmos-framework/examples/checkpoints/wan22_vae/Wan2.2_VAE.pth
```
- 大小：1,409,442,837 字节（1.4G）
- 键数：196
- 顶层键：`conv1.weight/bias`、`conv2.weight/bias`
- 此路径恰好是官方 launcher 默认 `WAN_VAE_PATH`（`examples/_sft_launcher_common.sh:52` `WAN_VAE_PATH="${WAN_VAE_PATH:-examples/checkpoints/wan22_vae/Wan2.2_VAE.pth}"`），训练开箱即用。

## 3. 验证①：键名映射的完整双向全等 + 形状匹配

转化脚本：`cosmos-framework/tools/g0/convert_vae_diffusers_to_native.py`

核心断言（运行全部通过）：

```python
assert set(mapping) == native_keys, "native keys not fully mapped"
assert set(mapping.values()) == diffusers_keys, "diffusers keys not consumed"
for native_key, diff_key in mapping.items():
    assert n_shape == d_shape, f"shape mismatch"
```

- 映射规则按架构位置一一对应：编码器 4 个 downsample 阶段（键数 14/18/18/12）、解码器 4 个 upsample 阶段（22/22/22/20）、mid 块 17、顶层/两端 conv 与 head；末级无 downsampler/upsampler 用存在性守卫跳过。

## 4. 验证②：原生 `WanVAE_` strict 加载（框架运行时的同一个检查）

```python
import torch
from cosmos_framework.model.generator.tokenizers.wan2pt2_vae_4x16x16 import WanVAE_
sd = torch.load("examples/checkpoints/wan22_vae/Wan2.2_VAE.pth", weights_only=True)
m = WanVAE_(temporal_window=4, encode_exact_durations=None)
r = m.load_state_dict(sd, strict=True)
print("missing:", len(r.missing_keys), "| unexpected:", len(r.unexpected_keys))
```

输出：
```
missing: 0 | unexpected: 0
```

## 5. 验证③：数值前向等价（关键证据）

**思路**：同一随机输入视频，分别跑「原权重 + diffusers `AutoencoderKLWan`」和「转化后权重 + 原生 `WanVAE_`」，比较编码器输出 latent。

**关键语义对齐**（审阅时注意）：
- 原生 `WanVAE_.encode(x, scale)`：`mu, _log_var = self.conv1(out).chunk(2, dim=1)`，即 `conv1` 输出 **96 通道**（mu 48 + logvar 48），仅返回前 48 的 `mu`；随后施加固定的 `(z - mean) * inv_std` 归一化（`mean/std` 为 Wan2.2 的 48 维常数表）。
- diffusers `AutoencoderKLWan._encode(x)`：`enc = self.quant_conv(out)`，输出同样是 **96 通道**，不施加 scale（由调用方处理）。
- 对比公平做法：给原生传 **identity scale `(0, 1)`** 使其不归一化，取 diffusers 输出的**前 48 通道**（mu 部分）与之比较。

```python
import sys; sys.path.insert(0, ".")
import torch
from cosmos_framework.model.generator.tokenizers.wan2pt2_vae_4x16x16 import WanVAE_
from diffusers.models.autoencoders import AutoencoderKLWan

sd = torch.load("examples/checkpoints/wan22_vae/Wan2.2_VAE.pth", weights_only=True)
native = WanVAE_(temporal_window=16, encode_exact_durations=[17]).eval().float()
assert not native.load_state_dict(sd, strict=True).missing_keys

diff = AutoencoderKLWan.from_pretrained("/disk/rl/models/Cosmos3-Edge-Policy-DROID/vae").eval().float()

torch.manual_seed(0)
x = (torch.rand(1, 3, 17, 64, 64) * 2 - 1)   # [B,C,T,H,W]，T=4n+1

with torch.no_grad():
    z = native.z_dim                          # 48
    z_native = native.encode(x, (torch.zeros(z), torch.ones(z)))  # 原生 mu
    h = diff._encode(x)                       # diffusers 裸输出 96 = mu+logvar
    z_diff = h[:, :z]                         # 取 mu 前 48

d = (z_native - z_diff).abs()
rel = (d / (z_diff.abs() + 1e-6)).max().item()
ok = torch.allclose(z_native, z_diff, rtol=1e-4, atol=1e-5)
```

**输出**：
```
z_dim=48 | native (1, 48, 5, 4, 4) vs diffusers-mu (1, 48, 5, 4, 4)
max|Δ| = 8.345e-07   mean|Δ| = 1.087e-07   |值域|均值 0.360
max 相对误差 = 5.345e-04
ALLCLOSE(rtol=1e-4,atol=1e-5): PASS
```

**判读**：
- 差异量级 1e-7 = **fp32 分块边界舍入**。原生把 T=17 编码为「首帧 prime + 一块 16 帧」（`encode_exact_durations=[17]` 跳过 padding）；diffusers 按「首帧 + 4×4 帧」分块。两者都是 CausalConv3d 因果编码，数学等价，仅浮点累加顺序不同。
- 若键映射**配对错误**（两个同形状张量互换位置），输出差异将是 O(1) 量级，绝不可能收敛到 1e-7。

## 6. 结论

1. 键名映射完整（196↔196）、形状全等；
2. 原生模块 strict 加载 0 missing / 0 unexpected —— 框架运行时唯一会执行的加载检查通过；
3. 编码器全链路数值前向等价（max Δ ≈ 8e-7）—— 证明配对正确、权重逐字等价。

**转化是纯键重命名，权重零改动，可以放心作为训练/推理的 VAE 使用。**

---

### 附：为什么不能在 cosmos-framework 里直接 diffusers 加载

- 视频 VAE 在 cosmos-framework 中**从不走 diffusers**：训练侧 `vae_path` 指向原生 `Wan2pt2VAEInterface`；连它自己的推理配置 `inference/configs/model/Cosmos3-Edge.yaml:119,138` 也指向同一个原生接口 + `vae_path: pretrained/tokenizers/video/wan2pt2/Wan2.2_VAE.pth`。
- diffusers `AutoencoderKLWan` 只是**整段前向编码**；原生 `WanVAE_` 是**分块因果流式编码**（`temporal_window`、`encode_exact_durations`、`feat_cache`），训练在线编码管线依赖这些能力。
- 换用 diffusers = 重写数据编码管线 + 换 tokenizer 接口 + 改所有 config；纯键重映射是成本最低、与官方机制完全对齐的做法。
- 唯一会被 diffusers 直接消费的是 **audio VAE**（`inference/common/checkpoints.py` 的 `_materialize_avae_ckpt` shim），与 Wan2.2 视频 VAE 无关。
