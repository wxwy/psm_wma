"""Isolate the frozen View Encode1 loader from the Policy's own Wan imports."""

from __future__ import annotations

import os
import socket
import struct
import subprocess
import sys
from io import BytesIO
from pathlib import Path

from g2.io import ContractError, read_json
from g2.latent_cache.batch_contract import validate_batch_recipe

MAX_PNG_BYTES = 32 * 1024**2
MAX_PNG_PIXELS = 4096**2
LATENT_SHAPE = (48, 16, 16)
LATENT_BYTES = 48 * 16 * 16 * 4


def read_view_recipe(path, expected_id):
    recipe = validate_batch_recipe(read_json(path, limit=1 << 20))
    if (
        recipe["recipe_id"] != expected_id
        or recipe["encoder"].get("test_only") is not False
        or recipe["encoder"]["legacy_loader"].get("device") != "cuda:0"
    ):
        raise ContractError("R2 requires the training job's real View VAE recipe")
    return recipe


def decode_rgb(raw):
    import numpy as np
    from PIL import Image

    with Image.open(BytesIO(raw)) as image:
        if (
            image.format != "PNG"
            or image.mode != "RGB"
            or image.width * image.height > MAX_PNG_PIXELS
        ):
            raise ContractError("R2 encoder requires a bounded final RGB PNG")
        return np.array(image, copy=True)


def _receive(channel, limit):
    def exact(size):
        data = bytearray(size)
        view = memoryview(data)
        while view:
            count = channel.recv_into(view)
            if not count:
                raise EOFError("R2 View encoder channel closed")
            view = view[count:]
        return data

    size = struct.unpack("!I", exact(4))[0]
    if not 0 < size <= limit:
        raise ContractError("R2 View encoder message exceeds its byte limit")
    return exact(size)


def _send(channel, payload):
    channel.sendall(struct.pack("!I", len(payload)))
    channel.sendall(payload)


class OnlineViewEncoder:
    """One resident encoder inside each existing Policy process group."""

    def __init__(self, *, weights, recipe_path, recipe_id, timeout_s):
        root = Path(__file__).resolve().parents[2]
        child = root / "cosmos-framework"
        environment = dict(
            os.environ,
            PYTHONPATH=os.pathsep.join((str(root), str(child))),
            PYTHONDONTWRITEBYTECODE="1",
            COSMOS_TRAINING="0",
            COSMOS_INTERNAL="0",
            COSMOS_DEVICE="cuda",
        )
        for key in ("RANK", "LOCAL_RANK", "WORLD_SIZE", "MASTER_ADDR", "MASTER_PORT"):
            environment.pop(key, None)
        self.process = None
        self.channel, worker = socket.socketpair()
        self.channel.settimeout(timeout_s)
        try:
            with worker:
                self.process = subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "g2.online.view_encoder",
                        str(worker.fileno()),
                        str(weights),
                        str(recipe_path),
                        recipe_id,
                    ],
                    pass_fds=(worker.fileno(),),
                    cwd=root,
                    env=environment,
                )
            if _receive(self.channel, 64) != recipe_id.encode():
                raise ContractError(
                    "R2 View encoder did not attest the configured recipe"
                )
        except BaseException:
            self.close()
            raise

    def encode(self, raw):
        import torch

        if not 0 < len(raw) <= MAX_PNG_BYTES:
            raise ContractError("R2 View input exceeds its byte limit")
        try:
            _send(self.channel, raw)
            result = _receive(self.channel, LATENT_BYTES)
            if len(result) != LATENT_BYTES:
                raise ContractError("R2 View encoder returned the wrong latent size")
            latent = torch.frombuffer(result, dtype=torch.float32).reshape(LATENT_SHAPE)
            if not bool(torch.isfinite(latent).all()):
                raise ContractError("R2 View encoder returned a nonfinite latent")
            return latent
        except (EOFError, OSError, ValueError):
            self.close()
            raise

    def close(self):
        self.channel.close()
        process = self.process
        self.process = None
        if process is not None:
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


def _worker(fd, weights, recipe_path, recipe_id):
    import numpy as np

    from g2.latent_cache.batch_encoding import WanBatchEncoder

    with socket.socket(fileno=int(fd)) as channel:
        recipe = read_view_recipe(recipe_path, recipe_id)
        encoder = WanBatchEncoder(weights, max_batch_size=recipe["batch_size"])
        if encoder.descriptor() != recipe["encoder"]:
            raise ContractError(
                "loaded View encoder source, weights or runtime differs from the R2 recipe"
            )
        # Admit the resident VAE under the existing Policy startup reservation.
        # This one probe is discarded and never becomes a Reader input.
        encoder.encode_batch(
            [np.zeros((1, 1, 3), dtype=np.uint8)], recipe["preprocessing"]
        )
        _send(channel, recipe_id.encode())
        while True:
            try:
                raw = _receive(channel, MAX_PNG_BYTES)
            except EOFError:
                return
            result = encoder.encode_batch([decode_rgb(raw)], recipe["preprocessing"])
            _send(channel, result[0][0].numpy().tobytes())


if __name__ == "__main__":
    _worker(*sys.argv[1:])
