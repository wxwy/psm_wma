"""CPU-only injected daemon boundary for the Registry peer lifecycle test.

This fixture never imports Torch or attests actual weights/GPU placement. The
production daemon command has no option selecting this test backend.
"""

from __future__ import annotations

import hashlib
import struct
import sys

from cosmos_framework.inference.robocasa_vae_daemon import run_daemon
from cosmos_framework.inference.robocasa_vae_protocol import canonical_json


def fake_encoder(config):
    def encode(frames):
        return [struct.pack("<96f", *([frame.rgb[0] / 255] * 96)) for frame in frames]

    return encode, {
        "identity": config["identity"],
        "vae_file_sha256": config["vae_file_sha256"],
        "constructor_config_sha256": hashlib.sha256(
            canonical_json(config["constructor_config"])
        ).hexdigest(),
        "backend": "synthetic_cpu_test",
        "device_type": "cpu",
        "bootstrap_drain_timeout_s": config["drain_timeout_s"],
    }


if __name__ == "__main__":
    run_daemon(
        int(sys.argv[1]),
        int(sys.argv[2]),
        encoder_factory=fake_encoder,
        clock_domain_fn=lambda: sys.argv[3] if len(sys.argv) == 4 else "cpu-clock",
        device_attestor=lambda expected, encoder: expected,
    )
