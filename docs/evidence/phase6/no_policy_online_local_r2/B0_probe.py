# SPDX-License-Identifier: OpenMDW-1.1
"""PHASE6-NO-POLICY-ONLINE-LOCAL-REAL-SMOKE probe (ds evidence only; 位于 /tmp，不改仓库)。

授权：`docs/collab/chatgpt/reviews/2026-10-05_V3_phase6_encode1_thresholded_parity_closure_8c38005.md`
verdict `APPROVE_TO_RUN_PHASE6_NO_POLICY_ONLINE_LOCAL_REAL_SMOKE_ONLY`。

范围（严格 bounded，无 policy）：
- 真实 CloseFridge ep26 composite（left|wrist 256x512）+ 真实 Wan tokenizer normal full Encode1；
- 只实例化 formal `LocalMemoryRuntime`，scan 走生产 `Cosmos3VFMNetwork.scan_local_memory` 模型侧接缝；
- 真实 completed sequence source steps 0..19（单次 20 步更新，N>T 分块），cold / prepare / commit /
  lost-response replay / changed same-frontier fail-closed / reset 全套事务语义；
- **不**加载 Policy DCP / HTTP server / simulator / training。

设计取舍（需 GPT 复核的两处非机械项）：
1. `RoboCasaLocalMemoryPolicyAdapter` 要求 `model.net.scan_local_memory` 可调用。本 probe 用
   `types.MethodType(Cosmos3VFMNetwork.scan_local_memory, net)` 把**生产方法本体**绑定到只持有
   formal `LocalMemoryRuntime` 的轻量 host 上，因此实际执行的 scan 代码逐字节来自
   `cosmos_framework/model/generator/mot/cosmos3_vfm_network.py`。probe 内断言
   `bound.__func__ is Cosmos3VFMNetwork.scan_local_memory` 并把该 sha256 写进 JSON。
2. wire 侧 `decode_image` 在生产中是 `action_policy_server_robocasa._decode_base64_png_to_rgb_uint8`。
   该 server 模块 import 时会执行 `init_script()`（被本 Gate 禁止的 server 加载路径），故此处**逐字节
   镜像**其实现（`_b64decode_loose` + PIL RGB + uint8 CHW），并对全部 20 行 composite 断言
   base64/PNG 往返**逐位等于**源 uint8 张量；该镜像的 sha256 与源码出处一并写进 JSON。
"""

from __future__ import annotations

import argparse
import base64
import binascii
import copy
import hashlib
import importlib.util
import io
import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch
from PIL import Image

SCRATCH = Path("/tmp/psm_wma_v3_phase6_cx")
TOOL_PATH = SCRATCH / "tools/v3/verify_robocasa_exact_window_real_parity.py"
POLICY_MODULE = SCRATCH / "cosmos_framework/inference/robocasa_local_memory_policy.py"
NETWORK_MODULE = SCRATCH / "cosmos_framework/model/generator/mot/cosmos3_vfm_network.py"
ONLINE_MODULE = SCRATCH / "cosmos_framework/inference/local_memory_online.py"
SERVER_MODULE = SCRATCH / "cosmos_framework/scripts/action_policy_server_robocasa.py"

if not Path(__file__).resolve().is_relative_to(Path("/tmp")):
    raise SystemExit("probe 必须位于 /tmp")


def _load_tool(path: Path):
    spec = importlib.util.spec_from_file_location("phase3p5_parity_tool", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


tool = _load_tool(TOOL_PATH)

from cosmos_framework.data.generator.action.datasets.robocasa_exact_window_cache import (  # noqa: E402
    RoboCasaExactWindowCacheCatalog,
)
from cosmos_framework.data.generator.action.datasets.robocasa_exact_window_policy import (  # noqa: E402
    CorrectedRoboCasaPolicyContract,
    OfficialRoboCasaPolicyAdapter,
)
from cosmos_framework.data.generator.action.datasets.robocasa_exact_window_source import (  # noqa: E402
    RoboCasaExactWindowSourceReader,
)
from cosmos_framework.data.generator.action.datasets.robocasa_lerobot_dataset import (  # noqa: E402
    _BASE_MOTION,
    _CONTROL_MODE,
    _EEF_POS,
    _EEF_ROT,
    _GRIPPER,
    _IMAGE_FEATURES,
    RoboCasaLeRobotDataset,
)
from cosmos_framework.inference.robocasa_local_memory_contract import (  # noqa: E402
    EVIDENCE_ACTION_DIM,
    EVIDENCE_FORMAT,
    EVIDENCE_VERSION,
    PREPROCESS_PROFILE,
)
from cosmos_framework.inference.robocasa_local_memory_policy import (  # noqa: E402
    RoboCasaLocalMemoryPolicyAdapter,
)
from cosmos_framework.model.generator.mot.cosmos3_vfm_network import Cosmos3VFMNetwork  # noqa: E402
from cosmos_framework.model.generator.mot.memory_prefix import LocalMemoryRuntime  # noqa: E402
from cosmos_framework.simulation.robocasa.eval_utils import (  # noqa: E402
    b64_png,
    canonicalize_raw15_for_env,
    decode_15d_to_env12,
)
from cosmos_framework.simulation.robocasa.local_memory_client import (  # noqa: E402
    RoboCasaLocalMemoryClient,
)

FORMAL_GEOMETRY = {
    "evidence_dim": 256,
    "local_dim": 32,
    "ttt_dim": 64,
    "fast_hidden_dim": 256,
    "inner_lr": 0.1,
    "ttt_tbptt_steps": 16,
    "k_local": 4,
    "action_dim": EVIDENCE_ACTION_DIM,
}

# 本 Gate 冻结：单一 20 步 completed sequence（source steps 0..19），blocking = 16 + 4。
EXPECTED_SOURCE_STEPS = 20
EXPECTED_SCAN_BLOCKS = [(16, False), (4, True)]


# ---------------------------------------------------------------------------
# wire 侧解码：逐字节镜像 action_policy_server_robocasa._b64decode_loose /
# _decode_base64_png_to_rgb_uint8（不 import 该 server 模块）。
# ---------------------------------------------------------------------------
def _strip_data_url_prefix(b64: str) -> str:
    if "," in b64 and b64[:64].lower().startswith("data:"):
        return b64.split(",", 1)[1].strip()
    return b64.strip()


def _b64decode_loose(b64: str) -> bytes:
    s = _strip_data_url_prefix(b64)
    s = "".join(s.split())
    pad = (-len(s)) % 4
    if pad:
        s = s + ("=" * pad)
    try:
        return base64.b64decode(s, validate=False)
    except binascii.Error:
        return base64.urlsafe_b64decode(s)


def _decode_base64_png_to_rgb_uint8(image_b64: str) -> torch.Tensor:
    """Returns a tensor with shape (3, H, W), dtype uint8, RGB."""
    raw = _b64decode_loose(image_b64)
    with Image.open(io.BytesIO(raw)) as img:
        img = img.convert("RGB")
        arr = np.asarray(img, dtype=np.uint8).copy()
    if arr.ndim != 3 or arr.shape[2] != 3:
        raise ValueError(f"Expected RGB image, got shape {arr.shape}")
    return torch.from_numpy(arr).permute(2, 0, 1).contiguous()


class _ModelOwnedScanHost:
    """只承载生产 Cosmos3VFMNetwork.scan_local_memory 所需的 config/runtime；无 LLM、无 policy 权重。"""

    def __init__(self, runtime: LocalMemoryRuntime) -> None:
        self.config = SimpleNamespace(local_memory_enabled=True)
        self.local_memory_runtime = runtime


def _sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _tensor_digest(tensors) -> str:
    digest = hashlib.sha256()
    for value in tensors:
        digest.update(value.detach().to("cpu", torch.float32).contiguous().numpy().tobytes())
    return digest.hexdigest()


def _state_digest(state) -> str | None:
    return None if state is None else _tensor_digest(tuple(state))


def _slow_inventory(runtime) -> dict[str, str]:
    return {
        name: hashlib.sha256(value.detach().to("cpu").contiguous().numpy().tobytes()).hexdigest()
        for name, value in sorted(runtime.state_dict().items())
    }


def _flags(value: torch.Tensor) -> dict[str, object]:
    return {
        "shape": list(value.shape),
        "dtype": str(value.dtype),
        "device": str(value.device),
        "finite": bool(torch.isfinite(value).all()),
    }


def _state_flags(state) -> list[dict[str, object]] | None:
    return None if state is None else [_flags(value) for value in state]


def _env12_from_dataset_action12(row12: np.ndarray, gripper_flip: bool) -> np.ndarray:
    """exact-window source item 的官方 12D dataset action -> env 12D（与 decode_15d_to_env12 同构）。"""
    row = np.asarray(row12, dtype=np.float64).reshape(-1)
    if row.shape != (12,) or not np.isfinite(row).all():
        raise ValueError("dataset action12 必须是有限 12D")
    mode = float(row[_CONTROL_MODE][0])
    env = np.zeros(12, dtype=np.float64)
    env[0:3] = row[_EEF_POS]
    env[3:6] = row[_EEF_ROT]
    grip = float(row[_GRIPPER][0])
    env[6] = float(np.clip(-grip if gripper_flip else grip, -1.0, 1.0))
    if mode > 0.0:
        env[7:11] = np.clip(row[_BASE_MOTION], -1.0, 1.0)
        env[11] = 1.0
    else:
        env[7:11] = 0.0
        env[11] = -1.0
    return env


def _single_frame_composite(deps, paths, timestamp, tolerance_s, video_backend):
    """复用 Phase3.5 reconstruct_episode 的同一 authority，只取单个 timestamp 的 256x512 composite。"""
    proxy = object.__new__(RoboCasaLeRobotDataset)
    proxy._image_features = _IMAGE_FEATURES
    proxy._skip_video_loading = False
    sample = {}
    for feature, (path, from_ts) in paths.items():
        kwargs = {"backend": video_backend} if video_backend is not None else {}
        frames = deps.decode(path, [from_ts + timestamp], tolerance_s, **kwargs)
        tool._validate_frames(frames, 1, feature)
        sample[feature] = frames
    composite = deps.compose(proxy, sample)
    if tuple(composite.shape) != (1, 3, 256, 512) or not bool(torch.isfinite(composite).all()):
        raise ValueError(f"single-frame official composite shape/finite 无效：{tuple(composite.shape)}")
    uint8 = deps.convert(proxy, composite)
    if uint8.dtype != torch.uint8 or tuple(uint8.shape) != (3, 1, 256, 512):
        raise ValueError(f"single-frame official uint8 conversion 无效：{uint8.dtype}/{tuple(uint8.shape)}")
    return uint8[:, 0].contiguous()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache-root", required=True, type=Path)
    ap.add_argument("--source-root", required=True, type=Path)
    ap.add_argument("--vae-path", required=True, type=Path)
    ap.add_argument("--output-json", required=True, type=Path)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--task-class", default="CloseFridge")
    ap.add_argument("--episode-index", type=int, default=26)
    ap.add_argument("--source-steps", type=int, default=EXPECTED_SOURCE_STEPS)
    ap.add_argument("--image-size", type=int, default=256)
    ap.add_argument("--video-backend", default="pyav")
    ap.add_argument("--tolerance-s", type=float, default=1e-4)
    ap.add_argument("--max-sessions", type=int, default=1)
    ap.add_argument("--max-evidence-steps", type=int, default=256)
    ap.add_argument("--manual-seed", type=int, default=20261005)
    ap.add_argument("--gripper-flip", action="store_true")
    args = ap.parse_args()

    if not args.vae_path.is_file():
        raise FileNotFoundError(f"本地 Wan VAE 文件缺失：{args.vae_path}")
    if args.source_steps != EXPECTED_SOURCE_STEPS:
        raise ValueError(f"本 Gate 冻结 source steps 0..{EXPECTED_SOURCE_STEPS - 1}（单次 20 步更新）")
    if args.gripper_flip:
        raise ValueError("本 Gate 冻结 canonicalize_raw15_for_env(..., False)")

    deps = tool.ProbeDependencies()
    catalog = RoboCasaExactWindowCacheCatalog(args.cache_root)
    source = RoboCasaExactWindowSourceReader(catalog, args.source_root)
    contract = CorrectedRoboCasaPolicyContract.from_cache_catalog(catalog)
    policy_adapter = OfficialRoboCasaPolicyAdapter(contract)
    config = tool.resolve_vae_config(contract, args.vae_path)
    selection = tool.select_episodes(catalog, (args.task_class,), args.episode_index, (0,), 1)
    record, sel_starts = selection[0]
    key = record.key
    rows, timestamps = tool.episode_rows(source, record)
    paths = tool.video_paths(source, key)
    if len(timestamps) < EXPECTED_SOURCE_STEPS + 16:
        raise ValueError(f"episode 帧数不足以覆盖 20 步 + 17 帧窗：{len(timestamps)}")

    device = torch.device(args.device)
    if device.type != "cuda" or not torch.cuda.is_available():
        raise ValueError("no-policy online Local smoke 需要可用 CUDA")
    torch.backends.cudnn.benchmark = False
    torch.cuda.init()
    torch.cuda.reset_peak_memory_stats(device)

    report: dict[str, object] = {
        "schema": "robocasa_phase6_no_policy_online_local_real_smoke_v1",
        "gate": "PHASE6-NO-POLICY-ONLINE-LOCAL-REAL-SMOKE",
        "role": "ds (execution/evidence only; no repo/cache/source/VAE write)",
        "authority": {
            "scratch_root": str(SCRATCH),
            "parity_tool_path": str(TOOL_PATH),
            "parity_tool_sha256": _sha256(TOOL_PATH),
            "adapter_module_path": str(POLICY_MODULE),
            "adapter_module_sha256": _sha256(POLICY_MODULE),
            "online_module_path": str(ONLINE_MODULE),
            "online_module_sha256": _sha256(ONLINE_MODULE),
            "network_module_path": str(NETWORK_MODULE),
            "network_module_sha256": _sha256(NETWORK_MODULE),
            "wire_decoder": {
                "provenance": str(SERVER_MODULE),
                "provenance_symbol": "_decode_base64_png_to_rgb_uint8 / _b64decode_loose",
                "imported_server_module": False,
                "reason": "server 模块 import 时执行 init_script()，属本 Gate 禁止的 server 加载路径",
                "mirror_sha256": hashlib.sha256(
                    (_b64decode_loose.__code__.co_code + _decode_base64_png_to_rgb_uint8.__code__.co_code)
                ).hexdigest(),
            },
            "cache_manifest_sha256": catalog.manifest_sha256,
            "corpus_digest": catalog.corpus_digest,
            "source_binding_digest": source.source_binding_digest,
            "runtime_source_root": str(args.source_root),
            "runtime_vae_path": str(args.vae_path),
            "vae_sha256": _sha256(args.vae_path),
            "resolved_vae_contract": config,
            "torch_version": torch.__version__,
            "cuda_version": torch.version.cuda,
            "device": args.device,
            "video_backend": args.video_backend,
            "cudnn_benchmark": torch.backends.cudnn.benchmark,
            "image_size": args.image_size,
            "tolerance_s": args.tolerance_s,
            "read_only": True,
            "no_fallback": True,
            "no_policy": True,
            "gripper_flip": bool(args.gripper_flip),
            "manual_seed": args.manual_seed,
            "local_memory_geometry": FORMAL_GEOMETRY,
            "expected_source_steps": EXPECTED_SOURCE_STEPS,
            "expected_scan_blocks": [list(item) for item in EXPECTED_SCAN_BLOCKS],
            "max_sessions": args.max_sessions,
            "max_evidence_steps": args.max_evidence_steps,
            "evidence_version": EVIDENCE_VERSION,
            "evidence_format": EVIDENCE_FORMAT,
            "preprocess_profile": PREPROCESS_PROFILE,
        },
        "episode": {
            "task_class": key.task_class,
            "episode_index": key.episode_index,
            "episode_frame_count": len(timestamps),
            "selected_starts": list(sel_starts),
            "source_steps": list(range(args.source_steps)),
            "camera_keys": [_IMAGE_FEATURES["left"], _IMAGE_FEATURES["wrist"]],
        },
        "witness": {},
        "stages": {},
        "counts": {},
        "resources": {},
        "checks": [],
        "status": "FAIL",
    }

    # ---- 真实 Wan tokenizer（Encode1 authority）----
    tokenizer = deps.tokenizer_factory(**config)
    tool.prepare_tokenizer_device(tokenizer, device)
    report["authority"]["tokenizer_state"] = {
        "class": type(tokenizer).__name__,
        "use_streaming_encode": bool(getattr(tokenizer, "use_streaming_encode", False)),
        "keep_encoder_cache": bool(getattr(tokenizer, "_keep_encoder_cache", False)),
        "keep_decoder_cache": bool(getattr(tokenizer, "_keep_decoder_cache", False)),
    }

    encode_calls: list[int] = []
    real_encode = tokenizer.encode

    def counted_encode(*call_args, **call_kwargs):
        encode_calls.append(len(encode_calls) + 1)
        return real_encode(*call_args, **call_kwargs)

    tokenizer.encode = counted_encode

    # ---- 因果 VAE cache 宿主解析（S24 证据）----
    # cache 实际持有者是 WanVAE_：tokenizer.model = WanVAE，WanVAE.model = WanVAE_。
    # 解析失败必须显式报错，绝不能静默通过（attempt1 的缺陷正是在此）。
    def _resolve_causal_cache_host(tok):
        outer = getattr(tok, "model", None)
        inner = getattr(outer, "model", None)
        if inner is None or not hasattr(inner, "_enc_cache") or not hasattr(inner, "_dec_cache"):
            raise RuntimeError(
                "无法解析因果 VAE cache 宿主，期望 tokenizer.model.model (WanVAE_) 持有 "
                "_enc_cache/_dec_cache；实际 "
                f"tokenizer={type(tok).__name__} "
                f"outer={type(outer).__name__ if outer is not None else None} "
                f"inner={type(inner).__name__ if inner is not None else None}")
        return inner

    causal_host = _resolve_causal_cache_host(tokenizer)

    def _cache_snapshot(host) -> dict:
        enc = host._enc_cache
        dec = host._dec_cache
        return {
            "host_class": type(host).__name__,
            "enc_cache_len": len(enc),
            "enc_cache_all_none": all(item is None for item in enc),
            "enc_stream_shape": host._enc_stream_shape,
            "dec_cache_len": len(dec),
            "dec_cache_all_none": all(item is None for item in dec),
        }

    # 直接计数 streaming / decode 入口：证明本轮从未走保留因果状态的路径。
    stream_calls = {"encode_streaming": 0, "decode": 0}
    real_encode_streaming = causal_host.encode_streaming
    real_wanvae_decode = causal_host.decode

    def counted_encode_streaming(*call_args, **call_kwargs):
        stream_calls["encode_streaming"] += 1
        return real_encode_streaming(*call_args, **call_kwargs)

    def counted_wanvae_decode(*call_args, **call_kwargs):
        stream_calls["decode"] += 1
        return real_wanvae_decode(*call_args, **call_kwargs)

    causal_host.encode_streaming = counted_encode_streaming
    causal_host.decode = counted_wanvae_decode
    vae_cache_before = _cache_snapshot(causal_host)
    report["authority"]["causal_vae_cache_before"] = vae_cache_before

    # ---- 固定随机源 + 轻量 model-owned host（生产 scan 绑定）----
    torch.manual_seed(args.manual_seed)
    report["authority"]["torch_rng"] = {
        "manual_seed": int(args.manual_seed),
        "torch_initial_seed": int(torch.initial_seed()),
        "cuda_initial_seed": int(torch.cuda.initial_seed()),
    }

    runtime = LocalMemoryRuntime()  # formal K4/T16/evidence256/local32/ttt64/hidden256/inner_lr0.1/action15
    observed_geometry = {
        "evidence_dim": runtime.core.evidence_dim,
        "local_dim": runtime.core.local_dim,
        "ttt_dim": runtime.core.ttt_dim,
        "fast_hidden_dim": runtime.core.fast_hidden_dim,
        "inner_lr": runtime.core.inner_lr,
        "ttt_tbptt_steps": runtime.core.ttt_tbptt_steps,
        "k_local": runtime.core.k_local,
        "action_dim": runtime.encoder.action_proj.in_features,
    }
    report["authority"]["runtime_geometry_observed"] = observed_geometry
    if observed_geometry != FORMAL_GEOMETRY:
        raise ValueError(f"LocalMemoryRuntime 几何与 formal 不一致：{observed_geometry}")
    runtime.to(device)

    net = _ModelOwnedScanHost(runtime)
    net.scan_local_memory = types.MethodType(Cosmos3VFMNetwork.scan_local_memory, net)
    scan_impl = net.scan_local_memory
    report["authority"]["scan_source"] = {
        "bound_from": "Cosmos3VFMNetwork.scan_local_memory",
        "is_production_method": bool(scan_impl.__func__ is Cosmos3VFMNetwork.scan_local_memory),
        "qualname": scan_impl.__func__.__qualname__,
        "defined_in": str(NETWORK_MODULE),
    }
    if not report["authority"]["scan_source"]["is_production_method"]:
        raise RuntimeError("scan 必须绑定生产 Cosmos3VFMNetwork.scan_local_memory")

    scan_calls: list[dict[str, object]] = []

    def counted_scan(visual, action, valid, state_in, **kwargs):
        scan_calls.append(
            {
                "index": len(scan_calls),
                "T": int(visual.shape[1]),
                "state_in_present": state_in is not None,
                "create_graph": bool(kwargs.get("create_graph", True)),
                "valid_all": bool(valid.all()),
            }
        )
        return scan_impl(visual, action, valid, state_in, **kwargs)

    net.scan_local_memory = counted_scan
    model = SimpleNamespace(net=net, tokenizer_vision_gen=tokenizer)
    adapter = RoboCasaLocalMemoryPolicyAdapter(
        SimpleNamespace(model=model),
        mode="required",
        decode_image=lambda value: _decode_base64_png_to_rgb_uint8(value),
        max_sessions=args.max_sessions,
        max_evidence_steps=args.max_evidence_steps,
    )
    report["authority"]["adapter_info"] = adapter.info()
    report["authority"]["scan_binding_after_adapter"] = {
        "adapter_scan_is_counted_wrapper": adapter.memory.scan_local_memory is counted_scan,
        "direct_core_fallback_absent": adapter.memory.scan_local_memory is not None,
    }

    slow_before = _slow_inventory(runtime)

    checks: list[dict[str, object]] = []

    def check(name: str, ok: bool, detail: object) -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    def snapshot(session_id: str) -> dict[str, object]:
        record_now = adapter.memory._records.get(session_id)
        visual_now = adapter._visual_records.get(session_id)
        return {
            "consumer_step": None if record_now is None else record_now.consumer_step,
            "fingerprint": None if record_now is None else record_now.fingerprint,
            "token_digest": None if record_now is None or record_now.token is None else _tensor_digest((record_now.token,)),
            "state_digest": None if record_now is None else _state_digest(record_now.state),
            "visual_frontier": None if visual_now is None else visual_now.consumer_step,
            "visual_present": visual_now is not None,
        }

    def request_from_client(slot: int) -> dict[str, object]:
        return {"image_size": args.image_size, "local_memory": client.payload(slot)}

    # ---- 真实 episode 素材：composite + exact-window item action[1] authority（steps 0..19）----
    evidence_rows: list[dict[str, object]] = []
    witness: dict[str, object] = {
        "per_source_step": [],
        "composite_png_roundtrip_exact": True,
        "canonical_redecode_max_abs": 0.0,
        "item_action_vs_dataset_env12_max_abs": 0.0,
    }
    for step in range(args.source_steps):
        window = source.read_window(key, step)
        if window.key != key or window.start_frame != step:
            raise ValueError(f"source window 锚定漂移：{window.key}/{window.start_frame}")
        # raw15 authority = current exact-window item 的 action[1]（官方 policy 转换产出，与 cached SFT action 同源）
        policy_window = policy_adapter.convert(window)
        if tuple(policy_window.action_with_state15.shape) != (17, 15):
            raise ValueError(f"exact-window item action 形状无效：{tuple(policy_window.action_with_state15.shape)}")
        item_raw15 = policy_window.action_with_state15[1].detach().cpu().numpy().astype(np.float64)
        if item_raw15.shape != (EVIDENCE_ACTION_DIM,) or not np.isfinite(item_raw15).all():
            raise ValueError("item action[1] 必须是有限 raw15")
        dataset_row12 = window.action12[0].detach().cpu().numpy().astype(np.float64)
        env12_dataset = _env12_from_dataset_action12(dataset_row12, args.gripper_flip)

        submitted, canonical = canonicalize_raw15_for_env(item_raw15, args.gripper_flip)
        redecode = float(np.max(np.abs(decode_15d_to_env12(canonical, args.gripper_flip) - submitted)))
        item_gap = float(np.max(np.abs(submitted - env12_dataset)))

        frame_uint8 = _single_frame_composite(
            deps, paths, timestamps[step], args.tolerance_s, args.video_backend
        )
        hwc = frame_uint8.permute(1, 2, 0).contiguous().numpy()
        image_b64 = b64_png(hwc)
        decoded = _decode_base64_png_to_rgb_uint8(image_b64)
        roundtrip = bool(torch.equal(decoded, frame_uint8))
        witness["composite_png_roundtrip_exact"] = bool(witness["composite_png_roundtrip_exact"]) and roundtrip
        witness["canonical_redecode_max_abs"] = max(float(witness["canonical_redecode_max_abs"]), redecode)
        witness["item_action_vs_dataset_env12_max_abs"] = max(
            float(witness["item_action_vs_dataset_env12_max_abs"]), item_gap
        )
        witness["per_source_step"].append(
            {
                "source_step": step,
                "item_action_row": 1,
                "item_raw15_sha256": hashlib.sha256(item_raw15.astype(np.float64).tobytes()).hexdigest(),
                "canonical_raw15_sha256": hashlib.sha256(canonical.tobytes()).hexdigest(),
                "submitted_env12_sha256": hashlib.sha256(submitted.astype(np.float64).tobytes()).hexdigest(),
                "dataset_action12_sha256": hashlib.sha256(dataset_row12.tobytes()).hexdigest(),
                "canonical_redecode_max_abs": redecode,
                "item_action_vs_dataset_env12_max_abs": item_gap,
                "item_base_mode": float(item_raw15[4]),
                "dataset_control_mode": float(dataset_row12[_CONTROL_MODE][0]),
                "composite_png_roundtrip_exact": roundtrip,
                "composite_shape": [int(x) for x in frame_uint8.shape],
                "composite_dtype": str(frame_uint8.dtype),
            }
        )
        evidence_rows.append(
            {
                "source_step": step,
                "composite_hwc_uint8": hwc,
                "canonical_raw15": canonical,
            }
        )
    report["witness"] = witness
    check(
        "W1_canonical_raw15_redecodes_submitted_env12",
        float(witness["canonical_redecode_max_abs"]) <= 2e-6,
        {"max_abs": witness["canonical_redecode_max_abs"], "tol": 2e-6},
    )
    check(
        "W2_item_action1_matches_dataset_env12",
        float(witness["item_action_vs_dataset_env12_max_abs"]) <= 2e-6,
        {"max_abs": witness["item_action_vs_dataset_env12_max_abs"], "tol": 2e-6},
    )
    check(
        "W3_composite_png_roundtrip_bit_exact",
        bool(witness["composite_png_roundtrip_exact"]),
        {"steps": args.source_steps},
    )
    check(
        "W4_source_steps_are_0_to_19_contiguous",
        [row["source_step"] for row in witness["per_source_step"]] == list(range(EXPECTED_SOURCE_STEPS)),
        {"steps": [row["source_step"] for row in witness["per_source_step"]][:3] + ["..."]},
    )

    def record_completed_steps(start: int, stop: int) -> None:
        for step in range(start, stop):
            row = evidence_rows[step]
            client.record_completed(0, row["composite_hwc_uint8"], row["canonical_raw15"])

    def run_stage(name: str, request: dict[str, object]) -> tuple[object, dict[str, object]]:
        before = (len(encode_calls), len(scan_calls))
        prepared = adapter.prepare(request)
        status = adapter.status(prepared)
        token = adapter.prefixes(prepared)[0]
        state = prepared.memory.replacement.state
        entry = {
            "stage": name,
            "encoded_steps": status["encoded_steps"],
            "replay": status["replay"],
            "prefix_present": status["prefix_present"],
            "consumer_step": status["consumer_step"],
            "adapted_steps": status["adapted_steps"],
            "inner_loss_mean": status["inner_loss_mean"],
            "fast_state_norm": status["fast_state_norm"],
            "fast_update_norm": status["fast_update_norm"],
            "token": None if token is None else _flags(token),
            "state_present": state is not None,
            "state_flags": _state_flags(state),
            "state_finite": None if state is None else all(bool(torch.isfinite(v).all()) for v in state),
            "encode_calls_delta": len(encode_calls) - before[0],
            "scan_calls_delta": len(scan_calls) - before[1],
            "telemetry_finite": bool(
                np.isfinite(
                    [
                        status["adapted_steps"],
                        status["inner_loss_mean"],
                        status["fast_state_norm"],
                        status["fast_update_norm"],
                    ]
                ).all()
            ),
        }
        return prepared, entry

    # ---- 1. cold S0（reset=true / step0 / 无 evidence）----
    client = RoboCasaLocalMemoryClient(enabled=True, max_evidence_steps=args.max_evidence_steps)
    client.begin(0, image_size=args.image_size)
    sid = client.session_id(0)
    request0 = request_from_client(0)
    check(
        "S1_cold_payload_is_reset_step0_empty",
        bool(request0["local_memory"]["reset"]) and request0["local_memory"]["consumer_step"] == 0
        and request0["local_memory"]["evidence"] == [],
        {"consumer_step": request0["local_memory"]["consumer_step"], "reset": request0["local_memory"]["reset"]},
    )
    live_before_cold = snapshot(sid)
    prepared0, entry0 = run_stage("cold_S0", request0)
    live_after_prepare_cold = snapshot(sid)
    check(
        "S2_cold_S0_prefix_absent_state_lazy",
        entry0["prefix_present"] is False
        and entry0["token"] is None
        and entry0["state_present"] is False
        and entry0["encoded_steps"] == 0
        and entry0["encode_calls_delta"] == 0
        and entry0["scan_calls_delta"] == 0
        and entry0["adapted_steps"] == 0.0
        and entry0["consumer_step"] == 0,
        entry0,
    )
    check(
        "S3_cold_prepare_does_not_publish_before_commit",
        live_after_prepare_cold["consumer_step"] is None
        and live_after_prepare_cold["state_digest"] is None
        and live_after_prepare_cold["token_digest"] is None,
        {"live_before": live_before_cold, "live_after_prepare": live_after_prepare_cold},
    )
    adapter.commit(prepared0)
    client.acknowledge(0, adapter.status(prepared0))
    live_after_commit_cold = snapshot(sid)
    check(
        "S4_cold_after_commit_live_step0_lazy_state",
        live_after_commit_cold["consumer_step"] == 0
        and live_after_commit_cold["state_digest"] is None
        and live_after_commit_cold["token_digest"] is None
        and live_after_commit_cold["visual_frontier"] == 0,
        live_after_commit_cold,
    )

    # ---- 2. 真实 completed sequence：steps 0..19 → 单次 20 步更新 ----
    record_completed_steps(0, EXPECTED_SOURCE_STEPS)
    request1 = request_from_client(0)
    check(
        "S5_update20_payload_frontier_20_with_20_rows_no_reset",
        request1["local_memory"]["consumer_step"] == EXPECTED_SOURCE_STEPS
        and len(request1["local_memory"]["evidence"]) == EXPECTED_SOURCE_STEPS
        and not request1["local_memory"]["reset"],
        {
            "consumer_step": request1["local_memory"]["consumer_step"],
            "rows": len(request1["local_memory"]["evidence"]),
            "reset": request1["local_memory"]["reset"],
            "row0_source_step": request1["local_memory"]["evidence"][0]["source_step"],
            "row19_source_step": request1["local_memory"]["evidence"][19]["source_step"],
        },
    )
    live_before_update = snapshot(sid)
    prepared1, entry1 = run_stage("update20_steps0_19", request1)
    live_after_prepare_update = snapshot(sid)
    report["stages"]["update20"] = {
        "live_before_prepare": live_before_update,
        "entry": entry1,
        "live_after_prepare_before_commit": live_after_prepare_update,
        "scan_calls": [dict(item) for item in scan_calls],
    }
    check(
        "S6_update20_real_encode1_and_model_owned_local_update",
        entry1["encoded_steps"] == EXPECTED_SOURCE_STEPS
        and entry1["encode_calls_delta"] == EXPECTED_SOURCE_STEPS
        and entry1["scan_calls_delta"] == 2
        and entry1["replay"] is False
        and entry1["adapted_steps"] == float(EXPECTED_SOURCE_STEPS)
        and entry1["consumer_step"] == EXPECTED_SOURCE_STEPS
        and entry1["telemetry_finite"] is True
        and entry1["inner_loss_mean"] > 0.0,
        entry1,
    )
    check(
        "S7_update20_prefix_finite_k4x32_and_fast_state_finite_fp32",
        entry1["prefix_present"] is True
        and entry1["token"] is not None
        and entry1["token"]["shape"] == [FORMAL_GEOMETRY["k_local"], FORMAL_GEOMETRY["local_dim"]]
        and entry1["token"]["finite"] is True
        and entry1["state_present"] is True
        and entry1["state_finite"] is True
        and all(item["dtype"] == "torch.float32" and item["finite"] for item in entry1["state_flags"]),
        {"token": entry1["token"], "state_flags": entry1["state_flags"]},
    )
    check(
        "S8_update20_chunked_scan_blocks_exactly_16_then_4",
        [(item["T"], item["state_in_present"]) for item in scan_calls] == EXPECTED_SCAN_BLOCKS
        and all(item["create_graph"] is False and item["valid_all"] is True for item in scan_calls),
        [dict(item) for item in scan_calls],
    )
    check(
        "S9_update20_live_frontier_still_0_before_commit",
        live_before_update["consumer_step"] == 0
        and live_after_prepare_update["consumer_step"] == 0
        and live_after_prepare_update["state_digest"] is None
        and live_after_prepare_update["token_digest"] is None,
        {"live_before": live_before_update, "live_after_prepare": live_after_prepare_update},
    )
    adapter.commit(prepared1)
    committed = snapshot(sid)
    check(
        "S10_update20_commit_advances_live_frontier_matches_candidate",
        committed["consumer_step"] == EXPECTED_SOURCE_STEPS
        and committed["token_digest"] == _tensor_digest((adapter.prefixes(prepared1)[0],))
        and committed["state_digest"] == _state_digest(prepared1.memory.replacement.state)
        and committed["visual_frontier"] == EXPECTED_SOURCE_STEPS,
        committed,
    )

    # ---- 3. lost-response replay：同一 payload（client 未 acknowledge）----
    request2 = request_from_client(0)
    check("S11_replay_payload_byte_identical", request2 == request1, {"identical": request2 == request1})
    prepared2, entry2 = run_stage("replay_step20_lost_response", request2)
    report["stages"]["replay"] = {"entry": entry2, "live_after_prepare": snapshot(sid)}
    check(
        "S12_replay_zero_encode_zero_scan_zero_adapt_same_prefix_state",
        entry2["replay"] is True
        and entry2["encoded_steps"] == 0
        and entry2["adapted_steps"] == 0.0
        and entry2["encode_calls_delta"] == 0
        and entry2["scan_calls_delta"] == 0
        and entry2["consumer_step"] == EXPECTED_SOURCE_STEPS
        and len(encode_calls) == EXPECTED_SOURCE_STEPS
        and len(scan_calls) == 2
        and _tensor_digest((adapter.prefixes(prepared2)[0],)) == committed["token_digest"]
        and _state_digest(prepared2.memory.replacement.state) == committed["state_digest"],
        {
            "entry": entry2,
            "encode_calls": len(encode_calls),
            "scan_calls": len(scan_calls),
            "token_digest": _tensor_digest((adapter.prefixes(prepared2)[0],)),
            "committed_token_digest": committed["token_digest"],
        },
    )
    adapter.commit(prepared2)
    after_replay_commit = snapshot(sid)
    check(
        "S13_replay_commit_does_not_move_frontier_or_state",
        after_replay_commit == committed,
        {"before": committed, "after": after_replay_commit},
    )

    # ---- 4. same-frontier（step20）changed evidence fail-closed ----
    rejects: list[dict[str, object]] = []
    for label in ("executed_action", "composite_image"):
        bad = copy.deepcopy(request1)
        if label == "executed_action":
            bad["local_memory"]["evidence"][19]["executed_action"][0] += 1.0
        else:
            changed = np.ascontiguousarray(evidence_rows[19]["composite_hwc_uint8"] + 1)
            bad["local_memory"]["evidence"][19]["composite_image"] = b64_png(changed)
        before = (len(encode_calls), len(scan_calls))
        raised = None
        try:
            adapter.prepare(bad)
        except ValueError as exc:
            raised = str(exc)
        rejects.append(
            {
                "case": label,
                "raised": raised,
                "encode_calls_delta": len(encode_calls) - before[0],
                "scan_calls_delta": len(scan_calls) - before[1],
                "state_after": snapshot(sid),
                "pending_clean": adapter.memory._pending == {} and adapter._visual_pending == {},
            }
        )
    report["stages"]["rejects"] = rejects
    check(
        "S14_changed_same_frontier_evidence_fail_closed",
        all(
            item["raised"] is not None
            and "bytes/action changed" in item["raised"]
            and item["encode_calls_delta"] == 0
            and item["scan_calls_delta"] == 0
            and item["state_after"] == committed
            and item["pending_clean"]
            for item in rejects
        ),
        rejects,
    )
    check(
        "S15_changed_evidence_keeps_encode_scan_counts_at_20_2",
        len(encode_calls) == EXPECTED_SOURCE_STEPS and len(scan_calls) == 2,
        {"encode_calls": len(encode_calls), "scan_calls": len(scan_calls)},
    )
    # 失败请求不得污染 client 账本：原 payload 仍可被精确 ack
    ack_ok, ack_error = True, None
    try:
        client.acknowledge(0, adapter.status(prepared2))
    except Exception as exc:  # noqa: BLE001 - 记录真实异常文本
        ack_ok, ack_error = False, repr(exc)
    check("S16_client_acknowledges_exact_frontier_after_replay", ack_ok, {"error": ack_error})

    # ---- 5. reset：清空 server 侧 memory / visual replay witness，新 episode 再次 cold ----
    adapter.reset(sid)
    cleared = {
        "records": adapter.memory._records == {},
        "pending": adapter.memory._pending == {},
        "visual_records": adapter._visual_records == {},
        "visual_pending": adapter._visual_pending == {},
    }
    check("S17_reset_clears_records_state_token_replay_witness", all(cleared.values()), cleared)
    client.end(0)
    client.begin(1, image_size=args.image_size)
    sid2 = client.session_id(1)
    request3 = request_from_client(1)
    check(
        "S18_post_reset_new_session_payload_is_cold",
        sid2 != sid
        and bool(request3["local_memory"]["reset"])
        and request3["local_memory"]["consumer_step"] == 0
        and request3["local_memory"]["evidence"] == [],
        {"session_changed": sid2 != sid, "consumer_step": request3["local_memory"]["consumer_step"]},
    )
    prepared3, entry3 = run_stage("post_reset_new_session_cold", request3)
    check(
        "S19_post_reset_new_episode_cold_prefix_absent_state_lazy",
        entry3["prefix_present"] is False
        and entry3["token"] is None
        and entry3["state_present"] is False
        and entry3["consumer_step"] == 0
        and entry3["encode_calls_delta"] == 0
        and entry3["scan_calls_delta"] == 0,
        entry3,
    )
    adapter.commit(prepared3)
    live_after_new_cold = snapshot(sid2)
    check(
        "S20_post_reset_live_session_is_fresh_lazy",
        live_after_new_cold["consumer_step"] == 0
        and live_after_new_cold["state_digest"] is None
        and live_after_new_cold["token_digest"] is None,
        live_after_new_cold,
    )
    report["stages"]["cold"] = {
        "payload": {
            "consumer_step": request0["local_memory"]["consumer_step"],
            "reset": request0["local_memory"]["reset"],
            "evidence_len": len(request0["local_memory"]["evidence"]),
        },
        "entry": entry0,
        "live_before": live_before_cold,
        "live_after_prepare": live_after_prepare_cold,
        "live_after_commit": live_after_commit_cold,
    }
    report["stages"]["reset"] = {
        "cleared": cleared,
        "new_session_payload": {
            "consumer_step": request3["local_memory"]["consumer_step"],
            "reset": request3["local_memory"]["reset"],
            "evidence_len": len(request3["local_memory"]["evidence"]),
            "session_changed": sid2 != sid,
        },
        "entry": entry3,
        "live_after_new_cold": live_after_new_cold,
    }
    report["stages"]["committed_frontier"] = committed

    # ---- 计数 / 资源 / 慢参数 ----
    slow_after = _slow_inventory(runtime)
    vae_cache_after = _cache_snapshot(causal_host)
    vae_cache_after["streaming_encode_calls"] = stream_calls["encode_streaming"]
    vae_cache_after["decoder_decode_calls"] = stream_calls["decode"]
    vae_cache_unchanged = all(
        vae_cache_after[key] == value for key, value in vae_cache_before.items()
    )
    report["counts"] = {
        "tokenizer_encode_calls": len(encode_calls),
        "model_owned_scan_calls": len(scan_calls),
        "scan_call_log": [dict(item) for item in scan_calls],
        "expected_encode_calls": EXPECTED_SOURCE_STEPS,
        "expected_scan_calls": len(EXPECTED_SCAN_BLOCKS),
    }
    report["resources"] = {
        "cuda_device": str(device),
        "cuda_device_name": torch.cuda.get_device_name(device),
        "peak_allocated_bytes": int(torch.cuda.max_memory_allocated(device)),
        "peak_reserved_bytes": int(torch.cuda.max_memory_reserved(device)),
        "allocated_bytes_at_end": int(torch.cuda.memory_allocated(device)),
        "slow_local_params_sha256_before": slow_before,
        "slow_local_params_sha256_after": slow_after,
        "slow_local_params_unchanged": slow_before == slow_after,
        "slow_local_param_count": len(slow_before),
        "vae_cache_before": vae_cache_before,
        "vae_cache_after": vae_cache_after,
        "vae_cache_unchanged": vae_cache_unchanged,
    }
    check(
        "S21_encode_call_count_is_20",
        len(encode_calls) == EXPECTED_SOURCE_STEPS,
        {"tokenizer_encode_calls": len(encode_calls)},
    )
    check(
        "S22_model_owned_scan_call_count_is_2",
        len(scan_calls) == len(EXPECTED_SCAN_BLOCKS),
        {"model_owned_scan_calls": len(scan_calls)},
    )
    check(
        "S23_slow_local_params_bit_exact_unchanged",
        slow_before == slow_after and len(slow_before) > 0,
        {"param_count": len(slow_before)},
    )
    check(
        "S24_no_retained_causal_vae_state",
        bool(getattr(tokenizer, "use_streaming_encode", False)) is False
        and bool(getattr(tokenizer, "_keep_encoder_cache", False)) is False
        and bool(getattr(tokenizer, "_keep_decoder_cache", False)) is False
        and vae_cache_after["host_class"] == "WanVAE_"
        and vae_cache_after["enc_cache_len"] > 0
        and vae_cache_after["enc_cache_all_none"] is True
        and vae_cache_after["enc_stream_shape"] is None
        and vae_cache_after["dec_cache_len"] > 0
        and vae_cache_after["dec_cache_all_none"] is True
        and vae_cache_after["streaming_encode_calls"] == 0
        and vae_cache_after["decoder_decode_calls"] == 0
        and vae_cache_unchanged is True,
        vae_cache_after,
    )

    failures = [item for item in checks if not item["ok"]]
    report["checks"] = checks
    report["status"] = "PASS" if not failures else "FAIL"
    report["smoke_gate_pass"] = not failures
    report["failures"] = [item["check"] for item in failures]
    report["resources"]["peak_allocated_mib"] = round(
        report["resources"]["peak_allocated_bytes"] / 1024**2, 1
    )
    report["resources"]["peak_reserved_mib"] = round(
        report["resources"]["peak_reserved_bytes"] / 1024**2, 1
    )
    args.output_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )

    print(f"REPORT={args.output_json}")
    print(
        f"episode_frames={len(timestamps)} image_size={args.image_size} "
        f"geometry={observed_geometry} seed={args.manual_seed}"
    )
    print(
        f"witness: canonical_redecode_max_abs={witness['canonical_redecode_max_abs']:.3e} "
        f"item_action_vs_dataset_env12_max_abs={witness['item_action_vs_dataset_env12_max_abs']:.3e} "
        f"composite_png_roundtrip_exact={witness['composite_png_roundtrip_exact']}"
    )
    for name in ("cold_S0", "update20_steps0_19", "replay_step20_lost_response", "post_reset_new_session_cold"):
        entry = next(item for item in (entry0, entry1, entry2, entry3) if item["stage"] == name)
        print(
            f"  {entry['stage']:<32} step={entry['consumer_step']:<2} "
            f"encoded={entry['encoded_steps']} replay={entry['replay']} "
            f"prefix={entry['prefix_present']} state={entry['state_present']} "
            f"enc_calls={entry['encode_calls_delta']} scan_calls={entry['scan_calls_delta']} "
            f"adapted={entry['adapted_steps']}"
        )
    print(f"scan_blocks={[(item['T'], item['state_in_present']) for item in scan_calls]}")
    print(f"counts: encode={len(encode_calls)} scan={len(scan_calls)}")
    print(
        f"resources: peak_allocated={report['resources']['peak_allocated_mib']} MiB "
        f"peak_reserved={report['resources']['peak_reserved_mib']} MiB"
    )
    for item in checks:
        print(f"  [{'PASS' if item['ok'] else 'FAIL'}] {item['check']}")
    print(f"STATUS={report['status']} SMOKE_GATE_PASS={report['smoke_gate_pass']}")
    return 0 if report["smoke_gate_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())